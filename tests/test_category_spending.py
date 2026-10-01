import pandas as pd
import pytest

from anomaly.category_spending import (
    build_monthly_category_baselines,
    flag_category_spending,
)


def test_monthly_category_baseline():
    transactions = pd.DataFrame(
        [
            {
                "user_id": "user_001",
                "date": "2026-01-10",
                "category": "transport",
                "amount": 100,
            },
            {
                "user_id": "user_001",
                "date": "2026-01-20",
                "category": "transport",
                "amount": 200,
            },
            {
                "user_id": "user_001",
                "date": "2026-02-10",
                "category": "transport",
                "amount": 300,
            },
            {
                "user_id": "user_001",
                "date": "2026-02-20",
                "category": "transport",
                "amount": 100,
            },
        ]
    )

    baselines = build_monthly_category_baselines(
        transactions
    )

    baseline = baselines[
        ("user_001", "transport")
    ]

    assert baseline.historical_months == 2
    assert baseline.median_monthly_spend == 350.0
    assert baseline.mad_monthly_spend == 50.0


def test_negative_amounts_are_excluded():
    transactions = pd.DataFrame(
        [
            {
                "user_id": "user_001",
                "date": "2026-01-10",
                "category": "transport",
                "amount": 500,
            },
            {
                "user_id": "user_001",
                "date": "2026-01-15",
                "category": "transport",
                "amount": -500,
            },
        ]
    )

    baselines = build_monthly_category_baselines(
        transactions
    )

    baseline = baselines[
        ("user_001", "transport")
    ]

    assert baseline.median_monthly_spend == 500.0
    assert baseline.mad_monthly_spend == 0.0


def test_missing_columns_raise_error():
    transactions = pd.DataFrame(
        [
            {
                "user_id": "user_001",
                "category": "transport",
                "amount": 500,
            }
        ]
    )

    with pytest.raises(ValueError):
        build_monthly_category_baselines(
            transactions
        )


def test_empty_dataframe_returns_empty_dict():
    transactions = pd.DataFrame(
        columns=[
            "user_id",
            "date",
            "category",
            "amount",
        ]
    )

    assert (
        build_monthly_category_baselines(
            transactions
        )
        == {}
    )


def test_category_spending_anomaly_is_detected():
    historical_transactions = pd.DataFrame(
        [
            {
                "user_id": "user_001",
                "date": "2026-01-10",
                "category": "transport",
                "amount": 100,
            },
            {
                "user_id": "user_001",
                "date": "2026-01-20",
                "category": "transport",
                "amount": 100,
            },
            {
                "user_id": "user_001",
                "date": "2026-02-10",
                "category": "transport",
                "amount": 120,
            },
            {
                "user_id": "user_001",
                "date": "2026-02-20",
                "category": "transport",
                "amount": 120,
            },
        ]
    )

    baselines = build_monthly_category_baselines(
        historical_transactions
    )

    result = flag_category_spending(
        monthly_spend=500,
        user_id="user_001",
        category="transport",
        baselines=baselines,
        z_threshold=3.0,
        minimum_history=2,
    )

    assert result.is_anomaly
    assert result.score > 3.0
    assert result.reason is not None


def test_category_spending_normal_is_not_anomaly():
    transactions = pd.DataFrame(
        [
            {
                "user_id": "user_001",
                "date": "2026-01-10",
                "category": "transport",
                "amount": 100,
            },
            {
                "user_id": "user_001",
                "date": "2026-02-10",
                "category": "transport",
                "amount": 120,
            },
            {
                "user_id": "user_001",
                "date": "2026-03-10",
                "category": "transport",
                "amount": 110,
            },
        ]
    )

    baselines = build_monthly_category_baselines(
        transactions
    )

    result = flag_category_spending(
        monthly_spend=115,
        user_id="user_001",
        category="transport",
        baselines=baselines,
        z_threshold=3.0,
        minimum_history=2,
    )

    assert not result.is_anomaly


def test_category_spending_requires_history():
    transactions = pd.DataFrame(
        [
            {
                "user_id": "user_001",
                "date": "2026-01-10",
                "category": "transport",
                "amount": 100,
            },
        ]
    )

    baselines = build_monthly_category_baselines(
        transactions
    )

    result = flag_category_spending(
        monthly_spend=5000,
        user_id="user_001",
        category="transport",
        baselines=baselines,
        minimum_history=3,
    )

    assert not result.is_anomaly
    assert result.reason == "Insufficient historical months"


def test_unknown_category_is_not_anomaly():
    baselines = {}

    result = flag_category_spending(
        monthly_spend=5000,
        user_id="user_001",
        category="transport",
        baselines=baselines,
    )

    assert not result.is_anomaly