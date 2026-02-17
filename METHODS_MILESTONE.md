# METHODS_MILESTONE.md

Repo audited: `https://github.com/WCIS24/ohyeah.git`  
Commit audited: `45b81432806d636558800940db33933920578541`

## 0. TL;DR

- This project is a reproducible FinDER-style financial RAG scaffold: data prep -> chunked corpus -> retrieval baseline/multistep -> optional numeric calculator -> experiment matrix/tables/figures (`README.md:3`, `README.md:39`, `README.md:91`, `README.md:118`, `README.md:140`).
- Main input is raw dataset rows mapped into `{qid, query, answer, evidences[]}` and corpus chunks with chunk metadata (`configs/prepare_data.yaml:15`, `src/data/finder.py:116`, `scripts/build_corpus.py:90`).
- Main outputs are run-scoped artifacts under `outputs/<run_id>/`, including logs/config/metrics/predictions and stage-specific files (`scripts/smoke.py:113`, `scripts/smoke.py:116`, `scripts/smoke.py:187`, `scripts/run_with_calculator.py:147`).
- Shortest reproducibility command in repo is smoke:
  - `python scripts/smoke.py --config configs/smoke.yaml` (`README.md:23`, `Makefile:12`).
- One-command orchestrated experiment entry (assuming prepared data/corpus/subsets exist):
  - `python scripts/run_experiment.py --config configs/step6_base.yaml --overrides run_id=<your_run_id>` (`scripts/run_experiment.py:30`, `scripts/run_experiment.py:81`).
- Smoke run was executed during this audit and succeeded with metrics output (`scripts/smoke.py:175`, `scripts/smoke.py:191`).

## 1. Repo Map

### 1.1 Directory tree (2-3 levels, responsibility annotated)

```text
.
|- configs/                     # YAML configs for each stage and Step6 orchestration
|  |- smoke.yaml
|  |- prepare_data.yaml
|  |- build_corpus.yaml
|  |- run_baseline.yaml
|  |- run_multistep.yaml
|  |- run_with_calculator.yaml
|  |- step6_base.yaml
|  |- step6_matrix.yaml
|  |- step6_experiments.yaml
|- scripts/                     # CLI entry points
|  |- smoke.py
|  |- prepare_data.py
|  |- build_corpus.py
|  |- eval_retrieval.py
|  |- run_baseline.py
|  |- train_retriever.py
|  |- run_multistep_retrieval.py
|  |- run_with_calculator.py
|  |- eval_numeric.py
|  |- run_experiment.py
|  |- sweep.py
|  |- run_matrix_step6.py
|  |- make_tables.py
|  |- plot_all.py
|- src/                         # Core library modules
|  |- data/finder.py
|  |- indexing/chunking.py
|  |- retrieval/retriever.py
|  |- retrieval/eval_utils.py
|  |- training/mining.py
|  |- training/pairs.py
|  |- multistep/{engine,planner,gap,refiner,stop}.py
|  |- calculator/{extract,compute}.py
|  |- config/schema.py
|  |- finder_rag/{config,logging_utils,utils,metrics}.py
|- tests/                       # Unit tests for core logic
|- docs/                        # Generated tables + design docs
|- data/ dataset/ models/ outputs/  # Runtime artifacts and data/model storage
```

Evidence: `README.md:188`, `README.md:189`, `README.md:190`, `README.md:195`, `rg --files` file list.

### 1.2 Entry points: single or multiple?

- This repo has multiple explicit entry points, not a single monolithic runner:
  - Data prep: `scripts/prepare_data.py` (`README.md:44`).
  - Corpus build: `scripts/build_corpus.py` (`README.md:50`).
  - Retrieval eval: `scripts/eval_retrieval.py` (`README.md:56`).
  - Baseline run: `scripts/run_baseline.py` (`README.md:62`).
  - Retriever FT: `scripts/mine_hard_negatives.py`, `scripts/train_retriever.py` (`README.md:79`, `README.md:82`).
  - Multistep run/eval: `scripts/run_multistep_retrieval.py`, `scripts/eval_multistep_retrieval.py` (`README.md:101`, `README.md:102`).
  - Calculator run/eval: `scripts/run_with_calculator.py`, `scripts/eval_numeric.py` (`README.md:125`, `README.md:126`).
  - Orchestrated experiments: `scripts/run_experiment.py`, `scripts/sweep.py`, `scripts/run_matrix_step6.py` (`README.md:147`, `README.md:153`, `scripts/run_experiment.py:76`).

### 1.3 Module-file mapping table

