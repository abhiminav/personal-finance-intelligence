import pandas as pd

from data.synthetic_generator import generate_dataset
from anomaly.baseline import (
    build_category_baselines,
    build_merchant_baselines,
)
from anomaly.flagging import flag_transaction


def main() -> None:
    transactions, profiles = generate_dataset(seed=42)

    rows = [
        {
            "transaction_id": tx.transaction_id,
            "user_id": tx.user_id,
            "date": tx.date,
            "description": tx.raw_description,
            "merchant_id": tx.merchant_id,
            "merchant_name": tx.canonical_merchant,
            "category": tx.category,
            "amount": tx.amount,
            "is_injected_anomaly": tx.is_injected_anomaly,
        }
        for tx in transactions
    ]

    df = pd.DataFrame(rows)

    df = df.sort_values(
        ["date", "transaction_id"]
    ).reset_index(drop=True)

    results = []

    for _, current_transaction in df.iterrows():

        historical = df[
            (df["user_id"] == current_transaction["user_id"])
            & (df["date"] < current_transaction["date"])
            & (~df["is_injected_anomaly"])
        ].copy()

        category_baselines = build_category_baselines(
            historical
        )

        merchant_baselines = build_merchant_baselines(
            historical
        )

        result = flag_transaction(
            amount=float(current_transaction["amount"]),
            category=current_transaction["category"],
            baselines=category_baselines,
            merchant_id=(
                current_transaction["merchant_id"]
                if pd.notna(current_transaction["merchant_id"])
                else None
            ),
            merchant_baselines=merchant_baselines,
            z_threshold=3.0,
        )

        results.append(
            {
                "transaction_id": current_transaction[
                    "transaction_id"
                ],
                "anomaly": result.is_anomaly,
                "anomaly_type": result.anomaly_type,
                "anomaly_score": result.score,
                "anomaly_reason": result.reason,
            }
        )

    detection_results = pd.DataFrame(results)

    flagged = df.merge(
        detection_results,
        on="transaction_id",
        how="left",
    )

    false_positives = flagged[
        flagged["anomaly"]
        & ~flagged["is_injected_anomaly"]
    ].copy()

    print("=" * 70)
    print("TEMPORAL FALSE POSITIVE DIAGNOSTIC")
    print("=" * 70)

    print(
        f"\nFalse positives: {len(false_positives)}"
    )

    print("\nBY CATEGORY")
    print(
        false_positives["category"]
        .value_counts()
        .to_string()
    )

    print("\nBY MERCHANT")
    print(
        false_positives["merchant_name"]
        .value_counts()
        .to_string()
    )

    print("\nBY USER")
    print(
        false_positives["user_id"]
        .value_counts()
        .to_string()
    )

    print("\nBY ANOMALY TYPE")
    print(
        false_positives["anomaly_type"]
        .value_counts()
        .to_string()
    )

    print("\nFALSE POSITIVE TRANSACTIONS")
    print("-" * 70)

    columns = [
        "transaction_id",
        "user_id",
        "date",
        "description",
        "merchant_name",
        "category",
        "amount",
        "anomaly_score",
        "anomaly_reason",
    ]

    print(
        false_positives[
            columns
        ]
        .sort_values(
            ["category", "merchant_name", "amount"],
            ascending=[True, True, False],
        )
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()