from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class RunRecord:
    role: str
    label: str
    run_id: str
    run_ref: str
    summary_path: Path
    numeric_metrics_path: Path
    numeric_per_query_path: Path
    predictions_calc_path: Path
    calc_stats_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build selective calculator closure report JSON")
    parser.add_argument("--matrix-id", required=True, help="Matrix id under outputs/<matrix_id>")
    parser.add_argument("--baseline-role", default="S0", help="Baseline role key")
    parser.add_argument(
        "--out",
        default="outputs/seal_checks/calc_selective_compare.json",
        help="Output compare JSON path",
    )
    parser.add_argument(
        "--skip-examples-out",
        default="outputs/seal_checks/calc_selective_skip_reason_examples.json",
        help="Output skip reason examples JSON path",
    )
    parser.add_argument(
        "--min-examples-per-reason",
        type=int,
        default=20,
        help="Target minimum qid examples per reason",
    )
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            rows.append(json.loads(s))
    return rows


def as_rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def mean_or_zero(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(mean(values))


def infer_role(index: int, label: str) -> str:
    lower = (label or "").lower()
    if "s0" in lower:
        return "S0"
    if "s1" in lower:
        return "S1"
    if "s2" in lower:
        return "S2"
    if "s3" in lower:
        return "S3"
    return f"S{index - 1}"


def build_record(matrix_id: str, exp: Dict[str, Any], index: int) -> RunRecord:
    run_id = str(exp.get("run_id", ""))
    run_dir = ROOT / "outputs" / matrix_id / "runs" / run_id
    return RunRecord(
        role=infer_role(index, str(exp.get("label", run_id))),
        label=str(exp.get("label", run_id)),
        run_id=run_id,
        run_ref=f"{matrix_id}/runs/{run_id}",
        summary_path=run_dir / "summary.json",
        numeric_metrics_path=ROOT
        / "outputs"
        / matrix_id
        / "runs"
        / f"{run_id}_numeric"
        / "numeric_metrics.json",
        numeric_per_query_path=ROOT
        / "outputs"
        / matrix_id
        / "runs"
        / f"{run_id}_numeric"
        / "numeric_per_query.jsonl",
        predictions_calc_path=ROOT
        / "outputs"
        / matrix_id
        / "runs"
        / f"{run_id}_calc"
        / "predictions_calc.jsonl",
        calc_stats_path=ROOT
        / "outputs"
        / matrix_id
        / "runs"
        / f"{run_id}_calc"
        / "calc_stats.json",
    )


def bucket(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {
            "count": 0,
            "coverage": 0.0,
            "em_all": 0.0,
            "em_on_covered": 0.0,
            "calculator_used_ratio": 0.0,
        }
    coverage_vals = [1.0 if bool(r.get("extracted_ok")) else 0.0 for r in rows]
    em_all_vals = [float(r.get("numeric_em", 0)) for r in rows]
    covered = [r for r in rows if bool(r.get("extracted_ok"))]
    em_cov_vals = [float(r.get("numeric_em", 0)) for r in covered]
    used_vals = [1.0 if bool(r.get("calculator_used")) else 0.0 for r in rows]
    return {
        "count": len(rows),
        "coverage": mean_or_zero(coverage_vals),
        "em_all": mean_or_zero(em_all_vals),
        "em_on_covered": mean_or_zero(em_cov_vals),
        "calculator_used_ratio": mean_or_zero(used_vals),
    }


def compute_s_calc_metrics(
    numeric_per_query: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
    needs_calc_reference: Optional[set[str]] = None,
) -> Dict[str, Any]:
    pred_by_qid = {str(r.get("qid")): r for r in predictions if r.get("qid")}
    joined: List[Dict[str, Any]] = []
    for row in numeric_per_query:
        qid = str(row.get("qid"))
        pred = pred_by_qid.get(qid)
        if pred is None:
            continue
        needs_calc_raw = pred.get("needs_calc")
        if isinstance(needs_calc_raw, bool):
            needs_calc = needs_calc_raw
        elif needs_calc_reference is not None:
            needs_calc = qid in needs_calc_reference
        else:
            needs_calc = False
        if needs_calc is not True:
            continue
        fallback_reason = pred.get("fallback_reason")
        calculator_used_raw = pred.get("calculator_used")
        if isinstance(calculator_used_raw, bool):
            calculator_used = calculator_used_raw
        else:
            calculator_used = fallback_reason in {None, ""}
        joined.append(
            {
                "qid": qid,
                "numeric_em": int(row.get("numeric_em", row.get("em", 0)) or 0),
                "extracted_ok": bool(row.get("extracted_ok", False)),
                "calculator_used": calculator_used,
                "calc_skip_reason": pred.get("calc_skip_reason"),
                "calc_skip_detail": pred.get("calc_skip_detail"),
                "fallback_reason": fallback_reason,
            }
        )

    calc_used_rows = [r for r in joined if bool(r.get("calculator_used"))]
    fallback_rows = [r for r in joined if not bool(r.get("calculator_used"))]
    calc_bucket = bucket(calc_used_rows)
    fallback_bucket = bucket(fallback_rows)
    gap = float(fallback_bucket["em_on_covered"]) - float(calc_bucket["em_on_covered"])

    skip_stage_counts: Dict[str, int] = {}
    skip_detail_counts: Dict[str, int] = {}
    for row in fallback_rows:
        stage = str(row.get("calc_skip_reason") or "fallback")
        detail = str(row.get("calc_skip_detail") or row.get("fallback_reason") or stage)
        skip_stage_counts[stage] = skip_stage_counts.get(stage, 0) + 1
        skip_detail_counts[detail] = skip_detail_counts.get(detail, 0) + 1

    return {
        "count": len(joined),
        "numeric_em": mean_or_zero([float(r.get("numeric_em", 0)) for r in joined]),
        "coverage": mean_or_zero(
            [1.0 if bool(r.get("extracted_ok")) else 0.0 for r in joined]
        ),
        "calculator_used_ratio": (
            mean_or_zero([1.0 if bool(r.get("calculator_used")) else 0.0 for r in joined])
        ),
        "calc_used": calc_bucket,
        "fallback": fallback_bucket,
        "gap_fallback_minus_calcused": gap,
        "skip_stage_counts": skip_stage_counts,
        "skip_detail_counts": skip_detail_counts,
    }


def collect_skip_examples(
    records: List[RunRecord],
    dev_by_qid: Dict[str, Dict[str, Any]],
    min_examples: int,
) -> tuple[Dict[str, Any], Dict[str, int]]:
    by_reason: Dict[str, List[Dict[str, Any]]] = {}
    for rec in records:
        if not rec.predictions_calc_path.exists():
            continue
        rows = load_jsonl(rec.predictions_calc_path)
        for row in rows:
            reason = row.get("calc_skip_reason")
            if reason in {None, ""}:
                continue
            key = str(reason)
            qid = str(row.get("qid"))
            q_meta = dev_by_qid.get(qid, {})
            item = {
                "qid": qid,
                "label": rec.label,
                "role": rec.role,
                "run_id": rec.run_id,
                "query": q_meta.get("query"),
                "calc_skip_detail": row.get("calc_skip_detail"),
                "fallback_reason": row.get("fallback_reason"),
            }
            by_reason.setdefault(key, []).append(item)

    trimmed: Dict[str, Any] = {}
    omitted: Dict[str, int] = {}
    for reason, rows in sorted(by_reason.items()):
        uniq: Dict[str, Dict[str, Any]] = {}
        for item in rows:
            uniq.setdefault(item["qid"], item)
        if len(uniq) < max(min_examples, 1):
            omitted[reason] = len(uniq)
            continue
        selected = list(uniq.values())[: max(min_examples, 1)]
        trimmed[reason] = {
            "available": len(uniq),
            "returned": len(selected),
            "examples": selected,
        }
    return trimmed, omitted


def main() -> int:
    args = parse_args()
    matrix_path = ROOT / "outputs" / args.matrix_id / "matrix.json"
    matrix = load_json(matrix_path)
    experiments = matrix.get("experiments") or []
    if not experiments:
        raise SystemExit(f"no experiments in {as_rel(matrix_path)}")

    records = [
        build_record(args.matrix_id, exp, idx)
        for idx, exp in enumerate(experiments, start=1)
    ]
    by_role = {r.role: r for r in records}
    if args.baseline_role not in by_role:
        raise SystemExit(f"baseline role not found: {args.baseline_role}")
    baseline = by_role[args.baseline_role]

    dev_rows = load_jsonl(ROOT / "data" / "processed" / "dev.jsonl")
    dev_by_qid = {str(r.get("qid")): r for r in dev_rows if r.get("qid")}

    run_payload: Dict[str, Any] = {}
    baseline_full_gap = 0.0
    baseline_subset_gap = 0.0
    needs_calc_reference: Optional[set[str]] = None

    for rec in records:
        if not rec.predictions_calc_path.exists():
            continue
        preds = load_jsonl(rec.predictions_calc_path)
        bool_rows = [row for row in preds if isinstance(row.get("needs_calc"), bool)]
        if bool_rows:
            needs_calc_reference = {
                str(row.get("qid"))
                for row in bool_rows
                if row.get("needs_calc") is True and row.get("qid")
            }
            break

    for rec in records:
        summary = load_json(rec.summary_path)
        numeric = load_json(rec.numeric_metrics_path)
        numeric_per_query = load_jsonl(rec.numeric_per_query_path)
        predictions = load_jsonl(rec.predictions_calc_path)
        calc_stats = load_json(rec.calc_stats_path)

        numeric_dev = ((summary.get("metrics") or {}).get("numeric_dev") or {})
        full_gap = float((numeric.get("fallback") or {}).get("em_on_covered") or 0.0) - float(
            (numeric.get("calc_used") or {}).get("em_on_covered") or 0.0
        )
        s_calc = compute_s_calc_metrics(
            numeric_per_query,
            predictions,
            needs_calc_reference=needs_calc_reference,
        )
        subset_gap = float(s_calc.get("gap_fallback_minus_calcused") or 0.0)

        if rec.role == baseline.role:
            baseline_full_gap = full_gap
            baseline_subset_gap = subset_gap

        run_payload[rec.role] = {
            "label": rec.label,
            "run_id": rec.run_id,
            "run_ref": rec.run_ref,
            "summary_path": as_rel(rec.summary_path),
            "numeric_metrics_path": as_rel(rec.numeric_metrics_path),
            "numeric_per_query_path": as_rel(rec.numeric_per_query_path),
            "predictions_calc_path": as_rel(rec.predictions_calc_path),
            "calc_stats_path": as_rel(rec.calc_stats_path),
            "full": {
                "numeric_em": float(numeric_dev.get("numeric_em") or 0.0),
                "coverage": float(numeric_dev.get("coverage") or 0.0),
                "fallback_ratio": float(numeric.get("fallback_ratio") or 0.0),
                "gap_fallback_minus_calcused": full_gap,
                "fallback_reason_counts": numeric.get("fallback_reason_counts") or {},
                "calc_skip_reason_counts": numeric.get("calc_skip_reason_counts") or {},
            },
            "s_calc": s_calc,
            "calc_stats_selective": (calc_stats.get("selective_stats") or {}),
        }

    baseline_row = run_payload[baseline.role]
    baseline_full = baseline_row["full"]
    baseline_subset = baseline_row["s_calc"]

    for role, row in run_payload.items():
        full = row["full"]
        subset = row["s_calc"]
        delta_full_numeric = float(full["numeric_em"]) - float(baseline_full["numeric_em"])
        delta_full_cov = float(full["coverage"]) - float(baseline_full["coverage"])
        delta_full_fallback = float(full["fallback_ratio"]) - float(baseline_full["fallback_ratio"])
        full_gap_shrink = baseline_full_gap - float(full["gap_fallback_minus_calcused"])

        delta_subset_numeric = float(subset["numeric_em"]) - float(baseline_subset["numeric_em"])
        delta_subset_cov = float(subset["coverage"]) - float(baseline_subset["coverage"])
        subset_gap_shrink = baseline_subset_gap - float(subset["gap_fallback_minus_calcused"])

        full_guardrail = delta_full_fallback <= 0.03
        full_numeric_floor = delta_full_numeric >= -0.01
        full_coverage_floor = delta_full_cov >= -0.05
        full_pass = full_guardrail and full_numeric_floor and full_coverage_floor

        subset_cond_a = delta_subset_numeric >= 0.03 and subset_gap_shrink >= 0.03
        subset_cond_b = (
            delta_subset_cov >= 0.03 and subset_gap_shrink >= 0.02 and full_guardrail
        )
        subset_pass = subset_cond_a or subset_cond_b

        row["delta_vs_baseline"] = {
            "full": {
                "numeric_em": delta_full_numeric,
                "coverage": delta_full_cov,
                "fallback_ratio": delta_full_fallback,
                "gap_shrink": full_gap_shrink,
            },
            "s_calc": {
                "numeric_em": delta_subset_numeric,
                "coverage": delta_subset_cov,
                "gap_shrink": subset_gap_shrink,
            },
        }
        row["acceptance"] = {
            "full_guardrail": full_guardrail,
            "full_numeric_floor": full_numeric_floor,
            "full_coverage_floor": full_coverage_floor,
            "full_pass": full_pass,
            "subset_condition_a": subset_cond_a,
            "subset_condition_b": subset_cond_b,
            "subset_pass": subset_pass,
            "pass": (role != baseline.role) and full_pass and subset_pass,
        }

    pass_roles = [
        role
        for role, row in run_payload.items()
        if role != baseline.role and bool((row.get("acceptance") or {}).get("pass"))
    ]
    best_subset_role = max(
        [r for r in run_payload if r != baseline.role],
        key=lambda x: float(run_payload[x]["s_calc"]["numeric_em"]),
        default=baseline.role,
    )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "matrix_id": args.matrix_id,
        "baseline": baseline.role,
        "thresholds": {
            "full_guardrail": "delta_fallback_ratio <= 0.03",
            "full_numeric_floor": "delta_numeric_em >= -0.01",
            "full_coverage_floor": "delta_coverage >= -0.05",
            "subset_condition_a": "delta_numeric_em >= 0.03 and gap_shrink >= 0.03",
            "subset_condition_b": (
                "delta_coverage >= 0.03 and gap_shrink >= 0.02 and full_guardrail"
            ),
        },
        "runs": run_payload,
        "best_subset_numeric_role": best_subset_role,
        "final_pass_candidates": pass_roles,
    }

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    selected_reasons, omitted_reasons = collect_skip_examples(
        records,
        dev_by_qid,
        int(args.min_examples_per_reason),
    )
    skip_examples = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "matrix_id": args.matrix_id,
        "min_examples_per_reason": int(args.min_examples_per_reason),
        "reasons": selected_reasons,
        "omitted_reasons_lt_min_examples": omitted_reasons,
    }
    skip_path = ROOT / args.skip_examples_out
    skip_path.parent.mkdir(parents=True, exist_ok=True)
    with skip_path.open("w", encoding="utf-8") as f:
        json.dump(skip_examples, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(as_rel(out_path))
    print(as_rel(skip_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
