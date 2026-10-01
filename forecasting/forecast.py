from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ForecastResult:
    category: str
    historical_months: int
    average_monthly_spend: float
    forecast_amount: float


@dataclass(frozen=True)
class UserForecastResult:
    user_id: str
    category: str | None
    historical_months: int
    average_monthly_spend: float
    forecast_amount: float


def forecast_category_spending(
    transactions: pd.DataFrame,
    category: str,
    minimum_history: int = 3,
    window: int | None = None,
) -> ForecastResult:
    """
    Forecast next-month spending for a category.

    By default, uses the cumulative historical monthly average.

    If window is provided, uses only the most recent `window`
    months.

    Expected columns:
        date
        category
        amount
    """

    required_columns = {
        "date",
        "category",
        "amount",
    }

    missing = required_columns - set(
        transactions.columns
    )

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if minimum_history < 1:
        raise ValueError(
            "minimum_history must be at least 1"
        )

    if window is not None and window < 1:
        raise ValueError(
            "window must be at least 1"
        )

    if transactions.empty:
        return ForecastResult(
            category=category,
            historical_months=0,
            average_monthly_spend=0.0,
            forecast_amount=0.0,
        )

    data = transactions.copy()

    data["date"] = pd.to_datetime(
        data["date"]
    )

    data = data[
        (data["category"] == category)
        & (data["amount"] > 0)
    ].copy()

    if data.empty:
        return ForecastResult(
            category=category,
            historical_months=0,
            average_monthly_spend=0.0,
            forecast_amount=0.0,
        )

    data["month"] = data["date"].dt.to_period("M")

    monthly_spending = (
        data.groupby("month")["amount"]
        .sum()
        .sort_index()
    )

    historical_months = len(monthly_spending)

    if historical_months < minimum_history:
        return ForecastResult(
            category=category,
            historical_months=historical_months,
            average_monthly_spend=0.0,
            forecast_amount=0.0,
        )

    if window is not None:
        monthly_spending = (
            monthly_spending.tail(window)
        )

    average_monthly_spend = float(
        monthly_spending.mean()
    )

    return ForecastResult(
        category=category,
        historical_months=historical_months,
        average_monthly_spend=average_monthly_spend,
        forecast_amount=average_monthly_spend,
    )


def forecast_user_spending(
    transactions: pd.DataFrame,
    user_id: str,
    category: str | None = None,
    minimum_history: int = 3,
    window: int | None = None,
) -> UserForecastResult:
    """
    Forecast next-month spending for one user.

    If category is provided, forecast that category only.
    Otherwise, forecast total spending across all categories.

    By default, uses the cumulative historical monthly average.

    If window is provided, uses only the most recent `window`
    months.

    Expected columns:
        user_id
        date
        amount

    Optional column:
        category
    """

    required_columns = {
        "user_id",
        "date",
        "amount",
    }

    missing = required_columns - set(
        transactions.columns
    )

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if (
        category is not None
        and "category" not in transactions.columns
    ):
        raise ValueError(
            "Missing required columns: ['category']"
        )

    if minimum_history < 1:
        raise ValueError(
            "minimum_history must be at least 1"
        )

    if window is not None and window < 1:
        raise ValueError(
            "window must be at least 1"
        )

    data = transactions.copy()

    data["date"] = pd.to_datetime(
        data["date"]
    )

    data = data[
        (data["user_id"] == user_id)
        & (data["amount"] > 0)
    ].copy()

    if category is not None:
        data = data[
            data["category"] == category
        ].copy()

    if data.empty:
        return UserForecastResult(
            user_id=user_id,
            category=category,
            historical_months=0,
            average_monthly_spend=0.0,
            forecast_amount=0.0,
        )

    data["month"] = data["date"].dt.to_period("M")

    monthly_spending = (
        data.groupby("month")["amount"]
        .sum()
        .sort_index()
    )

    historical_months = len(monthly_spending)

    if historical_months < minimum_history:
        return UserForecastResult(
            user_id=user_id,
            category=category,
            historical_months=historical_months,
            average_monthly_spend=0.0,
            forecast_amount=0.0,
        )

    if window is not None:
        monthly_spending = (
            monthly_spending.tail(window)
        )

    average_monthly_spend = float(
        monthly_spending.mean()
    )

    return UserForecastResult(
        user_id=user_id,
        category=category,
        historical_months=historical_months,
        average_monthly_spend=average_monthly_spend,
        forecast_amount=average_monthly_spend,
    )