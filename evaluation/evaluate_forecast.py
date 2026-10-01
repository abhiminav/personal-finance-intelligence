import pandas as pd

from data.synthetic_generator import generate_dataset
from forecasting.forecast import forecast_user_spending


def build_transaction_dataframe(
    transactions,
) -> pd.DataFrame:
    rows = []

    for transaction in transactions:
        rows.append(
            {
                "transaction_id": transaction.transaction_id,
                "user_id": transaction.user_id,
                "date": transaction.date,
                "category": transaction.category,
                "amount": transaction.amount,
                "is_injected_anomaly": (
                    transaction.is_injected_anomaly
                ),
            }
        )

    return pd.DataFrame(rows)


def evaluate_user_forecast(
    transactions: pd.DataFrame,
    user_id: str,
    minimum_history: int = 3,
    window: int | None = None,
) -> list[dict]:
    data = transactions[
        transactions["user_id"] == user_id
    ].copy()

    data["date"] = pd.to_datetime(
        data["date"]
    )

    data = data[data["amount"] > 0].copy()

    data["month"] = (
        data["date"].dt.to_period("M")
    )

    months = sorted(
        data["month"].unique()
    )

    results = []

    for index in range(
        minimum_history,
        len(months),
    ):
        target_month = months[index]

        training_data = data[
            data["month"] < target_month
        ].copy()

        actual_data = data[
            data["month"] == target_month
        ].copy()

        forecast = forecast_user_spending(
            training_data,
            user_id=user_id,
            minimum_history=minimum_history,
            window=window,
        )

        actual_amount = float(
            actual_data["amount"].sum()
        )

        forecast_amount = (
            forecast.forecast_amount
        )

        absolute_error = abs(
            forecast_amount
            - actual_amount
        )

        results.append(
            {
                "user_id": user_id,
                "target_month": str(
                    target_month
                ),
                "forecast": forecast_amount,
                "actual": actual_amount,
                "absolute_error": absolute_error,
            }
        )

    return results


def evaluate_strategy(
    transactions: pd.DataFrame,
    window: int | None,
) -> pd.DataFrame:
    all_results = []

    for user_id in sorted(
        transactions["user_id"].unique()
    ):
        results = evaluate_user_forecast(
            transactions,
            user_id=user_id,
            minimum_history=3,
            window=window,
        )

        all_results.extend(results)

    return pd.DataFrame(all_results)


def main():
    transactions, _ = generate_dataset(
        seed=42
    )

    transaction_df = (
        build_transaction_dataframe(
            transactions
        )
    )

    print("=" * 70)
    print("FORECASTING STRATEGY COMPARISON")
    print("=" * 70)

    print(
        f"\nTransactions: "
        f"{len(transaction_df)}"
    )

    print(
        f"Users: "
        f"{transaction_df['user_id'].nunique()}"
    )

    strategies = {
        "Cumulative average": None,
        "3-month rolling average": 3,
    }

    summary = []

    for name, window in strategies.items():
        results_df = evaluate_strategy(
            transaction_df,
            window=window,
        )

        mae = results_df[
            "absolute_error"
        ].mean()

        actual_total = results_df[
            "actual"
        ].sum()

        forecast_total = results_df[
            "forecast"
        ].sum()

        total_error = abs(
            forecast_total
            - actual_total
        )

        summary.append(
            {
                "strategy": name,
                "mae": mae,
                "actual_total": actual_total,
                "forecast_total": forecast_total,
                "total_error": total_error,
            }
        )

    summary_df = pd.DataFrame(
        summary
    )

    print("\nRESULTS")
    print("-" * 70)

    for _, row in summary_df.iterrows():
        print(
            f"{row['strategy']}:"
        )
        print(
            f"  MAE: "
            f"₹{row['mae']:,.2f}"
        )
        print(
            f"  Actual: "
            f"₹{row['actual_total']:,.2f}"
        )
        print(
            f"  Forecast: "
            f"₹{row['forecast_total']:,.2f}"
        )
        print(
            f"  Total error: "
            f"₹{row['total_error']:,.2f}"
        )
        print()

    print("COMPARISON")
    print("-" * 70)

    best_index = summary_df[
        "mae"
    ].idxmin()

    best = summary_df.loc[
        best_index
    ]

    print(
        f"Lowest MAE: "
        f"{best['strategy']}"
    )

    print(
        f"MAE: "
        f"₹{best['mae']:,.2f}"
    )


if __name__ == "__main__":
    main()