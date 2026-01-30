from __future__ import annotations

from typing import List

from multistep.engine import MultiStepConfig, MultiStepRetriever


class FakeRetriever:
    def retrieve(self, query: str, top_k: int, alpha: float, mode: str) -> List[dict]:
        return [
            {"meta": {"chunk_id": f"c{i}"}, "score": float(top_k - i), "text": f"text {i}"}
            for i in range(top_k)
        ]


def test_final_topk_fallback_fills() -> None:
    retriever = FakeRetriever()
    config = MultiStepConfig(
        max_steps=1,
        top_k_each_step=5,
        final_top_k=10,
        alpha=0.5,
        mode="dense",
        novelty_threshold=0.0,
        stop_no_new_steps=1,
    )
    engine = MultiStepRetriever(retriever, config)
    _, trace, _, final_topk = engine.run("query")
    assert len(final_topk) == 10
    assert any(c.get("chunk_id") == "c7" for c in final_topk)
    assert trace[-1].get("final_fallback_added", 0) >= 1


def test_final_topk_no_fallback_when_sufficient() -> None:
    retriever = FakeRetriever()
    config = MultiStepConfig(
        max_steps=1,
        top_k_each_step=5,
        final_top_k=5,
        alpha=0.5,
        mode="dense",
        novelty_threshold=0.0,
        stop_no_new_steps=1,
    )
    engine = MultiStepRetriever(retriever, config)
    _, trace, _, final_topk = engine.run("query")
    assert len(final_topk) == 5
    assert trace[-1].get("final_fallback_added", 0) == 0
