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
  out <- list(mode = "auto", output = NULL, seed_dataset_id = character())
  i <- 1
  while (i <= length(args)) {
    arg <- args[[i]]
    if (arg == "--mode") {
      i <- i + 1
      out$mode <- args[[i]]
    } else if (arg == "--output") {
      i <- i + 1
      out$output <- args[[i]]
    } else if (arg == "--seed-dataset-id") {
      i <- i + 1
      out$seed_dataset_id <- c(out$seed_dataset_id, args[[i]])
    } else {
      stop(sprintf("Unknown argument: %s", arg))
    }
    i <- i + 1
  }
  if (!out$mode %in% c("auto", "live", "mock")) {
    stop("--mode must be one of: auto, live, mock")
  }
  if (length(out$seed_dataset_id) == 0) {
    stop("At least one --seed-dataset-id is required")
  }
  if (is.null(out$output)) {
    stop("--output is required")
  }
  out
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

split_dataset_id <- function(dataset_id) {
  parts <- strsplit(dataset_id, "__", fixed = TRUE)[[1]]
  if (length(parts) != 5) {
    stop(sprintf("Expected 5-part dataset_id, got: %s", dataset_id))
  }
  list(
    cellLine = parts[[1]],
    growthType = parts[[2]],
    passage = parts[[3]],
    media = parts[[4]],
    flask = parts[[5]]
  )
}

escape_sql <- function(value) {
  gsub("'", "''", as.character(value), fixed = TRUE)
}

sql_equals_clause <- function(field, value, numeric = FALSE) {
  if (identical(value, "NA")) {
    return(sprintf("%s IS NULL", field))
  }
  if (numeric && grepl("^[0-9.]+$", value)) {
    return(sprintf("%s = %s", field, value))
  }
  sprintf("%s = '%s'", field, escape_sql(value))
}

fetch_live_fixture <- function(seed_dataset_id) {
  seed <- split_dataset_id(seed_dataset_id)
  con <- connect2DB()
  on.exit(dbDisconnect(con), add = TRUE)

  seed_event_sql <- sprintf(
    paste(
      "SELECT * FROM Passaging",
      "WHERE %s",
      "ORDER BY date, id"
    ),
    paste(
      c(
        sql_equals_clause("cellLine", seed$cellLine),
        sql_equals_clause("growthType", seed$growthType, numeric = TRUE),
        sql_equals_clause("passage", seed$passage, numeric = TRUE),
        sql_equals_clause("media", seed$media, numeric = TRUE),
        sql_equals_clause("flask", seed$flask, numeric = TRUE)
      ),
      collapse = " AND "
    )
  )
  seed_rows <- dbGetQuery(con, seed_event_sql)
  if (nrow(seed_rows) == 0) {
    stop(sprintf("No Passaging rows matched seed dataset_id: %s", seed_dataset_id))
  }

  fetch_rows_by_ids <- function(ids) {
    if (length(ids) == 0) {
      return(data.frame())
    }
    id_values <- paste(sprintf("'%s'", vapply(unique(ids), escape_sql, character(1))), collapse = ", ")
    sql <- sprintf(
      paste(
        "SELECT * FROM Passaging",
        "WHERE cellLine = '%s'",
        "AND id IN (%s)",
        "ORDER BY date, id"
      ),
      escape_sql(seed$cellLine),
      id_values
    )
    dbGetQuery(con, sql)
  }

  fetch_children_by_ids <- function(ids) {
    if (length(ids) == 0) {
      return(data.frame())
    }
    id_values <- paste(sprintf("'%s'", vapply(unique(ids), escape_sql, character(1))), collapse = ", ")
    sql <- sprintf(
      paste(
        "SELECT * FROM Passaging",
        "WHERE cellLine = '%s'",
        "AND (passaged_from_id1 IN (%s) OR passaged_from_id2 IN (%s))",
        "ORDER BY date, id"
      ),
      escape_sql(seed$cellLine),
      id_values,
      id_values
    )
    dbGetQuery(con, sql)
  }

  passaging <- seed_rows
  frontier_ids <- as.character(seed_rows$id)
  seen_ids <- unique(frontier_ids)
  expansion_queries <- list()
  max_depth <- 8
  for (depth in seq_len(max_depth)) {
    frontier_rows <- passaging[passaging$id %in% frontier_ids, , drop = FALSE]
    parent_ids <- unique(stats::na.omit(as.character(c(frontier_rows$passaged_from_id1, frontier_rows$passaged_from_id2))))
    parent_ids <- setdiff(parent_ids, seen_ids)
    parent_rows <- fetch_rows_by_ids(parent_ids)
    child_rows <- fetch_children_by_ids(frontier_ids)
    new_rows <- rbind(parent_rows, child_rows)
    if (nrow(new_rows) == 0) {
      break
    }
    new_rows <- new_rows[!(new_rows$id %in% seen_ids), , drop = FALSE]
    if (nrow(new_rows) == 0) {
      break
    }
    passaging <- rbind(passaging, new_rows)
    frontier_ids <- as.character(new_rows$id)
    seen_ids <- unique(c(seen_ids, frontier_ids))
    expansion_queries[[length(expansion_queries) + 1]] <- list(
      depth = depth,
      parent_id_count = length(parent_ids),
      new_event_count = nrow(new_rows)
    )
  }
  passaging <- passaging[order(passaging$date, passaging$id), , drop = FALSE]

  event_ids <- paste(sprintf("'%s'", vapply(as.character(passaging$id), escape_sql, character(1))), collapse = ", ")
  perspective_sql <- sprintf("SELECT * FROM Perspective WHERE origin IN (%s)", event_ids)
  perspective <- dbGetQuery(con, perspective_sql)

  identity <- data.frame()
  identity_sql <- NULL
  if (nrow(perspective) > 0) {
    perspective_ids <- unique(stats::na.omit(as.character(perspective$cloneID)))
    sample_sources <- unique(stats::na.omit(as.character(perspective$sampleSource)))
    clauses <- character()
    if (length(sample_sources) > 0) {
      sample_values <- paste(sprintf("'%s'", vapply(sample_sources, escape_sql, character(1))), collapse = ", ")
      clauses <- c(clauses, sprintf("sampleSource IN (%s)", sample_values))
    }
    if (length(perspective_ids) > 0) {
      perspective_values <- paste(sprintf("'%s'", vapply(perspective_ids, escape_sql, character(1))), collapse = ", ")
      clauses <- c(
        clauses,
        sprintf("GenomePerspective IN (%s)", perspective_values),
        sprintf("TranscriptomePerspective IN (%s)", perspective_values),
        sprintf("ExomePerspective IN (%s)", perspective_values),
        sprintf("KaryotypePerspective IN (%s)", perspective_values)
      )
    }
    if (length(clauses) > 0) {
      identity_sql <- sprintf(
        "SELECT * FROM Identity WHERE %s",
        paste(clauses, collapse = " OR ")
      )
      identity <- dbGetQuery(con, identity_sql)
    }
  }

  list(
    seed_dataset_id = seed_dataset_id,
    seed_context = seed,
    passaging = as_records(passaging),
    perspective = as_records(perspective),
    identity = as_records(identity),
    queries = list(
      list(name = "seed_event_rows", sql = seed_event_sql),
      list(name = "perspective_by_origin", sql = perspective_sql),
      if (!is.null(identity_sql)) list(name = "identity_by_sample_source_or_perspective", sql = identity_sql) else NULL
    ),
    graph_expansion = expansion_queries
  )
}

