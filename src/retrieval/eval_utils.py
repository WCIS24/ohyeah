from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def match_chunk(
    chunk: Dict[str, Any],
    qid: str,
    gold_evidences: List[Dict[str, Any]],
) -> Tuple[bool, str, Optional[int]]:
    meta = chunk.get("meta", {})
    evidence_id = meta.get("evidence_id")
    doc_id = meta.get("doc_id")
    source_qid = meta.get("source_qid")

    for ev in gold_evidences:
        ev_id = ev.get("meta", {}).get("evidence_id")
        ev_doc = ev.get("doc_id")
        if source_qid == qid and evidence_id == ev_id:
            if ev_doc is None or doc_id == ev_doc:
                return True, "id", ev_id

    chunk_text = normalize_text(chunk.get("text", ""))
    gold_texts = [normalize_text(ev.get("text", "")) for ev in gold_evidences]
    for ev_text, ev in zip(gold_texts, gold_evidences):
        if not ev_text:
            continue
        if chunk_text in ev_text or ev_text in chunk_text:
            return True, "text", ev.get("meta", {}).get("evidence_id")

    return False, "none", None


def compute_retrieval_metrics(
    eval_records: Iterable[Dict[str, Any]],
    retriever,
    k_values: List[int],
    mode: str = "dense",
    alpha: float = 0.5,
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    k_values = [int(k) for k in k_values]
    k_max = max(k_values)
    per_query = []
    recall_scores = {k: [] for k in k_values}
    hit_scores = {k: [] for k in k_values}
    mrr_scores = {k: [] for k in k_values}
    fallback_queries = 0

    for rec in eval_records:
        qid = rec.get("qid")
        gold_evidences = rec.get("evidences", [])
        if not gold_evidences:
            continue

        results = retriever.retrieve(rec.get("query", ""), top_k=k_max, alpha=alpha, mode=mode)
        qexpand_trace = {}
        if hasattr(retriever, "get_last_qexpand_trace"):
            try:
                qexpand_trace = retriever.get_last_qexpand_trace() or {}
            except Exception:
                qexpand_trace = {}
        hits = []
        matched_ids_by_rank: List[Optional[int]] = []
        used_fallback = False

        for chunk in results:
            hit, mode_used, ev_id = match_chunk(chunk, qid, gold_evidences)
            hits.append(hit)
            if hit:
                matched_ids_by_rank.append(ev_id)
                if mode_used == "text":
                    used_fallback = True
            else:
                matched_ids_by_rank.append(None)

        if used_fallback:
            fallback_queries += 1

        total_gold = len(gold_evidences)
        for k in k_values:
            top_hits = hits[:k]
            matched_ids = {ev_id for ev_id in matched_ids_by_rank[:k] if ev_id is not None}
            match_count = len(matched_ids)
            recall_scores[k].append(match_count / total_gold)
            hit_scores[k].append(1.0 if any(top_hits) else 0.0)
            mrr_scores[k].append(reciprocal_rank(top_hits))

        per_query.append(
            {
                "qid": qid,
                "first_hit_rank": (hits.index(True) + 1) if any(hits) else None,
                "matched_evidence_ids": sorted(
                    list({ev_id for ev_id in matched_ids_by_rank if ev_id is not None})
                ),
                "used_fallback": used_fallback,
                "qexpand": qexpand_trace,
            }
        )

    metrics = {
        "num_queries": len(per_query),
        "mode": mode,
        "alpha": alpha,
        "uncertain_match_ratio": fallback_queries / len(per_query) if per_query else 0.0,
    }
    for k in k_values:
        metrics[f"recall@{k}"] = mean(recall_scores[k])
        metrics[f"evidence_hit@{k}"] = mean(hit_scores[k])
        metrics[f"mrr@{k}"] = mean(mrr_scores[k])

    return metrics, per_query


def reciprocal_rank(hits: Iterable[bool]) -> float:
    for idx, hit in enumerate(hits, start=1):
        if hit:
            return 1.0 / idx
    return 0.0


def mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))
