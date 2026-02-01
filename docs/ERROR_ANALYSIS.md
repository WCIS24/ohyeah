# 错误分析与案例

<<<<<<< HEAD
<<<<<<< HEAD
## 1. 失败类型概览（Step6）
- **complex dev**：主要集中在 `no_gap` 与 `max_steps`，说明部分查询在第一步已覆盖核心证据，但 refine 能力仍有限；
- **numeric dev**：由于计算器门控关闭（allow_task_types=[]），多数样本回退到 baseline，表现为 fallback 占比高。

## 2. 失败原因分析
1) **简称歧义与实体对齐不足**：金融缩写可能指向多家公司，导致检索命中无关证据。  
2) **检索漂移**：refined query 若过于相似或偏离目标，会重复检索或引入噪声。  
3) **证据冲突与口径不一**：不同段落可能存在统计口径差异（如合并口径与单体口径），需要更强的单位/实体对齐策略。  
4) **计算器保守门控**：为避免算错，门控阈值偏保守，导致覆盖率受限。  

## 3. 典型案例
典型复杂查询案例已整理在附录 B（`docs/CASE_STUDIES.md`），包含 3 个查询的多步检索轨迹与证据对比。
=======
=======
>>>>>>> parent of 0b43bdb (Step6 align sweeps and tables with calc updates)
## Run 20260130_014940_21aa62_m03
- numeric_buckets: {}
- complex_buckets: {'max_steps': 45, 'no_gap': 525}

## Run 20260130_014940_21aa62_m04
- numeric_buckets: {'fallback': 570}
- complex_buckets: {}

## Run 20260130_014940_21aa62_m01
- numeric_buckets: {}
- complex_buckets: {}

## Run 20260130_014940_21aa62_m02
- numeric_buckets: {}
- complex_buckets: {}

## Run 20260130_014940_21aa62_m05
- numeric_buckets: {'fallback': 570}
- complex_buckets: {'max_steps': 45, 'no_gap': 525}

## Run 20260130_014940_21aa62_m06
- numeric_buckets: {'fallback': 570}
- complex_buckets: {'max_steps': 46, 'no_gap': 524}
>>>>>>> parent of 0b43bdb (Step6 align sweeps and tables with calc updates)
