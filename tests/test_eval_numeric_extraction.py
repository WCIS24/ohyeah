import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.eval_numeric import extract_numbers, pick_number


def test_result_tag_prefers_tagged_number() -> None:
    pred = "context 2019 details ... Result: 12.5 and extra notes"
    pred_nums = extract_numbers(pred)
    chosen, strategy_used = pick_number(pred, pred_nums, "result_tag")
    assert chosen is not None
    assert abs(float(chosen["value"]) - 12.5) < 1e-9
    assert strategy_used == "result_tag"


def test_first_strategy_matches_legacy_first_number_behavior() -> None:
    pred = "first 100 then Result: 12.5"
    pred_nums = extract_numbers(pred)
    assert pred_nums
    chosen, strategy_used = pick_number(pred, pred_nums, "first")
    assert chosen == pred_nums[0]
    assert strategy_used == "first"
