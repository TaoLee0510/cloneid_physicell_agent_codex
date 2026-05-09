#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(cloneid)
  library(DBI)
  library(jsonlite)
})

parse_args <- function(args) {
  out <- list(mode = "live", output = NULL, root_id = character(), max_depth = 80)
  i <- 1
  while (i <= length(args)) {
    arg <- args[[i]]
    if (arg == "--mode") {
      i <- i + 1
      out$mode <- args[[i]]
    } else if (arg == "--output") {
      i <- i + 1
      out$output <- args[[i]]
    } else if (arg == "--root-id") {
      i <- i + 1
      out$root_id <- c(out$root_id, unlist(strsplit(args[[i]], ",", fixed = TRUE)))
    } else if (arg == "--max-depth") {
      i <- i + 1
      out$max_depth <- as.integer(args[[i]])
    } else {
      stop(sprintf("Unknown argument: %s", arg))
    }
    i <- i + 1
  }
  out$root_id <- unique(trimws(out$root_id[out$root_id != ""]))
  if (!out$mode %in% c("live", "mock")) {
    stop("--mode must be one of: live, mock")
  }
  if (is.null(out$output)) {
    stop("--output is required")
  }
  if (length(out$root_id) == 0) {
    stop("At least one --root-id is required")
  }
  out
}

timestamp_utc <- function() {
  format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
}

as_records <- function(df) {
  if (is.null(df) || nrow(df) == 0) {
    return(list())
  }
  fromJSON(toJSON(df, dataframe = "rows", auto_unbox = TRUE, na = "null"))
}

escape_sql <- function(value) {
  gsub("'", "''", as.character(value), fixed = TRUE)
}

quoted_ids <- function(ids) {
  paste(sprintf("'%s'", vapply(unique(ids), escape_sql, character(1))), collapse = ", ")
}

empty_df <- function() {
  data.frame()
}

safe_table_fields <- function(con, table) {
  tryCatch(dbListFields(con, table), error = function(e) character())
}

fetch_by_sql <- function(con, sql) {
  dbGetQuery(con, sql)
}

fetch_passaging_by_ids <- function(con, ids) {
  ids <- unique(stats::na.omit(as.character(ids)))
  if (length(ids) == 0) {
    return(empty_df())
  }
  sql <- sprintf(
    paste(
      "SELECT * FROM Passaging",
      "WHERE id IN (%s)",
      "ORDER BY date, id"
    ),
    quoted_ids(ids)
  )
  fetch_by_sql(con, sql)
}

fetch_passaging_children <- function(con, ids) {
  ids <- unique(stats::na.omit(as.character(ids)))
  if (length(ids) == 0) {
    return(empty_df())
  }
  sql <- sprintf(
    paste(
      "SELECT * FROM Passaging",
      "WHERE passaged_from_id1 IN (%s)",
      "ORDER BY date, id"
    ),
    quoted_ids(ids)
  )
  fetch_by_sql(con, sql)
}

fetch_optional_flask <- function(con, flask_ids) {
  fields <- safe_table_fields(con, "Flask")
  flask_ids <- unique(stats::na.omit(as.character(flask_ids)))
  if (length(fields) == 0 || length(flask_ids) == 0 || !"id" %in% fields) {
    return(empty_df())
  }
  sql <- sprintf("SELECT * FROM Flask WHERE id IN (%s)", quoted_ids(flask_ids))
  fetch_by_sql(con, sql)
}

fetch_optional_qupath <- function(con, passaging) {
  fields <- safe_table_fields(con, "QuPathEvaluation")
  if (length(fields) == 0 || nrow(passaging) == 0) {
    return(empty_df())
  }
  clauses <- character()
  if ("id" %in% fields) {
    clauses <- c(clauses, sprintf("id IN (%s)", quoted_ids(passaging$id)))
  }
  if ("passaged_from_id1" %in% fields) {
    clauses <- c(clauses, sprintf("passaged_from_id1 IN (%s)", quoted_ids(passaging$id)))
  }
  shared <- intersect(c("cellLine", "growthType", "passage", "media", "flask"), intersect(fields, names(passaging)))
  context_clauses <- character()
  for (idx in seq_len(nrow(passaging))) {
    row <- passaging[idx, , drop = FALSE]
    parts <- character()
    for (field in shared) {
      value <- row[[field]][[1]]
      if (is.na(value) || identical(value, "")) {
        parts <- c(parts, sprintf("%s IS NULL", field))
      } else if (is.numeric(value)) {
        parts <- c(parts, sprintf("%s = %s", field, value))
      } else {
        parts <- c(parts, sprintf("%s = '%s'", field, escape_sql(value)))
      }
    }
    if (length(parts) > 0) {
      context_clauses <- c(context_clauses, sprintf("(%s)", paste(parts, collapse = " AND ")))
    }
  }
  clauses <- c(clauses, unique(context_clauses))
  if (length(clauses) == 0) {
    return(empty_df())
  }
  sql <- sprintf(
    "SELECT * FROM QuPathEvaluation WHERE %s ORDER BY date, id",
    paste(clauses, collapse = " OR ")
  )
  fetch_by_sql(con, sql)
}

