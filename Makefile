PYTHON ?= python

.PHONY: setup smoke test

setup:
	$(PYTHON) -m pip install -r requirements.txt

smoke:
	$(PYTHON) scripts/smoke.py --config configs/smoke.yaml

test:
	$(PYTHON) -m pytest -q
