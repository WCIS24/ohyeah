# SEAL Check - Step4/Step5 (Step6 主矩阵与消融闭环)

Date: 2026-02-18  
Checked matrix: `outputs/20260217_123645_68f6b9`

## 0) 结论（本步）

结论：`部分通过（Ablation Partial Pass）`。

- 已通过：
  - `dense(preFT) vs dense(postFT)` 对照成立，且提升明显。
  - `dense vs bm25 vs hybrid` 对照成立（同 seed/同 k 口径），差异显著。
- 未通过：
  - `multistep on/off` 与 `max_steps=1 vs 2` 收益极小，当前不足以证明模块有效。
  - `calculator` 仍接近“全回退”：m08 `gate_task=81.58%`、总 fallback `85.96%`；按封条规则判为不合格。

---

## 1) Step6 主矩阵定义恢复（MVP / 主表 / 主图）

## 1.1 MVP10 组成（seal matrix）

- Matrix config：`configs/step6_matrix_seal.yaml:1`
- Matrix metadata：`outputs/20260217_123645_68f6b9/matrix.json:2`
- 10 个 run（m01~m10）完整落盘于：
  `outputs/20260217_123645_68f6b9/runs/`

## 1.2 main vs ablation 分组（用于实验叙事）

- 分组定义：`configs/step6_experiments_seal.yaml:1`
- `main`：m01,m02,m03,m04,m05,m08,m09（`configs/step6_experiments_seal.yaml:2` 到 `configs/step6_experiments_seal.yaml:28`）
- `ablation`：m06,m07,m10（`configs/step6_experiments_seal.yaml:17` 到 `configs/step6_experiments_seal.yaml:31`）

## 1.3 主表/主图实际消费口径

- `make_tables` 当前不会按 group 过滤，`TABLE_MAIN` 吃全部 experiments：
  - 代码：`scripts/make_tables.py:44` 到 `scripts/make_tables.py:70`
  - 产物：`docs/TABLE_MAIN.md:3` 到 `docs/TABLE_MAIN.md:12`
- `plot_all` 的 `main_results` 也不做 group 过滤（直接用全部 experiments）：
  - 代码：`scripts/plot_all.py:599` 到 `scripts/plot_all.py:605`
- `ablation_breakdown` 才按 `group: ablation` 过滤：
  - 配置：`scripts/plot_config.yaml:59` 到 `scripts/plot_config.yaml:63`
  - 代码：`scripts/plot_all.py:750` 到 `scripts/plot_all.py:755`

---

## 2) 消融矩阵完成度表（对照成立 + 有效性判定）

判定口径（本审计）：
- `有效`：对照组与实验组配置差异可解释，且目标指标有可观提升（本报告按 `>=0.01` 作为“可观”经验阈值）。
- `无效`：对照成立但目标指标未改善或退化。
- `需重跑`：对照成立但提升极小/不稳定，不能支撑“模块有效”主张。

