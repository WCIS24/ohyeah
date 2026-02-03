# Phase 5 阻塞项 Top 5

Purpose:
- 仅列出会阻塞 Phase 6/7 的缺口与最小补齐路径。

How to use:
- 逐条补齐后再进入讨论/结论章节。

| Missing item | Why needed | Where to find (expected file/command) | How to obtain | Owner |
| --- | --- | --- | --- | --- |
| 多次随机种子实验（方差/置信区间） | 讨论与结论需稳定性证据 | scripts/run_experiment.py | 使用不同 seed 重跑 Step6 并汇总统计 | user |
| 误差分析/错误类型统计 | 讨论局限性与改进方向 | scripts/error_buckets.py; outputs/<run_id>/summary.json | 运行 error_buckets 并整理类别 | user |
| 数值错误分布图 | 数值推理稳定性展示 | outputs/<run_id>_numeric/numeric_per_query.jsonl | 统计 abs/rel error 分布并作图 | user |
| 外部文献对比基线 | 相关工作与讨论需对比 | 外部文献列表 | 提供引用清单或 BibTeX | user |
| 计算成本/资源占用 | 讨论效率与可部署性 | logs.txt 或运行时间统计 | 采集运行耗时与资源数据 | user |
