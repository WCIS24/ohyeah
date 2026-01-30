# Results: Calculator

This document records Step5 calculator experiments.

## Run IDs
- baseline predictions: `outputs/20260130_185127_8a0062`
- baseline numeric eval (numeric_dev): `outputs/20260130_190114_3ec5bf`
- baseline numeric eval (full dev): `outputs/20260130_190715_b565d1`
- baseline_calc predictions: `outputs/20260130_190127_ad7219`
- baseline_calc numeric eval (numeric_dev): `outputs/20260130_190513_1f2ea4`
- baseline_calc numeric eval (full dev): `outputs/20260130_190723_6186ed`
- multistep_calc predictions: `outputs/20260130_190522_3b7f80`
- multistep_calc numeric eval (numeric_dev): `outputs/20260130_190531_02d136`
- multistep_calc numeric eval (full dev): `outputs/20260130_190730_3c598c`

## Full dev metrics
| Setting | Run ID | Numeric-EM | RelErr mean | RelErr median | Coverage |
| --- | --- | --- | --- | --- | --- |
| baseline | 20260130_190715_b565d1 | 0.3617 | 411.8625 | 0.8861 | 0.5526 |
| baseline + calculator | 20260130_190723_6186ed | 0.3106 | 2717.5961 | 0.9250 | 0.6018 |
| multistep + calculator | 20260130_190730_3c598c | 0.3038 | 301.9089 | 0.9125 | 0.6070 |

## numeric_dev metrics
| Setting | Run ID | Numeric-EM | RelErr mean | RelErr median | Coverage |
| --- | --- | --- | --- | --- | --- |
| baseline | 20260130_190114_3ec5bf | 0.3617 | 411.8625 | 0.8861 | 0.6245 |
| baseline + calculator | 20260130_190513_1f2ea4 | 0.3106 | 2717.5961 | 0.9250 | 0.6609 |
| multistep + calculator | 20260130_190531_02d136 | 0.3038 | 301.9089 | 0.9125 | 0.6674 |

## Delta vs baseline
- baseline_calc - baseline:
  - numeric_dev: `outputs/20260130_190513_1f2ea4/delta_vs_baseline.json`
  - full dev: `outputs/20260130_190723_6186ed/delta_vs_baseline.json`
- multistep_calc - baseline:
  - numeric_dev: `outputs/20260130_190531_02d136/delta_vs_baseline.json`
  - full dev: `outputs/20260130_190730_3c598c/delta_vs_baseline.json`

## Notes
- Use outputs/<run_id>/numeric_metrics.json for values.
- See outputs/<run_id>/calc_stats.json for calculator success and error reasons.
