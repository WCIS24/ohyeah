# SEAL Check - Step3 (Retriever FT / Optional Hard Negatives)

Date: 2026-02-18  
Checked workspace commit: `0b7f9100b360408023ff78d8195bb78ebb1de659`

## 0) Verdict

`PASS (with warnings)`

结论：Step3 的 FT 训练链路与 Step6 下游调用链路是通的，且 pre-FT vs post-FT 对照在 seal matrix 中已存在并可追溯；
但当前仍有 4 个一致性风险（`latest` 可变指针、导出的是 final 而非 best checkpoint、legacy key 覆盖风险、FT 与 seal commit 分离）。

---

## 1) Retriever 训练入口、配置落盘、checkpoint 与 metrics

## 1.1 入口与配置

- 文档入口（Step3）:
  - `README.md:71` 到 `README.md:83`
  - 训练命令：`README.md:82`
- 训练脚本入口:
  - `scripts/train_retriever.py:51` 到 `scripts/train_retriever.py:54`
- 训练配置文件（默认）:
  - `configs/train_retriever.yaml:1` 到 `configs/train_retriever.yaml:33`

## 1.2 训练产物写入逻辑（代码）

- run 目录：`outputs/<run_id>/`
  - `scripts/train_retriever.py:159` 到 `scripts/train_retriever.py:163`
- 训练日志：`logs.txt`
  - `scripts/train_retriever.py:165` 到 `scripts/train_retriever.py:168`
- checkpoint：
  - `checkpoints/best_model`（按 `recall@5` 最优）
  - `checkpoints/step_<global_step>`（定期保存）
  - 证据：`scripts/train_retriever.py:300` 到 `scripts/train_retriever.py:309`
- 训练评估指标（周期评估）：
  - `eval_epoch*_steps*.json`
  - 证据：`scripts/train_retriever.py:146` 到 `scripts/train_retriever.py:149`
- 训练汇总指标：`metrics.json`
  - 证据：`scripts/train_retriever.py:328` 到 `scripts/train_retriever.py:340`
- 训练配置落盘：`train_config.yaml`
  - 证据：`scripts/train_retriever.py:325` 到 `scripts/train_retriever.py:326`
- 模型导出：
  - `models/retriever_ft/<run_id>` 与 `models/retriever_ft/latest`
  - 证据：`scripts/train_retriever.py:316` 到 `scripts/train_retriever.py:323`

## 1.3 实际训练 run 证据（outputs）

已发现 FT 训练 run：`20260203_005729_cd195e`

- 配置落盘：`outputs/20260203_005729_cd195e/train_config.yaml:31`（run_id），`outputs/20260203_005729_cd195e/train_config.yaml:32`（git_hash）
- 汇总指标：`outputs/20260203_005729_cd195e/metrics.json:2` 到 `outputs/20260203_005729_cd195e/metrics.json:9`
- 周期评估：`outputs/20260203_005729_cd195e/eval_epoch0_steps50.json:2` 到 `outputs/20260203_005729_cd195e/eval_epoch0_steps50.json:14`
- 日志（seed/git/hash/train_cfg）：
  - `outputs/20260203_005729_cd195e/logs.txt:3`
  - `outputs/20260203_005729_cd195e/logs.txt:5`
  - `outputs/20260203_005729_cd195e/logs.txt:7`
- checkpoint 目录存在：`outputs/20260203_005729_cd195e/checkpoints/best_model/`、`outputs/20260203_005729_cd195e/checkpoints/step_50/`
- 导出模型目录存在：`models/retriever_ft/20260203_005729_cd195e/`、`models/retriever_ft/latest/`

---

## 2) FT 配置与 Step6 下游调用一致性验收

## 2.1 Step6 使用哪个 retriever 模型

- Step6 seal matrix 明确 pre/post 路径：
  - pre-FT：`configs/step6_matrix_seal.yaml:5`
  - post-FT：`configs/step6_matrix_seal.yaml:14`（其余 m03-m10 同路径）
