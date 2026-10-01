from datetime import date

import pandas as pd

from data.deduplication import (
    detect_duplicate,
    detect_duplicates,
    flag_dataframe_duplicates,
    normalize_reference_number,
    transactions_look_identical,
)
from data.schemas import Transaction


def make_transaction(
    *,
    description: str = "SWIGGY",
    debit: float = 335.49,
    credit: float = 0.0,
    reference_number: str | None = None,
    transaction_date: date = date(2026, 9, 29),
) -> Transaction:
    return Transaction(
        date=transaction_date,
        description=description,
        debit=debit,
        credit=credit,
        balance=10000.0,
        transaction_type="debit",
        source_file="test.csv",
        reference_number=reference_number,
    )


def normalize_reference_number(
    reference_number: str | None,
) -> str | None:
    """
    Normalize a bank-provided transaction reference number.

    Bank statements may represent missing reference numbers as
    strings such as "nan", "none", or "null". These are treated
    as missing rather than as real reference numbers.
    """

    if reference_number is None:
        return None

    normalized = str(
        reference_number
    ).strip().upper()

    if not normalized:
        return None

    if normalized in {
        "NAN",
        "NONE",
        "NULL",
    }:
        return None

    return normalized

def test_normalize_empty_reference_number():
    assert normalize_reference_number(None) is None
    assert normalize_reference_number("") is None
    assert normalize_reference_number("   ") is None


def test_matching_reference_is_strong_duplicate():
    first = make_transaction(
        reference_number="UPI-123456"
    )

    second = make_transaction(
        reference_number="upi-123456"
    )

    result = detect_duplicate(
        second,
        [first],
    )

    assert result.is_duplicate is True
    assert result.is_possible_duplicate is False
    assert result.reason == (
        "Matching bank transaction reference number."
    )


def test_identical_transactions_without_reference_are_possible_duplicate():
    first = make_transaction()
    second = make_transaction()

    result = detect_duplicate(
        second,
        [first],
    )

    assert result.is_duplicate is False
    assert result.is_possible_duplicate is True
    assert result.reason == (
        "Transaction has identical date, description, "
        "debit, and credit values."
    )


def test_same_merchant_and_amount_on_different_dates_are_not_duplicate():
    first = make_transaction(
        transaction_date=date(2026, 9, 28)
    )

    second = make_transaction(
        transaction_date=date(2026, 9, 29)
    )

    result = detect_duplicate(
        second,
        [first],
    )

    assert result.is_duplicate is False
    assert result.is_possible_duplicate is False
    assert result.reason is None


def test_same_amount_and_date_but_different_description_are_not_duplicate():
    first = make_transaction(
        description="SWIGGY"
    )

    second = make_transaction(
        description="ZOMATO"
    )

    result = detect_duplicate(
        second,
        [first],
    )

    assert result.is_duplicate is False
    assert result.is_possible_duplicate is False
    assert result.reason is None


def test_transactions_look_identical():
    first = make_transaction()
    second = make_transaction()

    assert transactions_look_identical(
        first,
        second,
    ) is True


def test_different_amounts_are_not_identical():
    first = make_transaction(
        debit=335.49
    )

    second = make_transaction(
        debit=420.00
    )

    assert transactions_look_identical(
        first,
        second,
    ) is False


def test_detect_duplicates_preserves_first_occurrence():
    first = make_transaction(
        reference_number="UPI-123456"
    )

    second = make_transaction(
        reference_number="UPI-123456"
    )

    results = detect_duplicates(
        [first, second]
    )

    assert len(results) == 2

    assert results[0].is_duplicate is False
    assert results[0].is_possible_duplicate is False

    assert results[1].is_duplicate is True
    assert results[1].is_possible_duplicate is False


def test_detect_duplicates_flags_identical_rows_as_possible_duplicates():
    first = make_transaction()
    second = make_transaction()

    results = detect_duplicates(
        [first, second]
    )

    assert results[0].is_duplicate is False
    assert results[1].is_duplicate is False

    assert results[0].is_possible_duplicate is False
    assert results[1].is_possible_duplicate is True


def test_legitimate_repeated_transaction_with_same_amount_is_not_strong_duplicate():
    first = make_transaction(
        reference_number="UPI-111111"
    )

    second = make_transaction(
        reference_number="UPI-222222"
    )

    result = detect_duplicate(
        second,
        [first],
    )

    assert result.is_duplicate is False
    assert result.is_possible_duplicate is True


def test_flag_dataframe_duplicates_with_matching_reference():
    transactions = pd.DataFrame(
        [
            {
                "date": date(2026, 9, 29),
                "description": "SWIGGY",
                "debit": 335.49,
                "credit": 0.0,
                "reference_number": "UPI-123456",
            },
            {
                "date": date(2026, 9, 29),
                "description": "SWIGGY",
                "debit": 335.49,
                "credit": 0.0,
                "reference_number": "upi-123456",
            },
        ]
    )

    result = flag_dataframe_duplicates(
        transactions
    )

    assert len(result) == 2

    assert not result.iloc[0]["is_duplicate"]
    assert result.iloc[1]["is_duplicate"]

    assert not result.iloc[1]["is_possible_duplicate"]
    assert result.iloc[1]["duplicate_reason"] == (
        "Matching bank transaction reference number."
    )


def test_flag_dataframe_duplicates_without_reference():
    transactions = pd.DataFrame(
        [
            {
                "date": date(2026, 9, 29),
                "description": "SWIGGY",
                "debit": 335.49,
                "credit": 0.0,
            },
            {
                "date": date(2026, 9, 29),
                "description": "SWIGGY",
                "debit": 335.49,
                "credit": 0.0,
            },
        ]
    )

    result = flag_dataframe_duplicates(
        transactions
    )

    assert not result.iloc[0]["is_duplicate"]
    assert not result.iloc[1]["is_duplicate"]

    assert not result.iloc[0]["is_possible_duplicate"]
    assert result.iloc[1]["is_possible_duplicate"]


def test_flag_dataframe_duplicates_does_not_remove_rows():
    transactions = pd.DataFrame(
        [
            {
                "date": date(2026, 9, 29),
                "description": "SWIGGY",
                "debit": 335.49,
                "credit": 0.0,
                "reference_number": "UPI-111",
            },
            {
                "date": date(2026, 9, 29),
                "description": "SWIGGY",
                "debit": 335.49,
                "credit": 0.0,
                "reference_number": "UPI-222",
            },
        ]
    )

    result = flag_dataframe_duplicates(
        transactions
    )

    assert len(result) == 2

    assert not result.iloc[0]["is_duplicate"]
    assert not result.iloc[1]["is_duplicate"]

    assert result.iloc[1]["is_possible_duplicate"]


def test_flag_dataframe_duplicates_different_transactions():
    transactions = pd.DataFrame(
        [
            {
                "date": date(2026, 9, 29),
                "description": "SWIGGY",
                "debit": 335.49,
                "credit": 0.0,
            },
            {
                "date": date(2026, 9, 29),
                "description": "ZOMATO",
                "debit": 335.49,
                "credit": 0.0,
            },
        ]
    )

    result = flag_dataframe_duplicates(
        transactions
    )

    assert result["is_duplicate"].sum() == 0
    assert result["is_possible_duplicate"].sum() == 0


def test_flag_dataframe_duplicates_requires_columns():
    transactions = pd.DataFrame(
        [
            {
                "date": date(2026, 9, 29),
                "description": "SWIGGY",
                "debit": 335.49,
            }
        ]
    )

    try:
        flag_dataframe_duplicates(
            transactions
        )
    except ValueError as exc:
        assert "credit" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for missing columns."
        )