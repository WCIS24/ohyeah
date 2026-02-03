# RELEASE_NOTES

This release contains a template-agnostic, fully compilable LaTeX project.

- Chapters 1–5, abstracts, appendix, references, and acknowledgements are included.
- Citation keys are resolved; 9 entries remain placeholders awaiting real bibliographic metadata.
- Cover fields are variable-based (TBD) and should be filled before submission.

Build command:
1) xelatex main.tex
2) bibtex main
3) xelatex main.tex
4) xelatex main.tex

Known limitations:
- Placeholder bib entries remain.
- Overfull hbox warnings may appear due to long paths/commands.