| Module | Key file | Key function/class | Purpose | Evidence |
|---|---|---|---|---|
| Config IO | `src/finder_rag/config.py` | `load_config`, `save_config` | YAML config load/save | `src/finder_rag/config.py:8`, `src/finder_rag/config.py:14` |
| Logging | `src/finder_rag/logging_utils.py` | `setup_logging` | File + console logger setup | `src/finder_rag/logging_utils.py:5`, `src/finder_rag/logging_utils.py:12`, `src/finder_rag/logging_utils.py:17` |
| Run identity | `src/finder_rag/utils.py` | `generate_run_id`, `get_git_hash` | UTC+UUID run id; commit hash capture | `src/finder_rag/utils.py:15`, `src/finder_rag/utils.py:19` |
| Data normalization | `src/data/finder.py` | `normalize_sample`, `dataset_to_records`, `split_dataset` | Canonical sample schema and split logic | `src/data/finder.py:65`, `src/data/finder.py:125`, `src/data/finder.py:140` |
| Chunking | `src/indexing/chunking.py` | `chunk_text` | Sliding window chunking | `src/indexing/chunking.py:6`, `src/indexing/chunking.py:22` |
| Hybrid retriever | `src/retrieval/retriever.py` | `HybridRetriever` | BM25+dense(+FAISS optional) retrieval | `src/retrieval/retriever.py:58`, `src/retrieval/retriever.py:79`, `src/retrieval/retriever.py:124` |
| Retrieval metrics | `src/retrieval/eval_utils.py` | `match_chunk`, `compute_retrieval_metrics` | Recall/Hit/MRR with id/text fallback matching | `src/retrieval/eval_utils.py:10`, `src/retrieval/eval_utils.py:38` |
| Hard negative mining | `src/training/mining.py` | `mine_bm25`, `select_hard_negs` | BM25 candidate mining for triplets | `src/training/mining.py:17`, `src/training/mining.py:28` |
| Pair construction | `src/training/pairs.py` | `build_corpus_index`, `build_training_pairs` | Positive chunk matching and train pair build | `src/training/pairs.py:20`, `src/training/pairs.py:64` |
| Multistep controller | `src/multistep/engine.py` | `MultiStepRetriever.run` | Step planning, gap detect, refine, stop, merge | `src/multistep/engine.py:29`, `src/multistep/engine.py:40`, `src/multistep/engine.py:199` |
| Gap/planner/refiner/stop | `src/multistep/{planner,gap,refiner,stop}.py` | `StepPlanner.plan`, `detect_gap`, `refine_query`, `StopCriteria.check` | Rule-based multistep policies | `src/multistep/planner.py:25`, `src/multistep/gap.py:51`, `src/multistep/refiner.py:19`, `src/multistep/stop.py:32` |
| Numeric extraction | `src/calculator/extract.py` | `extract_facts_from_text` | Parse number/year/unit/metric with confidence | `src/calculator/extract.py:97`, `src/calculator/extract.py:127` |
| Numeric compute | `src/calculator/compute.py` | `compute_for_query` | Task detect + yoy/diff/share/multiple compute | `src/calculator/compute.py:49`, `src/calculator/compute.py:572` |
| Config schema | `src/config/schema.py` | `resolve_config`, `validate_config`, `get_path` | Defaults, legacy mapping, type/path checks | `src/config/schema.py:10`, `src/config/schema.py:176`, `src/config/schema.py:235`, `src/config/schema.py:241` |

## 2. Environment and Reproducibility

### 2.1 Dependencies and install

- Python deps are pinned in `requirements.txt` (NumPy, pandas, scikit-learn, datasets, rank-bm25, sentence-transformers, matplotlib, etc.) (`requirements.txt:1`).
- README setup command:
  - `python -m venv .venv`
  - `.\\.venv\\Scripts\\python -m pip install -r requirements.txt` (`README.md:10`, `README.md:11`).
- `Makefile` mirrors setup and smoke/test shortcuts (`Makefile:8`, `Makefile:11`, `Makefile:14`).

### 2.2 Seed and determinism

- Most runtime scripts set both `random` and `numpy` seeds from config (example: `smoke`, `prepare_data`, `eval_retrieval`, `run_baseline`, `run_with_calculator`, `train_retriever`) (`scripts/smoke.py:123`, `scripts/prepare_data.py:76`, `scripts/eval_retrieval.py:98`, `scripts/run_with_calculator.py:116`, `scripts/train_retriever.py:171`).
- Torch deterministic flags (`torch.manual_seed`, `cudnn.deterministic`) are not set in current codebase; training reproducibility is therefore partial for GPU-level nondeterminism (`scripts/train_retriever.py:262`).

### 2.3 Git hash / run metadata capture

- Git hash utility returns full commit or `"unknown"` (`src/finder_rag/utils.py:19`).
- Scripts log command line and config path, and usually write `config.yaml` plus metrics and/or `git_commit.txt` under run dir (`scripts/smoke.py:119`, `scripts/smoke.py:187`, `scripts/eval_retrieval.py:162`, `scripts/run_with_calculator.py:326`).

### 2.4 Hardware/resource assumptions

- Retriever uses `SentenceTransformer` with optional `device` from config (`src/retrieval/retriever.py:90`).
- FAISS is optional; falls back to brute-force if unavailable (`src/retrieval/retriever.py:101`, `src/retrieval/retriever.py:109`).
- Retriever training uses PyTorch optimizer/scheduler and optional AMP fp16 if CUDA is available (`scripts/train_retriever.py:265`, `scripts/train_retriever.py:272`, `scripts/train_retriever.py:281`).

### 2.5 Output location conventions

