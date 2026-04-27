#!/usr/bin/env bash

set -euo pipefail

echo "PhysiCell runtime environment check"
echo

check_cmd() {
  local name="$1"
  local path=""
  if path="$(command -v "$name" 2>/dev/null)"; then
    echo "[ok] $name -> $path"
  else
    echo "[missing] $name"
  fi
}

check_cmd make
check_cmd clang++
check_cmd g++
check_cmd /opt/homebrew/bin/g++-15
check_cmd cmake
check_cmd docker
check_cmd apptainer
check_cmd singularity

echo
echo "Recommended local PhysiCell compiler:"
if [ -x /opt/homebrew/bin/g++-15 ]; then
  echo "  export PHYSICELL_CPP=/opt/homebrew/bin/g++-15"
else
  echo "  Homebrew g++-15 not found"
fi

echo
echo "Compiler versions:"
if command -v clang++ >/dev/null 2>&1; then
  clang++ --version | head -n 1
fi
if [ -x /opt/homebrew/bin/g++-15 ]; then
  /opt/homebrew/bin/g++-15 --version | head -n 1
fi

echo
echo "Docker daemon check:"
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    echo "  docker daemon reachable"
  else
    echo "  docker daemon not reachable from current context"
  fi
else
  echo "  docker cli not installed"
fi
