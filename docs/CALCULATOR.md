# Calculator: Evidence -> Facts -> Computation -> Answer

This module provides a deterministic numeric pipeline without external LLMs:

1) Evidence chunks -> structured facts (rule-based extraction)
2) Facts -> calculation result (YoY/diff/share/multiple)
3) Result -> template answer

## Fact schema

```json
{
  "qid": "string",
  "chunk_id": "string",
  "metric": "string | null",
  "entity": "string | null",
  "year": 2021,
  "period": "string | null",
  "value": 123.45,
  "unit": "USD | % | null",
  "raw_span": "short evidence span",
  "confidence": 0.0,
  "inferred_year": false
}
```

### Extraction rules (summary)
- Numbers: integers, decimals, and thousand separators (e.g., 1,234.5)
- Percent: `%` or `percent/percentage`
- Year: 19xx/20xx in chunk; if absent, inherit from query (lower confidence)
- Units: currency symbols ($/USD/CNY/RMB/EUR/HKD) and scale words (k/m/b)
- Metric: keyword match within local window

## Result (R) schema

```json
{
  "qid": "string",
  "task_type": "yoy|diff|share|multiple|unknown",
  "inputs": [
    {"year": 2021, "value": 100.0, "unit": "USD", "chunk_id": "c-1"}
  ],
  "result_value": 12.34,
  "result_unit": "%",
  "explanation": "YoY = (x_t - x_t-1) / x_t-1",
  "confidence": 0.0,
  "status": "ok|no_match|ambiguous|unit_mismatch|insufficient_facts|invalid"
}
```

## Alignment + ambiguity handling
- Alignment key: (metric, entity, unit).
- If multiple candidates exist for a key:
  - choose the highest confidence when safe
  - mark `ambiguous` and refuse to compute when conflicts remain
- Unit mismatch: do not compute; return `unit_mismatch`.

## Output files
- `facts.jsonl`: extracted facts
- `results_R.jsonl`: per-query calculator results
- `calc_traces.jsonl`: selection and rejection reasons
- `predictions_calc.jsonl`: final answers with fallback reasons

