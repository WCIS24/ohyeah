# 本科论文草稿（合并版）

> 说明：本文档由 docs/ 下各章节 Markdown 自动合并并统一排版得到。所有结果均来自 Step6 的 outputs/ 指标与表格。若需导出为 LaTeX/PDF，请见文末“格式与排版建议”。

## 摘要

金融问答（FinDER）任务中的复杂查询常涉及多年份、多实体与显式数值计算。传统单步检索 + 占位式生成在复杂问题上易出现证据覆盖不足与算术错误。本文构建了一个可复现的金融 RAG 系统，在无外部 LLM API 的约束下，引入规则驱动的多步检索与显式计算器，并通过门控策略与系统化调参避免性能回退。实验结果表明：检索器微调显著提升整体检索表现（full dev Recall@10: 0.3246 → 0.3772）；多步检索在复杂子集上维持不退化且 MRR 略有提升；计算器通过门控确保数值指标不下降，为后续提升奠定稳定基线。本文所有实验配置与指标均可在 outputs/ 中复现。  
**关键词**：金融问答，检索增强生成，多步检索，显式计算，误差分析，可复现

---

## 1 引言

金融问答（FinDER）场景中的查询往往具有高信息密度与强对比/计算需求：同一问题可能同时涉及多个年份、实体、指标，并要求对证据进行对齐与推理。传统单步检索 + 占位式生成容易在复杂问题上出现证据覆盖不足与算术错误。

为此，本文围绕可复现的金融 RAG（Retrieval-Augmented Generation）系统，构建并验证了一个分层可控的工程方案：在强约束（无外部 LLM API）的条件下，引入规则驱动的多步检索与显式计算器，并通过系统化调参与门控机制避免性能回退。

本文贡献如下：
- 可复现工程框架：建立从数据规范化、检索、评测到实验编排的一体化体系，所有实验产出统一落盘，可审计、可回滚。
- 多步检索与门控策略：实现 gap 检测、合并策略与停止规则，构建可控的多步检索循环，保障复杂查询的证据覆盖。
- 显式计算器：在证据抽取与单位/年份校验基础上进行程序化计算，并通过门控阈值降低算错风险。
- 系统化调参与对照分析：输出 full dev / complex dev / numeric dev 的对照与消融结果，支持论文级结果表格与错误分析。

---

## 2 相关工作

### 2.1 金融问答与金融文本理解
金融 QA 数据集与任务通常聚焦于财报、公告、研报等长文档环境中的事实与数值问答。FinDER 等数据集强调对证据的精确定位与多字段对齐，对检索与推理能力要求较高。

### 2.2 检索增强生成（RAG）
RAG 框架通过检索模块提供高相关证据，再由生成模块构造答案。近期研究关注密集检索、稀疏检索与混合检索的结合，以及检索器微调对下游 QA 的传导效果。

### 2.3 多跳/多步检索与推理
多跳检索强调通过多轮检索逐步完善证据覆盖，常见于复杂比较问题与跨文档推理问题。本文的多步检索采用规则驱动的 gap 检测与可控门控策略，以保证解释性和稳定性。

### 2.4 显式数值推理与计算
数值类问题的核心挑战是单位、年份与数值的对齐。显式计算器通过结构化抽取与程序化计算降低算术错误，并配合门控策略避免错误传播。

---

## 3 方法

本文系统由四个核心模块组成：查询理解、多步检索推理、证据整合与计算、答案生成。整体流程如下：

```
Query -> Query Understanding -> Step-1 Retrieval -> Gap Detector
  -> (gap & gate) Refined Query Retrieval -> Merge & Rank
  -> Calculator (optional) -> Template Answer
```

### 3.1 查询理解
通过规则与词典对查询进行初步解析，包括年份识别、比较关系识别、数值提示词识别等。该模块用于驱动多步检索的 gap 类型判断与后续计算任务类型预测。

### 3.2 多步检索推理
多步检索在每一步使用当前查询进行检索，随后基于 gap 检测决定是否继续检索。核心机制包括：
- Gap Detector：检测年份缺失、实体缺失等信息缺口。
- Gate（门控）：当 gap_conf < min_gap_conf 时，停止后续检索（避免 query 漂移）。
- Merge Strategy：采用 maxscore 或 step1_first 合并策略对跨步候选排序与截断。
- Stop Criteria：达到 max_steps 或无新增证据时停止。

Step6 最优多步配置（dev）：
- max_steps=2
- top_k_each_step=10
- novelty_threshold=0.0
- stop_no_new_steps=1
- merge_strategy=maxscore
- gate.min_gap_conf=0.3

### 3.3 证据整合与计算
该模块包含数值抽取与显式计算：
- 抽取：从证据文本中提取数值、单位、年份，并标注 inferred_year 与 confidence。
- 计算器：支持 YoY / 差值 / 占比 / 倍数等任务。对于单位不一致、年份缺失、候选冲突等情况进行拒算，并记录原因。

Step6 最优门控（numeric dev）：
- min_conf=0.2
- allow_task_types=[]（在当前版本中关闭计算任务以避免 Numeric-EM 回退）

