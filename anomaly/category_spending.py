from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MonthlyCategoryBaseline:
    user_id: str
    category: str
    historical_months: int
    median_monthly_spend: float
    mad_monthly_spend: float
    p95_monthly_spend: float


@dataclass(frozen=True)
class CategorySpendingAnomaly:
    is_anomaly: bool
    score: float
    reason: str | None


def build_monthly_category_baselines(
    transactions: pd.DataFrame,
) -> dict[tuple[str, str], MonthlyCategoryBaseline]:
    """
    Build per-user, per-category monthly spending baselines.

    Uses the median and MAD (Median Absolute Deviation)
    instead of mean and standard deviation so that unusually
    large months have less influence on the baseline.
    """

    required_columns = {
        "user_id",
        "date",
        "category",
        "amount",
    }

    missing = required_columns - set(transactions.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if transactions.empty:
        return {}

    spending = transactions[
        transactions["amount"] > 0
    ].copy()

    if spending.empty:
        return {}

    spending["date"] = pd.to_datetime(
        spending["date"]
    )

    spending["month"] = (
        spending["date"]
        .dt.to_period("M")
    )

    monthly = (
        spending
        .groupby(
            [
                "user_id",
                "category",
                "month",
            ],
            as_index=False,
        )["amount"]
        .sum()
    )

    baselines = {}

    for (user_id, category), group in monthly.groupby(
        ["user_id", "category"]
    ):
        amounts = group["amount"].astype(float)

        median = float(amounts.median())

        mad = float(
            np.median(
                np.abs(amounts - median)
            )
        )

        baselines[
            (str(user_id), str(category))
        ] = MonthlyCategoryBaseline(
            user_id=str(user_id),
            category=str(category),
            historical_months=len(amounts),
            median_monthly_spend=median,
            mad_monthly_spend=mad,
            p95_monthly_spend=float(
                amounts.quantile(0.95)
            ),
        )

    return baselines


def flag_category_spending(
    monthly_spend: float,
    user_id: str,
    category: str,
    baselines: dict[
        tuple[str, str],
        MonthlyCategoryBaseline,
    ],
    z_threshold: float = 3.0,
    minimum_history: int = 4,
    minimum_increase_ratio: float = 1.5,
) -> CategorySpendingAnomaly:
    if monthly_spend < 0:
        raise ValueError(
            "monthly_spend must be non-negative"
        )

    if z_threshold < 0:
        raise ValueError(
            "z_threshold must be non-negative"
        )

    if minimum_history < 1:
        raise ValueError(
            "minimum_history must be at least 1"
        )

    if minimum_increase_ratio < 1:
        raise ValueError(
            "minimum_increase_ratio must be at least 1"
        )

    baseline = baselines.get(
        (str(user_id), str(category))
    )

    if baseline is None:
        return CategorySpendingAnomaly(False, 0.0, None)

    if baseline.historical_months < minimum_history:
        return CategorySpendingAnomaly(
            False,
            0.0,
            "Insufficient historical months",
        )

    if baseline.median_monthly_spend <= 0:
        return CategorySpendingAnomaly(
            False,
            0.0,
            "Historical median is zero",
        )

    increase_ratio = (
        monthly_spend
        / baseline.median_monthly_spend
    )

    if baseline.mad_monthly_spend == 0:
        if (
            monthly_spend
            > baseline.median_monthly_spend
            and increase_ratio >= minimum_increase_ratio
        ):
            return CategorySpendingAnomaly(
                True,
                float("inf"),
                (
                    f"Monthly {category} spending of "
                    f"₹{monthly_spend:.2f} is at least "
                    f"{minimum_increase_ratio:.1f}x the "
                    f"historical median of "
                    f"₹{baseline.median_monthly_spend:.2f}."
                ),
            )

        return CategorySpendingAnomaly(False, 0.0, None)

    robust_z = (
        0.6745
        * (
            monthly_spend
            - baseline.median_monthly_spend
        )
        / baseline.mad_monthly_spend
    )

    if (
        robust_z >= z_threshold
        and increase_ratio >= minimum_increase_ratio
    ):
        return CategorySpendingAnomaly(
            True,
            float(robust_z),
            (
                f"Monthly {category} spending of "
                f"₹{monthly_spend:.2f} is "
                f"{robust_z:.2f} robust standard deviations "
                f"above the historical median and "
                f"{increase_ratio:.2f}x the historical median."
            ),
        )

    return CategorySpendingAnomaly(
        False,
        float(robust_z),
        None,
    )