from training.mining import build_bm25, mine_bm25, select_hard_negs


def test_hard_negative_mining_excludes_positive():
    corpus = [
        {"text": "alpha beta", "meta": {"chunk_id": "c1"}},
        {"text": "gamma delta", "meta": {"chunk_id": "c2"}},
        {"text": "epsilon zeta", "meta": {"chunk_id": "c3"}},
    ]
    bm25 = build_bm25(corpus)
    candidates = mine_bm25("alpha", bm25, corpus, top_n=3)
    negs = select_hard_negs(candidates, corpus, pos_chunk_id="c1", hard_k=2)
    assert all(n["chunk_id"] != "c1" for n in negs)
    assert len(negs) <= 2
