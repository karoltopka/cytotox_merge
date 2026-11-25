#!/usr/bin/env python3
"""RAW 264.7 values from Zhang 2012 SI Figure S2 (B: ATP, C: LDH), read from the VECTOR graphics of SI pages 4-5.

The SI pages are converted to SVG (pdftocairo); every line segment, marker and error bar is a separate path with exact
coordinates.  Per panel:
  * axis calibration = least-squares fit through the tick marks (black, 0.6-0.7 pt strokes);
  * every series has one block of 40 error-bar paths (10 doses x upper bar, upper cap, lower bar, lower cap), drawn in
    legend order after all lines/markers -> block k = legend entry k (checked against the legend line colours);
  * value = midpoint between the two caps (mean +/- SD bars are symmetric; when a cap is clipped the end of the bar is used);
  * cross-checks: marker centre (constant shape offset) and the straight connecting segments extended to the dose.
Output: results/Zhang2012_SI_Fig_S2_RAW264.7_readings.csv (all 24 materials, both panels, both tests)."""
import collections
import csv
import re
import statistics
from xml.etree import ElementTree as ET

from common import DOSES, LEFT, NOM, OUT, RIGHT, si_svg

SVG = '{http://www.w3.org/2000/svg}'
NUM = r'-?\d+(?:\.\d+)?(?:e-?\d+)?'


def parse_matrix(t):
    if not t:
        return (1, 0, 0, 1, 0, 0)
    return tuple(float(x) for x in re.match(r'matrix\(([^)]*)\)', t).group(1).split(','))


def apply(m, x, y):
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def parse_d(d):
    toks = re.findall(r'[MLCZ]|' + NUM, d)
    cmds, i, cur = [], 0, None
    while i < len(toks):
        t = toks[i]
        if t in 'MLCZ':
            cur = t
            i += 1
            if t == 'Z':
                cmds.append(('Z', []))
            continue
        n = {'M': 2, 'L': 2, 'C': 6}[cur]
        cmds.append((cur, [float(v) for v in toks[i:i + n]]))
        i += n
        if cur == 'M':
            cur = 'L'
    return cmds


def load(path):
    """all drawn paths (glyph definitions excluded) in page coordinates, in drawing order"""
    root = ET.parse(path).getroot()
    defs = {id(el) for d in root.iter(SVG + 'defs') for el in d.iter(SVG + 'path')}
    out, order = [], 0
    for el in root.iter(SVG + 'path'):
        if id(el) in defs or not el.get('d', '').strip():
            continue
        st = dict(kv.strip().split(':', 1) for kv in el.get('style', '').split(';') if ':' in kv)
        m = parse_matrix(el.get('transform'))
        cmds = parse_d(el.get('d'))
        pts, allpts = [], []
        for c, v in cmds:
            if c in 'ML':
                p = apply(m, v[0], v[1])
                pts.append(p)
                allpts.append(p)
            elif c == 'C':
                p = apply(m, v[4], v[5])
                pts.append(p)
                allpts += [apply(m, v[0], v[1]), apply(m, v[2], v[3]), p]
        order += 1
        out.append(dict(order=order, fill=st.get('fill', 'none'), stroke=st.get('stroke', 'none'), sw=st.get('stroke-width'),
                        pts=pts, allpts=allpts, ncmd=len(cmds)))
    return out


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def segs_hv(P):
    out = []
    for p in P:
        if p['fill'] != 'none' or p['ncmd'] != 2:
            continue
        (x0, y0), (x1, y1) = p['pts']
        if abs(y0 - y1) < 1e-3 and abs(x0 - x1) > 1e-3:
            out.append(('H', p, min(x0, x1), max(x0, x1), y0))
        elif abs(x0 - x1) < 1e-3 and abs(y0 - y1) > 1e-3:
            out.append(('V', p, min(y0, y1), max(y0, y1), x0))
    return out


def fit(px, v):
    n = len(px)
    mx, mv = sum(px) / n, sum(v) / n
    b = sum((a - mx) * (c - mv) for a, c in zip(px, v)) / sum((a - mx) ** 2 for a in px)
    a = mv - b * mx
    return a, b, max(abs(a + b * q - c) for q, c in zip(px, v))


