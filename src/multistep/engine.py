from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from multistep.gap import detect_gap
from multistep.planner import StepPlanner
from multistep.refiner import refine_query
from multistep.stop import StopCriteria, StopState


@dataclass
class MultiStepConfig:
    max_steps: int
    top_k_each_step: int
    final_top_k: int
    alpha: float
    mode: str
    novelty_threshold: float
    stop_no_new_steps: int
    merge_strategy: str = "maxscore"
    gate_enabled: bool = True
    gate_min_gap_conf: float = 0.3
    gate_allow_types: List[str] = None
    gap_enabled: bool = True
    refiner_enabled: bool = True


class MultiStepRetriever:
    def __init__(self, retriever, config: MultiStepConfig) -> None:
        self.retriever = retriever
        self.config = config
        self.planner = StepPlanner()
        self.stopper = StopCriteria(
            max_steps=config.max_steps,
            no_new_steps_limit=config.stop_no_new_steps,
            novelty_threshold=config.novelty_threshold,
        )

    def run(self, query: str) -> Tuple[List[dict], List[dict], str, List[dict]]:
        collected: List[dict] = []
        collected_by_id: Dict[str, dict] = {}
        step1_ids: List[str] = []
        trace: List[dict] = []
        state = StopState()
        used_query = query
        stop_reason = "MAX_STEPS"
        gate_allow = self.config.gate_allow_types or ["YEAR", "COMPARE"]

        for step_idx in range(self.config.max_steps):
            plan = self.planner.plan(query)
            results = self.retriever.retrieve(
                used_query,
                top_k=self.config.top_k_each_step,
                alpha=self.config.alpha,
                mode=self.config.mode,
            )
            topk_chunks = []
            for res in results:
                topk_chunks.append(
                    {
                        "chunk_id": res.get("meta", {}).get("chunk_id"),
                        "score": res.get("score"),
                        "meta": res.get("meta"),
                        "text": res.get("text"),
                    }
                )

            empty_results = len(results) == 0

            new_candidates = []
            existing_ids = {c.get("meta", {}).get("chunk_id") for c in collected}
            for res in results:
                chunk_id = res.get("meta", {}).get("chunk_id")
                if chunk_id in existing_ids:
                    continue
                new_candidates.append(
                    {
                        "chunk_id": chunk_id,
                        "text": res.get("text"),
                        "score": res.get("score"),
                        "meta": res.get("meta"),
                    }
                )

            new_candidates = self.stopper.novelty_filter(new_candidates, collected)
            collected.extend(new_candidates)
            for res in results:
                chunk_id = res.get("meta", {}).get("chunk_id")
                if not chunk_id:
                    continue
                prev = collected_by_id.get(chunk_id)
                if not prev or res.get("score", 0.0) > prev.get("score", -1.0):
                    collected_by_id[chunk_id] = {
                        "chunk_id": chunk_id,
                        "score": res.get("score"),
                        "meta": res.get("meta"),
                        "text": res.get("text"),
                    }
            if step_idx == 0:
                step1_ids = [c.get("chunk_id") for c in topk_chunks if c.get("chunk_id")]

            if self.config.gap_enabled:
                gap = detect_gap(query, collected, plan.query_type)
            else:
                gap = detect_gap(query, collected, "OTHER")
                gap = gap.__class__(
                    gap_type="NO_GAP",
                    missing_years=[],
                    missing_entity=None,
                    gap_conf=0.0,
                )

            gate_decision = True
            if self.config.gate_enabled:
                gap_tag = gap.gap_type
                if gap_tag == "MISSING_YEAR":
                    gap_tag = "YEAR"
                elif gap_tag == "MISSING_ENTITY":
                    gap_tag = "COMPARE"
                gate_decision = (
                    gap.gap_conf >= self.config.gate_min_gap_conf and gap_tag in gate_allow
                )

            stop = self.stopper.check(
                step_idx=step_idx,
                new_chunk_ids=[c.get("chunk_id") for c in new_candidates],
                gap_type=gap.gap_type,
                empty_results=empty_results,
                state=state,
            )

            trace.append(
                {
                    "step_idx": step_idx,
                    "used_query": used_query,
                    "topk_chunks": [
                        {"chunk_id": c["chunk_id"], "score": c["score"]} for c in topk_chunks
                    ],
                    "newly_added_chunk_ids": [c.get("chunk_id") for c in new_candidates],
                    "gap": gap.gap_type,
                    "gap_conf": gap.gap_conf,
                    "gate_decision": gate_decision,
                    "stop_reason": stop.reason,
                }
            )

            if not gate_decision:
                stop_reason = "GATE_BLOCKED"
                break

            if stop.should_stop:
                stop_reason = stop.reason
                break

            if self.config.refiner_enabled:
                refinement = refine_query(
                    query,
                    gap.gap_type,
                    gap.missing_years,
                    gap.missing_entity,
                )
                used_query = refinement.refined_query
            else:
                used_query = query

        final_topk = self._merge_and_rank(collected_by_id, step1_ids)
        fallback_added = 0
        if len(final_topk) < self.config.final_top_k:
            baseline_results = self.retriever.retrieve(
                query,
                top_k=self.config.final_top_k,
                alpha=self.config.alpha,
                mode=self.config.mode,
            )
            for res in baseline_results:
                chunk_id = res.get("meta", {}).get("chunk_id")
                if not chunk_id or chunk_id in collected_by_id:
                    continue
                entry = {
                    "chunk_id": chunk_id,
                    "score": res.get("score"),
                    "meta": res.get("meta"),
                    "text": res.get("text"),
                }
                collected_by_id[chunk_id] = entry
                collected.append(entry)
                fallback_added += 1
                if len(collected_by_id) >= self.config.final_top_k:
                    break
            final_topk = self._merge_and_rank(collected_by_id, step1_ids)

        if trace:
            trace[-1]["final_pool_size"] = len(collected_by_id)
            trace[-1]["final_topk_size"] = len(final_topk)
            trace[-1]["final_fallback_added"] = fallback_added
        return collected, trace, stop_reason, final_topk

    def _merge_and_rank(self, collected_by_id: Dict[str, dict], step1_ids: List[str]) -> List[dict]:
        all_chunks = list(collected_by_id.values())
        if self.config.merge_strategy == "step1_first":
            step1_chunks = [c for c in all_chunks if c.get("chunk_id") in step1_ids]
            step1_chunks.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            rest = [c for c in all_chunks if c.get("chunk_id") not in step1_ids]
            rest.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            ordered = step1_chunks + rest
        else:
            ordered = sorted(all_chunks, key=lambda x: x.get("score", 0.0), reverse=True)
        return ordered[: self.config.final_top_k]
