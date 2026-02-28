# Calculator / Numeric QA Design

Purpose:
- Document numeric QA task types, fact extraction rules, combo routing, and audit outputs for method reproducibility.

How to use:
- Cite this document for numeric reasoning logic and point to the code paths listed in `[EVIDENCE]`.

## Fact extraction (from evidence text)
- Numbers, years, percentages, and currency/scale cues are detected via regex; metrics such as revenue/profit are matched by keyword windows. `[EVIDENCE] src/calculator/extract.py:7-88`
- Each extracted `Fact` stores `metric/entity/year/value/unit/confidence`; missing years can be inferred from the query with a confidence penalty. `[EVIDENCE] src/calculator/extract.py:97-154`

## Task detection and task types
- Legacy calculator task types are inferred from query keywords: `yoy`, `diff`, `share`, `multiple`. `[EVIDENCE] src/calculator/compute.py:9-59`
- `detect_task(...)` returns `None` if no task keyword matches, which leads the legacy calculator to skip with `status="no_match"`. `[EVIDENCE] src/calculator/compute.py:49-59; src/calculator/compute.py:572-598`

## Grouping and candidate selection
- Legacy module `B` groups facts by `(metric, entity, unit)` and selects the largest group as the candidate set for computation. `[EVIDENCE] src/calculator/compute.py:62-77; src/calculator/compute.py:599-614`
- For non-year tasks (`diff/share/multiple`), ambiguity is flagged if multiple candidates exist without year anchors. `[EVIDENCE] src/calculator/compute.py:616-637`

## Computation and confidence
- `compute_for_query(...)` dispatches to `compute_yoy / compute_diff / compute_share / compute_multiple` and assigns confidence from input quality. `[EVIDENCE] src/calculator/compute.py:639-670; src/calculator/compute.py:80-115`
- For `yoy`, missing years, unit mismatch, or division by zero produce failure statuses such as `insufficient_facts`, `unit_mismatch`, and `invalid`. `[EVIDENCE] src/calculator/compute.py:129-239`

## Legacy gating and fallback
- `run_with_calculator.py` still supports the original gate logic: allow-list task types, minimum confidence, unit consistency, and year match checks. Rejected calculator outputs fall back to placeholder generation and record `fallback_reason`. `[EVIDENCE] scripts/run_with_calculator.py:1185-1220`

## Combo mode (A⊕B, default off)
- `configs/step6_base.yaml` does not define any combo keys. `run_with_calculator.py` reads `calculator.combo.enabled`, `calculator.fact_filter.enabled`, and `calculator.value.enabled` with default `false`, so the old Step6 path remains unchanged unless the new keys are explicitly set. `[EVIDENCE] configs/step6_base.yaml; scripts/run_with_calculator.py:907-930`
- When `calculator.combo.enabled=false`, the run stays on legacy module `B`. Audit fields are still written, but they record `used_module="B"` and `route_reason="combo_disabled"` rather than changing behavior. `[EVIDENCE] scripts/run_with_calculator.py:1056-1058; scripts/run_with_calculator.py:1497-1499`
- When `calculator.combo.enabled=true`, routing is:
  1. extract `facts_raw`
  2. optionally apply `filter_facts(...)`
  3. if `calculator.value.enabled=true` and `predict_value_for_query(...)` returns `ok` with confidence `>= tau_a`, emit module `A`
  4. else, if `calculator.combo.use_b=true`, run legacy module `B`
  5. else, emit fallback text
  `[EVIDENCE] scripts/run_with_calculator.py:1133-1140; scripts/run_with_calculator.py:1180-1275`

