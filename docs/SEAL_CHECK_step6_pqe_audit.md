# SEAL Check - Step6 PQE Audit

Date: 2026-02-18
Scope: Prompt #0 audit only (no code edits, no rerun)

## 1) Implementation Effective (with evidence)

Conclusion: `PQE is active and not a silent no-op`.

Chain of entry points (config -> runtime -> output):

1. `qexpand.*` is defined in base config and seal matrix runs.
Evidence: `configs/step6_base.yaml:64-73`, `configs/step6_matrix_seal.yaml:207-249`.
2. Schema has defaults and type checks for `qexpand.*`.
Evidence: `src/config/schema.py:62-69`, `src/config/schema.py:131-138`.
3. Expander is built only when `qexpand.enabled=true`; otherwise `None`.
Evidence: `src/retrieval/query_expansion.py:242-245`.
4. Retriever wiring happens only if expander exists.
Evidence: `scripts/eval_retrieval.py:167-175`, `scripts/run_with_calculator.py:86-90`.
5. Retrieval uses baseline scores first; expansion/boost happens only inside the enabled branch.
Evidence: `src/retrieval/retriever.py:170-171`, `src/retrieval/retriever.py:183-223`.
6. `qexpand_stats.json` is emitted only when PQE is enabled.
Evidence: `scripts/eval_retrieval.py:213-218`.

Artifact-side verification:

1. `m01` (PQE off) logs `qexpand_enabled=False` and has no `qexpand_stats.json`.
Evidence: `outputs/20260218_092521_637290/runs/20260218_092521_637290_m01_retrieval_full/logs.txt:7`,
`outputs/20260218_092521_637290/runs/20260218_092521_637290_m01_retrieval_full` file list lines `1-6`.
2. `m02` (PQE on) logs `qexpand_enabled=True` and writes stats.
Evidence: `outputs/20260218_092521_637290/runs/20260218_092521_637290_m02_retrieval_full/logs.txt:7-8`.
3. `m02` expansion ratio is `483/570 = 0.847`.
Evidence: `outputs/20260218_092521_637290/runs/20260218_092521_637290_m02_retrieval_full/qexpand_stats.json:2-8`.
4. `m03` (abbrev-only) has `prf_year.enabled=false` and expansion ratio only `11/570 = 0.019`.
Evidence: `outputs/20260218_092521_637290/runs/20260218_092521_637290_m03_retrieval_full/config.resolved.yaml:74-75`,
`outputs/20260218_092521_637290/runs/20260218_092521_637290_m03_retrieval_full/qexpand_stats.json:2-8`.

## 2) Metric Change and Interpretation

### 2.1 Baseline vs PQE (`m01 -> m02`)

| split | R@10 delta | MRR@10 delta | interpretation |
|---|---:|---:|---|
| full | +0.0053 | +0.0029 | visible gain |
| complex | +0.0123 | +0.0040 | main gain from PRF-year expansion |
| abbrev | +0.0040 | +0.0030 | improved but below +0.010 target |

Evidence: `outputs/seal_checks/pqe_audit_snapshot.json:10-52`.

### 2.2 Multistep downgrade decision

Conclusion: `multistep can be downgraded to baseline/control`.

1. Dense single-step (`m02`) and multistep (`m05`/`m06`) are near-identical in retrieval metrics.
Evidence: `docs/TABLE_MAIN.md:4`, `docs/TABLE_MAIN.md:7-8`.
2. Gate-open and gate-disabled multistep ablations stay near-identical.
Evidence: `docs/TABLE_MAIN.md:9-12`, `docs/TABLE_ABLATION.md:4-7`.
3. Current seal decision still marks multistep closure as failed.
Evidence: `docs/SEAL_DECISION.md:15-23`, `docs/SEAL_DECISION.md:41`.

### 2.3 Malformed override `m04` and replacement by `m05`

Conclusion: `m04 is invalid for acceptance; m05 is the clean replacement`.

1. `m04` has config type issue (`allow_task_types` parsed as string).
Evidence: `outputs/20260218_092521_637290/runs/20260218_092521_637290_m04/logs.txt:7`,
`outputs/20260218_092521_637290/runs/20260218_092521_637290_m04/config.resolved.yaml:52`.
2. `m05` has correct list type for `allow_task_types`.
Evidence: `outputs/20260218_092521_637290/runs/20260218_092521_637290_m05/config.resolved.yaml:52-54`.
3. Snapshot marks `m04` separately as invalid and uses `m05` for PQE+calc comparison.
Evidence: `outputs/seal_checks/pqe_audit_snapshot.json:2-9`.

## 3) Calculator Interaction Risk (initial diagnosis)

Observed interaction: under PQE+calc (`m05`) vs calc baseline (`m08`), `coverage` rises but `numeric_em` drops.
Evidence: `outputs/seal_checks/pqe_audit_snapshot.json:74-90`, `docs/TABLE_NUMERIC.md:14`.

Risk classes:

1. `task detection / gate dominance` (high likelihood)
`unknown` task volume is high and `gate_task_ratio` does not improve (`0.8158 -> 0.8158`).
Evidence: `outputs/20260218_092521_637290/runs/20260218_092521_637290_m05_calc/calc_stats.json:10-17`,
`outputs/seal_checks/pqe_audit_snapshot.json:77-90`,
`src/calculator/compute.py:49-59`,
`src/calculator/compute.py:577-589`,
`scripts/run_with_calculator.py:264-266`.
2. `fact selection / numeric noise` (high likelihood)
Facts are extracted from all retrieved chunks with no top-N cap.
Evidence: `scripts/run_with_calculator.py:225-231`.
3. `numeric eval extraction artifact` (high risk)
Eval uses first extracted number (`pred_nums[0]`, `gold_nums[0]`), which can be off-target.
Evidence: `scripts/eval_numeric.py:221-230`, `scripts/eval_numeric.py:267-271`.
4. `subset construction bug` (high risk, affects complex and multistep interpretation)
`YEAR_RE` uses capturing group with `findall()`, so two-year detection can collapse to `19/20`.
Evidence: `scripts/build_subsets.py:20`, `scripts/build_subsets.py:74-76`.

## 4) Minimal Next Diagnostics (3-6 items)

1. D1: per-query split by `calc_used` vs `fallback_reason` for `numeric_em` and coverage.
Evidence basis: `scripts/run_with_calculator.py:294-302`, `scripts/eval_numeric.py:205`, `scripts/eval_numeric.py:251-265`.
2. D2: noise sensitivity with `calculator.evidence.max_chunks_for_facts` at N=`1/5/10`.
Evidence basis: current all-chunk extraction `scripts/run_with_calculator.py:225-231`.
3. D3: compare extraction policy in numeric eval (`first-number` vs `Result:`-first).
Evidence basis: `scripts/eval_numeric.py:229-230`, `scripts/run_with_calculator.py:286`.
4. D4: fix subset year regex and rebuild subsets before reevaluating `m02/m11/m12`.
Evidence basis: `scripts/build_subsets.py:20`, `scripts/build_subsets.py:74-76`.
5. D5: register `m11/m12/m13` into seal experiments and regenerate tables.
Evidence basis: defined in matrix `configs/step6_matrix_seal.yaml:207-249`,
missing from experiments `configs/step6_experiments_seal.yaml:1-52`.

---

Seal readiness (current): `Not Ready`.
Primary blockers are evaluation/protocol risks in calculator and subset logic, not PQE trigger failure itself.
