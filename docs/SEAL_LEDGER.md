# SEAL Ledger (Step0-Step7)

Generated on: 2026-02-17  
Workspace commit now: `0b7f9100b360408023ff78d8195bb78ebb1de659`  
Seal matrix commit captured in outputs: `27c146e3da3d3b525a7793c90e512103fa649335`

Legend:
- `PASS` = pass criteria is verifiable from current repo/outputs.
- `PARTIAL` = core artifacts exist but one required trace item is missing.
- `**MISSING**` = required artifact/trace item not found.

## 1) Step0-Step7 Single Source of Truth (mapping)

Because repo docs use `Step3..Step7` headings, this ledger uses the following
equivalence mapping for your requested `Step0..Step7`.

| Requested step | Repo-equivalent step | Evidence |
|---|---|---|
| Step0 Preflight | Smoke + config validation + traceability spec check | `README.md:20`, `README.md:23`, `README.md:140`, `README.md:144`, `AGENTS.md:27`, `docs/SEAL_TRACEABILITY.md:5` |
| Step1 Gate fix | Step6 seal matrix runs `m07` vs `m08` calculator gate contrast | `configs/step6_matrix_seal.yaml:66`, `configs/step6_matrix_seal.yaml:84` |
| Step2 Retrieval mode contrast | Step6 seal matrix runs `dense/bm25/hybrid` | `configs/step6_matrix_seal.yaml:20`, `configs/step6_matrix_seal.yaml:35` |
| Step3 Abbrev subset integration | `eval.subsets.abbrev_path` + `run_experiment` abbrev branch + table/plot consumers | `configs/step6_base.yaml:66`, `configs/step6_base.yaml:69`, `scripts/run_experiment.py:266`, `scripts/run_experiment.py:373`, `scripts/make_tables.py:56`, `scripts/plot_config.yaml:37` |
| Step4 Numeric tolerance compatibility | `eval_numeric` dual-key compatibility logic + warning | `scripts/eval_numeric.py:103`, `scripts/eval_numeric.py:141`, `configs/eval_numeric.yaml:5` |
| Step5 Engineering chain stabilization | CLI consistency, script bug fixes, plot gating, sweep fail-fast | `README.md:165`, `README.md:169`, `scripts/error_buckets.py:14`, `scripts/error_buckets.py:19`, `scripts/run_calculator.py:61`, `scripts/plot_config.yaml:44`, `scripts/sweep.py:55` |
| Step6 Seal traceability closure | Matrix parent metadata + runs/ layout + per-run key config | `scripts/run_matrix_step6.py:76`, `scripts/run_matrix_step6.py:78`, `scripts/run_matrix_step6.py:156`, `scripts/run_matrix_step6.py:160`, `docs/SEAL_TRACEABILITY.md:8` |
| Step7 Run stage | Smoke -> subsets -> seal matrix -> tables -> plots | `README.md:23`, `README.md:98`, `README.md:122`, `README.md:153`, `README.md:156`, `scripts/plot_all.py:47` |

## 2) Step-by-step acceptance ledger

### Step0 - Preflight

Goal (1 sentence): verify baseline executability and reproducibility logging before
seal matrix runs.

Entry command/script:
- `python scripts/smoke.py --config configs/smoke.yaml`
- `python scripts/validate_config.py --config configs/step6_base.yaml`

Key configs:
- `configs/smoke.yaml` (`configs/smoke.yaml:1`, `configs/smoke.yaml:6`)
- `configs/step6_base.yaml` (`README.md:144`)

Expected artifacts:
- `outputs/<run_id>/config.yaml`, `metrics.json`, `logs.txt` (`README.md:26`).

Actual found artifacts:

| Artifact | Exists | Time | Commit/seed evidence |
|---|---|---|---|
| `outputs/20260217_123459_5b6847/config.yaml` | Yes | 2026-02-17 20:34:59 | seed/git in log (`outputs/20260217_123459_5b6847/logs.txt:3`) |
| `outputs/20260217_123459_5b6847/metrics.json` | Yes | 2026-02-17 20:34:59 | metrics logged (`outputs/20260217_123459_5b6847/logs.txt:6`) |
| `outputs/20260217_123459_5b6847/logs.txt` | Yes | 2026-02-17 20:34:59 | command/config logged (`outputs/20260217_123459_5b6847/logs.txt:1`) |
| `validate_config` run log under `outputs/` | **MISSING** | - | no run_id/log artifact expected from script-only command |

Pass criteria:
- Smoke run produced `config.yaml + metrics.json + logs.txt` with seed/git logged.

Step result: `PASS` (for smoke preflight); `validate_config` has no run artifact.

---

### Step1 - Calculator gate empty allow-list contrast

Goal (1 sentence): verify empty allow-list and whitelist behavior are both reproducible.

Entry command/script:
- Seal matrix via `run_matrix_step6.py` (commands persisted in matrix metadata).

Key config + overrides:
- Empty gate run: `calculator.gate.allow_task_types=[]`
  (`configs/step6_matrix_seal.yaml:74`)
- Whitelist run: `calculator.gate.allow_task_types=["yoy","diff"]`
  (`configs/step6_matrix_seal.yaml:84`)

Expected artifacts:
- `outputs/<run_id>_calc/calc_stats.json`
- `outputs/<run_id>/summary.json` numeric metrics.

Actual found artifacts:

| Contrast run | Artifact | Exists | Key fields (evidence) |
|---|---|---|---|
| `m07` empty allow | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07_calc/calc_stats.json` | Yes | `total_queries=570`, `gate_task=570` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07_calc/calc_stats.json:2`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07_calc/calc_stats.json:17`) |
| `m08` whitelist | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_calc/calc_stats.json` | Yes | `total_queries=570`, `gate_task=465` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_calc/calc_stats.json:2`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_calc/calc_stats.json:17`) |
| `m07` numeric summary | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/summary.json` | Yes | `coverage=0.6180`, `numeric_em=0.3964` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/summary.json:61`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/summary.json:62`) |
| `m08` numeric summary | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json` | Yes | `coverage=0.6695`, `numeric_em=0.3197` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json:61`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json:62`) |

Pass criteria:
- Both control and patched gate runs must exist and produce `calc_stats.json`.
- `gate_task` ratio must change between control and whitelist runs.

Step result: `PASS` (ratio changed from `570/570=1.00` to `465/570=0.816`).

---

### Step2 - Retrieval mode contrast (dense/bm25/hybrid)

Goal (1 sentence): ensure dense-only is complemented by bm25/hybrid runs under same pipeline.

Entry command/script:
- Seal matrix run (parent command persisted in matrix metadata).

Key config + overrides:
- `retriever.mode=dense/bm25/hybrid`
  (`configs/step6_matrix_seal.yaml:15`, `configs/step6_matrix_seal.yaml:24`,
  `configs/step6_matrix_seal.yaml:33`)

Expected artifacts:
- `outputs/<run_id>/summary.json` with retrieval full/complex/abbrev metrics.

Actual found artifacts:

