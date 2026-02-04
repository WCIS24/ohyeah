# Build Instructions

This folder contains a minimal, template-agnostic LaTeX project.

## Requirements
- TeX Live (XeLaTeX + BibTeX)

## Build (manual)
1) xelatex main.tex
2) bibtex main
3) xelatex main.tex
4) xelatex main.tex

## Build (script)
- From repo root:
  - bash scripts/build_thesis.sh

## Output
- main.pdf will be generated in this folder.
- Build log: thesis/_build/build.log
