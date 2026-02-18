from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from retrieval.query_expansion import QueryExpander, build_query_expander_from_config

logger = logging.getLogger(__name__)


def tokenize(text: str) -> List[str]:
    return text.lower().split()


def min_max_normalize(scores: np.ndarray) -> np.ndarray:
    if scores.size == 0:
        return scores
    min_val = float(scores.min())
    max_val = float(scores.max())
    if max_val == min_val:
        return np.zeros_like(scores, dtype=np.float32)
    return (scores - min_val) / (max_val - min_val)


def cosine_sim(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    return np.dot(matrix, query_vec)


def try_import_faiss() -> Optional[object]:
    try:
        import faiss  # type: ignore

        return faiss
    except Exception:
        return None


def build_retriever_from_config(config: Dict[str, object]) -> "HybridRetriever":
    retr_cfg = config.get("retriever", {}) if isinstance(config, dict) else {}
    dense_cfg = retr_cfg.get("dense", {}) if isinstance(retr_cfg, dict) else {}
    index_cfg = retr_cfg.get("index", {}) if isinstance(retr_cfg, dict) else {}
    model_name = dense_cfg.get("model_name_or_path") or retr_cfg.get(
        "model_name", "sentence-transformers/all-MiniLM-L6-v2"
    )
    use_faiss = bool(index_cfg.get("use_faiss", retr_cfg.get("use_faiss", True)))
    device = retr_cfg.get("device")
    batch_size = int(retr_cfg.get("batch_size", 32))
    retriever = HybridRetriever(
        model_name=model_name,
        use_faiss=use_faiss,
        device=device,
        batch_size=batch_size,
    )
    qexpand_cfg = config.get("qexpand", {}) if isinstance(config, dict) else {}
    expander = build_query_expander_from_config(config)
    if expander is not None:
        retriever.set_query_expander(expander, qexpand_cfg if isinstance(qexpand_cfg, dict) else {})
    return retriever


class HybridRetriever:
    def __init__(
        self,
        model_name: object = "sentence-transformers/all-MiniLM-L6-v2",
        use_faiss: bool = True,
        device: Optional[str] = None,
        batch_size: int = 32,
    ) -> None:
        self.model_name = model_name
        self.use_faiss = use_faiss
        self.device = device
        self.batch_size = batch_size

        self.texts: List[str] = []
        self.metas: List[Dict[str, str]] = []
        self.bm25: Optional[BM25Okapi] = None
        self.model: Optional[SentenceTransformer] = None
        self.loaded_model_name: Optional[str] = None
        self.embeddings: Optional[np.ndarray] = None
        self.faiss_index = None
        self.query_expander: Optional[QueryExpander] = None
        self.qexpand_cfg: Dict[str, Any] = {}
        self._last_qexpand_trace: Dict[str, Any] = {}

    def build_index(self, corpus_chunks: List[Dict[str, object]]) -> None:
        self.texts = [c["text"] for c in corpus_chunks]
        self.metas = [c["meta"] for c in corpus_chunks]

        tokenized = [tokenize(t) for t in self.texts]
        self.bm25 = BM25Okapi(tokenized)

        if isinstance(self.model_name, SentenceTransformer):
            self.model = self.model_name
            self.loaded_model_name = getattr(self.model, "name_or_path", "provided_instance")
        else:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.loaded_model_name = str(self.model_name)
        embeddings = self.model.encode(
            self.texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )
        self.embeddings = embeddings.astype("float32")

        faiss_mod = try_import_faiss() if self.use_faiss else None
        if faiss_mod is not None:
            index = faiss_mod.IndexFlatIP(self.embeddings.shape[1])
            index.add(self.embeddings)
            self.faiss_index = index
        else:
            self.faiss_index = None
            if self.use_faiss:
                logger.warning("FAISS not available, falling back to brute-force")

    def _dense_scores(self, query: str) -> np.ndarray:
        if self.model is None or self.embeddings is None:
            raise RuntimeError("Dense model not initialized")

        query_vec = self.model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")[0]

        if self.faiss_index is not None:
            scores, _ = self.faiss_index.search(query_vec.reshape(1, -1), len(self.texts))
            return scores.flatten()
        return cosine_sim(query_vec, self.embeddings)

    def set_query_expander(self, expander: Optional[QueryExpander], cfg: Optional[Dict[str, Any]]) -> None:
        self.query_expander = expander
        self.qexpand_cfg = cfg or {}

    def get_last_qexpand_trace(self) -> Dict[str, Any]:
        return dict(self._last_qexpand_trace)

    def _combined_scores(
        self,
        query: str,
        alpha: float,
        mode: str,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.bm25 is None:
            raise RuntimeError("BM25 not initialized")

        bm25_scores = np.array(self.bm25.get_scores(tokenize(query)), dtype=np.float32)
        dense_scores = self._dense_scores(query)

        if mode == "bm25":
            combined = min_max_normalize(bm25_scores)
        elif mode == "dense":
            combined = min_max_normalize(dense_scores)
        else:
            bm25_norm = min_max_normalize(bm25_scores)
            dense_norm = min_max_normalize(dense_scores)
            combined = alpha * bm25_norm + (1.0 - alpha) * dense_norm
        return combined, bm25_scores, dense_scores

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.5,
        mode: str = "hybrid",
    ) -> List[Dict[str, object]]:
        base_scores, bm25_scores, dense_scores = self._combined_scores(query, alpha=alpha, mode=mode)
        final_scores = base_scores.copy()
        expanded_queries = [query]
        trace = {
            "enabled": bool(self.query_expander and self.qexpand_cfg.get("enabled", False)),
            "expanded": False,
            "num_queries": 1,
            "queries": [query],
            "abbrev_added": False,
            "prf_year_added": False,
            "years_added": [],
        }

        if self.query_expander and self.qexpand_cfg.get("enabled", False):
            seed_top_k = int(self.qexpand_cfg.get("seed_top_k", 5))
            seed_top_k = max(1, min(seed_top_k, len(self.texts)))
            seed_idx = np.argsort(base_scores)[::-1][:seed_top_k]
            seed_chunks = [
                {
                    "text": self.texts[idx],
                    "score": float(base_scores[idx]),
                    "meta": self.metas[idx],
                }
                for idx in seed_idx
            ]

            expanded_queries = self.query_expander.expand(query, seed_chunks=seed_chunks)
            boost = float(self.qexpand_cfg.get("boost", 0.15))
            expansion_top_m = int(self.qexpand_cfg.get("expansion_top_m", top_k))
            expansion_top_m = max(1, min(expansion_top_m, len(self.texts)))

            if boost > 0:
                for expanded_query in expanded_queries[1:]:
                    expanded_scores, _, _ = self._combined_scores(
                        expanded_query,
                        alpha=alpha,
                        mode=mode,
                    )
                    boosted_idx = np.argsort(expanded_scores)[::-1][:expansion_top_m]
                    final_scores[boosted_idx] += boost * expanded_scores[boosted_idx]

            expander_trace = self.query_expander.get_last_trace()
            trace.update(
                {
                    "expanded": bool(expander_trace.get("expanded", False)),
                    "num_queries": int(expander_trace.get("num_queries", len(expanded_queries))),
                    "queries": expanded_queries,
                    "abbrev_added": bool(expander_trace.get("abbrev_added", False)),
                    "prf_year_added": bool(expander_trace.get("prf_year_added", False)),
                    "years_added": expander_trace.get("years_added", []),
                    "boost": boost,
                }
            )

        self._last_qexpand_trace = trace
        top_idx = np.argsort(final_scores)[::-1][:top_k]
        results = []
        for idx in top_idx:
            results.append(
                {
                    "text": self.texts[idx],
                    "score": float(final_scores[idx]),
                    "bm25": float(bm25_scores[idx]),
                    "dense": float(dense_scores[idx]),
                    "meta": self.metas[idx],
                }
            )
        return results
