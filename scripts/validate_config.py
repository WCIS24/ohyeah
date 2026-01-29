from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from config.schema import resolve_and_validate  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and resolve config")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--output-dir", default="outputs", help="Output dir for resolved config")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = generate_run_id()
    run_dir = os.path.join(args.output_dir, run_id)
    ensure_dir(run_dir)

    log_path = os.path.join(run_dir, "logs.txt")
    logger = setup_logging(log_path)
    logger.info("command_line=%s", " ".join(sys.argv))
    logger.info("config_path=%s", args.config)

    git_hash = get_git_hash()
    logger.info("git_hash=%s", git_hash)

    resolved, resolved_path, issues = resolve_and_validate(args.config, run_dir)

    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(f"{git_hash}\n")

    logger.info("resolved_config_path=%s", resolved_path)
    if issues:
        logger.info("issues=%s", issues)
    else:
        logger.info("issues=none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
