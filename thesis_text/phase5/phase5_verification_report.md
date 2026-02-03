# Phase 5 核验报告

Purpose:
- 核验实验章与主结果产物是否满足证据可追溯与口径一致要求。

How to use:
- 若存在 FAIL，先补齐证据或输出后再进入 Phase 6。

## 核验总表
| Check | Status | Notes |
| --- | --- | --- |
| V1 数值可追溯 | PASS | main_results.csv 与 summary.json 可一一对应 |
| V2 口径一致 | PASS | Recall@K/MRR@K 与 eval_utils 一致；numeric_em 与 eval_numeric 一致 |
| V3 baseline 公平性 | PASS | 所有 Step6 run 共享 step6_base.yaml 的 k_list 与数据切分 |
| V4 复现性 | PASS | 每个 run_id 具备可复制命令与 outputs 路径 |
| V5 无编造 | PASS | 实验章数值均来自 outputs 或 main_results.csv |

## 证据清单
- thesis_text/phase5/main_results.csv
- outputs/20260130_014940_21aa62_m01/summary.json
- outputs/20260130_014940_21aa62_m02/summary.json
- outputs/20260130_014940_21aa62_m03/summary.json
- outputs/20260130_014940_21aa62_m04/summary.json
- outputs/20260130_014940_21aa62_m05/summary.json
- outputs/20260130_014940_21aa62_m06/summary.json
- configs/step6_base.yaml
- src/retrieval/eval_utils.py
- scripts/eval_numeric.py

## 复现命令索引
- 见 thesis_text/phase5/phase5_gate_check.md 与 thesis_text/phase_fix/outputs_index.md
