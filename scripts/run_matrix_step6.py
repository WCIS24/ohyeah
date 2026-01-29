from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, List

import yaml

from finder_rag.utils import ensure_dir, generate_run_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Step6 experiment matrix")
    parser.add_argument("--base-config", required=True, help="Base config YAML")
    parser.add_argument("--matrix", required=True, help="Matrix YAML with experiments")
    return parser.parse_args()


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    args = parse_args()
    matrix = load_yaml(args.matrix)
    experiments = matrix.get("experiments", [])

    matrix_id = generate_run_id()
    matrix_dir = os.path.join("outputs", matrix_id)
    ensure_dir(matrix_dir)

    results = []

    for idx, exp in enumerate(experiments, start=1):
        run_id = f"{matrix_id}_m{idx:02d}"
        overrides = exp.get("overrides", [])
        overrides = list(overrides) + [f"run_id={run_id}"]

        cmd = [sys.executable, "scripts/run_experiment.py", "--config", args.base_config]
        tag = exp.get("tag")
        if tag:
            cmd += ["--tag", tag]
        for ov in overrides:
            cmd += ["--overrides", ov]

        proc = subprocess.run(cmd, cwd=os.getcwd())
        if proc.returncode != 0:
            results.append({"label": exp.get("label"), "run_id": run_id, "status": "failed"})
            continue

        summary_path = os.path.join("outputs", run_id, "summary.json")
        results.append({"label": exp.get("label"), "run_id": run_id, "summary": summary_path})

    out = {"matrix_id": matrix_id, "experiments": results}
    with open(os.path.join(matrix_dir, "matrix.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    resolved_path = os.path.join(matrix_dir, "experiments_resolved.yaml")
    with open(resolved_path, "w", encoding="utf-8") as f:
        yaml.safe_dump({"experiments": results}, f, sort_keys=False)

    print(f"matrix_id={matrix_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
