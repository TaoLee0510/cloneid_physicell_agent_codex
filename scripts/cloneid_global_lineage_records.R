#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(cloneid)
  library(DBI)
  library(jsonlite)
})

parse_args <- function(args) {
  out <- list(mode = "auto", output = NULL)
  i <- 1
  while (i <= length(args)) {
    arg <- args[[i]]
    if (arg == "--mode") {
      i <- i + 1
      out$mode <- args[[i]]
    } else if (arg == "--output") {
      i <- i + 1
      out$output <- args[[i]]
    } else {
      stop(sprintf("Unknown argument: %s", arg))
    }
    i <- i + 1
  }
  if (!out$mode %in% c("live", "mock")) {
    stop("--mode must be one of: live, mock")
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

fetch_live_records <- function() {
  con <- connect2DB()
  on.exit(dbDisconnect(con), add = TRUE)

  passaging_sql <- paste(
    "SELECT",
    "id, cellLine, event, passaged_from_id1, passaged_from_id2,",
    "growthType, passage, cellCount, correctedCount, date, media, flask,",
    "areaOccupied_um2, cellSize_um2, comment",
    "FROM Passaging",
    "ORDER BY date, id"
  )
  passaging <- dbGetQuery(con, passaging_sql)

  perspective_sql <- paste(
    "SELECT",
    "cloneID, origin, whichPerspective, size, parent, sampleSource, rootID, state, alias, hasChildren",
    "FROM Perspective",
    "WHERE origin IS NOT NULL"
  )
  perspective <- dbGetQuery(con, perspective_sql)

  identity <- data.frame()
  identity_sql <- NULL
  if (nrow(perspective) > 0) {
    perspective_ids <- unique(stats::na.omit(as.character(perspective$cloneID)))
    sample_sources <- unique(stats::na.omit(as.character(perspective$sampleSource)))
    clauses <- character()
    if (length(sample_sources) > 0) {
      sample_values <- paste(sprintf("'%s'", gsub("'", "''", sample_sources, fixed = TRUE)), collapse = ", ")
      clauses <- c(clauses, sprintf("sampleSource IN (%s)", sample_values))
    }
    if (length(perspective_ids) > 0) {
      perspective_values <- paste(sprintf("'%s'", gsub("'", "''", perspective_ids, fixed = TRUE)), collapse = ", ")
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
        paste(
          "SELECT",
          "cloneID, size, whichPerspective, rootID, sampleSource, parent,",
          "KaryotypePerspective, GenomePerspective, ExomePerspective, TranscriptomePerspective,",
          "state, alias, hasChildren",
          "FROM Identity WHERE %s"
        ),
        paste(clauses, collapse = " OR ")
      )
      identity <- dbGetQuery(con, identity_sql)
    }
  }

  list(
    passaging = as_records(passaging),
    perspective = as_records(perspective),
    identity = as_records(identity),
    queries = Filter(
      Negate(is.null),
      list(
        list(name = "all_passaging", sql = passaging_sql),
        list(name = "all_perspective_with_origin", sql = perspective_sql),
        if (!is.null(identity_sql)) list(name = "identity_by_global_perspective_refs", sql = identity_sql) else NULL
      )
    )
  )
}

mock_records <- function() {
  list(
    passaging = list(
      list(id = "short_root", cellLine = "MOCK", growthType = "0", passage = 1, media = 1, flask = 1, event = "seed", date = "2024-01-01 00:00:00", passaged_from_id1 = NULL, passaged_from_id2 = NULL, correctedCount = 100),
      list(id = "short_end", cellLine = "MOCK", growthType = "0", passage = 1, media = 1, flask = 1, event = "harvest", date = "2024-01-02 00:00:00", passaged_from_id1 = "short_root", passaged_from_id2 = NULL, correctedCount = 140),
      list(id = "long_r0", cellLine = "MOCK", growthType = "0", passage = 10, media = 1, flask = 1, event = "seed", date = "2024-02-01 00:00:00", passaged_from_id1 = NULL, passaged_from_id2 = NULL, correctedCount = 100),
      list(id = "long_r1", cellLine = "MOCK", growthType = "0", passage = 11, media = 1, flask = 1, event = "seed", date = "2024-02-03 00:00:00", passaged_from_id1 = "long_r0", passaged_from_id2 = NULL, correctedCount = 120),
      list(id = "long_r2", cellLine = "MOCK", growthType = "0", passage = 12, media = 1, flask = 1, event = "seed", date = "2024-02-05 00:00:00", passaged_from_id1 = "long_r1", passaged_from_id2 = NULL, correctedCount = 150),
      list(id = "long_r3", cellLine = "MOCK", growthType = "0", passage = 13, media = 1, flask = 1, event = "seed", date = "2024-02-07 00:00:00", passaged_from_id1 = "long_r2", passaged_from_id2 = NULL, correctedCount = 180),
      list(id = "long_end", cellLine = "MOCK", growthType = "0", passage = 14, media = 1, flask = 1, event = "harvest", date = "2024-02-09 00:00:00", passaged_from_id1 = "long_r3", passaged_from_id2 = NULL, correctedCount = 220)
    ),
    perspective = list(
      list(cloneID = "p_short", origin = "short_end", whichPerspective = "GenomePerspective", size = 1.0, sampleSource = "short_end"),
      list(cloneID = "p_long", origin = "long_end", whichPerspective = "GenomePerspective", size = 1.0, sampleSource = "long_end")
    ),
    identity = list(
      list(cloneID = "id_long", sampleSource = "long_end", GenomePerspective = "p_long", state = "A")
    ),
    queries = list()
  )
}

main <- function() {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  payload <- if (args$mode == "mock") mock_records() else fetch_live_records()
  dir.create(dirname(args$output), recursive = TRUE, showWarnings = FALSE)
  writeLines(toJSON(payload, auto_unbox = TRUE, pretty = TRUE, null = "null"), args$output)
}

main()
