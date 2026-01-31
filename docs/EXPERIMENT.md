# 实验设置

## 数据集与划分
使用 FinDER 数据集，包含 5,703 个查询—证据—答案三元组。数据按 train/dev/test 划分，所有样本统一格式：

```json
{ "qid": "...", "query": "...", "answer": "...", "evidences": [{"text": "..."}], "meta": {} }
```

## 子集定义
- **complex\_dev**：满足任一条件即进入子集：多证据、查询含 ≥2 年份、含比较/变化关键词、或含数值+年份组合。
- **numeric\_dev**：查询或答案含数字/百分号/同比/差值/倍数关键词。

## 评价指标与口径
- 检索指标：Recall@k、MRR@k、evidence\_hit@k
- QA 指标：EM/F1（用于对照）
- 数值指标：Numeric-EM、RelErr、Coverage
- 不确定匹配比例：当证据缺少 doc\_id/evidence\_id 时使用文本匹配，并记录比例。

## 关键参数
- 检索器：BM25 + Dense + Hybrid（alpha=0.5）
- 多步检索（best）：max\_steps=2，top\_k\_each\_step=10，merge=maxscore
- 计算器门控（best）：min\_conf=0.2，allow\_task\_types=[]

所有实验配置与结果均保存在 outputs/<run\_id>/，可复现。
