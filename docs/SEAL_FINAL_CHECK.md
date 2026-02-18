# SEAL Final Check

## 结论
- **Ready**
- 冻结标识：`smoke_run_id=seal_final_smoke`，`matrix_id=20260218_160058_ee7290`。
- 判定快照：`outputs/seal_checks/seal_final_snapshot.json:3`、`outputs/seal_checks/seal_final_snapshot.json:6`、`outputs/seal_checks/seal_final_snapshot.json:7`。

## 环境与命令
- Git 提交：`7b4f157`（`outputs/seal_checks/seal_final_snapshot.json:4`）。
- Python：`3.12.7`（`outputs/seal_final_smoke/env_versions.json:5`）。
- 依赖快照：`outputs/seal_final_smoke/env_versions.json:2`、`outputs/seal_final_smoke/env_versions.json:10`。
- 执行命令（按要求顺序）：
  1. `python scripts/smoke.py --config configs/smoke.yaml --run-id seal_final_smoke`
  2. `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/tmp_matrix_seal_pqe_only.yaml`
  3. `python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml`
  4. `python scripts/plot_all.py --config scripts/plot_config.yaml`
- 命令证据：`outputs/seal_checks/seal_final_snapshot.json:11`、`outputs/seal_checks/seal_final_snapshot.json:15`、`outputs/seal_checks/seal_final_snapshot.json:19`、`outputs/seal_checks/seal_final_snapshot.json:23`。

## 产物清单
- 矩阵元数据：`outputs/20260218_160058_ee7290/matrix.json`、`outputs/20260218_160058_ee7290/experiments_resolved.yaml`。
- 运行摘要：
  - `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m01/summary.json`
  - `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m02/summary.json`
  - `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m03/summary.json`
  - `outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04/summary.json`
- 封装脚本：`scripts/seal_reproduce.sh:1`、`scripts/seal_reproduce.sh:13`、`scripts/seal_reproduce.sh:25`。
- 冻结快照：`outputs/seal_checks/seal_final_snapshot.json:1`。

## 表图对齐
- PQE 映射到最新矩阵 run：`configs/step6_experiments_seal.yaml:54`、`configs/step6_experiments_seal.yaml:57`、`configs/step6_experiments_seal.yaml:60`。
- 主表已消费最新 PQE：`docs/TABLE_MAIN.md:20`、`docs/TABLE_MAIN.md:21`、`docs/TABLE_MAIN.md:22`。
- 数值表已消费最新 PQE：`docs/TABLE_NUMERIC.md:20`、`docs/TABLE_NUMERIC.md:21`、`docs/TABLE_NUMERIC.md:22`。
- 消融表含 PQE 消融臂：`docs/TABLE_ABLATION.md:13`、`docs/TABLE_ABLATION.md:14`。
- 全表 run_id 到 `summary.json` 可追溯：`outputs/seal_checks/seal_final_table_traceability.json:387`。
- plot `has_data=False` 数量为 0：`outputs/seal_checks/seal_final_snapshot.json:269`。
- 图产物落盘：`outputs/seal_checks/seal_final_plot_all_cmd.log:8`、`thesis/figures_seal/ThemeA/figures/ablation_breakdown.pdf`。

## 消融闭环
- multistep baseline 在官方表：`docs/TABLE_MAIN.md:7`、`docs/TABLE_MAIN.md:8`、`docs/TABLE_NUMERIC.md:7`、`docs/TABLE_NUMERIC.md:8`。
- calculator 系列在官方表：`docs/TABLE_MAIN.md:14`、`docs/TABLE_MAIN.md:17`、`docs/TABLE_NUMERIC.md:14`、`docs/TABLE_NUMERIC.md:17`。
- PQE 主结果在官方表：`docs/TABLE_MAIN.md:20`、`docs/TABLE_MAIN.md:21`、`docs/TABLE_MAIN.md:22`。
- numeric 评测策略可审计（`extract_strategy=first`）：`outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04/summary.json:72`、`outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04/summary.json:88`。

## 风险与回滚
- 风险 1（非阻断）：绘图样式文件未命中 warning（不影响出图）`outputs/seal_checks/seal_final_plot_all_cmd.log:6`。
- 风险 2（已收敛）：`configs/` 中 `latest` 软路径已清零，扫描结果 `NO_MATCH`（`outputs/seal_checks/seal_final_config_latest_scan.log:1`）。
- 风险 3（变更面）：本次冻结更新了路径锁定与表图指向（`configs/step6_matrix.yaml:11`、`configs/search_space_calc.yaml:2`、`configs/search_space_multistep.yaml:2`、`configs/step6_postft_baseline.yaml:21`）。
- 回滚点：回滚以上 5 个配置文件 + `configs/step6_experiments_seal.yaml` + `docs/TABLE_*.md` + `scripts/seal_reproduce.sh` 即可恢复冻结前状态。

## Checklist（逐条可验证）
- [x] 一键链路四条命令均执行并产生日志：`outputs/seal_checks/seal_final_snapshot.json:10`、`outputs/seal_checks/seal_final_snapshot.json:14`、`outputs/seal_checks/seal_final_snapshot.json:18`、`outputs/seal_checks/seal_final_snapshot.json:22`。
- [x] `matrix.json` / `experiments_resolved.yaml` / run `summary.json` 齐全：`outputs/seal_checks/seal_final_snapshot.json:28`、`outputs/seal_checks/seal_final_snapshot.json:29`、`outputs/seal_checks/seal_final_snapshot.json:37`。
- [x] 日志包含 seed 与 git_hash：`outputs/seal_checks/seal_final_smoke_cmd.log:3`、`outputs/seal_checks/seal_final_matrix_cmd.log:4`、`outputs/seal_checks/seal_final_matrix_cmd.log:7`。
- [x] `configs` 不再引用 `latest`：`outputs/seal_checks/seal_final_config_latest_scan.log:1`。
- [x] 主表/数值表/消融表包含 PQE 与关键 baseline/calculator 行：`docs/TABLE_MAIN.md:20`、`docs/TABLE_NUMERIC.md:20`、`docs/TABLE_ABLATION.md:13`、`docs/TABLE_MAIN.md:7`、`docs/TABLE_MAIN.md:14`。
- [x] 表格行可追溯到 `summary.json`：`outputs/seal_checks/seal_final_table_traceability.json:387`。
- [x] 绘图 `has_data=False` 数量为 0，图路径可定位：`outputs/seal_checks/seal_final_snapshot.json:269`、`outputs/seal_checks/seal_final_plot_all_cmd.log:8`。
- [x] matrix 元数据闭环与状态正常：`outputs/seal_checks/seal_final_snapshot.json:30`、`outputs/seal_checks/seal_final_snapshot.json:288`。
- [x] numeric 策略可审计字段存在：`outputs/seal_checks/seal_final_snapshot.json:263`。
- [x] 无“静默失效”配置键结论（以最终检查项通过为准）：`outputs/seal_checks/seal_final_snapshot.json:284`、`outputs/seal_checks/seal_final_snapshot.json:295`。
