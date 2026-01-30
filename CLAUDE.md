# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FinDER Financial RAG is a reproducible research project for retrieval-augmented generation systems on financial question-answering. The codebase implements a complete pipeline: baseline RAG, multi-step retrieval, calculator integration for numeric QA, retriever fine-tuning, and evaluation.

## Commands

### Setup
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
# or: make setup
```

### Testing
```powershell
python -m pytest tests/ -v
# or: make test
```

### Smoke Test (quick validation)
```powershell
python scripts\smoke.py --config configs\smoke.yaml
# or: make smoke
```

### Full Pipeline Commands
```powershell
# Data preparation + corpus
python scripts\prepare_data.py --config configs\prepare_data.yaml
python scripts\build_corpus.py --config configs\build_corpus.yaml

# Retrieval evaluation
python scripts\eval_retrieval.py --config configs\eval_retrieval.yaml

# Baseline RAG
python scripts\run_baseline.py --config configs\run_baseline.yaml

# Retriever fine-tuning
python scripts\mine_hard_negatives.py --config configs\mine_hard_negatives.yaml
python scripts\train_retriever.py --config configs\train_retriever.yaml

# Multi-step retrieval
python scripts\build_subsets.py --config configs\build_subsets.yaml
python scripts\run_multistep_retrieval.py --config configs\run_multistep.yaml
python scripts\eval_multistep_retrieval.py --config configs\eval_multistep.yaml --results outputs/<run_id>/retrieval_results.jsonl

# Calculator (numeric QA)
python scripts\build_numeric_subset.py --config configs\build_numeric_subset.yaml
python scripts\run_with_calculator.py --config configs\run_with_calculator.yaml
python scripts\eval_numeric.py --config configs\eval_numeric.yaml --predictions outputs/<run_id>/predictions_calc.jsonl
```

## Architecture

### Core Modules

**src/data/finder.py**: Dataset loader for FinDER from HF (Linq-AI-Research/FinDER). Parses evidence fields and handles normalization.

**src/retrieval/retriever.py**: Retrieval implementations:
- `TfidfRetriever`: Sparse TF-IDF retrieval
- `HybridRetriever`: Combines BM25 (sparse) and Sentence-BERT dense (all-MiniLM-L6-v2)
- `BM25Okapi`: Okapi BM25 implementation
- Supports FAISS indexing with NumPy fallback

**src/calculator/**: Numeric QA module
- `extract.py`: `extract_facts_from_text()` extracts numeric facts with year/unit detection
- `compute.py`: Handles YoY growth, difference, share, and multiple calculations

**src/multistep/**: Iterative retrieval
- `engine.py`: Manages multi-step process
- `planner.py`: Plans retrieval steps
- `refiner.py`: Query refinement
- `gap.py`: Detects information gaps
- `stop.py`: Stop criteria

**src/indexing/chunking.py**: `chunk_text()` and `chunk_evidence()` for splitting text with metadata tracking.

**src/finder_rag/metrics.py**: Evaluation metrics including `exact_match()`, `recall_at_k()`, `reciprocal_rank()`, `mrr()`.

### Configuration System

All pipeline stages use YAML configs in `configs/`. Scripts load via `src/finder_rag/config.py`.

### Output Structure

Every run writes to `outputs/</<run_id>/`:
- `config.yaml`: Full configuration
- `metrics.json`: Evaluation results
- `logs.txt`: Run logs
- `retrieval_results.jsonl`: Retrieved chunks per query
- `predictions.jsonl`: QA predictions
- `predictions_calc.jsonl`: Numeric QA predictions
- `facts.jsonl`: Extracted numeric facts
- `calc_traces.jsonl`: Calculation traces/rejection reasons
- `multistep_traces.jsonl`: Multi-step retrieval traces

## Code Style & Conventions

- Follow PEP 8, lines <= 100 chars
- Use type hints for public functions
- Use `logging` (not print) in scripts; logs go to `outputs/<run_id>/logs.txt`
- Set random seeds for reproducibility (numpy, random)
- Every run must write config.yaml, seed, git hash, and metrics to output directory
- Do NOT commit dataset files to git
- Always run smoke test before experiments