- Standard run artifacts go to `outputs/<run_id>/` (`scripts/smoke.py:113`, `scripts/run_experiment.py:83`).
- Retriever FT model export goes to `models/retriever_ft/<run_id>` and copies to `models/retriever_ft/latest` (`scripts/train_retriever.py:316`, `scripts/train_retriever.py:320`).
- Data/output/model directories are git-ignored by default (`.gitignore:9`, `.gitignore:10`, `.gitignore:11`, `.gitignore:12`).

## 3. Data Pipeline

### 3.1 Expected raw input format in repo

- Default raw source is CSV: `dataset/finder_dataset.csv` (`configs/prepare_data.yaml:11`).
- Field mapping used by prep:
  - `qid <- _id`
  - `query <- text`
  - `answer <- answer`
  - `evidences <- references`
  - `doc_id <- null` (`configs/prepare_data.yaml:15`).
- Required columns for smoke CSV loader are `text`, `references`, `answer` (`src/finder_rag/data.py:8`).
- Normalized record schema becomes:
  - `qid: str`
  - `query: str`
  - `answer: str`
  - `evidences: [{text, doc_id, meta:{evidence_id}}]`
  - `meta.source:{...}` (`src/data/finder.py:116`).

### 3.2 Data Step Cards (execution order)

#### Step Card D1 - Load dataset and inspect schema

A) Purpose: Ingest raw dataset and serialize schema for auditability.  
B) Input: `dataset_name`/`data_files` from config (`configs/prepare_data.yaml:11`, `scripts/prepare_data.py:82`).  
C) Logic: `load_finder_dataset` picks CSV/JSON/HF load path, then `inspect_schema` dumps split feature schema (`src/data/finder.py:26`, `src/data/finder.py:19`, `scripts/prepare_data.py:94`).  
D) Output: `outputs/<run_id>/data_schema.json` (`scripts/prepare_data.py:95`).  
E) Evidence: `scripts/prepare_data.py:88`, `scripts/prepare_data.py:95`, `src/data/finder.py:37`.  
F) Checks/pitfalls: If field mapping names do not exist, prep fails fast (`scripts/prepare_data.py:51`).

#### Step Card D2 - Split train/dev/test

A) Purpose: Construct stable train/dev/test splits when raw dataset has one split.  
B) Input: Ratios and seed from config (`configs/prepare_data.yaml:4`, `configs/prepare_data.yaml:5`, `configs/prepare_data.yaml:6`, `configs/prepare_data.yaml:3`).  
C) Logic: If single split, do two-stage random split (`train_test_split` then dev/test split); if multi-split input, map `validation->dev` and keep existing (`src/data/finder.py:149`, `src/data/finder.py:165`, `src/data/finder.py:168`).  
D) Output: in-memory `DatasetDict(train/dev/test)` then JSONL files in next step (`scripts/prepare_data.py:105`).  
E) Evidence: `scripts/prepare_data.py:98`, `scripts/prepare_data.py:105`, `src/data/finder.py:169`.  
F) Checks/pitfalls: No stratification is applied; class/topic balance is not explicitly preserved (`src/data/finder.py:165`).

Code evidence snippet (split core, 11 lines):

```python
train_split = base.train_test_split(test_size=(1 - train_ratio), seed=seed)
temp = train_split["test"]
dev_size = dev_ratio / (dev_ratio + test_ratio)
dev_test = temp.train_test_split(test_size=(1 - dev_size), seed=seed)
return DatasetDict(
    {
        "train": train_split["train"],
        "dev": dev_test["train"],
        "test": dev_test["test"],
    }
)
```

Source: `src/data/finder.py:165`.

#### Step Card D3 - Normalize and write processed JSONL

A) Purpose: Convert heterogeneous raw rows to canonical JSONL format for all downstream scripts.  
B) Input: Split datasets + `field_map` (`scripts/prepare_data.py:114`).  
C) Logic: `dataset_to_records -> normalize_sample`; records without evidences are dropped (`src/data/finder.py:125`, `src/data/finder.py:135`).  
D) Output:
- `data/processed/train.jsonl`
- `data/processed/dev.jsonl`
- `data/processed/test.jsonl` (`scripts/prepare_data.py:129`).  
E) Evidence: `scripts/prepare_data.py:126`, `scripts/prepare_data.py:130`, `src/data/finder.py:100`.  
F) Checks/pitfalls: Missing `query` field raises `KeyError`; empty evidence rows are excluded (`src/data/finder.py:82`, `src/data/finder.py:37`).

#### Step Card D4 - Build chunked corpus

A) Purpose: Transform evidence texts into retrievable chunk units with traceable metadata.  
B) Input: `data/processed/*.jsonl`, `chunk_size`, `overlap` (`configs/build_corpus.yaml:2`, `configs/build_corpus.yaml:5`).  
C) Logic: For each evidence, `chunk_text` sliding windows; attach `source_qid`, `evidence_id`, and deterministic `chunk_id` (`scripts/build_corpus.py:88`, `scripts/build_corpus.py:94`, `src/indexing/chunking.py:17`).  
D) Output: `data/corpus/chunks.jsonl` (`configs/build_corpus.yaml:3`, `scripts/build_corpus.py:76`).  
E) Evidence: `scripts/build_corpus.py:67`, `scripts/build_corpus.py:76`, `scripts/build_corpus.py:97`.  
F) Checks/pitfalls:
- `overlap >= chunk_size` is invalid and throws (`src/indexing/chunking.py:11`).
- Missing split file logs warning and skips split (`scripts/build_corpus.py:80`).

