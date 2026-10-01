from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CategoryBaseline:
    category: str
    transaction_count: int
    mean_amount: float
    median_amount: float
    std_amount: float
    p95_amount: float


@dataclass(frozen=True)
class MerchantBaseline:
    merchant_id: str
    merchant_name: str
    category: str
    transaction_count: int
    mean_amount: float
    median_amount: float
    std_amount: float
    p95_amount: float


def build_category_baselines(
    transactions: pd.DataFrame,
) -> dict[str, CategoryBaseline]:
    """
    Build spending baselines for each category.

    Expected columns:
        category
        amount
    """

    required_columns = {"category", "amount"}

    missing = required_columns - set(transactions.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if transactions.empty:
        return {}

    spending = transactions[
        transactions["amount"] > 0
    ].copy()

    baselines: dict[str, CategoryBaseline] = {}

    for category, group in spending.groupby("category"):
        amounts = group["amount"].astype(float)

        baselines[category] = CategoryBaseline(
            category=category,
            transaction_count=len(amounts),
            mean_amount=float(amounts.mean()),
            median_amount=float(amounts.median()),
            std_amount=float(amounts.std(ddof=0)),
            p95_amount=float(amounts.quantile(0.95)),
        )

    return baselines


def build_merchant_baselines(
    transactions: pd.DataFrame,
) -> dict[str, MerchantBaseline]:
    """
    Build spending baselines for each merchant.

    Expected columns:
        merchant_id
        merchant_name
        category
        amount

    Transactions without a merchant_id are ignored.
    """

    required_columns = {
        "merchant_id",
        "merchant_name",
        "category",
        "amount",
    }

    missing = required_columns - set(transactions.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if transactions.empty:
        return {}

    spending = transactions[
        (transactions["amount"] > 0)
        & transactions["merchant_id"].notna()
    ].copy()

    baselines: dict[str, MerchantBaseline] = {}

    for merchant_id, group in spending.groupby(
        "merchant_id"
    ):
        amounts = group["amount"].astype(float)

        merchant_name = str(
            group["merchant_name"].iloc[0]
        )

        category = str(
            group["category"].iloc[0]
        )

        baselines[merchant_id] = MerchantBaseline(
            merchant_id=str(merchant_id),
            merchant_name=merchant_name,
            category=category,
            transaction_count=len(amounts),
            mean_amount=float(amounts.mean()),
            median_amount=float(amounts.median()),
            std_amount=float(amounts.std(ddof=0)),
            p95_amount=float(amounts.quantile(0.95)),
        )

    return baselines