| 对照项 | run_id 对照 | config key 差异（关键） | 指标差异（核心） | 判定 | 证据 |
|---|---|---|---|---|---|
| dense(preFT) vs dense(postFT) | m01 vs m02 | 仅模型路径变化：`all-MiniLM` -> `models/retriever_ft/latest`；seed=42, mode=dense | Full R@10 `0.3246 -> 0.3789` (`+0.0544`), Full MRR@10 `+0.0525`; Complex R@10 `+0.0494`; Abbrev R@10 `+0.0539` | 有效 | 配置：`outputs/20260217_123645_68f6b9/experiments_resolved.yaml:22`, `outputs/20260217_123645_68f6b9/experiments_resolved.yaml:44`; 指标：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01/summary.json:22`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:22` |
| dense vs bm25 vs hybrid（单步） | m02 vs m03 vs m04 | mode 分别为 dense/bm25/hybrid；seed=42，k_list=[1,5,10] | Full R@10: `0.3789 / 0.2246 / 0.3491`; Full MRR@10: `0.2554 / 0.1266 / 0.2092` | 有效（对照成立，dense 最优） | 配置：`outputs/20260217_123645_68f6b9/experiments_resolved.yaml:45`, `outputs/20260217_123645_68f6b9/experiments_resolved.yaml:67`, `outputs/20260217_123645_68f6b9/experiments_resolved.yaml:89`; 指标：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:22`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m03/summary.json:22`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m04/summary.json:22` |
| multistep on/off | m02 (off) vs m05 (on, max_steps=2) | m05 开启 multistep，并设 `max_steps=2, top_k_each_step=10` | Full R@10 `Δ=0`; Full MRR@10 `+0.000146`; Complex MRR@10 `+0.000343`; Abbrev MRR@10 `+0.000166` | 需重跑（收益过小） | 配置：`outputs/20260217_123645_68f6b9/experiments_resolved.yaml:47`, `outputs/20260217_123645_68f6b9/experiments_resolved.yaml:112`; 指标：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:24`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05/summary.json:24` |
| multistep 深度 | m06 (max_steps=1) vs m05 (max_steps=2) | 关键差异为 `multistep.max_steps`（1 vs 2） | MRR@10 提升仍仅 `+0.000146~+0.000343`；无显著差异 | 需重跑（深度收益未被证明） | 配置：`outputs/20260217_123645_68f6b9/experiments_resolved.yaml:140`, `outputs/20260217_123645_68f6b9/experiments_resolved.yaml:113`; 指标：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06/summary.json:24`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05/summary.json:24`; 过程统计：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05_ms/logs.txt:8`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06_ms/logs.txt:8` |
| calculator gate 空白名单 vs 白名单 | m07 (allow=`[]`) vs m08 (allow=`[yoy,diff]`) | 仅 gate 任务白名单不同；其余检索配置一致 | Numeric: EM `0.3964 -> 0.3197`（下降），Coverage `0.6180 -> 0.6695`（上升）；但 m08 `gate_task=81.58%`, fallback_total `85.96%` | 无效（且不合格） | 配置：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/config.resolved.yaml:52`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/config.resolved.yaml:52`; 指标：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/summary.json:61`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json:61`; fallback：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07_calc/calc_stats.json:16`, `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_calc/calc_stats.json:16` |

---

## 3) Calculator fallback_counts 占比（必须项）

> 计算口径：每个 reason 占比 = `fallback_counts[reason] / total_queries`。  
> 代码依据：`scripts/run_with_calculator.py:280` 到 `scripts/run_with_calculator.py:283`（每条样本写单一 `fallback_reason`），以及 `scripts/run_with_calculator.py:308` 到 `scripts/run_with_calculator.py:314`（落盘 `calc_stats.json`）。

代码证据摘录（14行）：

```python
if result.status == "ok" and gate_reason is None:
    ...
    fallback_reason = None
else:
    ...
    fallback_reason = gate_reason or result.status
    fallback_counts[fallback_reason] += 1

preds_f.write(json.dumps({
    "qid": qid,
    ...
    "fallback_reason": fallback_reason,
}, ensure_ascii=False) + "\n")
```

Source: `scripts/run_with_calculator.py:271` 到 `scripts/run_with_calculator.py:283`

| Run | total_queries | fallback reason 占比 | fallback_total 占比 | calc_used_est 占比 |
|---|---:|---|---:|---:|
| m07 | 570 | gate_task: `570/570 = 100.00%` | `100.00%` | `0.00%` |
| m08 | 570 | gate_task `81.58%`; status_insufficient_facts `3.16%`; status_no_match `0.53%`; gate_inferred `0.53%`; status_ambiguous `0.18%` | `85.96%` | `14.04%` |
| m09 | 570 | gate_task `81.58%`; status_insufficient_facts `2.98%`; status_ambiguous `0.35%` | `84.91%` | `15.09%` |
| m10 | 570 | gate_task `81.58%`; status_insufficient_facts `2.98%`; status_ambiguous `0.35%` | `84.91%` | `15.09%` |

