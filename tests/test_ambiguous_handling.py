from calculator.compute import compute_for_query
from calculator.extract import Fact


def test_ambiguous_handling() -> None:
    facts = [
        Fact(
            qid="q1",
            chunk_id="c1",
            metric="profit",
            entity="ABC",
            year=None,
            period=None,
            value=10.0,
            unit="USD",
            raw_span="",
            confidence=0.5,
        ),
        Fact(
            qid="q1",
            chunk_id="c2",
            metric="profit",
            entity="ABC",
            year=None,
            period=None,
            value=11.0,
            unit="USD",
            raw_span="",
            confidence=0.6,
        ),
        Fact(
            qid="q1",
            chunk_id="c3",
            metric="profit",
            entity="ABC",
            year=None,
            period=None,
            value=12.0,
            unit="USD",
            raw_span="",
            confidence=0.4,
        ),
    ]
    result, _ = compute_for_query("difference", facts, output_percent=True)
    assert result.status == "ambiguous"
