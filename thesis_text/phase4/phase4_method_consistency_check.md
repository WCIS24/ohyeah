# 方法章术语与口径一致性检查

Purpose:
- 核对方法章用语与 Phase 1 术语规范是否一致，提前发现口径偏差。

How to use:
- 若发现不一致，按“修复建议”改写方法章相关段落。

## 术语一致性核验
| Term | Expected (Phase 1) | Used in Method | Status | Notes |
| --- | --- | --- | --- | --- |
| FinDER | FinDER | FinDER CSV | PASS | 与数据文件命名一致 | 
| RAG | Retrieval-Augmented Generation (RAG) | 检索增强（RAG） | PASS | 出现在 3.3 段落 | 
| multi-step retrieval | 多步检索 / multi-step retrieval | 多步检索（multistep） | PASS | 英文括注一致 | 
| calculator / numeric reasoning | 计算器/数值推理 | calculator / numeric_em | PASS | 数值评测字段保持一致 | 
| Recall@K | Recall@K | Recall@K | PASS | 指标写法统一 | 
| MRR@K | MRR@K | MRR@K | PASS | 指标写法统一 | 
| EM | Exact Match (EM) | Exact Match (EM) | PASS | 指标写法统一 | 
| run_id | run_id | run_id | PASS | outputs/<run_id> 结构已说明 | 
| baseline | baseline | baseline | PASS | 与 README 命名一致 | 
| LLM dependency | baseline 为模板式生成 | baseline 不依赖外部 LLM | PASS | 见 docs/repro_env_and_llm_dependency.md | 
| 数据统计 | 使用 docs/data_stats.json | 已引用 docs/data_stats.json | PASS | 统计口径统一 | 

## 口径检查结论
- 当前方法章术语与 Phase 1 规范一致，未发现“同名不同义”或指标命名冲突。

## 修复建议（若需）
- 无
