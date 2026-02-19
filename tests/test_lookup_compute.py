from calculator.compute import compute_for_query
from calculator.extract import Fact


def build_fact(year: int, value: float) -> Fact:
    return Fact(
        qid="q1",
        chunk_id="c1",
        metric="revenue",
        entity="ABC",
        year=year,
        period=None,
        value=value,
        unit="USD",
        raw_span="revenue",
        confidence=0.95,
    )


def test_lookup_enabled_returns_single_fact_result() -> None:
    facts = [build_fact(2023, 123.4)]
    result, _trace = compute_for_query(
        "What is revenue in 2023?",
        facts,
        output_percent=True,
        enable_lookup=True,
    )
    assert result.status == "ok"
    assert result.task_type == "lookup"
    assert result.result_value == 123.4
    assert result.result_unit == "USD"


def test_lookup_disabled_keeps_legacy_no_match() -> None:
    facts = [build_fact(2023, 123.4)]
    result, _trace = compute_for_query(
        "What is revenue in 2023?",
        facts,
        output_percent=True,
        enable_lookup=False,
    )
    assert result.status == "no_match"
    assert result.task_type == "unknown"
