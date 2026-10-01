import pandas as pd
import pytest

from anomaly.baseline import (
    build_category_baselines,
    build_merchant_baselines,
)
from anomaly.flagging import (
    flag_transaction,
    flag_transactions,
)


def test_build_category_baselines():
    transactions = pd.DataFrame(
        {
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
                "transport",
                "transport",
            ],
            "amount": [
                100,
                150,
                200,
                50,
                100,
            ],
        }
    )

    baselines = build_category_baselines(
        transactions
    )

    assert "food & dining" in baselines
    assert "transport" in baselines

    food = baselines["food & dining"]

    assert food.transaction_count == 3
    assert food.mean_amount == 150
    assert food.median_amount == 150


def test_empty_transactions():
    transactions = pd.DataFrame(
        columns=["category", "amount"]
    )

    assert build_category_baselines(
        transactions
    ) == {}


def test_missing_baseline_is_not_anomaly():
    baselines = {}

    result = flag_transaction(
        amount=1000,
        category="shopping",
        baselines=baselines,
    )

    assert result.is_anomaly is False
    assert result.anomaly_type is None


def test_insufficient_history():
    transactions = pd.DataFrame(
        {
            "category": [
                "food & dining",
                "food & dining",
            ],
            "amount": [100, 150],
        }
    )

    baselines = build_category_baselines(
        transactions
    )

    result = flag_transaction(
        amount=5000,
        category="food & dining",
        baselines=baselines,
    )

    assert result.is_anomaly is False
    assert result.reason == "Insufficient category history"


def test_large_amount_is_anomaly():
    transactions = pd.DataFrame(
        {
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
            ],
            "amount": [
                100,
                110,
                90,
                105,
                95,
            ],
        }
    )

    baselines = build_category_baselines(
        transactions
    )

    result = flag_transaction(
        amount=1000,
        category="food & dining",
        baselines=baselines,
    )

    assert result.is_anomaly is True
    assert result.anomaly_type == "amount_spike"
    assert result.score >= 3.0
    assert result.reason is not None


def test_normal_amount_is_not_anomaly():
    transactions = pd.DataFrame(
        {
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
            ],
            "amount": [
                100,
                110,
                90,
                105,
                95,
            ],
        }
    )

    baselines = build_category_baselines(
        transactions
    )

    result = flag_transaction(
        amount=120,
        category="food & dining",
        baselines=baselines,
    )

    assert result.is_anomaly is False


def test_negative_amount_is_rejected():
    with pytest.raises(ValueError):
        flag_transaction(
            amount=-100,
            category="shopping",
            baselines={},
        )


def test_flag_transactions():
    transactions = pd.DataFrame(
        {
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
                "food & dining",
            ],
            "amount": [
                100,
                110,
                90,
                105,
                95,
            ],
        }
    )

    baselines = build_category_baselines(
        transactions
    )

    new_transactions = pd.DataFrame(
        {
            "category": [
                "food & dining",
                "food & dining",
            ],
            "amount": [
                120,
                1000,
            ],
        }
    )

    result = flag_transactions(
        new_transactions,
        baselines,
    )

    assert len(result) == 2
    assert "anomaly" in result.columns
    assert "anomaly_type" in result.columns
    assert "anomaly_score" in result.columns
    assert "anomaly_reason" in result.columns

    assert bool(result.iloc[0]["anomaly"]) is False
    assert bool(result.iloc[1]["anomaly"]) is True


def test_build_merchant_baselines():
    transactions = pd.DataFrame(
        {
            "merchant_id": [
                "swiggy",
                "swiggy",
                "swiggy",
                "amazon",
                "amazon",
            ],
            "merchant_name": [
                "Swiggy",
                "Swiggy",
                "Swiggy",
                "Amazon",
                "Amazon",
            ],
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
                "shopping",
                "shopping",
            ],
            "amount": [
                300,
                400,
                500,
                1000,
                2000,
            ],
        }
    )

    baselines = build_merchant_baselines(
        transactions
    )

    assert "swiggy" in baselines
    assert "amazon" in baselines

    swiggy = baselines["swiggy"]

    assert swiggy.merchant_id == "swiggy"
    assert swiggy.merchant_name == "Swiggy"
    assert swiggy.category == "food & dining"
    assert swiggy.transaction_count == 3
    assert swiggy.mean_amount == 400
    assert swiggy.median_amount == 400


def test_merchant_without_id_is_ignored():
    transactions = pd.DataFrame(
        {
            "merchant_id": [
                None,
                "swiggy",
                "swiggy",
            ],
            "merchant_name": [
                None,
                "Swiggy",
                "Swiggy",
            ],
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
            ],
            "amount": [
                5000,
                300,
                400,
            ],
        }
    )

    baselines = build_merchant_baselines(
        transactions
    )

    assert list(baselines.keys()) == ["swiggy"]
    assert baselines["swiggy"].transaction_count == 2


def test_merchant_baseline_is_preferred():
    transactions = pd.DataFrame(
        {
            "merchant_id": [
                "swiggy",
                "swiggy",
                "swiggy",
            ],
            "merchant_name": [
                "Swiggy",
                "Swiggy",
                "Swiggy",
            ],
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
            ],
            "amount": [
                300,
                350,
                400,
            ],
        }
    )

    merchant_baselines = build_merchant_baselines(
        transactions
    )

    category_transactions = pd.DataFrame(
        {
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
            ],
            "amount": [
                300,
                350,
                400,
            ],
        }
    )

    category_baselines = build_category_baselines(
        category_transactions
    )

    result = flag_transaction(
        amount=1000,
        category="food & dining",
        baselines=category_baselines,
        merchant_id="swiggy",
        merchant_baselines=merchant_baselines,
    )

    assert result.is_anomaly is True
    assert "Swiggy" in result.reason


def test_category_baseline_is_fallback():
    transactions = pd.DataFrame(
        {
            "category": [
                "food & dining",
                "food & dining",
                "food & dining",
            ],
            "amount": [
                100,
                110,
                90,
            ],
        }
    )

    baselines = build_category_baselines(
        transactions
    )

    result = flag_transaction(
        amount=1000,
        category="food & dining",
        baselines=baselines,
        merchant_id="unknown",
        merchant_baselines={},
    )

    assert result.is_anomaly is True
    assert "food & dining" in result.reason