mock_fixture <- function(seed_dataset_id) {
  seed <- split_dataset_id(seed_dataset_id)
  list(
    seed_dataset_id = seed_dataset_id,
    seed_context = seed,
    passaging = list(
      list(id = "mock_seed_1", cellLine = seed$cellLine, growthType = seed$growthType, passage = seed$passage, media = seed$media, flask = seed$flask, date = "2024-01-01 00:00:00", passaged_from_id1 = NULL, passaged_from_id2 = NULL, correctedCount = 100, areaOccupied_um2 = 1000),
      list(id = "mock_harvest_1", cellLine = seed$cellLine, growthType = seed$growthType, passage = seed$passage, media = seed$media, flask = seed$flask, date = "2024-01-02 00:00:00", passaged_from_id1 = "mock_seed_1", passaged_from_id2 = NULL, correctedCount = 180, areaOccupied_um2 = 1800)
    ),
    perspective = list(
      list(cloneID = "mock_persp_1", origin = "mock_harvest_1", whichPerspective = "GenomePerspective", state = "A", sampleSource = "mock_harvest_1", size = 1.0)
    ),
    identity = list(
      list(cloneID = "mock_identity_1", sampleSource = "mock_harvest_1", GenomePerspective = "mock_persp_1", state = "A")
    ),
    queries = list()
  )
}

main <- function() {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  dir.create(args$output, recursive = TRUE, showWarnings = FALSE)

  for (seed_dataset_id in args$seed_dataset_id) {
    fixture <- if (args$mode == "mock") {
      mock_fixture(seed_dataset_id)
    } else {
      fetch_live_fixture(seed_dataset_id)
    }
    path <- file.path(args$output, sprintf("%s_records.json", sanitize_component(seed_dataset_id)))
    writeLines(toJSON(fixture, auto_unbox = TRUE, pretty = TRUE, null = "null"), path)
  }
}

main()
