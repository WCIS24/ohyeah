# 方法

本文系统由四个核心模块构成：**查询理解**、**多步检索推理**、**证据整合与计算**、**答案生成**。系统采用流水线式数据流，模块间接口明确，便于复现与扩展。

**图1 多步检索循环流程（示意）**

```
Query → Query Understanding → Step-1 Retrieval → Gap Detector
  → (gap & gate) Refined Query Retrieval → Merge & Rank
  → Calculator (optional) → Template Answer
```

## 3.1 查询理解
目标是将原始金融查询规范化，解决缩写、实体歧义与任务类型识别问题。可采用：
- 规则与词典扩展（如将“YOY”扩展为“同比”）；
- 金融领域 NER 与实体链接；
- 轻量语义解析（不开启外部 API）。

输出为规范化查询 $q'$ 与结构化槽位（实体、指标、年份、计算类型），作为多步检索的输入。

## 3.2 多步检索推理
多步检索在第 $t$ 轮使用当前查询 $q_t$ 检索 top-$k$ 证据，基于 gap 检测决定是否继续：

- **Gap Detector**：判断是否缺失关键年份或比较对象；
- **Gate**：若 $\text{gap\_conf} < \tau$，终止后续检索；
- **Merge Strategy**：跨步候选去重并按 maxscore 或 step1	extunderscore first 排序；
- **Stop Criteria**：达到 $T$ 或连续无新增证据时停止。

关键超参数定义：
- 检索轮数 $T$（max\_steps）
- 每轮检索 top-$k$（top\_k\_each\_step）
- 最终截断 top-$k_f$（top\_k\_final）
- 门控阈值 $\tau$（min\_gap\_conf）

**Step6 最优配置**：$T=2$，top\_k\_each\_step=10，merge=maxscore，novelty\_threshold=0.0，stop\_no\_new\_steps=1，$\tau=0.3$。

## 3.3 证据整合与计算
该模块从证据中抽取数值、年份、单位与实体，并执行显式计算（YoY/差值/占比/倍数）。核心约束：
- 单位一致性校验；
- 年份对齐要求；
- 候选冲突时拒算并回退。

**Step6 最优门控**：min\_conf=0.2，allow\_task\_types=[]（当前版本以稳定性为先）。

## 3.4 答案生成
采用模板化生成：若计算器返回 status=ok 且通过门控，则输出结构化结果与解释；否则回退基线答案，并记录 fallback 原因以支持审计。
