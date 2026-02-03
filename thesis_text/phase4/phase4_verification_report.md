# Phase 4 修改效果核验报告

Purpose:
- 核验 Phase 4 修改是否满足证据可追溯、模块边界清晰与可复现要求。

How to use:
- 若存在 FAIL，按“修复建议”执行后再进入 Phase 5。

## 核验总表（V1–V6）
| Check | Status | Notes |
| --- | --- | --- |
| V1 证据可追溯 | PASS | 方法章新增段落均带 [EVIDENCE]，含 docs/data_stats.json 与设计文档引用 |
| V2 模块边界清晰 | PASS | baseline/multistep/calculator/eval 输入输出与 configs 控制已说明 |
| V3 与代码一致 | PASS | method_to_code_map 覆盖核心模块与新增 docs/script 路径 |
| V4 阻塞项收敛 | PASS | Top 5 均已标记 RESOLVED（见下表） |
| V5 可复现入口 | PASS | retrieval-only / full QA / multistep / calculator 命令均已列出 |
| V6 强制门槛复核 | PASS | (1) 与 (5) 均为 RESOLVED；允许进入 Phase 5 = YES（但本次不进入） |

## 阻塞项状态表
| Item | Status | Evidence |
| --- | --- | --- |
| (1) 数据集切分规模 | RESOLVED | docs/data_stats.json; outputs/20260202_165254_c4b131/data_stats.json; outputs/20260202_165303_b04a7b/subsets_stats.json |
| (2) 多步检索细节 | RESOLVED | docs/multistep_design.md; src/multistep/{planner,gap,stop,refiner}.py |
| (3) 计算器规则库 | RESOLVED | docs/calculator_design.md; src/calculator/{extract,compute}.py |
| (4) baseline LLM 依赖 | RESOLVED | docs/repro_env_and_llm_dependency.md; scripts/run_baseline.py |
| (5) 关键 run_id 与主结果表 | RESOLVED | thesis_text/phase_fix/outputs_index.md; configs/step6_experiments.yaml; thesis/figures/FIGURE_CATALOG.md |

## 可复现入口（最短命令）
- Retrieval-only:
  - `python scripts\eval_retrieval.py --config configs\eval_retrieval.yaml`
- Full QA baseline:
  - `python scripts\run_baseline.py --config configs\run_baseline.yaml`
  - `python scripts\eval_qa.py --config configs\eval_qa.yaml --predictions outputs/<run_id>/predictions.jsonl --gold data/processed/dev.jsonl`
- Multistep:
  - `python scripts\run_multistep_retrieval.py --config configs\run_multistep.yaml`
  - `python scripts\eval_multistep_retrieval.py --config configs\eval_multistep.yaml --results outputs/<run_id>/retrieval_results.jsonl`
- Calculator / Numeric QA:
  - `python scripts\run_with_calculator.py --config configs\run_with_calculator.yaml`
  - `python scripts\eval_numeric.py --config configs\eval_numeric.yaml --predictions outputs/<run_id>/predictions_calc.jsonl`

## 修复建议
- 无（本轮核验通过）
