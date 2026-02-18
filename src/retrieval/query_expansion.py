from __future__ import annotations

import json
import logging
import os
import re
from collections import Counter
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

ABBREV_RE = re.compile(r"\b[A-Z]{2,6}\b")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _unique_keep_order(items: Sequence[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _clean_text(text: str) -> str:
    return " ".join(str(text).split())


def _coerce_terms(value: Any) -> List[str]:
    if isinstance(value, str):
        return [_clean_text(value)] if value.strip() else []
    if isinstance(value, Sequence):
        terms = [_clean_text(str(v)) for v in value if str(v).strip()]
        return _unique_keep_order(terms)
    return []


class QueryExpander:
    """Generate deterministic query variants for single-step retrieval."""

    def __init__(
        self,
        enabled: bool = True,
        max_queries: int = 3,
        abbrev_enabled: bool = True,
        prf_year_enabled: bool = True,
        seed_top_k: int = 5,
        abbrev_dict_path: Optional[str] = None,
        abbrev_map: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.enabled = bool(enabled)
        self.max_queries = max(1, int(max_queries))
        self.abbrev_enabled = bool(abbrev_enabled)
        self.prf_year_enabled = bool(prf_year_enabled)
        self.seed_top_k = max(1, int(seed_top_k))

        loaded_map: Dict[str, List[str]] = {}
        if abbrev_dict_path:
            loaded_map = self._load_abbrev_map(abbrev_dict_path)
        if abbrev_map:
            for key, val in abbrev_map.items():
                terms = _coerce_terms(val)
                if terms:
                    loaded_map[str(key).upper()] = terms
        self.abbrev_map = loaded_map
        self._last_trace: Dict[str, Any] = {}

    @staticmethod
    def extract_abbrevs(query: str) -> List[str]:
        return _unique_keep_order([m.group(0) for m in ABBREV_RE.finditer(query or "")])

    @staticmethod
    def extract_years(text: str) -> List[str]:
        return _unique_keep_order([m.group(0) for m in YEAR_RE.finditer(text or "")])

    def expand(self, query: str, seed_chunks: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        query = _clean_text(query)
        seed_chunks = seed_chunks or []
        if not self.enabled:
            self._last_trace = {
                "enabled": False,
                "expanded": False,
                "num_queries": 1,
                "abbrev_added": False,
                "prf_year_added": False,
                "abbrevs": [],
                "years_added": [],
            }
            return [query]

        queries = [query]
        abbrevs = self.extract_abbrevs(query)
        abbrev_added = False
        prf_year_added = False
        years_added: List[str] = []

        if self.abbrev_enabled and len(queries) < self.max_queries:
            expanded_query, abbrev_added = self._abbrev_query(query, abbrevs, seed_chunks)
            if expanded_query and expanded_query != query:
                queries.append(expanded_query)

        if self.prf_year_enabled and len(queries) < self.max_queries:
            expanded_query, years_added = self._prf_year_query(query, seed_chunks)
            if expanded_query and expanded_query != query:
                prf_year_added = True
                queries.append(expanded_query)

        queries = _unique_keep_order(queries)[: self.max_queries]
        self._last_trace = {
            "enabled": True,
            "expanded": len(queries) > 1,
            "num_queries": len(queries),
            "abbrev_added": abbrev_added,
            "prf_year_added": prf_year_added,
            "abbrevs": abbrevs,
            "years_added": years_added,
        }
        return queries

    def get_last_trace(self) -> Dict[str, Any]:
        return dict(self._last_trace)

    def _abbrev_query(
        self,
        query: str,
        abbrevs: List[str],
        seed_chunks: List[Dict[str, Any]],
    ) -> Tuple[Optional[str], bool]:
        if not abbrevs:
            return None, False

        terms: List[str] = []
        for abbrev in abbrevs:
            mapped = self.abbrev_map.get(abbrev, [])
            if mapped:
                terms.extend(mapped[:1])
                continue
            seed_candidate = self._infer_abbrev_from_seed(abbrev, seed_chunks)
            if seed_candidate:
                terms.append(seed_candidate)

        terms = _unique_keep_order([t for t in terms if t])
        if not terms:
            return None, False
        return _clean_text(f"{query} {' '.join(terms)}"), True

    def _prf_year_query(
        self,
        query: str,
        seed_chunks: List[Dict[str, Any]],
    ) -> Tuple[Optional[str], List[str]]:
        if not seed_chunks:
            return None, []

        year_counts: Counter[str] = Counter()
        for chunk in seed_chunks[: self.seed_top_k]:
            text = chunk.get("text", "") if isinstance(chunk, dict) else ""
            for year in self.extract_years(str(text)):
                year_counts[year] += 1

        if not year_counts:
            return None, []

        query_years = set(self.extract_years(query))
        ranked = sorted(year_counts.items(), key=lambda x: (-x[1], -int(x[0]), x[0]))
        years = [year for year, _ in ranked if year not in query_years][:2]
        if not years:
            return None, []

        return _clean_text(f"{query} {' '.join(years)}"), years

    def _infer_abbrev_from_seed(self, abbrev: str, seed_chunks: List[Dict[str, Any]]) -> Optional[str]:
        counts: Counter[str] = Counter()
        for chunk in seed_chunks[: self.seed_top_k]:
            text = str(chunk.get("text", "")) if isinstance(chunk, dict) else ""
            for phrase in self._extract_long_forms(text, abbrev):
                counts[phrase] += 1
        if not counts:
            return None
        return counts.most_common(1)[0][0]

    @staticmethod
    def _extract_long_forms(text: str, abbrev: str) -> List[str]:
        escaped = re.escape(abbrev)
        patterns = [
            re.compile(rf"([A-Za-z][A-Za-z0-9&/.,\- ]{{2,80}}?)\s*\(\s*{escaped}\s*\)"),
            re.compile(rf"{escaped}\s*\(\s*([A-Za-z][A-Za-z0-9&/.,\- ]{{2,80}}?)\s*\)"),
        ]
        candidates: List[str] = []
        for pattern in patterns:
            for match in pattern.finditer(text):
                phrase = _clean_text(match.group(1).strip(" ,.;:()"))
                if len(phrase.split()) < 2:
                    continue
                if phrase.upper() == phrase:
                    continue
                candidates.append(phrase)
        return _unique_keep_order(candidates)

    def _load_abbrev_map(self, path: str) -> Dict[str, List[str]]:
        if not os.path.exists(path):
            logger.warning("abbrev dict path not found: %s", path)
            return {}

        _, ext = os.path.splitext(path.lower())
        loaded: Dict[str, List[str]] = {}
        try:
            if ext == ".json":
                with open(path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                if isinstance(payload, dict):
                    for key, val in payload.items():
                        terms = _coerce_terms(val)
                        if terms:
                            loaded[str(key).upper()] = terms
                return loaded

            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    row = line.strip()
                    if not row or row.startswith("#"):
                        continue
                    if "\t" in row:
                        key, raw = row.split("\t", 1)
                    elif "=" in row:
                        key, raw = row.split("=", 1)
                    elif ":" in row:
                        key, raw = row.split(":", 1)
                    else:
                        continue
                    terms = _coerce_terms([p for p in raw.split("|") if p.strip()])
                    if terms:
                        loaded[key.strip().upper()] = terms
        except Exception as exc:
            logger.warning("failed to load abbrev dict %s: %s", path, exc)
            return {}
        return loaded


def build_query_expander_from_config(config: Dict[str, Any]) -> Optional[QueryExpander]:
    qexpand_cfg = config.get("qexpand", {}) if isinstance(config, dict) else {}
    if not isinstance(qexpand_cfg, dict) or not qexpand_cfg.get("enabled", False):
        return None

    abbrev_cfg = qexpand_cfg.get("abbrev", {}) if isinstance(qexpand_cfg.get("abbrev"), dict) else {}
    prf_cfg = (
        qexpand_cfg.get("prf_year", {}) if isinstance(qexpand_cfg.get("prf_year"), dict) else {}
    )
    return QueryExpander(
        enabled=bool(qexpand_cfg.get("enabled", False)),
        max_queries=int(qexpand_cfg.get("max_queries", 3)),
        abbrev_enabled=bool(abbrev_cfg.get("enabled", True)),
        prf_year_enabled=bool(prf_cfg.get("enabled", True)),
        seed_top_k=int(qexpand_cfg.get("seed_top_k", 5)),
        abbrev_dict_path=abbrev_cfg.get("dict_path"),
    )
