# Phase 7 LaTeX Integration Report

Purpose:
- 记录主工程 include 顺序与可编译命令，便于后续排版与调试。

How to use:
- 若编译失败，按“常见问题定位”检查路径与引用键。

## Include Order (main.tex)
1) cover.tex
2) statement_originality.tex
3) authorization.tex
4) abstract_cn.tex
5) abstract_en.tex
6) toc.tex
7) ch01_introduction.tex
8) ch02_related_work.tex
9) ch03_method.tex
10) ch04_experiments.tex
11) ch05_conclusion.tex
12) references.tex
13) appendix.tex
14) acknowledgements.tex

## Bibliography Backend
- BibTeX（references.tex 使用 \bibliography{references}）

## Compile Command (XeLaTeX + BibTeX)
1) xelatex main.tex
2) bibtex main
3) xelatex main.tex
4) xelatex main.tex

## 常见问题定位
- 缺失文件：确认 thesis/ 下对应 .tex 是否存在。
- 引用报错：检查 thesis/references.bib 是否包含 ch02_related_work.tex 中的所有 \cite{} key。
- 编码问题：建议使用 XeLaTeX 编译，确保 UTF-8 文件正常显示。
