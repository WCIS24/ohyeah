# CALC Closure Action Plan

## Scope
- Source run: `m13_pqe_calc`
- Base total queries: `570`
- Evidence JSON: `outputs/seal_checks/calc_closure_action_plan.json`

## Top-3 Bottlenecks (from `calc_diagnosis_metrics.json`)

| Rank | Bottleneck | Count | Ratio | Sample qids (10) | Planned change |
| --- | --- | --- | --- | --- | --- |
| 1 | Task detection miss -> gate_task(unknown) | 432 | 0.7579 | 8c8c8c34, 8b69ba09, 49f441e1, 52e25ec7, f5053c04, 206cf371, a43f933c, 7f2d921c, e8fdc0e5, d4d17284 | Enable calculator.task_parser.mode=v2 with confidence threshold and rule audit. |
| 2 | Fallback extraction mismatch | 146 | 0.2561 | 8b69ba09, e4a78419, 52e25ec7, e8fdc0e5, 939c086f, 3f5148bf, 73a13b04, 84eb41e4, f012ab87, 390a7978 | Reduce fallback by raising valid calc_used ratio; keep extraction strategy auditable. |
| 3 | Calc used but wrong fact selection | 81 | 0.1421 | 4b2b8dc7, 51df659f, 7f09e26f, cd085a74, 6f2e146d, d26e78f3, c9276b6c, 4f7b7ad8, 307ebb9a, 896d72e6 | Add calculator.fact_selector.mode=scored_v1 and auditable pair scoring. |

## Evidence Paths
- `outputs/seal_checks/calc_diagnosis_metrics.json`
- `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04_calc/predictions_calc.jsonl`
- `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04_numeric/numeric_per_query.jsonl`
- `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04_calc/calc_stats.json`
- `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04/summary.json`

## Implementation Mapping
- Bottleneck 1 -> `calculator.task_parser.mode=v2` + `calculator.task_parser.v2.min_conf`.
- Bottleneck 2 -> improve calc hit rate so numeric path depends less on fallback-only text.
- Bottleneck 3 -> `calculator.fact_selector.mode=scored_v1` + score audit in `calc_used_records.jsonl`.

## 2026-02-19 Execution Update
- Implemented and tested:
  - Policy retry path in `src/calculator/compute.py`.
  - Soft fallback + top-groups wiring in `scripts/run_with_calculator.py`.
  - Route-split numeric metrics in `scripts/eval_numeric.py`.
  - New closure matrix `configs/step6_matrix_calc_closure_v1.yaml`.
- Latest closure matrix: `20260219_071245_dd1cc7`.
- Result: no pass candidate under A/B + guardrail (`outputs/seal_checks/calc_closure_compare.json:169`).
- Next priority (if continuing A-path): task coverage expansion (`lookup`) + better fact quality ranking; pure gate tightening is no longer first priority.
