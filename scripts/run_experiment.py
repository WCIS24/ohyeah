from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
from typing import Any, Dict, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from config.schema import (
    get_path,
    resolve_config,
    set_path,
    validate_config,
    validate_paths,
    write_resolved_config,
)
from finder_rag.config import load_config, save_config
from finder_rag.logging_utils import setup_logging
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a unified experiment")
    parser.add_argument("--config", required=True, help="Base config YAML")
    parser.add_argument("--overrides", nargs="*", default=[], help="key=value overrides")
    parser.add_argument("--tag", default=None, help="Tag for grouping")
    return parser.parse_args()


def parse_override(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        lowered = value.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value


def apply_overrides(config: Dict[str, Any], overrides: List[str]) -> Dict[str, Any]:
    for override in overrides:
        if "=" not in override:
            continue
        key, raw_val = override.split("=", 1)
        set_path(config, key, parse_override(raw_val))
    return config


def run_script(cmd: List[str], log_path: str) -> int:
    with open(log_path, "a", encoding="utf-8") as log_f:
        log_f.write(f"\n$ {' '.join(cmd)}\n")
        proc = subprocess.run(cmd, cwd=ROOT_DIR, stdout=log_f, stderr=log_f)
        return proc.returncode


def stage_config(base: Dict[str, Any], run_id: str, extras: Dict[str, Any]) -> Dict[str, Any]:
    cfg = copy.deepcopy(base)
    cfg["run_id"] = run_id
    for key, val in extras.items():
        cfg[key] = val
    return cfg


def main() -> int:
    args = parse_args()
    raw_config = load_config(args.config)
    raw_config = apply_overrides(raw_config, args.overrides)

    run_id = raw_config.get("run_id") or generate_run_id()
    output_dir = raw_config.get("output_dir", "outputs")
    run_dir = os.path.join(output_dir, run_id)
    ensure_dir(run_dir)

    log_path = os.path.join(run_dir, "logs.txt")
    logger = setup_logging(log_path)
    logger.info("command_line=%s", " ".join(sys.argv))
    logger.info("config_path=%s", args.config)
    logger.info("overrides=%s", args.overrides)

    git_hash = get_git_hash()
    logger.info("git_hash=%s", git_hash)

    resolved = resolve_config(raw_config)
    resolved_path = write_resolved_config(resolved, run_dir)
    issues = validate_config(resolved) + validate_paths(resolved)
    logger.info("resolved_config_path=%s", resolved_path)
    if issues:
        logger.info("config_issues=%s", issues)

    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(f"{git_hash}\n")

    save_config(resolved, os.path.join(run_dir, "config.yaml"))

    summary: Dict[str, Any] = {
        "run_id": run_id,
        "tag": args.tag,
        "resolved_config": resolved_path,
        "runs": {},
        "metrics": {},
    }

    multistep_enabled = bool(get_path(resolved, "multistep.enabled", False))
    calc_enabled = bool(get_path(resolved, "calculator.enabled", False))

    # Retrieval evaluation
    if multistep_enabled:
        ms_run_id = f"{run_id}_ms"
        ms_cfg = stage_config(resolved, ms_run_id, {})
        ms_cfg_path = os.path.join(run_dir, "config.ms.yaml")
        save_config(ms_cfg, ms_cfg_path)
        rc = run_script(
            [sys.executable, "scripts/run_multistep_retrieval.py", "--config", ms_cfg_path],
            log_path,
        )
        if rc != 0:
            logger.error("run_multistep failed rc=%d", rc)
            return rc

        summary["runs"]["multistep"] = ms_run_id

        eval_run_id = f"{run_id}_ms_eval_full"
        eval_cfg = stage_config(
            resolved,
            eval_run_id,
            {"results_path": f"outputs/{ms_run_id}/retrieval_results.jsonl"},
        )
        eval_cfg_path = os.path.join(run_dir, "config.ms_eval_full.yaml")
        save_config(eval_cfg, eval_cfg_path)
        rc = run_script(
            [sys.executable, "scripts/eval_multistep_retrieval.py", "--config", eval_cfg_path],
            log_path,
        )
        if rc != 0:
            logger.error("eval_multistep full failed rc=%d", rc)
            return rc
        summary["runs"]["retrieval_full"] = eval_run_id

        complex_path = get_path(resolved, "eval.subsets.complex_path")
        eval_c_run_id = f"{run_id}_ms_eval_complex"
        eval_c_cfg = stage_config(
            resolved,
            eval_c_run_id,
            {
                "results_path": f"outputs/{ms_run_id}/retrieval_results.jsonl",
                "subset_qids_path": complex_path,
            },
        )
        eval_c_cfg_path = os.path.join(run_dir, "config.ms_eval_complex.yaml")
        save_config(eval_c_cfg, eval_c_cfg_path)
        rc = run_script(
            [
                sys.executable,
                "scripts/eval_multistep_retrieval.py",
                "--config",
                eval_c_cfg_path,
                "--subset-qids",
                complex_path,
            ],
            log_path,
        )
        if rc != 0:
            logger.error("eval_multistep complex failed rc=%d", rc)
            return rc
        summary["runs"]["retrieval_complex"] = eval_c_run_id
    else:
        eval_run_id = f"{run_id}_retrieval_full"
        eval_cfg = stage_config(resolved, eval_run_id, {})
        eval_cfg_path = os.path.join(run_dir, "config.retrieval_full.yaml")
        save_config(eval_cfg, eval_cfg_path)
        rc = run_script(
            [sys.executable, "scripts/eval_retrieval.py", "--config", eval_cfg_path],
            log_path,
        )
        if rc != 0:
            logger.error("eval_retrieval full failed rc=%d", rc)
            return rc
        summary["runs"]["retrieval_full"] = eval_run_id

        complex_path = get_path(resolved, "eval.subsets.complex_path")
        eval_c_run_id = f"{run_id}_retrieval_complex"
        eval_c_cfg = stage_config(resolved, eval_c_run_id, {})
        eval_c_cfg_path = os.path.join(run_dir, "config.retrieval_complex.yaml")
        save_config(eval_c_cfg, eval_c_cfg_path)
        rc = run_script(
            [
                sys.executable,
                "scripts/eval_retrieval.py",
                "--config",
                eval_c_cfg_path,
                "--subset-qids",
                complex_path,
            ],
            log_path,
        )
        if rc != 0:
            logger.error("eval_retrieval complex failed rc=%d", rc)
            return rc
        summary["runs"]["retrieval_complex"] = eval_c_run_id

    # Calculator pipeline
    if calc_enabled:
        calc_run_id = f"{run_id}_calc"
        calc_cfg = stage_config(resolved, calc_run_id, {})
        if multistep_enabled:
            calc_cfg["use_multistep_results"] = True
            calc_cfg["multistep_results_path"] = (
                f"outputs/{summary['runs']['multistep']}/retrieval_results.jsonl"
            )
        calc_cfg_path = os.path.join(run_dir, "config.calc.yaml")
        save_config(calc_cfg, calc_cfg_path)
        rc = run_script(
            [sys.executable, "scripts/run_with_calculator.py", "--config", calc_cfg_path],
            log_path,
        )
        if rc != 0:
            logger.error("run_with_calculator failed rc=%d", rc)
            return rc
        summary["runs"]["calculator"] = calc_run_id

        numeric_path = get_path(resolved, "eval.subsets.numeric_path")
        eval_n_run_id = f"{run_id}_numeric"
        eval_n_cfg = stage_config(
            resolved,
            eval_n_run_id,
            {"predictions_path": f"outputs/{calc_run_id}/predictions_calc.jsonl"},
        )
        eval_n_cfg_path = os.path.join(run_dir, "config.numeric.yaml")
        save_config(eval_n_cfg, eval_n_cfg_path)
        rc = run_script(
            [
                sys.executable,
                "scripts/eval_numeric.py",
                "--config",
                eval_n_cfg_path,
                "--subset-qids",
                numeric_path,
            ],
            log_path,
        )
        if rc != 0:
            logger.error("eval_numeric failed rc=%d", rc)
            return rc
        summary["runs"]["numeric_dev"] = eval_n_run_id

        eval_nf_run_id = f"{run_id}_numeric_full"
        eval_nf_cfg = stage_config(
            resolved,
            eval_nf_run_id,
            {"predictions_path": f"outputs/{calc_run_id}/predictions_calc.jsonl"},
        )
        eval_nf_cfg_path = os.path.join(run_dir, "config.numeric_full.yaml")
        save_config(eval_nf_cfg, eval_nf_cfg_path)
        rc = run_script(
            [
                sys.executable,
                "scripts/eval_numeric.py",
                "--config",
                eval_nf_cfg_path,
                "--subset-qids",
                "none",
            ],
            log_path,
        )
        if rc != 0:
            logger.error("eval_numeric full failed rc=%d", rc)
            return rc
        summary["runs"]["numeric_full"] = eval_nf_run_id

    # Load metrics for summary
    def load_metrics(run_key: str, filename: str) -> Dict[str, Any]:
        run_name = summary["runs"].get(run_key)
        if not run_name:
            return {}
        path = os.path.join("outputs", run_name, filename)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    summary["metrics"]["retrieval_full"] = load_metrics("retrieval_full", "metrics.json")
    summary["metrics"]["retrieval_complex"] = load_metrics("retrieval_complex", "metrics.json")
    summary["metrics"]["numeric_dev"] = load_metrics("numeric_dev", "numeric_metrics.json")
    summary["metrics"]["numeric_full"] = load_metrics("numeric_full", "numeric_metrics.json")

    summary_path = os.path.join(run_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    metrics_path = os.path.join(run_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary["metrics"], f, indent=2)

    logger.info("summary_path=%s", summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
