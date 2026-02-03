# Calculator / Numeric QA Design

Purpose:
- Document numeric QA task types, fact extraction rules, and calculator gating for method reproducibility.

How to use:
- Cite this document for numeric reasoning logic and point to the code paths listed in [EVIDENCE].

## Fact extraction (from evidence text)
- Numbers, years, percentages, and currency/scale cues are detected via regex; metrics (e.g., revenue/profit) are matched by keyword windows.[EVIDENCE] src/calculator/extract.py:7-88
- Each extracted Fact stores metric/entity/year/value/unit and confidence; missing year can be inferred from query years with a confidence penalty.[EVIDENCE] src/calculator/extract.py:97-154

## Task detection and task types
- Task types are inferred from query keywords: yoy, diff, share, multiple.[EVIDENCE] src/calculator/compute.py:9-59
- detect_task returns None if no task keyword matches, causing the calculator to skip with status "no_match".[EVIDENCE] src/calculator/compute.py:49-59; src/calculator/compute.py:572-598

## Grouping and candidate selection
- Facts are grouped by (metric, entity, unit) and the largest group is selected as the candidate set for computation.[EVIDENCE] src/calculator/compute.py:62-77; src/calculator/compute.py:599-614
- For non-year tasks (diff/share/multiple), ambiguity is flagged if multiple candidates exist without year anchors.[EVIDENCE] src/calculator/compute.py:616-637

## Computation and confidence
- compute_for_query dispatches to compute_yoy / compute_diff / compute_share / compute_multiple and assigns confidence based on input quality.[EVIDENCE] src/calculator/compute.py:639-670; src/calculator/compute.py:80-115
- For yoy, missing years, unit mismatch, or division by zero produce failure statuses (insufficient_facts/unit_mismatch/invalid).[EVIDENCE] src/calculator/compute.py:129-239

## Calculator gating and fallback
- run_with_calculator applies gate rules (allow_task_types, min_conf, unit/year consistency) before accepting calculator outputs; otherwise it falls back to placeholder generation and records fallback_reason.[EVIDENCE] scripts/run_with_calculator.py:244-279

## Numeric evaluation
- eval_numeric extracts numbers from predictions/gold, computes numeric_em with precision, and writes numeric_per_query.jsonl + numeric_metrics.json.[EVIDENCE] scripts/eval_numeric.py:151-234
