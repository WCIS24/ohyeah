# RESULTS MULTISTEP

## Runs
- baseline (pre_multistep): outputs/20260128_192907_7a5655
- multistep (full dev):
  - run_multistep: outputs/20260128_194024_dab941
  - eval_multistep: outputs/20260128_194522_9b8e83
  - traces: outputs/20260128_194024_dab941/multistep_traces.jsonl
- complex subset eval: outputs/20260128_195020_57287e
 - fixed eval (top_k_final=10): outputs/20260130_122935_424646 (run) + outputs/20260130_123904_e49881 (eval)

## Baseline vs Multistep (full dev)

| metric | baseline | multistep | delta |
| --- | --- | --- | --- |
| recall@1 | 0.156140 | 0.156140 | 0.000000 |
| recall@5 | 0.259649 | 0.259649 | 0.000000 |
| recall@10 | 0.324561 | 0.259649 | -0.064912 |
| mrr@1 | 0.156140 | 0.156140 | 0.000000 |
| mrr@5 | 0.194327 | 0.194094 | -0.000234 |
| mrr@10 | 0.202958 | 0.194094 | -0.008864 |

Delta source: outputs/20260128_194522_9b8e83/delta_vs_baseline.json

## Complex subset (dev_complex_qids.txt)

Subset path: data/subsets/dev_complex_qids.txt

| metric | multistep (complex) |
| --- | --- |
| recall@5 | 0.279835 |
| recall@10 | 0.279835 |
| mrr@10 | 0.223800 |

## Ablations (full dev)

| ablation | eval run_id | recall@5 | recall@10 | mrr@10 |
| --- | --- | --- | --- | --- |
| T=1 (single step) | outputs/20260128_195759_65c4d1 | 0.259649 | 0.259649 | 0.194327 |
| gap detector off | outputs/20260128_200700_2e6ead | 0.259649 | 0.259649 | 0.194327 |
| novelty_threshold=0 | outputs/20260128_201703_d0b18b | 0.259649 | 0.259649 | 0.194094 |

## Notes
- Complex subset built by scripts/build_subsets.py; stats in outputs/<run_id>/subsets_stats.json.
- Matching rule identical to Step2 (doc_id/evidence_id first, fallback text containment).
- traces provide step-level evidence for paper case studies.
- `top_k_each_step` is per-step retrieval size, while `top_k_final` is the final candidate pool used for eval.
- Ensure `top_k_final >= max(k_values)` to avoid Recall@10 being truncated by output length.