- seal matrix metadata 固化 override：
  - `outputs/20260217_123645_68f6b9/matrix.json:24`
  - `outputs/20260217_123645_68f6b9/matrix.json:76`
- 子 run resolved config：
  - pre-FT: `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01/config.resolved.yaml:22`
  - post-FT: `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/config.resolved.yaml:22`

## 2.2 下游是否实际加载了该路径

- pre-FT run 日志：
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01_retrieval_full/logs.txt:6`
- post-FT run 日志：
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02_retrieval_full/logs.txt:6`

## 2.3 pre/post 结果对照（证明确实不是同一模型效果）

- pre-FT（m01）`recall@10`：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01/summary.json:22`
- post-FT（m02）`recall@10`：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/summary.json:22`

---

## 3) Hard Negatives 开关验收（是否生效）

## 3.1 开关在代码层面是“真开关”

- `hard_negatives.enabled` 影响样本构造：
  - `scripts/train_retriever.py:66` 到 `scripts/train_retriever.py:74`
- `hard_negatives.enabled` 影响 loss 类型：
  - `scripts/train_retriever.py:212` 到 `scripts/train_retriever.py:215`

代码证据摘录（10行）：

```python
if train_cfg.hard_enabled:
    if not hard_negs:
        missing += 1
        continue
    for neg in hard_negs[:hard_k]:
        examples.append(InputExample(texts=[query, pos, neg.get("text", "")]))
else:
    examples.append(InputExample(texts=[query, pos]))

if train_cfg.hard_enabled:
    train_loss = losses.TripletLoss(model=model)
else:
    train_loss = losses.MultipleNegativesRankingLoss(model=model)
```

Source: `scripts/train_retriever.py:66` 到 `scripts/train_retriever.py:74`，`scripts/train_retriever.py:212` 到 `scripts/train_retriever.py:215`

## 3.2 当前 seal 产物中，HN 实际状态

- 配置默认是关闭：`configs/train_retriever.yaml:16` 到 `configs/train_retriever.yaml:19`
- 实际训练 run 也是关闭：
  - `outputs/20260203_005729_cd195e/train_config.yaml:15`
  - `outputs/20260203_005729_cd195e/metrics.json:6`
  - `outputs/20260203_005729_cd195e/logs.txt:5`（`hard_enabled=False`）

## 3.3 是否应作为“封条硬要求”

建议：`降级为可选`（当前工程阶段）。

理由（以仓库事实为准）：
1. 现有 seal matrix（MVP10）未包含 HN on/off 对照，只验证了 pre/post FT 与系统模块消融（`configs/step6_matrix_seal.yaml:1` 到 `configs/step6_matrix_seal.yaml:116`）。
2. `METHODS_MILESTONE` 对 HN 是条件分支描述（“if enabled”），不是当前主结论的硬前提（`METHODS_MILESTONE.md:255` 到 `METHODS_MILESTONE.md:258`）。
3. 画图封条目标下，现有 pre/post FT 对照已经可画并可复查（`configs/step6_experiments_seal.yaml:2` 到 `configs/step6_experiments_seal.yaml:7`）。

---

## 4) Retriever 模型谱系表（pre-FT / post-FT / optional HN-FT）

