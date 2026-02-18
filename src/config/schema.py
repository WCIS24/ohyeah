from __future__ import annotations

import copy
import os
from typing import Any, Dict, List, Tuple

import yaml


DEFAULT_CONFIG: Dict[str, Any] = {
    "output_dir": "outputs",
    "data": {
        "processed_dir": "data/processed",
        "corpus_dir": "data/corpus",
        "corpus_file": "chunks.jsonl",
        "splits": {"train": "train.jsonl", "dev": "dev.jsonl", "test": "test.jsonl"},
    },
    "chunking": {"chunk_size": 200, "overlap": 50},
    "retriever": {
        "mode": "hybrid",
        "top_k": 5,
        "top_k_each_step": 5,
        "sparse": {"enabled": True, "type": "bm25"},
        "dense": {"enabled": True, "model_name_or_path": "sentence-transformers/all-MiniLM-L6-v2"},
        "hybrid": {"enabled": True, "alpha": 0.5},
        "index": {"use_faiss": False, "faiss_type": "flatip", "brute_force_fallback": True},
    },
    "multistep": {
        "enabled": False,
        "max_steps": 3,
        "top_k_each_step": 5,
        "top_k_final": 10,
        "novelty_threshold": 0.3,
        "stop_no_new_steps": 2,
        "merge_strategy": "maxscore",
        "gate": {"enabled": True, "min_gap_conf": 0.3, "allow_types": ["YEAR", "COMPARE"]},
    },
    "calculator": {
        "enabled": False,
        "gate": {
            "enabled": True,
            "min_conf": 0.4,
            "require_unit_consistency": True,
            "require_year_match": True,
            "allow_inferred": False,
            "allow_task_types": ["yoy", "diff"],
        },
        "parsing": {
            "rounding": 4,
            "thousand_sep": ",",
            "unit_map": {
                "billion": 1e9,
                "million": 1e6,
                "thousand": 1e3,
                "k": 1e3,
                "m": 1e6,
                "b": 1e9,
            },
            "output_percent": True,
        },
    },
    "eval": {
        "k_list": [1, 5, 10],
        "skip_retrieval": False,
        "subsets": {
            "complex_path": "data/subsets/dev_complex_qids.txt",
            "abbrev_path": "data/subsets/dev_abbrev_qids.txt",
            "numeric_path": "data/subsets/dev_numeric_qids.txt",
        },
        "numeric": {"tolerance": 4, "rel_eps": 1e-9, "normalize_percent_mode": "auto"},
    },
    "runtime": {"seed": 42, "max_samples": None, "num_workers": 1, "device": None},
}


