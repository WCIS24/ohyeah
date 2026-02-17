from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate result tables")
    parser.add_argument("--experiments", required=True, help="experiments.yaml")
    return parser.parse_args()


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fmt(val: Any, digits: int = 4) -> str:
    if isinstance(val, float):
        return f"{val:.{digits}f}"
    if val is None:
        return "-"
    return str(val)


def main() -> int:
    args = parse_args()
    data = load_yaml(args.experiments)
    experiments = data.get("experiments", [])

    rows_main = []
    rows_num = []
    rows_ablation = []

    for exp in experiments:
        run_id = exp.get("run_id")
        label = exp.get("label", run_id)
        group = exp.get("group", "main")
        summary_path = os.path.join("outputs", run_id, "summary.json")
        if not os.path.exists(summary_path):
            continue
        summary = load_json(summary_path)
        metrics = summary.get("metrics", {})

        full = metrics.get("retrieval_full", {})
        complex_m = metrics.get("retrieval_complex", {})
        abbrev_m = metrics.get("retrieval_abbrev", {})
        numeric = metrics.get("numeric_dev", {})

        rows_main.append(
            {
                "label": label,
                "run_id": run_id,
                "full_r10": fmt(full.get("recall@10")),
                "full_mrr10": fmt(full.get("mrr@10")),
                "complex_r10": fmt(complex_m.get("recall@10")),
                "complex_mrr10": fmt(complex_m.get("mrr@10")),
                "abbrev_r10": fmt(abbrev_m.get("recall@10")),
                "abbrev_mrr10": fmt(abbrev_m.get("mrr@10")),
            }
        )
        rows_num.append(
            {
                "label": label,
                "run_id": run_id,
                "num_em": fmt(numeric.get("numeric_em")),
                "num_rel": fmt(numeric.get("rel_error_mean")),
                "num_cov": fmt(numeric.get("coverage")),
            }
        )
        if group == "ablation":
            rows_ablation.append(rows_main[-1])

    def write_table(path: str, headers: List[str], rows: List[Dict[str, Any]]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
            for row in rows:
                f.write("| " + " | ".join(str(row[h]) for h in headers) + " |\n")

    write_table(
        os.path.join("docs", "TABLE_MAIN.md"),
        [
            "label",
            "run_id",
            "full_r10",
            "full_mrr10",
            "complex_r10",
            "complex_mrr10",
            "abbrev_r10",
            "abbrev_mrr10",
        ],
        rows_main,
    )
    write_table(
        os.path.join("docs", "TABLE_NUMERIC.md"),
        ["label", "run_id", "num_em", "num_rel", "num_cov"],
        rows_num,
    )
    write_table(
        os.path.join("docs", "TABLE_ABLATION.md"),
        [
            "label",
            "run_id",
            "full_r10",
            "full_mrr10",
            "complex_r10",
            "complex_mrr10",
            "abbrev_r10",
            "abbrev_mrr10",
        ],
        rows_ablation,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