| Run | Mode evidence | Full R@10 / MRR@10 | Complex R@10 / MRR@10 | Abbrev R@10 / MRR@10 |
|---|---|---|---|---|
| `20260217_123645_68f6b9_m02` | `mode=dense` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:13`) | `0.3789 / 0.2554` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:22`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:24`) | `0.3951 / 0.2961` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:37`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:39`) | `0.3713 / 0.2497` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:52`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:54`) |
| `20260217_123645_68f6b9_m03` | `mode=bm25` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json:13`) | `0.2246 / 0.1266` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json:22`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json:24`) | `0.2099 / 0.1266` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json:37`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json:39`) | `0.2136 / 0.1233` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json:52`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json:54`) |
| `20260217_123645_68f6b9_m04` | `mode=hybrid` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json:13`) | `0.3491 / 0.2092` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json:22`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json:24`) | `0.3457 / 0.2159` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json:37`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json:39`) | `0.3373 / 0.1992` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json:52`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json:54`) |

Pass criteria:
- All three modes exist with comparable summary fields.

Step result: `PASS`.

---

### Step3 - Abbrev subset enters main evaluation flow

Goal (1 sentence): ensure `summary.json`/tables/plots can consume `abbrev` metrics.

Entry command/script:
- `run_experiment.py` retrieval branches + table/plot generation.

Key config + code points:
- Abbrev subset path wired in base config (`configs/step6_base.yaml:68`)
- Single-step abbrev eval branch (`scripts/run_experiment.py:266`)
- Multistep abbrev eval branch (`scripts/run_experiment.py:198`)
- Summary write key `retrieval_abbrev` (`scripts/run_experiment.py:373`)
- Table reader uses `retrieval_abbrev` (`scripts/make_tables.py:56`)
- Plot table columns include `abbrev_*` (`scripts/plot_config.yaml:37`)

Expected artifacts:
- Each seal run summary includes `metrics.retrieval_abbrev`.
- Table/plot config can read abbrev metrics.

Actual found artifacts:

| Artifact | Exists | Evidence |
|---|---|---|
| `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json` has `retrieval_abbrev` run mapping | Yes | (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:8`) |
| `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json` has abbrev metrics | Yes | (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:43`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:52`) |
| `docs/TABLE_MAIN.md` includes abbrev columns | Yes | generator columns in code (`scripts/make_tables.py:99`, `scripts/make_tables.py:100`) |

Pass criteria:
- `retrieval_abbrev` appears in summary and downstream table schema.

Step result: `PASS`.

---

### Step4 - Numeric tolerance key compatibility

Goal (1 sentence): ensure numeric tolerance uses canonical key while supporting legacy keys with warnings.

Entry command/script:
- `python scripts/eval_numeric.py --config configs/eval_numeric.yaml`

Key config + code points:
- Canonical key in config: `eval.numeric.tolerance` (`configs/eval_numeric.yaml:5`)
- Compatibility resolver (`scripts/eval_numeric.py:103`)
- Warning for legacy keys (`scripts/eval_numeric.py:126`, `scripts/eval_numeric.py:132`)
- Final applied source logging (`scripts/eval_numeric.py:141`)

Expected artifacts:
- Logs should show `numeric_tolerance=<n> source=<key_source>`.
- Legacy key should not be silent.

Actual found artifacts:

| Run/log | Exists | Evidence |
|---|---|---|
| Canonical-key run (`m08_numeric`) | Yes | `numeric_tolerance=4 source=eval.numeric.tolerance` (`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_numeric/logs.txt:8`) |
| Legacy precision run | Yes | warning + source legacy (`outputs/seal_numeric_legacy_p0/logs.txt:8`, `outputs/seal_numeric_legacy_p0/logs.txt:9`) |
| Conflict run (new + legacy) | Yes | warning + new key wins (`outputs/seal_numeric_both_conflict/logs.txt:8`, `outputs/seal_numeric_both_conflict/logs.txt:9`) |

Pass criteria:
- No silent key drift; logs must disclose key source/warning.

Step result: `PASS`.

---

### Step5 - Engineering-chain stabilization checks

Goal (1 sentence): verify non-model blockers (CLI, scripts, plotting, sweep constraints) are stabilized for seal workflow.

Entry command/script:
- `python scripts/error_buckets.py --run-id <run_id>` (`README.md:166`)
- `python scripts/error_buckets.py --config <yaml>` (`README.md:169`)
- `python scripts/plot_all.py --config scripts/plot_config.yaml`
- `python scripts/sweep.py --base-config configs/step6_base.yaml --search-space <space.yaml>`

Key code points:
- Error buckets CLI supports both modes (`scripts/error_buckets.py:14`,
  `scripts/error_buckets.py:19`)
- `run_calculator.py` uses `raw_config`/`resolved` consistently (`scripts/run_calculator.py:61`,
  `scripts/run_calculator.py:79`)
