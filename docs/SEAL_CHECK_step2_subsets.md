# SEAL Check - Step2 (Subsets: complex/abbrev/numeric)

Date: 2026-02-18  
Checked commit: `0b7f9100b360408023ff78d8195bb78ebb1de659`  
Seal matrix reference: `outputs/20260217_123645_68f6b9/matrix.json:2`

## 0) Verdict

`PASS`

Summary:
1. Three subset generators and artifacts exist, with concrete counts/ratios in stats files.
2. `complex/abbrev/numeric` are wired into Step6 main evaluation flow and reach `summary.json`.
3. Table/plot pipeline reads abbrev metrics; dedicated abbrev figure is currently disabled by config
   (not a data-path break).

---

## 1) Current repository truth (subset definitions and artifacts)

## 1.1 Subset generation logic (code truth)

- `complex` + `abbrev` builder:
  - script entry: `scripts/build_subsets.py:25`
  - complex rules (OR): multi-evidence / two years / compare keywords / digit+year:
    `scripts/build_subsets.py:73` to `scripts/build_subsets.py:80`
  - abbrev rule: regex `\b[A-Z]{2,6}\b` on query:
    `scripts/build_subsets.py:21`, `scripts/build_subsets.py:92` to
    `scripts/build_subsets.py:94`
  - outputs:
    - `data/subsets/dev_complex_qids.txt` (`scripts/build_subsets.py:96`)
    - `data/subsets/dev_abbrev_qids.txt` (`scripts/build_subsets.py:101`)
    - stats `outputs/<run_id>/subsets_stats.json` (`scripts/build_subsets.py:117`)

- `numeric` builder:
  - script entry: `scripts/build_numeric_subset.py:50`
  - numeric rule (OR): query number / answer number / keyword hit / percent hit:
    `scripts/build_numeric_subset.py:101` to `scripts/build_numeric_subset.py:116`
  - output:
    - `data/subsets/dev_numeric_qids.txt` (`scripts/build_numeric_subset.py:126`)
    - stats `outputs/<run_id>/numeric_subset_stats.json`
      (`scripts/build_numeric_subset.py:135`)

Note:
- `KEYWORDS` in numeric builder contains garbled Chinese tokens:
  `scripts/build_numeric_subset.py:34` to `scripts/build_numeric_subset.py:45`.
  This does not block current seal runs, but it affects non-ASCII keyword matching quality.

## 1.2 Existing subset artifacts and observed stats

Generated files:
- `data/subsets/dev_complex_qids.txt`
- `data/subsets/dev_abbrev_qids.txt`
- `data/subsets/dev_numeric_qids.txt`

Observed line counts:
- `complex`: 243
- `abbrev`: 501
- `numeric`: 466

Evidence:
- stats (complex+abbrev):
  - `outputs/20260217_123507_c871d6/subsets_stats.json:3` (`complex_size`)
  - `outputs/20260217_123507_c871d6/subsets_stats.json:5` (`abbrev_size`)
  - `outputs/20260217_123507_c871d6/subsets_stats.json:4` / `:6` (ratios)
- stats (numeric):
  - `outputs/20260217_123507_1693c0/numeric_subset_stats.json:12` (`numeric_size`)
  - `outputs/20260217_123507_1693c0/numeric_subset_stats.json:13` (`numeric_ratio`)

Generation trace:
- `build_subsets` command + git hash:
  - `outputs/20260217_123507_c871d6/logs.txt:1`
  - `outputs/20260217_123507_c871d6/logs.txt:3`
- `build_numeric_subset` command + git hash:
  - `outputs/20260217_123507_1693c0/logs.txt:1`
  - `outputs/20260217_123507_1693c0/logs.txt:3`

---

## 2) Do subsets enter Step6 main evaluation flow?

## 2.1 Config wiring

- Step6 base points to all three subset files:
  - `configs/step6_base.yaml:67` (`complex_path`)
  - `configs/step6_base.yaml:68` (`abbrev_path`)
  - `configs/step6_base.yaml:69` (`numeric_path`)

- Seal matrix records same subset paths in key config:
  - `outputs/20260217_123645_68f6b9/matrix.json:57` to `:59`

## 2.2 Runtime wiring in unified runner

- Complex eval branch:
  - single-step: `scripts/run_experiment.py:247` to `scripts/run_experiment.py:266`
  - multistep: `scripts/run_experiment.py:169` to `scripts/run_experiment.py:198`
- Abbrev eval branch:
  - single-step: `scripts/run_experiment.py:268` to `scripts/run_experiment.py:289`
  - multistep: `scripts/run_experiment.py:200` to `scripts/run_experiment.py:232`
- Numeric subset eval branch:
  - `scripts/run_experiment.py:313` to `scripts/run_experiment.py:336`
- Summary write keys:
  - `retrieval_full`: `scripts/run_experiment.py:373`
  - `retrieval_complex`: `scripts/run_experiment.py:374`
  - `retrieval_abbrev`: `scripts/run_experiment.py:375`
  - `numeric_dev`: `scripts/run_experiment.py:376`

## 2.3 Output evidence (summary/table/plot)

- Summary includes abbrev + numeric subset metrics:
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:8`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:41`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json:44`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json:59`

- Runtime logs show subset-qids consumed:
  - complex: `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/logs.txt:19`
  - abbrev: `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/logs.txt:30`
  - numeric: `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_numeric/logs.txt:1`

- Table pipeline reads and shows abbrev:
  - reader keys: `scripts/make_tables.py:55` to `scripts/make_tables.py:57`
  - abbrev columns: `scripts/make_tables.py:67` to `scripts/make_tables.py:68`
  - output evidence header: `docs/TABLE_MAIN.md:1`

