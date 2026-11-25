"""Paths and constants shared by the figure-reading scripts.

inputs/  the publication PDFs (not distributed: download them from the publishers and save them under these names) and the dataset
         records of these publications as they enter the viability check of the pipeline (records_before_viability_check.csv)
results/ readings and validations written by the scripts; work/ intermediate SVG and image files
"""
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS, WORK, OUT = HERE / "inputs", HERE / "work", HERE / "results"
PDF_ZHANG = INPUTS / "10.1021_nn3010087.pdf"             # Zhang et al., ACS Nano 2012, 6, 4349-4368
PDF_ZHANG_SI = INPUTS / "10.1021_nn3010087_SI.pdf"       # its Supporting Information
RECORDS = INPUTS / "records_before_viability_check.csv"

# two-fold dilution series of Zhang et al. (ug/mL) and the value stored in the dataset column 'Concentration (ug/ml)'
DOSES = [0.390625, 0.78125, 1.5625, 3.125, 6.25, 12.5, 25, 50, 100, 200]
NOM = {0.390625: 0.4, 0.78125: 0.8, 1.5625: 1.6, 3.125: 3.2, 6.25: 6.3, 12.5: 12.5, 25: 25, 50: 50, 100: 100, 200: 200}

# legend order of the panels (= drawing order of the series)
RIGHT = ['Al2O3', 'CeO2', 'Fe2O3', 'Fe3O4', 'Gd2O3', 'HfO2', 'In2O3', 'NiO', 'SiO2', 'SnO2', 'TiO2', 'WO3', 'Y2O3',
         'Yb2O3', 'ZrO2', 'La2O3', 'Sb2O3']
LEFT = ['Co3O4', 'Cr2O3', 'Ni2O3', 'CuO', 'Mn2O3', 'CoO', 'ZnO']


def si_svg(page):
    """page of the Supporting Information converted to SVG (vector paths keep their exact coordinates)"""
    f = WORK / f"si_p{page}.svg"
    if not f.exists():
        WORK.mkdir(exist_ok=True)
        subprocess.run(["pdftocairo", "-svg", "-f", str(page), "-l", str(page), str(PDF_ZHANG_SI), str(f)], check=True)
    return f


def fig2_tiff():
    """native raster of Fig. 2 of the paper (page 5, 1635 x 2439 px CMYK, 300 ppi, lossless)"""
    f = WORK / "fig2-000.tif"
    if not f.exists():
        WORK.mkdir(exist_ok=True)
        subprocess.run(["pdfimages", "-f", "5", "-l", "5", "-tiff", str(PDF_ZHANG), str(WORK / "fig2")], check=True)
    return f
