#!/usr/bin/env python3
"""BEAS-2B values from Zhang 2012 main Figure 2 (B: ATP, C: LDH), read from the native 300-ppi raster (lossless CMYK).

Every series is drawn in its own exact CMYK colour; anti-aliasing only blends edges.  Per series and dose:
  * axis calibration = linear fit through tick-mark centroids found automatically (black pixels, K-weighted);
  * the straight connecting line between two doses is located column by column in the gap between the markers
    (7 px margin); the line centre comes from a run of exact-colour pixels of full line thickness, or - when another
    series covers one side - from the uncovered edge plus half the line thickness.  An edge counts as uncovered when its
    neighbour is background, an anti-aliased blend with white, or a series drawn EARLIER (drawing order = legend order);
  * robust straight-line fit (RANSAC) per segment, value = line extended to the dose x (both neighbouring segments
    when available);
  * acceptance: >=8 columns and predicted s.e. at the dose <=0.8 px; two segments must agree within 0.75 units
    (weighted mean); a single unconfirmed segment needs >=12 columns and s.e. <=0.5 px;
  * confirmation: pair of error-bar caps (series colour blended with white) symmetric around the value.
Doses <=6.25 ug/mL lie <=17 px from the y axis where the markers/error bars of all series overlap -> not readable.

Colours: the main figure draws series 7 in YELLOW although the legend shows the SI colour (olive ZnO / maroon In2O3).
Verified by the marker shapes on the yellow line (right-pointing triangles = In2O3 / ZnO) and, for ZnO, by the published
values; the olive line carries hexagons (NiO) and the single maroon line spheres (TiO2).
Output: results/Zhang2012_Fig_2_BEAS-2B_readings.csv"""
import csv
import itertools

import numpy as np
from PIL import Image

from common import DOSES, LEFT, NOM, OUT, RIGHT, fig2_tiff

A = np.asarray(Image.open(fig2_tiff())).astype(float)          # H x W x CMYK
C = lambda *v: np.array(v, float)
COLOUR = {'black': C(93, 93, 93, 243), 'red': C(0, 255, 255, 0), 'green': C(255, 0, 255, 0), 'blue': C(255, 255, 0, 0),
          'cyan': C(255, 0, 0, 0), 'magenta': C(0, 255, 0, 0), 'yellow': C(0, 0, 255, 0), 'olive': C(67, 67, 195, 90),
          'navy': C(195, 195, 67, 90), 'purple': C(67, 195, 67, 90), 'maroon': C(67, 195, 195, 90),
          'dkgreen': C(195, 67, 195, 90), 'teal': C(195, 67, 67, 90), 'ybblue': C(220, 220, 60, 52),
          'orange': C(0, 127, 255, 0), 'violet': C(127, 255, 0, 0), 'pink': C(0, 255, 127, 0)}
RIGHT_COL = ['black', 'red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'olive', 'navy', 'purple', 'maroon',
             'dkgreen', 'teal', 'ybblue', 'orange', 'violet', 'pink']
LEFT_COL = ['black', 'red', 'green', 'blue', 'cyan', 'magenta', 'yellow']
PANELS = {  # box (x0, x1, y0, y1) in native pixels, y tick values, test, figure label
    'B_right': ((820, 1460, 930, 1560), list(range(0, 141, 20)), 'ATP', 'Fig. 2B (right panel)', list(zip(RIGHT, RIGHT_COL))),
    'C_right': ((820, 1460, 1700, 2400), list(range(0, 101, 20)), 'LDH', 'Fig. 2C (right panel)', list(zip(RIGHT, RIGHT_COL))),
    'B_left': ((60, 800, 930, 1560), list(range(0, 121, 20)), 'ATP', 'Fig. 2B (left panel)', list(zip(LEFT, LEFT_COL))),
    'C_left': ((60, 800, 1700, 2400), list(range(0, 101, 20)), 'LDH', 'Fig. 2C (left panel)', list(zip(LEFT, LEFT_COL)))}
MARGIN = 7          # px kept free around each dose (markers are ~11 px wide)
T0 = 4.57           # exact-colour core thickness of a line (isolated SnO2 line: runs of 4-5 px at slope 0.1)


# ---------- axes ----------
def _runs(p, thr=0.5):
    out, i = [], 0
    while i < len(p):
        if p[i] > thr:
            j = i
            while j < len(p) and p[j] > thr:
                j += 1
            seg = np.arange(i, j)
            out.append((float((p[seg] * seg).sum() / p[seg].sum()), float(p[seg].sum()), j - i))
            i = j
        else:
            i += 1
    return out


