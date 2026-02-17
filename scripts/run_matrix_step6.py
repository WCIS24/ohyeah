from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

import yaml

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Step6 experiment matrix")
    parser.add_argument("--base-config", required=True, help="Base config YAML")
    parser.add_argument("--matrix", required=True, help="Matrix YAML with experiments")
    return parser.parse_args()


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def as_rel(path: str) -> str:
    return os.path.relpath(path, ROOT_DIR).replace("\\", "/")


def find_override_value(overrides: List[str], key: str) -> Optional[str]:
    prefix = f"{key}="
    for item in overrides:
        if item.startswith(prefix):
            return item[len(prefix) :]
    return None


def run_key_config(run_dir: str) -> Dict[str, Any]:
    resolved_path = os.path.join(run_dir, "config.resolved.yaml")
    if not os.path.exists(resolved_path):
        return {}
    cfg = load_yaml(resolved_path)
    eval_subsets = ((cfg.get("eval") or {}).get("subsets") or {})
    return {
        "seed": ((cfg.get("runtime") or {}).get("seed")),
        "retriever_mode": ((cfg.get("retriever") or {}).get("mode")),
        "multistep_enabled": bool(((cfg.get("multistep") or {}).get("enabled"))),
        "calculator_enabled": bool(((cfg.get("calculator") or {}).get("enabled"))),
        "subset_complex_path": eval_subsets.get("complex_path"),
        "subset_abbrev_path": eval_subsets.get("abbrev_path"),
        "subset_numeric_path": eval_subsets.get("numeric_path"),
    }


def run_output_root(overrides: List[str], default_root: str) -> str:
    output_dir = find_override_value(overrides, "output_dir")
    if output_dir is None:
        return default_root
    if os.path.isabs(output_dir):
        return output_dir
    return os.path.join(ROOT_DIR, output_dir)


def main() -> int:
    args = parse_args()
    matrix = load_yaml(args.matrix)
    experiments = matrix.get("experiments", [])

    matrix_id = generate_run_id()
    matrix_dir = os.path.join("outputs", matrix_id)
    runs_root = os.path.join(matrix_dir, "runs")
    ensure_dir(matrix_dir)
    ensure_dir(runs_root)

    results: List[Dict[str, Any]] = []
    resolved_rows: List[Dict[str, Any]] = []

    for idx, exp in enumerate(experiments, start=1):
        run_id = f"{matrix_id}_m{idx:02d}"
        overrides = [str(v) for v in exp.get("overrides", [])]
        if find_override_value(overrides, "output_dir") is None:
            overrides.append(f"output_dir={as_rel(runs_root)}")
        overrides.append(f"run_id={run_id}")

        cmd = [sys.executable, "scripts/run_experiment.py", "--config", args.base_config]
        tag = exp.get("tag")
        if tag:
            cmd += ["--tag", tag]
        for ov in overrides:
            cmd += ["--overrides", ov]

        output_root = run_output_root(overrides, runs_root)
        run_dir = os.path.join(output_root, run_id)
        summary_path = os.path.join(run_dir, "summary.json")
        resolved_path = os.path.join(run_dir, "config.resolved.yaml")
        logs_path = os.path.join(run_dir, "logs.txt")
        git_commit_path = os.path.join(run_dir, "git_commit.txt")

        proc = subprocess.run(cmd, cwd=ROOT_DIR)
        status = "ok" if proc.returncode == 0 else "failed"
        key_cfg = run_key_config(run_dir)

        row = {
            "index": idx,
            "label": exp.get("label"),
            "tag": tag,
            "run_id": run_id,
            "status": status,
            "command": cmd,
            "overrides": overrides,
            "run_dir": as_rel(run_dir),
            "summary": as_rel(summary_path),
            "resolved_config": as_rel(resolved_path),
            "logs": as_rel(logs_path),
            "git_commit_file": as_rel(git_commit_path),
            "key_config": key_cfg,
        }
        results.append(row)
        resolved_rows.append(
            {
                "label": exp.get("label"),
                "tag": tag,
                "run_id": run_id,
                "status": status,
                "run_dir": as_rel(run_dir),
                "summary": as_rel(summary_path),
                "resolved_config": as_rel(resolved_path),
                "seed": key_cfg.get("seed"),
                "retriever_mode": key_cfg.get("retriever_mode"),
                "multistep_enabled": key_cfg.get("multistep_enabled"),
                "calculator_enabled": key_cfg.get("calculator_enabled"),
                "subset_complex_path": key_cfg.get("subset_complex_path"),
                "subset_abbrev_path": key_cfg.get("subset_abbrev_path"),
                "subset_numeric_path": key_cfg.get("subset_numeric_path"),
                "overrides": overrides,
            }
        )

    matrix_payload = {
        "matrix_id": matrix_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_hash": get_git_hash(),
        "base_config": as_rel(os.path.abspath(args.base_config)),
        "matrix_config": as_rel(os.path.abspath(args.matrix)),
        "matrix_dir": as_rel(matrix_dir),
        "runs_root": as_rel(runs_root),
        "experiments": results,
    }
    matrix_json_path = os.path.join(matrix_dir, "matrix.json")
    with open(matrix_json_path, "w", encoding="utf-8") as f:
        json.dump(matrix_payload, f, indent=2)

    resolved_yaml_path = os.path.join(matrix_dir, "experiments_resolved.yaml")
    with open(resolved_yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            {
                "matrix_id": matrix_id,
                "base_config": as_rel(os.path.abspath(args.base_config)),
                "matrix_config": as_rel(os.path.abspath(args.matrix)),
                "git_hash": get_git_hash(),
                "runs_root": as_rel(runs_root),
                "experiments": resolved_rows,
            },
            f,
            sort_keys=False,
        )

    print(f"matrix_id={matrix_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
