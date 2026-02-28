# SEAL Freeze Manifest

Generated at: 2026-02-28 18:33:41 Asia/Shanghai
Freeze status: Ready to freeze after creating one git commit and one git tag.

## 1. Freeze Recommendation

| Item | Value |
| --- | --- |
| repo | `WCIS24/ohyeah` |
| remote | `https://github.com/WCIS24/ohyeah.git` |
| branch | `feat/pqe_replace_multistep` |
| base_commit_now | `427933035d8144eca44ac919fd0a9c2692469f6e` |
| recommended_freeze_commit | Create one new commit from the current worktree after staging `Makefile`, `configs/step6_experiments_seal.yaml`, `docs/SEAL_FREEZE_MANIFEST.md`, `docs/SEAL_FINAL_CHECK.md`, `docs/TABLE_*.md`, `thesis/figures_seal/**`, and `outputs/seal_checks/seal_final_snapshot.json` if local audit JSON is intentionally tracked outside the remote rule. |
| recommended_freeze_tag | `seal-final-20260228-matrix-20260228_055920_06d6bb` |
| current_matrix_id | `20260228_055920_06d6bb` |
| current_plot_run_id | `20260228_103340_cb1bb1` |

## 2. Canonical Seal Fact Source

The seal truth source is fixed to the seal config set below. Do not treat the default Makefile Step6 targets as seal truth.

- Step6 base: `configs/step6_base.yaml`
- Step6 matrix: `configs/step6_matrix_seal.yaml`
- Step6 experiments mapping: `configs/step6_experiments_seal.yaml`
- Plot config: `scripts/plot_config.yaml`
- Commit-safe pointer docs: `docs/TABLE_MAIN.md`, `docs/TABLE_NUMERIC.md`, `docs/TABLE_ABLATION.md`, `docs/SEAL_*.md`
- Local audit supplement: `outputs/20260228_055920_06d6bb/**`, `outputs/seal_final_smoke/**`, `outputs/20260228_103340_cb1bb1/**`, `outputs/seal_checks/seal_final_snapshot.json`

## 3. Canonical Seal Entry Commands

These are the only canonical seal entry commands to record in the freeze manifest.

1. `python scripts/smoke.py --config configs/smoke.yaml --run-id seal_final_smoke`
2. `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix_seal.yaml`
3. `python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml`
4. `python scripts/plot_all.py --config scripts/plot_config.yaml`

## 4. Non-Commit Artifacts and Reproduction Rules

`outputs/`, `data/`, and `models/` are local-only runtime assets and are not the commit boundary for this repository. The remote repository does not use `outputs/` as the publication surface, so commit-safe evidence must remain anchored in `docs/TABLE_*` and `docs/SEAL_*`. Local `outputs/` artifacts are audit supplements only.

Reproduction rules:

1. Run from repo root with the exact four commands above. `smoke` must run first.
2. Keep the local model path used by the seal matrix available: `models/retriever_ft/20260203_005729_cd195e`.
3. Local runs must write reproducibility artifacts under `outputs/<run_id>/`: `config.yaml`, `logs.txt`, `git_commit.txt` or `unknown`, `seed.txt` when emitted, and metrics/summary files.
4. For audit, preserve `outputs/seal_final_smoke/`, `outputs/20260228_055920_06d6bb/`, `outputs/20260228_103340_cb1bb1/`, and `outputs/seal_checks/seal_final_snapshot.json` until the freeze commit and thesis handoff are done.
5. For commit-safe review, use `docs/TABLE_*` plus `docs/SEAL_FREEZE_MANIFEST.md` and `docs/SEAL_FINAL_CHECK.md` first; only then drill into `outputs/`.

## 5. Makefile Alignment

The default `Makefile` targets `run_matrix_step6` and `make_tables` still point to the non-seal configs `configs/step6_matrix.yaml` and `configs/step6_experiments.yaml`. To avoid breaking existing workflows, new seal targets were added instead of replacing the defaults.

Added seal targets:

- `make seal_smoke`
- `make seal_matrix`
- `make seal_tables`
- `make seal_plots`

Freeze rule: future seal reproductions must use the four canonical commands above or the new `seal_*` targets only.

## 6. Freeze File Inventory

Entry points and dependencies:

- `Makefile`
- `README.md`
- `AGENTS.md`
- `requirements.txt`

Step6/Step7 seal configs:

- `configs/smoke.yaml`
- `configs/step6_base.yaml`
- `configs/step6_matrix_seal.yaml`
- `configs/step6_experiments_seal.yaml`
- `scripts/plot_config.yaml`

Key scripts:

- `scripts/smoke.py`
- `scripts/run_matrix_step6.py`
- `scripts/run_experiment.py`
- `scripts/run_multistep_retrieval.py`
- `scripts/eval_retrieval.py`
- `scripts/eval_numeric.py`
- `scripts/run_calculator.py`
- `scripts/run_with_calculator.py`
- `scripts/make_tables.py`
- `scripts/plot_all.py`
- `scripts/plot_utils.py`

Core `src` modules:

- `src/finder_rag/config.py`
- `src/finder_rag/data.py`
- `src/finder_rag/logging_utils.py`
- `src/finder_rag/metrics.py`
- `src/finder_rag/retrieval.py`
- `src/finder_rag/utils.py`
- `src/retrieval/query_expansion.py`
- `src/multistep/engine.py`
- `src/multistep/planner.py`
- `src/multistep/refiner.py`
- `src/multistep/stop.py`
- `src/calculator/compute.py`
- `src/calculator/extract.py`
- `src/calculator/fact_filter.py`
- `src/calculator/gap.py`
- `src/calculator/value_task.py`

Commit-safe docs pointers:

- `docs/TABLE_MAIN.md`
- `docs/TABLE_NUMERIC.md`
- `docs/TABLE_ABLATION.md`
- `docs/SEAL_ACCEPTANCE_REPORT.md`
- `docs/SEAL_CHECK_comboC.md`
- `docs/SEAL_CHECK_step0_step1.md`
- `docs/SEAL_CHECK_step2_subsets.md`
- `docs/SEAL_CHECK_step3_retriever.md`
- `docs/SEAL_CHECK_step4_step5_ablation.md`
- `docs/SEAL_CHECK_step6_final_gateclear.md`
- `docs/SEAL_CHECK_step6_pqe.md`
- `docs/SEAL_CHECK_step6_pqe_audit.md`
- `docs/SEAL_CHECK_step6_tables.md`
- `docs/SEAL_CHECK_step7_plots.md`
- `docs/SEAL_DECISION.md`
- `docs/SEAL_FINAL_CHECK.md`
- `docs/SEAL_FREEZE_MANIFEST.md`
- `docs/SEAL_LEDGER.md`
- `docs/SEAL_TRACEABILITY.md`

Current `thesis/figures_seal/**` contents:

- `thesis/figures_seal/FIGURE_CATALOG.md`
- `thesis/figures_seal/figures_auto.tex`
- `thesis/figures_seal/ThemeA/figures/ablation_breakdown.pdf`
- `thesis/figures_seal/ThemeA/figures/ablation_breakdown.png`
- `thesis/figures_seal/ThemeA/tables/main_results.csv`
- `thesis/figures_seal/ThemeA/tables/main_results.tex`
- `thesis/figures_seal/ThemeA/figures/abbrev_breakdown.pdf`
- `thesis/figures_seal/ThemeA/figures/abbrev_breakdown.png`

## 7. Risks and Known Differences

1. `docs/SEAL_CHECK_*`, `docs/SEAL_ACCEPTANCE_REPORT.md`, and some earlier `docs/SEAL_*` files predate the current matrix and may still reference older run lists. They remain useful as history, but they are not the freeze truth source for this seal.
2. The exact official `run_matrix_step6` command was started first and created `matrix_id=20260228_055920_06d6bb`. After the terminal wrapper timed out, the remaining runs were completed under the same seal config set and the same `matrix_id`, and then `outputs/20260228_055920_06d6bb/matrix.json` plus `outputs/20260228_055920_06d6bb/experiments_resolved.yaml` were regenerated from the same config. This is auditable, but it is an operational difference from a single uninterrupted matrix invocation.
3. `plot_all.py` emitted `style_not_found` in `outputs/20260228_103340_cb1bb1/logs.txt`, but table/figure outputs were still generated successfully.
4. `scripts/plot_config.yaml` currently enables only `main_results` and `ablation_breakdown`. The older files `thesis/figures_seal/ThemeA/figures/abbrev_breakdown.pdf` and `.png` remain in the tree from a prior run and should be treated as stale, disabled outputs rather than current seal deliverables.
5. `make_tables.py` does not create its own run-scoped `outputs/<run_id>/logs.txt`. Its audit trail in this freeze comes from the updated `docs/TABLE_*.md`, the sealed experiments mapping in `configs/step6_experiments_seal.yaml`, and the run summaries under `outputs/20260228_055920_06d6bb/runs/*/summary.json`.

## 8. Freeze Decision

Ready to freeze.

Blocking conditions remaining before creating the git tag:

- Create the freeze commit from the current worktree.
- Apply the recommended freeze tag.
- If a perfectly clean `thesis/figures_seal/**` tree is required, remove or quarantine the stale disabled `abbrev_breakdown.*` files in a separate follow-up commit.
