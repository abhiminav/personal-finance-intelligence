from collections import Counter

from categorization.counterparty import extract_counterparty
from categorization.rule_based import classify_transaction
from data.synthetic_generator import generate_dataset


def main():
    transactions, _ = generate_dataset(
        n_users=5,
        months=12,
        seed=42,
    )

    unresolved = []

    for transaction in transactions:
        result = classify_transaction(transaction.raw_description)

        if result.category is None:
            unresolved.append(transaction)

    print(f"Unresolved transactions: {len(unresolved)}")
    print()

    extracted = []
    failed = []

    for transaction in unresolved:
        counterparty = extract_counterparty(
            transaction.raw_description
        )

        if counterparty is not None:
            extracted.append((transaction, counterparty))
        else:
            failed.append(transaction)

    print(f"Counterparties extracted: {len(extracted)}")
    print(f"Still unresolved: {len(failed)}")
    print()

    if extracted:
        print("Counterparty distribution:")
        counts = Counter(
            counterparty.name
            for _, counterparty in extracted
        )

        for name, count in counts.most_common():
            print(f"  {name}: {count}")

    print()
    print("Sample extracted transactions:")

    for transaction, counterparty in extracted[:15]:
        print(
            f"{transaction.raw_description:45} -> "
            f"{counterparty.name}"
        )

    if failed:
        print()
        print("Still unresolved examples:")

        for transaction in failed[:15]:
            print(transaction.raw_description)


if __name__ == "__main__":
    main()