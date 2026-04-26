#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(cloneid)
  library(DBI)
  library(jsonlite)
})

`%||%` <- function(x, y) {
  if (is.null(x) || length(x) == 0 || identical(x, "")) y else x
}

parse_args <- function(args) {
  out <- list(mode = "auto", output = NULL, run_id = NULL)
  i <- 1
  while (i <= length(args)) {
    arg <- args[[i]]
    if (arg == "--mode") {
      i <- i + 1
      out$mode <- args[[i]]
    } else if (arg == "--output") {
      i <- i + 1
      out$output <- args[[i]]
    } else if (arg == "--run-id") {
      i <- i + 1
      out$run_id <- args[[i]]
    } else {
      stop(sprintf("Unknown argument: %s", arg))
    }
    i <- i + 1
  }
  if (!out$mode %in% c("auto", "live", "mock")) {
    stop("--mode must be one of: auto, live, mock")
  }
  out
}

timestamp_utc <- function() {
  format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
}

default_run_id <- function() {
  format(Sys.time(), "inventory_%Y%m%dT%H%M%S", tz = "UTC")
}

as_records <- function(df) {
  if (is.null(df) || nrow(df) == 0) {
    return(list())
  }
  fromJSON(toJSON(df, dataframe = "rows", auto_unbox = TRUE, na = "null"))
}

named_vector_to_records <- function(vec, value_name = "count") {
  if (length(vec) == 0) {
    return(list())
  }
  df <- data.frame(name = names(vec), value = as.vector(vec), row.names = NULL)
  names(df) <- c("name", value_name)
  as_records(df)
}

resolve_output_dir <- function(output, run_id) {
  if (!is.null(output)) {
    return(output)
  }
  file.path("runs", run_id %||% default_run_id())
}

