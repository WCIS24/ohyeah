# Results: Calculator

This document records Step5 calculator experiments.

## Run IDs
- baseline predictions: `outputs/20260128_211020_5935a8`
- baseline numeric eval (numeric_dev): `outputs/20260128_212644_cbacd4`
- baseline numeric eval (full dev): `outputs/20260128_212727_5321e1`
- baseline_calc predictions: `outputs/20260128_212135_315d34`
- baseline_calc numeric eval (numeric_dev): `outputs/20260128_212744_daf6fd`
- baseline_calc numeric eval (full dev): `outputs/20260128_212754_7cc4ca`
- multistep_calc predictions: `outputs/20260128_212621_cd2ac8`
- multistep_calc numeric eval (numeric_dev): `outputs/20260128_212800_9d488c`
- multistep_calc numeric eval (full dev): `outputs/20260128_212807_4ff352`

## Full dev metrics
| Setting | Run ID | Numeric-EM | RelErr mean | RelErr median | Coverage |
| --- | --- | --- | --- | --- | --- |
| baseline | 20260128_212727_5321e1 | 0.3617 | 417.6051 | 0.8911 | 0.5526 |
| baseline + calculator | 20260128_212754_7cc4ca | 0.2819 | 2674.6817 | 0.9714 | 0.6140 |
| multistep + calculator | 20260128_212807_4ff352 | 0.2785 | 2674.7331 | 0.9762 | 0.6140 |

## numeric_dev metrics
| Setting | Run ID | Numeric-EM | RelErr mean | RelErr median | Coverage |
| --- | --- | --- | --- | --- | --- |
| baseline | 20260128_212644_cbacd4 | 0.3617 | 417.6051 | 0.8911 | 0.6245 |
| baseline + calculator | 20260128_212744_daf6fd | 0.2819 | 2674.6817 | 0.9714 | 0.6717 |
| multistep + calculator | 20260128_212800_9d488c | 0.2785 | 2674.7331 | 0.9762 | 0.6717 |

## Delta vs baseline
- baseline_calc - baseline:
  - numeric_dev: `outputs/20260128_212744_daf6fd/delta_vs_baseline.json`
  - full dev: `outputs/20260128_212754_7cc4ca/delta_vs_baseline.json`
- multistep_calc - baseline:
  - numeric_dev: `outputs/20260128_212800_9d488c/delta_vs_baseline.json`
  - full dev: `outputs/20260128_212807_4ff352/delta_vs_baseline.json`

## Notes
- Use outputs/<run_id>/numeric_metrics.json for values.
- See outputs/<run_id>/calc_stats.json for calculator success and error reasons.