def axes(box, yvals):
    x0, x1, y0, y1 = box
    sub = A[y0:y1, x0:x1]
    c, m, y, k = sub[..., 0], sub[..., 1], sub[..., 2], sub[..., 3]
    w = np.where((np.abs(c - m) <= 4) & (np.abs(m - y) <= 4) & ((c >= 30) | (k >= 10)), np.clip(k / 243.0, 0, 1), 0)
    cs, rs = w.sum(0), w.sum(1)
    ax, ay = int(np.argmax(cs)), int(np.argmax(rs))
    yt = [cc + y0 for cc, t, n in _runs(w[:, ax - 12:ax - 3].sum(1)) if t >= 2 and cc <= ay + 1]
    xt = [cc + x0 for cc, t, n in _runs(w[ay + 3:ay + 10, :].sum(0)) if t >= 2 and n <= 4 and cc >= ax - 1]
    yt = sorted(yt, reverse=True)
    assert len(yt) == len(yvals) and len(xt) == 5, (yt, xt)
    py = np.polyfit(yt, yvals, 1)
    pxx = np.polyfit(xt, [0, 50, 100, 150, 200], 1)
    res_y = float(np.max(np.abs(np.polyval(py, yt) - yvals)))
    res_x = float(np.max(np.abs(np.polyval(pxx, xt) - [0, 50, 100, 150, 200])))
    # rows searched: from just above the top tick down to just above the x-axis line
    return dict(py=py, x0=-pxx[1] / pxx[0], sx=1 / pxx[0], yr=(int(min(yt)) - 8, int(round(ay + y0)) - 3), res_y=res_y, res_x=res_x,
                yticks=yt, xticks=xt)


# ---------- colours ----------
NAMES = list(COLOUR)
CVEC = np.array([COLOUR[k] for k in NAMES])


def mask(col, tol=36):
    return np.abs(A - COLOUR[col]).sum(-1) < tol


def prop_mask(col, cos_min=0.985, amin=0.3):
    """series colour blended with white (CMYK proportional to the colour) - thin anti-aliased error-bar caps"""
    c = COLOUR[col]
    cn = c / np.linalg.norm(c)
    proj = A @ cn
    return (proj / (np.linalg.norm(A, axis=-1) + 1e-9) >= cos_min) & (proj / np.linalg.norm(c) >= amin)


def classify(p):
    if p.sum() < 25:
        return ('bg', None)
    d = np.abs(CVEC - p).sum(1)
    j = int(np.argmin(d))
    if d[j] < 40:
        return ('col', NAMES[j])
    cos = (CVEC @ p) / (np.linalg.norm(CVEC, axis=1) * np.linalg.norm(p))
    j = int(np.argmax(cos))
    return ('blend', NAMES[j]) if cos[j] > 0.985 else ('mix', None)


# ---------- lines ----------
def column_runs(m, x, y0, y1):
    col = m[y0:y1, x]
    out, i = [], 0
    while i < len(col):
        if col[i]:
            j = i
            while j < len(col) and col[j]:
                j += 1
            out.append((i + y0, j - 1 + y0))
            i = j
        else:
            i += 1
    return out


def edge_points(col, zorder, xa, xb, yr):
    m = mask(col)
    z = zorder[col]
    pts = []

    def true_edge(y, x):
        k, c = classify(A[y, x])
        if k == 'bg':
            return True
        if k == 'blend':
            return c == col or zorder.get(c, 99) < z
        if k == 'col':
            return c != col and zorder.get(c, 99) < z
        return False
    for x in range(int(np.ceil(xa + MARGIN)), int(np.floor(xb - MARGIN)) + 1):
        for a, b in column_runs(m, x, *yr):
            pts.append((x, a, b, true_edge(a - 1, x), true_edge(b + 1, x)))
    return pts


def centres(pts, k=0.0):
    T = T0 * np.sqrt(1 + k * k)
    out = []
    for x, a, b, t, bt in pts:
        if t and bt and b - a + 1 >= T - 1.2:
            out.append((x, (a + b) / 2))
        elif t and not bt:
            out.append((x, a + (T - 1) / 2))
        elif bt and not t:
            out.append((x, b - (T - 1) / 2))
    return out


def ransac_line(pts, tol=1.0, minpts=4, trials=400, seed=0):
    P = np.array(pts, float).reshape(-1, 2)
    if len(P) < minpts:
        return None
    n = len(P)
    if n * (n - 1) // 2 <= trials:
        ia, ib = np.triu_indices(n, 1)
    else:
        rng = np.random.default_rng(seed)
        ia, ib = rng.integers(0, n, trials), rng.integers(0, n, trials)
    dx = P[ib, 0] - P[ia, 0]
    ok = np.abs(dx) >= 3
    ia, ib, dx = ia[ok], ib[ok], dx[ok]
    if len(ia) == 0:
        return None
    k = (P[ib, 1] - P[ia, 1]) / dx
    b = P[ia, 1] - k * P[ia, 0]
    res = np.abs(P[None, :, 1] - (k[:, None] * P[None, :, 0] + b[:, None]))
    cnt = (res <= tol).sum(1)
    j = int(np.argmax(cnt))
    if cnt[j] < minpts:
        return None
    inl = res[j] <= tol
    kk, bb = np.polyfit(P[inl, 0], P[inl, 1], 1)
    r = P[inl, 1] - (kk * P[inl, 0] + bb)
    return dict(k=kk, b=bb, xs=P[inl, 0], rms=float(np.sqrt(np.mean(r ** 2))))


def segment_line(col, zorder, xa, xb, yr):
    E = edge_points(col, zorder, xa, xb, yr)
    L = ransac_line(centres(E, 0.0))
    if L:                                   # second pass with the slope-corrected line thickness
        L = ransac_line(centres(E, L['k']))
    return L


