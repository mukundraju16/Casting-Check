import pandas as pd

from casting_check.data_cleaner import clean_number
from casting_check.validator import classify_difference, detect_total_rows, validate_totals


def test_clean_number_brackets_and_commas():
    assert clean_number("(1,234.50)") == -1234.5
    assert clean_number("1,000") == 1000.0


def test_detect_total_rows():
    df = pd.DataFrame({"item": ["A", "Subtotal", "Grand Total"], "amount": [1, 1, 2]})
    mask = detect_total_rows(df)
    assert mask.tolist() == [False, True, True]


def test_validate_totals_casting_error():
    df = pd.DataFrame({"item": ["A", "B", "Total"], "amount": [10, 20, 40]})
    out, recs = validate_totals(df, "t1", tolerance=0.01)
    assert recs[0].status == "Casting Error"
    assert out.loc[2, "status"] == "Casting Error"


def test_classify_rounding():
    assert classify_difference(0.02, 0.01) == "Decimal Rounding Difference"