| 谱系 | 模型路径/定义 | 训练来源 | 下游 run_id（从 outputs 反查） | 证据 |
|---|---|---|---|---|
| pre-FT | `sentence-transformers/all-MiniLM-L6-v2` | 无本地 FT（基座） | `20260217_123645_68f6b9_m01`, `20260217_122501_ed87fb_m01`, `20260217_162742_f5ae79_m01`, `20260130_014940_21aa62_m01`, `20260217_121446_1b39d3_t01`, `20260217_121809_fcfae7_t01` | 示例：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m01/config.resolved.yaml:22`；`outputs/20260217_123645_68f6b9/matrix.json:24` |
| post-FT | `models/retriever_ft/latest` | `outputs/20260203_005729_cd195e`（导出到 `models/retriever_ft/20260203_005729_cd195e`，并复制为 `latest`） | `20260217_123645_68f6b9_m02` 到 `m10`，`20260130_014940_21aa62_m02` 到 `m06`，`seal_mvp02`, `seal_mvp03`, `seal_mvp04`, `seal_mvp07`, `seal_mvp08` | 训练导出：`scripts/train_retriever.py:316` 到 `scripts/train_retriever.py:323`；下游调用：`configs/step6_matrix_seal.yaml:14`，`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/config.resolved.yaml:22` |
| HN-FT（可选） | 当前未见独立 HN-FT 模型目录或 run | 当前唯一 FT run 为 `hard_negatives.enabled=false` | 无（N/A） | `outputs/20260203_005729_cd195e/train_config.yaml:15`，`outputs/20260203_005729_cd195e/metrics.json:6` |

备注：上表 run_id 来自对 `outputs/**/summary.json + config.resolved.yaml` 的反查（以 summary 存在为准）。

---

## 5) 一致性风险（路径漂移 / 覆盖优先级 / legacy key）

## 风险 R1：`models/retriever_ft/latest` 是可变指针

- 风险：后续再次训练会覆盖 `latest`，导致 Step6 在相同 config 下读取到不同模型。
- 证据：
  - 训练脚本每次删除并重建 latest：`scripts/train_retriever.py:320` 到 `scripts/train_retriever.py:323`
  - Step6 seal 全部 post-FT run 使用 `latest`：`configs/step6_matrix_seal.yaml:14`（m03-m10 同理）

## 风险 R2：下游默认用 final 导出模型，不是 best checkpoint

- 风险：训练中 `best_model` 与最终 `model_dir` 可能不同；当前 Step6 默认读取后者。
- 证据：
  - best checkpoint 保存：`scripts/train_retriever.py:304` 到 `scripts/train_retriever.py:305`
  - final 导出与 latest 指向：`scripts/train_retriever.py:316` 到 `scripts/train_retriever.py:323`
  - 下游读取 `latest`：`configs/step6_matrix_seal.yaml:14`

## 风险 R3：配置覆盖链存在 legacy 映射，可能产生“隐式覆盖”

- 风险：旧键（如 `retriever.model_name`、顶层 `mode/alpha/top_k`）会在 `resolve_config` 阶段写入新 schema，若混用新旧键，优先级不直观。
- 证据：
  - legacy 映射：`src/config/schema.py:178` 到 `src/config/schema.py:214`
  - 旧式配置示例：`configs/run_baseline.yaml:6` 到 `configs/run_baseline.yaml:11`，`configs/run_multistep.yaml:7` 到 `configs/run_multistep.yaml:13`
  - 统一入口先 override 再 resolve：`scripts/run_experiment.py:79`，`scripts/run_experiment.py:97`

## 风险 R4：seal commit 与 FT 训练 commit 不一致（可追溯但未绑定）

- 风险：seal 运行 commit 是 `27c146...`，FT 训练 commit 是 `a57a56...`；目前通过日志可追溯，但 matrix 没有“模型文件hash”字段。
- 证据：
  - seal matrix commit：`outputs/20260217_123645_68f6b9/matrix.json:4`
  - seal run commit：`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m02/git_commit.txt:1`
  - FT run commit：`outputs/20260203_005729_cd195e/train_config.yaml:32`

---

## 6) 对封条阶段的最小建议（不新增实验）

1. 在封条 matrix 中把 `retriever.dense.model_name_or_path` 从 `models/retriever_ft/latest` 固化为 `models/retriever_ft/20260203_005729_cd195e`（避免后续漂移）。
2. 在 seal 文档中显式写明“当前 Step3 使用的是 non-HN FT”；HN 对照暂不作为封条硬门槛。
3. 若后续论文要主张 HN 收益，再补 1 组最小 A/B：同一配置仅切 `hard_negatives.enabled`，其余不变。

