from calculator.compute import compute_for_query
from calculator.extract import Fact


def test_yoy_compute() -> None:
    facts = [
        Fact(
            qid="q1",
            chunk_id="c1",
            metric="revenue",
            entity="ABC",
            year=2020,
            period=None,
            value=100.0,
            unit="USD",
            raw_span="",
            confidence=0.9,
        ),
        Fact(
            qid="q1",
            chunk_id="c2",
            metric="revenue",
            entity="ABC",
            year=2021,
            period=None,
            value=200.0,
            unit="USD",
            raw_span="",
            confidence=0.9,
        ),
    ]
    result, _ = compute_for_query("yoy 2020 2021", facts, output_percent=True)
    assert result.status == "ok"
    assert abs(result.result_value - 100.0) < 1e-6
