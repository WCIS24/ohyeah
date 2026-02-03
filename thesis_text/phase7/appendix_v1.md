\appendix
\chapter{附录}

\section{复现命令清单}
以下命令基于仓库脚本与配置文件，可用于复现实验流水线：
\begin{verbatim}
python scripts\prepare_data.py --config configs\prepare_data.yaml
python scripts\build_corpus.py --config configs\build_corpus.yaml
python scripts\eval_retrieval.py --config configs\eval_retrieval.yaml
python scripts\run_baseline.py --config configs\run_baseline.yaml
python scripts\eval_qa.py --config configs\eval_qa.yaml --predictions outputs/<run_id>/predictions.jsonl --gold data/processed/dev.jsonl
python scripts\run_multistep_retrieval.py --config configs\run_multistep.yaml
python scripts\eval_multistep_retrieval.py --config configs\eval_multistep.yaml --results outputs/<run_id>/retrieval_results.jsonl
python scripts\run_with_calculator.py --config configs\run_with_calculator.yaml
python scripts\eval_numeric.py --config configs\eval_numeric.yaml --predictions outputs/<run_id>/predictions_calc.jsonl
python scripts\run_experiment.py --config configs\step6_base.yaml --overrides ...
python scripts\make_tables.py --experiments configs\step6_experiments.yaml
\end{verbatim}

\section{关键配置文件}
核心配置文件包括：configs/prepare_data.yaml、configs/build_corpus.yaml、configs/eval_retrieval.yaml、configs/run_baseline.yaml、configs/eval_qa.yaml、configs/run_multistep.yaml、configs/eval_multistep.yaml、configs/run_with_calculator.yaml、configs/eval_numeric.yaml、configs/step6_base.yaml、configs/step6_experiments.yaml 等。

\section{outputs 结构说明}
实验输出统一写入 outputs/<run_id>/，其中包含 config.yaml、metrics.json、logs.txt 等基础文件；检索与多步检索还会生成 retrieval_results.jsonl 与 multistep_traces.jsonl；数值评测生成 numeric_metrics.json 与 numeric_per_query.jsonl。

\section{环境与依赖}
本文复现条件以 requirements.txt 所列依赖为准；项目当前未记录固定的 Python 版本与硬件信息，本文不将其作为复现前置条件。baseline 生成不依赖外部 LLM API，相关说明见 docs/repro_env_and_llm_dependency.md。