#### Step Card D5 - Build dev subsets for retrieval analysis

A) Purpose: Build subset QID lists (complex / abbreviation) for focused evaluation.  
B) Input: `data/processed/dev.jsonl` and keyword list (`configs/build_subsets.yaml:2`, `configs/build_subsets.yaml:5`).  
C) Logic: Rule-based flags using multi-evidence, multi-year, compare keywords, digit+year, uppercase abbreviations (`scripts/build_subsets.py:73`, `scripts/build_subsets.py:79`, `scripts/build_subsets.py:92`).  
D) Output:
- `data/subsets/dev_complex_qids.txt`
- `data/subsets/dev_abbrev_qids.txt`
- `outputs/<run_id>/subsets_stats.json` (`scripts/build_subsets.py:96`, `scripts/build_subsets.py:101`, `scripts/build_subsets.py:117`).  
E) Evidence: `scripts/build_subsets.py:56`, `scripts/build_subsets.py:117`.  
F) Checks/pitfalls: Keyword list strongly affects subset composition; audit `complex_keywords` before reporting subset metrics (`configs/build_subsets.yaml:5`).

#### Step Card D6 - Build numeric subset for calculator eval

A) Purpose: Construct `dev_numeric_qids.txt` by numeric/question heuristics.  
B) Input: dev split records (`configs/build_numeric_subset.yaml:2`).  
C) Logic: Query/answer number regex + numeric keywords + percent symbol check (`scripts/build_numeric_subset.py:101`, `scripts/build_numeric_subset.py:103`, `scripts/build_numeric_subset.py:104`).  
D) Output:
- `data/subsets/dev_numeric_qids.txt`
- `outputs/<run_id>/numeric_subset_stats.json` (`scripts/build_numeric_subset.py:126`, `scripts/build_numeric_subset.py:135`).  
E) Evidence: `scripts/build_numeric_subset.py:115`, `scripts/build_numeric_subset.py:131`.  
F) Checks/pitfalls: Keyword table contains mojibake non-ASCII tokens in current file; this can change match behavior (`scripts/build_numeric_subset.py:34`).

### 3.3 Intermediate cache artifacts and naming

- The main pipeline does not create pickle/pt/npy caches for retrieval; intermediate artifacts are JSON/JSONL and text lists (`scripts/prepare_data.py:129`, `scripts/build_corpus.py:76`, `scripts/run_multistep_retrieval.py:166`).
- Smoke-only fallback cache: `data/finder_subset.csv` auto-downloaded from HF if configured dataset CSV is missing (`scripts/smoke.py:63`, `scripts/smoke.py:65`, `README.md:31`).

## 4. Modeling and Training

### 4.1 Model decomposition

| Submodule | Implementation | What it does | Evidence |
|---|---|---|---|
| Sparse retriever | `BM25Okapi` inside `HybridRetriever` | Token-level lexical scoring | `src/retrieval/retriever.py:83`, `src/retrieval/retriever.py:134` |
| Dense retriever | `SentenceTransformer.encode` | Embedding retrieval score | `src/retrieval/retriever.py:92`, `src/retrieval/retriever.py:115` |
| Hybrid fusion | Min-max normalized weighted sum | `combined = alpha*bm25 + (1-alpha)*dense` | `src/retrieval/retriever.py:142`, `src/retrieval/retriever.py:144` |
| Multistep planner | `StepPlanner` | Query type (COMPARE/TREND/FACT/OTHER) | `src/multistep/planner.py:25`, `src/multistep/planner.py:32` |
| Gap detector | `detect_gap` | Missing year/entity detection + confidence | `src/multistep/gap.py:51`, `src/multistep/gap.py:58` |
| Query refiner | `refine_query` | Appends missing year/entity/synonyms | `src/multistep/refiner.py:26`, `src/multistep/refiner.py:30` |
| Stopper | `StopCriteria` | EMPTY/NO_GAP/MAX_STEPS/NO_NEW_EVIDENCE stop logic | `src/multistep/stop.py:41`, `src/multistep/stop.py:43`, `src/multistep/stop.py:51` |
| Numeric extractor | `extract_facts_from_text` | Parse number/year/unit/metric with confidence | `src/calculator/extract.py:111`, `src/calculator/extract.py:131` |
| Numeric solver | `compute_for_query` | Task detect + yoy/diff/share/multiple compute | `src/calculator/compute.py:577`, `src/calculator/compute.py:639` |

### 4.2 Training objective and loss

- Retriever FT uses sentence-transformers:
  - If hard negatives enabled: `TripletLoss`.
  - Else: `MultipleNegativesRankingLoss` (`scripts/train_retriever.py:212`, `scripts/train_retriever.py:215`).
- Hard negatives are prepared as triplets from mined candidates (`scripts/mine_hard_negatives.py:95`, `scripts/train_retriever.py:70`).
- No explicit class weighting / imbalance weighting / threshold optimization appears in retriever training loop (`scripts/train_retriever.py:265`).

### 4.3 Training Step Cards

#### Step Card T1 - Mine hard negatives

