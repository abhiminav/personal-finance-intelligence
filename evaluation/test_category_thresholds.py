import pandas as pd

from anomaly.category_spending import (
    build_monthly_category_baselines,
)
from data.synthetic_generator import generate_dataset


def main():
    transactions, _ = generate_dataset(
        n_users=5,
        months=12,
        seed=42,
    )

    rows = [
        {
            "user_id": transaction.user_id,
            "date": transaction.date,
            "category": transaction.category,
            "amount": transaction.amount,
            "is_injected_anomaly": transaction.is_injected_anomaly,
        }
        for transaction in transactions
    ]

    df = pd.DataFrame(rows)

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")

    # Exclude injected anomalies from historical data.
    baseline_df = df[
        ~df["is_injected_anomaly"]
    ].copy()

    monthly_spending = (
        baseline_df
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

    thresholds = [1.25, 1.50, 1.75, 2.00]

    results = []

    unique_months = sorted(
        df["month"].unique()
    )

    for current_month in unique_months:
        historical = baseline_df[
            baseline_df["month"] < current_month
        ].copy()

        if historical.empty:
            continue

        baselines = build_monthly_category_baselines(
            historical[
                [
                    "user_id",
                    "date",
                    "category",
                    "amount",
                ]
            ]
        )

        current_rows = monthly_spending[
            monthly_spending["month"]
            == current_month
        ]

        for _, row in current_rows.iterrows():
            baseline = baselines.get(
                (
                    str(row["user_id"]),
                    str(row["category"]),
                )
            )

            if baseline is None:
                continue

            if baseline.historical_months < 4:
                continue

            if baseline.median_monthly_spend <= 0:
                continue

            robust_z = 0.0

            if baseline.mad_monthly_spend > 0:
                robust_z = (
                    0.6745
                    * (
                        float(row["amount"])
                        - baseline.median_monthly_spend
                    )
                    / baseline.mad_monthly_spend
                )

            if robust_z < 3.0:
                continue

            increase_ratio = (
                float(row["amount"])
                / baseline.median_monthly_spend
            )

            results.append(
                {
                    "user_id": row["user_id"],
                    "category": row["category"],
                    "month": str(row["month"]),
                    "current_spend": float(row["amount"]),
                    "historical_median": (
                        baseline.median_monthly_spend
                    ),
                    "increase_ratio": increase_ratio,
                    "robust_z": robust_z,
                }
            )

    diagnostics = pd.DataFrame(results)

    print("=" * 80)
    print("CATEGORY ANOMALY THRESHOLD DIAGNOSTIC")
    print("=" * 80)

    if diagnostics.empty:
        print("No statistically unusual months found.")
        return

    for threshold in thresholds:
        count = (
            diagnostics["increase_ratio"]
            >= threshold
        ).sum()

        print(
            f"{threshold:.2f}x median: "
            f"{count} anomalies"
        )

    print()
    print("=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)

    diagnostics = diagnostics.sort_values(
        "increase_ratio",
        ascending=False,
    )

    print(
        diagnostics.to_string(
            index=False,
            float_format=lambda value: f"{value:.2f}",
        )
    )


if __name__ == "__main__":
    main()