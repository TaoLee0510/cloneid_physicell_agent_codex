#!/usr/bin/env bash

set -euo pipefail

SOURCE_ROOT="${1:-/tmp/PhysiCell-1.14.2-src}"
DEST_ROOT="${2:-/Users/4470246/Downloads/PhysiCell-1.14.2}"

if [ ! -d "${SOURCE_ROOT}" ]; then
  echo "Source PhysiCell tree not found: ${SOURCE_ROOT}" >&2
  exit 1
fi

if [ -e "${DEST_ROOT}" ]; then
  echo "Destination already exists: ${DEST_ROOT}" >&2
  exit 1
fi

mkdir -p "$(dirname "${DEST_ROOT}")"
cp -R "${SOURCE_ROOT}" "${DEST_ROOT}"

echo "Installed PhysiCell tree to: ${DEST_ROOT}"
