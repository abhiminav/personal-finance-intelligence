from collections import Counter

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

from categorization.rule_based import classify_transaction
from data.synthetic_generator import generate_dataset


def main():
    transactions, _ = generate_dataset(
        n_users=5,
        months=12,
        seed=42,
    )

    actual_categories = []
    predicted_categories = []

    method_counts = Counter()

    for transaction in transactions:
        result = classify_transaction(
            transaction.raw_description
        )

        actual_categories.append(transaction.category)
        predicted_categories.append(result.category)
        method_counts[result.method] += 1

    accuracy = accuracy_score(
        actual_categories,
        predicted_categories,
    )

    print("=" * 70)
    print("RULE-BASED CLASSIFIER EVALUATION")
    print("=" * 70)

    print()
    print(f"Total transactions: {len(transactions)}")
    print(f"Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")

    print()
    print("Classification methods:")
    for method, count in method_counts.most_common():
        print(
            f"  {method:15} "
            f"{count:4} "
            f"({count / len(transactions) * 100:.2f}%)"
        )

    print()
    print("=" * 70)
    print("PER-CATEGORY METRICS")
    print("=" * 70)

    report = classification_report(
        actual_categories,
        predicted_categories,
        zero_division=0,
    )

    print(report)

    print("=" * 70)
    print("CONFUSION MATRIX")
    print("=" * 70)

    labels = sorted(set(actual_categories))

    matrix = confusion_matrix(
        actual_categories,
        predicted_categories,
        labels=labels,
    )

    print()
    print("Labels:")
    for index, label in enumerate(labels):
        print(f"  {index}: {label}")

    print()
    print(matrix)


if __name__ == "__main__":
    main()