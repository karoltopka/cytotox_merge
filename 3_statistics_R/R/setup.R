suppressPackageStartupMessages({
  library(dplyr); library(stringr); library(forcats)
  library(ggplot2); library(patchwork); library(cowplot); library(ggh4x); library(ggrepel)
  library(readxl)
  library(effsize); library(car); library(lme4); library(pbkrtest); library(emmeans)
  library(Rtsne)
})

source(file.path("R", "paths.R"), local = TRUE)
for (sub in c("figures", "tables", "reports")) dir.create(file.path(OUT, sub), recursive = TRUE, showWarnings = FALSE)
out <- function(...) file.path(OUT, ...)

source(file.path("R", "data_prep_utils.R"), local = TRUE)
source(file.path("R", "violin_gradient_utils.R"), local = TRUE)

# every module loads the data itself, so no module sees data changed by another module
final_data <- load_analysis_data(DATA_FILE)
stopifnot(all(final_data[["Cell_Viability (%)"]] >= 0 & final_data[["Cell_Viability (%)"]] <= 200, na.rm = TRUE))   # viability 0-200 %, never clipped to 100
DIAM <- "Dry_Diameter (nm)"   # primary-particle (dry, microscopy) diameter


message(nrow(final_data), " records | outputs: ", normalizePath(OUT))

# readable names of the dataset columns for plot titles and axis labels
VAR_LABEL <- c("Animal_mapped_combined" = "species", "Cell_organ" = "organ of origin", "Cell_Type" = "cell line", "Test" = "viability assay",
               "Coat" = "coating", "Cancer" = "cancer status", "Material" = "nanomaterial", "Time (hr)" = "exposure time (h)",
               "Dry_Diameter (nm)" = "dry diameter (nm)", "Zeta_in_Water (mV)" = "zeta potential in water (mV)",
               "Concentration (g/l)2" = "mass concentration (g/L)", "Cell_Viability (%)" = "viability (%)")
var_label <- function(x, capital = FALSE) {
  l <- ifelse(x %in% names(VAR_LABEL), VAR_LABEL[x], x)
  if (capital) l <- sub("^(.)", "\\U\\1", l, perl = TRUE)
  unname(l)
}


theme_uniform <- theme(plot.title = element_text(face = "bold", hjust = 0.5), axis.title = element_text(face = "bold"),
                       legend.title = element_text(face = "bold"), axis.text = element_text(face = "plain"), strip.text = element_text(face = "bold"))
