# Milestone Evidence Map

Generated (UTC): 2026-02-18T17:46:57.199369+00:00

## Traceability Gate
- Status: OK
- rows_checked: 52
- blockers: 0
- Source mapping: `configs/step6_experiments_seal.yaml`
- Source tables: `docs/TABLE_MAIN.md`, `docs/TABLE_NUMERIC.md`, `docs/TABLE_ABLATION.md`

## Module Evidence Table
| Module | Defect | Implementation (<=3 refs) | Ablation design (run_id) | Metrics and conclusion |
| --- | --- | --- | --- | --- |
| Query preprocessing (PQE) | Single-query retrieval misses year constraints and acronym expansions, hurting complex and abbrev recall. | `src/retrieval/query_expansion.py:71-77`<br>`src/retrieval/query_expansion.py:149-173`<br>`scripts/eval_retrieval.py:72-103` | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02`<br>`20260218_160058_ee7290/runs/20260218_160058_ee7290_m03` | full/complex/abbrev R@10=0.3789/0.3951/0.3713<br>Conclusion=Moderate<br>m11_pqe vs m12_pqe_abbrev_only: complex R@10 +0.0123; prf_year_expanded_count 0 -> 483 (evidence: outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m02_retrieval_full/qexpand_stats.json, outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m03_retrieval_full/qexpand_stats.json). |
| Retriever FT and mode (pre-FT/post-FT, dense/bm25/hybrid) | Pre-FT and sparse retrieval underperform for semantic finance QA. | `src/retrieval/retriever.py:141-161`<br>`src/retrieval/retriever.py:153-160`<br>`scripts/run_experiment.py:233-288` | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01`<br>`20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03`<br>`20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04` | full/complex/abbrev R@10=0.3246/0.3457/0.3174<br>Conclusion=Strong<br>m02_postFT_dense vs m01_preFT_dense: full R@10 +0.0544, complex R@10 +0.0494, abbrev R@10 +0.0539 (evidence: docs/TABLE_MAIN.md:3-6 and mapped summary.json files). |
| Replacement module (PQE vs multistep baseline) | Multistep adds orchestration complexity with limited retrieval gain. | `src/multistep/engine.py:114-148`<br>`scripts/run_experiment.py:129-167`<br>`src/retrieval/retriever.py:183-210` | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05`<br>`20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06` | full/complex/abbrev R@10=0.3789/0.3951/0.3713<br>Conclusion=Moderate<br>m11_pqe vs m05_multistep: complex R@10 +0.0123, full R@10 +0.0053 (evidence: outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m02/summary.json, outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05/summary.json). |
| Calculator gate / allow_task_types / fallback | Calculator dispatch is fallback-heavy; coverage/EM tradeoff remains unresolved. | `src/calculator/compute.py:49-59`<br>`src/calculator/compute.py:572-669`<br>`scripts/run_with_calculator.py:255-325` | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07`<br>`20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08`<br>`20260217_174322_d71045/runs/20260217_174322_d71045_m01`<br>`20260218_032001_2056e7/runs/20260218_032001_2056e7_m03` | full/complex/abbrev R@10=0.3789/0.3951/0.3713<br>numeric delta m13-m08: coverage=0.0172, EM=-0.0118<br>Conclusion=Negative<br>m13_pqe_calc vs m08_allow_yoy_diff: coverage +0.0172, EM -0.0118; gate_task fallback m07=570, m08=465, m08d=432, m13=465 (evidence: calc_stats.json under each run _calc folder). |
| Numeric extraction strategy (first vs result_tag) | Numeric extraction can pick non-answer numbers unless strategy is explicit and auditable. | `scripts/eval_numeric.py:149-167`<br>`scripts/eval_numeric.py:170-200`<br>`scripts/eval_numeric.py:298-332` | `seal_a2_numeric_first`<br>`seal_a2_numeric_result_tag`<br>`20260218_160058_ee7290/runs/20260218_160058_ee7290_m04` | full/complex/abbrev R@10=0.3842/0.4074/0.3752<br>numeric delta result_tag-first: coverage=0.0000, EM=0.0000<br>Conclusion=Weak<br>result_tag vs first: delta coverage=0.0000, delta EM=0.0000, query-level diffs=30 (evidence: outputs/seal_checks/numeric_extraction_strategy_compare.json). |
| Subset protocol (complex/abbrev/numeric, subsets_v2) | Subset definitions require versioned rules and pinned paths to avoid evaluation drift. | `scripts/build_subsets.py:23-61`<br>`scripts/build_subsets.py:162-170`<br>`scripts/run_experiment.py:247-281` | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02`<br>`20260218_160058_ee7290/runs/20260218_160058_ee7290_m02` | full/complex/abbrev R@10=0.3789/0.3951/0.3713<br>subset sizes c/a/n=243/501/466<br>Conclusion=Strong<br>subsets_v2 counts: complex=243, abbrev=501, numeric=466; rule_hits.two_years=49 (evidence: data/subsets_v2/subsets_stats.json and outputs/20260218_160058_ee7290/matrix.json). |

## Risks And Limits
### Query preprocessing (PQE)
- Conclusion level: Moderate
- Risks/limits:
  - No multi-seed variance estimate is reported.
  - boost=0.15 is not sensitivity-tested in this gate set.
- Next steps:
  - Run seed sweep for m11 vs m12 under subsets_v2.
  - Tune qexpand.boost and seed_top_k with fixed retriever weights.
### Retriever FT and mode (pre-FT/post-FT, dense/bm25/hybrid)
- Conclusion level: Strong
- Risks/limits:
  - Single-seed comparison only.
  - Latency/cost across dense, bm25, hybrid is not in this map.
- Next steps:
  - Add significance tests and confidence bands.
  - Add runtime and memory profiling for each retrieval mode.
### Replacement module (PQE vs multistep baseline)
- Conclusion level: Moderate
- Risks/limits:
  - No wall-clock comparison between multistep and PQE in this artifact.
  - Effect size is moderate; more stability testing is needed.
- Next steps:
  - Report runtime/cost for m05/m06 vs m11/m12.
  - Audit multistep gate behavior with trace-level error buckets.
### Calculator gate / allow_task_types / fallback
- Conclusion level: Negative
- Risks/limits:
  - Task detector still yields many non-actionable cases.
  - Gate thresholds are not tuned on a coverage/EM Pareto frontier.
- Next steps:
  - Refine task classification before calculator invocation.
  - Tune gate and allow_task_types jointly with held-out numeric split.
### Numeric extraction strategy (first vs result_tag)
- Conclusion level: Weak
- Risks/limits:
  - Aggregate metrics unchanged despite query-level differences.
  - Regex-based extraction remains brittle on noisy generated text.
- Next steps:
  - Add structured numeric output tags from calculator.
  - Evaluate hybrid extraction with unit/year constraints.
### Subset protocol (complex/abbrev/numeric, subsets_v2)
- Conclusion level: Strong
- Risks/limits:
  - No explicit old-vs-v2 replay in the same run bundle.
  - Regex heuristics may miss edge linguistic patterns.
- Next steps:
  - Version and diff subset rules in CI.
  - Add sampled manual QA over subset assignments.

## End-to-End Narrative
The chain starts from query preprocessing and retrieval selection: post-FT dense is the base, then PQE toggles abbreviation/year expansion before ranking. The retrieval table rows map one-to-one to run outputs, and PQE shows moderate gains over abbrev-only and multistep baselines on complex and abbrev subsets.
For numeric tasks, calculator gate/allow_task_types controls whether to trust computed results or fallback text. Current gate settings improve coverage but reduce EM, while extraction strategy is now auditable via explicit fields. subsets_v2 protocol pins complex/abbrev/numeric paths in the seal matrix so evaluation scope remains reproducible.

## Traceability Appendix
| table | line | label | run_id | summary | exists |
| --- | --- | --- | --- | --- | --- |
| MAIN | 3 | seal_mvp01_preft_dense_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01/summary.json` | yes |
| MAIN | 4 | seal_mvp02_dense_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json` | yes |
| MAIN | 5 | seal_mvp03_bm25_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json` | yes |
| MAIN | 6 | seal_mvp04_hybrid_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json` | yes |
| MAIN | 7 | seal_mvp05_dense_multistep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05/summary.json` | yes |
| MAIN | 8 | seal_mvp06_dense_multistep_t1 | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06/summary.json` | yes |
| MAIN | 9 | seal_mvp05b_dense_multistep_gate_open | `20260218_023916_906096/runs/20260218_023916_906096_m01` | `outputs/20260218_023916_906096/runs/20260218_023916_906096_m01/summary.json` | yes |
| MAIN | 10 | seal_mvp06b_dense_multistep_t1_gate_open | `20260218_023916_906096/runs/20260218_023916_906096_m02` | `outputs/20260218_023916_906096/runs/20260218_023916_906096_m02/summary.json` | yes |
| MAIN | 11 | seal_mvp05c_dense_multistep_gate_disabled | `20260218_032001_2056e7/runs/20260218_032001_2056e7_m01` | `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m01/summary.json` | yes |
| MAIN | 12 | seal_mvp06c_dense_multistep_t1_gate_disabled | `20260218_032001_2056e7/runs/20260218_032001_2056e7_m02` | `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m02/summary.json` | yes |
| MAIN | 13 | seal_mvp07_dense_calc_empty_allow | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/summary.json` | yes |
| MAIN | 14 | seal_mvp08_dense_calc_allow_yoy_diff | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json` | yes |
| MAIN | 15 | seal_mvp08b_dense_calc_gate_off | `20260217_174322_d71045/runs/20260217_174322_d71045_m01` | `outputs/20260217_174322_d71045/runs/20260217_174322_d71045_m01/summary.json` | yes |
| MAIN | 16 | seal_mvp08c_dense_calc_minconf_02 | `20260218_012802_326769/runs/20260218_012802_326769_m01` | `outputs/20260218_012802_326769/runs/20260218_012802_326769_m01/summary.json` | yes |
| MAIN | 17 | seal_mvp08d_dense_calc_expand_tasks | `20260218_032001_2056e7/runs/20260218_032001_2056e7_m03` | `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m03/summary.json` | yes |
| MAIN | 18 | seal_mvp09_dense_multistep_calc | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09/summary.json` | yes |
| MAIN | 19 | seal_mvp10_dense_multistep_t1_calc | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10/summary.json` | yes |
| MAIN | 20 | m11_pqe | `20260218_160058_ee7290/runs/20260218_160058_ee7290_m02` | `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m02/summary.json` | yes |
| MAIN | 21 | m12_pqe_abbrev_only | `20260218_160058_ee7290/runs/20260218_160058_ee7290_m03` | `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m03/summary.json` | yes |
| MAIN | 22 | m13_pqe_calc | `20260218_160058_ee7290/runs/20260218_160058_ee7290_m04` | `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04/summary.json` | yes |
| NUM | 3 | seal_mvp01_preft_dense_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01/summary.json` | yes |
| NUM | 4 | seal_mvp02_dense_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json` | yes |
| NUM | 5 | seal_mvp03_bm25_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json` | yes |
| NUM | 6 | seal_mvp04_hybrid_singlestep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json` | yes |
| NUM | 7 | seal_mvp05_dense_multistep | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05/summary.json` | yes |
| NUM | 8 | seal_mvp06_dense_multistep_t1 | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06/summary.json` | yes |
| NUM | 9 | seal_mvp05b_dense_multistep_gate_open | `20260218_023916_906096/runs/20260218_023916_906096_m01` | `outputs/20260218_023916_906096/runs/20260218_023916_906096_m01/summary.json` | yes |
| NUM | 10 | seal_mvp06b_dense_multistep_t1_gate_open | `20260218_023916_906096/runs/20260218_023916_906096_m02` | `outputs/20260218_023916_906096/runs/20260218_023916_906096_m02/summary.json` | yes |
| NUM | 11 | seal_mvp05c_dense_multistep_gate_disabled | `20260218_032001_2056e7/runs/20260218_032001_2056e7_m01` | `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m01/summary.json` | yes |
| NUM | 12 | seal_mvp06c_dense_multistep_t1_gate_disabled | `20260218_032001_2056e7/runs/20260218_032001_2056e7_m02` | `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m02/summary.json` | yes |
| NUM | 13 | seal_mvp07_dense_calc_empty_allow | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/summary.json` | yes |
| NUM | 14 | seal_mvp08_dense_calc_allow_yoy_diff | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json` | yes |
| NUM | 15 | seal_mvp08b_dense_calc_gate_off | `20260217_174322_d71045/runs/20260217_174322_d71045_m01` | `outputs/20260217_174322_d71045/runs/20260217_174322_d71045_m01/summary.json` | yes |
| NUM | 16 | seal_mvp08c_dense_calc_minconf_02 | `20260218_012802_326769/runs/20260218_012802_326769_m01` | `outputs/20260218_012802_326769/runs/20260218_012802_326769_m01/summary.json` | yes |
| NUM | 17 | seal_mvp08d_dense_calc_expand_tasks | `20260218_032001_2056e7/runs/20260218_032001_2056e7_m03` | `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m03/summary.json` | yes |
| NUM | 18 | seal_mvp09_dense_multistep_calc | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09/summary.json` | yes |
| NUM | 19 | seal_mvp10_dense_multistep_t1_calc | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10/summary.json` | yes |
| NUM | 20 | m11_pqe | `20260218_160058_ee7290/runs/20260218_160058_ee7290_m02` | `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m02/summary.json` | yes |
| NUM | 21 | m12_pqe_abbrev_only | `20260218_160058_ee7290/runs/20260218_160058_ee7290_m03` | `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m03/summary.json` | yes |
| NUM | 22 | m13_pqe_calc | `20260218_160058_ee7290/runs/20260218_160058_ee7290_m04` | `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04/summary.json` | yes |
| ABL | 3 | seal_mvp06_dense_multistep_t1 | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06/summary.json` | yes |
| ABL | 4 | seal_mvp05b_dense_multistep_gate_open | `20260218_023916_906096/runs/20260218_023916_906096_m01` | `outputs/20260218_023916_906096/runs/20260218_023916_906096_m01/summary.json` | yes |
| ABL | 5 | seal_mvp06b_dense_multistep_t1_gate_open | `20260218_023916_906096/runs/20260218_023916_906096_m02` | `outputs/20260218_023916_906096/runs/20260218_023916_906096_m02/summary.json` | yes |
| ABL | 6 | seal_mvp05c_dense_multistep_gate_disabled | `20260218_032001_2056e7/runs/20260218_032001_2056e7_m01` | `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m01/summary.json` | yes |
| ABL | 7 | seal_mvp06c_dense_multistep_t1_gate_disabled | `20260218_032001_2056e7/runs/20260218_032001_2056e7_m02` | `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m02/summary.json` | yes |
| ABL | 8 | seal_mvp07_dense_calc_empty_allow | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/summary.json` | yes |
| ABL | 9 | seal_mvp08b_dense_calc_gate_off | `20260217_174322_d71045/runs/20260217_174322_d71045_m01` | `outputs/20260217_174322_d71045/runs/20260217_174322_d71045_m01/summary.json` | yes |
| ABL | 10 | seal_mvp08c_dense_calc_minconf_02 | `20260218_012802_326769/runs/20260218_012802_326769_m01` | `outputs/20260218_012802_326769/runs/20260218_012802_326769_m01/summary.json` | yes |
| ABL | 11 | seal_mvp08d_dense_calc_expand_tasks | `20260218_032001_2056e7/runs/20260218_032001_2056e7_m03` | `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m03/summary.json` | yes |
| ABL | 12 | seal_mvp10_dense_multistep_t1_calc | `20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10` | `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10/summary.json` | yes |
| ABL | 13 | m12_pqe_abbrev_only | `20260218_160058_ee7290/runs/20260218_160058_ee7290_m03` | `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m03/summary.json` | yes |
| ABL | 14 | m13_pqe_calc | `20260218_160058_ee7290/runs/20260218_160058_ee7290_m04` | `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04/summary.json` | yes |
