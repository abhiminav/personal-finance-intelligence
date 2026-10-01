from datetime import date

import pandas as pd
import pytest

from anomaly.recurring import (
    detect_recurring_transaction,
)


def test_detects_monthly_recurring_payment():
    history = pd.DataFrame(
        [
            {
                "date": date(2025, 10, 15),
                "amount": 1499.0,
                "merchant_id": "gym",
            }
        ]
    )

    result = detect_recurring_transaction(
        current_date=date(2025, 11, 10),
        current_amount=1499.0,
        merchant_id="gym",
        historical_transactions=history,
    )

    assert result.is_recurring is True
    assert result.confidence == 1.0


def test_allows_small_amount_difference():
    history = pd.DataFrame(
        [
            {
                "date": date(2025, 10, 10),
                "amount": 1000.0,
                "merchant_id": "internet",
            }
        ]
    )

    result = detect_recurring_transaction(
        current_date=date(2025, 11, 10),
        current_amount=1050.0,
        merchant_id="internet",
        historical_transactions=history,
    )

    assert result.is_recurring is True


def test_rejects_large_amount_difference():
    history = pd.DataFrame(
        [
            {
                "date": date(2025, 10, 10),
                "amount": 1000.0,
                "merchant_id": "internet",
            }
        ]
    )

    result = detect_recurring_transaction(
        current_date=date(2025, 11, 10),
        current_amount=1500.0,
        merchant_id="internet",
        historical_transactions=history,
    )

    assert result.is_recurring is False


def test_rejects_non_monthly_transaction():
    history = pd.DataFrame(
        [
            {
                "date": date(2025, 10, 10),
                "amount": 1499.0,
                "merchant_id": "gym",
            }
        ]
    )

    result = detect_recurring_transaction(
        current_date=date(2025, 11, 25),
        current_amount=1499.0,
        merchant_id="gym",
        historical_transactions=history,
    )

    assert result.is_recurring is False


def test_rejects_missing_merchant():
    history = pd.DataFrame(
        [
            {
                "date": date(2025, 10, 10),
                "amount": 1499.0,
                "merchant_id": "gym",
            }
        ]
    )

    result = detect_recurring_transaction(
        current_date=date(2025, 11, 10),
        current_amount=1499.0,
        merchant_id=None,
        historical_transactions=history,
    )

    assert result.is_recurring is False


def test_empty_history():
    history = pd.DataFrame(
        columns=[
            "date",
            "amount",
            "merchant_id",
        ]
    )

    result = detect_recurring_transaction(
        current_date=date(2025, 11, 10),
        current_amount=1499.0,
        merchant_id="gym",
        historical_transactions=history,
    )

    assert result.is_recurring is False