A) Purpose: Build retrieval-hard triplets before FT.  
B) Input: `data/processed/train.jsonl`, `data/corpus/chunks.jsonl` (`configs/mine_hard_negatives.yaml:3`, `configs/mine_hard_negatives.yaml:4`).  
C) Logic:
- Build positive pairs by matching qid/evidence ids (`scripts/mine_hard_negatives.py:81`).
- Mine candidates with BM25 or dense retriever (`scripts/mine_hard_negatives.py:91`, `scripts/mine_hard_negatives.py:109`).
- Exclude positive chunk id, keep top `hard_k` negatives (`src/training/mining.py:37`, `src/training/mining.py:46`).  
D) Output: `data/processed/train_triplets.jsonl` + mining stats JSON (`scripts/mine_hard_negatives.py:155`, `scripts/mine_hard_negatives.py:175`).  
E) Evidence: `configs/mine_hard_negatives.yaml:5`, `scripts/mine_hard_negatives.py:157`.  
F) Checks/pitfalls: If positives are not found, samples are dropped and ratios increase in `pos_missing_ratio` (`scripts/mine_hard_negatives.py:169`).

#### Step Card T2 - Build training examples

A) Purpose: Convert triplets to sentence-transformers `InputExample`s.  
B) Input: triplets JSONL (`scripts/train_retriever.py:199`).  
C) Logic: `build_examples` emits `[query,pos,neg]` or `[query,pos]` depending on hard negative mode (`scripts/train_retriever.py:57`, `scripts/train_retriever.py:66`).  
D) Output: in-memory `examples` list + missing hard-neg ratio logged (`scripts/train_retriever.py:204`, `scripts/train_retriever.py:206`).  
E) Evidence: `configs/train_retriever.yaml:16`, `configs/train_retriever.yaml:17`.  
F) Checks/pitfalls: In hard mode, entries without negatives are skipped entirely (`scripts/train_retriever.py:67`).

#### Step Card T3 - Train loop with periodic retrieval eval

A) Purpose: Optimize retriever encoder and evaluate retrieval quality during training.  
B) Input: examples dataloader, dev records, corpus chunks (`scripts/train_retriever.py:217`, `scripts/train_retriever.py:224`).  
C) Logic:
- AdamW + linear warmup scheduler (`scripts/train_retriever.py:265`, `scripts/train_retriever.py:268`).
- Forward/backward, gradient accumulation, optimizer step (`scripts/train_retriever.py:279`, `scripts/train_retriever.py:289`).
- Evaluate every `eval_every_steps`; score is `recall@5` (`scripts/train_retriever.py:300`, `scripts/train_retriever.py:144`).
- Save best checkpoint when score improves (`scripts/train_retriever.py:302`, `scripts/train_retriever.py:304`).  
D) Output: checkpoint dirs + final model export + training metrics JSON (`scripts/train_retriever.py:245`, `scripts/train_retriever.py:316`, `scripts/train_retriever.py:338`).  
E) Evidence: `configs/train_retriever.yaml:27`, `configs/train_retriever.yaml:28`, `configs/train_retriever.yaml:14`.  
F) Checks/pitfalls:
- No gradient clipping in loop.
- No early stopping criterion besides `max_steps`/epoch end (`scripts/train_retriever.py:311`).

Code evidence snippet (core training loop, 19 lines):

```python
for epoch in range(train_cfg.num_epochs):
    for batch in train_dataloader:
        features, labels = batch
        if train_cfg.fp16 and torch.cuda.is_available():
            with torch.cuda.amp.autocast():
                loss_value = train_loss(features, labels)
            scaler.scale(loss_value).backward()
        else:
            loss_value = train_loss(features, labels)
            loss_value.backward()

        if (global_step + 1) % train_cfg.grad_accum == 0:
            if train_cfg.fp16 and torch.cuda.is_available():
                scaler.step(optimizer)
                scaler.update()
            else:
                optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
```

Source: `scripts/train_retriever.py:278`.

#### Step Card T4 - Baseline and multistep inference

A) Purpose: Produce retrieval outputs used by QA and numeric pipelines.  
B) Input: `data/processed/dev.jsonl` and corpus index (`scripts/run_baseline.py:86`, `scripts/run_baseline.py:90`, `scripts/run_multistep_retrieval.py:103`).  
C) Logic:
- Baseline: single retrieval top-k -> template answer (`scripts/run_baseline.py:133`, `scripts/run_baseline.py:135`).
- Multistep: iterative retrieve -> gap/gate/refine/stop -> merge+fallback to fill `final_top_k` (`src/multistep/engine.py:50`, `src/multistep/engine.py:103`, `src/multistep/engine.py:167`, `src/multistep/engine.py:169`).  
D) Output:
- Baseline `predictions.jsonl`
- Multistep `multistep_traces.jsonl`, `retrieval_results.jsonl` (`scripts/run_baseline.py:128`, `scripts/run_multistep_retrieval.py:166`, `scripts/run_multistep_retrieval.py:167`).  
E) Evidence: `README.md:110`, `README.md:111`.  
F) Checks/pitfalls:
- Multistep needs `top_k_final >= max(k_values)` for fair recall comparison (`README.md:116`).
- If final pool is short, baseline fallback retrieval is appended (`src/multistep/engine.py:170`).

