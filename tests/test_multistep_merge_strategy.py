from multistep.engine import MultiStepConfig, MultiStepRetriever


class DummyRetriever:
    def retrieve(self, query: str, top_k: int, alpha: float, mode: str):
        return []


def test_multistep_merge_strategy() -> None:
    base = {
        "max_steps": 2,
        "top_k_each_step": 2,
        "final_top_k": 3,
        "alpha": 0.5,
        "mode": "dense",
        "novelty_threshold": 0.0,
        "stop_no_new_steps": 1,
        "merge_strategy": "maxscore",
        "gate_enabled": False,
        "gate_min_gap_conf": 0.0,
        "gate_allow_types": [],
    }
    cfg = MultiStepConfig(**base)
    engine = MultiStepRetriever(DummyRetriever(), cfg)
    collected = {
        "a": {"chunk_id": "a", "score": 0.9},
        "b": {"chunk_id": "b", "score": 0.8},
        "c": {"chunk_id": "c", "score": 0.95},
    }
    step1_ids = ["a", "b"]

    cfg.merge_strategy = "maxscore"
    ranked = engine._merge_and_rank(collected, step1_ids)
    assert [r["chunk_id"] for r in ranked] == ["c", "a", "b"]

    cfg.merge_strategy = "step1_first"
    ranked = engine._merge_and_rank(collected, step1_ids)
    assert [r["chunk_id"] for r in ranked] == ["a", "b", "c"]
