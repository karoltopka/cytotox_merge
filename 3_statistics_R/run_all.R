# Renders the analysis modules 01-04 (R Markdown) in order; the HTML reports, figures and tables go to the output folder of R/paths.R.
#   Rscript run_all.R            all modules
#   Rscript run_all.R 02 04      selected modules
# Needs pandoc (bundled with RStudio; otherwise on PATH).
args <- commandArgs(trailingOnly = TRUE)
here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))))
setwd(here)
source(file.path("R", "paths.R"))
dir.create(file.path(OUT, "reports"), recursive = TRUE, showWarnings = FALSE)
mods <- sort(list.files(".", pattern = "^0[1-4]_.*\\.Rmd$"))
only <- grep("^0[1-4]$", args, value = TRUE)
if (length(only)) mods <- mods[substr(mods, 1, 2) %in% only] else unlink(file.path(OUT, "key_numbers.csv"))   # full run: no numbers from older runs
for (m in mods) {
  t0 <- Sys.time()
  rmarkdown::render(m, output_dir = file.path(OUT, "reports"), intermediates_dir = tempdir(), knit_root_dir = here, envir = new.env(), quiet = TRUE)
  message(sprintf("%-28s %5.0f s", m, as.numeric(difftime(Sys.time(), t0, units = "secs"))))
}
