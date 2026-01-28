from finder_rag.metrics import exact_match, recall_at_k


def test_exact_match_case_insensitive():
    assert exact_match("Hello  World", "hello world") == 1.0


def test_recall_at_k_simple():
    retrieved = ["a", "b", "c"]
    relevant = ["b", "x"]
    assert recall_at_k(retrieved, relevant, k=2) == 0.5