mock_inventory_template <- function(run_id, requested_mode, live_error = NULL) {
  table_names <- c(
    "CellLinesAndPatients",
    "CellSurfaceMarkers_hg19",
    "Crypgene_LiquidNitrogenBackup",
    "Flask",
    "FlowCytometry",
    "Identity",
    "IdentitySub",
    "LiquidNitrogen",
    "Loci",
    "Media",
    "MediaIngredients",
    "Minus80Freezer",
    "Passaging",
    "Passaging_backup_2025_10_09",
    "Perspective",
    "PerspectivePartial",
    "QuPathEvaluation",
    "ToDelete_MorphologyPerspective"
  )

  row_counts <- c(
    CellLinesAndPatients = 220,
    CellSurfaceMarkers_hg19 = 4267,
    Crypgene_LiquidNitrogenBackup = 13,
    Flask = 22,
    FlowCytometry = 41,
    Identity = 87,
    IdentitySub = 9,
    LiquidNitrogen = 7371,
    Loci = 198,
    Media = 108,
    MediaIngredients = 70,
    Minus80Freezer = 810,
    Passaging = 11917,
    Passaging_backup_2025_10_09 = 11524,
    Perspective = 187925,
    PerspectivePartial = 264004,
    QuPathEvaluation = 5124,
    ToDelete_MorphologyPerspective = 257940
  )

  fields <- list(
    Passaging = c(
      "id", "cellLine", "event", "passaged_from_id1", "passaged_from_id2",
      "growthType", "passage", "cellCount", "date", "comment", "media",
      "flask", "correctedCount", "areaOccupied_um2", "cellSize_um2"
    ),
    QuPathEvaluation = c(
      "id", "cellLine", "event", "passaged_from_id1", "passaged_from_id2",
      "growthType", "passage", "cellCount", "date", "comment", "media",
      "flask", "cellCount_brightnessCorrection", "cellCount_brightnessCorrection2",
      "cellCount_standard", "cellCount_cellpose", "cellCount_cellpose_g65",
      "cellCount_cellpose_flowThresh80", "cellCount_QCmetrics"
    ),
    Perspective = c(
      "whichPerspective", "size", "parent", "profile", "profile_hash", "origin",
      "sampleSource", "coordinates", "rootID", "cloneID", "profile_loci",
      "state", "alias", "hasChildren"
    ),
    Identity = c(
      "size", "whichPerspective", "rootID", "sampleSource", "cloneID", "parent",
      "KaryotypePerspective", "GenomePerspective", "ExomePerspective",
      "TranscriptomePerspective", "coordinates", "profile_loci", "state",
      "alias", "hasChildren"
    ),
    CellLinesAndPatients = c("name", "doublingTime_hours", "year_of_first_report", "whichType", "source"),
    Flask = c("id", "dishSurfaceArea_cm2", "surface_treated_type", "bottom_shape"),
    Media = c(
      "id", "base1", "base1_pct", "base2", "base2_pct", "FBS", "FBS_pct",
      "EnergySource", "EnergySource_nM", "EnergySource2", "EnergySource2_pct",
      "Stressor", "Stressor_concentration", "Stressor_unit", "oxygen_pct", "comment"
    ),
    MediaIngredients = c("name", "vendor", "catalogue_number", "reference_number", "description")
  )

  summary_note <- "Mock inventory derived from previously inspected live schema metadata."
  warnings <- c("Mock mode uses cached schema/table observations and does not query the live database.")
  if (!is.null(live_error)) {
    warnings <- c(warnings, paste("Live access failed and mock mode was used instead:", live_error))
  }

  list(
    run_id = run_id,
    generated_at = timestamp_utc(),
    requested_mode = requested_mode,
    mode_used = "mock",
    status = if (is.null(live_error)) "ok" else "degraded",
    live_access = list(
      attempted = requested_mode != "mock",
      success = FALSE,
      error = live_error
    ),
    database = list(
      source = "cloneid R package",
      connection_method = "cloneid::connect2DB()",
      database_name = NULL
    ),
    tables = table_names,
    table_count = length(table_names),
    row_counts = as_records(
      data.frame(
        table = names(row_counts),
        row_count = as.integer(unname(row_counts)),
        row.names = NULL
      )
    ),
    fields = fields,
    key_table_summaries = list(
      Passaging = list(
        row_count = unname(row_counts["Passaging"]),
        important_fields = fields$Passaging,
        note = summary_note
      ),
      QuPathEvaluation = list(
        row_count = unname(row_counts["QuPathEvaluation"]),
        important_fields = fields$QuPathEvaluation,
        note = summary_note
      ),
      Perspective = list(
        row_count = unname(row_counts["Perspective"]),
        important_fields = fields$Perspective,
        note = summary_note
      ),
      Identity = list(
        row_count = unname(row_counts["Identity"]),
        important_fields = fields$Identity,
        note = summary_note
      ),
      CellLinesAndPatients = list(
        row_count = unname(row_counts["CellLinesAndPatients"]),
        important_fields = fields$CellLinesAndPatients,
        note = summary_note
      ),
      Flask = list(
        row_count = unname(row_counts["Flask"]),
        important_fields = fields$Flask,
        note = summary_note
      ),
      Media = list(
        row_count = unname(row_counts["Media"]),
        important_fields = fields$Media,
        note = summary_note
      ),
      MediaIngredients = list(
        row_count = unname(row_counts["MediaIngredients"]),
        important_fields = fields$MediaIngredients,
        note = summary_note
      )
    ),
    queries = list(),
    warnings = as.list(warnings)
  )
}

scalar_query <- function(con, sql) {
  df <- dbGetQuery(con, sql)
  if (nrow(df) == 0 || ncol(df) == 0) {
    return(NULL)
  }
  df[[1]][[1]]
}

table_summary_records <- function(con, table, column, limit = 20) {
  sql <- sprintf(
    "SELECT `%s` AS value, COUNT(*) AS n FROM `%s` WHERE `%s` IS NOT NULL GROUP BY `%s` ORDER BY n DESC LIMIT %d",
    column, table, column, column, limit
  )
  as_records(dbGetQuery(con, sql))
}

nonnull_count <- function(con, table, column) {
  sql <- sprintf("SELECT COUNT(*) AS n FROM `%s` WHERE `%s` IS NOT NULL", table, column)
  as.integer(scalar_query(con, sql))
}