def find_axes(P, region, yvals, xvals=(0, 50, 100, 150, 200)):
    x0r, x1r, y0r, y1r = region
    S = segs_hv(P)
    isax = lambda s: (s[1]['stroke'] == 'rgb(0%,0%,0%)' and s[1]['sw'] and 0.55 < float(s[1]['sw']) < 0.75
                      and 2 < s[3] - s[2] < 3.5)
    yt = [s for s in S if s[0] == 'H' and isax(s) and x0r < s[2] < x1r and y0r < s[4] < y1r]
    xt = [s for s in S if s[0] == 'V' and isax(s) and x0r < s[4] < x1r and y0r < s[2] < y1r]
    ytp = sorted({round(s[4], 3) for s in yt}, reverse=True)
    xtp = sorted({round(s[4], 3) for s in xt})
    assert len(ytp) == len(yvals) and len(xtp) == len(xvals), (ytp, xtp)
    return dict(ytp=ytp, xtp=xtp, fy=fit(ytp, yvals), fx=fit(xtp, xvals), ax_order=min(s[1]['order'] for s in yt + xt))


def errbar_blocks(P, region, after_order):
    """maximal runs (in drawing order) of thin coloured 2-point segments"""
    x0r, x1r, y0r, y1r = region
    rows = [p for p in P if p['order'] > after_order and p['fill'] == 'none' and p['ncmd'] == 2 and p['sw']
            and float(p['sw']) < 0.4]
    blocks, cur = [], None
    for p in rows:
        (xa, ya), (xb, yb) = p['pts']
        inside = x0r < (xa + xb) / 2 < x1r and y0r - 40 < (ya + yb) / 2 < y1r
        key = (p['stroke'], p['sw'])
        if cur and cur['key'] == key and p['order'] == cur['last'] + 1 and inside:
            cur['paths'].append(p)
            cur['last'] = p['order']
        else:
            if cur and len(cur['paths']) >= 8:
                blocks.append(cur)
            cur = dict(key=key, paths=[p], last=p['order']) if inside else None
    if cur and len(cur['paths']) >= 8:
        blocks.append(cur)
    return blocks


def block_extremes(block):
    """error-bar parts clustered per dose x: (x, top, bottom, number of caps, parts)"""
    items = []
    for p in block['paths']:
        (xa, ya), (xb, yb) = p['pts']
        if abs(ya - yb) < 1e-3:
            items.append(((xa + xb) / 2, 'cap', [ya], p['order']))
        else:
            items.append((xa, 'bar', [ya, yb], p['order']))
    items.sort(key=lambda t: t[0])
    cl = []
    for it in items:
        if cl and it[0] - cl[-1][-1][0] < 0.12:
            cl[-1].append(it)
        else:
            cl.append([it])
    out = []
    for c in cl:
        ys = [y for it in c for y in it[2]]
        bars = [it[0] for it in c if it[1] == 'bar']
        x = sum(bars) / len(bars) if bars else sum(it[0] for it in c) / len(c)
        out.append((x, min(ys), max(ys), sum(1 for it in c if it[1] == 'cap'), c))
    return out


def is_errbar_block(b):
    """40 axis-parallel parts at 10 dose positions (an asterisk marker block has diagonals)"""
    if len(b['paths']) < 36:
        return False
    for p in b['paths']:
        (xa, ya), (xb, yb) = p['pts']
        if abs(xa - xb) > 1e-3 and abs(ya - yb) > 1e-3:
            return False
    ex = block_extremes(b)
    return len(ex) == 10 and sum(e[3] for e in ex) >= 19


def panel_series(P, region, yvals, names):
    a = find_axes(P, region, yvals)
    ay, by, _ = a['fy']
    ax, bx, _ = a['fx']
    bl = [b for b in errbar_blocks(P, region, a['ax_order']) if is_errbar_block(b)]
    assert len(bl) == len(names), (len(bl), len(names))
    out = {}
    for name, b in zip(names, bl):
        rows = []
        for x, ytop, ybot, nc, cl in block_extremes(b):
            capy = sorted({round(it[2][0], 3) for it in cl if it[1] == 'cap'})
            if len(capy) >= 2:              # both caps present: their midpoint is the mean
                ytop, ybot = capy[0], capy[-1]
            ymid = (ytop + ybot) / 2
            dose = ax + bx * x
            rows.append(dict(dose=min(DOSES, key=lambda d: abs(d - dose)), dose_read=dose, x=x, ymid=ymid,
                             sd=(ybot - ytop) / 2 * abs(by), ncaps=nc, color=b['key'][0], first=b['paths'][0]['order']))
        assert len({r['dose'] for r in rows}) == 10
        out[name] = rows
    return out, a