SCHEMA_TYPES: Dict[str, Tuple[type, ...]] = {
    "output_dir": (str,),
    "data": (dict,),
    "data.processed_dir": (str,),
    "data.corpus_dir": (str,),
    "data.corpus_file": (str,),
    "data.splits": (dict,),
    "data.splits.train": (str,),
    "data.splits.dev": (str,),
    "data.splits.test": (str,),
    "chunking": (dict,),
    "chunking.chunk_size": (int,),
    "chunking.overlap": (int,),
    "retriever": (dict,),
    "retriever.mode": (str,),
    "retriever.top_k": (int,),
    "retriever.top_k_each_step": (int,),
    "retriever.sparse.enabled": (bool,),
    "retriever.sparse.type": (str,),
    "retriever.dense.enabled": (bool,),
    "retriever.dense.model_name_or_path": (str,),
    "retriever.hybrid.enabled": (bool,),
    "retriever.hybrid.alpha": (float, int),
    "retriever.index.use_faiss": (bool,),
    "retriever.index.faiss_type": (str,),
    "retriever.index.brute_force_fallback": (bool,),
    "multistep.enabled": (bool,),
    "multistep.max_steps": (int,),
    "multistep.top_k_each_step": (int,),
    "multistep.top_k_final": (int,),
    "multistep.novelty_threshold": (float, int),
    "multistep.stop_no_new_steps": (int,),
    "multistep.merge_strategy": (str,),
    "multistep.gate.enabled": (bool,),
    "multistep.gate.min_gap_conf": (float, int),
    "multistep.gate.allow_types": (list,),
    "calculator.enabled": (bool,),
    "calculator.gate.enabled": (bool,),
    "calculator.gate.min_conf": (float, int),
    "calculator.gate.require_unit_consistency": (bool,),
    "calculator.gate.require_year_match": (bool,),
    "calculator.gate.allow_inferred": (bool,),
    "calculator.gate.allow_task_types": (list,),
    "calculator.parsing.rounding": (int,),
    "calculator.parsing.thousand_sep": (str,),
    "calculator.parsing.unit_map": (dict,),
    "calculator.parsing.output_percent": (bool,),
    "eval.k_list": (list,),
    "eval.skip_retrieval": (bool,),
    "eval.subsets.complex_path": (str,),
    "eval.subsets.abbrev_path": (str,),
    "eval.subsets.numeric_path": (str,),
    "eval.numeric.tolerance": (int,),
    "eval.numeric.rel_eps": (float, int),
    "eval.numeric.normalize_percent_mode": (str,),
    "runtime.seed": (int,),
    "runtime.max_samples": (int, type(None)),
    "runtime.num_workers": (int,),
    "runtime.device": (str, type(None)),
}


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def save_yaml(data: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(base.get(key), dict):
            base[key] = deep_merge(base[key], val)
        else:
            base[key] = val
    return base


def set_path(config: Dict[str, Any], dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    cur = config
    for part in parts[:-1]:
        if part not in cur or not isinstance(cur[part], dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = value


def get_path(config: Dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    parts = dotted_key.split(".")
    cur: Any = config
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _apply_legacy_mappings(raw: Dict[str, Any], resolved: Dict[str, Any]) -> None:
    for split_key, legacy_key in [
        ("train", "processed_train_path"),
        ("dev", "processed_dev_path"),
        ("test", "processed_test_path"),
    ]:
        legacy_path = raw.get(legacy_key)
        if legacy_path:
            set_path(resolved, "data.processed_dir", os.path.dirname(legacy_path))
            set_path(resolved, f"data.splits.{split_key}", os.path.basename(legacy_path))

    if raw.get("processed_dir"):
        set_path(resolved, "data.processed_dir", raw["processed_dir"])

    corpus_path = raw.get("corpus_path") or raw.get("corpus_file")
    if corpus_path:
        set_path(resolved, "data.corpus_dir", os.path.dirname(corpus_path))
        set_path(resolved, "data.corpus_file", os.path.basename(corpus_path))

    retr_cfg = raw.get("retriever", {})
    if "model_name" in retr_cfg:
        set_path(resolved, "retriever.dense.model_name_or_path", retr_cfg.get("model_name"))
    if "use_faiss" in retr_cfg:
        set_path(resolved, "retriever.index.use_faiss", bool(retr_cfg.get("use_faiss")))
    if "alpha" in retr_cfg:
        set_path(resolved, "retriever.hybrid.alpha", float(retr_cfg.get("alpha")))
    if "mode" in retr_cfg:
        set_path(resolved, "retriever.mode", retr_cfg.get("mode"))
    if "top_k" in retr_cfg:
        set_path(resolved, "retriever.top_k", int(retr_cfg.get("top_k")))
    if "top_k_each_step" in retr_cfg:
        set_path(resolved, "retriever.top_k_each_step", int(retr_cfg.get("top_k_each_step")))

    if "alpha" in raw:
        set_path(resolved, "retriever.hybrid.alpha", float(raw.get("alpha")))
    if "mode" in raw:
        set_path(resolved, "retriever.mode", raw.get("mode"))
    if "top_k" in raw:
        set_path(resolved, "retriever.top_k", int(raw.get("top_k")))
    if "k_values" in raw:
        set_path(resolved, "eval.k_list", list(raw.get("k_values")))
    if "seed" in raw:
        try:
            set_path(resolved, "runtime.seed", int(raw.get("seed")))
        except (TypeError, ValueError):
            pass

    if "max_steps" in raw:
        set_path(resolved, "multistep.max_steps", int(raw.get("max_steps")))
    if "top_k_final" in raw:
        set_path(resolved, "multistep.top_k_final", int(raw.get("top_k_final")))
    if "novelty_threshold" in raw:
        set_path(resolved, "multistep.novelty_threshold", float(raw.get("novelty_threshold")))
    if "stop_no_new_steps" in raw:
        set_path(resolved, "multistep.stop_no_new_steps", int(raw.get("stop_no_new_steps")))
    if "gap_enabled" in raw:
        set_path(resolved, "multistep.gate.enabled", bool(raw.get("gap_enabled")))
    if "refiner_enabled" in raw:
        set_path(resolved, "multistep.refiner_enabled", bool(raw.get("refiner_enabled")))

    if "output_percent" in raw:
        set_path(resolved, "calculator.parsing.output_percent", bool(raw.get("output_percent")))


def resolve_config(raw: Dict[str, Any]) -> Dict[str, Any]:
    resolved = deep_merge(copy.deepcopy(DEFAULT_CONFIG), raw)
    _apply_legacy_mappings(raw, resolved)
    return resolved


def validate_config(config: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key, expected in SCHEMA_TYPES.items():
        val = get_path(config, key, None)
        if val is None:
            continue
        if not isinstance(val, expected):
            errors.append(f"{key}: expected {expected}, got {type(val)}")
    return errors


def validate_paths(config: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    processed_dir = get_path(config, "data.processed_dir")
    corpus_dir = get_path(config, "data.corpus_dir")
    if processed_dir and not os.path.exists(processed_dir):
        warnings.append(f"processed_dir missing: {processed_dir}")
    if corpus_dir and not os.path.exists(corpus_dir):
        warnings.append(f"corpus_dir missing: {corpus_dir}")
    for path_key in [
        "eval.subsets.complex_path",
        "eval.subsets.abbrev_path",
        "eval.subsets.numeric_path",
    ]:
        path = get_path(config, path_key)
        if path and not os.path.exists(path):
            warnings.append(f"subset path missing: {path}")
    return warnings


def load_and_resolve(config_path: str) -> Dict[str, Any]:
    raw = load_yaml(config_path)
    return resolve_config(raw)


def write_resolved_config(config: Dict[str, Any], run_dir: str) -> str:
    path = os.path.join(run_dir, "config.resolved.yaml")
    save_yaml(config, path)
    return path


def resolve_and_validate(config_path: str, run_dir: str) -> Tuple[Dict[str, Any], str, List[str]]:
    resolved = load_and_resolve(config_path)
    errors = validate_config(resolved)
    warnings = validate_paths(resolved)
    resolved_path = write_resolved_config(resolved, run_dir)
    return resolved, resolved_path, errors + warnings
