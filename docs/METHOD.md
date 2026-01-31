# 方法

本文系统由四个核心模块组成：**查询理解**、**多步检索推理**、**证据整合与计算**、**答案生成**。整体流程如下：

```mermaid
flowchart TD
  Q[Query] --> U[Query Understanding]
  U --> R1[Step-1 Retrieval]
  R1 --> G[Gap Detector]
  G -->|gap & gate| Rn[Refined Query Retrieval]
  Rn --> M[Merge & Rank]
  M --> C[Calculator (optional)]
  C --> A[Template Answer]
  G -->|no gap| M
```

## 1. 查询理解
通过规则与词典对查询进行初步解析，包括年份识别、比较关系识别、数值提示词识别等。该模块用于驱动多步检索的 gap 类型判断与后续计算任务类型预测。

## 2. 多步检索推理
多步检索在每一步使用当前查询进行检索，随后基于 gap 检测决定是否继续检索。核心机制包括：

- **Gap Detector**：检测年份缺失、实体缺失等信息缺口。
- **Gate（门控）**：当 gap_conf < min_gap_conf 时，停止后续检索（避免 query 漂移）。
- **Merge Strategy**：采用 `maxscore` 或 `step1_first` 合并策略对跨步候选排序与截断。
- **Stop Criteria**：达到 max_steps 或无新增证据时停止。

**Step6 最优多步配置（dev）**：
- max_steps=2
- top_k_each_step=10
- novelty_threshold=0.0
- stop_no_new_steps=1
- merge_strategy=maxscore
- gate.min_gap_conf=0.3

## 3. 证据整合与计算
该模块包含数值抽取与显式计算：

- **抽取**：从证据文本中提取数值、单位、年份，并标注 inferred_year 与 confidence。
- **计算器**：支持 YoY / 差值 / 占比 / 倍数等任务。对于单位不一致、年份缺失、候选冲突等情况进行拒算，并记录原因。

**Step6 最优门控（numeric dev）**：
- min_conf=0.2
- allow_task_types=[]（在当前版本中关闭计算任务以避免 Numeric-EM 回退）

## 4. 答案生成
生成采用模板化策略：
- 若计算器返回 `status=ok` 且通过门控，则输出结构化计算结果与简要解释；
- 否则回退到 baseline 的占位式生成，并记录 fallback 原因。
