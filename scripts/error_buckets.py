from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from typing import Any, Dict, List

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Error bucket analysis")
    parser.add_argument("--run-id", default=None, help="Experiment run_id (summary.json)")
    parser.add_argument(
        "--config",
        default=None,
        help="Optional experiments yaml for batch mode (reads experiments[].run_id)",
    )
    return parser.parse_args()


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_run_ids_from_experiments(path: str) -> List[str]:
    if not os.path.exists(path):
        raise SystemExit(f"missing config: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    experiments = data.get("experiments", [])
    run_ids: List[str] = []
    for exp in experiments:
        if not isinstance(exp, dict):
            continue
        run_id = exp.get("run_id")
        if run_id:
            run_ids.append(str(run_id))
    return run_ids


def analyze_run(run_id: str) -> None:
    summary_path = os.path.join("outputs", run_id, "summary.json")
    if not os.path.exists(summary_path):
        raise SystemExit(f"missing summary: {summary_path}")

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    calc_run = summary.get("runs", {}).get("calculator")
    ms_run = summary.get("runs", {}).get("multistep")
    complex_eval = summary.get("runs", {}).get("retrieval_complex")

    numeric_buckets = Counter()
    if calc_run:
        pred_path = os.path.join("outputs", calc_run, "predictions_calc.jsonl")
        for row in load_jsonl(pred_path):
            reason = row.get("fallback_reason") or "ok"
            if reason is None:
                reason = "ok"
            if "unit" in reason:
                bucket = "unit_mismatch"
            elif "year" in reason or "inferred" in reason:
                bucket = "year_missing"
            elif "ambiguous" in reason:
                bucket = "ambiguous"
            elif "no_match" in reason:
                bucket = "parse_fail"
            elif reason == "ok":
                bucket = "ok"
            else:
                bucket = "fallback"
            numeric_buckets[bucket] += 1

    complex_buckets = Counter()
    if ms_run:
        trace_path = os.path.join("outputs", ms_run, "multistep_traces.jsonl")
        for row in load_jsonl(trace_path):
            trace = row.get("trace", [])
            stop_reason = trace[-1].get("stop_reason") if trace else "no_trace"
            if stop_reason in {"GATE_BLOCKED"}:
                bucket = "gate_block"
            elif stop_reason in {"NO_GAP"}:
                bucket = "no_gap"
            elif stop_reason in {"NO_NEW"}:
                bucket = "no_new_evidence"
            elif stop_reason in {"MAX_STEPS"}:
                bucket = "max_steps"
            else:
                bucket = stop_reason
            complex_buckets[bucket] += 1

    stats = {
        "run_id": run_id,
        "calculator_run": calc_run,
        "multistep_run": ms_run,
        "retrieval_complex_run": complex_eval,
        "numeric_buckets": dict(numeric_buckets),
        "complex_buckets": dict(complex_buckets),
    }

    out_path = os.path.join("outputs", run_id, "error_bucket_stats.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    doc_path = os.path.join("docs", "ERROR_ANALYSIS.md")
    with open(doc_path, "a", encoding="utf-8") as f:
        f.write(f"\n## Run {run_id}\n")
        f.write(f"- numeric_buckets: {dict(numeric_buckets)}\n")
        f.write(f"- complex_buckets: {dict(complex_buckets)}\n")


def main() -> int:
    args = parse_args()
    if not args.run_id and not args.config:
        raise SystemExit("provide --run-id or --config")

    run_ids: List[str] = []
    if args.run_id:
        run_ids.append(args.run_id)
    if args.config:
        run_ids.extend(load_run_ids_from_experiments(args.config))
    run_ids = list(dict.fromkeys(run_ids))
    if not run_ids:
        raise SystemExit("no run_id found")

    for run_id in run_ids:
        analyze_run(run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
