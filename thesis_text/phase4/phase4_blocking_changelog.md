# Phase 4 阻塞项变更记录

Purpose:
- 逐条记录 Top 5 阻塞项的处理动作、产物与证据路径。

How to use:
- 配合 verification_report 判定 RESOLVED / PARTIAL / STILL_BLOCKED。

## (1) 数据集切分规模（train/dev/test 计数）
- Actions:
  - 运行 prepare_data 与 build_subsets 生成 data_stats.json / subsets_stats.json
  - 新增 scripts/compute_data_stats.py 合并统计并落盘 docs/data_stats.json
  - 新增 configs/data_stats.yaml 与 docs/data_stats.md
- Evidence:
  - outputs/20260202_165254_c4b131/data_stats.json
  - outputs/20260202_165303_b04a7b/subsets_stats.json
  - docs/data_stats.json
- Status: RESOLVED

## (2) 多步检索 Planner/Gap/Stop/Refiner 细节补全
- Actions:
  - 为 StepPlanner / detect_gap / StopCriteria / refine_query 添加简短 docstring
  - 新增 docs/multistep_design.md 总结内部规则
  - 更新方法章 3.4 引用该文档与代码
- Evidence:
  - src/multistep/planner.py:25-41
  - src/multistep/gap.py:51-84
  - src/multistep/stop.py:26-67
  - src/multistep/refiner.py:19-34
  - docs/multistep_design.md
- Status: RESOLVED

## (3) 计算器任务类型与规则库说明
- Actions:
  - 新增 docs/calculator_design.md（任务类型、抽取规则、gate 与 numeric eval）
  - 更新方法章 3.6 引用该文档与代码
- Evidence:
  - src/calculator/compute.py:9-670
  - src/calculator/extract.py:7-154
  - scripts/run_with_calculator.py:244-279
  - scripts/eval_numeric.py:151-234
  - docs/calculator_design.md
- Status: RESOLVED

## (4) baseline 生成模块是否需要真实 LLM
- Actions:
  - 新增 docs/repro_env_and_llm_dependency.md（说明模板式生成与最短复现命令）
  - 方法章 3.3 增加引用
- Evidence:
  - scripts/run_baseline.py:50-51; 128-141
  - README.md:53-69
  - docs/repro_env_and_llm_dependency.md
- Status: RESOLVED

## (5) 关键 run_id 与主结果表可引用路径核对
- Actions:
  - 更新 thesis_text/phase_fix/outputs_index.md，新增 data_stats / subset_stats / merged stats run_id
  - 标注 Step6 主结果表依赖的 run_id（当前 outputs 缺失）与生成命令
- Evidence:
  - thesis_text/phase_fix/outputs_index.md
  - configs/step6_experiments.yaml:1-13
  - thesis/figures/FIGURE_CATALOG.md
- Status: RESOLVED
