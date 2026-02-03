# Phase 8 Consistency & QA Check

Purpose:
- 扫描术语一致性、占位符残留、章节互引与引用闭环风险。

How to use:
- 若新增内容，重新运行扫描并更新本报告。

## 1) 术语一致性
- FinDER / RAG / multistep / calculator：在 ch01–ch05 使用一致。
- 指标命名：Recall@K、MRR@K、EM、numeric_em 在方法/实验/结论中一致。
- 未发现同名不同义的指标表述。

## 2) 占位符与 TODO 扫描
- cover.tex 中字段变量为 TBD（允许，用于后续替换）。
- references.bib 中保留 PLACEHOLDER/TODO（允许，已结构化 note，详见 phase8_missing_bib_list.md）。
- thesis/figures/figures_auto.tex 与 FIGURE_CATALOG.md 含 TODO，但未被 main.tex include（不影响编译）。
- 正文 .tex 中未发现 TODO/TBD/PLACEHOLDER/[EVIDENCE] 残留。

## 3) 章节互引与一致性
- 方法章模块（baseline/multistep/calculator/eval）均在实验章有对应评测描述。
- 结论章中出现的代表性数值均来自实验章主结果（main_results.csv）。
- 正文未使用 \ref 或 \label（不存在悬空引用）。

## 4) 编译告警（最终）
- 无 undefined citations / undefined references。
- 仍有 overfull/underfull hbox 警告（长路径/命令导致），不影响可编译。

## 5) 修复动作记录
- 更新 references.bib note 字段为结构化缺失提示。
- 将 cover 字段变量化并设置默认 TBD。
- 清理 references.tex 中未转义的下划线（phase3_citation_plan.md）。
