from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class RunRecord:
    role: str
    label: str
    run_id: str
    run_ref: str
    summary_path: Path
    calc_stats_path: Path
    numeric_metrics_path: Path
    calc_used_records_path: Path
    numeric_per_query_path: Path
    predictions_calc_path: Path
    numeric_em: float
    coverage: float
    fallback_ratio: float
    calc_used: Dict[str, Any]
    fallback: Dict[str, Any]
    gap_fallback_minus_calcused: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build calculator closure comparison JSON")
    parser.add_argument("--matrix-id", required=True, help="Matrix id under outputs/<matrix_id>")
    parser.add_argument(
        "--out",
        default="outputs/seal_checks/calc_closure_compare.json",
        help="Output JSON path",
    )
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def as_rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def infer_role(label: str, index: int) -> str:
    lower = (label or "").lower()
    for role in ("c0", "c1", "c2", "c3"):
        if role in lower:
            return role.upper()
    return f"C{index - 1}"


def build_record(matrix_id: str, exp: Dict[str, Any], index: int) -> RunRecord:
    run_id = str(exp.get("run_id", ""))
    run_ref = f"{matrix_id}/runs/{run_id}"
    run_dir = ROOT / "outputs" / matrix_id / "runs" / run_id
    summary_path = run_dir / "summary.json"
    calc_stats_path = ROOT / "outputs" / matrix_id / "runs" / f"{run_id}_calc" / "calc_stats.json"
    numeric_metrics_path = (
        ROOT / "outputs" / matrix_id / "runs" / f"{run_id}_numeric" / "numeric_metrics.json"
    )
    calc_used_records_path = (
        ROOT / "outputs" / matrix_id / "runs" / f"{run_id}_calc" / "calc_used_records.jsonl"
    )
    numeric_per_query_path = (
        ROOT / "outputs" / matrix_id / "runs" / f"{run_id}_numeric" / "numeric_per_query.jsonl"
    )
    predictions_calc_path = (
        ROOT / "outputs" / matrix_id / "runs" / f"{run_id}_calc" / "predictions_calc.jsonl"
    )

    summary = load_json(summary_path)
    numeric_metrics = load_json(numeric_metrics_path)

    numeric_dev = ((summary.get("metrics") or {}).get("numeric_dev") or {})
    calc_used = numeric_metrics.get("calc_used") or {}
    fallback = numeric_metrics.get("fallback") or {}
    calc_cov_em = to_float(calc_used.get("em_on_covered"), to_float(numeric_metrics.get("calc_used_em")))
    fallback_cov_em = to_float(
        fallback.get("em_on_covered"), to_float(numeric_metrics.get("fallback_em"))
    )
    gap = fallback_cov_em - calc_cov_em

    return RunRecord(
        role=infer_role(str(exp.get("label", "")), index),
        label=str(exp.get("label", run_id)),
        run_id=run_id,
        run_ref=run_ref,
        summary_path=summary_path,
        calc_stats_path=calc_stats_path,
        numeric_metrics_path=numeric_metrics_path,
        calc_used_records_path=calc_used_records_path,
        numeric_per_query_path=numeric_per_query_path,
        predictions_calc_path=predictions_calc_path,
        numeric_em=to_float(numeric_dev.get("numeric_em")),
        coverage=to_float(numeric_dev.get("coverage")),
        fallback_ratio=to_float(numeric_metrics.get("fallback_ratio")),
        calc_used=calc_used,
        fallback=fallback,
        gap_fallback_minus_calcused=gap,
    )


def main() -> int:
    args = parse_args()
    matrix_id = args.matrix_id
    matrix_path = ROOT / "outputs" / matrix_id / "matrix.json"
    matrix = load_json(matrix_path)
    experiments = matrix.get("experiments") or []
    if not experiments:
        raise SystemExit(f"no experiments in {as_rel(matrix_path)}")

    records: List[RunRecord] = []
    for idx, exp in enumerate(experiments, start=1):
        records.append(build_record(matrix_id, exp, idx))

    by_role: Dict[str, RunRecord] = {r.role: r for r in records}
    baseline = by_role.get("C0", records[0])
    baseline_gap = baseline.gap_fallback_minus_calcused

    payload_runs: Dict[str, Any] = {}
    for rec in records:
        delta_numeric = rec.numeric_em - baseline.numeric_em
        delta_coverage = rec.coverage - baseline.coverage
        delta_fallback = rec.fallback_ratio - baseline.fallback_ratio
        gap_shrink = baseline_gap - rec.gap_fallback_minus_calcused
        condition_a = delta_numeric >= 0.02 and delta_coverage >= -0.03
        condition_b = (
            delta_numeric >= -0.005
            and delta_coverage >= 0.01
            and gap_shrink >= 0.05
        )
        guardrail = delta_fallback <= 0.03
        passed = rec.role != baseline.role and (condition_a or condition_b) and guardrail

        payload_runs[rec.role] = {
            "label": rec.label,
            "run_id": rec.run_id,
            "run_ref": rec.run_ref,
            "summary_path": as_rel(rec.summary_path),
            "calc_stats_path": as_rel(rec.calc_stats_path),
            "numeric_metrics_path": as_rel(rec.numeric_metrics_path),
            "calc_used_records_path": as_rel(rec.calc_used_records_path),
            "numeric_per_query_path": as_rel(rec.numeric_per_query_path),
            "predictions_calc_path": as_rel(rec.predictions_calc_path),
            "numeric_em": rec.numeric_em,
            "coverage": rec.coverage,
            "fallback_ratio": rec.fallback_ratio,
            "calc_used": rec.calc_used,
            "fallback": rec.fallback,
            "gap_fallback_minus_calcused": rec.gap_fallback_minus_calcused,
            "delta_vs_c0": {
                "numeric_em": delta_numeric,
                "coverage": delta_coverage,
                "fallback_ratio": delta_fallback,
                "gap_shrink": gap_shrink,
            },
            "acceptance": {
                "condition_a": condition_a,
                "condition_b": condition_b,
                "guardrail_fallback_ratio": guardrail,
                "pass": passed,
            },
        }

    non_baseline = [r for r in records if r.role != baseline.role]
    best_role = max(non_baseline, key=lambda r: r.numeric_em).role if non_baseline else baseline.role
    final_pass_candidates = [
        role
        for role, row in payload_runs.items()
        if role != baseline.role and bool((row.get("acceptance") or {}).get("pass"))
    ]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "matrix_id": matrix_id,
        "baseline": baseline.role,
        "thresholds": {
            "condition_a": "delta_numeric_em >= 0.02 and delta_coverage >= -0.03",
            "condition_b": (
                "delta_numeric_em >= -0.005 and delta_coverage >= 0.01 and gap_shrink >= 0.05"
            ),
            "guardrail_fallback_ratio": "delta_fallback_ratio <= 0.03",
        },
        "runs": payload_runs,
        "best_candidate_by_numeric_em": best_role,
        "final_pass_candidates": final_pass_candidates,
    }

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(as_rel(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