fetch_perspective_identity <- function(con, event_ids) {
  perspective_sql <- sprintf("SELECT * FROM Perspective WHERE origin IN (%s)", quoted_ids(event_ids))
  perspective <- fetch_by_sql(con, perspective_sql)

  identity <- empty_df()
  identity_sql <- NULL
  if (nrow(perspective) > 0) {
    perspective_ids <- unique(stats::na.omit(as.character(perspective$cloneID)))
    sample_sources <- unique(stats::na.omit(as.character(perspective$sampleSource)))
    clauses <- character()
    identity_fields <- safe_table_fields(con, "Identity")
    if (length(sample_sources) > 0 && "sampleSource" %in% identity_fields) {
      clauses <- c(clauses, sprintf("sampleSource IN (%s)", quoted_ids(sample_sources)))
    }
    for (field in intersect(c("GenomePerspective", "TranscriptomePerspective", "ExomePerspective", "KaryotypePerspective"), identity_fields)) {
      if (length(perspective_ids) > 0) {
        clauses <- c(clauses, sprintf("%s IN (%s)", field, quoted_ids(perspective_ids)))
      }
    }
    if (length(clauses) > 0) {
      identity_sql <- sprintf("SELECT * FROM Identity WHERE %s", paste(clauses, collapse = " OR "))
      identity <- fetch_by_sql(con, identity_sql)
    }
  }
  list(
    perspective = perspective,
    identity = identity,
    queries = Filter(
      Negate(is.null),
      list(
        list(name = "perspective_by_origin", sql = perspective_sql),
        if (!is.null(identity_sql)) list(name = "identity_by_sample_source_or_perspective", sql = identity_sql) else NULL
      )
    )
  )
}

fetch_live_rk_records <- function(root_ids, max_depth) {
  con <- connect2DB()
  on.exit(dbDisconnect(con), add = TRUE)

  roots <- fetch_passaging_by_ids(con, root_ids)
  if (nrow(roots) == 0) {
    stop(sprintf("No Passaging rows found for requested root ids: %s", paste(root_ids, collapse = ", ")))
  }
  found_roots <- unique(as.character(roots$id))
  missing_roots <- setdiff(root_ids, found_roots)
  if (length(missing_roots) > 0) {
    stop(sprintf("Missing requested root ids in Passaging: %s", paste(missing_roots, collapse = ", ")))
  }

  passaging <- roots
  seen_ids <- unique(as.character(roots$id))
  frontier <- seen_ids
  expansion <- list()
  for (depth in seq_len(max_depth)) {
    child_rows <- fetch_passaging_children(con, frontier)
    if (nrow(child_rows) == 0) {
      break
    }
    child_rows <- child_rows[!(as.character(child_rows$id) %in% seen_ids), , drop = FALSE]
    if (nrow(child_rows) == 0) {
      break
    }
    passaging <- rbind(passaging, child_rows)
    frontier <- unique(as.character(child_rows$id))
    seen_ids <- unique(c(seen_ids, frontier))
    expansion[[length(expansion) + 1]] <- list(depth = depth, new_event_count = nrow(child_rows))
  }
  passaging <- passaging[order(passaging$date, passaging$id), , drop = FALSE]

  flask <- fetch_optional_flask(con, passaging$flask)
  qupath <- fetch_optional_qupath(con, passaging)
  molecular <- fetch_perspective_identity(con, as.character(passaging$id))

  list(
    generated_at = timestamp_utc(),
    source = "cloneid R package",
    connection_method = "cloneid::connect2DB()",
    root_ids = as.list(root_ids),
    traversal_policy = "descendants through Passaging.passaged_from_id1 only; passaged_from_id2 retained as secondary support when present",
    max_depth = max_depth,
    missing_root_ids = as.list(character()),
    passaging = as_records(passaging),
    flask = as_records(flask),
    qupath = as_records(qupath),
    perspective = as_records(molecular$perspective),
    identity = as_records(molecular$identity),
    graph_expansion = expansion,
    queries = c(
      list(
        list(name = "root_passaging_rows", sql_template = "SELECT * FROM Passaging WHERE id IN (...)"),
        list(name = "descendant_passaging_rows", sql_template = "SELECT * FROM Passaging WHERE passaged_from_id1 IN (...)")
      ),
      molecular$queries
    )
  )
}

mock_payload <- function(root_ids) {
  list(
    generated_at = timestamp_utc(),
    source = "mock",
    connection_method = "mock",
    root_ids = as.list(root_ids),
    traversal_policy = "mock only",
    max_depth = 0,
    missing_root_ids = as.list(character()),
    passaging = list(),
    flask = list(),
    qupath = list(),
    perspective = list(),
    identity = list(),
    graph_expansion = list(),
    queries = list()
  )
}

main <- function() {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  payload <- if (args$mode == "mock") {
    mock_payload(args$root_id)
  } else {
    fetch_live_rk_records(args$root_id, args$max_depth)
  }
  dir.create(dirname(args$output), recursive = TRUE, showWarnings = FALSE)
  writeLines(toJSON(payload, auto_unbox = TRUE, pretty = TRUE, null = "null"), args$output)
}

main()