- Plot config disables known no-data charts (`scripts/plot_config.yaml:44`,
  `scripts/plot_config.yaml:52`, `scripts/plot_config.yaml:71`, `scripts/plot_config.yaml:78`)
- Sweep fail-fast on missing baseline path (`scripts/sweep.py:55`,
  `scripts/sweep.py:56`, `scripts/sweep.py:95`)

Actual found artifacts:

| Artifact | Exists | Evidence |
|---|---|---|
| `outputs/seal_mvp08/error_bucket_stats.json` | Yes | generated stats file timestamped 2026-02-17 20:17:47 |
| `outputs/seal_mvp02/error_bucket_stats.json` | Yes | generated stats file timestamped 2026-02-17 20:17:51 |
| `docs/ERROR_ANALYSIS.md` appended | Yes | run sections (`docs/ERROR_ANALYSIS.md:2`, `docs/ERROR_ANALYSIS.md:6`) |
| Plot run has enabled figure with `has_data=True` | Yes | (`outputs/20260217_140808_4c7530/logs.txt:8`) |
| Sweep runtime evidence in this seal batch | **MISSING** | no current-step sweep output referenced by seal matrix |

Pass criteria:
- CLI modes and plot gating are verifiable; optional sweep test should fail fast when path missing.

Step result: `PARTIAL` (static/code evidence present; no fresh sweep run artifact in seal batch).

---

### Step6 - Seal traceability closure

Goal (1 sentence): ensure matrix-level parent metadata and per-run trace chain are complete.

Entry command/script:
- `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix_seal.yaml`

Key config + code points:
- Matrix parent folder creation (`scripts/run_matrix_step6.py:76`,
  `scripts/run_matrix_step6.py:78`)
- Parent metadata writes (`scripts/run_matrix_step6.py:156`,
  `scripts/run_matrix_step6.py:160`)
- Per-run key config extraction includes seed/subset paths
  (`scripts/run_matrix_step6.py:52`, `scripts/run_matrix_step6.py:58`)

Expected artifacts:
- `outputs/<matrix_id>/matrix.json`
- `outputs/<matrix_id>/experiments_resolved.yaml`
- child run dirs under `outputs/<matrix_id>/runs/`.

Actual found artifacts:

| Artifact | Exists | Time | Evidence |
|---|---|---|---|
| `outputs/20260217_123645_68f6b9/matrix.json` | Yes | 2026-02-17 22:06:31 | id/commit/config recorded (`outputs/20260217_123645_68f6b9/matrix.json:2`, `outputs/20260217_123645_68f6b9/matrix.json:4`, `outputs/20260217_123645_68f6b9/matrix.json:6`) |
| `outputs/20260217_123645_68f6b9/experiments_resolved.yaml` | Yes | 2026-02-17 22:06:31 | matrix id + seed rows (`outputs/20260217_123645_68f6b9/experiments_resolved.yaml:1`, `outputs/20260217_123645_68f6b9/experiments_resolved.yaml:14`) |
| `outputs/20260217_123645_68f6b9/runs/<rid>/summary.json` | Yes | see run table below | all 10 runs `status=ok` (`outputs/20260217_123645_68f6b9/matrix.json:540`) |

Pass criteria:
- Parent metadata and child-run trace files exist and are cross-linkable.

Step result: `PASS`.

---

### Step7 - Execution stage (smoke + subsets + seal matrix + tables + plot)

Goal (1 sentence): run the minimal seal workflow and emit table/figure artifacts.

Entry command/script:
- Smoke: `python scripts/smoke.py --config configs/smoke.yaml`
- Subsets: `python scripts/build_subsets.py --config configs/build_subsets.yaml`
- Numeric subset: `python scripts/build_numeric_subset.py --config configs/build_numeric_subset.yaml`
- Seal matrix: `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix_seal.yaml`
- Tables: `python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml`
- Plots: `python scripts/plot_all.py --config scripts/plot_config.yaml`