build_live_inventory <- function(run_id, requested_mode) {
  if (identical(Sys.getenv("CLONEID_AGENT_FORCE_LIVE_ERROR"), "1")) {
    stop("Forced live error via CLONEID_AGENT_FORCE_LIVE_ERROR=1")
  }

  con <- connect2DB()
  on.exit(dbDisconnect(con), add = TRUE)

  tables <- dbListTables(con)
  row_count_records <- lapply(tables, function(tbl) {
    data.frame(
      table = tbl,
      row_count = as.integer(scalar_query(con, sprintf("SELECT COUNT(*) AS n FROM `%s`", tbl))),
      row.names = NULL
    )
  })
  row_counts_df <- do.call(rbind, row_count_records)

  fields <- stats::setNames(lapply(tables, function(tbl) dbListFields(con, tbl)), tables)
  database_name <- scalar_query(con, "SELECT DATABASE() AS database_name")

  queries <- list(
    list(name = "list_tables", sql = "DBI::dbListTables(con)"),
    list(name = "list_fields", sql = "DBI::dbListFields(con, <table>)"),
    list(name = "row_counts", sql = "SELECT COUNT(*) AS n FROM `<table>`")
  )

  passaging_summary <- list(
    row_count = as.integer(row_counts_df$row_count[row_counts_df$table == "Passaging"]),
    distinct_cell_lines = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT cellLine) AS n FROM `Passaging`")),
    distinct_growth_types = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT growthType) AS n FROM `Passaging`")),
    date_min = scalar_query(con, "SELECT MIN(date) AS value FROM `Passaging`"),
    date_max = scalar_query(con, "SELECT MAX(date) AS value FROM `Passaging`"),
    event_counts = as_records(dbGetQuery(con, "SELECT event, COUNT(*) AS n FROM `Passaging` GROUP BY event ORDER BY n DESC")),
    nonnull_counts = list(
      correctedCount = nonnull_count(con, "Passaging", "correctedCount"),
      areaOccupied_um2 = nonnull_count(con, "Passaging", "areaOccupied_um2"),
      cellSize_um2 = nonnull_count(con, "Passaging", "cellSize_um2")
    ),
    top_growth_types = table_summary_records(con, "Passaging", "growthType")
  )

  qupath_summary <- list(
    row_count = as.integer(row_counts_df$row_count[row_counts_df$table == "QuPathEvaluation"]),
    distinct_cell_lines = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT cellLine) AS n FROM `QuPathEvaluation`")),
    nonnull_counts = list(
      cellCount_brightnessCorrection = nonnull_count(con, "QuPathEvaluation", "cellCount_brightnessCorrection"),
      cellCount_brightnessCorrection2 = nonnull_count(con, "QuPathEvaluation", "cellCount_brightnessCorrection2"),
      cellCount_standard = nonnull_count(con, "QuPathEvaluation", "cellCount_standard"),
      cellCount_cellpose = nonnull_count(con, "QuPathEvaluation", "cellCount_cellpose"),
      cellCount_cellpose_g65 = nonnull_count(con, "QuPathEvaluation", "cellCount_cellpose_g65"),
      cellCount_cellpose_flowThresh80 = nonnull_count(con, "QuPathEvaluation", "cellCount_cellpose_flowThresh80"),
      cellCount_QCmetrics = nonnull_count(con, "QuPathEvaluation", "cellCount_QCmetrics")
    ),
    top_growth_types = table_summary_records(con, "QuPathEvaluation", "growthType")
  )

  perspective_summary <- list(
    row_count = as.integer(row_counts_df$row_count[row_counts_df$table == "Perspective"]),
    distinct_which_perspective = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT whichPerspective) AS n FROM `Perspective`")),
    distinct_sample_source = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT sampleSource) AS n FROM `Perspective`")),
    nonnull_origin = nonnull_count(con, "Perspective", "origin"),
    top_which_perspective = table_summary_records(con, "Perspective", "whichPerspective"),
    top_states = table_summary_records(con, "Perspective", "state")
  )

  identity_summary <- list(
    row_count = as.integer(row_counts_df$row_count[row_counts_df$table == "Identity"]),
    distinct_which_perspective = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT whichPerspective) AS n FROM `Identity`")),
    distinct_sample_source = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT sampleSource) AS n FROM `Identity`")),
    nonnull_counts = list(
      GenomePerspective = nonnull_count(con, "Identity", "GenomePerspective"),
      TranscriptomePerspective = nonnull_count(con, "Identity", "TranscriptomePerspective"),
      ExomePerspective = nonnull_count(con, "Identity", "ExomePerspective"),
      KaryotypePerspective = nonnull_count(con, "Identity", "KaryotypePerspective")
    ),
    top_states = table_summary_records(con, "Identity", "state")
  )

  cell_lines_summary <- list(
    row_count = as.integer(row_counts_df$row_count[row_counts_df$table == "CellLinesAndPatients"]),
    distinct_types = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT whichType) AS n FROM `CellLinesAndPatients`")),
    year_min = scalar_query(con, "SELECT MIN(year_of_first_report) AS value FROM `CellLinesAndPatients`"),
    year_max = scalar_query(con, "SELECT MAX(year_of_first_report) AS value FROM `CellLinesAndPatients`"),
    nonnull_doubling_time = nonnull_count(con, "CellLinesAndPatients", "doublingTime_hours"),
    top_types = table_summary_records(con, "CellLinesAndPatients", "whichType")
  )

  flask_summary <- list(
    row_count = as.integer(row_counts_df$row_count[row_counts_df$table == "Flask"]),
    distinct_bottom_shape = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT bottom_shape) AS n FROM `Flask`")),
    distinct_surface_treated_type = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT surface_treated_type) AS n FROM `Flask`")),
    area_min = scalar_query(con, "SELECT MIN(dishSurfaceArea_cm2) AS value FROM `Flask`"),
    area_max = scalar_query(con, "SELECT MAX(dishSurfaceArea_cm2) AS value FROM `Flask`"),
    top_bottom_shapes = table_summary_records(con, "Flask", "bottom_shape")
  )

  media_summary <- list(
    row_count = as.integer(row_counts_df$row_count[row_counts_df$table == "Media"]),
    distinct_stressors = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT Stressor) AS n FROM `Media`")),
    nonnull_counts = list(
      Stressor = nonnull_count(con, "Media", "Stressor"),
      Stressor_concentration = nonnull_count(con, "Media", "Stressor_concentration"),
      oxygen_pct = nonnull_count(con, "Media", "oxygen_pct")
    ),
    top_stressors = table_summary_records(con, "Media", "Stressor")
  )

  media_ingredients_summary <- list(
    row_count = as.integer(row_counts_df$row_count[row_counts_df$table == "MediaIngredients"]),
    distinct_vendors = as.integer(scalar_query(con, "SELECT COUNT(DISTINCT vendor) AS n FROM `MediaIngredients`")),
    nonnull_description = nonnull_count(con, "MediaIngredients", "description"),
    top_vendors = table_summary_records(con, "MediaIngredients", "vendor")
  )

  list(
    run_id = run_id,
    generated_at = timestamp_utc(),
    requested_mode = requested_mode,
    mode_used = "live",
    status = "ok",
    live_access = list(
      attempted = TRUE,
      success = TRUE,
      error = NULL
    ),
    database = list(
      source = "cloneid R package",
      connection_method = "cloneid::connect2DB()",
      database_name = database_name
    ),
    tables = as.list(tables),
    table_count = length(tables),
    row_counts = as_records(row_counts_df),
    fields = fields,
    key_table_summaries = list(
      Passaging = passaging_summary,
      QuPathEvaluation = qupath_summary,
      Perspective = perspective_summary,
      Identity = identity_summary,
      CellLinesAndPatients = cell_lines_summary,
      Flask = flask_summary,
      Media = media_summary,
      MediaIngredients = media_ingredients_summary
    ),
    queries = queries,
    warnings = list()
  )
}

