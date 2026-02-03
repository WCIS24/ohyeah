# Multi-step Retrieval Design

Purpose:
- Make the multistep retrieval rules reproducible and traceable to code for the method chapter.

How to use:
- Cite this document for internal logic (planner/gap/stop/refiner/merge) and point to the code paths listed in [EVIDENCE].

## Config surface (runtime controls)
- max_steps / top_k_each_step / top_k_final / novelty_threshold / stop_no_new_steps are the core knobs for multistep retrieval.[EVIDENCE] configs/run_multistep.yaml:1-21
- These config values are read and injected into MultiStepConfig when running `scripts/run_multistep_retrieval.py`.[EVIDENCE] scripts/run_multistep_retrieval.py:127-148

## StepPlanner (query intent classification)
- StepPlanner inspects the query for compare keywords, years, and percentages to assign a query_type (COMPARE / TREND / FACT / OTHER).[EVIDENCE] src/multistep/planner.py:7-40
- The query_type is used downstream by gap detection to decide whether to continue retrieval.[EVIDENCE] src/multistep/engine.py:51-106; src/multistep/gap.py:51-84

## Gap detection (missing evidence signals)
- detect_gap checks missing years for multi-year queries and missing entities for COMPARE queries, returning a GapResult with gap_type and confidence.[EVIDENCE] src/multistep/gap.py:7-84
- GapResult is consumed by the gate and stop logic to decide whether to continue.[EVIDENCE] src/multistep/engine.py:103-131

## Stop criteria and novelty filter
- StopCriteria stops on EMPTY_RESULTS, NO_GAP, MAX_STEPS, or NO_NEW_EVIDENCE; it tracks consecutive steps without new evidence.[EVIDENCE] src/multistep/stop.py:26-53
- novelty_filter removes near-duplicate chunks using Jaccard similarity over text and the novelty_threshold.[EVIDENCE] src/multistep/stop.py:7-66

## Query refinement
- refine_query appends missing years/entities to the query, and can append metric synonyms for MISSING_METRIC cases.[EVIDENCE] src/multistep/refiner.py:6-34

## Candidate collection, merge, and fallback
- MultiStepRetriever collects new chunks per step, updates a collected-by-id pool, and appends trace entries for each step.[EVIDENCE] src/multistep/engine.py:40-147
- After stopping, results are merged and ranked; if final_topk is smaller than final_top_k, the retriever falls back to a baseline retrieval to fill the pool.[EVIDENCE] src/multistep/engine.py:167-191; src/multistep/engine.py:199-209

## Output artifacts and fields
- multistep_traces.jsonl records per-step query, gap, gate decision, and stop reasons; retrieval_results.jsonl contains final_top_chunks and all_collected_chunks.[EVIDENCE] scripts/run_multistep_retrieval.py:166-213
