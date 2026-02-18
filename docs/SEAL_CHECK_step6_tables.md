# SEAL Check - Step6 (make_tables consistency)

Date: 2026-02-18  
Checked target: `configs/step6_experiments_seal.yaml`

## 0) Verdict

Verdict: `PASS`.

- `make_tables` regenerates all 3 tables without code changes.
- All 11 `summary.json` inputs referenced by `step6_experiments_seal.yaml` exist.
- `abbrev` metrics are present in generated main/ablation tables.

---

## 1) Reproducible command

```bash
python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml
```

Evidence:
- CLI argument (`--experiments`): `scripts/make_tables.py:11` to `scripts/make_tables.py:14`
- Reads experiments YAML: `scripts/make_tables.py:37` to `scripts/make_tables.py:39`
- Writes fixed docs outputs:
  - `docs/TABLE_MAIN.md`
  - `docs/TABLE_NUMERIC.md`
  - `docs/TABLE_ABLATION.md`
  - code: `scripts/make_tables.py:90` to `scripts/make_tables.py:122`

---

## 2) Input dependency list

Source experiment list:
- `configs/step6_experiments_seal.yaml:1` to `configs/step6_experiments_seal.yaml:31`

Per-run input path rule in `make_tables`:
- `outputs/<run_id>/summary.json`
- code: `scripts/make_tables.py:48` to `scripts/make_tables.py:51`

Dependencies used by this Step6 table run:

| label | run_id | summary input file |
|---|---|---|
| seal_mvp01_preft_dense_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01/summary.json` |
| seal_mvp02_dense_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json` |
| seal_mvp03_bm25_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json` |
| seal_mvp04_hybrid_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json` |
| seal_mvp05_dense_multistep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05/summary.json` |
| seal_mvp06_dense_multistep_t1 | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06/summary.json` |
| seal_mvp07_dense_calc_empty_allow | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/summary.json` |
| seal_mvp08_dense_calc_allow_yoy_diff | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json` |
| seal_mvp08b_dense_calc_gate_off | `20260217_174322_d71045/runs/20260217_174322_d71045_m01` | `outputs/20260217_174322_d71045/runs/20260217_174322_d71045_m01/summary.json` |
| seal_mvp09_dense_multistep_calc | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09/summary.json` |
| seal_mvp10_dense_multistep_t1_calc | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10/summary.json` |

Existence verification log:
- `outputs/seal_checks/step6_tables_inputs.log:1` to `outputs/seal_checks/step6_tables_inputs.log:11`

---

## 3) Table field dictionary

### 3.1 `docs/TABLE_MAIN.md`

Code path:
- row build: `scripts/make_tables.py:59` to `scripts/make_tables.py:69`
- header/write: `scripts/make_tables.py:90` to `scripts/make_tables.py:103`

| table column | source in `summary.json` | code evidence |
|---|---|---|
| `label` | `experiments[].label` | `scripts/make_tables.py:46`, `scripts/make_tables.py:61` |
| `run_id` | `experiments[].run_id` | `scripts/make_tables.py:45`, `scripts/make_tables.py:62` |
| `full_r10` | `metrics.retrieval_full.recall@10` | `scripts/make_tables.py:54`, `scripts/make_tables.py:63` |
| `full_mrr10` | `metrics.retrieval_full.mrr@10` | `scripts/make_tables.py:54`, `scripts/make_tables.py:64` |
| `complex_r10` | `metrics.retrieval_complex.recall@10` | `scripts/make_tables.py:55`, `scripts/make_tables.py:65` |
| `complex_mrr10` | `metrics.retrieval_complex.mrr@10` | `scripts/make_tables.py:55`, `scripts/make_tables.py:66` |
| `abbrev_r10` | `metrics.retrieval_abbrev.recall@10` | `scripts/make_tables.py:56`, `scripts/make_tables.py:67` |
| `abbrev_mrr10` | `metrics.retrieval_abbrev.mrr@10` | `scripts/make_tables.py:56`, `scripts/make_tables.py:68` |

### 3.2 `docs/TABLE_NUMERIC.md`

Code path:
- row build: `scripts/make_tables.py:71` to `scripts/make_tables.py:78`
- header/write: `scripts/make_tables.py:104` to `scripts/make_tables.py:108`

| table column | source in `summary.json` | code evidence |
|---|---|---|
| `num_em` | `metrics.numeric_dev.numeric_em` | `scripts/make_tables.py:57`, `scripts/make_tables.py:75` |
| `num_rel` | `metrics.numeric_dev.rel_error_mean` | `scripts/make_tables.py:57`, `scripts/make_tables.py:76` |
| `num_cov` | `metrics.numeric_dev.coverage` | `scripts/make_tables.py:57`, `scripts/make_tables.py:77` |

### 3.3 `docs/TABLE_ABLATION.md`

Code path:
- subset filter: `group == "ablation"`: `scripts/make_tables.py:80` to `scripts/make_tables.py:81`
- header/write: `scripts/make_tables.py:109` to `scripts/make_tables.py:122`

Meaning:
- Uses the same retrieval columns as `TABLE_MAIN`, but only for experiments with
  `group: ablation` in `configs/step6_experiments_seal.yaml`.

---

## 4) Consistency checks

Check criteria:
- `TABLE_MAIN` run order equals `experiments` run order
- `TABLE_NUMERIC` run order equals `experiments` run order
- `TABLE_ABLATION` run order equals experiments where `group == ablation`
- `abbrev` columns present in main and ablation tables

Check result:
- `main_eq_experiments=True`
- `numeric_eq_experiments=True`
- `ablation_eq_group_subset=True`
- counts: main=11, ablation=4, numeric=11

Evidence:
- consistency log: `outputs/seal_checks/step6_tables_consistency.log:1` to `outputs/seal_checks/step6_tables_consistency.log:6`
- abbrev columns in main table header: `docs/TABLE_MAIN.md:1`
- abbrev columns in ablation table header: `docs/TABLE_ABLATION.md:1`

Seal matrix alignment note (`run_id` target):
- Most experiments point to seal matrix `20260217_123645_68f6b9`:
  `configs/step6_experiments_seal.yaml:3` to `configs/step6_experiments_seal.yaml:25`,
  `configs/step6_experiments_seal.yaml:29` to `configs/step6_experiments_seal.yaml:33`
- Action1 diagnostic run `seal_mvp08b_dense_calc_gate_off` points to one-run matrix
  `20260217_174322_d71045`:
  `configs/step6_experiments_seal.yaml:26` to `configs/step6_experiments_seal.yaml:28`
- Matrix configs:
  - seal matrix: `outputs/20260217_123645_68f6b9/matrix.json:6`
  - action1 one-run matrix: `outputs/20260217_174322_d71045/matrix.json:6`

---

## 5) Final status for Step6 tables

- `make_tables` consistency check passes.
- Fixed reproducible command:

```bash
python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml
```

- Fixed output files:
  - `docs/TABLE_MAIN.md`
  - `docs/TABLE_NUMERIC.md`
  - `docs/TABLE_ABLATION.md`
