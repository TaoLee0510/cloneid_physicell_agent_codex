#!/usr/bin/env bash

set -euo pipefail

PHYSICELL_ROOT="${1:-/Users/4470246/Downloads/PhysiCell-1.14.2}"
MAX_TIME_MIN="${2:-60}"
OMP_THREADS="${3:-1}"

CONFIG_PATH="${PHYSICELL_ROOT}/config/PhysiCell_settings.xml"
EXECUTABLE_PATH="${PHYSICELL_ROOT}/heterogeneity"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_FOLDER="output_smoke_${STAMP}"
BACKUP_CONFIG="$(mktemp)"

if [ ! -d "${PHYSICELL_ROOT}" ]; then
  echo "PhysiCell root not found: ${PHYSICELL_ROOT}" >&2
  exit 1
fi

if [ ! -x "${EXECUTABLE_PATH}" ]; then
  echo "PhysiCell executable not found: ${EXECUTABLE_PATH}" >&2
  exit 1
fi

cp "${CONFIG_PATH}" "${BACKUP_CONFIG}"
restore_config() {
  cp "${BACKUP_CONFIG}" "${CONFIG_PATH}"
  rm -f "${BACKUP_CONFIG}"
}
trap restore_config EXIT

perl -0pi -e "s|<max_time units=\"min\">.*?</max_time>|<max_time units=\"min\">${MAX_TIME_MIN}</max_time>|s" "${CONFIG_PATH}"
perl -0pi -e "s|<omp_num_threads>.*?</omp_num_threads>|<omp_num_threads>${OMP_THREADS}</omp_num_threads>|s" "${CONFIG_PATH}"
perl -0pi -e "s|<folder>output</folder>|<folder>${OUTPUT_FOLDER}</folder>|s" "${CONFIG_PATH}"

cd "${PHYSICELL_ROOT}"
"${EXECUTABLE_PATH}"

echo "Smoke test finished."
echo "Output folder: ${PHYSICELL_ROOT}/${OUTPUT_FOLDER}"
