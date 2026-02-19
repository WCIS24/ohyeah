from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build calculator diagnosis metrics")
    parser.add_argument(
        "--out",
        default="outputs/seal_checks/calc_diagnosis_metrics.json",
        help="Output JSON path",
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


def mean(vals: Iterable[float]) -> Optional[float]:
    arr = list(vals)
    if not arr:
        return None
    return sum(arr) / len(arr)


def detect_expected_task(query: str) -> Optional[str]:
    q = (query or "").lower()
    yoy_kw = ["yoy", "year over year", "growth", "increase", "decrease"]
    diff_kw = ["difference", "change", "delta", "diff"]
    share_kw = ["share", "percentage", "portion"]
    mult_kw = ["times", "multiple"]
    if any(k in q for k in yoy_kw):
        return "yoy"
    if any(k in q for k in diff_kw):
        return "diff"
    if any(k in q for k in share_kw):
        return "share"
    if any(k in q for k in mult_kw):
        return "multiple"
    return None


def classify_error(
    *,
    q_meta: Dict[str, Any],
    pred: Dict[str, Any],
    perq: Dict[str, Any],
) -> str:
    numeric_em = int(perq.get("numeric_em", 0))
    extracted_ok = bool(perq.get("extracted_ok", False))
    if numeric_em == 1:
        return "correct"
    if not extracted_ok:
        return "extraction_mismatch"

    result = pred.get("R", {}) if isinstance(pred.get("R"), dict) else {}
    fallback_reason = pred.get("fallback_reason")
    status = str(result.get("status", ""))
    task_type = str(result.get("task_type", ""))
    inputs = result.get("inputs", []) if isinstance(result.get("inputs"), list) else []

    if status == "unit_mismatch" or fallback_reason in {"gate_unit", "status_unit_mismatch"}:
        return "unit_mismatch"

    expected_task = detect_expected_task(str(q_meta.get("query", "")))
    if expected_task and task_type and task_type not in {"unknown", expected_task}:
        return "wrong_op"

    if fallback_reason is None:
        # Calculator was used; most misses are from selecting wrong numbers/facts.
        values = [v.get("value") for v in inputs if isinstance(v, dict)]
        has_year_like_value = any(
            isinstance(v, (int, float)) and 1900 <= abs(float(v)) <= 2100 for v in values
        )
        if has_year_like_value:
            return "wrong_fact"
        return "wrong_fact"

    if str(fallback_reason).startswith("status_") or fallback_reason in {
        "gate_task",
        "gate_conf",
        "gate_year",
        "gate_inferred",
    }:
        return "wrong_fact"
    return "wrong_op"


def bucket_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {
            "count": 0,
            "coverage": None,
            "em_all": None,
            "em_on_covered": None,
            "error_type_counts": {},
        }
    coverage_vals = [1.0 if bool(r["extracted_ok"]) else 0.0 for r in rows]
    em_all_vals = [float(r["numeric_em"]) for r in rows]
    covered_rows = [r for r in rows if bool(r["extracted_ok"])]
    em_cov_vals = [float(r["numeric_em"]) for r in covered_rows]
    err_counter = Counter(str(r["error_type"]) for r in rows)
    return {
        "count": n,
        "coverage": mean(coverage_vals),
        "em_all": mean(em_all_vals),
        "em_on_covered": mean(em_cov_vals) if em_cov_vals else None,
        "error_type_counts": dict(err_counter),
    }


@dataclass
class RunInput:
    name: str
    run_ref: str
    predictions_calc: str
    numeric_per_query: str
    summary: str
    calc_stats: str
    numeric_metrics: str


def run_specs() -> List[RunInput]:
    specs = [
        RunInput(
            name="m08_allow_yoy_diff",
            run_ref="20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08",
            predictions_calc=(
                "outputs/20260217_123645_68f6b9/runs/"
                "20260217_123645_68f6b9_m08_calc/predictions_calc.jsonl"
            ),
            numeric_per_query=(
                "outputs/20260217_123645_68f6b9/runs/"
                "20260217_123645_68f6b9_m08_numeric/numeric_per_query.jsonl"
            ),
            summary="outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json",
            calc_stats=(
                "outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_calc/"
                "calc_stats.json"
            ),
            numeric_metrics=(
                "outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_numeric/"
                "numeric_metrics.json"
            ),
        ),
        RunInput(
            name="m08d_expand_tasks",
            run_ref="20260218_032001_2056e7/runs/20260218_032001_2056e7_m03",
            predictions_calc=(
                "outputs/20260218_032001_2056e7/runs/"
                "20260218_032001_2056e7_m03_calc/predictions_calc.jsonl"
            ),
            numeric_per_query=(
                "outputs/20260218_032001_2056e7/runs/"
                "20260218_032001_2056e7_m03_numeric/numeric_per_query.jsonl"
            ),
            summary="outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m03/summary.json",
            calc_stats=(
                "outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m03_calc/"
                "calc_stats.json"
            ),
            numeric_metrics=(
                "outputs/20260218_032001_2056e7/runs/20260218_032001_2056e7_m03_numeric/"
                "numeric_metrics.json"
            ),
        ),
        RunInput(
            name="m13_pqe_calc",
            run_ref="20260218_160058_ee7290/runs/20260218_160058_ee7290_m04",
            predictions_calc=(
                "outputs/20260218_160058_ee7290/runs/"
                "20260218_160058_ee7290_m04_calc/predictions_calc.jsonl"
            ),
            numeric_per_query=(
                "outputs/20260218_160058_ee7290/runs/"
                "20260218_160058_ee7290_m04_numeric/numeric_per_query.jsonl"
            ),
            summary="outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04/summary.json",
            calc_stats=(
                "outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04_calc/"
                "calc_stats.json"
            ),
            numeric_metrics=(
                "outputs/20260218_160058_ee7290/runs/20260218_160058_ee7290_m04_numeric/"
                "numeric_metrics.json"
            ),
        ),
    ]

    diag_candidates = [
        RunInput(
            name="calc_diag_m13_baseline_new",
            run_ref="20260219_011425_65f019/runs/20260219_011425_65f019_m01",
            predictions_calc=(
                "outputs/20260219_011425_65f019/runs/"
                "20260219_011425_65f019_m01_calc/predictions_calc.jsonl"
            ),
            numeric_per_query=(
                "outputs/20260219_011425_65f019/runs/"
                "20260219_011425_65f019_m01_numeric/numeric_per_query.jsonl"
            ),
            summary="outputs/20260219_011425_65f019/runs/20260219_011425_65f019_m01/summary.json",
            calc_stats=(
                "outputs/20260219_011425_65f019/runs/20260219_011425_65f019_m01_calc/"
                "calc_stats.json"
            ),
            numeric_metrics=(
                "outputs/20260219_011425_65f019/runs/20260219_011425_65f019_m01_numeric/"
                "numeric_metrics.json"
            ),
        ),
        RunInput(
            name="calc_diag_m13_fact_top3_new",
            run_ref="20260219_011425_65f019/runs/20260219_011425_65f019_m02",
            predictions_calc=(
                "outputs/20260219_011425_65f019/runs/"
                "20260219_011425_65f019_m02_calc/predictions_calc.jsonl"
            ),
            numeric_per_query=(
                "outputs/20260219_011425_65f019/runs/"
                "20260219_011425_65f019_m02_numeric/numeric_per_query.jsonl"
            ),
            summary="outputs/20260219_011425_65f019/runs/20260219_011425_65f019_m02/summary.json",
            calc_stats=(
                "outputs/20260219_011425_65f019/runs/20260219_011425_65f019_m02_calc/"
                "calc_stats.json"
            ),
            numeric_metrics=(
                "outputs/20260219_011425_65f019/runs/20260219_011425_65f019_m02_numeric/"
                "numeric_metrics.json"
            ),
        ),
    ]
    for candidate in diag_candidates:
        if (ROOT / candidate.summary).exists():
            specs.append(candidate)
    return specs


def main() -> int:
    args = parse_args()
    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    dev_path = ROOT / "data" / "processed" / "dev.jsonl"
    dev_rows = load_jsonl(dev_path)
    dev_by_qid = {str(r.get("qid")): r for r in dev_rows if r.get("qid")}

    payload: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "dev_path": str(dev_path.relative_to(ROOT)).replace("\\", "/"),
            "strategy_compare": "outputs/seal_checks/numeric_extraction_strategy_compare.json",
        },
        "runs": {},
        "comparisons": {},
    }

    for spec in run_specs():
        pred_path = ROOT / spec.predictions_calc
        perq_path = ROOT / spec.numeric_per_query
        summary_path = ROOT / spec.summary
        calc_stats_path = ROOT / spec.calc_stats
        numeric_metrics_path = ROOT / spec.numeric_metrics

        preds = load_jsonl(pred_path)
        perq = load_jsonl(perq_path)
        pred_by_qid = {str(r.get("qid")): r for r in preds if r.get("qid")}
        perq_by_qid = {str(r.get("qid")): r for r in perq if r.get("qid")}

        joined_rows: List[Dict[str, Any]] = []
        missing_preds = 0
        for qid, pq in perq_by_qid.items():
            pred = pred_by_qid.get(qid)
            if pred is None:
                missing_preds += 1
                continue
            q_meta = dev_by_qid.get(qid, {})
            fallback_reason = pred.get("fallback_reason")
            calc_used = fallback_reason is None
            extracted_ok = bool(pq.get("extracted_ok", False))
            numeric_em = int(pq.get("numeric_em", pq.get("em", 0)) or 0)
            err = classify_error(q_meta=q_meta, pred=pred, perq=pq)
            joined_rows.append(
                {
                    "qid": qid,
                    "calc_used": calc_used,
                    "fallback_reason": fallback_reason,
                    "numeric_em": numeric_em,
                    "extracted_ok": extracted_ok,
                    "error_type": err,
                    "task_type": (pred.get("R", {}) or {}).get("task_type"),
                    "status": (pred.get("R", {}) or {}).get("status"),
                }
            )

        calc_rows = [r for r in joined_rows if r["calc_used"]]
        fallback_rows = [r for r in joined_rows if not r["calc_used"]]
        split = {
            "calc_used": bucket_metrics(calc_rows),
            "fallback": bucket_metrics(fallback_rows),
        }

        by_reason: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in fallback_rows:
            by_reason[str(r["fallback_reason"])].append(r)

        by_reason_metrics = {reason: bucket_metrics(rows) for reason, rows in sorted(by_reason.items())}

        task_counter = Counter(str(r.get("task_type")) for r in joined_rows)
        status_counter = Counter(str(r.get("status")) for r in joined_rows)
        error_counter = Counter(str(r.get("error_type")) for r in joined_rows)

        run_obj = {
            "run_ref": spec.run_ref,
            "files": {
                "predictions_calc": spec.predictions_calc,
                "numeric_per_query": spec.numeric_per_query,
                "summary": spec.summary,
                "calc_stats": spec.calc_stats,
                "numeric_metrics": spec.numeric_metrics,
            },
            "join": {
                "numeric_rows": len(perq_by_qid),
                "pred_rows": len(pred_by_qid),
                "joined_rows": len(joined_rows),
                "missing_predictions_for_numeric_rows": missing_preds,
            },
            "overall": bucket_metrics(joined_rows),
            "split": split,
            "by_fallback_reason": by_reason_metrics,
            "task_type_counts": dict(task_counter),
            "status_counts": dict(status_counter),
            "error_type_counts": dict(error_counter),
            "raw_numeric_metrics": load_json(numeric_metrics_path),
            "raw_calc_stats": load_json(calc_stats_path),
            "raw_summary_numeric_dev": (
                load_json(summary_path).get("metrics", {}).get("numeric_dev", {})
            ),
        }
        payload["runs"][spec.name] = run_obj

    def run_val(run_name: str, path: List[str]) -> Optional[float]:
        cur: Any = payload["runs"].get(run_name, {})
        for p in path:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(p)
        return float(cur) if isinstance(cur, (int, float)) else None

    comparisons = {}
    pairs = [
        ("m13_vs_m08", "m13_pqe_calc", "m08_allow_yoy_diff"),
        ("m13_vs_m08d", "m13_pqe_calc", "m08d_expand_tasks"),
        (
            "diag_top3_vs_diag_base",
            "calc_diag_m13_fact_top3_new",
            "calc_diag_m13_baseline_new",
        ),
    ]
    for key, a, b in pairs:
        if a not in payload["runs"] or b not in payload["runs"]:
            continue
        comparisons[key] = {
            "overall_coverage_delta": (
                (run_val(a, ["overall", "coverage"]) or 0.0)
                - (run_val(b, ["overall", "coverage"]) or 0.0)
            ),
            "overall_em_all_delta": (
                (run_val(a, ["overall", "em_all"]) or 0.0)
                - (run_val(b, ["overall", "em_all"]) or 0.0)
            ),
            "calc_used_em_all_delta": (
                (run_val(a, ["split", "calc_used", "em_all"]) or 0.0)
                - (run_val(b, ["split", "calc_used", "em_all"]) or 0.0)
            ),
            "fallback_em_all_delta": (
                (run_val(a, ["split", "fallback", "em_all"]) or 0.0)
                - (run_val(b, ["split", "fallback", "em_all"]) or 0.0)
            ),
            "calc_used_count_delta": (
                (run_val(a, ["split", "calc_used", "count"]) or 0.0)
                - (run_val(b, ["split", "calc_used", "count"]) or 0.0)
            ),
            "fallback_count_delta": (
                (run_val(a, ["split", "fallback", "count"]) or 0.0)
                - (run_val(b, ["split", "fallback", "count"]) or 0.0)
            ),
        }
    payload["comparisons"] = comparisons

    first_perq_path = ROOT / "outputs" / "seal_a2_numeric_first" / "numeric_per_query.jsonl"
    tag_perq_path = ROOT / "outputs" / "seal_a2_numeric_result_tag" / "numeric_per_query.jsonl"
    if first_perq_path.exists() and tag_perq_path.exists():
        first_rows = load_jsonl(first_perq_path)
        tag_rows = load_jsonl(tag_perq_path)
        first_by_qid = {str(r.get("qid")): r for r in first_rows if r.get("qid")}
        tag_by_qid = {str(r.get("qid")): r for r in tag_rows if r.get("qid")}
        common_qids = sorted(set(first_by_qid).intersection(tag_by_qid))

        pred_diff_rows: List[Dict[str, Any]] = []
        strategy_diff_rows: List[Dict[str, Any]] = []
        for qid in common_qids:
            a = first_by_qid[qid]
            b = tag_by_qid[qid]
            pred_a = a.get("pred_num", a.get("pred_number"))
            pred_b = b.get("pred_num", b.get("pred_number"))
            em_a = int(a.get("numeric_em", a.get("em", 0)) or 0)
            em_b = int(b.get("numeric_em", b.get("em", 0)) or 0)
            sa = str(a.get("strategy_used", ""))
            sb = str(b.get("strategy_used", ""))
            row = {
                "qid": qid,
                "pred_first": pred_a,
                "pred_result_tag": pred_b,
                "em_first": em_a,
                "em_result_tag": em_b,
                "strategy_used_first": sa,
                "strategy_used_result_tag": sb,
                "pred_text_snippet": b.get("pred_text_snippet") or a.get("pred_text_snippet"),
            }
            if sa != sb:
                strategy_diff_rows.append(row)
            if pred_a != pred_b:
                pred_diff_rows.append(row)

        both_wrong = [r for r in pred_diff_rows if r["em_first"] == 0 and r["em_result_tag"] == 0]
        first_only = [r for r in pred_diff_rows if r["em_first"] == 1 and r["em_result_tag"] == 0]
        tag_only = [r for r in pred_diff_rows if r["em_first"] == 0 and r["em_result_tag"] == 1]
        payload["strategy_compare_detail"] = {
            "files": {
                "first_per_query": "outputs/seal_a2_numeric_first/numeric_per_query.jsonl",
                "result_tag_per_query": "outputs/seal_a2_numeric_result_tag/numeric_per_query.jsonl",
            },
            "common_qid_count": len(common_qids),
            "strategy_changed_qid_count": len(strategy_diff_rows),
            "pred_number_changed_qid_count": len(pred_diff_rows),
            "both_wrong_when_pred_changed": len(both_wrong),
            "first_correct_result_tag_wrong": len(first_only),
            "result_tag_correct_first_wrong": len(tag_only),
            "pred_changed_examples_top20": pred_diff_rows[:20],
        }

    strategy_compare_path = ROOT / "outputs" / "seal_checks" / "numeric_extraction_strategy_compare.json"
    if strategy_compare_path.exists():
        payload["strategy_compare"] = load_json(strategy_compare_path)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"wrote={out_path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
