from calculator.extract import extract_facts_from_text


def test_extract_numbers() -> None:
    text = "Revenue was $1,234.5 million. Margin was 12%. Profit 1.2 billion."
    facts = extract_facts_from_text("q1", "c1", text, "Revenue 2020", [2020])
    values = [f.value for f in facts]

    assert any(abs(v - 1.2345e9) < 1e-3 for v in values)
    percent_facts = [f for f in facts if f.unit == "%"]
    assert percent_facts
    assert abs(percent_facts[0].value - 12.0) < 1e-6
    assert any(abs(v - 1.2e9) < 1e-3 for v in values)
