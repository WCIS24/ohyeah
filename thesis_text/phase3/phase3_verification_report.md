# Phase 3 核验报告

## 核验总表
| Check | Status | Notes |
| --- | --- | --- |
| A0 产物存在性 | PASS | 5 个必需文件齐全 |
| A1 叙事线/贡献点一致性 | PASS | 定位段措辞克制，与 Phase 1 一致 |
| A2 引用占位符与可补齐性 | PASS | 9 个 TODO 占位符均在 citation_plan 中给出补齐策略 |
| A3 结构与覆盖度 | PASS | 2.1–2.5 全部覆盖 |
| A4 产物联动 | PASS | paragraph_map 已与正文段落对齐 |

## 主要问题清单
- 无（已同步 paragraph_map）

## 最小修复动作
- 无

## 进入 Phase 4 的证据准备情况
- 方法章所需证据已具备：
  - README.md（流程入口与脚本序列）
  - configs/*.yaml（关键超参与参数）
  - scripts/*.py（产物写入与日志输出）
  - 仓库地图.pdf（模块边界与 outputs 结构）

## 证据路径清单
- README.md:41-131
- configs/prepare_data.yaml:1-20
- configs/build_corpus.yaml:1-6
- configs/run_baseline.yaml:1-12
- configs/eval_retrieval.yaml:1-13
- configs/run_multistep.yaml:1-21
- configs/run_with_calculator.yaml:1-17
- scripts/run_baseline.py:128-141
- scripts/run_multistep_retrieval.py:166-213
- scripts/run_with_calculator.py:147-152
- scripts/eval_retrieval.py:153-160
- scripts/eval_numeric.py:154-235
- 仓库地图.pdf:page 1
