# Prompt for Claude Code

```
The folder inputs/ contains the PDF of Zhang et al., ACS Nano 2012, 6, 4349-4368 (doi 10.1021/nn3010087) and the PDF of its Supporting
Information. Figure 2B (ATP assay) and Figure 2C (LDH assay) of the paper show BEAS-2B cells; Figure S2B and Figure S2C of the Supporting
Information show RAW 264.7 cells. Each plot shows the response of metal oxide nanoparticles at ten doses (0.390625 to 200 ug/mL, two-fold
dilutions); the left-hand panels show the toxic materials and the right-hand panels the non-toxic ones.

Write Python scripts that read every plotted value exactly. Do not estimate any value by looking at the figure: every number must be computed
by the scripts from the PDF.

1. Find out how each figure is encoded in the PDF. Convert vector pages to SVG with pdftocairo and use the coordinates of the paths; extract
   embedded raster images with pdfimages, without resampling, and use their pixels.
2. Calibrate each axis by a least-squares fit through its tick marks and report the residuals.
3. Identify each series by its colour, marker and drawing order, and check the identification against the legend. Do not rely on the
   colour alone: the colour of a series on the plot does not always match its legend entry (in Fig. 2 of the paper the seventh series is
   drawn in yellow, although the legend shows another colour). Confirm the identity of every series by the shape of its markers, by the
   drawing order (series drawn later cover earlier ones) and, where possible, by values that are known independently.
4. Vector plots: take the midpoint between the two caps of each error bar (mean +/- SD); check it against the centre of the marker and against
   the extension of the line segments that connect the doses.
5. Raster plots: locate the pixels of each series' own colour between consecutive doses, fit a straight line to each segment robustly
   (RANSAC) and extend it to the dose. Accept a reading only when enough pixel columns support it and the extrapolation error is small, and
   confirm it with the neighbouring segment or with a symmetric pair of error-bar caps. Mark every dose that cannot be read reliably as
   unreadable instead of guessing a value.
6. Convert the readings to viability: ATP level in percent of the control; for LDH, 100 minus the percentage of cell death.
7. Validate the method on the left-hand panels: inputs/records_before_viability_check.csv gives the values of CoO, CuO, Mn2O3 and ZnO in the
   Nanopharos dataset. Report the mean and the maximum absolute difference for each figure.
8. Whenever a reading or the identity of a series is uncertain, do not decide alone and do not enter the value: publish an artifact (a
   review page) that shows the crop of the figure with the reading drawn on it, the candidate values and the reason for the doubt, and wait
   for the user's decision. Record each decision with its reason.
9. Write every reading with its figure, method and status to CSV files in results/, so that running the scripts again gives the same numbers.
```