Key configs:
- `configs/smoke.yaml`, `configs/build_subsets.yaml`,
  `configs/build_numeric_subset.yaml`, `configs/step6_matrix_seal.yaml`,
  `configs/step6_experiments_seal.yaml`, `scripts/plot_config.yaml`.

Expected artifacts:
- smoke run dir, subset qid files, seal matrix parent + runs, docs tables, plot outputs.

Actual found artifacts:

| Artifact | Exists | Time | Commit/seed evidence |
|---|---|---|---|
| `outputs/20260217_123459_5b6847/metrics.json` (smoke) | Yes | 2026-02-17 20:34:59 | seed/git in log (`outputs/20260217_123459_5b6847/logs.txt:3`) |
| `data/subsets/dev_complex_qids.txt` | Yes | 2026-02-17 20:35:07 | subset builder log with git (`outputs/20260217_123507_c871d6/logs.txt:3`) |
| `data/subsets/dev_abbrev_qids.txt` | Yes | 2026-02-17 20:35:07 | subset builder stats (`outputs/20260217_123507_c871d6/logs.txt:4`) |
| `data/subsets/dev_numeric_qids.txt` | Yes | 2026-02-17 20:35:07 | numeric subset stats (`outputs/20260217_123507_1693c0/logs.txt:5`) |
| `outputs/20260217_123645_68f6b9/matrix.json` | Yes | 2026-02-17 22:06:31 | matrix commit logged (`outputs/20260217_123645_68f6b9/matrix.json:4`) |
| `docs/TABLE_MAIN.md` | Yes | 2026-02-17 22:07:46 | table built from summaries (`scripts/make_tables.py:48`) |
| `docs/TABLE_NUMERIC.md` | Yes | 2026-02-17 22:07:46 | numeric table logic (`scripts/make_tables.py:71`) |
| `docs/TABLE_ABLATION.md` | Yes | 2026-02-17 22:07:46 | ablation group logic (`scripts/make_tables.py:80`) |
| `outputs/20260217_140808_4c7530/logs.txt` | Yes | 2026-02-17 22:08:09 | seed/git/has_data logged (`outputs/20260217_140808_4c7530/logs.txt:3`, `outputs/20260217_140808_4c7530/logs.txt:4`, `outputs/20260217_140808_4c7530/logs.txt:8`) |
| `thesis/figures_seal/ThemeA/figures/ablation_breakdown.pdf` | Yes | 2026-02-17 22:08:08 | written by plot run (`outputs/20260217_140808_4c7530/logs.txt:8`) |
| `make_tables` run_id/seed/git log | **MISSING** | - | script does not emit run-scoped output/log (`scripts/make_tables.py:35`) |

Pass criteria:
- Smoke + subset + matrix + table + figure artifacts all exist and cross-referenceable.
- If script has no run-scoped metadata, mark as missing trace item.

Step result: `PARTIAL` (functional outputs exist; `make_tables` lacks run-bound trace metadata).

## 3) Run-level binding ledger (reverse command trace)

This table binds each seal matrix run to `run_id`, `config.resolved`, `seed`,
and `git hash`, so commands can be reconstructed from `matrix.json`.

Parent command evidence:
- command template in code (`scripts/run_matrix_step6.py:92`)
- per-run concrete command arrays in metadata (`outputs/20260217_123645_68f6b9/matrix.json:12`)

