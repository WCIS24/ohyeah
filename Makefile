PYTHON ?= python

.PHONY: setup smoke test
.PHONY: mine_negs train_retriever eval_retriever_pre eval_retriever_post

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
