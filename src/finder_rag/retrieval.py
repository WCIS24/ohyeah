from __future__ import annotations

from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class TfidfRetriever:
    def __init__(self, max_features: int = 20000, ngram_range: Tuple[int, int] = (1, 2)):
        self.vectorizer = TfidfVectorizer(max_features=max_features, ngram_range=ngram_range)
        self.matrix = None
        self.corpus: List[str] = []

    def fit(self, corpus: List[str]) -> None:
        self.corpus = corpus
        self.matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, k: int) -> List[int]:
        if self.matrix is None:
            raise RuntimeError("Retriever is not fitted.")
        query_vec = self.vectorizer.transform([query])
        scores = linear_kernel(query_vec, self.matrix).ravel()
        top_idx = scores.argsort()[::-1][:k]
        return top_idx.tolist()
