# Outputs Index (Phase Fix)

Purpose:
- Provide a single index of run_ids, commands, configs, and key output files for thesis evidence.

How to use:
- Use the run_id and metrics paths as evidence in Phase 2+ writing.

## T1 Smoke
- run_id: 20260202_165246_3703da
- command: python scripts\smoke.py --config configs\smoke.yaml
- config: configs/smoke.yaml
- outputs:
  - outputs/20260202_165246_3703da/config.yaml
  - outputs/20260202_165246_3703da/metrics.json
  - outputs/20260202_165246_3703da/logs.txt

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

## Data stats (prepare_data)
- run_id: 20260202_165254_c4b131
- command: python scripts\prepare_data.py --config configs\prepare_data.yaml
- config: configs/prepare_data.yaml
- outputs:
  - outputs/20260202_165254_c4b131/data_stats.json
  - outputs/20260202_165254_c4b131/data_schema.json
  - outputs/20260202_165254_c4b131/config.yaml
  - outputs/20260202_165254_c4b131/logs.txt

## Dev subsets stats (complex/abbrev)
- run_id: 20260202_165303_b04a7b
- command: python scripts\build_subsets.py --config configs\build_subsets.yaml
- config: configs/build_subsets.yaml
- outputs:
  - outputs/20260202_165303_b04a7b/subsets_stats.json
  - data/subsets/dev_complex_qids.txt
  - data/subsets/dev_abbrev_qids.txt

## Data stats (merged for thesis)
- run_id: 20260202_165328_634a0d
- command: python scripts\compute_data_stats.py --config configs\data_stats.yaml
- config: configs/data_stats.yaml
- outputs:
  - docs/data_stats.json
  - outputs/20260202_165328_634a0d/metrics.json
  - outputs/20260202_165328_634a0d/config.yaml
  - outputs/20260202_165328_634a0d/logs.txt

## Main results table (Step6)
- table catalog: thesis/figures/FIGURE_CATALOG.md
- table output: thesis/figures/ThemeA/tables/main_results.csv
- config (run_id list): configs/step6_experiments.yaml
- run_ids expected (currently missing in outputs/):
  - 20260130_014940_21aa62_m01 (pre_ft_baseline)
  - 20260130_014940_21aa62_m02 (post_ft_baseline)
  - 20260130_014940_21aa62_m03 (post_ft_multistep_best)
  - 20260130_014940_21aa62_m04 (post_ft_baseline_calc_best)
  - 20260130_014940_21aa62_m05 (post_ft_multistep_calc_best)
  - 20260130_014940_21aa62_m06 (post_ft_multistep_T1_calc_best)
- commands to generate table once summary.json exists:
  - python scripts\run_matrix_step6.py --base-config configs\step6_base.yaml --matrix configs\step6_matrix.yaml
  - python scripts\make_tables.py --experiments configs\step6_experiments.yaml


## Step6 Runs (Main Results)
- base config: configs/step6_base.yaml
- matrix: configs/step6_matrix.yaml

### pre_ft_baseline
- run_id: 20260130_014940_21aa62_m01
- command: python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=sentence-transformers/all-MiniLM-L6-v2 --overrides multistep.enabled=false --overrides calculator.enabled=false --overrides run_id=20260130_014940_21aa62_m01 --tag pre_ft
- outputs:
  - outputs/20260130_014940_21aa62_m01/summary.json
  - outputs/20260130_014940_21aa62_m01/metrics.json
  - outputs/20260130_014940_21aa62_m01/logs.txt

### post_ft_baseline
- run_id: 20260130_014940_21aa62_m02
- command: python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=models/retriever_ft/latest --overrides multistep.enabled=false --overrides calculator.enabled=false --overrides run_id=20260130_014940_21aa62_m02 --tag post_ft
- outputs:
  - outputs/20260130_014940_21aa62_m02/summary.json
  - outputs/20260130_014940_21aa62_m02/metrics.json
  - outputs/20260130_014940_21aa62_m02/logs.txt

### post_ft_multistep_best
- run_id: 20260130_014940_21aa62_m03
- command: python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=models/retriever_ft/latest --overrides multistep.enabled=true --overrides multistep.max_steps=2 --overrides multistep.top_k_each_step=10 --overrides multistep.novelty_threshold=0.0 --overrides multistep.stop_no_new_steps=1 --overrides multistep.merge_strategy=step1_first --overrides multistep.gate.min_gap_conf=0.3 --overrides calculator.enabled=false --overrides run_id=20260130_014940_21aa62_m03 --tag post_ft_ms
- outputs:
  - outputs/20260130_014940_21aa62_m03/summary.json
  - outputs/20260130_014940_21aa62_m03/metrics.json
  - outputs/20260130_014940_21aa62_m03/logs.txt

### post_ft_baseline_calc_best
- run_id: 20260130_014940_21aa62_m04
- command: python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=models/retriever_ft/latest --overrides multistep.enabled=false --overrides calculator.enabled=true --overrides calculator.gate.min_conf=0.4 --overrides calculator.gate.allow_task_types=[] --overrides run_id=20260130_014940_21aa62_m04 --tag post_ft_calc
- outputs:
  - outputs/20260130_014940_21aa62_m04/summary.json
  - outputs/20260130_014940_21aa62_m04/metrics.json
  - outputs/20260130_014940_21aa62_m04/logs.txt

### post_ft_multistep_calc_best
- run_id: 20260130_014940_21aa62_m05
- command: python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=models/retriever_ft/latest --overrides multistep.enabled=true --overrides multistep.max_steps=2 --overrides multistep.top_k_each_step=10 --overrides multistep.novelty_threshold=0.0 --overrides multistep.stop_no_new_steps=1 --overrides multistep.merge_strategy=step1_first --overrides multistep.gate.min_gap_conf=0.3 --overrides calculator.enabled=true --overrides calculator.gate.min_conf=0.4 --overrides calculator.gate.allow_task_types=[] --overrides run_id=20260130_014940_21aa62_m05 --tag post_ft_ms_calc
- outputs:
  - outputs/20260130_014940_21aa62_m05/summary.json
  - outputs/20260130_014940_21aa62_m05/metrics.json
  - outputs/20260130_014940_21aa62_m05/logs.txt

### post_ft_multistep_T1_calc_best
- run_id: 20260130_014940_21aa62_m06
- command: python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=models/retriever_ft/latest --overrides multistep.enabled=true --overrides multistep.max_steps=1 --overrides multistep.top_k_each_step=10 --overrides multistep.novelty_threshold=0.0 --overrides multistep.stop_no_new_steps=1 --overrides multistep.merge_strategy=step1_first --overrides multistep.gate.min_gap_conf=0.3 --overrides calculator.enabled=true --overrides calculator.gate.min_conf=0.4 --overrides calculator.gate.allow_task_types=[] --overrides run_id=20260130_014940_21aa62_m06 --tag post_ft_ms_T1_calc
- outputs:
  - outputs/20260130_014940_21aa62_m06/summary.json
  - outputs/20260130_014940_21aa62_m06/metrics.json
  - outputs/20260130_014940_21aa62_m06/logs.txt

## Retriever fine-tune (for post_ft runs)
- hard negative mining run_id: 20260203_005224_2417f9
- training run_id: 20260203_005729_cd195e
- commands:
  - python scripts\mine_hard_negatives.py --config configs\mine_hard_negatives.yaml
  - python scripts\train_retriever.py --config configs\train_retriever.yaml
- outputs:
  - outputs/20260203_005224_2417f9/neg_mining_stats.json
  - outputs/20260203_005729_cd195e/metrics.json
  - models/retriever_ft/latest
