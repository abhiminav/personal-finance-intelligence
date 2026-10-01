from sklearn.metrics import accuracy_score, classification_report

from categorization.ml_classifier import MLClassifier
from data.synthetic_generator import generate_dataset
from evaluation.generalization_dataset import (
    get_generalization_dataset,
)


def main():
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

    classifier = MLClassifier()

    classifier.fit(
        descriptions,
        categories,
    )

    (
        test_descriptions,
        test_categories,
    ) = get_generalization_dataset()

    predictions = classifier.predict(
        test_descriptions
    )

    accuracy = accuracy_score(
        test_categories,
        predictions,
    )

    print("=" * 70)
    print("ML GENERALIZATION TEST")
    print("=" * 70)

    print()
    print(
        f"Unseen test transactions: "
        f"{len(test_descriptions)}"
    )

    print(
        f"Accuracy: "
        f"{accuracy:.4f} "
        f"({accuracy * 100:.2f}%)"
    )

    print()
    print("=" * 70)
    print("PER-CATEGORY METRICS")
    print("=" * 70)

    print(
        classification_report(
            test_categories,
            predictions,
            zero_division=0,
        )
    )

    print("=" * 70)
    print("INCORRECT PREDICTIONS")
    print("=" * 70)

    incorrect = 0

    for description, actual, predicted in zip(
        test_descriptions,
        test_categories,
        predictions,
    ):
        if actual != predicted:
            incorrect += 1

            print(
                f"[WRONG] "
                f"{description:40} "
                f"| actual: {actual:18} "
                f"| predicted: {predicted}"
            )

    if incorrect == 0:
        print("No incorrect predictions.")

    print()
    print(f"Incorrect predictions: {incorrect}")


if __name__ == "__main__":
    main()