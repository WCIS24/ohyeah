import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.eval_numeric import extract_numbers, normalize_percent_mode


def test_percent_normalization() -> None:
    gold = extract_numbers("12%")
    pred = extract_numbers("0.12")
    assert gold and pred
    adj = normalize_percent_mode(gold[0], pred[0], "auto")
    assert abs(adj - 12.0) < 1e-6
