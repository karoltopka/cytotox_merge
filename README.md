# Merging Cytotoxicity Data of Inorganic Nanomaterials – code and data

This repository holds the data integration pipeline, the analysis code and the final dataset of a study that merges three published
collections of in vitro cytotoxicity data on nanomaterials into one dataset. The pipeline brings the three sources to a common schema,
restricts them to a defined scope (spherical inorganic nanomaterials, mammalian cell models, viability 0–200 %), harmonises every variable
and verifies every value against the publication it comes from. The analyses describe the merged dataset (PCA and t-SNE of the particle
descriptors, viability by nanomaterial, cell line and organ, mixed-effects models) and the compatibility of the viability assays.

The repository splits into 4 parts:

| folder               | content                                                                                                     |
| -------------------- | ----------------------------------------------------------------------------------------------------------- |
| `1_pipeline`       | the data-integration pipeline, one folder per step (S01–S24), the three source files and the final dataset |
| `2_figure_reading` | Example of values reading from published figures (Zhang Et. Al)                                             |
| `3_statistics_R`   | R analyses of the final dataset: figures, tables                                                            |
| `4_notebooks`      | Python notebooks: compatibility matrix of the viability assays and the examples of divergent assays         |

## Data

### Source data (`1_pipeline/00_source_data`)

| file                            | source                                                                                                                                          |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `Nano_2021_dataset_raw.xlsx`  | Gul G., Yildirim R., Ileri-Ercan N.,*Environ. Sci.: Nano* 2021, 8, 937–949, doi [10.1039/D0EN01240H](https://doi.org/10.1039/D0EN01240H)      |
| `NanoPharos_dataset_raw.xlsx` | NovaMechanics, Cytotoxicity data for 14 metal oxide nanoparticles, Zenodo, doi[10.5281/zenodo.14863537](https://doi.org/10.5281/zenodo.14863537) |
| `nn8b07562_si_001.xlsx`       | Labouta H.I. et al.,*ACS Nano* 2019, Supporting Information, doi [10.1021/acsnano.8b07562](https://doi.org/10.1021/acsnano.8b07562)            |

### Final dataset (`1_pipeline/Final_dataset/dataset_final.xlsx`)

2862 records from 103 publications, one record per nanomaterial × cell line × concentration × exposure time × assay. Every record keeps
its identifier in the source file (`raw_id`: G = Gul et al., L = Labouta et al., P = NanoPharos). The columns describe the nanomaterial
(material, coating, synthesis, surface charge, dry diameter with its origin and measuring technique, hydrodynamic diameters and zeta
potentials in water, culture medium and other dispersants), the cell model (cell line, tumour status, organ, cell-type family, germ layer,
species), the exposure (cells per well, time, concentration in µg/mL, g/L and µM, serum status of the medium), the assay (name, family,
readout) and the response (cell viability, %). Three comment columns give the statements of the publications behind.

### Pipeline

Every step folder of `1_pipeline` holds the table after the step (`S*.xlsx`), the comments of the step (`S*_comments.xlsx`: every
decision taken on the strength of a publication, with the record, the variable, the new value or the removal and the reason with the
quotation or the place in the publication) and the audit of the step (`S*_audit.xlsx`: every changed cell with its kind of change, old
and new value and comment; every removed record with its comment). `00_steps_index.xlsx` gives the number of records after each step andthe numbers of harmonised, corrected and added cells.

### Data contact

* **Karol Topka Kłończyński - <karol.topkaklonczynski@phdstud.ug.edu.pl>**
* **Tomasz Puzyn - <tomasz.puzyn@ug.edu.pl>**

## Getting started

The parts run in this order; each one reads the output of the previous one.

1. **Pipeline** – run the notebooks of `1_pipeline` in the order of the steps: `S01_*/code/S01.ipynb` reads `00_source_data`, every
   later step reads the table of the previous step, and `Final_dataset/code/Final_dataset.ipynb` writes `Final_dataset/dataset_final.xlsx`.
   Each notebook applies the coded rules of its step. The repository already contains the outputof every step, so the analyses can be run without 
   rerunning the pipeline.
2. **R analyses** – `Rscript 3_statistics_R/run_all.R` renders the four R Markdown modules in order (`run_all.R 02 04` renders selected
   modules); figures, tables, are written to `3_statistics_R/results`. The input path is set in `3_statistics_R/R/paths.R`.
3. **Notebooks** – run `4_notebooks/01_test_compatibility_matrix_Figure3.ipynb` and `4_notebooks/02_table1_assay_discrepancies.ipynb`
   (Jupyter); outputs in `4_notebooks/results`.
4. **Values read from figures** (optional) – the values that `2_figure_reading` reads from the figures of Zhang et al. 2012 are already part
   of the comments table of step S22, so the pipeline runs without this part. To reproduce the reading, download the publication and its
   Supporting Information into `2_figure_reading/inputs` under the names given in `2_figure_reading/README.md` and run the scripts in the
   order given there.

What each part produces:

| output                                                                                                                 | produced by                                    |
| ---------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| final dataset, records after each step, removed records, changed values                                                | `1_pipeline`                                 |
| Figure 1, Figures S1–S2                                                                                               | `3_statistics_R/02_eda_dimreduction.Rmd`     |
| Figure 2, Figure S3, Figures S6–S8                                                                                    | `3_statistics_R/03_visualizations.Rmd`       |
| Figures S4, S5 and S9, Tables S6, S7 and S7.1                                                                          | `3_statistics_R/04_statistical_analysis.Rmd` |
| Figure 3 (assay compatibility matrix, with sensitivity analysis), Table 1 (pairs of assays under identical conditions) | `4_notebooks`                                |
| values read from the figures of Zhang et al. 2012 and the validation of the reading                                    | `2_figure_reading`                           |

## Requirements

**Python 3.10** (pipeline notebooks, figure reading, notebooks)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # numpy, pandas, openpyxl, matplotlib, Pillow, ipykernel (versions pinned)
pip install jupyter                    # to open and run the notebooks
```

**R 4.4.3** (analyses)

The packages and the versions used are listed, with their citations, in `3_statistics_R/results/tables/package_versions.csv`
`run_all.R` also needs `rmarkdown` to render the modules. Install them with `install.packages()`. `rmarkdown::render` needs
**pandoc ≥ 2.8** on the `PATH`.

**Poppler** (`pdftocairo`, `pdfimages`; version 22.02 used) – only for `2_figure_reading`.

## Publications

* Gul G., Yildirim R., Ileri-Ercan N.,*Environ. Sci.: Nano* 2021, 8, 937–949, doi [10.1039/D0EN01240H](https://doi.org/10.1039/D0EN01240H)
* NovaMechanics, Cytotoxicity data for 14 metal oxide nanoparticles, Zenodo, doi[10.5281/zenodo.14863537](https://doi.org/10.5281/zenodo.14863537)
* Labouta H.I. et al.,*ACS Nano* 2019, Supporting Information, doi [10.1021/acsnano.8b07562](https://doi.org/10.1021/acsnano.8b07562)

## Contributing

* Report problems and propose changes through the issues and pull requests of the repository.

## Notes

## Authors

* **Karol Topka Kłończyński** – *conceptualization, investigation, methodology, formal analysis, visualization, writing-original draft*
* **Krzesimir Ciura** – *conceptualization, edition of the manuscript*
* **Maciej Stępnik** – *supervision, edition of the manuscript*
* **Tomasz Puzyn** – *conceptualization, supervision, edition of the manuscript*

## License

* 

## Acknowledgments

*
