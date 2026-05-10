#!/usr/bin/env bash

set -euo pipefail

CANDIDATE_DIR="${1:?candidate dir required}"
PHYSICELL_ROOT="${2:-/Users/4482173/Documents/PhysiCell}"
MAX_TIME_MIN="${3:-60}"
OMP_THREADS="${4:-1}"

CONFIG_PATH="${CANDIDATE_DIR}/config/PhysiCell_settings.xml"
EXECUTABLE_PATH="${PHYSICELL_ROOT}/heterogeneity"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_FOLDER="${CANDIDATE_DIR}/simulation_output_runtime_${STAMP}"
TEMP_CONFIG="$(mktemp)"

if [ ! -d "${CANDIDATE_DIR}" ]; then
  echo "Candidate dir not found: ${CANDIDATE_DIR}" >&2
  exit 1
fi

if [ ! -f "${CONFIG_PATH}" ]; then
  echo "Candidate config not found: ${CONFIG_PATH}" >&2
  exit 1
fi

if [ ! -x "${EXECUTABLE_PATH}" ]; then
  echo "PhysiCell executable not found: ${EXECUTABLE_PATH}" >&2
  exit 1
fi

cp "${CONFIG_PATH}" "${TEMP_CONFIG}"
trap 'rm -f "${TEMP_CONFIG}"' EXIT

TEMP_CONFIG_PATH="${TEMP_CONFIG}" \
MAX_TIME_MIN_VALUE="${MAX_TIME_MIN}" \
OMP_THREADS_VALUE="${OMP_THREADS}" \
OUTPUT_FOLDER_VALUE="${OUTPUT_FOLDER}" \
python3 - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
import os

path = Path(os.environ["TEMP_CONFIG_PATH"])
tree = ET.parse(path)
root = tree.getroot()
root.find("./overall/max_time").text = os.environ["MAX_TIME_MIN_VALUE"]
root.find("./parallel/omp_num_threads").text = os.environ["OMP_THREADS_VALUE"]
root.find("./save/folder").text = os.environ["OUTPUT_FOLDER_VALUE"]
tree.write(path, encoding="utf-8", xml_declaration=False)
PY

"${EXECUTABLE_PATH}" "${TEMP_CONFIG}"

echo "Generated-model PhysiCell runtime execution finished."
echo "Output folder: ${OUTPUT_FOLDER}"
