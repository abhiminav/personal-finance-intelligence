from collections import Counter

from categorization.merchant_clustering import cluster_merchants
from data.synthetic_generator import generate_dataset


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

    clusters = cluster_merchants(descriptions)

    print("=" * 70)
    print("MERCHANT CLUSTERING EVALUATION")
    print("=" * 70)

    print()
    print(f"Transactions: {len(transactions)}")
    print(f"Clusters:     {len(clusters)}")

    resolved = [
        cluster
        for cluster in clusters
        if cluster.merchant_id is not None
    ]

    unresolved = [
        cluster
        for cluster in clusters
        if cluster.merchant_id is None
    ]

    print(f"Resolved:     {len(resolved)}")
    print(f"Unresolved:   {len(unresolved)}")

    if clusters:
        resolution_rate = (
            len(resolved) / len(clusters) * 100
        )
    else:
        resolution_rate = 0.0

    print(
        f"Resolution rate: "
        f"{resolution_rate:.2f}%"
    )

    print()
    print("=" * 70)
    print("CANONICAL MERCHANT DISTRIBUTION")
    print("=" * 70)

    merchant_counts = Counter(
        cluster.canonical_name
        for cluster in resolved
    )

    for merchant, count in merchant_counts.most_common():
        print(f"{merchant:<25}{count:>5}")

    print()
    print("=" * 70)
    print("UNRESOLVED CLUSTERS")
    print("=" * 70)

    if not unresolved:
        print("None")
    else:
        for cluster in unresolved:
            print()
            print(f"Cluster: {cluster.cluster_id}")
            print(f"Canonical: {cluster.canonical_name}")
            print(f"Members: {len(cluster.members)}")

            for member in cluster.members[:10]:
                print(f"  - {member}")

            if len(cluster.members) > 10:
                print(
                    f"  ... and "
                    f"{len(cluster.members) - 10} more"
                )


if __name__ == "__main__":
    main()