def line_estimates(P, color, o0, o1, xs):
    """y at each dose from extending the series' straight connecting segments (they stop short of the markers)"""
    segs = [p for p in P if o0 <= p['order'] <= o1 and p['fill'] == 'none' and p['stroke'] == color and p['ncmd'] == 2
            and p['sw'] and float(p['sw']) > 0.7]
    est = {x: [] for x in xs}
    for p in segs:
        (xa, ya), (xb, yb) = p['pts']
        if xb < xa:
            xa, ya, xb, yb = xb, yb, xa, ya
        if xb - xa < 0.05:
            continue
        left = max([x for x in xs if x <= xa + 0.01], default=None)
        right = min([x for x in xs if x >= xb - 0.01], default=None)
        if left is None or right is None:
            continue
        k = (yb - ya) / (xb - xa)
        est[left].append(ya + k * (left - xa))
        est[right].append(yb + k * (right - xb))
    return est


def marker_centres(P, color, o0, o1):
    out = []
    for p in P:
        if o0 <= p['order'] <= o1 and p['fill'] == color:
            b = bbox(p['allpts'])
            out.append(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))
    return out


def main():
    P4, P5 = load(si_svg(4)), load(si_svg(5))
    panels = [('ATP', 'left', P4, (80, 300, 520, 700), list(range(0, 121, 20)), LEFT, 'S2B'),
              ('ATP', 'right', P4, (300, 500, 520, 700), list(range(0, 141, 20)), RIGHT, 'S2B'),
              ('LDH', 'left', P5, (80, 300, 170, 345), list(range(0, 101, 20)), LEFT, 'S2C'),
              ('LDH', 'right', P5, (300, 500, 170, 345), list(range(0, 101, 20)), RIGHT, 'S2C')]
    rows = []
    for test, side, P, reg, yv, names, fig in panels:
        S, a = panel_series(P, reg, yv, names)
        ay, by, ry = a['fy']
        # series k: its lines + markers lie between the first thick line of colour k and of colour k+1 (legend order)
        eb_first = min(r[0]['first'] for r in S.values())
        thick = [p for p in P if a['ax_order'] < p['order'] < eb_first and p['fill'] == 'none' and p['sw']
                 and 0.8 < float(p['sw']) < 0.9 and reg[0] < p['pts'][0][0] < reg[1] and reg[2] - 30 < p['pts'][0][1] < reg[3]]
        starts, prev = [], None
        for p in thick:
            if p['stroke'] != prev:
                starts.append((p['stroke'], p['order']))
                prev = p['stroke']
        assert [c for c, o in starts] == [S[n][0]['color'] for n in names], 'series order differs from legend order'
        for k, n in enumerate(names):
            o0 = starts[k][1]
            o1 = (starts[k + 1][1] - 1) if k + 1 < len(starts) else eb_first - 1
            col = S[n][0]['color']
            le = line_estimates(P, col, o0, o1, [r['x'] for r in S[n]])
            mc = marker_centres(P, col, o0, o1)
            for r in S[n]:
                v = ay + by * r['ymid']
                m = [c for c in mc if abs(c[0] - r['x']) < 0.8]
                mval = (ay + by * min(m, key=lambda c: abs(c[1] - r['ymid']))[1]) if m else None
                lval = statistics.mean(ay + by * y for y in le[r['x']]) if le[r['x']] else None
                rows.append(dict(
                    cell_line='RAW 264.7', test=test, figure=f'SI Fig. {fig} ({side} panel)', material=n,
                    dose_ug_ml=NOM[r['dose']], dose_exact=r['dose'], dose_read_from_axis=round(r['dose_read'], 3),
                    value_on_figure=round(v, 2), unit='% ATP level' if test == 'ATP' else '% cell death',
                    SD=round(r['sd'], 2), viability=round(v if test == 'ATP' else 100 - v, 1),
                    check_marker=None if mval is None else round(mval, 2),
                    check_line=None if lval is None else round(lval, 2), error_bar_caps=r['ncaps'],
                    calibration_y_max_residual=round(ry, 4)))
    OUT.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    with open(OUT / 'Zhang2012_SI_Fig_S2_RAW264.7_readings.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    d = collections.defaultdict(list)
    for r in rows:
        if r['check_line'] is not None:
            d['line'].append(abs(r['check_line'] - r['value_on_figure']))
    print(f'{len(rows)} RAW 264.7 readings; median |line - error bars| = {statistics.median(d["line"]):.3f} units')


if __name__ == '__main__':
    main()
