from __future__ import annotations

from typing import Dict, List


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be < chunk_size")

    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        if end == text_len:
            break
        start = end - overlap
    return chunks


def chunk_evidence(
    evidence_text: str,
    meta: Dict[str, str],
    chunk_size: int,
    overlap: int,
) -> List[Dict[str, str]]:
    chunks = chunk_text(evidence_text, chunk_size, overlap)
    output = []
    for idx, chunk in enumerate(chunks):
        chunk_meta = dict(meta)
        chunk_meta["chunk_id"] = f"{meta.get('evidence_id', 'e')}_c{idx}"
        output.append({"text": chunk, "meta": chunk_meta})
    return output
