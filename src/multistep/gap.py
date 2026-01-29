from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

COMPARE_SPLIT_RE = re.compile(r"\bvs\b|\bversus\b|\bcompare\b|\bthan\b", re.IGNORECASE)


@dataclass
class GapResult:
    gap_type: str
    missing_years: List[str]
    missing_entity: Optional[str]
    gap_conf: float


def extract_years(text: str) -> List[str]:
    return list({m.group(0) for m in YEAR_RE.finditer(text)})


def extract_entities_from_query(query: str) -> List[str]:
    # Extract quoted phrases or uppercase abbreviations
    entities = []
    for match in re.findall(r"\"([^\"]{2,})\"|'([^']{2,})'", query):
        phrase = next((m for m in match if m), None)
        if phrase:
            entities.append(phrase)

    for match in re.findall(r"\b[A-Z]{2,6}\b", query):
        entities.append(match)

    # Split around compare keywords to guess two sides
    parts = COMPARE_SPLIT_RE.split(query)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) >= 2:
        entities.extend(parts[:2])

    # Deduplicate preserving order
    seen = set()
    ordered = []
    for e in entities:
        if e not in seen:
            seen.add(e)
            ordered.append(e)
    return ordered


def detect_gap(query: str, chunks: List[dict], query_type: str) -> GapResult:
    query_years = extract_years(query)
    chunk_years = set()
    for ch in chunks:
        chunk_years.update(extract_years(ch.get("text", "")))

    missing_years = [y for y in query_years if y not in chunk_years]
    if len(query_years) >= 2 and missing_years:
        gap_conf = len(missing_years) / len(query_years) if query_years else 0.0
        return GapResult(
            gap_type="MISSING_YEAR",
            missing_years=missing_years,
            missing_entity=None,
            gap_conf=gap_conf,
        )

    if query_type == "COMPARE":
        entities = extract_entities_from_query(query)
        if len(entities) >= 2:
            found = []
            for e in entities[:2]:
                if any(e.lower() in (ch.get("text", "").lower()) for ch in chunks):
                    found.append(e)
            if len(found) == 1:
                missing_entity = entities[1] if entities[0] in found else entities[0]
                return GapResult(
                    gap_type="MISSING_ENTITY",
                    missing_years=[],
                    missing_entity=missing_entity,
                    gap_conf=1.0,
                )

    return GapResult(gap_type="NO_GAP", missing_years=[], missing_entity=None, gap_conf=0.0)
