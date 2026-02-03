# Phase 5 ?????????

"
"Purpose:
- ?? main_results.* ???????????

"
"How to use:
- ?????? main_results.csv / main_results.md ????????

"
"## Data sources
"
"- configs/step6_experiments.yaml (run_id ?????)
"
"- outputs/<run_id>/summary.json (retrieval_full / retrieval_complex / numeric_dev ??)

"
"## Build command
"
"- python scripts/make_tables.py --experiments configs/step6_experiments.yaml
"
"- python (inline) ?? summary.json ?? thesis_text/phase5/main_results.csv

"
"## Output files
"
"- thesis_text/phase5/main_results.csv
"
"- thesis_text/phase5/main_results.md
" , encoding='utf-8')

Path('thesis_text/phase5/phase5_delta_summary.md').write_text(
Purpose:
- ??????? baseline ???????? main_results.csv??

How to use:
- ?????????? delta_vs_baseline.json / delta_vs_baseline.md?

[EVIDENCE] thesis_text/phase5/delta_vs_baseline.json; thesis_text/phase5/main_results.csv
