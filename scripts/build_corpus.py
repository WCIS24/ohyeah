from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from indexing.chunking import chunk_text  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build corpus chunks")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--input-dir", default=None, help="Override processed data dir")
    parser.add_argument("--output-file", default=None, help="Override corpus output file")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.input_dir is not None:
        config["processed_dir"] = args.input_dir
    if args.output_file is not None:
        config["corpus_file"] = args.output_file
    return config


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    config = apply_overrides(config, args)

    run_id = config.get("run_id") or generate_run_id()
    config["run_id"] = run_id
    output_dir = config.get("output_dir", "outputs")
    run_dir = os.path.join(output_dir, run_id)
    ensure_dir(run_dir)

    log_path = os.path.join(run_dir, "logs.txt")
    logger = setup_logging(log_path)
    logger.info("command_line=%s", " ".join(sys.argv))
    logger.info("config_path=%s", args.config)

    git_hash = get_git_hash()
    config["git_hash"] = git_hash
    logger.info("git_hash=%s", git_hash)

    processed_dir = config.get("processed_dir", "data/processed")
    corpus_file = config.get("corpus_file", "data/corpus/chunks.jsonl")
    ensure_dir(os.path.dirname(corpus_file))

    splits = config.get("splits", ["train", "dev", "test"])
    chunk_size = int(config.get("chunk_size", 1000))
    overlap = int(config.get("overlap", 100))

    total_chunks = 0
    with open(corpus_file, "w", encoding="utf-8") as out_f:
        for split in splits:
            path = os.path.join(processed_dir, f"{split}.jsonl")
            if not os.path.exists(path):
                logger.warning("missing split file: %s", path)
                continue
            records = load_jsonl(path)
            for rec in records:
                qid = rec.get("qid")
                for ev in rec.get("evidences", []):
                    ev_text = ev.get("text", "")
                    evidence_id = ev.get("meta", {}).get("evidence_id")
                    chunks = chunk_text(ev_text, chunk_size, overlap)
                    for idx, chunk in enumerate(chunks):
                        meta = {
                            "source_qid": qid,
                            "doc_id": ev.get("doc_id"),
                            "evidence_id": evidence_id,
                            "chunk_id": f"{qid}_e{evidence_id}_c{idx}",
                            "split": split,
                        }
                        out_f.write(json.dumps({"text": chunk, "meta": meta}) + "\n")
                        total_chunks += 1

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    logger.info("processed_dir=%s", processed_dir)
    logger.info("corpus_file=%s", corpus_file)
    logger.info("total_chunks=%d", total_chunks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
