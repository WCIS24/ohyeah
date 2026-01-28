PYTHON ?= python

.PHONY: setup smoke test
.PHONY: mine_negs train_retriever eval_retriever_pre eval_retriever_post build_subsets run_multistep eval_multistep
.PHONY: build_numeric_subset extract_facts run_calculator run_baseline_calc run_multistep_calc eval_numeric

setup:
	$(PYTHON) -m pip install -r requirements.txt

smoke:
	$(PYTHON) scripts/smoke.py --config configs/smoke.yaml

test:
	$(PYTHON) -m pytest -q

mine_negs:
	$(PYTHON) scripts/mine_hard_negatives.py --config configs/mine_hard_negatives.yaml

train_retriever:
	$(PYTHON) scripts/train_retriever.py --config configs/train_retriever.yaml

eval_retriever_pre:
	$(PYTHON) scripts/eval_retrieval.py --config configs/eval_retrieval.yaml

eval_retriever_post:
	$(PYTHON) scripts/eval_retrieval.py --config configs/eval_retrieval.yaml

build_subsets:
	$(PYTHON) scripts/build_subsets.py --config configs/build_subsets.yaml

run_multistep:
	$(PYTHON) scripts/run_multistep_retrieval.py --config configs/run_multistep.yaml

eval_multistep:
	$(PYTHON) scripts/eval_multistep_retrieval.py --config configs/eval_multistep.yaml

build_numeric_subset:
	$(PYTHON) scripts/build_numeric_subset.py --config configs/build_numeric_subset.yaml

extract_facts:
	$(PYTHON) scripts/extract_facts.py --config configs/extract_facts.yaml

run_calculator:
	$(PYTHON) scripts/run_calculator.py --config configs/run_calculator.yaml

run_baseline_calc:
	$(PYTHON) scripts/run_with_calculator.py --config configs/run_with_calculator.yaml

MULTISTEP_RESULTS ?= outputs/<run_id>/retrieval_results.jsonl
run_multistep_calc:
	$(PYTHON) scripts/run_with_calculator.py --config configs/run_with_calculator.yaml --use-multistep 1 --multistep-results $(MULTISTEP_RESULTS)

PREDICTIONS ?= outputs/<run_id>/predictions_calc.jsonl
eval_numeric:
	$(PYTHON) scripts/eval_numeric.py --config configs/eval_numeric.yaml --predictions $(PREDICTIONS)