## Module A: value prediction
- Module `A` is query-only and does not read gold answers.
- `numeric_intent(query)` is a deterministic rule over query text only. `[EVIDENCE] src/calculator/value_task.py:19-73`
- `year_hint`, `percent_hint`, and `unit_hint` derive soft expectations from the query. `[EVIDENCE] src/calculator/value_task.py:49-63`
- `predict_value_for_query(...)` filters facts by confidence, scores them deterministically, and returns a top-1 value with `(status, value, unit, confidence, reason)`. `[EVIDENCE] src/calculator/value_task.py:147-195`
- `format_result_line(...)` preserves the calculator output shape: `Result: <num> <unit>`. `[EVIDENCE] src/calculator/value_task.py:141-145`

## Fact filter
- `filter_facts(...)` is deterministic and side-effect free. `[EVIDENCE] src/calculator/fact_filter.py:65-100`
- Supported operations:
  - drop year-like values in `[1900, 2099]` when both `metric` and `unit` are missing
  - enforce `min_conf`
  - keep only top `N` facts per `(metric, entity, unit)` group
  `[EVIDENCE] src/calculator/fact_filter.py:31-63; src/calculator/fact_filter.py:71-100`

## Fallback modes
- `calculator.fallback.mode="template"` keeps the historical placeholder output.
- `calculator.fallback.mode="mask_numbers"` applies a deterministic regex replacement from numeric spans to `#`.
- `calculator.fallback.mode="no_number"` returns the fixed sentence `Insufficient numeric evidence.`
- Invalid fallback modes are coerced back to `template`. `[EVIDENCE] scripts/run_with_calculator.py:139-144; scripts/run_with_calculator.py:929-935`

## Audit fields and files
- Every row in `predictions_calc.jsonl` now includes:
  - `used_module`
  - `route_reason`
  - `fallback_mode`
  `[EVIDENCE] scripts/run_with_calculator.py:1497-1499`
- `calc_used_records.jsonl` also records:
  - route state
  - value-route status/reason/confidence/threshold
  - pre-gate audit
  - selected facts/chunks/numbers
  `[EVIDENCE] scripts/run_with_calculator.py:1522-1570`
- Each run writes `calc_audit.json`, which summarizes:
  - combo enablement and `use_b`
  - `used_module_counts`
  - `route_reason_counts`
  - `fallback_mode_counts`
  - value-module `status/reason/reject_reason`
  - fact-filter kept/removed counts
  `[EVIDENCE] scripts/run_with_calculator.py:1591-1617`

## Configuration dictionary

Legacy behavior requires no new config. The following keys are optional and default-safe:

```yaml
calculator:
  combo:
    enabled: false
    use_b: true
    tau_a: 0.6
  value:
    enabled: false
    min_confidence: 0.6
    weights:
      metric_present: 0.05
      year_match: 0.20
      year_mismatch: 0.10
      year_missing: 0.05
      percent_match: 0.15
      percent_mismatch: 0.12
      unit_match: 0.10
      unit_mismatch: 0.08
      inferred_year_penalty: 0.08
  fact_filter:
    enabled: false
    min_conf: 0.0
    max_facts_per_group: 0
    drop_year_like_values:
      enabled: true
      min_year: 1900
      max_year: 2099
  fallback:
    mode: template
```

Notes:
- `combo.enabled=false` is the main rollback switch.
- `value.enabled=false` disables module `A` even if combo is on.
- `use_b=false` routes `A` rejection directly to fallback.
- `max_facts_per_group <= 0` keeps all facts.

## Numeric evaluation
- `eval_numeric.py` extracts numbers from predictions and gold answers, computes `coverage` from whether prediction-side numeric extraction succeeded, computes `numeric_em` on rows with both sides numeric, and writes `numeric_per_query.jsonl` plus `numeric_metrics.json`. `[EVIDENCE] scripts/eval_numeric.py:347-413`

## Rollback
- Safe rollback: leave combo keys unset, or set `calculator.combo.enabled=false`.
- Full code rollback: remove `src/calculator/fact_filter.py`, `src/calculator/value_task.py`, `src/calculator/combo_types.py`, and revert the combo-specific blocks in `scripts/run_with_calculator.py`.
