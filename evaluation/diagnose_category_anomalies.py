import pandas as pd

from anomaly.category_spending import (
    build_monthly_category_baselines,
    flag_category_spending,
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
            "transaction_id": transaction.transaction_id,
            "user_id": transaction.user_id,
            "date": transaction.date,
            "category": transaction.category,
            "amount": transaction.amount,
            "is_injected_anomaly": transaction.is_injected_anomaly,
            "injected_anomaly_type": transaction.anomaly_type,
        }
        for transaction in transactions
    ]

    df = pd.DataFrame(rows)

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")

    # We evaluate only normal transactions when constructing
    # historical baselines.
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

    monthly_spending = monthly_spending.sort_values(
        [
            "user_id",
            "category",
            "month",
        ]
    )

    results = []

    unique_months = sorted(
        df["month"].unique()
    )

    minimum_history = 4

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
            result = flag_category_spending(
                monthly_spend=float(row["amount"]),
                user_id=str(row["user_id"]),
                category=str(row["category"]),
                baselines=baselines,
                z_threshold=3.0,
                minimum_history=minimum_history,
            )

            if result.is_anomaly:
                baseline = baselines.get(
                    (
                        str(row["user_id"]),
                        str(row["category"]),
                    )
                )

                if baseline is None:
                    continue

                results.append(
                    {
                        "user_id": row["user_id"],
                        "category": row["category"],
                        "month": str(row["month"]),
                        "current_spend": float(row["amount"]),
                        "historical_months": (
                            baseline.historical_months
                        ),
                        "historical_median": (
                            baseline.median_monthly_spend
                        ),
                        "historical_mad": (
                            baseline.mad_monthly_spend
                        ),
                        "historical_p95": (
                            baseline.p95_monthly_spend
                        ),
                        "robust_z": result.score,
                    }
                )

    diagnostics = pd.DataFrame(results)

    if diagnostics.empty:
        print("No monthly category anomalies found.")
        return

    diagnostics = diagnostics.sort_values(
        "robust_z",
        ascending=False,
    )

    print("=" * 100)
    print("MONTHLY CATEGORY ANOMALY DIAGNOSTIC")
    print("=" * 100)

    print()
    print(
        f"Monthly category anomalies: "
        f"{len(diagnostics)}"
    )

    print()
    print(
        diagnostics.to_string(
            index=False,
            float_format=lambda value: f"{value:.2f}",
        )
    )

    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)

    print()
    print(
        diagnostics[
            [
                "historical_months",
                "historical_mad",
                "robust_z",
            ]
        ].describe()
    )


if __name__ == "__main__":
    main()