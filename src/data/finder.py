from __future__ import annotations

import ast
import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from datasets import Dataset, DatasetDict, load_dataset


def _features_to_dict(features: Any) -> Dict[str, Any]:
    try:
        return features.to_dict()
    except Exception:
        return {"repr": str(features)}


def inspect_schema(dataset: DatasetDict) -> Dict[str, Any]:
    schema = {}
    for split, ds in dataset.items():
        schema[split] = _features_to_dict(ds.features)
    return schema


def load_finder_dataset(
    dataset_name: Optional[str] = None,
    dataset_config: Optional[str] = None,
    data_files: Optional[Any] = None,
    split: Optional[str] = None,
) -> DatasetDict:
    if data_files:
        file_path = data_files if isinstance(data_files, str) else None
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".csv":
                return load_dataset("csv", data_files={"train": file_path})
            if ext in {".json", ".jsonl"}:
                return load_dataset("json", data_files={"train": file_path})
        return load_dataset("csv", data_files=data_files)

    if not dataset_name:
        raise ValueError("dataset_name or data_files must be provided")

    if dataset_config:
        return load_dataset(dataset_name, dataset_config, split=split)
    return load_dataset(dataset_name, split=split)


def _parse_evidence_field(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(v) for v in parsed if str(v).strip()]
        except (SyntaxError, ValueError):
            return [value] if value.strip() else []
    return [str(value)]


def normalize_sample(
    sample: Dict[str, Any],
    field_map: Dict[str, str],
    sample_index: int,
) -> Dict[str, Any]:
    qid_key = field_map.get("qid")
    query_key = field_map.get("query")
    answer_key = field_map.get("answer")
    evidence_key = field_map.get("evidences")
    doc_id_key = field_map.get("doc_id")

    if qid_key and qid_key in sample:
        qid = str(sample[qid_key])
    else:
        qid = f"row_{sample_index}"

    if not query_key or query_key not in sample:
        raise KeyError(f"query field '{query_key}' not found in sample")

    query = str(sample.get(query_key, ""))
    answer = str(sample.get(answer_key, "")) if answer_key else ""

    evidences_raw = []
    if evidence_key:
        evidences_raw = _parse_evidence_field(sample.get(evidence_key))

    doc_ids: List[Optional[str]] = []
    if doc_id_key and doc_id_key in sample:
        doc_val = sample.get(doc_id_key)
        if isinstance(doc_val, list):
            doc_ids = [str(v) for v in doc_val]
        else:
            doc_ids = [str(doc_val)] * len(evidences_raw)

    evidences = []
    for idx, text in enumerate(evidences_raw):
        doc_id = doc_ids[idx] if idx < len(doc_ids) else None
        evidences.append(
            {
                "text": str(text),
                "doc_id": doc_id,
                "meta": {"evidence_id": idx},
            }
        )

    meta = {"source": {}}
    for key, value in sample.items():
        if key in {qid_key, query_key, answer_key, evidence_key, doc_id_key}:
            continue
        meta["source"][key] = value

    return {
        "qid": qid,
        "query": query,
        "answer": answer,
        "evidences": evidences,
        "meta": meta,
    }


def dataset_to_records(
    dataset: Dataset,
    field_map: Dict[str, str],
    max_samples: Optional[int] = None,
) -> List[Dict[str, Any]]:
    records = []
    for idx, sample in enumerate(dataset):
        if max_samples is not None and idx >= max_samples:
            break
        record = normalize_sample(sample, field_map, idx)
        if record["evidences"]:
            records.append(record)
    return records


def split_dataset(
    dataset: DatasetDict,
    seed: int,
    train_ratio: float,
    dev_ratio: float,
    test_ratio: float,
    max_samples: Optional[int] = None,
) -> DatasetDict:
    splits = list(dataset.keys())
    if len(splits) > 1:
        mapped = DatasetDict()
        if "train" in dataset:
            mapped["train"] = dataset["train"]
        if "validation" in dataset:
            mapped["dev"] = dataset["validation"]
        if "dev" in dataset:
            mapped["dev"] = dataset["dev"]
        if "test" in dataset:
            mapped["test"] = dataset["test"]
        dataset = mapped

    if len(dataset.keys()) == 1:
        base = next(iter(dataset.values()))
        if max_samples:
            base = base.shuffle(seed=seed).select(range(min(max_samples, len(base))))
        train_split = base.train_test_split(test_size=(1 - train_ratio), seed=seed)
        temp = train_split["test"]
        dev_size = dev_ratio / (dev_ratio + test_ratio)
        dev_test = temp.train_test_split(test_size=(1 - dev_size), seed=seed)
        return DatasetDict(
            {
                "train": train_split["train"],
                "dev": dev_test["train"],
                "test": dev_test["test"],
            }
        )

    if max_samples:
        for split_name in list(dataset.keys()):
            ds = dataset[split_name]
            if len(ds) > max_samples:
                dataset[split_name] = ds.shuffle(seed=seed).select(range(max_samples))
    return dataset


def summarize_text_stats(texts: Iterable[str]) -> Dict[str, float]:
    lengths = [len(t) for t in texts]
    if not lengths:
        return {"count": 0}
    lengths_sorted = sorted(lengths)
    p50 = lengths_sorted[len(lengths_sorted) // 2]
    p90 = lengths_sorted[int(len(lengths_sorted) * 0.9) - 1]
    return {
        "count": len(lengths),
        "min": min(lengths),
        "max": max(lengths),
        "mean": sum(lengths) / len(lengths),
        "p50": p50,
        "p90": p90,
    }


def summarize_numeric(values: Iterable[int]) -> Dict[str, float]:
    values = [int(v) for v in values]
    if not values:
        return {"count": 0}
    values_sorted = sorted(values)
    p50 = values_sorted[len(values_sorted) // 2]
    p90 = values_sorted[int(len(values_sorted) * 0.9) - 1]
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "p50": p50,
        "p90": p90,
    }


def compute_query_flags(queries: Iterable[str]) -> Dict[str, float]:
    year_re = re.compile(r"\b(19|20)\d{2}\b")
    digit_re = re.compile(r"\d")
    percent_re = re.compile(r"%")

    queries = list(queries)
    if not queries:
        return {"year_ratio": 0.0, "digit_ratio": 0.0, "percent_ratio": 0.0}

    year_hits = sum(1 for q in queries if year_re.search(q))
    digit_hits = sum(1 for q in queries if digit_re.search(q))
    percent_hits = sum(1 for q in queries if percent_re.search(q))

    total = len(queries)
    return {
        "year_ratio": year_hits / total,
        "digit_ratio": digit_hits / total,
        "percent_ratio": percent_hits / total,
    }


def write_json(obj: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
