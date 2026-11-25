# Helpers for the colour gradient inside the violin plots

library(dplyr)

# Polygon data of the gradient of one violin
create_violin_gradient <- function(data, n_slices = 500) {
  # cut = 0: do not extend the density beyond the real range of the data
  vals <- data$`Cell_Viability (%)`
  dens <- density(vals, na.rm = TRUE, cut = 0)
  x_seq <- seq(min(vals, na.rm = TRUE), max(vals, na.rm = TRUE),
               length.out = n_slices)

  dens_fun <- approxfun(dens$x, dens$y, yleft = 0, yright = 0)
  density_values <- dens_fun(x_seq)
  normalized_widths <- (density_values / max(dens$y)) * 0.995

  polygon_data <- data.frame()

  for(i in 1:(length(x_seq) - 1)) {
    x_width <- x_seq[i+1] - x_seq[i]
    overlap <- x_width * 0.1  # overlap of the slices, so that no white lines appear between them

    slice <- data.frame(
      x = c(x_seq[i] - overlap, x_seq[i+1] + overlap,
            x_seq[i+1] + overlap, x_seq[i] - overlap),
      y_rel = c(-normalized_widths[i], -normalized_widths[i+1],
                normalized_widths[i+1], normalized_widths[i]),
      fill_value = mean(c(x_seq[i], x_seq[i+1])),
      slice_id = i
    )
    polygon_data <- rbind(polygon_data, slice)
  }

  return(polygon_data)
}

# Gradient data for all categories
prepare_gradient_data <- function(data_labelled, category_col, width_scale = 0.445) {
  all_gradient_data <- data.frame()
  category_levels <- levels(data_labelled[[category_col]])

  for(i in seq_along(category_levels)) {
    category <- category_levels[i]
    subset_data <- data_labelled %>% filter(.data[[category_col]] == category)

    if(nrow(subset_data) <= 2) next

    gradient_data <- create_violin_gradient(subset_data)
    gradient_data[[category_col]] <- category
    gradient_data$y_position <- i

    all_gradient_data <- rbind(all_gradient_data, gradient_data)
  }

  all_gradient_data <- all_gradient_data %>%
    mutate(
      y_abs = y_position + y_rel * width_scale,
      polygon_id = paste0(.data[[category_col]], "_", slice_id)
    )

  return(all_gradient_data)
}

# One gradient violin plot for every categorical figure (modules 03 and 04, one style for all of them). Categories with fewer than
# min_n records are dropped, the labels carry the share of the shown records, the categories are
# ordered by that share (largest on top), the dot marks the mean and the "Mean:" annotation repeats it with one decimal.
gradient_violin <- function(data, category_col, plot_title, min_n = 10, viab = "Cell_Viability (%)") {
  data <- data %>% filter(!is.na(.data[[category_col]]), !is.na(.data[[viab]]))
  keep_levels <- data %>% count(.data[[category_col]]) %>% filter(n >= min_n) %>% pull(1)
  data <- data %>% filter(.data[[category_col]] %in% keep_levels)
  if (!nrow(data)) return(NULL)
  counts <- data %>% count(.data[[category_col]], name = "n_cat") %>% mutate(percent = 100 * n_cat / sum(n_cat)) %>% arrange(desc(percent))
  data <- data %>% left_join(counts, by = category_col) %>% mutate(Category_label = paste0(.data[[category_col]], " (", round(percent, 1), "%)"))
  lab_order <- data %>% distinct(.data[[category_col]], Category_label) %>% arrange(match(.data[[category_col]], counts[[1]])) %>% pull(Category_label)
  data$Category_label <- factor(data$Category_label, levels = rev(lab_order))
  grad <- prepare_gradient_data(data, "Category_label")
  st <- data %>% group_by(Category_label) %>% summarise(mean_viab = mean(.data[[viab]]), .groups = "drop") %>% mutate(y = as.numeric(Category_label))
  mx <- max(data[[viab]])
  ggplot() +
    geom_polygon(data = grad, aes(x = x, y = y_abs, group = polygon_id, fill = fill_value), color = NA) +
    geom_violin(data = data, aes(x = .data[[viab]], y = as.numeric(Category_label), group = Category_label), trim = TRUE, fill = NA,
                color = "black", linewidth = 0.8, scale = "width") +
    geom_point(data = st, aes(x = mean_viab, y = y), size = 1.2) +
    geom_text(data = st, aes(x = mx * 1.04, y = y, label = sprintf("Mean: %5.1f", mean_viab)), hjust = 0, size = 4, fontface = "bold", family = "mono") +
    scale_fill_viridis_c(name = "Viability (%)") +
    scale_y_continuous(breaks = seq_along(levels(data$Category_label)), labels = levels(data$Category_label),
                       limits = c(0.5, length(levels(data$Category_label)) + 0.5)) +
    scale_x_continuous(breaks = seq(0, 200, by = 25)) + coord_cartesian(xlim = c(0, mx * 1.35)) +
    theme_minimal(base_size = 13) + labs(y = NULL, x = "Viability (%)", title = plot_title) +
    theme(axis.text.y = element_text(size = 12)) + theme_uniform
}

