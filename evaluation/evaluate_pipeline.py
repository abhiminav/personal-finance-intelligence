import pandas as pd

from data.synthetic_generator import generate_dataset
from pipeline import run_pipeline


def build_transaction_dataframe(
    transactions,
) -> pd.DataFrame:
    """
    Convert synthetic transaction objects
    into the DataFrame expected by the pipeline.
    """

    rows = []

    for transaction in transactions:
        rows.append(
            {
                "transaction_id": (
                    transaction.transaction_id
                ),
                "user_id": transaction.user_id,
                "date": transaction.date,
                "amount": transaction.amount,
                "category": transaction.category,
                "merchant_id": (
                    transaction.merchant_id
                ),
                "merchant_name": (
                    transaction.canonical_merchant
                ),
                "is_injected_anomaly": (
                    transaction.is_injected_anomaly
                ),
                "anomaly_type": (
                    transaction.anomaly_type
                ),
            }
        )

    return pd.DataFrame(rows)


def main():
    print("=" * 70)
    print("END-TO-END PIPELINE EVALUATION")
    print("=" * 70)

    transactions, profiles = generate_dataset(
        seed=42
    )

    transaction_df = (
        build_transaction_dataframe(
            transactions
        )
    )

    print(
        f"\nInput transactions: "
        f"{len(transaction_df)}"
    )

    print(
        f"Users: "
        f"{transaction_df['user_id'].nunique()}"
    )

    all_results = []

    print("\nPROCESSING USERS")
    print("-" * 70)

    for user_id in sorted(
        transaction_df["user_id"].unique()
    ):
        user_input = transaction_df[
            transaction_df["user_id"] == user_id
        ].copy()

        try:
            result = run_pipeline(
                transaction_df,
                user_id=user_id,
            )

            output = result.transactions

            anomaly_count = int(
                output["anomaly"].sum()
            )

            forecast_amount = (
                result.forecast.forecast_amount
            )

            expected_count = len(
                user_input
            )

            actual_count = len(output)

            print(
                f"{user_id}: "
                f"{actual_count}/{expected_count} "
                f"transactions | "
                f"{anomaly_count} anomalies | "
                f"forecast ₹"
                f"{forecast_amount:,.2f}"
            )

            all_results.append(
                {
                    "user_id": user_id,
                    "input_count": expected_count,
                    "output_count": actual_count,
                    "anomaly_count": anomaly_count,
                    "forecast": forecast_amount,
                    "success": True,
                }
            )

        except Exception as exc:
            print(
                f"{user_id}: FAILED — {exc}"
            )

            all_results.append(
                {
                    "user_id": user_id,
                    "input_count": len(
                        user_input
                    ),
                    "output_count": 0,
                    "anomaly_count": 0,
                    "forecast": 0.0,
                    "success": False,
                }
            )

    results_df = pd.DataFrame(
        all_results
    )

    print("\nPIPELINE SUMMARY")
    print("-" * 70)

    successful_users = int(
        results_df["success"].sum()
    )

    total_output = int(
        results_df["output_count"].sum()
    )

    total_anomalies = int(
        results_df["anomaly_count"].sum()
    )

    total_input = len(
        transaction_df
    )

    print(
        f"Successful users: "
        f"{successful_users}/"
        f"{len(results_df)}"
    )

    print(
        f"Input transactions: "
        f"{total_input}"
    )

    print(
        f"Output transactions: "
        f"{total_output}"
    )

    print(
        f"Transaction preservation: "
        f"{total_output == total_input}"
    )

    print(
        f"Total anomalies flagged: "
        f"{total_anomalies}"
    )

    print(
        f"Forecasts generated: "
        f"{successful_users}"
    )

    print("\nINJECTED ANOMALY CHECK")
    print("-" * 70)

    injected = transaction_df[
        transaction_df[
            "is_injected_anomaly"
        ]
    ].copy()

    detected_anomalies = []

    for user_id in sorted(
        injected["user_id"].unique()
    ):
        user_input = transaction_df[
            transaction_df["user_id"] == user_id
        ].copy()

        result = run_pipeline(
            transaction_df,
            user_id=user_id,
        )

        output = result.transactions

        detected = output[
            output["anomaly"]
        ]

        detected_anomalies.append(
            detected
        )

    if detected_anomalies:
        detected_df = pd.concat(
            detected_anomalies,
            ignore_index=True,
        )
    else:
        detected_df = pd.DataFrame()

    detected_ids = set(
        detected_df[
            "transaction_id"
        ]
    )

    for anomaly_type in sorted(
        injected["anomaly_type"]
        .dropna()
        .unique()
    ):
        type_injected = injected[
            injected["anomaly_type"]
            == anomaly_type
        ]

        detected_count = sum(
            transaction_id
            in detected_ids
            for transaction_id
            in type_injected[
                "transaction_id"
            ]
        )

        print(
            f"{anomaly_type}: "
            f"{detected_count}/"
            f"{len(type_injected)} detected"
        )

    print("\nFINAL STATUS")
    print("-" * 70)

    pipeline_success = (
        successful_users
        == len(results_df)
        and total_output
        == total_input
    )

    if pipeline_success:
        print(
            "END-TO-END PIPELINE: PASS"
        )
    else:
        print(
            "END-TO-END PIPELINE: FAIL"
        )


if __name__ == "__main__":
    main()