### 4.4 Hyperparameter source and precedence

Priority from highest to lowest:

1. CLI overrides (`--split`, `--subset-qids`, `--overrides key=value`, etc.) applied first in script-specific `apply_overrides` (`scripts/eval_retrieval.py:39`, `scripts/run_multistep_retrieval.py:45`, `scripts/run_experiment.py:52`).
2. User YAML config values (`load_config`) (`scripts/run_experiment.py:78`).
3. Global defaults + legacy-key mapping from `resolve_config` (`src/config/schema.py:10`, `src/config/schema.py:176`, `src/config/schema.py:235`).

Implication: legacy flat keys like `mode`, `alpha`, `k_values`, `top_k_final` can be remapped into nested schema fields (`src/config/schema.py:209`, `src/config/schema.py:215`, `src/config/schema.py:221`).

## 5. Evaluation Protocol and Metrics

### 5.1 Data split protocol

- Default ratios are `train:0.8 / dev:0.1 / test:0.1` in prep config (`configs/prepare_data.yaml:4`, `configs/prepare_data.yaml:5`, `configs/prepare_data.yaml:6`).
- Split is seeded, random, and non-stratified (`src/data/finder.py:165`).
- Eval scripts mostly use `dev` split unless overridden (`scripts/eval_retrieval.py:103`, `scripts/run_baseline.py:87`, `scripts/eval_numeric.py:142`).

### 5.2 Best checkpoint selection / early stopping behavior

- During retriever FT, best model criterion is max `recall@5` from periodic evaluator (`scripts/train_retriever.py:144`, `scripts/train_retriever.py:302`, `scripts/train_retriever.py:304`).
- There is no explicit early-stopping patience; training ends by epoch completion or `max_steps` (`scripts/train_retriever.py:311`).

### 5.3 Metric computation details

Retrieval:

- Match policy: first by `(source_qid, evidence_id, doc_id)`, fallback by normalized text containment (`src/retrieval/eval_utils.py:23`, `src/retrieval/eval_utils.py:32`).
- Metrics per k: `recall@k`, `evidence_hit@k`, `mrr@k`, plus `uncertain_match_ratio` for fallback usage (`src/retrieval/eval_utils.py:104`, `src/retrieval/eval_utils.py:105`, `src/retrieval/eval_utils.py:106`, `src/retrieval/eval_utils.py:101`).

QA:

- `exact_match` and token-level F1 from `predictions.jsonl` vs gold split (`scripts/eval_qa.py:117`, `scripts/eval_qa.py:118`).

Numeric:

- Number extraction from answer strings uses regex and takes first number per sample for error/EM calculation (`scripts/eval_numeric.py:62`, `scripts/eval_numeric.py:178`, `scripts/eval_numeric.py:179`).
- Percent normalization mode `"auto"` can map between ratio and percent scales (`scripts/eval_numeric.py:76`, `scripts/eval_numeric.py:89`).
- Numeric EM is rounded comparison with configured tolerance (`scripts/eval_numeric.py:151`, `scripts/eval_numeric.py:195`).

### 5.4 Evaluation outputs and field definitions

| Stage | Output file | Key fields | Evidence |
|---|---|---|---|
| Retrieval eval | `metrics.json` | `recall@k`, `evidence_hit@k`, `mrr@k`, `uncertain_match_ratio` | `scripts/eval_retrieval.py:153`, `src/retrieval/eval_utils.py:97` |
| Retrieval eval | `per_query_results.jsonl` | `qid`, `first_hit_rank`, `matched_evidence_ids`, `used_fallback` | `scripts/eval_retrieval.py:157`, `src/retrieval/eval_utils.py:87` |
| Multistep eval | `metrics.json`, `per_query.jsonl` | same retrieval families, optional `use_collected` flag | `scripts/eval_multistep_retrieval.py:169`, `scripts/eval_multistep_retrieval.py:183` |
| Baseline run | `predictions.jsonl` | `qid`, `pred_answer`, `used_chunks` | `scripts/run_baseline.py:128`, `scripts/run_baseline.py:138` |
| Calculator run | `predictions_calc.jsonl` | `qid`, `pred_answer`, `used_chunks`, `R`, `fallback_reason` | `scripts/run_with_calculator.py:151`, `scripts/run_with_calculator.py:285` |
| Numeric eval | `numeric_metrics.json`, `numeric_per_query.jsonl` | coverage, numeric_em, error stats; per-q abs/rel errors | `scripts/eval_numeric.py:232`, `scripts/eval_numeric.py:154` |

## 6. Experiment Artifacts

### 6.1 Logging

- Logger format and dual handlers are centralized in `setup_logging` (`src/finder_rag/logging_utils.py:10`, `src/finder_rag/logging_utils.py:12`, `src/finder_rag/logging_utils.py:17`).
- Scripts conventionally log `command_line` and `config_path` first (`scripts/prepare_data.py:72`, `scripts/run_baseline.py:67`, `scripts/run_with_calculator.py:101`).

### 6.2 Checkpoints and model exports

