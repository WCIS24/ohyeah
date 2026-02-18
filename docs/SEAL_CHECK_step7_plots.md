# SEAL Check - Step7 (plot pipeline)

Date: 2026-02-18  
Seal config: `scripts/plot_config.yaml`  
Seal plot run: `outputs/20260217_180116_13588b`

## 0) Verdict

Verdict: `PASS (for seal-enabled plots)`.

- Enabled items in seal config are:
  - `main_results` (table)
  - `ablation_breakdown` (figure)
- Both have valid data and outputs.
- Optional plots remain disabled by config; for each disabled block, root cause and
  minimal fix are listed below (not just config toggles).

---

## 1) Entry points and filtering logic

Command:

```bash
python scripts/plot_all.py --config scripts/plot_config.yaml
```

Evidence:
- CLI entry: `scripts/plot_all.py:46` to `scripts/plot_all.py:55`
- Figure config source: `scripts/plot_config.yaml:19` to `scripts/plot_config.yaml:84`
- Experiments source: `scripts/plot_config.yaml:5`
- Group filtering for recall curves (`use_groups`): `scripts/plot_all.py:646` to `scripts/plot_all.py:650`
- Group filtering for ablation (`group`): `scripts/plot_all.py:752` to `scripts/plot_all.py:755`

---

## 2) Seal run acceptance (`has_data` for enabled items)

Runtime evidence:
- `outputs/20260217_180116_13588b/logs.txt:1` to `outputs/20260217_180116_13588b/logs.txt:11`

| Item | Enabled in seal | Data check | Status | Evidence |
|---|---|---|---|---|
| `main_results` | yes | table rows written = 11, metrics present in CSV | ok | `outputs/20260217_180116_13588b/logs.txt:7`, `thesis/figures_seal/ThemeA/tables/main_results.csv:2` |
| `ablation_breakdown` | yes | `has_data=True` | ok | `outputs/20260217_180116_13588b/logs.txt:8` |

Generated outputs:
- `thesis/figures_seal/ThemeA/tables/main_results.csv`
- `thesis/figures_seal/ThemeA/tables/main_results.tex`
- `thesis/figures_seal/ThemeA/figures/ablation_breakdown.pdf`
- `thesis/figures_seal/ThemeA/figures/ablation_breakdown.png`

Catalog/tex output:
- `thesis/figures_seal/FIGURE_CATALOG.md` (entries=2): `outputs/20260217_180116_13588b/logs.txt:9`
- `thesis/figures_seal/figures_auto.tex`: `outputs/20260217_180116_13588b/logs.txt:10`

---

## 3) Per-figure diagnosis for disabled/`has_data=False` items

To validate root causes, a diagnostic run enabled all plot blocks:

```bash
python scripts/plot_all.py --config outputs/tmp_plot_diag.yaml
```

Diagnostic run log:
- `outputs/20260217_171714_373022/logs.txt:1` to `outputs/20260217_171714_373022/logs.txt:16`

`has_data` from diagnostic run:
- `recall_mrr_k`: false (`outputs/20260217_171714_373022/logs.txt:8`)
- `delta_bar`: false (`outputs/20260217_171714_373022/logs.txt:9`)
- `ablation_breakdown`: true (`outputs/20260217_171714_373022/logs.txt:10`)
- `abbrev_breakdown`: true (`outputs/20260217_171714_373022/logs.txt:11`)
- `numeric_error_dist`: false (`outputs/20260217_171714_373022/logs.txt:12`)
- `multistep_trace_case`: false (`outputs/20260217_171714_373022/logs.txt:13`)

### 3.1 `recall_mrr_curves` (disabled, would fail now)

Root cause:
- Plot code parses `recall@k`/`mrr@k` from top-level keys:
  `scripts/plot_utils.py:76` to `scripts/plot_utils.py:83`,
  used at `scripts/plot_all.py:224` to `scripts/plot_all.py:227`.
- Actual run `metrics.json` stores values under nested keys `retrieval_full.*`:
  `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/metrics.json:2`
  and metric keys at `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/metrics.json:7`.

Minimal fix:
- Keep disabled for seal; or patch `plot_recall_mrr_curves` to read
  `retrieval_full` (or summary-extracted flat metrics).

### 3.2 `delta_bar` (disabled, would fail now)

Root cause:
- Loader requires `delta_vs_baseline.json` / `delta_vs_pre.json` in each run dir:
  `scripts/plot_all.py:292` to `scripts/plot_all.py:294`.
- Seal run dirs do not contain these files:
  `outputs/seal_checks/step7_plot_data_presence.log:4`,
  `outputs/seal_checks/step7_plot_data_presence.log:5`
  (same pattern across all runs).

Minimal fix:
- Generate delta artifacts (via baseline-aware eval), or keep `delta_bar` disabled.

### 3.3 `numeric_errors` (disabled, would fail now)

Root cause:
- Config has `run_id: null`:
  `scripts/plot_config.yaml:82` to `scripts/plot_config.yaml:85`.
- Plot loader only reads when `run_id` is set:
  `scripts/plot_all.py:421` to `scripts/plot_all.py:425`.
- `numeric_per_query.jsonl` exists in sibling `*_numeric` dirs, not base run dir:
  `outputs/seal_checks/step7_plot_data_presence.log:72` to
  `outputs/seal_checks/step7_plot_data_presence.log:80`.
- File is written in eval run directory:
  `scripts/eval_numeric.py:150` to `scripts/eval_numeric.py:154`,
  `scripts/eval_numeric.py:205`.

Minimal fix:
- Set `numeric_errors.run_id` to a concrete `*_numeric` run id, or patch loader
  to resolve from `summary.runs.numeric_dev`.

### 3.4 `multistep_trace` (disabled, would fail now)

Root cause:
- Config has `run_id: null`:
  `scripts/plot_config.yaml:87` to `scripts/plot_config.yaml:90`.
- Plot loader reads `data_root/<run_id>/multistep_traces.jsonl`:
  `scripts/plot_all.py:464` to `scripts/plot_all.py:467`.
- Traces are written under sibling `*_ms` dirs:
  `scripts/run_multistep_retrieval.py:166`,
  and observed at
  `outputs/seal_checks/step7_plot_data_presence.log:81` to
  `outputs/seal_checks/step7_plot_data_presence.log:85`.

Minimal fix:
- Set `multistep_trace.run_id` to a concrete `*_ms` run id, or patch loader
  to resolve from `summary.runs.multistep`.

### 3.5 `abbrev_breakdown` (disabled by choice, data is available)

Evidence:
- Disabled in seal config: `scripts/plot_config.yaml:65` to `scripts/plot_config.yaml:69`
- Diagnostic run shows `has_data=True` when enabled:
  `outputs/20260217_171714_373022/logs.txt:11`

Minimal fix:
- Enable only if this figure is needed for final camera-ready plots.

---

## 4) Figure catalog artifact

Generated machine-readable catalog:
- `docs/FIGURE_CATALOG.json`

Contains, per item:
- figure/table name
- whether enabled in seal
- seal/diagnostic `has_data`
- output paths
- root cause and minimal fix

Evidence:
- `docs/FIGURE_CATALOG.json:1` to `docs/FIGURE_CATALOG.json:141`

---

## 5) Non-blocking warning

Plot style assets path in config does not exist:
- Config path values:
  - `scripts/plot_config.yaml:2`
  - `scripts/plot_config.yaml:3`
  - `scripts/plot_config.yaml:4`
- Runtime warning:
  `outputs/20260217_180116_13588b/logs.txt:6`

This does not block plotting, but style falls back to matplotlib defaults.
