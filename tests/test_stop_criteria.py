from multistep.stop import StopCriteria, StopState


def test_stop_max_steps():
    stop = StopCriteria(max_steps=2, no_new_steps_limit=2, novelty_threshold=0.3)
    state = StopState()
    result = stop.check(step_idx=1, new_chunk_ids=["c1"], gap_type="OTHER", empty_results=False, state=state)
    assert result.should_stop is True
    assert result.reason == "MAX_STEPS"


def test_stop_no_new_evidence():
    stop = StopCriteria(max_steps=5, no_new_steps_limit=2, novelty_threshold=0.3)
    state = StopState()
    result1 = stop.check(step_idx=0, new_chunk_ids=[], gap_type="OTHER", empty_results=False, state=state)
    assert result1.should_stop is False
    result2 = stop.check(step_idx=1, new_chunk_ids=[], gap_type="OTHER", empty_results=False, state=state)
    assert result2.should_stop is True
    assert result2.reason == "NO_NEW_EVIDENCE"


def test_stop_no_gap():
    stop = StopCriteria(max_steps=5, no_new_steps_limit=2, novelty_threshold=0.3)
    state = StopState()
    result = stop.check(step_idx=0, new_chunk_ids=["c1"], gap_type="NO_GAP", empty_results=False, state=state)
    assert result.should_stop is True
    assert result.reason == "NO_GAP"
