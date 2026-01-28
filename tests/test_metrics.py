from finder_rag.metrics import exact_match, mrr, recall_at_k, reciprocal_rank


def test_exact_match_case_insensitive():
    assert exact_match("Hello  World", "hello world") == 1.0


def test_recall_at_k_simple():
    retrieved = ["a", "b", "c"]
    relevant = ["b", "x"]
    assert recall_at_k(retrieved, relevant, k=2) == 0.5


def test_reciprocal_rank():
    assert reciprocal_rank([False, True, False]) == 0.5
    assert reciprocal_rank([False, False]) == 0.0


def test_mrr():
    scores = [[False, True], [True, False], [False, False]]
    assert mrr(scores) == (0.5 + 1.0 + 0.0) / 3.0
