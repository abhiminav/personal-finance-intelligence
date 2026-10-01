import pandas as pd

from anomaly.baseline import (
    build_category_baselines,
    build_merchant_baselines,
)
from anomaly.category_spending import (
    build_monthly_category_baselines,
    flag_category_spending,
)
from anomaly.flagging import flag_transaction
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
            "merchant_id": transaction.merchant_id,
            "merchant_name": transaction.canonical_merchant,
            "is_injected_anomaly": transaction.is_injected_anomaly,
            "injected_anomaly_type": transaction.anomaly_type,
            "description": transaction.raw_description,
        }
        for transaction in transactions
    ]

    df = pd.DataFrame(rows)

    print("=" * 70)
    print("ANOMALY DETECTION EVALUATION")
    print("=" * 70)

    print()
    print(f"Transactions: {len(df)}")
    print(
        f"Injected anomalies: "
        f"{df['is_injected_anomaly'].sum()}"
    )

    # ---------------------------------------------------------
    # Transaction-level temporal evaluation
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    # Each transaction is evaluated using ONLY transactions
    # that occurred before it.
    #
    # Injected anomalies are excluded from the historical
    # baseline so the synthetic benchmark does not contaminate
    # the "normal spending" reference distribution.
    # ---------------------------------------------------------

    sorted_df = df.sort_values(
        ["date", "transaction_id"]
    ).reset_index(drop=True)

    transaction_results = []

    for _, current_transaction in sorted_df.iterrows():

        historical_transactions = sorted_df[
            (
                sorted_df["date"]
                < current_transaction["date"]
            )
            & (
                ~sorted_df["is_injected_anomaly"]
            )
        ].copy()

        # Only use the current user's historical data.
        historical_transactions = historical_transactions[
            historical_transactions["user_id"]
            == current_transaction["user_id"]
        ]

        category_baselines = build_category_baselines(
            historical_transactions[
                [
                    "category",
                    "amount",
                ]
            ]
        )

        merchant_baselines = build_merchant_baselines(
            historical_transactions[
                [
                    "merchant_id",
                    "merchant_name",
                    "category",
                    "amount",
                ]
            ]
        )

        result = flag_transaction(
            amount=float(
                current_transaction["amount"]
            ),
            category=str(
                current_transaction["category"]
            ),
            baselines=category_baselines,
            z_threshold=3.0,
            merchant_id=(
                current_transaction["merchant_id"]
                if pd.notna(
                    current_transaction["merchant_id"]
                )
                else None
            ),
            merchant_baselines=merchant_baselines,
        )

        transaction_results.append(
            {
                "transaction_id": current_transaction[
                    "transaction_id"
                ],
                "transaction_anomaly": result.is_anomaly,
                "anomaly_type": result.anomaly_type,
                "anomaly_score": result.score,
                "anomaly_reason": result.reason,
            }
        )

    transaction_results = pd.DataFrame(
        transaction_results
    )

    transaction_results = sorted_df.merge(
        transaction_results,
        on="transaction_id",
        how="left",
    )

    transaction_results["date"] = pd.to_datetime(
        transaction_results["date"]
    )

    transaction_results["month"] = (
        transaction_results["date"]
        .dt.to_period("M")
    )

    # ---------------------------------------------------------
    # Monthly category detection
    # ---------------------------------------------------------

    monthly_spending = (
        transaction_results
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

    monthly_spending[
        "category_anomaly"
    ] = False

    monthly_spending[
        "category_anomaly_score"
    ] = 0.0

    monthly_spending[
        "category_anomaly_reason"
    ] = None

    unique_months = sorted(
        monthly_spending["month"].unique()
    )

    minimum_history = 4

    for current_month in unique_months:

        historical_transactions = (
            transaction_results[
                transaction_results["month"]
                < current_month
            ]
            .copy()
        )

        if historical_transactions.empty:
            continue

        historical_baselines = (
            build_monthly_category_baselines(
                historical_transactions[
                    [
                        "user_id",
                        "date",
                        "category",
                        "amount",
                    ]
                ]
            )
        )

        current_rows = monthly_spending[
            monthly_spending["month"]
            == current_month
        ]

        for index, row in current_rows.iterrows():

            result = flag_category_spending(
                monthly_spend=float(
                    row["amount"]
                ),
                user_id=str(
                    row["user_id"]
                ),
                category=str(
                    row["category"]
                ),
                baselines=historical_baselines,
                z_threshold=3.0,
                minimum_history=minimum_history,
                minimum_increase_ratio=1.5,
            )

            monthly_spending.loc[
                index,
                "category_anomaly",
            ] = result.is_anomaly

            monthly_spending.loc[
                index,
                "category_anomaly_score",
            ] = result.score

            monthly_spending.loc[
                index,
                "category_anomaly_reason",
            ] = result.reason

    # ---------------------------------------------------------
    # Transaction-level evaluation
    # ---------------------------------------------------------

    injected_transactions = df[
        df["is_injected_anomaly"]
    ]

    transaction_results_for_eval = (
        transaction_results[
            [
                "transaction_id",
                "transaction_anomaly",
            ]
        ]
    )

    injected_transaction_results = (
        injected_transactions[
            [
                "transaction_id",
                "injected_anomaly_type",
            ]
        ]
        .merge(
            transaction_results_for_eval,
            on="transaction_id",
            how="left",
        )
    )

    # ---------------------------------------------------------
    # Category-level evaluation
    # ---------------------------------------------------------

    injected_category_events = (
        df[
            df["is_injected_anomaly"]
            & df["injected_anomaly_type"].eq(
                "category_spike"
            )
        ]
        .groupby(
            [
                "user_id",
                "category",
            ],
            as_index=False,
        )
        .agg(
            month=(
                "date",
                lambda values:
                pd.to_datetime(values)
                .dt.to_period("M")
                .iloc[0],
            )
        )
    )

    injected_category_events["injected"] = True

    detected_category_events = (
        monthly_spending[
            monthly_spending["category_anomaly"]
        ][
            [
                "user_id",
                "category",
                "month",
                "category_anomaly_score",
            ]
        ]
        .copy()
    )

    detected_category_events[
        "detected"
    ] = True

    # ---------------------------------------------------------
    # Detection by injected anomaly type
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("DETECTION BY INJECTED ANOMALY TYPE")
    print("=" * 70)

    unusual_purchase = (
        injected_transaction_results[
            injected_transaction_results[
                "injected_anomaly_type"
            ].eq("unusual_purchase")
        ]
    )

    large_one_off = (
        injected_transaction_results[
            injected_transaction_results[
                "injected_anomaly_type"
            ].eq("large_one_off")
        ]
    )

    unusual_detected = (
        unusual_purchase[
            "transaction_anomaly"
        ].any()
        if not unusual_purchase.empty
        else False
    )

    large_detected = (
        large_one_off[
            "transaction_anomaly"
        ].any()
        if not large_one_off.empty
        else False
    )

    print(
        f"{'unusual_purchase':<25}"
        f"{int(unusual_detected)}/1"
    )

    print(
        f"{'large_one_off':<25}"
        f"{int(large_detected)}/1"
    )

    if injected_category_events.empty:
        category_detected = 0
        category_total = 0

    else:
        category_check = (
            injected_category_events.merge(
                detected_category_events,
                on=[
                    "user_id",
                    "category",
                    "month",
                ],
                how="left",
            )
        )

        category_detected = (
            category_check["detected"]
            .fillna(False)
            .sum()
        )

        category_total = len(
            injected_category_events
        )

    print(
        f"{'category_spike':<25}"
        f"{int(category_detected)}/"
        f"{category_total}"
    )

    # ---------------------------------------------------------
    # Transaction-level false positives
    # ---------------------------------------------------------

    normal_transactions = (
        transaction_results[
            ~transaction_results[
                "is_injected_anomaly"
            ]
        ]
    )

    transaction_false_positives = (
        normal_transactions[
            normal_transactions[
                "transaction_anomaly"
            ]
        ]
    )

    transaction_fpr = (
        len(transaction_false_positives)
        / len(normal_transactions)
        * 100
        if len(normal_transactions) > 0
        else 0.0
    )

    # ---------------------------------------------------------
    # Category-level false positives
    # ---------------------------------------------------------

    normal_category_events = (
        monthly_spending.copy()
    )

    injected_category_keys = set(
        zip(
            injected_category_events[
                "user_id"
            ],
            injected_category_events[
                "category"
            ],
            injected_category_events[
                "month"
            ],
        )
    )

    normal_category_events[
        "is_injected_category_event"
    ] = normal_category_events.apply(
        lambda row: (
            row["user_id"],
            row["category"],
            row["month"],
        )
        in injected_category_keys,
        axis=1,
    )

    normal_category_events = (
        normal_category_events[
            ~normal_category_events[
                "is_injected_category_event"
            ]
        ]
    )

    category_false_positives = (
        normal_category_events[
            normal_category_events[
                "category_anomaly"
            ]
        ]
    )

    category_fpr = (
        len(category_false_positives)
        / len(normal_category_events)
        * 100
        if len(normal_category_events) > 0
        else 0.0
    )

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("FALSE POSITIVE CHECK")
    print("=" * 70)

    print(
        f"Transaction-level false positives: "
        f"{len(transaction_false_positives)}"
    )

    print(
        f"Transaction-level false positive rate: "
        f"{transaction_fpr:.2f}%"
    )

    print(
        f"Category-level false positives: "
        f"{len(category_false_positives)}"
    )

    print(
        f"Category-level false positive rate: "
        f"{category_fpr:.2f}%"
    )

    print()
    print("=" * 70)
    print("CATEGORY ANOMALY EVENTS")
    print("=" * 70)

    print(
        f"Detected category events: "
        f"{len(detected_category_events)}"
    )

    if not detected_category_events.empty:
        print()

        print(
            detected_category_events.to_string(
                index=False,
                float_format=lambda value:
                f"{value:.2f}",
            )
        )


if __name__ == "__main__":
    main()