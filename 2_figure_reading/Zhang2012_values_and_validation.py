"""Zhang et al. 2012: the figure readings mapped onto the dataset records, and the validation of the reading method.

In the Nanopharos source, the 378 records of the ten non-toxic oxides carry integer placeholders (80-99, independent of the dose); their
values are taken from the right panels of the figures. The left panels show the four toxic oxides (CoO, CuO, Mn2O3, ZnO), whose values
the Nanopharos source gives; the same readings of these panels validate the method.

Inputs:  results/Zhang2012_SI_Fig_S2_RAW264.7_readings.csv, results/Zhang2012_Fig_2_BEAS-2B_readings.csv (the two reading scripts),
         inputs/records_before_viability_check.csv
Outputs: results/Zhang2012_values_for_dataset.csv (one row per placeholder record), results/Zhang2012_validation_toxic_oxides.csv
"""
import numpy as np
import pandas as pd

from common import OUT, RECORDS

TEN = ['Al2O3', 'CeO2', 'Fe2O3', 'Gd2O3', 'HfO2', 'In2O3', 'La2O3', 'NiO', 'Sb2O3', 'SiO2']   # non-toxic oxides with placeholders
FIGURE = {'RAW 264.7': 'SI Fig. S2{p} (right panel), SVG vector graphics', 'BEAS-2B': 'Fig. 2{p} (right panel), raster 300 ppi'}
METHOD = {'RAW 264.7': 'midpoint between the error-bar caps (mean +/- SD); checks: marker centre and extension of the connecting line',
          'BEAS-2B': 'line connecting the doses extended to the dose (pixels of the series colour); checks: error-bar caps / second segment'}

raw = pd.read_csv(OUT / 'Zhang2012_SI_Fig_S2_RAW264.7_readings.csv').assign(status='read', confirmation='')
beas = pd.read_csv(OUT / 'Zhang2012_Fig_2_BEAS-2B_readings.csv')
readings = pd.concat([raw, beas], ignore_index=True)
readings['side'] = np.where(readings.figure.str.contains('right panel'), 'right', 'left')
records = pd.read_csv(RECORDS)
zhang = records[records.DOI == '10.1021/nn3010087']

# validation: readings of the left panels against the values the Nanopharos source gives for the toxic oxides
left = readings[(readings.side == 'left') & readings.viability.notna()]
val = left.merge(zhang, left_on=['cell_line', 'material', 'test', 'dose_ug_ml'], right_on=['Cell_Type', 'Material', 'Test', 'Concentration (ug/ml)'])
val = val[['raw_id', 'cell_line', 'test', 'material', 'dose_ug_ml', 'viability', 'Cell_Viability (%)']].rename(
    columns={'viability': 'read_from_figure', 'Cell_Viability (%)': 'value_in_Nanopharos'})
val['difference_pp'] = (val.read_from_figure - val.value_in_Nanopharos).round(2)
val.to_csv(OUT / 'Zhang2012_validation_toxic_oxides.csv', index=False)
accuracy = {c: 'validated on %d values of CoO/CuO/Mn2O3/ZnO given by the Nanopharos source (same figure): mean %.2f pp, max %.2f pp'
               % (len(g), g.difference_pp.abs().mean(), g.difference_pp.abs().max()) for c, g in val.groupby('cell_line')}

# values for the placeholder records: readings of the right panels
rows = []
for _, r in zhang[zhang.Material.isin(TEN)].iterrows():
    m = readings[(readings.cell_line == r.Cell_Type) & (readings.side == 'right') & (readings.material == r.Material) & (readings.test == r.Test)
                 & np.isclose(readings.dose_ug_ml, r['Concentration (ug/ml)'])]
    assert len(m) == 1, (r.raw_id, len(m))
    m = m.iloc[0]
    ok = pd.notna(m.viability)
    note = '' if r.Cell_Type == 'RAW 264.7' else m.status + (' | ' + m.confirmation if isinstance(m.confirmation, str) and m.confirmation else '')
    rows.append({'raw_id': r.raw_id, 'Material': r.Material, 'Cell_Type': r.Cell_Type, 'Test': r.Test, 'Concentration (ug/ml)': r['Concentration (ug/ml)'],
                 'placeholder_value_source': r['Cell_Viability (%)'], 'value_read_from_figure': m.value_on_figure, 'figure_unit': m.unit,
                 'SD_read_from_figure': m.SD if r.Cell_Type == 'RAW 264.7' else None, 'Cell_Viability (%)': round(m.viability, 1) if ok else None,
                 'status': 'read' if ok else m.status.split(':')[0], 'notes': note, 'figure': FIGURE[r.Cell_Type].format(p='B' if r.Test == 'ATP' else 'C'),
                 'method': METHOD[r.Cell_Type], 'accuracy': accuracy[r.Cell_Type],
                 'conversion': 'ATP: % ATP level = viability' if r.Test == 'ATP' else 'LDH: viability = 100 - % cell death'})
res = pd.DataFrame(rows)
res.to_csv(OUT / 'Zhang2012_values_for_dataset.csv', index=False)

for c, g in val.groupby('cell_line'):
    print(f'validation {c}: n = {len(g)}, mean |difference| = {g.difference_pp.abs().mean():.2f} pp, max = {g.difference_pp.abs().max():.2f} pp')
print(res.groupby(['Cell_Type', 'Test', 'status']).size().to_string())
print('read', (res.status == 'read').sum(), 'of', len(res))
