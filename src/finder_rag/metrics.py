from __future__ import annotations

import re
from typing import Iterable, List


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def exact_match(pred: str, gold: str) -> float:
    return 1.0 if normalize_text(pred) == normalize_text(gold) else 0.0


def recall_at_k(retrieved: Iterable[str], relevant: Iterable[str], k: int) -> float:
    retrieved_k = list(retrieved)[:k]
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    hit = len(set(retrieved_k) & relevant_set)
    return hit / float(len(relevant_set))


def mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))
