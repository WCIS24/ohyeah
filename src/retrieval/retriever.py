from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

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
    return HybridRetriever(
        model_name=model_name,
        use_faiss=use_faiss,
        device=device,
        batch_size=batch_size,
    )


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

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.5,
        mode: str = "hybrid",
    ) -> List[Dict[str, object]]:
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

        top_idx = np.argsort(combined)[::-1][:top_k]
        results = []
        for idx in top_idx:
            results.append(
                {
                    "text": self.texts[idx],
                    "score": float(combined[idx]),
                    "bm25": float(bm25_scores[idx]),
                    "dense": float(dense_scores[idx]),
                    "meta": self.metas[idx],
                }
            )
        return results