证据：
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07_calc/calc_stats.json:2` 到 `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07_calc/calc_stats.json:18`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_calc/calc_stats.json:2` 到 `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_calc/calc_stats.json:22`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09_calc/calc_stats.json:2` 到 `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09_calc/calc_stats.json:20`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10_calc/calc_stats.json:2` 到 `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10_calc/calc_stats.json:20`

封条判定（按你给的规则）：
- m08/m09/m10 仍接近全回退（`fallback_total ~85%`, `gate_task ~82%`），`calculator` 链路判定为 `不合格（不可封条）`。

---

## 4) 最小补齐路径（仅列缺口项）

说明：`bm25/hybrid` 与 `abbrev` 当前不缺，已具备可用对照与产物；本节仅列仍未闭环项。

## 4.1 缺口一：multistep 有效性证据不足

最小 patch（配置级）：
- 文件：`configs/step6_matrix_seal.yaml`
- 建议改动：对 m05/m06（可选 m09/m10）将 `multistep.gate.min_gap_conf` 下调（例如 `0.3 -> 0.0`）或加一组 `multistep.gate.enabled=false` 诊断对照。

最小重跑集合：
1. `m05`（step2）
2. `m06`（step1）

验收标准：
- `m05_ms/logs.txt` 中 `avg_steps` 明显高于 1（建议 >1.2）且 `MAX_STEPS` 比例上升；
- 相对 m06，至少一个检索核心指标达到可见提升（建议 `complex_mrr10` 或 `full_mrr10` `>= +0.005`）。

## 4.2 缺口二：calculator 仍接近全回退

最小 patch（先诊断再收敛）：
- 文件：`configs/step6_matrix_seal.yaml`
- 追加 1 个诊断 run（建议命名 `seal_mvp08b_dense_calc_gate_off`）：
  - `calculator.gate.enabled=false`
  - 其余与 m08 保持一致

最小重跑集合：
1. `m08b`（gate-off 诊断）
2. 若 m08b 显示可用样本明显上升，再重跑一个“收敛配置”run（例如放宽 gate，但不改检索）

验收标准：
- `calc_stats.json`：`fallback_total` 不再接近全回退（建议 <70%），且 `gate_task` 明显下降（建议 <50%）；
- `summary.json`：在 coverage 提升的同时，`numeric_em` 不出现不可接受退化（可设容忍阈值，例如不低于当前 m08 超过 0.02）。

如果无法满足上述标准：
- 从“主图主表硬结论”中降级 calculator（保留为失败消融/诊断结果），再封条进入绘图。

---

## 5) 结语（A5）

- Step6 主矩阵结构与 run 覆盖已完整恢复。
- 但在“可证明模块有效”层面，当前只稳固证明了 `FT` 与 `retriever mode`；`multistep` 与 `calculator` 尚未形成可封条证据闭环。

---

## 6) 2026-02-18 Action1 执行更新（m08b gate-off 诊断）

执行内容：
- 在 `configs/step6_matrix_seal.yaml` 新增
  `seal_mvp08b_dense_calc_gate_off`（`calculator.gate.enabled=false`）。
- 以 one-run matrix 方式最小重跑：
  - `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix outputs/tmp_matrix_action1_m08b.yaml`
  - 新矩阵：`outputs/20260217_174322_d71045/matrix.json:2`

结果对照（m08 vs m08b）：

| 指标 | m08 (allow=[yoy,diff]) | m08b (gate_off) | 变化 |
|---|---:|---:|---:|
| gate_task 占比 | 0.815789 | 0.000000 | -0.815789 |
| fallback_total 占比 | 0.859649 | 0.800000 | -0.059649 |
| numeric coverage | 0.669528 | 0.682403 | +0.012876 |
| numeric_em | 0.319728 | 0.286667 | -0.033061 |

证据：
- 对照汇总日志：
  - `outputs/seal_checks/action1_m08_vs_m08b_compare.log:3`
  - `outputs/seal_checks/action1_m08_vs_m08b_compare.log:14`
