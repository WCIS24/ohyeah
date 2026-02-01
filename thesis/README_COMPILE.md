# Thesis Compile Guide

This repo provides a single-file merged thesis: `thesis/thesis_full.tex`.

## Compile (XeLaTeX)

```powershell
cd thesis
xelatex thesis_full.tex
xelatex thesis_full.tex
```

Notes:
- Two passes are required to resolve the Table of Contents.
- Bibliography is included via `thebibliography` in `backmatter/references.tex`,
  so no bibtex/biber is required for this file.

If XeLaTeX is not installed, install a TeX distribution (e.g., TeX Live or MiKTeX).
