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
    alpha: float
    mode: str
    novelty_threshold: float
    stop_no_new_steps: int
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

    def run(self, query: str) -> Tuple[List[dict], List[dict], str]:
        collected: List[dict] = []
        trace: List[dict] = []
        state = StopState()
        used_query = query
        stop_reason = "MAX_STEPS"

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

            if self.config.gap_enabled:
                gap = detect_gap(query, collected, plan.query_type)
            else:
                gap = detect_gap(query, collected, "OTHER")
                gap = gap.__class__(gap_type="NO_GAP", missing_years=[], missing_entity=None)

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
                    "stop_reason": stop.reason,
                }
            )

            if stop.should_stop:
                stop_reason = stop.reason
                break

            if self.config.refiner_enabled:
                refinement = refine_query(query, gap.gap_type, gap.missing_years, gap.missing_entity)
                used_query = refinement.refined_query
            else:
                used_query = query

        return collected, trace, stop_reason