# Violins that describe the composition of the data (Figure S9, species and organ): one violin per group with at least min_n
# records, the records as points coloured by the log10 mass concentration (grey: no mass concentration), the median as a black bar. The
# label of a group gives its numbers of cell lines and publications, because a group of one or two cell lines cannot stand for a species
# or an organ.
composition_violin <- function(data, category_col, panel_title, min_n = 10, viab = "Cell_Viability (%)") {
  d <- data %>% filter(!is.na(.data[[category_col]]), !is.na(.data[[viab]])) %>%
    mutate(grp = .data[[category_col]], conc = suppressWarnings(as.numeric(`Concentration (ug/ml)`)), lconc = ifelse(conc > 0, log10(conc), NA))
  st <- d %>% group_by(grp) %>%
    summarise(n = n(), lines = n_distinct(Cell_Type), pubs = n_distinct(tolower(DOI)), med = median(.data[[viab]]), .groups = "drop") %>%
    filter(n >= min_n) %>% arrange(n) %>%
    mutate(y = row_number(), label = sprintf("%s (%d %s, %d publ.)", grp, lines, ifelse(lines == 1, "line", "lines"), pubs))
  d <- d %>% inner_join(st %>% select(grp, y), by = "grp")
  mx <- max(d[[viab]])
  ggplot(d) +
    geom_violin(aes(x = .data[[viab]], y = y, group = y), fill = "grey93", color = "grey35", linewidth = 0.4, scale = "width", trim = TRUE,
                width = 0.85, orientation = "y") +
    geom_point(aes(x = .data[[viab]], y = y, color = lconc), size = 0.45, alpha = 0.6,
               position = position_jitter(width = 0, height = 0.28, seed = 1)) +
    geom_segment(data = st, aes(x = med, xend = med, y = y - 0.4, yend = y + 0.4), linewidth = 1.1) +
    geom_text(data = st, aes(x = mx * 1.03, y = y, label = sprintf("n = %d, median %.1f", n, med)), hjust = 0, size = 3.4) +
    scale_color_viridis_c(name = "log10 mass\nconcentration\n(µg/mL)", na.value = "grey65") +
    scale_y_continuous(breaks = st$y, labels = st$label, expand = expansion(add = 0.6)) +
    scale_x_continuous(breaks = seq(0, 200, by = 25)) + coord_cartesian(xlim = c(0, mx * 1.3)) +
    theme_minimal(base_size = 12) + labs(x = "Viability (%)", y = NULL, title = panel_title) + theme_uniform +
    theme(plot.title = element_text(hjust = 0), axis.text.y = element_text(size = 10.5))
}
