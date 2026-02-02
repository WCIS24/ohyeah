# Phase_fix 核验报告

## 核验总表
| Item | Status | Evidence |
| --- | --- | --- |
| T1 | PASS | outputs/20260202_135956_ff2118/metrics.json |
| T2 | PASS | outputs/20260202_140330_7c95c6/metrics.json |
| T3 | PASS | outputs/20260202_141720_e674e0/metrics.json |
| T4 | PASS | outputs/20260202_142407_03d6dc/metrics.json; outputs/20260202_142407_03d6dc/delta_vs_baseline.json |
| T5 | PASS | outputs/20260202_142931_d30d8e/numeric_metrics.json; outputs/20260202_142931_d30d8e/numeric_per_query.jsonl |

## T1 核验
- Status: PASS
- Metrics file: outputs/20260202_135956_ff2118/metrics.json
- Keys (actual): ['recall@5', 'em', 'recall_at_k', 'exact_match', 'num_queries', 'k', 'seed']
- Keys (expected): ['recall@5', 'em', 'recall_at_k', 'exact_match', 'num_queries', 'k', 'seed']

## T2 核验
- Status: PASS
- Metrics file: outputs/20260202_140330_7c95c6/metrics.json
- Keys (actual): ['num_queries', 'mode', 'alpha', 'uncertain_match_ratio', 'recall@1', 'evidence_hit@1', 'mrr@1', 'recall@5', 'evidence_hit@5', 'mrr@5', 'recall@10', 'evidence_hit@10', 'mrr@10']
- Keys (expected): ['num_queries', 'mode', 'alpha', 'uncertain_match_ratio', 'recall@1', 'evidence_hit@1', 'mrr@1', 'recall@5', 'evidence_hit@5', 'mrr@5', 'recall@10', 'evidence_hit@10', 'mrr@10']

## T3 核验
- Status: PASS
- Metrics file: outputs/20260202_141720_e674e0/metrics.json
- Keys (actual): ['exact_match', 'token_f1', 'missing_rate', 'num_samples']
- Keys (expected): ['exact_match', 'token_f1', 'missing_rate', 'num_samples']

## T4 核验
- Status: PASS
- Metrics file: outputs/20260202_142407_03d6dc/metrics.json
- Keys (actual): ['num_queries', 'use_collected', 'uncertain_match_ratio', 'recall@1', 'evidence_hit@1', 'mrr@1', 'recall@5', 'evidence_hit@5', 'mrr@5', 'recall@10', 'evidence_hit@10', 'mrr@10']
- Keys (expected): ['num_queries', 'use_collected', 'uncertain_match_ratio', 'recall@1', 'evidence_hit@1', 'mrr@1', 'recall@5', 'evidence_hit@5', 'mrr@5', 'recall@10', 'evidence_hit@10', 'mrr@10']
- delta_vs_baseline.json: outputs/20260202_142407_03d6dc/delta_vs_baseline.json
- baseline_metrics_path (from config): outputs/20260202_142407_03d6dc/config.yaml

## T5 核验
- Status: PASS
- Metrics file: outputs/20260202_142931_d30d8e/numeric_metrics.json
- Keys (actual): ['total_queries', 'coverage', 'numeric_em', 'abs_error_mean', 'abs_error_median', 'rel_error_mean', 'rel_error_median', 'missing_pred', 'missing_gold', 'multi_pred', 'multi_gold', 'predictions_path']
- Keys (expected): ['total_queries', 'coverage', 'numeric_em', 'abs_error_mean', 'abs_error_median', 'rel_error_mean', 'rel_error_median', 'missing_pred', 'missing_gold', 'multi_pred', 'multi_gold', 'predictions_path']
- numeric_per_query.jsonl: outputs/20260202_142931_d30d8e/numeric_per_query.jsonl

## 口径一致性核验
- 指标命名：smoke 使用 recall@5/em 与 recall_at_k/exact_match；检索评估使用 recall@k/mrr@k；QA 使用 exact_match/token_f1；数值评估使用 numeric_em 与误差统计。不存在同名不同义字段。
- top-k 截断核验：candidate_count_summary.json 存在，below_k=0，k=10。
- 统计文件: outputs/20260202_141735_63db48/candidate_count_summary.json
- 报告文件: outputs/20260202_141735_63db48/candidate_count_report.md

## 进入 Phase 2 的证据清单
- outputs/20260202_135956_ff2118/metrics.json (smoke)
- outputs/20260202_140330_7c95c6/metrics.json (baseline retrieval)
- outputs/20260202_141720_e674e0/metrics.json (baseline QA)
- outputs/20260202_142407_03d6dc/metrics.json (multistep metrics)
- outputs/20260202_142407_03d6dc/delta_vs_baseline.json
- outputs/20260202_142931_d30d8e/numeric_metrics.json
- outputs/20260202_142931_d30d8e/numeric_per_query.jsonl