### 3.4 答案生成
生成采用模板化策略：
- 若计算器返回 status=ok 且通过门控，则输出结构化计算结果与简要解释；
- 否则回退到 baseline 的占位式生成，并记录 fallback 原因。

---

## 4 实验设置

### 4.1 数据集与划分
使用 FinDER 数据集，按官方或既有切分方式划分为 train / dev / test。所有子集与样本格式统一为：

```
{
  "qid": "...",
  "query": "...",
  "answer": "...",
  "evidences": [{"text": "...", "doc_id": null, "meta": {}}],
  "meta": {}
}
```

### 4.2 子集定义
- complex_dev：满足任一条件即进入子集：多证据；查询包含 ≥2 年份；包含比较/变化关键词；或包含数值与年份组合。
- numeric_dev：查询或答案含数值/百分号/同比/差值/倍数关键词。

### 4.3 评价指标
- 检索指标：Recall@k、MRR@k、evidence_hit@k
- 数值指标：Numeric-EM、相对误差（RelErr）、覆盖率（Coverage）
- 不确定匹配比例：doc_id/evidence_id 缺失时回退文本匹配并记录比例。

### 4.4 关键参数
- 检索器：稀疏（BM25）+ 稠密（sentence-transformers）+ 混合（alpha=0.5）
- 多步检索（best）：max_steps=2, top_k_each_step=10, merge_strategy=maxscore
- 计算器门控（best）：min_conf=0.2, allow_task_types=[]

---

## 5 实验结果

### 5.1 检索效果（full dev / complex dev）
主表见：docs/TABLE_MAIN.md

关键结论（complex dev）：
- baseline(post-ft) vs best multistep
  - Recall@10：0.3909465 → 0.3909465（持平）
  - MRR@10：0.2960138 → 0.2960873（+0.00007）

检索器微调带来的整体提升（full dev）：
- pre-ft baseline → post-ft baseline：Recall@10 0.3246 → 0.3772（+0.0526）

### 5.2 数值题表现（numeric dev）
主表见：docs/TABLE_NUMERIC.md

关键对照（numeric dev）：
- baseline(post-ft) vs best calc gate
  - Numeric-EM：0.3838 → 0.3838（持平）
  - RelErr(mean)：683.3536 → 683.3536（持平）
  - Coverage：0.6266 → 0.6266（持平）

说明：当前版本计算器门控在 dev 上选择 allow_task_types=[]，以避免数值误差回退。因此 numeric 指标未出现回退，但也尚未体现提升。该结果为“安全启用”基线，可在后续提升抽取/计算置信度后再重新开启任务类型。

---

## 6 误差分析与案例

### 6.1 失败类型统计（Step6）
- numeric_buckets 多为 fallback（因计算器任务被门控关闭）
- complex_buckets 主要为 no_gap 与 max_steps

### 6.2 典型复杂查询案例
**qid**: 8c8c8c34
**query**: Hasbro (HAS) 2023 one-time charges impact on operating profitability vs historical trends and cap allocation implications.

多步检索轨迹摘要：
- step0: gap=MISSING_ENTITY, gap_conf=1.0, gate_decision=true
- step1: gap=MISSING_ENTITY, stop_reason=MAX_STEPS, final_topk_size=10

分析：
该问题涉及对比历史趋势与一次性费用的影响，属于复杂查询。多步检索识别到实体/比较型 gap，但 refined query 与原查询高度相似，第二步检索未引入新证据，最终以 MAX_STEPS 停止。该案例反映出 refiner 仍偏保守，需要提升实体拆分与 query 改写能力。

---

## 7 讨论

多步检索在 complex dev 上未显著提升 Recall@10，但通过门控与合并策略避免了退化。计算器在未充分校准前易“算得更多但算错更多”，因此 Step6 中使用 gate 将计算任务关闭，保证 numeric 指标不回退。未来需通过更稳健的单位/年份对齐、置信度打分与任务识别提升计算器有效性。

---

## 8 结论

本文构建了可复现的金融 RAG 工程体系，覆盖数据规范化、检索、评测与实验编排，并实现多步检索与显式计算模块。实验表明：检索器微调显著提升整体检索表现（full dev Recall@10: 0.3246 → 0.3772）；多步检索在复杂子集上不再造成性能回退；计算器通过门控避免数值指标退化。未来将继续提升 gap 识别能力与计算器鲁棒性。

---

## 格式与排版建议（中文本科论文）

- 标题层级建议：一级标题（黑体三号），二级标题（黑体四号），正文（宋体小四），行距 1.5 倍。
- 参考文献与引用：建议采用 GB/T 7714 格式，可在后续整理文献条目并替换占位引用。
- 图表：可将 docs/TABLE_MAIN.md 与 docs/TABLE_NUMERIC.md 转为 LaTeX 表格或 Word 表格；图表均需编号与题注。

> 如需 LaTeX 或 PDF 输出，可在此基础上进行模板转换（例如使用 Pandoc）或补充学校格式模板。