| run_id | label | resolved config | seed | git hash | summary | calc_stats | ms logs | mtime |
|---|---|---|---:|---|---|---|---|---|
| `20260217_123645_68f6b9_m01` | `seal_mvp01_preft_dense_singlestep` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01/config.resolved.yaml` | 42 | `27c146e3da3d3b525a7793c90e512103fa649335` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01/summary.json` | - | - | 2026-02-17 20:47:51 |
| `20260217_123645_68f6b9_m02` | `seal_mvp02_dense_singlestep` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/config.resolved.yaml` | 42 | `27c146e3da3d3b525a7793c90e512103fa649335` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json` | - | - | 2026-02-17 20:58:51 |
| `20260217_123645_68f6b9_m03` | `seal_mvp03_bm25_singlestep` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/config.resolved.yaml` | 42 | `27c146e3da3d3b525a7793c90e512103fa649335` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json` | - | - | 2026-02-17 21:09:51 |
| `20260217_123645_68f6b9_m04` | `seal_mvp04_hybrid_singlestep` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/config.resolved.yaml` | 42 | `27c146e3da3d3b525a7793c90e512103fa649335` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json` | - | - | 2026-02-17 21:20:50 |
| `20260217_123645_68f6b9_m05` | `seal_mvp05_dense_multistep` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05/config.resolved.yaml` | 42 | `27c146e3da3d3b525a7793c90e512103fa649335` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05/summary.json` | - | `outputs/20260217_123645_68f6b9/runs\20260217_123645_68f6b9_m05_ms\logs.txt` | 2026-02-17 21:24:51 |
| `20260217_123645_68f6b9_m06` | `seal_mvp06_dense_multistep_t1` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06/config.resolved.yaml` | 42 | `27c146e3da3d3b525a7793c90e512103fa649335` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06/summary.json` | - | `outputs/20260217_123645_68f6b9/runs\20260217_123645_68f6b9_m06_ms\logs.txt` | 2026-02-17 21:28:42 |
| `20260217_123645_68f6b9_m07` | `seal_mvp07_dense_calc_empty_allow` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/config.resolved.yaml` | 42 | `27c146e3da3d3b525a7793c90e512103fa649335` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/summary.json` | `outputs/20260217_123645_68f6b9/runs\20260217_123645_68f6b9_m07_calc\calc_stats.json` | - | 2026-02-17 21:43:38 |
| `20260217_123645_68f6b9_m08` | `seal_mvp08_dense_calc_allow_yoy_diff` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/config.resolved.yaml` | 42 | `27c146e3da3d3b525a7793c90e512103fa649335` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json` | `outputs/20260217_123645_68f6b9/runs\20260217_123645_68f6b9_m08_calc\calc_stats.json` | - | 2026-02-17 21:58:30 |
| `20260217_123645_68f6b9_m09` | `seal_mvp09_dense_multistep_calc` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09/config.resolved.yaml` | 42 | `27c146e3da3d3b525a7793c90e512103fa649335` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09/summary.json` | `outputs/20260217_123645_68f6b9/runs\20260217_123645_68f6b9_m09_calc\calc_stats.json` | `outputs/20260217_123645_68f6b9/runs\20260217_123645_68f6b9_m09_ms\logs.txt` | 2026-02-17 22:02:34 |
| `20260217_123645_68f6b9_m10` | `seal_mvp10_dense_multistep_t1_calc` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10/config.resolved.yaml` | 42 | `27c146e3da3d3b525a7793c90e512103fa649335` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10/summary.json` | `outputs/20260217_123645_68f6b9/runs\20260217_123645_68f6b9_m10_calc\calc_stats.json` | `outputs/20260217_123645_68f6b9/runs\20260217_123645_68f6b9_m10_ms\logs.txt` | 2026-02-17 22:06:31 |

## 4) Final pass/fail snapshot by step

| Step | Status | Reason |
|---|---|---|
| Step0 | PASS | smoke preflight reproducibility artifacts complete |
| Step1 | PASS | gate contrast outputs exist; `gate_task` changed |
| Step2 | PASS | dense/bm25/hybrid runs complete with summaries |
| Step3 | PASS | abbrev path + eval branch + summary/table consumption connected |
| Step4 | PASS | tolerance compatibility and warning behavior evidenced in logs |
| Step5 | PARTIAL | engineering fixes present; no fresh sweep runtime artifact in seal batch |
| Step6 | PASS | matrix parent metadata + child run trace chain complete |
| Step7 | PARTIAL | core outputs complete; `make_tables` lacks run-bound seed/git trace |
