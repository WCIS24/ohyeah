from training.pairs import build_training_pairs, build_corpus_index


def test_training_pairs_pos_present():
    corpus = [
        {"text": "evidence one", "meta": {"source_qid": "q1", "evidence_id": 0, "chunk_id": "c1"}},
        {"text": "other", "meta": {"source_qid": "q2", "evidence_id": 0, "chunk_id": "c2"}},
    ]
    records = [
        {
            "qid": "q1",
            "query": "what?",
            "evidences": [{"text": "evidence one", "meta": {"evidence_id": 0}}],
        }
    ]
    corpus_index = build_corpus_index(corpus)
    pairs, stats = build_training_pairs(records, corpus_index)
    assert stats["pos_found"] == 1
    assert pairs[0]["pos_chunk_id"] == "c1"
    assert pairs[0]["pos_text"]
