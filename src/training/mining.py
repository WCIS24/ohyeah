from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> List[str]:
    return text.lower().split()


def build_bm25(corpus_chunks: List[Dict[str, Any]]) -> BM25Okapi:
    return BM25Okapi([tokenize(c["text"]) for c in corpus_chunks])


def mine_bm25(
    query: str,
    bm25: BM25Okapi,
    corpus_chunks: List[Dict[str, Any]],
    top_n: int,
) -> List[Tuple[int, float]]:
    scores = bm25.get_scores(tokenize(query))
    idx_sorted = np.argsort(scores)[::-1][:top_n]
    return [(int(idx), float(scores[idx])) for idx in idx_sorted]


def select_hard_negs(
    candidates: List[Tuple[int, float]],
    corpus_chunks: List[Dict[str, Any]],
    pos_chunk_id: str,
    hard_k: int,
) -> List[Dict[str, Any]]:
    negs = []
    for idx, score in candidates:
        chunk = corpus_chunks[idx]
        if chunk.get("meta", {}).get("chunk_id") == pos_chunk_id:
            continue
        negs.append(
            {
                "chunk_id": chunk.get("meta", {}).get("chunk_id"),
                "text": chunk.get("text"),
                "score": score,
            }
        )
        if len(negs) >= hard_k:
            break
    return negs
