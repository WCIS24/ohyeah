from data.finder import normalize_sample


def test_normalize_sample_fields_present():
    sample = {
        "_id": "x1",
        "text": "What is revenue?",
        "answer": "42",
        "references": ["evidence text"],
        "category": "test",
    }
    field_map = {
        "qid": "_id",
        "query": "text",
        "answer": "answer",
        "evidences": "references",
        "doc_id": None,
    }
    record = normalize_sample(sample, field_map, 0)
    assert record["qid"] == "x1"
    assert record["query"]
    assert record["answer"]
    assert record["evidences"]
    assert record["evidences"][0]["text"]
