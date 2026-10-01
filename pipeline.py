from dataclasses import dataclass

import pandas as pd

from anomaly.baseline import (
    build_category_baselines,
    build_merchant_baselines,
)
from anomaly.flagging import flag_transactions
from data.deduplication import flag_dataframe_duplicates
from forecasting.forecast import forecast_user_spending


@dataclass(frozen=True)
class PipelineResult:
    transactions: pd.DataFrame
    forecast: object


def prepare_transactions(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Validate and normalize the transaction DataFrame
    used by the intelligence pipeline.

    Required columns:
        date
        user_id
        amount
        category

    Optional columns:
        merchant_id
        merchant_name
        description
        debit
        credit
        reference_number
    """

    required_columns = {
        "date",
        "user_id",
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

    data = transactions.copy()

    data["date"] = pd.to_datetime(
        data["date"]
    )

    data["amount"] = pd.to_numeric(
        data["amount"],
        errors="raise",
    )

    data = data[
        data["amount"] > 0
    ].copy()

    data = data.sort_values(
        ["user_id", "date"]
    ).reset_index(drop=True)

    return data


def run_pipeline(
    transactions: pd.DataFrame,
    user_id: str,
    forecast_category: str | None = None,
) -> PipelineResult:
    """
    Run the complete transaction intelligence pipeline.

    Flow:
        validation
        -> duplicate detection
        -> baselines
        -> anomaly detection
        -> forecasting

    Duplicate transactions are never removed. They are instead
    marked with duplicate metadata so downstream consumers can
    decide how to handle them.
    """

    data = prepare_transactions(
        transactions
    )

    user_transactions = data[
        data["user_id"] == user_id
    ].copy()

    if user_transactions.empty:
        raise ValueError(
            f"No transactions found for user: {user_id}"
        )

    if {
        "description",
        "debit",
        "credit",
    }.issubset(user_transactions.columns):
        user_transactions = flag_dataframe_duplicates(
            user_transactions
        )
    else:
        user_transactions["is_duplicate"] = False
        user_transactions["is_possible_duplicate"] = False
        user_transactions["duplicate_reason"] = None

    category_baselines = (
        build_category_baselines(
            user_transactions
        )
    )

    merchant_baselines = (
        build_merchant_baselines(
            user_transactions
        )
    )

    enriched_transactions = flag_transactions(
        transactions=user_transactions,
        baselines=category_baselines,
        merchant_baselines=merchant_baselines,
    )

    forecast = forecast_user_spending(
        user_transactions,
        user_id=user_id,
        category=forecast_category,
    )

    return PipelineResult(
        transactions=enriched_transactions,
        forecast=forecast,
    )