write_markdown_report <- function(inventory, output_path) {
  lines <- c(
    "# Database Inventory",
    "",
    sprintf("- Run ID: `%s`", inventory$run_id),
    sprintf("- Generated at: `%s`", inventory$generated_at),
    sprintf("- Requested mode: `%s`", inventory$requested_mode),
    sprintf("- Mode used: `%s`", inventory$mode_used),
    sprintf("- Status: `%s`", inventory$status),
    sprintf("- Table count: `%s`", inventory$table_count),
    ""
  )

  if (!is.null(inventory$database$database_name)) {
    lines <- c(lines, sprintf("- Database name: `%s`", inventory$database$database_name), "")
  }

  if (length(inventory$warnings) > 0) {
    lines <- c(lines, "## Warnings", "")
    lines <- c(lines, unlist(lapply(inventory$warnings, function(w) sprintf("- %s", w))), "")
  }

  lines <- c(lines, "## Tables", "", "| Table | Rows |", "|---|---:|")
  row_counts <- inventory$row_counts
  if (is.data.frame(row_counts)) {
    for (idx in seq_len(nrow(row_counts))) {
      lines <- c(lines, sprintf("| `%s` | %s |", row_counts$table[[idx]], row_counts$row_count[[idx]]))
    }
  } else {
    for (idx in seq_along(row_counts)) {
      row <- row_counts[[idx]]
      lines <- c(lines, sprintf("| `%s` | %s |", row$table, row$row_count))
    }
  }

  lines <- c(lines, "", "## Key Table Summaries", "")
  for (table_name in names(inventory$key_table_summaries)) {
    summary <- inventory$key_table_summaries[[table_name]]
    lines <- c(lines, sprintf("### `%s`", table_name), "")
    if (!is.null(summary$row_count)) {
      lines <- c(lines, sprintf("- Row count: `%s`", summary$row_count))
    }
    if (!is.null(summary$distinct_cell_lines)) {
      lines <- c(lines, sprintf("- Distinct cell lines: `%s`", summary$distinct_cell_lines))
    }
    if (!is.null(summary$distinct_growth_types)) {
      lines <- c(lines, sprintf("- Distinct growth types: `%s`", summary$distinct_growth_types))
    }
    if (!is.null(summary$distinct_which_perspective)) {
      lines <- c(lines, sprintf("- Distinct `whichPerspective`: `%s`", summary$distinct_which_perspective))
    }
    if (!is.null(summary$distinct_sample_source)) {
      lines <- c(lines, sprintf("- Distinct sample sources: `%s`", summary$distinct_sample_source))
    }
    if (!is.null(summary$distinct_types)) {
      lines <- c(lines, sprintf("- Distinct `whichType`: `%s`", summary$distinct_types))
    }
    if (!is.null(summary$distinct_stressors)) {
      lines <- c(lines, sprintf("- Distinct stressors: `%s`", summary$distinct_stressors))
    }
    if (!is.null(summary$distinct_vendors)) {
      lines <- c(lines, sprintf("- Distinct vendors: `%s`", summary$distinct_vendors))
    }
    if (!is.null(summary$date_min) || !is.null(summary$date_max)) {
      lines <- c(lines, sprintf("- Date range: `%s` to `%s`", summary$date_min %||% "NA", summary$date_max %||% "NA"))
    }
    if (!is.null(summary$year_min) || !is.null(summary$year_max)) {
      lines <- c(lines, sprintf("- Year range: `%s` to `%s`", summary$year_min %||% "NA", summary$year_max %||% "NA"))
    }
    if (!is.null(summary$area_min) || !is.null(summary$area_max)) {
      lines <- c(lines, sprintf("- Flask area range: `%s` to `%s`", summary$area_min %||% "NA", summary$area_max %||% "NA"))
    }
    if (!is.null(summary$important_fields)) {
      lines <- c(lines, sprintf("- Important fields: `%s`", paste(summary$important_fields, collapse = "`, `")))
    }
    if (!is.null(summary$note)) {
      lines <- c(lines, sprintf("- Note: %s", summary$note))
    }
    lines <- c(lines, "")
  }

  writeLines(lines, output_path)
}

main <- function() {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  run_id <- args$run_id %||% default_run_id()
  output_dir <- resolve_output_dir(args$output, run_id)
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

  inventory <- NULL
  live_error <- NULL

  if (args$mode == "mock") {
    inventory <- mock_inventory_template(run_id = run_id, requested_mode = args$mode)
  } else {
    inventory <- tryCatch(
      build_live_inventory(run_id = run_id, requested_mode = args$mode),
      error = function(e) {
        live_error <<- conditionMessage(e)
        mock_inventory_template(run_id = run_id, requested_mode = args$mode, live_error = live_error)
      }
    )
  }

  json_path <- file.path(output_dir, "database_inventory.json")
  md_path <- file.path(output_dir, "database_inventory.md")

  writeLines(toJSON(inventory, auto_unbox = TRUE, pretty = TRUE, null = "null", na = "null"), json_path)
  write_markdown_report(inventory, md_path)

  cat(sprintf("Wrote %s\n", json_path))
  cat(sprintf("Wrote %s\n", md_path))
  if (!is.null(live_error)) {
    cat(sprintf("Live inventory failed; mock output was written instead: %s\n", live_error))
  }
}

main()
