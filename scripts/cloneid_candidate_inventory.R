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
  format(Sys.time(), "candidate_inventory_%Y%m%dT%H%M%S", tz = "UTC")
}

resolve_output_dir <- function(output, run_id) {
  if (!is.null(output)) {
    return(output)
  }
  file.path("runs", run_id %||% default_run_id())
}

as_records <- function(df) {
  if (is.null(df) || nrow(df) == 0) {
    return(list())
  }
  fromJSON(toJSON(df, dataframe = "rows", auto_unbox = TRUE, na = "null"))
}

sanitize_component <- function(x) {
  x <- ifelse(is.na(x) | x == "", "NA", as.character(x))
  gsub("[^A-Za-z0-9._-]+", "_", x)
}

build_dataset_ids <- function(df) {
  paste(
    sanitize_component(df$cellLine),
    sanitize_component(df$growthType),
    sanitize_component(df$passage),
    sanitize_component(df$media),
    sanitize_component(df$flask),
    sep = "__"
  )
}

mock_candidate_inventory <- function(run_id, requested_mode, live_error = NULL) {
  candidates <- data.frame(
    dataset_id = c("TOY_A549__adherent_2D__1__1__1", "TOY_HGC27__adherent_2D__2__3__1"),
    cellLine = c("TOY_A549", "TOY_HGC27"),
    growthType = c("adherent_2D", "adherent_2D"),
    passage = c(1, 2),
    media = c(1, 3),
    flask = c(1, 1),
    passaging_rows = c(3, 2),
    seeding_events = c(1, 1),
    harvest_events = c(2, 1),
    distinct_dates = c(3, 2),
    lineage_link_rows = c(2, 1),
    corrected_count_rows = c(3, 2),
    area_rows = c(3, 1),
    qupath_rows = c(2, 1),
    perspective_rows = c(2, 0),
    distinct_perspectives = c(1, 0),
    distinct_perspective_states = c(2, 0),
    context_complete = c(TRUE, TRUE),
    row.names = NULL
  )

  warnings <- c("Mock candidate inventory uses synthetic summary rows and does not query the live database.")
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
    grouping_definition = list(
      description = "Candidate dataset groups Passaging rows by shared cellLine, growthType, passage, media, and flask.",
      fields = list("Passaging.cellLine", "Passaging.growthType", "Passaging.passage", "Passaging.media", "Passaging.flask"),
      reversible_assumption = TRUE
    ),
    candidate_count = nrow(candidates),
    candidates = as_records(candidates),
    queries = list(),
    warnings = as.list(warnings)
  )
}

build_live_candidate_inventory <- function(run_id, requested_mode) {
  if (identical(Sys.getenv("CLONEID_AGENT_FORCE_LIVE_ERROR"), "1")) {
    stop("Forced live error via CLONEID_AGENT_FORCE_LIVE_ERROR=1")
  }

  con <- connect2DB()
  on.exit(dbDisconnect(con), add = TRUE)

  passaging_sql <- paste(
    "SELECT",
    "cellLine, growthType, passage, media, flask,",
    "COUNT(*) AS passaging_rows,",
    "SUM(CASE WHEN event = 'seeding' THEN 1 ELSE 0 END) AS seeding_events,",
    "SUM(CASE WHEN event = 'harvest' THEN 1 ELSE 0 END) AS harvest_events,",
    "COUNT(DISTINCT date) AS distinct_dates,",
    "SUM(CASE WHEN passaged_from_id1 IS NOT NULL OR passaged_from_id2 IS NOT NULL THEN 1 ELSE 0 END) AS lineage_link_rows,",
    "SUM(CASE WHEN correctedCount IS NOT NULL THEN 1 ELSE 0 END) AS corrected_count_rows,",
    "SUM(CASE WHEN areaOccupied_um2 IS NOT NULL THEN 1 ELSE 0 END) AS area_rows,",
    "MIN(date) AS date_min,",
    "MAX(date) AS date_max",
    "FROM Passaging",
    "GROUP BY cellLine, growthType, passage, media, flask"
  )
  passaging <- dbGetQuery(con, passaging_sql)

  qupath_sql <- paste(
    "SELECT",
    "cellLine, growthType, passage, media, flask,",
    "COUNT(*) AS qupath_rows,",
    "SUM(CASE WHEN cellCount_standard IS NOT NULL THEN 1 ELSE 0 END) AS qupath_standard_rows,",
    "SUM(CASE WHEN cellCount_cellpose IS NOT NULL THEN 1 ELSE 0 END) AS qupath_cellpose_rows",
    "FROM QuPathEvaluation",
    "GROUP BY cellLine, growthType, passage, media, flask"
  )
  qupath <- dbGetQuery(con, qupath_sql)

  perspective_sql <- paste(
    "SELECT",
    "p.cellLine, p.growthType, p.passage, p.media, p.flask,",
    "COUNT(pr.cloneID) AS perspective_rows,",
    "COUNT(DISTINCT pr.whichPerspective) AS distinct_perspectives,",
    "COUNT(DISTINCT pr.state) AS distinct_perspective_states",
    "FROM Passaging p",
    "LEFT JOIN Perspective pr ON pr.origin = p.id",
    "GROUP BY p.cellLine, p.growthType, p.passage, p.media, p.flask"
  )
  perspective <- dbGetQuery(con, perspective_sql)

  merged <- merge(passaging, qupath, all.x = TRUE, by = c("cellLine", "growthType", "passage", "media", "flask"))
  merged <- merge(merged, perspective, all.x = TRUE, by = c("cellLine", "growthType", "passage", "media", "flask"))
  zero_fill_columns <- c(
    "qupath_rows",
    "qupath_standard_rows",
    "qupath_cellpose_rows",
    "perspective_rows",
    "distinct_perspectives",
    "distinct_perspective_states"
  )
  for (column in zero_fill_columns) {
    if (column %in% names(merged)) {
      merged[[column]][is.na(merged[[column]])] <- 0
    }
  }
  merged$context_complete <- !(is.na(merged$cellLine) | is.na(merged$growthType) | is.na(merged$media) | is.na(merged$flask))
  merged$dataset_id <- build_dataset_ids(merged)
  merged <- merged[, c(
    "dataset_id", "cellLine", "growthType", "passage", "media", "flask",
    "passaging_rows", "seeding_events", "harvest_events", "distinct_dates",
    "lineage_link_rows", "corrected_count_rows", "area_rows", "date_min", "date_max",
    "qupath_rows", "qupath_standard_rows", "qupath_cellpose_rows",
    "perspective_rows", "distinct_perspectives", "distinct_perspective_states", "context_complete"
  )]

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
    grouping_definition = list(
      description = "Candidate dataset groups Passaging rows by shared cellLine, growthType, passage, media, and flask, then attaches QuPath and Perspective summaries by the same context keys.",
      fields = list("Passaging.cellLine", "Passaging.growthType", "Passaging.passage", "Passaging.media", "Passaging.flask"),
      reversible_assumption = TRUE
    ),
    candidate_count = nrow(merged),
    candidates = as_records(merged),
    queries = list(
      list(name = "candidate_passaging_groups", sql = passaging_sql),
      list(name = "candidate_qupath_groups", sql = qupath_sql),
      list(name = "candidate_perspective_groups", sql = perspective_sql)
    ),
    warnings = list("Identity linkage is not yet used in candidate grouping because the first-pass join rule remains ambiguous.")
  )
}

