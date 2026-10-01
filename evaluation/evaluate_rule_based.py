from collections import Counter

from categorization.rule_based import classify_transaction
from data.synthetic_generator import generate_dataset


def main():
    transactions, _ = generate_dataset(
        n_users=5,
        months=12,
        seed=42,
    )

    results = []

    for transaction in transactions:
        result = classify_transaction(
            transaction.raw_description
        )

        results.append(
            {
                "transaction": transaction,
                "result": result,
            }
        )

    total = len(results)

    correctly_classified = 0
    unresolved = 0
    incorrect = 0

    method_counts = Counter()

    for item in results:
        transaction = item["transaction"]
        result = item["result"]

        method_counts[result.method] += 1

        predicted_category = result.category
        actual_category = transaction.category

        if predicted_category is None:
            unresolved += 1
        elif predicted_category == actual_category:
            correctly_classified += 1
        else:
            incorrect += 1

    resolved = total - unresolved

    print(f"Total transactions: {total}")
    print(f"Resolved: {resolved}")
    print(f"Unresolved: {unresolved}")
    print(f"Incorrect: {incorrect}")
    print()

    print(
        f"Resolution rate: "
        f"{resolved / total * 100:.2f}%"
    )

    print(
        f"Category accuracy: "
        f"{correctly_classified / total * 100:.2f}%"
    )

    print()
    print("Classification methods:")

    for method, count in method_counts.most_common():
        percentage = count / total * 100
        print(
            f"  {method}: "
            f"{count} ({percentage:.2f}%)"
        )


if __name__ == "__main__":
    main()