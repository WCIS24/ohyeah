from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import subprocess
import sys
from typing import Any, Dict, List

import yaml

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.utils import ensure_dir, generate_run_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grid sweep runner")
    parser.add_argument("--base-config", required=True, help="Base config YAML")
    parser.add_argument("--search-space", required=True, help="Search space YAML")
    parser.add_argument("--tag", default=None, help="Optional tag")
    return parser.parse_args()


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_metric(summary: Dict[str, Any], metric_path: str) -> Any:
    parts = metric_path.split(".")
    cur: Any = summary.get("metrics", {})
    for p in parts:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


def constraint_min_value(constraint: Dict[str, Any]) -> Any:
    min_val = constraint.get("min")
    if min_val is not None:
        return min_val
    baseline_path = constraint.get("baseline_metrics_path")
    metric = constraint.get("metric")
    delta = constraint.get("min_delta", 0.0)
    if baseline_path and metric and os.path.exists(baseline_path):
        with open(baseline_path, "r", encoding="utf-8") as f:
            base = json.load(f)
        base_val = base.get(metric)
        if base_val is None:
            return None
        return base_val + delta
    return None


def main() -> int:
    args = parse_args()
    search_space = load_yaml(args.search_space)
    parameters: Dict[str, List[Any]] = search_space.get("parameters", {})
    objective = search_space.get("objective", {})
    constraint = search_space.get("constraint", {})

    sweep_id = generate_run_id()
    sweep_dir = os.path.join("outputs", sweep_id)
    ensure_dir(sweep_dir)

    keys = list(parameters.keys())
    values = [parameters[k] for k in keys]
    combos = list(itertools.product(*values))

    leaderboard_path = os.path.join(sweep_dir, "leaderboard.csv")
    best_config_path = os.path.join(sweep_dir, "best_config.yaml")

    rows = []
    best_score = None
    best_run = None

    constraint_min = constraint_min_value(constraint) if constraint else None

    for idx, combo in enumerate(combos, start=1):
        overrides = []
        for k, v in zip(keys, combo):
            overrides.append(f"{k}={json.dumps(v)}")
        run_id = f"{sweep_id}_t{idx:02d}"
        overrides.append(f"run_id={run_id}")

        cmd = [sys.executable, "scripts/run_experiment.py", "--config", args.base_config]
        if args.tag:
            cmd += ["--tag", args.tag]
        for ov in overrides:
            cmd += ["--overrides", ov]

        proc = subprocess.run(cmd, cwd=ROOT_DIR)
        if proc.returncode != 0:
            rows.append({"run_id": run_id, "status": "failed"})
            continue

        summary_path = os.path.join("outputs", run_id, "summary.json")
        if not os.path.exists(summary_path):
            rows.append({"run_id": run_id, "status": "missing_summary"})
            continue
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        metric_path = objective.get("metric")
        score = get_metric(summary, metric_path) if metric_path else None
        status = "ok"
        if constraint and constraint_min is not None:
            constraint_metric = constraint.get("metric")
            c_val = get_metric(summary, constraint_metric) if constraint_metric else None
            if c_val is None or c_val < constraint_min:
                status = "constraint_fail"
        rows.append({"run_id": run_id, "score": score, "status": status})

        if status == "ok" and score is not None:
            if best_score is None or (
                objective.get("mode", "max") == "max" and score > best_score
            ):
                best_score = score
                best_run = run_id

    with open(leaderboard_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["run_id", "score", "status"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    if best_run:
        resolved_path = os.path.join("outputs", best_run, "config.resolved.yaml")
        if os.path.exists(resolved_path):
            with open(resolved_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            with open(best_config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=False)

    print(f"sweep_dir={sweep_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