- Train checkpoints:
  - `outputs/<run_id>/checkpoints/step_<global_step>`
  - `outputs/<run_id>/checkpoints/best_model` (`scripts/train_retriever.py:245`, `scripts/train_retriever.py:304`, `scripts/train_retriever.py:308`).
- Final model:
  - `models/retriever_ft/<run_id>`
  - mirrored to `models/retriever_ft/latest` (`scripts/train_retriever.py:316`, `scripts/train_retriever.py:323`).

### 6.3 Results aggregation and tables

- `run_experiment.py` writes `summary.json` and `metrics.json` in parent run dir (`scripts/run_experiment.py:301`, `scripts/run_experiment.py:305`).
- `make_tables.py` consumes `configs/step6_experiments.yaml` and writes:
  - `docs/TABLE_MAIN.md`
  - `docs/TABLE_NUMERIC.md`
  - `docs/TABLE_ABLATION.md` (`scripts/make_tables.py:87`, `scripts/make_tables.py:92`, `scripts/make_tables.py:97`).

### 6.4 Figure generation (if enabled)

- `plot_all.py` reads `scripts/plot_config.yaml`, experiments list, run summaries, and writes themed figure/table assets plus catalog/latex include snippets (`scripts/plot_all.py:545`, `scripts/plot_all.py:573`, `scripts/plot_all.py:901`, `scripts/plot_all.py:903`).
- Default output root in config is `thesis/figures` (`scripts/plot_config.yaml:1`).

## 7. From Code to Paper Methods Traceability

| Suggested paper subsection | Engineering step | Key implementation | Key hyperparams/data conventions | Evidence |
|---|---|---|---|---|
| 3.1 Data source and normalization | Raw FinDER-style ingestion -> canonical JSONL | `scripts/prepare_data.py`, `src/data/finder.py` | `field_map`, split ratios, seed | `scripts/prepare_data.py:114`, `src/data/finder.py:116`, `configs/prepare_data.yaml:15` |
| 3.2 Corpus construction | Evidence chunking into retrieval units | `scripts/build_corpus.py`, `src/indexing/chunking.py` | `chunk_size`, `overlap`, `chunk_id` pattern | `scripts/build_corpus.py:72`, `scripts/build_corpus.py:94`, `src/indexing/chunking.py:6` |
| 3.3 Hybrid retriever | BM25 + dense fusion | `src/retrieval/retriever.py` | `mode`, `alpha`, `use_faiss`, model name | `src/retrieval/retriever.py:134`, `src/retrieval/retriever.py:144`, `src/retrieval/retriever.py:101` |
| 3.4 Retriever fine-tuning | Hard negatives + sentence-transformers loss | `scripts/mine_hard_negatives.py`, `scripts/train_retriever.py` | `top_n`, `hard_k`, `learning_rate`, `eval_every_steps` | `configs/mine_hard_negatives.yaml:8`, `configs/train_retriever.yaml:8`, `scripts/train_retriever.py:300` |
| 3.5 Rule-based multistep retrieval | Plan-gap-refine-stop iterative retrieval | `src/multistep/engine.py` and helpers | `max_steps`, `top_k_each_step`, `top_k_final`, `novelty_threshold`, gate config | `src/multistep/engine.py:133`, `configs/run_multistep.yaml:16`, `src/multistep/stop.py:51` |
| 3.6 Numeric calculator | Fact extraction + symbolic compute + gate fallback | `src/calculator/extract.py`, `src/calculator/compute.py`, `scripts/run_with_calculator.py` | `output_percent`, `min_conf`, allow task types, unit/year checks | `src/calculator/extract.py:127`, `src/calculator/compute.py:639`, `scripts/run_with_calculator.py:252` |
| 4.1 Retrieval evaluation protocol | Recall/Hit/MRR with id/text matching | `src/retrieval/eval_utils.py`, `scripts/eval_retrieval.py` | `k_list`, fallback uncertainty ratio | `src/retrieval/eval_utils.py:104`, `scripts/eval_retrieval.py:132` |
| 4.2 Numeric evaluation protocol | Numeric EM + absolute/relative error | `scripts/eval_numeric.py` | `eval.numeric.tolerance`, `normalize_percent_mode` | `scripts/eval_numeric.py:151`, `scripts/eval_numeric.py:217` |
| 4.3 Experiment management | Unified run orchestration and summary | `scripts/run_experiment.py`, `scripts/sweep.py`, `scripts/run_matrix_step6.py` | `--overrides` precedence, objective/constraint in search space | `scripts/run_experiment.py:52`, `scripts/sweep.py:69`, `configs/search_space_multistep.yaml:9` |

## 8. Appendix

### A. Key executable commands (copy-ready)

1. Smoke test (required before longer runs):
   - `python scripts/smoke.py --config configs/smoke.yaml`
2. Data prep:
   - `python scripts/prepare_data.py --config configs/prepare_data.yaml`
3. Build corpus:
   - `python scripts/build_corpus.py --config configs/build_corpus.yaml`
4. Baseline retrieval eval and baseline prediction:
   - `python scripts/eval_retrieval.py --config configs/eval_retrieval.yaml`
   - `python scripts/run_baseline.py --config configs/run_baseline.yaml`