- Plot pipeline reads abbrev metrics into table outputs:
  - extraction keys: `scripts/plot_utils.py:97` to `scripts/plot_utils.py:105`
  - main_results columns include abbrev: `scripts/plot_config.yaml:37` to `scripts/plot_config.yaml:41`
  - output evidence header: `thesis/figures_seal/ThemeA/tables/main_results.csv:1`
  - run log shows table generation: `outputs/20260217_162648_133004/logs.txt:7`

Important:
- Dedicated abbrev chart is currently disabled:
  - `scripts/plot_config.yaml:65` to `scripts/plot_config.yaml:69`
  - This is a visualization choice, not a missing data path.

---

## 3) If abbrev were missing: minimal closure patch?

Current state: `not needed` (already integrated).

Closure conditions currently satisfied:
1. config has `eval.subsets.abbrev_path` (`configs/step6_base.yaml:68`)
2. run-time abbrev eval branch exists (`scripts/run_experiment.py:268`)
3. summary writes `retrieval_abbrev` (`scripts/run_experiment.py:375`)
4. table/plot readers consume abbrev fields (`scripts/make_tables.py:56`,
   `scripts/plot_utils.py:97`)

If a future regression happens (abbrev disappears), minimal closure order:
1. restore `eval.subsets.abbrev_path`
2. restore abbrev eval branch in `run_experiment.py`
3. restore `summary.metrics.retrieval_abbrev`
4. ensure `make_tables.py` + `plot_utils.py` have abbrev keys
5. rerun only affected evaluations and rebuild tables/plots (see section 5)

---

## 4) Subset version freeze recommendation (hash/date/commit)

Recommended seal manifest fields:
- subset file path
- line count
- sha256
- generator run_id
- generator command/config
- generator git hash
- generation timestamp

Current freeze snapshot (recommended to treat as seal subset version):

| Item | Value |
|---|---|
| `dev_complex_qids.txt` sha256 | `4d3e990a6770ce5a34cc06ed3f63a3dc75ab7ce9dfb541cb5814ad23f9e566ed` |
| `dev_abbrev_qids.txt` sha256 | `fbbe096641cdfc0df7e8a737fe3bad00ce2cf46f8c3236b5a7e8724e1bb48337` |
| `dev_numeric_qids.txt` sha256 | `12e51f95b4beef64df273ec95e8a5eb74952f7d90981628e898cb3b4d2895f5a` |
| `subsets_stats.json` sha256 | `ecdb735a2c9b8c60c14652178efed20c462541c4ec9629bf2d441112e16a0a1c` |
| `numeric_subset_stats.json` sha256 | `333e166bbcbb4283e252c96e62a99b1f4a1bc155ec16764f273499dcebe9ce5b` |
| generation time | `2026-02-17 20:35:07` (file mtime + logs) |
| generator commit | `27c146e3da3d3b525a7793c90e512103fa649335` (`outputs/20260217_123507_c871d6/logs.txt:3`, `outputs/20260217_123507_1693c0/logs.txt:3`) |

---

## 5) Impact scope and minimal recompute strategy

## 5.1 Which outputs are impacted if subsets change?

If `dev_complex_qids.txt` changes:
- affected child eval outputs:
  - `*_retrieval_complex/metrics.json`
  - `*_ms_eval_complex/metrics.json`
- affected parent outputs:
  - `outputs/<run_id>/summary.json` (`metrics.retrieval_complex`)
  - `docs/TABLE_MAIN.md`, `docs/TABLE_ABLATION.md`
  - `thesis/figures_seal/ThemeA/tables/main_results.csv/.tex`

If `dev_abbrev_qids.txt` changes:
- affected child eval outputs:
  - `*_retrieval_abbrev/metrics.json`
  - `*_ms_eval_abbrev/metrics.json`
- affected parent outputs:
  - `outputs/<run_id>/summary.json` (`metrics.retrieval_abbrev`)
  - `docs/TABLE_MAIN.md`, `docs/TABLE_ABLATION.md`
  - `thesis/figures_seal/ThemeA/tables/main_results.csv/.tex`
  - optional abbrev figure outputs (only if enabled)

If `dev_numeric_qids.txt` changes:
- affected child eval outputs:
  - `*_numeric/numeric_metrics.json` (calc-enabled runs only)
- affected parent outputs:
  - `outputs/<run_id>/summary.json` (`metrics.numeric_dev`)
  - `docs/TABLE_NUMERIC.md`
  - plot tables/figures that use numeric fields

## 5.2 Fastest strategy without rerunning full pipeline

`Do not rerun retriever FT / matrix generation / corpus build.`

Minimal path:
1. Regenerate subset files:
   - `python scripts/build_subsets.py --config configs/build_subsets.yaml`
   - `python scripts/build_numeric_subset.py --config configs/build_numeric_subset.yaml`
2. Recompute only affected evaluations:
   - retrieval subset evals (`eval_retrieval.py` / `eval_multistep_retrieval.py`)
   - numeric subset evals (`eval_numeric.py`) for calc runs
3. Refresh parent `summary.json` for affected runs.
4. Rebuild tables/plots:
   - `python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml`
   - `python scripts/plot_all.py --config scripts/plot_config.yaml`

Practical note:
- Current repo has no standalone "refresh summary only" CLI; if summary refresh automation is not
  added, safest no-surprise fallback is rerun `scripts/run_experiment.py` only for affected run_ids
  (not the full 10-run matrix).