def pred_se(L, x):
    xs = L['xs']
    s = max(L['rms'], 0.3)
    return s * np.sqrt(1 / len(xs) + (x - xs.mean()) ** 2 / np.sum((xs - xs.mean()) ** 2))


def cap_rows(pm, xc, y0, y1, offsets=(-4, -3, -2, 2, 3, 4)):
    rows = [y for y in range(y0, y1) if sum(1 for dx in offsets if pm[y, int(round(xc + dx))]) >= len(offsets) - 1]
    groups, cur = [], []
    for y in rows:
        if cur and y - cur[-1] > 1:
            groups.append(cur)
            cur = []
        cur.append(y)
    if cur:
        groups.append(cur)
    return [sum(g) / len(g) for g in groups]


# ---------- panel ----------
def read_panel(name):
    box, yvals, test, fig, series = PANELS[name]
    ax = axes(box, yvals)
    py, x0, sx, yr = ax['py'], ax['x0'], ax['sx'], ax['yr']
    val = lambda y: float(np.polyval(py, y))
    zorder = {c: i for i, (_, c) in enumerate(series)}
    out = []
    for mat, col in series:
        pm = prop_mask(col)
        segs = {}
        for da, db in zip(DOSES[:-1], DOSES[1:]):
            xa, xb = x0 + da * sx, x0 + db * sx
            if xb - xa - 2 * MARGIN >= 10:
                segs[(da, db)] = (xa, xb, segment_line(col, zorder, xa, xb, yr))
        for d in DOSES:
            xd = x0 + d * sx
            ests = []
            for (da, db), (xa, xb, L) in segs.items():
                if d in (da, db) and L:
                    se = pred_se(L, xd)
                    ests.append(dict(side='R' if d == da else 'L', y=L['k'] * xd + L['b'], se=se, n=len(L['xs']),
                                     rms=L['rms'], ok=len(L['xs']) >= 8 and se <= 0.8))
            good = [e for e in ests if e['ok']]
            v, status, conf, tentative = None, '', [], None
            if d <= 6.25:
                status = 'unreadable: doses <= 6.25 lie <= 17 px from the y axis, where the markers and error bars of 17 series overlap'
            elif not good:
                status = 'unreadable: the line of the series is hidden by series drawn later'
            else:
                y = None
                if len(good) == 2:
                    dif = abs(good[0]['y'] - good[1]['y'])
                    if dif * abs(py[0]) <= 0.75:
                        y = np.average([e['y'] for e in good], weights=[1 / e['se'] ** 2 for e in good])
                        conf.append('2 segments agree (difference %.2f units)' % (dif * abs(py[0])))
                    else:
                        status = 'unreadable: the segments disagree by %.2f units' % (dif * abs(py[0]))
                else:
                    y = good[0]['y']
                if y is not None:
                    caps = cap_rows(pm, xd, yr[0], yr[1] + 4)
                    pairs = [(a, b) for i, a in enumerate(caps) for b in caps[i + 1:] if abs((a + b) / 2 - y) <= 1.5 and b - a >= 2]
                    if pairs:
                        a, b = min(pairs, key=lambda p: abs((p[0] + p[1]) / 2 - y))
                        conf.append('error-bar caps %.1f/%.1f -> %.2f' % (val(a), val(b), val((a + b) / 2)))
                    if not conf and (good[0]['n'] < 12 or good[0]['se'] > 0.5):
                        tentative = round(val(y), 2)
                        status = 'rejected: weak reading (1 segment, n=%d, se=%.2f px, not confirmed)' % (good[0]['n'], good[0]['se'])
                    else:
                        v = val(y)
                        status = 'read' if conf else 'read (1 segment, not confirmed by error-bar caps)'
            out.append(dict(
                cell_line='BEAS-2B', test=test, figure=fig, material=mat, colour_on_figure=col, dose_ug_ml=NOM[d], dose_exact=d,
                value_on_figure=None if v is None else round(v, 2), unit='% ATP level' if test == 'ATP' else '% cell death',
                viability=None if v is None else round(v if test == 'ATP' else 100 - v, 1), status=status,
                confirmation='; '.join(conf), rejected_tentative_value=tentative,
                segments='; '.join('%s %.2f (n=%d, se=%.2f px, rms=%.2f%s)' % (e['side'], val(e['y']), e['n'], e['se'], e['rms'],
                                                                              '' if e['ok'] else ', rejected') for e in ests),
                px_per_unit=round(1 / abs(py[0]), 3), calibration_residual_y=round(ax['res_y'], 3),
                calibration_residual_x=round(ax['res_x'], 3)))
    return out


def main():
    rows = []
    for p in ('B_right', 'C_right', 'B_left', 'C_left'):
        rows += read_panel(p)
    OUT.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    with open(OUT / 'Zhang2012_Fig_2_BEAS-2B_readings.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n = sum(1 for r in rows if r['viability'] is not None)
    print(f'{len(rows)} BEAS-2B positions, {n} read')


if __name__ == '__main__':
    main()
