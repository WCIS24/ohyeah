# METRICS

Retrieval metrics (scripts/eval_retrieval.py):

- Recall@k
  - Definition: for each query, number of unique gold evidences retrieved in top-k / total gold evidences.
  - Aggregation: average across queries.
- Evidence Hit@k
  - Definition: fraction of queries with at least one matching evidence in top-k.
- MRR@k
  - Definition: reciprocal rank of the first matching evidence in top-k; 0 if none. Averaged across queries.

Matching rule:
1) Primary: match by `(source_qid, evidence_id)` (and `doc_id` if available).
2) Fallback: text match (normalized, whitespace-collapsed) where chunk text is a substring of gold evidence text or vice versa.
3) `uncertain_match_ratio` reports the fraction of queries that required fallback matching.

QA metrics (scripts/eval_qa.py):

- Exact Match (EM): case-insensitive exact string match after whitespace normalization.
- Token F1: token-level precision/recall F1 using whitespace tokenization.
- Missing rate: fraction of gold rows without valid predictions or gold answers.

Hybrid score normalization:
- `bm25` and `dense` scores are independently min-max normalized per query.
- Hybrid score: `alpha * bm25_norm + (1 - alpha) * dense_norm`.
