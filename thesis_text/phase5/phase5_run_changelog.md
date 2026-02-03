# Phase 5 Run Changelog
Purpose:
- ?? Step6 ??? run ????????????
How to use:
- ???????????????

## pre_ft_baseline (20260130_014940_21aa62_m01)
- command: `python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=sentence-transformers/all-MiniLM-L6-v2 --overrides multistep.enabled=false --overrides calculator.enabled=false --overrides run_id=20260130_014940_21aa62_m01 --tag pre_ft`
- outputs: outputs/20260130_014940_21aa62_m01
- output tree (top-level):
  - config.resolved.yaml
  - config.retrieval_complex.yaml
  - config.retrieval_full.yaml
  - config.yaml
  - git_commit.txt
  - logs.txt
  - metrics.json
  - summary.json
- key files:
  - outputs/20260130_014940_21aa62_m01/metrics.json
  - outputs/20260130_014940_21aa62_m01/summary.json
  - outputs/20260130_014940_21aa62_m01/logs.txt
- subruns: {'retrieval_full': '20260130_014940_21aa62_m01_retrieval_full', 'retrieval_complex': '20260130_014940_21aa62_m01_retrieval_complex'}
- metrics keys:
  - retrieval_full: ['alpha', 'evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mode', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio']
  - retrieval_complex: ['alpha', 'evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mode', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio']
  - numeric_dev: []

## post_ft_baseline (20260130_014940_21aa62_m02)
- command: `python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=models/retriever_ft/latest --overrides multistep.enabled=false --overrides calculator.enabled=false --overrides run_id=20260130_014940_21aa62_m02 --tag post_ft`
- outputs: outputs/20260130_014940_21aa62_m02
- output tree (top-level):
  - config.resolved.yaml
  - config.retrieval_complex.yaml
  - config.retrieval_full.yaml
  - config.yaml
  - git_commit.txt
  - logs.txt
  - metrics.json
  - summary.json
- key files:
  - outputs/20260130_014940_21aa62_m02/metrics.json
  - outputs/20260130_014940_21aa62_m02/summary.json
  - outputs/20260130_014940_21aa62_m02/logs.txt
- subruns: {'retrieval_full': '20260130_014940_21aa62_m02_retrieval_full', 'retrieval_complex': '20260130_014940_21aa62_m02_retrieval_complex'}
- metrics keys:
  - retrieval_full: ['alpha', 'evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mode', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio']
  - retrieval_complex: ['alpha', 'evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mode', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio']
  - numeric_dev: []

## post_ft_multistep_best (20260130_014940_21aa62_m03)
- command: `python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=models/retriever_ft/latest --overrides multistep.enabled=true --overrides multistep.max_steps=2 --overrides multistep.top_k_each_step=10 --overrides multistep.novelty_threshold=0.0 --overrides multistep.stop_no_new_steps=1 --overrides multistep.merge_strategy=step1_first --overrides multistep.gate.min_gap_conf=0.3 --overrides calculator.enabled=false --overrides run_id=20260130_014940_21aa62_m03 --tag post_ft_ms`
- outputs: outputs/20260130_014940_21aa62_m03
- output tree (top-level):
  - config.ms.yaml
  - config.ms_eval_complex.yaml
  - config.ms_eval_full.yaml
  - config.resolved.yaml
  - config.yaml
  - git_commit.txt
  - logs.txt
  - metrics.json
  - summary.json
- key files:
  - outputs/20260130_014940_21aa62_m03/metrics.json
  - outputs/20260130_014940_21aa62_m03/summary.json
  - outputs/20260130_014940_21aa62_m03/logs.txt
- subruns: {'multistep': '20260130_014940_21aa62_m03_ms', 'retrieval_full': '20260130_014940_21aa62_m03_ms_eval_full', 'retrieval_complex': '20260130_014940_21aa62_m03_ms_eval_complex'}
- metrics keys:
  - retrieval_full: ['evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio', 'use_collected']
  - retrieval_complex: ['evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio', 'use_collected']
  - numeric_dev: []

## post_ft_baseline_calc_best (20260130_014940_21aa62_m04)
- command: `python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=models/retriever_ft/latest --overrides multistep.enabled=false --overrides calculator.enabled=true --overrides calculator.gate.min_conf=0.4 --overrides calculator.gate.allow_task_types=[] --overrides run_id=20260130_014940_21aa62_m04 --tag post_ft_calc`
- outputs: outputs/20260130_014940_21aa62_m04
- output tree (top-level):
  - config.calc.yaml
  - config.numeric.yaml
  - config.numeric_full.yaml
  - config.resolved.yaml
  - config.retrieval_complex.yaml
  - config.retrieval_full.yaml
  - config.yaml
  - git_commit.txt
  - logs.txt
  - metrics.json
  - summary.json
- key files:
  - outputs/20260130_014940_21aa62_m04/metrics.json
  - outputs/20260130_014940_21aa62_m04/summary.json
  - outputs/20260130_014940_21aa62_m04/logs.txt
- subruns: {'retrieval_full': '20260130_014940_21aa62_m04_retrieval_full', 'retrieval_complex': '20260130_014940_21aa62_m04_retrieval_complex', 'calculator': '20260130_014940_21aa62_m04_calc', 'numeric_dev': '20260130_014940_21aa62_m04_numeric', 'numeric_full': '20260130_014940_21aa62_m04_numeric_full'}
- metrics keys:
  - retrieval_full: ['alpha', 'evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mode', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio']
  - retrieval_complex: ['alpha', 'evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mode', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio']
  - numeric_dev: ['abs_error_mean', 'abs_error_median', 'coverage', 'missing_gold', 'missing_pred', 'multi_gold', 'multi_pred', 'numeric_em', 'predictions_path', 'rel_error_mean', 'rel_error_median', 'total_queries']

## post_ft_multistep_calc_best (20260130_014940_21aa62_m05)
- command: `python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=models/retriever_ft/latest --overrides multistep.enabled=true --overrides multistep.max_steps=2 --overrides multistep.top_k_each_step=10 --overrides multistep.novelty_threshold=0.0 --overrides multistep.stop_no_new_steps=1 --overrides multistep.merge_strategy=step1_first --overrides multistep.gate.min_gap_conf=0.3 --overrides calculator.enabled=true --overrides calculator.gate.min_conf=0.4 --overrides calculator.gate.allow_task_types=[] --overrides run_id=20260130_014940_21aa62_m05 --tag post_ft_ms_calc`
- outputs: outputs/20260130_014940_21aa62_m05
- output tree (top-level):
  - config.calc.yaml
  - config.ms.yaml
  - config.ms_eval_complex.yaml
  - config.ms_eval_full.yaml
  - config.numeric.yaml
  - config.numeric_full.yaml
  - config.resolved.yaml
  - config.yaml
  - git_commit.txt
  - logs.txt
  - metrics.json
  - summary.json
- key files:
  - outputs/20260130_014940_21aa62_m05/metrics.json
  - outputs/20260130_014940_21aa62_m05/summary.json
  - outputs/20260130_014940_21aa62_m05/logs.txt
- subruns: {'multistep': '20260130_014940_21aa62_m05_ms', 'retrieval_full': '20260130_014940_21aa62_m05_ms_eval_full', 'retrieval_complex': '20260130_014940_21aa62_m05_ms_eval_complex', 'calculator': '20260130_014940_21aa62_m05_calc', 'numeric_dev': '20260130_014940_21aa62_m05_numeric', 'numeric_full': '20260130_014940_21aa62_m05_numeric_full'}
- metrics keys:
  - retrieval_full: ['evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio', 'use_collected']
  - retrieval_complex: ['evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio', 'use_collected']
  - numeric_dev: ['abs_error_mean', 'abs_error_median', 'coverage', 'missing_gold', 'missing_pred', 'multi_gold', 'multi_pred', 'numeric_em', 'predictions_path', 'rel_error_mean', 'rel_error_median', 'total_queries']

## post_ft_multistep_T1_calc_best (20260130_014940_21aa62_m06)
- command: `python scripts\run_experiment.py --config configs\step6_base.yaml --overrides retriever.dense.model_name_or_path=models/retriever_ft/latest --overrides multistep.enabled=true --overrides multistep.max_steps=1 --overrides multistep.top_k_each_step=10 --overrides multistep.novelty_threshold=0.0 --overrides multistep.stop_no_new_steps=1 --overrides multistep.merge_strategy=step1_first --overrides multistep.gate.min_gap_conf=0.3 --overrides calculator.enabled=true --overrides calculator.gate.min_conf=0.4 --overrides calculator.gate.allow_task_types=[] --overrides run_id=20260130_014940_21aa62_m06 --tag post_ft_ms_T1_calc`
- outputs: outputs/20260130_014940_21aa62_m06
- output tree (top-level):
  - config.calc.yaml
  - config.ms.yaml
  - config.ms_eval_complex.yaml
  - config.ms_eval_full.yaml
  - config.numeric.yaml
  - config.numeric_full.yaml
  - config.resolved.yaml
  - config.yaml
  - git_commit.txt
  - logs.txt
  - metrics.json
  - summary.json
- key files:
  - outputs/20260130_014940_21aa62_m06/metrics.json
  - outputs/20260130_014940_21aa62_m06/summary.json
  - outputs/20260130_014940_21aa62_m06/logs.txt
- subruns: {'multistep': '20260130_014940_21aa62_m06_ms', 'retrieval_full': '20260130_014940_21aa62_m06_ms_eval_full', 'retrieval_complex': '20260130_014940_21aa62_m06_ms_eval_complex', 'calculator': '20260130_014940_21aa62_m06_calc', 'numeric_dev': '20260130_014940_21aa62_m06_numeric', 'numeric_full': '20260130_014940_21aa62_m06_numeric_full'}
- metrics keys:
  - retrieval_full: ['evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio', 'use_collected']
  - retrieval_complex: ['evidence_hit@1', 'evidence_hit@10', 'evidence_hit@5', 'mrr@1', 'mrr@10', 'mrr@5', 'num_queries', 'recall@1', 'recall@10', 'recall@5', 'uncertain_match_ratio', 'use_collected']
  - numeric_dev: ['abs_error_mean', 'abs_error_median', 'coverage', 'missing_gold', 'missing_pred', 'multi_gold', 'multi_pred', 'numeric_em', 'predictions_path', 'rel_error_mean', 'rel_error_median', 'total_queries']
