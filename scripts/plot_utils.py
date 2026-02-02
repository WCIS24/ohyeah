from __future__ import annotations

import json
import os
import random
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import yaml


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_yaml(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(data: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def load_json(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def read_experiments(
    experiments_path: Optional[str],
    extra_experiments: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    experiments: List[Dict[str, Any]] = []
    if experiments_path and os.path.exists(experiments_path):
        data = load_yaml(experiments_path)
        experiments = list(data.get("experiments", []) or [])
    if extra_experiments:
        experiments.extend(extra_experiments)
    return experiments


def format_value(value: Any, digits: int) -> str:
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return str(value)


def parse_metric_k(metrics: Dict[str, Any], prefix: str) -> Dict[int, float]:
    out: Dict[int, float] = {}
    pattern = re.compile(rf"^{re.escape(prefix)}@(\d+)$")
    for key, val in metrics.items():
        match = pattern.match(str(key))
        if match and isinstance(val, (int, float)):
            out[int(match.group(1))] = float(val)
    return out


def choose_k_values(metrics: Dict[str, Any], prefix: str, fallback: List[int]) -> List[int]:
    found = parse_metric_k(metrics, prefix)
    if found:
        return sorted(found.keys())
    return fallback


def extract_summary_metrics(summary: Dict[str, Any]) -> Dict[str, Optional[float]]:
    metrics = summary.get("metrics", {}) if isinstance(summary, dict) else {}
    full = metrics.get("retrieval_full", {}) if isinstance(metrics, dict) else {}
    complex_m = metrics.get("retrieval_complex", {}) if isinstance(metrics, dict) else {}
    numeric = metrics.get("numeric_dev", {}) if isinstance(metrics, dict) else {}
    return {
        "full_r10": _safe_float(full.get("recall@10")),
        "full_mrr10": _safe_float(full.get("mrr@10")),
        "complex_r10": _safe_float(complex_m.get("recall@10")),
        "complex_mrr10": _safe_float(complex_m.get("mrr@10")),
        "numeric_em": _safe_float(numeric.get("numeric_em")),
        "rel_error_mean": _safe_float(numeric.get("rel_error_mean")),
        "coverage": _safe_float(numeric.get("coverage")),
    }


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_role_map(role_map_path: str) -> Dict[str, Any]:
    return load_yaml(role_map_path) if role_map_path else {}


def resolve_role(
    label: str,
    explicit_role: Optional[str],
    role_map: Dict[str, Any],
) -> str:
    roles = role_map.get("roles", {})
    if explicit_role and explicit_role in roles:
        return explicit_role
    aliases = role_map.get("aliases", {})
    if label in aliases:
        return aliases[label]
    if label.lower() in aliases:
        return aliases[label.lower()]
    if roles:
        return next(iter(roles.keys()))
    return "baseline"


def role_style(
    role: str,
    role_map: Dict[str, Any],
    palette: Dict[str, Any],
    theme: str,
) -> Dict[str, Any]:
    roles = role_map.get("roles", {})
    role_cfg = roles.get(role, {})
    color_key = role_cfg.get("color_key", "neutral")
    theme_cfg = palette.get("themes", {}).get(theme, {})
    colors = theme_cfg.get("colors", {})
    color = colors.get(color_key)
    if color is None:
        color = colors.get("neutral", "#4d4d4d")
    return {
        "color": color,
        "linestyle": role_cfg.get("linestyle", "-"),
        "marker": role_cfg.get("marker", None),
        "label": role_cfg.get("label", role),
        "hatch": role_cfg.get("hatch", None),
    }


def best_and_second(
    values: Iterable[Optional[float]],
    higher_is_better: bool,
) -> Tuple[Optional[float], Optional[float]]:
    cleaned = [v for v in values if isinstance(v, (int, float))]
    if not cleaned:
        return None, None
    sorted_vals = sorted(set(cleaned), reverse=higher_is_better)
    best_val = sorted_vals[0] if sorted_vals else None
    second_val = sorted_vals[1] if len(sorted_vals) > 1 else None
    return best_val, second_val


def find_existing_file(run_dir: str, filenames: List[str]) -> Optional[str]:
    for name in filenames:
        path = os.path.join(run_dir, name)
        if os.path.exists(path):
            return path
    return None


def path_or_none(path: Optional[str]) -> Optional[str]:
    if path and os.path.exists(path):
        return path
    return None


def data_root_from_config(config: Dict[str, Any]) -> str:
    return str(config.get("data_root", "outputs"))


def style_dir_from_config(config: Dict[str, Any]) -> str:
    return str(config.get("style_dir", "thesis/figures/style"))


def output_root_from_config(config: Dict[str, Any]) -> str:
    return str(config.get("output_root", "thesis/figures"))


def safe_path(*parts: str) -> str:
    return str(Path(*parts))
