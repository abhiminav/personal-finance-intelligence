from dataclasses import dataclass

import pandas as pd

from anomaly.baseline import (
    CategoryBaseline,
    MerchantBaseline,
)
from anomaly.recurring import (
    detect_recurring_transaction,
)
from categorization.merchant_dictionary import (
    get_merchant_by_id,
)


@dataclass(frozen=True)
class AnomalyResult:
    is_anomaly: bool
    anomaly_type: str | None
    score: float
    reason: str | None


def flag_transaction(
    amount: float,
    category: str,
    baselines: dict[str, CategoryBaseline],
    z_threshold: float = 3.0,
    merchant_id: str | None = None,
    merchant_baselines: dict[str, MerchantBaseline] | None = None,
    minimum_merchant_history: int = 3,
    current_date=None,
    historical_transactions: pd.DataFrame | None = None,
) -> AnomalyResult:
    """
    Flag unusually large spending transactions.

    Detection hierarchy:
    1. P2P transfers are excluded.
    2. Recurring payments are excluded from amount anomalies.
    3. Known merchants require sufficient merchant history.
    4. Merchant-level history is preferred when sufficient history exists.
    5. Category-level history is used for unknown merchants.
    6. Historical p95 + median ratio is the primary signal.

    This detector identifies unusual spending, not fraud.
    """

    if amount < 0:
        raise ValueError("amount must be non-negative")

    if z_threshold < 0:
        raise ValueError("z_threshold must be non-negative")

    if minimum_merchant_history < 1:
        raise ValueError(
            "minimum_merchant_history must be at least 1"
        )

    if category == "transfers/P2P":
        return AnomalyResult(
            False,
            None,
            0.0,
            None,
        )

    if (
        current_date is not None
        and historical_transactions is not None
        and merchant_id is not None
    ):
        recurring_result = detect_recurring_transaction(
            current_date=current_date,
            current_amount=amount,
            merchant_id=merchant_id,
            historical_transactions=historical_transactions,
        )

        if recurring_result.is_recurring:
            return AnomalyResult(
                False,
                None,
                0.0,
                (
                    "Recurring payment detected. "
                    + (recurring_result.reason or "")
                ).strip(),
            )

    baseline = None
    baseline_name = category
    using_merchant_baseline = False

    if (
        merchant_id is not None
        and merchant_baselines is not None
    ):
        merchant_baseline = merchant_baselines.get(
            merchant_id
        )

        if merchant_baseline is not None:
            if (
                merchant_baseline.transaction_count
                < minimum_merchant_history
            ):
                return AnomalyResult(
                    False,
                    None,
                    0.0,
                    "Insufficient merchant history",
                )

            baseline = merchant_baseline
            baseline_name = merchant_baseline.merchant_name
            using_merchant_baseline = True

        else:
            # A known merchant with no historical baseline
            # has insufficient merchant history and should not
            # fall back to the broader category baseline.
            known_merchant = get_merchant_by_id(
                merchant_id
            )

            if known_merchant is not None:
                return AnomalyResult(
                    False,
                    None,
                    0.0,
                    "Insufficient merchant history",
                )

    if baseline is None:
        baseline = baselines.get(category)

    if baseline is None:
        return AnomalyResult(
            False,
            None,
            0.0,
            None,
        )

    if baseline.transaction_count < 3:
        return AnomalyResult(
            False,
            None,
            0.0,
            "Insufficient category history",
        )

    median = baseline.median_amount
    p95 = baseline.p95_amount

    if median <= 0:
        return AnomalyResult(
            False,
            None,
            0.0,
            None,
        )

    increase_ratio = amount / median
    p95_trigger = amount > p95

    minimum_ratio = 2.5

    robust_trigger = (
        p95_trigger
        and increase_ratio >= minimum_ratio
    )

    if robust_trigger:
        reason = (
            f"Amount ₹{amount:.2f} exceeds the historical "
            f"{baseline_name} 95th percentile of "
            f"₹{p95:.2f} and is "
            f"{increase_ratio:.2f}x the historical median "
            f"of ₹{median:.2f}."
        )

        return AnomalyResult(
            True,
            "amount_spike",
            float(increase_ratio),
            reason,
        )

    return AnomalyResult(
        False,
        None,
        float(increase_ratio),
        None,
    )


def flag_transactions(
    transactions: pd.DataFrame,
    baselines: dict[str, CategoryBaseline],
    z_threshold: float = 3.0,
    merchant_baselines: dict[str, MerchantBaseline] | None = None,
    minimum_merchant_history: int = 3,
) -> pd.DataFrame:
    """
    Flag transactions using merchant-level baselines when
    sufficient history exists, otherwise category-level
    baselines for unknown merchants.

    Expected columns:
        amount
        category

    Optional columns:
        merchant_id
        date
    """

    required_columns = {
        "amount",
        "category",
    }

    missing = required_columns - set(
        transactions.columns
    )

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    results = transactions.apply(
        lambda row: flag_transaction(
            amount=float(row["amount"]),
            category=row["category"],
            baselines=baselines,
            z_threshold=z_threshold,
            merchant_id=(
                row["merchant_id"]
                if "merchant_id" in row
                and pd.notna(row["merchant_id"])
                else None
            ),
            merchant_baselines=merchant_baselines,
            minimum_merchant_history=minimum_merchant_history,
            current_date=(
                row["date"]
                if "date" in row
                else None
            ),
            historical_transactions=(
                transactions[
                    transactions["date"] < row["date"]
                ]
                if "date" in row
                else None
            ),
        ),
        axis=1,
    )

    result = transactions.copy()

    result["anomaly"] = [
        item.is_anomaly
        for item in results
    ]

    result["anomaly_type"] = [
        item.anomaly_type
        for item in results
    ]

    result["anomaly_score"] = [
        item.score
        for item in results
    ]

    result["anomaly_reason"] = [
        item.reason
        for item in results
    ]

    return result