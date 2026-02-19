# Calculator Diagnosis Report

## 1) 现象复述（m08 / m08d / m13+calc）

- 现象成立：`m13_pqe_calc` 相比 `m08_allow_yoy_diff`，coverage 上升但 numeric_em 下降。  
  证据：`outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04/summary.json:61-72`，`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json:61-72`，以及聚合差分 `outputs/seal_checks/calc_diagnosis_metrics.json:837-845`。
- 现象细分（基于 per-query join）：`m13` 的整体 coverage 更高，但 `calc_used` 桶的 EM 极低，拉低了闭环质量。  
  证据：`outputs/seal_checks/calc_diagnosis_metrics.json:520-547`（m13），`outputs/seal_checks/calc_diagnosis_metrics.json:23-49`（m08）。

## 2) D1: calc_used vs fallback 分解

### 关键结论（只保留重要问题）

- `calc_used` 明显劣于 `fallback`（远超 0.05 阈值），主因不是“没抽到数字”，而是“算了但算错/选错事实”。  
  证据（m13）：
  - `calc_used.em_on_covered=0.0122`，`fallback.em_on_covered=0.3866`：`outputs/seal_checks/calc_diagnosis_metrics.json:533-547`。
  - `calc_used` 中 `wrong_fact=81/82`：`outputs/seal_checks/calc_diagnosis_metrics.json:533-540`。
- `m08` 同样模式：`calc_used.em_on_covered=0.0000`，`fallback.em_on_covered=0.4034`。  
  证据：`outputs/seal_checks/calc_diagnosis_metrics.json:35-49`。
- 绝大多数 fallback 来自 `gate_task`，说明 task 识别/任务类型覆盖是上游瓶颈。  
  证据：`outputs/seal_checks/calc_diagnosis_metrics.json:67-71`（m08），`outputs/seal_checks/calc_diagnosis_metrics.json:565-569`（m13）。

### 机制证据（代码）

- gate 决策与 fallback 分流：`scripts/run_with_calculator.py:267-293`。  
- `unknown/no_match` 与任务识别入口：`src/calculator/compute.py:49-59`，`src/calculator/compute.py:577-613`。  
- YoY 在缺乏明确对齐时按高置信年份回退选值，易引入“年份值被当作财务值”类错误：`src/calculator/compute.py:141-152`。

## 3) D2: “首数字误伤”是否仍残留

- 残留存在，但不是当前 EM 下降主因。  
  - `first` vs `result_tag`：`pred_number_changed_qid_count=30`，且这 30 条 `both_wrong_when_pred_changed=30`，互无净增益。  
    证据：`outputs/seal_checks/calc_diagnosis_metrics.json:868-873`。  
  - 官方比较同样显示 aggregate 不变：`delta_result_tag_minus_first` 全 0。  
    证据：`outputs/seal_checks/calc_diagnosis_metrics.json:1096-1100`，`outputs/seal_checks/numeric_extraction_strategy_compare.json:15-19`。
- 多数差异样本都出现在 `Result: ...` 后面含多个数字的表达式文本中（例如 YoY / diff 展开式）。  
  证据：`outputs/seal_checks/calc_diagnosis_metrics.json:883-924`，`outputs/seal_checks/calc_diagnosis_metrics.json:1112-1124`。

### 口径建议（兼容开关，不破旧逻辑）

- 保留 `first` 为默认（兼容历史），新增可选策略：
  - `result_tag_strict`：仅取 `Result:` 标签后的数；失败不回退 first。
  - `best_match_with_tolerance`：只在评测层启用，基于容差从候选数中选与 gold 最接近者（仅用于诊断，不默认用于主表）。
- 当前代码已支持策略开关入口：`scripts/eval_numeric.py:149-200`，并将每题策略落盘：`scripts/eval_numeric.py:298-337`。

## 4) D3: fact 噪声轻量消融（max_chunks_for_facts）

### 已完成改动（可配置、可一行开关）

- 新增配置键：`calculator.evidence.max_chunks_for_facts`。  
  证据：`src/config/schema.py:48-50`，`src/config/schema.py:129-137`。
- 在 calculator 抽取时生效（只截取前 N 个 chunk 做事实抽取）。  
  证据：`scripts/run_with_calculator.py:162-171`，`scripts/run_with_calculator.py:235-236`。
- 抽取统计中落盘该键，便于审计。  
  证据：`scripts/run_with_calculator.py:320-330`。

### 新对照配置与运行

- 新 matrix 配置（可进入 Step6 链路）：
  - `configs/tmp_matrix_calc_diag_maxchunks.yaml:1-39`（baseline vs `calculator.evidence.max_chunks_for_facts=3`）。
  - Step6 experiments 清单（供 `make_tables.py` 使用）：`configs/step6_experiments_calc_diag.yaml:1-7`。
- 实际运行产物：`outputs/20260219_011425_65f019/matrix.json:1-159`。

### 消融结果（只保留结论）

