# the comments of the step, apart from the data handling: Audit.put and Audit.drop record every value set and every record
# removed (rule, comment, kind of change against the source files); Audit.write compares the table after the step with the table before
# it and writes the audit workbook (sheet changes: every changed cell; sheet removed: every removed record)
import re

import numpy as np
import pandas as pd

CHANGE_COLUMNS = ["step", "rule_id", "raw_id", "Dataset", "DOI", "column", "change_type", "old_value", "new_value", "comment"]
REMOVED_COLUMNS = ["step", "rule_id", "comment", "raw_id", "Dataset", "DOI", "Material", "Cell_Type", "Test", "Time (hr)", "Cell_Viability (%)"]
NUMERIC = ['Aspect_Ratio', 'Cell_Viability (%)', 'Concentration (g/l)2', 'Concentration (uM)', 'Concentration (ug/ml)', 'DLS_Diameter (nm)', 'DLS_Diameter_Medium (nm)', 'DLS_Diameter_Other (nm)', 'DLS_Diameter_Water (nm)', 'Diameter (nm)', 'Dry_Diameter (nm)', 'No_of_Cells (cells/well)', 'Size_in_Medium (nm)', 'Size_in_Water (nm)', 'Time (hr)', 'Zeta potential (mV)', 'Zeta_in_Medium (mV)', 'Zeta_in_Other (mV)', 'Zeta_in_Water (mV)']   # a value set from the comments is a number in these columns, text elsewhere


def same(a, b):
    # equal cell values: numbers compared as numbers, empty cells equal
    if pd.isna(a) and pd.isna(b):
        return True
    if pd.isna(a) or pd.isna(b):
        return False
    try:
        return abs(float(a) - float(b)) <= 1e-6 * max(1.0, abs(float(b)))
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


def without_own_doi(basis, doi):
    # the basis without the DOI of the record itself, which the tables give in their DOI column; kept where the basis cites another
    # document as well, because there the DOI tells the sources apart
    if not isinstance(basis, str) or not isinstance(doi, str) or not doi.strip() or doi.strip().lower() not in basis.lower():
        return basis
    doi = doi.strip()
    if {d.lower().rstrip(".:") for d in re.findall(r"10\.\d{4,9}/[^\s\"'“”;,)\]]+", basis)} - {doi.lower()}:
        return basis
    d = re.escape(doi)
    for pattern, repl in ((rf"^{d},?\s+", ""),                        # "10.x/y p. 5: '...'", "10.x/y, Supplementary Information ..."
                          (rf"\s*\({d}\)", ""),                       # "'...' (10.x/y)"
                          (rf"\({d}\s+", "("),                        # "'...' (10.x/y p. 9)" -> "(p. 9)"
                          (rf"^publication {d} ", "The publication "),  # "Publication 10.x/y reports ..."
                          (rf"\s+(?:for|in) {d}:", ":")):              # "Supplementary material for 10.x/y: ..."
        basis = re.sub(pattern, repl, basis, flags=re.I)
    assert doi.lower() not in basis.lower(), f"the DOI of the record is left in the basis: {basis[:120]}"
    return basis.strip()



def comment_text(comment, basis=""):
    # one comment: the reason and, where there is one, the quotation or place in the publication after it (a value from the
    # publication review carries only its explanation)
    comment = "" if pd.isna(comment) else str(comment).strip()
    basis = "" if pd.isna(basis) else str(basis).strip()
    if not basis:
        return comment
    if comment in ("", "curated value (publication review)"):
        return basis
    return comment.rstrip(".") + ". Basis: " + basis


