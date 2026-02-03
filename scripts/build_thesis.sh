#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
THESIS_DIR="$ROOT_DIR/thesis"
BUILD_DIR="$THESIS_DIR/_build"
LOG_FILE="$BUILD_DIR/build.log"

mkdir -p "$BUILD_DIR"
: > "$LOG_FILE"

cd "$THESIS_DIR"

xelatex -interaction=nonstopmode -halt-on-error main.tex | tee -a "$LOG_FILE"
bibtex main | tee -a "$LOG_FILE"
xelatex -interaction=nonstopmode -halt-on-error main.tex | tee -a "$LOG_FILE"
xelatex -interaction=nonstopmode -halt-on-error main.tex | tee -a "$LOG_FILE"

printf "\nBuild complete. Log: %s\n" "$LOG_FILE"