write_markdown_report <- function(inventory, output_path) {
  lines <- c(
    "# Candidate Dataset Inventory",
    "",
    sprintf("- Run ID: `%s`", inventory$run_id),
    sprintf("- Generated at: `%s`", inventory$generated_at),
    sprintf("- Requested mode: `%s`", inventory$requested_mode),
    sprintf("- Mode used: `%s`", inventory$mode_used),
    sprintf("- Candidate count: `%s`", inventory$candidate_count),
    "",
    "## Grouping Definition",
    "",
    sprintf("- %s", inventory$grouping_definition$description),
    sprintf("- Fields: `%s`", paste(unlist(inventory$grouping_definition$fields), collapse = "`, `")),
    ""
  )

  if (length(inventory$warnings) > 0) {
    lines <- c(lines, "## Warnings", "")
    lines <- c(lines, unlist(lapply(inventory$warnings, function(w) sprintf("- %s", w))), "")
  }

  lines <- c(
    lines,
    "## Candidates",
    "",
    "| Dataset ID | Cell line | Growth type | Passage | Media | Flask | Passaging rows | Harvests | Perspectives | Context complete |",
    "|---|---|---|---:|---:|---:|---:|---:|---:|---|"
  )
  candidates <- inventory$candidates
  if (is.data.frame(candidates) && nrow(candidates) > 0) {
    for (idx in seq_len(nrow(candidates))) {
      lines <- c(
        lines,
        sprintf(
          "| `%s` | `%s` | `%s` | %s | %s | %s | %s | %s | %s | `%s` |",
          candidates$dataset_id[[idx]],
          candidates$cellLine[[idx]],
          candidates$growthType[[idx]],
          candidates$passage[[idx]],
          candidates$media[[idx]],
          candidates$flask[[idx]],
          candidates$passaging_rows[[idx]],
          candidates$harvest_events[[idx]],
          candidates$perspective_rows[[idx]],
          candidates$context_complete[[idx]]
        )
      )
    }
  }

  writeLines(lines, output_path)
}

main <- function() {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  run_id <- args$run_id %||% default_run_id()
  output_dir <- resolve_output_dir(args$output, run_id)
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

  live_error <- NULL
  inventory <- NULL

  if (args$mode == "mock") {
    inventory <- mock_candidate_inventory(run_id, args$mode)
  } else {
    inventory <- tryCatch(
      build_live_candidate_inventory(run_id, args$mode),
      error = function(e) {
        live_error <<- conditionMessage(e)
        mock_candidate_inventory(run_id, args$mode, live_error = live_error)
      }
    )
  }

  json_path <- file.path(output_dir, "dataset_inventory.json")
  md_path <- file.path(output_dir, "dataset_inventory.md")
  writeLines(toJSON(inventory, auto_unbox = TRUE, pretty = TRUE, null = "null", na = "null"), json_path)
  write_markdown_report(inventory, md_path)

  cat(sprintf("Wrote %s\n", json_path))
  cat(sprintf("Wrote %s\n", md_path))
  if (!is.null(live_error)) {
    cat(sprintf("Live candidate inventory failed; mock output was written instead: %s\n", live_error))
  }
}

main()
