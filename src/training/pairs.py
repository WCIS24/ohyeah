from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Tuple

from retrieval.eval_utils import normalize_text


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def build_corpus_index(corpus_chunks: List[Dict[str, Any]]) -> Dict[str, Dict[int, List[Dict[str, Any]]]]:
    index: Dict[str, Dict[int, List[Dict[str, Any]]]] = {}
    for chunk in corpus_chunks:
        meta = chunk.get("meta", {})
        qid = meta.get("source_qid")
        evidence_id = meta.get("evidence_id")
        if qid is None or evidence_id is None:
            continue
        index.setdefault(qid, {}).setdefault(int(evidence_id), []).append(chunk)
    return index


def find_positive_chunk(
    record: Dict[str, Any],
    corpus_index: Dict[str, Dict[int, List[Dict[str, Any]]]],
) -> Tuple[Optional[Dict[str, Any]], str]:
    qid = record.get("qid")
    evidences = record.get("evidences", [])
    if not evidences:
        return None, "missing_evidence"

    for ev in evidences:
        ev_id = ev.get("meta", {}).get("evidence_id")
        if qid in corpus_index and ev_id in corpus_index[qid]:
            return corpus_index[qid][ev_id][0], "id"

    # Fallback: match by text within same qid
    qid_chunks = []
    if qid in corpus_index:
        for chunks in corpus_index[qid].values():
            qid_chunks.extend(chunks)
    ev_texts = [normalize_text(ev.get("text", "")) for ev in evidences]

    for chunk in qid_chunks:
        chunk_text = normalize_text(chunk.get("text", ""))
        for ev_text in ev_texts:
            if not ev_text:
                continue
            if chunk_text in ev_text or ev_text in chunk_text:
                return chunk, "text"

    return None, "not_found"


def build_training_pairs(
    records: Iterable[Dict[str, Any]],
    corpus_index: Dict[str, Dict[int, List[Dict[str, Any]]]],
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    pairs = []
    stats = {"total": 0, "pos_found": 0, "pos_text_fallback": 0, "pos_missing": 0}

    for record in records:
        stats["total"] += 1
        pos_chunk, mode = find_positive_chunk(record, corpus_index)
        if pos_chunk is None:
            stats["pos_missing"] += 1
            continue
        if mode == "text":
            stats["pos_text_fallback"] += 1
        stats["pos_found"] += 1

        pairs.append(
            {
                "qid": record.get("qid"),
                "query": record.get("query"),
                "pos_chunk_id": pos_chunk.get("meta", {}).get("chunk_id"),
                "pos_text": pos_chunk.get("text"),
            }
        )

    return pairs, stats
