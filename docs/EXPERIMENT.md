# 实验设置

## 数据集与划分
使用 FinDER 数据集，按官方或既有切分方式划分为 train / dev / test。所有子集与样本格式统一为：

```json
{
  "qid": "...",
  "query": "...",
  "answer": "...",
  "evidences": [{"text": "...", "doc_id": null, "meta": {}}],
  "meta": {}
}
```

## 子集定义
- **complex_dev**：满足任一条件即进入子集：
  - 多证据（evidence ≥ 2）
  - 查询包含 ≥2 年份
  - 查询含比较/变化关键词（vs/compare/yoy/增长率 等）
  - 查询含数值与年份组合
- **numeric_dev**：查询或答案含数值/百分号/同比/差值/倍数关键词。

## 评价指标
- **检索指标**：Recall@k、MRR@k、evidence_hit@k
- **数值指标**：Numeric-EM、相对误差（RelErr）、覆盖率（Coverage）
- **不确定匹配比例**：当 doc_id/evidence_id 缺失时，回退到文本匹配并记录比例。

## 关键参数
- 检索器：稀疏（BM25）+ 稠密（sentence-transformers）+ 混合（alpha=0.5）
- 多步检索（best）：max_steps=2, top_k_each_step=10, merge_strategy=maxscore
- 计算器门控（best）：min_conf=0.2, allow_task_types=[]

所有实验参数与最终配置均在 `outputs/<run_id>/config.resolved.yaml` 中可复现追溯。
