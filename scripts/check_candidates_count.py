from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def percentile(values: List[int], p: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * p
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return float(values_sorted[f])
    d0 = values_sorted[f] * (c - k)
    d1 = values_sorted[c] * (k - f)
    return float(d0 + d1)


def candidate_count(row: Dict[str, Any]) -> int:
    if "final_top_chunks" in row and isinstance(row.get("final_top_chunks"), list):
        return len(row.get("final_top_chunks"))
    if "all_collected_chunks" in row and isinstance(row.get("all_collected_chunks"), list):
        return len(row.get("all_collected_chunks"))
    if "chunks" in row and isinstance(row.get("chunks"), list):
        return len(row.get("chunks"))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize candidate counts in retrieval results")
    parser.add_argument("--results", required=True, help="Path to retrieval_results.jsonl")
    parser.add_argument("--out-dir", default=None, help="Output directory (default: results parent)")
    parser.add_argument("--k", type=int, default=10, help="Target k for Recall@k checks")
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        raise SystemExit(f"missing results file: {results_path}")

    out_dir = Path(args.out_dir) if args.out_dir else results_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "logs.txt"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(log_path, mode="a", encoding="utf-8")],
    )
    logging.info("command_line=%s", " ".join(sys.argv))
    logging.info("results_path=%s out_dir=%s k=%d", results_path, out_dir, args.k)

    rows = load_jsonl(results_path)
    counts = [candidate_count(r) for r in rows]

    summary = {
        "results_path": str(results_path),
        "num_queries": len(rows),
        "min": min(counts) if counts else 0,
        "max": max(counts) if counts else 0,
        "mean": float(statistics.mean(counts)) if counts else 0.0,
        "p50": percentile(counts, 0.50),
        "p95": percentile(counts, 0.95),
        "below_k": sum(1 for c in counts if c < args.k),
        "k": args.k,
    }

    summary_path = out_dir / "candidate_count_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    report_lines = [
        "# Candidate Count Report",
        "",
        f"results_path: {results_path}",
        f"num_queries: {summary['num_queries']}",
        f"min/mean/p50/p95/max: {summary['min']}/{summary['mean']:.3f}/{summary['p50']:.1f}/{summary['p95']:.1f}/{summary['max']}",
        f"k={summary['k']} below_k: {summary['below_k']}",
        "",
    ]

    if summary["below_k"] > 0:
        report_lines.append(
            "Note: Some queries have fewer candidates than k; Recall@k may be truncated. "
            "Consider increasing top_k_final or preserving more candidates during merging."
        )
    else:
        report_lines.append("All queries have >= k candidates; no Recall@k truncation detected.")

    report_path = out_dir / "candidate_count_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    logging.info(
        "summary_path=%s report_path=%s below_k=%d",
        summary_path,
        report_path,
        summary["below_k"],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
