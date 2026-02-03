# 毕业论文文件说明（Thesis File Guide）

面向：本人/导师/答辩检查人员

本指南基于仓库 **WCIS24/ohyeah** 当前实际文件生成，按“可编译 + 可追溯 + 可维护”的工程视角说明论文相关文件用途、编译方式、证据路径与更新方法。

---

## 1) 快速开始（Quick Start）

### 最短编译命令
在 `thesis/` 下执行：
```
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

### 依赖说明
- TeX 发行版：TeX Live（支持 XeLaTeX + BibTeX）
- 编译器：XeLaTeX（ctexbook 需要中文支持）
- 字体：由 ctex 自动加载系统中文字体（Windows 环境默认可用）

### 典型错误与定位
- `Citation ... undefined`：通常是未运行 BibTeX 或 references.bib 中缺少 key。先 `bibtex main` 再两次 `xelatex`。
- `No file main.bbl`：说明 BibTeX 尚未运行。
- `File not found`：检查 `main.tex` 的 `\input{...}` 是否存在对应文件。
- 目录或引用显示不完整：需多运行一次 `xelatex` 生成 toc/out。
- `Overfull hbox`：长路径/命令导致，不影响编译，只影响版面。

可用脚本：`scripts/build_thesis.sh`（自动执行 xelatex/bibtex/xelatex/xelatex 并保存日志）。

---

## 2) 论文工程总览

- **`thesis/`**：最终可编译论文源（LaTeX 主工程）。
- **`thesis_text/phase*`**：写作流程的中间产物、核验报告、证据映射、结果汇总等（不可直接编译）。
- **`docs/`**：方法/数据/复现说明与结果表（设计文档 + 统计结果）。
- **`thesis_text/phase_fix/outputs_index.md`**：run_id → outputs 证据索引（用于实验结果可追溯）。
- **`outputs/`**：实验产物（metrics.json / summary.json / logs.txt 等）。

> 说明：仓库根目录未发现 `outputs_index.md`，使用 `thesis_text/phase_fix/outputs_index.md` 作为权威索引。

---

## 3) thesis/ 目录逐文件说明

> 表格字段：Path / Purpose / How it’s used / When to edit

| Path | Purpose | How it’s used | When to edit |
| --- | --- | --- | --- |
| `thesis/main.tex` | 主入口与章节组织 | `\input{...}` 引入封面、摘要、正文、参考文献、附录、致谢 | 新增/调整章节顺序或新增模块时 |
| `thesis/preamble.tex` | 全局包与基础设置 | `main.tex` 首行引入 | 需要新增宏包或全局设置时 |
| `thesis/cover.tex` | 封面页（变量占位） | `main.tex` 中 `\input{cover}` | 填写封面字段（姓名、学号等） |
| `thesis/statement_originality.tex` | 原创性声明 | `\input{statement_originality}` | 学校模板要求改变时 |
| `thesis/authorization.tex` | 授权声明 | `\input{authorization}` | 学校模板要求改变时 |
| `thesis/abstract_cn.tex` | 中文摘要 + 关键词 | `\input{abstract_cn}` | 修改摘要内容或关键词 |
| `thesis/abstract_en.tex` | 英文摘要 + keywords | `\input{abstract_en}` | 修改英文摘要 |
| `thesis/toc.tex` | 目录 | `\input{toc}` | 一般无需手改 |
| `thesis/ch01_introduction.tex` | 第一章：绪论 | `\input{ch01_introduction}` | 修改引言正文 |
| `thesis/ch02_related_work.tex` | 第二章：相关工作 | `\input{ch02_related_work}` | 修改相关工作正文或引用 |
| `thesis/ch03_method.tex` | 第三章：方法 | `\input{ch03_method}` | 修改方法正文 |
| `thesis/ch04_experiments.tex` | 第四章：实验与结果 | `\input{ch04_experiments}` | 更新实验描述或结果说明 |
| `thesis/ch05_conclusion.tex` | 第五章：结论 | `\input{ch05_conclusion}` | 修改结论内容 |
| `thesis/references.tex` | 参考文献章 | `\bibliography{references}` | 更换引用样式/说明文字 |
| `thesis/references.bib` | BibTeX 条目 | BibTeX 读取 | 补齐真实文献或新增引用 |
| `thesis/appendix.tex` | 附录 | `\input{appendix}` | 更新复现命令/配置说明 |
| `thesis/acknowledgements.tex` | 致谢 | `\input{acknowledgements}` | 修改致谢内容 |
| `thesis/BUILD.md` | 构建说明 | 人工阅读 | 新增构建要求时 |
| `thesis/figures/` | 论文图表与样式 | 当前未在 main.tex 引用 | 需要插图/表时启用 |
| `thesis/main.pdf` | 编译产物 | 由 XeLaTeX 生成 | 不手改，仅检查 |
| `thesis/main.log` / `.aux` / `.bbl` / `.blg` / `.out` / `.toc` | 编译中间文件 | 由编译生成 | 不手改 |

---

## 4) thesis_text/phase* 流程产物地图

| Phase | 目的 | 关键产物 | 对应章节/用途 |
| --- | --- | --- | --- |
| Phase 0 | 项目概况与证据收集 | `phase0_project_overview.md`, `phase0_evidence_table.md` | 论文背景与证据基线 |
| Phase 1 | 叙事线与贡献点 | `phase1_contribution_statements.md`, `phase1_claim_evidence_matrix_v2.md` | 论文叙事、贡献框架 |
| Phase 2 | 绪论写作与核验 | `ch01_introduction_v1.md`, `phase2_verification_report.md` | 第一章内容来源 |
| Phase 3 | 相关工作写作与引用计划 | `ch02_related_work_v1.md`, `phase3_citation_plan.md` | 第二章与引用规划 |
| Phase 4 | 方法章 | `ch03_method_v1.md`, `phase4_verification_report.md` | 第三章内容来源 |
| Phase 5 | 实验章 | `ch04_experiments_v1.md`, `main_results.csv`, `delta_vs_baseline.json` | 第四章数据与主结果 |
| Phase 6 | 结论 | `ch05_conclusion_v1.md`, `phase6_verification_report.md` | 第五章内容来源 |
| Phase 7 | 摘要/附录/引用闭环 | `abstract_cn_v1.md`, `abstract_en_v1.md`, `phase7_*` | 摘要/附录/引用闭环 |
| Phase 8 | 最终收敛 | `phase8_*` | 编译/引用/发布包核验 |

**从一句话追溯证据示例**
1) “Full dev Recall@10 从 0.3246 提升至 0.3789” → `thesis_text/phase5/main_results.csv` → `outputs/20260130_014940_21aa62_m01/summary.json` & `outputs/20260130_014940_21aa62_m02/summary.json`（详见 `thesis_text/phase_fix/outputs_index.md`）
2) “FinDER 数据集包含 5,703 查询三元组” → `my-thesis/金融AI选题评价.pdf`（Phase 2 引用）
3) “calculator 产生 numeric_em 指标” → `outputs/20260130_014940_21aa62_m04/summary.json` + `thesis_text/phase5/main_results.csv`

---

## 5) 结果与证据来源（Results Provenance）

- 主结果表：
  - `thesis_text/phase5/main_results.csv`
  - `docs/TABLE_MAIN.md`（表格文字版）
  - `thesis/figures/ThemeA/tables/main_results.csv`（可用于图表渲染）
- 原始指标文件：`outputs/<run_id>/summary.json` 或 `outputs/<run_id>/metrics.json`
- run_id 与命令索引：`thesis_text/phase_fix/outputs_index.md`

**可追溯规则**
- 论文中每个数字 → 必须能在 `main_results.csv` 或 `outputs/<run_id>/metrics.json` / `summary.json` 找到。
- 先用 `outputs_index.md` 定位 run_id，再打开对应 outputs 目录验证指标。

---

## 6) 修改指南（Maintenance）

### 只改文字
- 直接修改 `thesis/chXX_*.tex`。
- 如需同步流程文档，可更新 `thesis_text/phase*/chXX_*.md`。

### 补封面字段
- 修改 `thesis/cover.tex` 顶部变量：
  - `\thesistitle`, `\studentname`, `\studentid`, `\advisorname`, `\department`, `\major`, `\classname`, `\dateSubmitted`

### 补真实文献
- 修改 `thesis/references.bib` 占位条目（见 `thesis_text/phase8/phase8_missing_bib_list.md`）。
- 运行 `bibtex main` 并重新 `xelatex` 两次。

### 更新实验结果
- 更新 `outputs/` 与 `thesis_text/phase_fix/outputs_index.md`
- 重新生成 `thesis_text/phase5/main_results.csv` 与 `docs/TABLE_MAIN.md`
- 同步修改 `thesis/ch04_experiments.tex` 中描述

### 出新版发布
- 运行 `scripts/build_thesis.sh`（会生成 `thesis/_build/build.log`）
- 打包 `thesis_release.zip`（仓库根目录已生成）

---

## 7) 一页式检查清单（Checklist）

**编译前**
- [ ] `references.bib` 中的 `\cite{}` key 全部存在
- [ ] `thesis/cover.tex` 字段已填真实信息（或允许 TBD）
- [ ] 正文无 TODO/TBD/PLACEHOLDER 残留

**编译后**
- [ ] 目录/五章/参考文献/附录/致谢齐全
- [ ] `main.log` 无 undefined citations / references

**提交前**
- [ ] `thesis_release.zip` 已更新
- [ ] `outputs_index.md` 与主结果表可追溯
- [ ] 复现命令与环境说明在附录中可查

---

## 可选：目录树（见 docs/THESIS_FILE_TREE.txt）

如需快速浏览结构，请查看 `docs/THESIS_FILE_TREE.txt`。
