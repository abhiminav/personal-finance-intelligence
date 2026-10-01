from sklearn.metrics import accuracy_score

from categorization.ml_classifier import MLClassifier
from data.synthetic_generator import generate_dataset
from evaluation.generalization_dataset import (
    get_generalization_dataset,
)


THRESHOLDS = [
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
]


def main():
    # Generate the training data.
    transactions, _ = generate_dataset(
        n_users=5,
        months=12,
        seed=42,
    )

    descriptions = [
        transaction.raw_description
        for transaction in transactions
    ]

    categories = [
        transaction.category
        for transaction in transactions
    ]

    # Train the ML classifier.
    classifier = MLClassifier()

    classifier.fit(
        descriptions,
        categories,
    )

    # Load the separate generalization benchmark.
    (
        test_descriptions,
        test_categories,
    ) = get_generalization_dataset()

    prediction_results = (
        classifier.predict_with_confidence(
            test_descriptions
        )
    )

    print("=" * 80)
    print("ML CONFIDENCE THRESHOLD EVALUATION")
    print("=" * 80)

    print()
    print(
        f"Generalization examples: "
        f"{len(test_descriptions)}"
    )

    print()

    for threshold in THRESHOLDS:
        accepted_predictions = []
        accepted_actual = []

        rejected = 0

        for actual, (
            prediction,
            confidence,
        ) in zip(
            test_categories,
            prediction_results,
        ):
            if confidence >= threshold:
                accepted_predictions.append(
                    prediction
                )
                accepted_actual.append(actual)
            else:
                rejected += 1

        accepted = len(accepted_predictions)

        if accepted > 0:
            accuracy = accuracy_score(
                accepted_actual,
                accepted_predictions,
            )
        else:
            accuracy = 0.0

        coverage = (
            accepted / len(test_descriptions)
        )

        wrong_accepted = sum(
            actual != predicted
            for actual, predicted in zip(
                accepted_actual,
                accepted_predictions,
            )
        )

        print(
            f"Threshold: {threshold:.0%}"
        )
        print(
            f"  Accepted:          "
            f"{accepted:2} / {len(test_descriptions)}"
        )
        print(
            f"  Rejected / review: "
            f"{rejected:2}"
        )
        print(
            f"  Coverage:          "
            f"{coverage:.2%}"
        )
        print(
            f"  Accuracy:          "
            f"{accuracy:.2%}"
        )
        print(
            f"  Wrong accepted:    "
            f"{wrong_accepted}"
        )
        print()


if __name__ == "__main__":
    main()