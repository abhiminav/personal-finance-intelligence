from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RecurringResult:
    is_recurring: bool
    confidence: float
    reason: str | None


def detect_recurring_transaction(
    current_date,
    current_amount: float,
    merchant_id: str | None,
    historical_transactions: pd.DataFrame,
    minimum_occurrences: int = 1,
    day_tolerance: int = 5,
    amount_tolerance: float = 0.10,
) -> RecurringResult:
    """
    Detect whether a transaction appears to be part of a
    recurring merchant payment pattern.

    A transaction is considered recurring when:
    - it has a merchant ID
    - there is sufficient historical activity for that merchant
    - a previous transaction occurred roughly one month earlier
    - the previous amount is within the allowed tolerance

    This is intentionally conservative. It identifies recurring
    payment patterns; it does not attempt to forecast future dates.
    """

    if current_amount < 0:
        raise ValueError(
            "current_amount must be non-negative"
        )

    if minimum_occurrences < 1:
        raise ValueError(
            "minimum_occurrences must be at least 1"
        )

    if day_tolerance < 0:
        raise ValueError(
            "day_tolerance must be non-negative"
        )

    if amount_tolerance < 0:
        raise ValueError(
            "amount_tolerance must be non-negative"
        )

    if merchant_id is None:
        return RecurringResult(
            is_recurring=False,
            confidence=0.0,
            reason=None,
        )

    if historical_transactions.empty:
        return RecurringResult(
            is_recurring=False,
            confidence=0.0,
            reason=None,
        )

    required_columns = {
        "date",
        "amount",
        "merchant_id",
    }

    missing = required_columns - set(
        historical_transactions.columns
    )

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    history = historical_transactions[
        historical_transactions["merchant_id"]
        == merchant_id
    ].copy()

    history = history[
        history["amount"] > 0
    ].copy()

    if len(history) < minimum_occurrences:
        return RecurringResult(
            is_recurring=False,
            confidence=0.0,
            reason=None,
        )

    current_date = pd.Timestamp(current_date)

    history["date"] = pd.to_datetime(
        history["date"]
    )

    history["days_before"] = (
        current_date - history["date"]
    ).dt.days

    # Monthly recurring payments normally occur about
    # 28–31 days apart. We allow a small scheduling variation.
    expected_days = 30

    candidate_history = history[
        (
            history["days_before"]
            >= expected_days - day_tolerance
        )
        & (
            history["days_before"]
            <= expected_days + day_tolerance
        )
    ].copy()

    if candidate_history.empty:
        return RecurringResult(
            is_recurring=False,
            confidence=0.0,
            reason=None,
        )

    candidate_history["amount_difference"] = (
        (
            candidate_history["amount"]
            - current_amount
        ).abs()
        / current_amount
    )

    matching_amounts = candidate_history[
        candidate_history["amount_difference"]
        <= amount_tolerance
    ]

    if matching_amounts.empty:
        return RecurringResult(
            is_recurring=False,
            confidence=0.0,
            reason=None,
        )

    best_match = matching_amounts.iloc[
        matching_amounts["amount_difference"].argmin()
    ]

    amount_difference = float(
        best_match["amount_difference"]
    )

    days_before = int(
        best_match["days_before"]
    )

    confidence = 1.0 - (
        amount_difference / amount_tolerance
        if amount_tolerance > 0
        else 0.0
    )

    confidence = max(
        0.0,
        min(1.0, confidence),
    )

    reason = (
        f"Similar {merchant_id} payment of "
        f"₹{float(best_match['amount']):.2f} occurred "
        f"{days_before} days earlier."
    )

    return RecurringResult(
        is_recurring=True,
        confidence=float(confidence),
        reason=reason,
    )