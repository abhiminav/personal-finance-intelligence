import pandas as pd
import pytest

from pipeline import (
    prepare_transactions,
    run_pipeline,
)


def test_prepare_transactions():
    transactions = pd.DataFrame(
        {
            "date": [
                "2026-01-10",
                "2026-01-11",
            ],
            "user_id": [
                "user_001",
                "user_001",
            ],
            "amount": [
                500,
                1000,
            ],
            "category": [
                "food & dining",
                "shopping",
            ],
        }
    )

    result = prepare_transactions(
        transactions
    )

    assert len(result) == 2

    assert pd.api.types.is_datetime64_any_dtype(
        result["date"]
    )


def test_prepare_transactions_removes_non_spending():
    transactions = pd.DataFrame(
        {
            "date": [
                "2026-01-10",
                "2026-01-11",
            ],
            "user_id": [
                "user_001",
                "user_001",
            ],
            "amount": [
                500,
                -500,
            ],
            "category": [
                "food & dining",
                "salary/income",
            ],
        }
    )

    result = prepare_transactions(
        transactions
    )

    assert len(result) == 1
    assert result.iloc[0]["amount"] == 500


def test_prepare_transactions_requires_columns():
    transactions = pd.DataFrame(
        {
            "date": [
                "2026-01-10"
            ],
            "amount": [
                500
            ],
        }
    )

    with pytest.raises(ValueError):
        prepare_transactions(
            transactions
        )


def test_run_pipeline():
    transactions = pd.DataFrame(
        {
            "date": [
                "2026-01-10",
                "2026-02-10",
                "2026-03-10",
                "2026-04-10",
                "2026-05-10",
                "2026-06-10",
            ],
            "user_id": [
                "user_001",
                "user_001",
                "user_001",
                "user_001",
                "user_001",
                "user_001",
            ],
            "amount": [
                500,
                600,
                550,
                700,
                650,
                600,
            ],
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
            ],
            "merchant_id": [
                "swiggy",
                "swiggy",
                "swiggy",
                "swiggy",
                "swiggy",
                "swiggy",
            ],
            "merchant_name": [
                "Swiggy",
                "Swiggy",
                "Swiggy",
                "Swiggy",
                "Swiggy",
                "Swiggy",
            ],
        }
    )

    result = run_pipeline(
        transactions,
        user_id="user_001",
    )

    assert len(result.transactions) == 6

    assert "anomaly" in (
        result.transactions.columns
    )

    assert "anomaly_type" in (
        result.transactions.columns
    )

    assert "anomaly_score" in (
        result.transactions.columns
    )

    assert "anomaly_reason" in (
        result.transactions.columns
    )

    assert result.forecast.forecast_amount > 0


def test_run_pipeline_supports_category_forecast():
    transactions = pd.DataFrame(
        {
            "date": [
                "2026-01-10",
                "2026-02-10",
                "2026-03-10",
                "2026-04-10",
                "2026-05-10",
                "2026-06-10",
            ],
            "user_id": [
                "user_001",
                "user_001",
                "user_001",
                "user_001",
                "user_001",
                "user_001",
            ],
            "amount": [
                500,
                600,
                550,
                700,
                650,
                600,
            ],
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
                "shopping",
                "food & dining",
                "food & dining",
            ],
            "merchant_id": [
                "swiggy",
                "swiggy",
                "swiggy",
                "amazon",
                "swiggy",
                "swiggy",
            ],
            "merchant_name": [
                "Swiggy",
                "Swiggy",
                "Swiggy",
                "Amazon",
                "Swiggy",
                "Swiggy",
            ],
        }
    )

    result = run_pipeline(
        transactions,
        user_id="user_001",
        forecast_category="food & dining",
    )

    assert (
        result.forecast.category
        == "food & dining"
    )

    assert (
        result.forecast.forecast_amount
        > 0
    )


def test_run_pipeline_rejects_unknown_user():
    transactions = pd.DataFrame(
        {
            "date": [
                "2026-01-10",
                "2026-02-10",
                "2026-03-10",
            ],
            "user_id": [
                "user_001",
                "user_001",
                "user_001",
            ],
            "amount": [
                500,
                600,
                550,
            ],
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
            ],
        }
    )

    with pytest.raises(ValueError):
        run_pipeline(
            transactions,
            user_id="unknown",
        )


def test_pipeline_adds_duplicate_metadata():
    transactions = pd.DataFrame(
        [
            {
                "date": "2026-09-01",
                "user_id": "user_001",
                "amount": 500.0,
                "category": "food & dining",
                "description": "SWIGGY",
                "debit": 500.0,
                "credit": 0.0,
                "reference_number": "UPI-123",
                "merchant_id": "swiggy",
                "merchant_name": "Swiggy",
            },
            {
                "date": "2026-09-01",
                "user_id": "user_001",
                "amount": 500.0,
                "category": "food & dining",
                "description": "SWIGGY",
                "debit": 500.0,
                "credit": 0.0,
                "reference_number": "UPI-123",
                "merchant_id": "swiggy",
                "merchant_name": "Swiggy",
            },
        ]
    )

    result = run_pipeline(
        transactions,
        user_id="user_001",
    )

    assert len(result.transactions) == 2

    assert not result.transactions.iloc[0]["is_duplicate"]
    assert result.transactions.iloc[1]["is_duplicate"]

    assert not result.transactions.iloc[1][
        "is_possible_duplicate"
    ]

    assert result.transactions.iloc[1][
        "duplicate_reason"
    ] == "Matching bank transaction reference number."