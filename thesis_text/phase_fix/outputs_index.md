# Outputs Index (Phase Fix)

Purpose:
- Provide a single index of run_ids, commands, configs, and key output files for thesis evidence.

How to use:
- Use the run_id and metrics paths as evidence in Phase 2+ writing.

## T1 Smoke
- run_id: 20260202_135956_ff2118
- command: python scripts\smoke.py --config configs\smoke.yaml
- config: configs/smoke.yaml
- outputs:
  - outputs/20260202_135956_ff2118/config.yaml
  - outputs/20260202_135956_ff2118/metrics.json
  - outputs/20260202_135956_ff2118/logs.txt

## T2 Baseline Retrieval
- run_id: 20260202_140330_7c95c6
- command: python scripts\eval_retrieval.py --config configs\eval_retrieval.yaml
- config: configs/eval_retrieval.yaml
- outputs:
  - outputs/20260202_140330_7c95c6/config.yaml
  - outputs/20260202_140330_7c95c6/metrics.json
  - outputs/20260202_140330_7c95c6/per_query_results.jsonl
  - outputs/20260202_140330_7c95c6/logs.txt

## T3 Baseline QA
- run_id (predictions): 20260202_141213_55bae0
- run_id (eval_qa metrics): 20260202_141720_e674e0
- commands:
  - python scripts\run_baseline.py --config configs\run_baseline.yaml
  - python scripts\eval_qa.py --config configs\eval_qa.yaml --predictions outputs\20260202_141213_55bae0\predictions.jsonl --gold data\processed\dev.jsonl
- configs: configs/run_baseline.yaml, configs/eval_qa.yaml
- outputs:
  - outputs/20260202_141213_55bae0/predictions.jsonl
  - outputs/20260202_141720_e674e0/metrics.json
  - outputs/20260202_141720_e674e0/config.yaml
  - outputs/20260202_141720_e674e0/logs.txt

## T4 Multistep + Delta
- run_id (multistep run): 20260202_141735_63db48
- run_id (multistep eval): 20260202_142407_03d6dc
- commands:
  - python scripts\run_multistep_retrieval.py --config configs\run_multistep.yaml
  - python scripts\eval_multistep_retrieval.py --config configs\eval_multistep.yaml --results outputs\20260202_141735_63db48\retrieval_results.jsonl
  - python scripts\check_candidates_count.py --results outputs\20260202_141735_63db48\retrieval_results.jsonl
- config: configs/run_multistep.yaml, configs/eval_multistep.yaml
- outputs:
  - outputs/20260202_141735_63db48/retrieval_results.jsonl
  - outputs/20260202_141735_63db48/multistep_traces.jsonl
  - outputs/20260202_142407_03d6dc/metrics.json
  - outputs/20260202_142407_03d6dc/delta_vs_baseline.json
  - outputs/20260202_141735_63db48/candidate_count_summary.json
  - outputs/20260202_141735_63db48/candidate_count_report.md

## T5 Calculator / Numeric QA
- run_id (calculator run): 20260202_142434_1691cc
- run_id (numeric eval): 20260202_142931_d30d8e
- commands:
  - python scripts\run_with_calculator.py --config configs\run_with_calculator.yaml
  - python scripts\eval_numeric.py --config configs\eval_numeric.yaml --predictions outputs\20260202_142434_1691cc\predictions_calc.jsonl
- config: configs/run_with_calculator.yaml, configs/eval_numeric.yaml
- outputs:
  - outputs/20260202_142434_1691cc/predictions_calc.jsonl
  - outputs/20260202_142931_d30d8e/numeric_metrics.json
  - outputs/20260202_142931_d30d8e/numeric_per_query.jsonl
  - outputs/20260202_142931_d30d8e/config.yaml
  - outputs/20260202_142931_d30d8e/logs.txt
