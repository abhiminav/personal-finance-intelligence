import pandas as pd
import pytest

from forecasting.forecast import (
    forecast_category_spending,
    forecast_user_spending,
)


def test_forecast_category_spending():
    transactions = pd.DataFrame(
        {
            "date": [
                "2026-01-10",
                "2026-01-15",
                "2026-02-10",
                "2026-02-15",
                "2026-03-10",
                "2026-03-15",
            ],
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
            ],
            "amount": [
                400,
                600,
                500,
                700,
                300,
                500,
            ],
        }
    )

    result = forecast_category_spending(
        transactions,
        category="food & dining",
    )

    assert result.historical_months == 3
    assert result.average_monthly_spend == pytest.approx(
        1000.0
    )
    assert result.forecast_amount == pytest.approx(
        1000.0
    )


def test_forecast_ignores_other_categories():
    transactions = pd.DataFrame(
        {
            "date": [
                "2026-01-10",
                "2026-01-15",
                "2026-02-10",
                "2026-02-15",
                "2026-03-10",
                "2026-03-15",
            ],
            "category": [
                "food & dining",
                "shopping",
                "food & dining",
                "shopping",
                "food & dining",
                "shopping",
            ],
            "amount": [
                500,
                5000,
                500,
                5000,
                500,
                5000,
            ],
        }
    )

    result = forecast_category_spending(
        transactions,
        category="food & dining",
    )

    assert result.forecast_amount == pytest.approx(
        500.0
    )


def test_forecast_requires_history():
    transactions = pd.DataFrame(
        {
            "date": [
                "2026-01-10",
                "2026-02-10",
            ],
            "category": [
                "food & dining",
                "food & dining",
            ],
            "amount": [
                500,
                700,
            ],
        }
    )

    result = forecast_category_spending(
        transactions,
        category="food & dining",
        minimum_history=3,
    )

    assert result.historical_months == 2
    assert result.forecast_amount == 0.0


def test_forecast_empty_transactions():
    transactions = pd.DataFrame(
        columns=[
            "date",
            "category",
            "amount",
        ]
    )

    result = forecast_category_spending(
        transactions,
        category="food & dining",
    )

    assert result.historical_months == 0
    assert result.forecast_amount == 0.0


def test_forecast_rejects_missing_columns():
    transactions = pd.DataFrame(
        {
            "date": ["2026-01-10"],
            "category": ["food & dining"],
        }
    )

    with pytest.raises(ValueError):
        forecast_category_spending(
            transactions,
            category="food & dining",
        )


def test_forecast_rejects_invalid_minimum_history():
    transactions = pd.DataFrame(
        columns=[
            "date",
            "category",
            "amount",
        ]
    )

    with pytest.raises(ValueError):
        forecast_category_spending(
            transactions,
            category="food & dining",
            minimum_history=0,
        )


def test_forecast_user_spending():
    transactions = pd.DataFrame(
        {
            "user_id": [
                "user_001",
                "user_001",
                "user_001",
                "user_001",
                "user_002",
                "user_002",
            ],
            "date": [
                "2026-01-10",
                "2026-02-10",
                "2026-03-10",
                "2026-03-15",
                "2026-01-10",
                "2026-02-10",
            ],
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
                "shopping",
                "food & dining",
                "food & dining",
            ],
            "amount": [
                500,
                700,
                600,
                5000,
                9000,
                9000,
            ],
        }
    )

    result = forecast_user_spending(
        transactions,
        user_id="user_001",
        category="food & dining",
    )

    assert result.user_id == "user_001"
    assert result.category == "food & dining"
    assert result.historical_months == 3
    assert result.forecast_amount == pytest.approx(
        600.0
    )


def test_forecast_user_total_spending():
    transactions = pd.DataFrame(
        {
            "user_id": [
                "user_001",
                "user_001",
                "user_001",
                "user_001",
            ],
            "date": [
                "2026-01-10",
                "2026-02-10",
                "2026-03-10",
                "2026-03-15",
            ],
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
                "shopping",
            ],
            "amount": [
                500,
                700,
                600,
                200,
            ],
        }
    )

    result = forecast_user_spending(
        transactions,
        user_id="user_001",
    )

    assert result.category is None
    assert result.historical_months == 3
    assert result.forecast_amount == pytest.approx(
        666.6666667
    )


def test_forecast_users_are_kept_separate():
    transactions = pd.DataFrame(
        {
            "user_id": [
                "user_001",
                "user_001",
                "user_001",
                "user_002",
                "user_002",
                "user_002",
            ],
            "date": [
                "2026-01-10",
                "2026-02-10",
                "2026-03-10",
                "2026-01-10",
                "2026-02-10",
                "2026-03-10",
            ],
            "amount": [
                100,
                200,
                300,
                1000,
                2000,
                3000,
            ],
        }
    )

    result = forecast_user_spending(
        transactions,
        user_id="user_001",
    )

    assert result.forecast_amount == pytest.approx(
        200.0
    )


def test_forecast_unknown_user():
    transactions = pd.DataFrame(
        {
            "user_id": [
                "user_001",
                "user_001",
                "user_001",
            ],
            "date": [
                "2026-01-10",
                "2026-02-10",
                "2026-03-10",
            ],
            "amount": [
                100,
                200,
                300,
            ],
        }
    )

    result = forecast_user_spending(
        transactions,
        user_id="unknown",
    )

    assert result.historical_months == 0
    assert result.forecast_amount == 0.0