class Audit:
    def __init__(self, step, df, before=None):
        # step: its id; df: the table the rules work on (records are removed in place); before: the file of the table before the
        # step
        self.step, self.df, self.before, self.changes, self.removed = step, df, before, [], []

    def put(self, i, column, value, rule, comment, basis="", outside=True):
        # write a value and record the change. Kind of change, measured against the three source files: 'harmonisation' when the
        # rule only maps or normalises a source value (outside=False); otherwise 'correction' when the field held a value before our
        # first change to it and 'addition' when it was empty (the column _first_change keeps that verdict for the later steps)
        df = self.df
        old = df.at[i, column]
        if same(old, value):
            return
        kind = "harmonisation"
        if outside:
            first = dict(x.split("=", 1) for x in str(df.at[i, "_first_change"]).split(";") if "=" in x)
            kind = first.get(column) or ("addition" if pd.isna(old) or str(old).strip() == "" else "correction")
            first[column] = kind
            df.at[i, "_first_change"] = ";".join(f"{k}={v}" for k, v in first.items())
        df.at[i, column] = value
        self.changes.append({"step": self.step, "rule_id": rule, "raw_id": df.at[i, "raw_id"], "Dataset": df.at[i, "Dataset"],
                             "DOI": df.at[i, "DOI"], "column": column, "change_type": kind, "old_value": old, "new_value": value,
                             "comment": comment_text(comment, without_own_doi(basis, df.at[i, "DOI"]) if basis else "")})

    def drop(self, mask, rule, comment):
        # remove the records of the mask (in place) and record them
        df = self.df
        mask = mask.fillna(False).astype(bool)
        for _, r in df[mask].iterrows():
            self.removed.append({"step": self.step, "rule_id": rule, "comment": comment, "raw_id": r["raw_id"], "Dataset": r["Dataset"],
                                 "DOI": r["DOI"], "Material": r["Material"], "Cell_Type": r["Cell_Type"], "Test": r["Test_raw"],
                                 "Time (hr)": r["Time (hr)"], "Cell_Viability (%)": r["Cell_Viability (%)"]})
        df.drop(index=df.index[mask.to_numpy()], inplace=True)

    def write(self, path):
        # compare the table after the step with the table before it, then write the audit workbook
        df = self.df
        if self.before is not None:
            before = pd.read_excel(self.before, keep_default_na=False, na_values=[""]).astype(object)
            after = df.set_index("raw_id")
            gone = set(before.raw_id) - set(after.index)
            assert gone == {r["raw_id"] for r in self.removed}, "the removed records and the removals of the rules differ"
            kept = before.set_index("raw_id").loc[after.index]
            recorded = {(c["raw_id"], c["column"]) for c in self.changes}
            differ = {(rid, col) for col in kept.columns if col in after.columns and not col.startswith("_")
                      for rid, x, y in zip(after.index, kept[col], after[col]) if not same(x, y)}
            assert differ <= recorded, f"cells changed without a rule: {sorted(differ - recorded)[:5]}"
            print(len(gone), "records removed and", len(differ), "cells changed compared with the table before the step")
        with pd.ExcelWriter(path) as xw:
            pd.DataFrame(self.changes, columns=CHANGE_COLUMNS).to_excel(xw, sheet_name="changes", index=False)
            pd.DataFrame(self.removed, columns=REMOVED_COLUMNS).to_excel(xw, sheet_name="removed", index=False)
        print(len(df), "records after the step |", len(self.removed), "records removed |", len(self.changes), "cells changed |", path)


def apply_comments(audit, path, rules):
    # the rows of the comments table of the step whose rule is in rules, in the order of the table: set the value of a variable of a
    # record, or remove the record; the comment goes with the change into the audit workbook
    t = pd.read_excel(path, keep_default_na=False, na_values=[""], dtype={"raw_id": str, "DOI": str}).astype(object)
    t = t[t["rule"].isin(rules)]
    df = audit.df
    n_set = n_removed = 0
    for r in t.itertuples(index=False):
        if r.action == "remove record":
            audit.drop(df["raw_id"] == r.raw_id, r.rule, r.comment)
            n_removed += 1
            continue
        idx = df.index[df["raw_id"] == r.raw_id]
        assert len(idx) == 1, f"record {r.raw_id} not found once"
        value = r.new_value
        if not pd.isna(value):
            value = float(value) if r.variable in NUMERIC else str(value)
        audit.put(idx[0], r.variable, value, r.rule, r.comment)
        n_set += 1
    print(len(t), "comments applied (" + ", ".join(rules) + "):", n_set, "values set,", n_removed, "records removed")
