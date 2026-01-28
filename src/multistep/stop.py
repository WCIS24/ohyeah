from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set


def jaccard(a: str, b: str) -> float:
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


@dataclass
class StopState:
    no_new_steps: int = 0


@dataclass
class StopResult:
    should_stop: bool
    reason: str


class StopCriteria:
    def __init__(self, max_steps: int, no_new_steps_limit: int, novelty_threshold: float) -> None:
        self.max_steps = max_steps
        self.no_new_steps_limit = no_new_steps_limit
        self.novelty_threshold = novelty_threshold

    def check(
        self,
        step_idx: int,
        new_chunk_ids: List[str],
        gap_type: str,
        empty_results: bool,
        state: StopState,
    ) -> StopResult:
        if empty_results:
            return StopResult(True, "EMPTY_RESULTS")
        if gap_type == "NO_GAP":
            return StopResult(True, "NO_GAP")
        if step_idx + 1 >= self.max_steps:
            return StopResult(True, "MAX_STEPS")
        if not new_chunk_ids:
            state.no_new_steps += 1
        else:
            state.no_new_steps = 0
        if state.no_new_steps >= self.no_new_steps_limit:
            return StopResult(True, "NO_NEW_EVIDENCE")
        return StopResult(False, "CONTINUE")

    def novelty_filter(self, new_chunks: List[dict], existing_chunks: List[dict]) -> List[dict]:
        if self.novelty_threshold <= 0:
            return new_chunks
        filtered = []
        for ch in new_chunks:
            text = ch.get("text", "")
            if not text:
                filtered.append(ch)
                continue
            if all(jaccard(text, ex.get("text", "")) < self.novelty_threshold for ex in existing_chunks):
                filtered.append(ch)
        return filtered
