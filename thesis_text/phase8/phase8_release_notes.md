# Release Notes (Phase 8)

## Scope
- Template-agnostic, fully compilable LaTeX project (ctexbook).
- All chapters, abstracts, appendix, references, acknowledgements included.
- Citation keys resolved in references.bib (placeholders remain where no source found).

## Known Limitations
- 9 bibliography entries remain placeholders (need real author/title/venue).
- Cover fields use TBD variables and require manual filling.
- Overfull hbox warnings may appear due to long commands/paths.

## Build
- xelatex -> bibtex -> xelatex -> xelatex

## Files
- thesis/ (all LaTeX sources)
- scripts/build_thesis.sh
