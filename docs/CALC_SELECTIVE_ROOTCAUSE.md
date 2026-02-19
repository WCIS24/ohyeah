# CALC Selective Root Cause (Short)

## 0.1 失败后输出分布劣化（placeholder / 非 baseline answer）

结论：
- 旧链路在 `calculator` 未通过 gate 时，直接写 `placeholder_generate(...)`，而不是主链路 baseline answer。
- 这条路径会把大量样本写成模板化文本，导致 `fallback_ratio` 与路由分布恶化，并放大 `calc_used` vs `fallback` 质量差。

代码证据：
- placeholder 生成函数：`scripts/run_with_calculator.py:119`
- 旧逻辑失败分支写 placeholder：`scripts/run_with_calculator.py:1219`
- 旧逻辑失败分支计入 fallback：`scripts/run_with_calculator.py:1221`
- gate 将 `status_xxx` 映射为拒用原因：`scripts/run_with_calculator.py:1194`, `scripts/run_with_calculator.py:1196`

运行证据（当前 closure 对照）：
- `C1` 相对 `C0`：`delta_fallback_ratio=+0.0794`（guardrail fail）
  - 来源：`outputs/seal_checks/calc_closure_compare.json:79`, `outputs/seal_checks/calc_closure_compare.json:85`
- `C2/C3` guardrail 虽过，但 `gap_shrink<0`
  - 来源：`outputs/seal_checks/calc_closure_compare.json:119`, `outputs/seal_checks/calc_closure_compare.json:158`

机制解释：
- 旧流程把“算不出来/不该算”的 query 仍送入计算链，失败后写模板文本，形成额外 fallback 压力；
- 同时 `calc_used` 路由质量并未提升，导致 `gap_shrink` 仍为负。

## 0.2 `status_insufficient_facts` 激增触发条件与 C2(事实选择)机制

结论：
- `insufficient_facts` 的主触发是：任务被识别为可算（尤其 `yoy`）但入算 facts 不满足年/操作数约束；
- 在事实选择更激进时（hard scored selector），`selected_fact_count` 大幅下降，`yoy` 更容易触发 `missing_years`。

代码证据（触发条件）：
- `yoy` 缺少可用双年份，直接 `status=insufficient_facts`：`src/calculator/compute.py:538`, `src/calculator/compute.py:560`
- `yoy` 失败原因 `missing_years`：`src/calculator/compute.py:545`, `src/calculator/compute.py:567`
- `diff/share/multiple` 在操作数不足时也会 `insufficient_facts`：`src/calculator/compute.py:665`, `src/calculator/compute.py:747`, `src/calculator/compute.py:850`
- 抽取阶段会把 query 年份推断到 fact（inferred year）：`src/calculator/extract.py:121`
- gate 对 inferred year 有额外拒用：`scripts/run_with_calculator.py:1207`, `scripts/run_with_calculator.py:1209`

代码证据（为何事实选择会放大该问题）：
- scored selector 在 top-groups 过滤后只保留很小候选池：`scripts/run_with_calculator.py:627`, `scripts/run_with_calculator.py:654`, `scripts/run_with_calculator.py:680`
- 当候选内缺少跨年/同单位配对时，计算器进入 `insufficient_facts`/`unit_mismatch`。

运行证据：
- 当前 closure 对照中，激进 scored 路由（C1）`status_insufficient_facts` 从 `C0=16` 升到 `51`：
  - `outputs/20260219_071245_dd1cc7/runs/20260219_071245_dd1cc7_m01_calc/calc_stats.json`
  - `outputs/20260219_071245_dd1cc7/runs/20260219_071245_dd1cc7_m02_calc/calc_stats.json`
- 同时 `selected_fact_count_mean` 从 `38.50` 降到 `3.64`（同上两文件 `fact_selector_stats`）。

备注：
- 你的描述中“C0=16 -> C2=61”与当前仓库最新 closure 文件编号不一致；但根因一致：**事实选择过窄 + 年份/单位约束下的可算性不足** 会系统性抬高 `insufficient_facts`。