- m08 calc stats：
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_calc/calc_stats.json:16`
- m08b calc stats：
  - `outputs/20260217_174322_d71045/runs/20260217_174322_d71045_m01_calc/calc_stats.json:16`
- m08 numeric summary：
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json:61`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json:62`
- m08b numeric summary：
  - `outputs/20260217_174322_d71045/runs/20260217_174322_d71045_m01/summary.json:61`
  - `outputs/20260217_174322_d71045/runs/20260217_174322_d71045_m01/summary.json:62`

判定：
- Action1 的“gate_task 显著下降”目标已达成；
- 但 fallback_total 仍高（80%），且 EM 下滑，说明还需要 Action2 的 gate 参数收敛对照。

---

## 7) 2026-02-18 Action2 执行更新（m08c min_conf=0.2）

执行内容：
- 在 `configs/step6_matrix_seal.yaml:97` 新增
  `seal_mvp08c_dense_calc_minconf_02`，仅将 `calculator.gate.min_conf=0.2`
  （对照 m08 的 `0.4`）。
- 运行前 smoke：
  `python scripts/smoke.py --config configs/smoke.yaml --run-id a8_action2_smoke`
  （证据：`outputs/a8_action2_smoke/logs.txt:1`）。
- one-run matrix 运行：
  `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix outputs/tmp_matrix_action2_m08c.yaml`
  （证据：`outputs/20260218_012802_326769/matrix.json:2`）。

关键对照（m08 vs m08b vs m08c）：

| 指标 | m08 | m08b (gate_off) | m08c (min_conf=0.2) |
|---|---:|---:|---:|
| gate_task 占比 | 0.815789 | 0.000000 | 0.815789 |
| fallback_total 占比 | 0.859649 | 0.800000 | 0.859649 |
| numeric coverage | 0.669528 | 0.682403 | 0.669528 |
| numeric_em | 0.319728 | 0.286667 | 0.319728 |

证据：
- m08c 覆盖配置确实生效（命令中 `calculator.gate.min_conf=0.2`）：
  `outputs/20260218_012802_326769/matrix.json:32`
- m08c gate_task 仍为 465：
  `outputs/20260218_012802_326769/runs/20260218_012802_326769_m01_calc/calc_stats.json:17`
- m08c numeric 指标：
  `outputs/20260218_012802_326769/runs/20260218_012802_326769_m01/summary.json:61`
  `outputs/20260218_012802_326769/runs/20260218_012802_326769_m01/summary.json:62`
- 三者对照日志：
  `outputs/seal_checks/action2_m08_m08b_m08c_compare.log:2`
  `outputs/seal_checks/action2_m08_m08b_m08c_compare.log:4`

判定：
- Action2 未通过（`min_conf` 下调对当前瓶颈无效，m08c 与 m08 指标完全一致）；
- 当前主要阻断仍在 `allow_task_types` + 任务识别分布导致的 `gate_task` 大规模触发。

---

## 8) 2026-02-18 Action3 执行更新（m05b/m06b multistep gate-open）

执行内容：
- 在 `configs/step6_matrix_seal.yaml` 新增：
  - `seal_mvp05b_dense_multistep_gate_open`
  - `seal_mvp06b_dense_multistep_t1_gate_open`
  并将两者 `multistep.gate.min_gap_conf=0.0`。
- one-run pair matrix：
  `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix outputs/tmp_matrix_action3_m05b_m06b.yaml`
  （证据：`outputs/20260218_023916_906096/matrix.json:2`）。

关键结果（old vs new）：

| 对照 | Full MRR@10 | Complex MRR@10 | avg_steps | stop_reasons |
|---|---:|---:|---:|---|
| m05_old (`gate=0.3`) | 0.255595 | 0.296471 | 1.081 | `MAX_STEPS=45, GATE_BLOCKED=525` |
| m05b_new (`gate=0.0`) | 0.255595 | 0.296471 | 1.081 | `MAX_STEPS=45, GATE_BLOCKED=525` |
| m06_old (`gate=0.3`) | 0.255448 | 0.296128 | 1.000 | `MAX_STEPS=46, GATE_BLOCKED=524` |
| m06b_new (`gate=0.0`) | 0.255448 | 0.296128 | 1.000 | `MAX_STEPS=46, GATE_BLOCKED=524` |

证据：
- 汇总对照：
  `outputs/seal_checks/action3_multistep_compare.json:2`
  `outputs/seal_checks/action3_multistep_compare.json:32`
- m05b multistep 日志：
  `outputs/20260218_023916_906096/runs/20260218_023916_906096_m01_ms/logs.txt:8`
  `outputs/20260218_023916_906096/runs/20260218_023916_906096_m01_ms/logs.txt:9`
- m06b multistep 日志：
  `outputs/20260218_023916_906096/runs/20260218_023916_906096_m02_ms/logs.txt:8`
  `outputs/20260218_023916_906096/runs/20260218_023916_906096_m02_ms/logs.txt:9`

判定：
- Action3 已执行但未形成有效提升证据；
- 现阶段 multistep 的收益仍然仅为极小量级（与旧 run 完全一致）。

---

## 9) 2026-02-18 Action3 拓展（m05c/m06c gate disabled）+ Calculator 收敛（m08d）

执行内容：
- 新增 `m05c/m06c`：`multistep.gate.enabled=false`（并保留 `min_gap_conf=0.0`）。
- 新增 `m08d`：`calculator.gate.allow_task_types=["yoy","diff","share","multiple"]`。
- 运行矩阵：
  `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix outputs/tmp_matrix_action3ext_m05c_m06c_m08d.yaml`
  （证据：`outputs/20260218_032001_2056e7/matrix.json:2`）。

### 9.1 Multistep 结果（m05/m06 vs m05c/m06c）

| 对照 | Full MRR@10 | Complex MRR@10 | avg_steps | stop_reasons |
|---|---:|---:|---:|---|
| m05 (`gate=0.3`) | 0.255595 | 0.296471 | 1.081 | `MAX_STEPS=45, GATE_BLOCKED=525` |
| m05c (`gate.enabled=false`) | 0.255448 | 0.296128 | 1.000 | `NO_GAP=570` |
| m06 (`gate=0.3`) | 0.255448 | 0.296128 | 1.000 | `MAX_STEPS=46, GATE_BLOCKED=524` |
| m06c (`gate.enabled=false`) | 0.255448 | 0.296128 | 1.000 | `NO_GAP=570` |

证据：
- 汇总：
  `outputs/seal_checks/action3ext_multistep_compare.json:2`
  `outputs/seal_checks/action3ext_multistep_compare.json:61`
- m05c stop reason：
  `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m01_ms/logs.txt:9`
- m06c stop reason：
  `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m02_ms/logs.txt:9`

判定：
- 关闭 gate 后，`GATE_BLOCKED` 消失但被 `NO_GAP` 100% 终止替代；
- 指标未提升，且 m05 反而小幅下降，multistep 仍未形成“有效模块”证据。

### 9.2 Calculator 结果（m08/m08c vs m08d）

| Run | gate_task_ratio | fallback_ratio | coverage | numeric_em |
|---|---:|---:|---:|---:|
| m08 | 0.815789 | 0.859649 | 0.669528 | 0.319728 |
| m08c | 0.815789 | 0.859649 | 0.669528 | 0.319728 |
| m08d | 0.757895 | 0.805263 | 0.682403 | 0.293333 |

证据：
- 汇总：
  `outputs/seal_checks/action3ext_calc_compare.json:2`
  `outputs/seal_checks/action3ext_calc_compare.json:72`
- m08d 任务分布与 gate_task：
  `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m03_calc/calc_stats.json:10`
  `outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m03_calc/calc_stats.json:17`

判定：
- 扩展任务白名单后，`gate_task` 与总 fallback 有下降，coverage 有提升；
- 但 fallback 仍高（约 80.5%）且 EM 下降，calculator 仍未达到可封条的稳定收益标准。
