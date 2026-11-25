# Helper functions for data preparation.

library(dplyr)

#   - `Coat/Functional Group` -> `Coat` (the name used in the whole code);
#   - lower case only for the annotation vocabularies (organ, species, test); cell line names keep their case (A549, HaCaT, RAW 264.7);
#   - `Dataset` without the trailing space of "Labouta Et. Al. ".
load_analysis_data <- function(path) {
  d <- suppressWarnings(readxl::read_excel(path))
  if ("Coat/Functional Group" %in% names(d)) {
    d <- dplyr::rename(d, Coat = `Coat/Functional Group`)
  }
  for (col in c("Cell_organ", "Animal_mapped_combined", "Test")) d[[col]] <- tolower(d[[col]])
  d[["Dataset"]] <- trimws(d[["Dataset"]])
  d
}
