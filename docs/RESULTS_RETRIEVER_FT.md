# RESULTS RETRIEVER FT

Pre-run (pre_ft): outputs/20260128_172909_b323af
Post-run (post_ft): outputs/20260128_175456_4e0caf

## Metrics (dev)

| metric | pre | post | delta |
| --- | --- | --- | --- |
| recall@1 | 0.156140 | 0.208772 | +0.052632 |
| recall@5 | 0.259649 | 0.331579 | +0.071930 |
| recall@10 | 0.324561 | 0.377193 | +0.052632 |
| mrr@1 | 0.156140 | 0.208772 | +0.052632 |
| mrr@5 | 0.194327 | 0.253977 | +0.059649 |
| mrr@10 | 0.202958 | 0.260061 | +0.057102 |

Delta source: outputs/20260128_175456_4e0caf/delta_vs_pre.json

## Error analysis

See outputs/20260128_175456_4e0caf/error_analysis_top20.jsonl for the top 20 improved
and top 20 declined queries with their pre/post top-k retrievals.
