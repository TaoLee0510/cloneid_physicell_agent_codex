#!/usr/bin/env bash

set -euo pipefail

PHYSICELL_SOURCE_ROOT="${1:-/tmp/PhysiCell-1.14.2-src}"
PHYSICELL_CPP_PATH="${PHYSICELL_CPP:-/opt/homebrew/bin/g++-15}"

if [ ! -d "${PHYSICELL_SOURCE_ROOT}" ]; then
  echo "PhysiCell source directory not found: ${PHYSICELL_SOURCE_ROOT}" >&2
  exit 1
fi

if [ ! -x "${PHYSICELL_CPP_PATH}" ]; then
  echo "Compiler not found or not executable: ${PHYSICELL_CPP_PATH}" >&2
  exit 1
fi

echo "Building PhysiCell from: ${PHYSICELL_SOURCE_ROOT}"
echo "Using compiler: ${PHYSICELL_CPP_PATH}"

cd "${PHYSICELL_SOURCE_ROOT}"
env PHYSICELL_CPP="${PHYSICELL_CPP_PATH}" make

EXECUTABLE_NAME="$(
  awk '/^PROGRAM_NAME[[:space:]]*:=/ {print $3; found=1} END {if (!found) print ""}' Makefile
)"
if [ -z "${EXECUTABLE_NAME}" ] || [ ! -x "${PHYSICELL_SOURCE_ROOT}/${EXECUTABLE_NAME}" ]; then
  EXECUTABLE_NAME="$(find "${PHYSICELL_SOURCE_ROOT}" -maxdepth 1 -type f -perm -111 | xargs -n1 basename | head -n1)"
fi

echo "Build finished."
echo "Expected executable path: ${PHYSICELL_SOURCE_ROOT}/${EXECUTABLE_NAME}"