- `top3` 相比 baseline：
  - coverage 下降（`-0.00644`），EM(all) 仅微升（`+0.00215`），不是稳健收益。  
    证据：`outputs/seal_checks/calc_diagnosis_metrics.json:854-857`。
  - 事实量显著下降（`39707 -> 22899`），但 `status_insufficient_facts` / `status_no_match` 变多。  
    证据：`outputs/20260219_011425_65f019/runs/20260219_011425_65f019_m01_calc/extract_stats.json:5-7`，`outputs/20260219_011425_65f019/runs/20260219_011425_65f019_m02_calc/extract_stats.json:5-7`，`outputs/20260219_011425_65f019/runs/20260219_011425_65f019_m01_calc/calc_stats.json:16-20`，`outputs/20260219_011425_65f019/runs/20260219_011425_65f019_m02_calc/calc_stats.json:16-20`。

## 5) 原因链条（结论）

1. 主矛盾是 `calc_used` 质量，而不是 `fallback` 覆盖。  
   证据：`outputs/seal_checks/calc_diagnosis_metrics.json:533-547`，`outputs/seal_checks/calc_diagnosis_metrics.json:35-49`。  
2. task/gate 把大量样本分流到 `gate_task`，calculator 真正接管的样本少且错得多。  
   证据：`outputs/seal_checks/calc_diagnosis_metrics.json:67-71`，`outputs/seal_checks/calc_diagnosis_metrics.json:565-569`，`scripts/run_with_calculator.py:267-277`。  
3. numeric 抽取策略（first/result_tag）不是主因：改口径不改变 aggregate。  
   证据：`outputs/seal_checks/calc_diagnosis_metrics.json:868-873`，`outputs/seal_checks/calc_diagnosis_metrics.json:1096-1100`。

## 6) 改进候选（按成本/收益排序）

1. **高收益/中高成本**：任务识别前置 + calculator dispatch 重构  
   目标：显著提高 `calc_used` EM。  
   关键点：把 `unknown`/`gate_task` 前置为可学习或规则增强的 task classifier，再决定是否进 calculator。  
   代码锚点：`src/calculator/compute.py:49-59`，`scripts/run_with_calculator.py:267-277`。
2. **中收益/中成本**：事实选择器（entity/year/unit 一致性打分）替代“仅靠置信度取值”  
   目标：降低 `wrong_fact`。  
   代码锚点：`src/calculator/compute.py:141-152`，`src/calculator/compute.py:599-640`。
3. **低收益/低成本**：评测抽取策略补丁（strict result_tag / best-match）  
   目标：减少口径噪声，但不应被当作主增益。  
   代码锚点：`scripts/eval_numeric.py:149-200`，`scripts/eval_numeric.py:298-337`。

## 7) 推荐方案（继续做 / 停在现状）

**推荐：本轮封板“停在现状”（不宣称 calculator 闭环成功），把 Calculator 定位为诊断模块；下一里程碑再做 1、2 两项结构性修复。**

理由：
- 决策阈值已触发：`calc_used` 比 `fallback` EM 低很多（远超 0.05）。  
  证据：`outputs/seal_checks/calc_diagnosis_metrics.json:533-547`。
- 低成本修补（D2、D3）都不能稳定关闭 gap。  
  证据：`outputs/seal_checks/calc_diagnosis_metrics.json:854-857`，`outputs/seal_checks/calc_diagnosis_metrics.json:868-873`。

## 8) 论文严谨写法（可直接用）

### 中文

我们观察到在引入 Calculator 后，numeric coverage 有小幅提升，但 numeric EM 未同步提升。进一步分解显示，Calculator 实际接管样本（calc_used）的准确率显著低于 fallback 样本，主要误差来自事实选择与任务识别，而非评测抽取策略本身。我们通过限制事实抽取 chunk 数做了轻量消融，结果仅表现为轻微 EM 波动并伴随 coverage 回落，未形成稳定增益。因此本文将 Calculator 作为误差诊断组件，而非主增益来源；其闭环优化（任务识别与事实选择）留作后续工作。

### English (optional)

After enabling Calculator, numeric coverage improves slightly, but numeric EM does not improve accordingly. A calc_used-vs-fallback decomposition shows that calculator-handled cases are substantially less accurate than fallback cases, indicating that the bottleneck is mainly in task identification and fact selection rather than in numeric extraction policy. A lightweight fact-noise ablation (limiting fact extraction chunks) only yields marginal EM fluctuation with coverage drop, without robust gains. Therefore, in this paper we treat Calculator as a diagnostic module rather than a primary source of improvement, and leave full-loop optimization (task dispatch and fact selection) to future work.

## 9) 产物清单

- 诊断报告：`docs/CALC_DIAGNOSIS_REPORT.md`
- 分桶统计：`outputs/seal_checks/calc_diagnosis_metrics.json`
- 最小 patch：
  - `src/config/schema.py`
  - `scripts/run_with_calculator.py`
  - `scripts/calc_diagnosis.py`
- 新对照配置：
  - `configs/tmp_matrix_calc_diag_maxchunks.yaml`
  - `configs/step6_experiments_calc_diag.yaml`
- 新运行矩阵：
  - `outputs/20260219_011425_65f019/matrix.json`
