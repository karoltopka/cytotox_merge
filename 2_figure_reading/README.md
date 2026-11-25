# Values read from published figures

| file                                   | content                                                                                                                   |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `10.1021_nn3010087.pdf`              | Zhang H. et al., ACS Nano 2012, 6, 4349–4368 (Fig. 2: BEAS-2B)                                                           |
| `10.1021_nn3010087_SI.pdf`           | its Supporting Information (Fig. S2: RAW 264.7)                                                                           |
| `records_before_viability_check.csv` | the dataset records of the publications read here, as they enter the viability check of the pipeline (output of step S21) |

The PDF files are not distributed with the code (copyright of the publishers); download them using the DOIs and save them under these names.

## Zhang et al. 2012 (Nanopharos source)

In the Nanopharos source, the 378 records of the ten non-toxic oxides (Al2O3, CeO2, Fe2O3, Gd2O3, HfO2, In2O3, La2O3, NiO, Sb2O3, SiO2) carry
integer values between 80 and 99 that do not depend on the dose and contradict the published figures. Their values were read from the
right-hand panels of the figures; the left-hand panels show the four toxic oxides (CoO, CuO, Mn2O3, ZnO), whose values the Nanopharos source
gives, and the same readings of these panels validate the method.

**RAW 264.7, SI Fig. S2B (ATP) and S2C (LDH), vector graphics** – `read_Zhang2012_SI_Fig_S2_RAW264_7.py`

1. SI pages 4 and 5 are converted to SVG (`pdftocairo -svg`); every line segment, marker and error bar is a separate path with exact coordinates.
2. Axis calibration: least-squares line through the tick marks (largest tick deviation ≤ 0.04 pt).
3. Series: every series has one block of 40 error-bar paths (10 doses × upper bar, upper cap, lower bar, lower cap), drawn in legend order
   after all lines and markers; the order of the colours was checked against the legend lines.
4. Value = midpoint between the two caps of the error bar (mean ± SD); when a cap is clipped by the axis, the end of the bar is used.
5. Independent checks: the centre of the marker (constant shape offset; median spread within a series 0.07 units) and the extension of the
   straight segments that connect the doses (median difference 0.03 units).

**BEAS-2B, Fig. 2B (ATP) and 2C (LDH), raster image (300 ppi, lossless CMYK)** – `read_Zhang2012_Fig_2_BEAS_2B.py`

1. The embedded image is extracted without resampling (`pdfimages -tiff`); every series has its own exact CMYK colour.
2. Axis calibration: centroids of the tick marks, linear fit (tick deviation ≤ 0.07 px).
3. The line of a series is located in the pixel columns between two doses (7 px away from the markers), from the full width of the series
   colour or, where a later series is drawn over it, from its uncovered edge plus half the line width.
4. Value: robust straight-line fit (RANSAC) of each segment, extended to the dose; the weighted mean when both neighbouring segments exist.
5. Acceptance: at least 8 columns and an extrapolation error ≤ 0.8 px, two segments agreeing within 0.75 units, and ≥ 12 columns with an error
   ≤ 0.5 px for a single unconfirmed segment. Confirmation by a symmetric pair of error-bar caps of the series colour or by the agreement of the
   two neighbouring segments.
6. Not readable: all doses ≤ 6.25 µg/mL (within 17 px of the y axis, where the markers and error bars of 17 series overlap) and 20 points at
   higher doses whose line is hidden by series drawn later; five weak readings were rejected. These 120 records are removed from the dataset.
7. Colours: Fig. 2 draws the seventh series (In2O3; ZnO in the left-hand panel) in yellow, although the legend shows another colour. The
   assignment was confirmed by the marker shapes on the yellow line and by the drawing order, in which later series cover earlier ones.
   The vector plots of the Supporting Information are read in legend order and do not depend on the colours.

**Result and validation** – `Zhang2012_values_and_validation.py`

| cell line       | assay | figure               |                read |  not readable |    rejected |
| --------------- | ----- | -------------------- | ------------------: | ------------: | ----------: |
| RAW 264.7       | ATP   | SI Fig. S2B (vector) |             96 / 96 |             0 |           0 |
| RAW 264.7       | LDH   | SI Fig. S2C (vector) |             96 / 96 |             0 |           0 |
| BEAS-2B         | ATP   | Fig. 2B (raster)     |             38 / 92 |            52 |           2 |
| BEAS-2B         | LDH   | Fig. 2C (raster)     |             28 / 94 |            63 |           3 |
| **total** |       |                      | **258 / 378** | **115** | **5** |

Validation on the toxic oxides of the same figures (`results/Zhang2012_validation_toxic_oxides.csv`; Figure S3 of the Supplementary
Materials, drawn by `validation_figure.py`):

| cell line          | values | mean\|reading − Nanopharos\| |     max |
| ------------------ | -----: | ----------------------------: | ------: |
| RAW 264.7 (vector) |     59 |                       0.16 pp | 0.50 pp |
| BEAS-2B (raster)   |     39 |                       0.09 pp | 0.40 pp |

Conversion to viability: ATP, % ATP level = viability; LDH, viability = 100 − % cell death. Doses 0.390625–200 µg/mL (two-fold dilutions),
stored in the dataset as 0.4, 0.8, 1.6, 3.2, 6.3, 12.5, 25, 50, 100 and 200.

## Running

```bash
python3 read_Zhang2012_SI_Fig_S2_RAW264_7.py   # ~1 s
python3 read_Zhang2012_Fig_2_BEAS_2B.py        # ~30 s
python3 Zhang2012_values_and_validation.py
python3 validation_figure.py
```

Requirements: Python 3 with numpy, pandas, Pillow and matplotlib; poppler-utils (`pdftocairo`, `pdfimages`). Intermediate files (SVG,
TIFF, PNG) are written to `work/`.

The scripts were written with Claude Code 2.1.286 (Anthropic) and the model Claude Opus 5.5, with the publication PDFs stored on the local
computer; `PROMPT.md` describes the task for Claude Code. The scripts compute every value from the PDF files; no value was estimated by
the model.