5. Retriever FT:
   - `python scripts/mine_hard_negatives.py --config configs/mine_hard_negatives.yaml`
   - `python scripts/train_retriever.py --config configs/train_retriever.yaml`
6. Multistep:
   - `python scripts/build_subsets.py --config configs/build_subsets.yaml`
   - `python scripts/run_multistep_retrieval.py --config configs/run_multistep.yaml`
   - `python scripts/eval_multistep_retrieval.py --config configs/eval_multistep.yaml --results outputs/<run_id>/retrieval_results.jsonl`
7. Calculator:
   - `python scripts/build_numeric_subset.py --config configs/build_numeric_subset.yaml`
   - `python scripts/run_with_calculator.py --config configs/run_with_calculator.yaml`
   - `python scripts/eval_numeric.py --config configs/eval_numeric.yaml --predictions outputs/<run_id>/predictions_calc.jsonl`
8. Step6 orchestration:
   - `python scripts/validate_config.py --config configs/step6_base.yaml`
   - `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix.yaml`
   - `python scripts/make_tables.py --experiments configs/step6_experiments.yaml`

Evidence: `README.md:23`, `README.md:44`, `README.md:50`, `README.md:56`, `README.md:62`, `README.md:79`, `README.md:82`, `README.md:98`, `README.md:101`, `README.md:125`, `README.md:126`, `README.md:144`, `README.md:153`, `README.md:156`.

### B. Key config checklist (defaults + override behavior)

| Config | Important defaults | Where consumed | Override path |
|---|---|---|---|
| `configs/prepare_data.yaml` | `train/dev/test=0.8/0.1/0.1`, `field_map` | `scripts/prepare_data.py` | CLI `--out-dir/--max-samples/--seed` |
| `configs/build_corpus.yaml` | `chunk_size=1000`, `overlap=100` | `scripts/build_corpus.py` | CLI `--input-dir/--output-file` |
| `configs/eval_retrieval.yaml` | `k_values=[1,5,10]`, `mode=dense` | `scripts/eval_retrieval.py` | CLI `--split/--subset-qids` |
| `configs/run_multistep.yaml` | `max_steps=3`, `top_k_final=10` | `scripts/run_multistep_retrieval.py` | CLI flags (`--max-steps`, etc.) |
| `configs/run_with_calculator.yaml` | `use_multistep_results=false`, `output_percent=true` | `scripts/run_with_calculator.py` | CLI `--use-multistep`, `--multistep-results` |
| `configs/step6_base.yaml` | integrated defaults across retriever/multistep/calculator/eval | `scripts/run_experiment.py` | `--overrides key=value` |

Evidence: `configs/prepare_data.yaml:4`, `configs/build_corpus.yaml:5`, `configs/eval_retrieval.yaml:8`, `configs/run_multistep.yaml:16`, `configs/run_with_calculator.yaml:15`, `scripts/run_experiment.py:32`.

### C. Key data structures and tensor/record conventions

| Object | Structure | Evidence |
|---|---|---|
| Processed QA record | `{"qid","query","answer","evidences":[{"text","doc_id","meta":{"evidence_id"}}],"meta":{"source":...}}` | `src/data/finder.py:116` |
| Corpus chunk record | `{"text": chunk, "meta":{"source_qid","doc_id","evidence_id","chunk_id","split"}}` | `scripts/build_corpus.py:90` |
| Retrieval result row | `{"text","score","bm25","dense","meta"}` | `src/retrieval/retriever.py:149` |
| Multistep result row | `{"qid","final_top_chunks","all_collected_chunks","stop_reason","steps_used"}` | `scripts/run_multistep_retrieval.py:204` |
| Extracted fact | `Fact(qid,chunk_id,metric,entity,year,period,value,unit,raw_span,confidence,inferred_year)` | `src/calculator/extract.py:37` |
| Calculator result | `CalcResult(qid,task_type,inputs,result_value,result_unit,explanation,confidence,status)` | `src/calculator/compute.py:28` |

### D. Open issues / minimum info needed from you

1. README command mismatch for error analysis.
   - README uses `python scripts\\error_buckets.py --config configs\\step6_experiments.yaml` (`README.md:166`), but script requires `--run-id` (`scripts/error_buckets.py:12`).
   - Please confirm intended CLI contract and preferred usage in your thesis workflow.
2. `run_calculator.py` has a runtime variable bug.
   - It logs `config.get(...)` though no `config` variable exists in scope (`scripts/run_calculator.py:98`).
   - Please confirm whether you use this script directly, or only `run_with_calculator.py`.
3. Mojibake keyword tokens appear in numeric keyword lists.
   - Present in `build_numeric_subset` and calculator task keyword arrays (`scripts/build_numeric_subset.py:34`, `src/calculator/compute.py:15`).
   - Please confirm intended multilingual keyword list encoding.
4. Figure path defaults may not match current thesis folder naming.
   - Plot config writes to `thesis/figures` (`scripts/plot_config.yaml:1`), while your working tabs show `thesis_v1/figures`.
   - Please confirm final target path used in your paper build.

---

Audit execution note:

- Smoke run executed and passed: `python scripts/smoke.py --config configs/smoke.yaml`.
- Unit tests executed and passed: `python -m pytest -q` (19 passed).
