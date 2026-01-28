from __future__ import annotations

import ast
from typing import Dict, List

import pandas as pd

REQUIRED_COLUMNS = ["text", "references", "answer"]


def load_finder_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def parse_references(refs: str) -> List[str]:
    if refs is None or (isinstance(refs, float) and pd.isna(refs)):
        return []
    try:
        items = ast.literal_eval(refs)
    except (SyntaxError, ValueError):
        return []
    if not isinstance(items, list):
        return []
    return [str(x) for x in items if isinstance(x, str) and x.strip()]


def build_records(df: pd.DataFrame, max_evidence_per_query: int) -> List[Dict[str, str]]:
    records = []
    for _, row in df.iterrows():
        evidence = parse_references(row.get("references"))
        if max_evidence_per_query > 0:
            evidence = evidence[:max_evidence_per_query]
        if not evidence:
            continue
        records.append(
            {
                "query": str(row.get("text", "")),
                "answer": str(row.get("answer", "")),
                "evidence": evidence,
            }
        )
    return records


def build_corpus(records: List[Dict[str, str]]) -> List[str]:
    seen = set()
    corpus = []
    for rec in records:
        for ev in rec["evidence"]:
            if ev not in seen:
                seen.add(ev)
                corpus.append(ev)
    return corpus
