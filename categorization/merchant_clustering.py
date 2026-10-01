import re
from dataclasses import dataclass

from rapidfuzz import fuzz, process

from categorization.counterparty import extract_counterparty
from categorization.merchant_dictionary import (
    MERCHANT_LOOKUP,
    resolve_exact_merchant,
)


PAYMENT_CHANNELS = (
    "PAYTM",
    "PHONEPE",
    "GPAY",
    "BHIM",
    "UPI",
    "IMPS",
    "NEFT",
    "RTGS",
    "POS",
)

PAYMENT_SUFFIXES = (
    "OKAXIS",
    "OKSBI",
    "OKICICI",
    "YBL",
)

LOCATION_CODES = (
    "BLR",
    "DEL",
    "MUM",
    "BOM",
    "HYD",
    "CHE",
    "PUNE",
    "NOIDA",
    "GURGAON",
)

GENERIC_WORDS = (
    "ONLINE",
    "ORDER",
    "PAYMENT",
    "PURCHASE",
    "INDIA",
    "INDIAN",
    "SERVICES",
    "SERVICE",
    "TRIP",
    "RIDE",
    "BILL",
    "FOOD",
    "QUICK",
    "COMMERCE",
)


@dataclass
class MerchantCluster:
    """
    Represents a group of transaction descriptions
    believed to refer to the same merchant.
    """

    cluster_id: str
    canonical_name: str
    merchant_id: str | None
    category: str | None
    members: list[str]


def normalize_merchant_name(name: str) -> str:
    """
    Normalize a merchant name into a comparable form.

    Removes common payment channels, transaction identifiers,
    location suffixes, and generic transaction words.
    """

    if not isinstance(name, str):
        raise TypeError("name must be a string")

    text = name.upper().strip()

    text = re.sub(
        r"\b(?:"
        + "|".join(PAYMENT_CHANNELS)
        + r")\b",
        " ",
        text,
    )

    text = re.sub(
        r"\b\d{4,12}\b",
        " ",
        text,
    )

    text = re.sub(
        r"\b(?:"
        + "|".join(PAYMENT_SUFFIXES)
        + r")\b",
        " ",
        text,
    )

    text = re.sub(
        r"(?:"
        + "|".join(LOCATION_CODES)
        + r")$",
        " ",
        text,
    )

    text = re.sub(
        r"\b(?:"
        + "|".join(LOCATION_CODES)
        + r")\b",
        " ",
        text,
    )

    text = re.sub(
        r"\b(?:"
        + "|".join(GENERIC_WORDS)
        + r")\b",
        " ",
        text,
    )

    text = re.sub(
        r"[/_*|:-]+",
        " ",
        text,
    )

    text = re.sub(
        r"[^A-Z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text.lower()


def merchant_similarity(
    first: str,
    second: str,
) -> float:
    """
    Calculate similarity between two merchant names.

    Returns a score from 0 to 100.
    """

    first_normalized = normalize_merchant_name(first)
    second_normalized = normalize_merchant_name(second)

    return float(
        fuzz.token_set_ratio(
            first_normalized,
            second_normalized,
        )
    )


def is_counterparty_transaction(
    description: str,
) -> bool:
    """
    Return True when a transaction description contains
    a recognized P2P counterparty.
    """

    return extract_counterparty(description) is not None


def filter_merchant_descriptions(
    names: list[str],
) -> list[str]:
    """
    Remove P2P/counterparty descriptions before merchant clustering.
    """

    if not isinstance(names, list):
        raise TypeError("names must be a list")

    merchant_names = []

    for name in names:
        if not isinstance(name, str):
            raise TypeError(
                "all merchant names must be strings"
            )

        if not name.strip():
            continue

        if is_counterparty_transaction(name):
            continue

        merchant_names.append(name)

    return merchant_names


def resolve_cluster_merchant(
    cluster_name: str,
) -> tuple[str | None, str | None, str | None]:
    """
    Resolve a clustered merchant description against the
    canonical merchant dictionary.

    Resolution order:
        1. Exact canonical alias
        2. Fuzzy canonical alias
        3. Unresolved

    Returns:
        (merchant_id, merchant_name, category)
    """

    normalized_name = normalize_merchant_name(
        cluster_name
    )

    if not normalized_name:
        return None, None, None

    # ---------------------------------------------------------
    # Step 1: exact alias resolution
    # ---------------------------------------------------------
    merchant = resolve_exact_merchant(
        normalized_name
    )

    if merchant is not None:
        return (
            merchant.merchant_id,
            merchant.name,
            merchant.category,
        )

    # ---------------------------------------------------------
    # Step 2: fuzzy alias resolution
    # ---------------------------------------------------------
    result = process.extractOne(
        normalized_name,
        list(MERCHANT_LOOKUP.keys()),
        scorer=fuzz.WRatio,
    )

    if result is None:
        return None, None, None

    merchant_id, score, _ = result

    if score < 80:
        return None, None, None

    merchant = MERCHANT_LOOKUP[merchant_id]

    return (
        merchant.merchant_id,
        merchant.name,
        merchant.category,
    )


def cluster_merchants(
    names: list[str],
    threshold: float = 85.0,
) -> list[MerchantCluster]:
    """
    Group merchant descriptions into clusters.

    P2P/counterparty transactions are excluded before clustering.

    Each remaining description is compared against existing
    cluster representatives. If similarity reaches the threshold,
    the description is assigned to that cluster.

    After clustering, each cluster is resolved against the
    canonical merchant dictionary.
    """

    if not isinstance(names, list):
        raise TypeError("names must be a list")

    if not 0 <= threshold <= 100:
        raise ValueError(
            "threshold must be between 0 and 100"
        )

    merchant_names = filter_merchant_descriptions(names)

    clusters: list[MerchantCluster] = []

    for name in merchant_names:
        best_cluster = None
        best_score = -1.0

        for cluster in clusters:
            score = merchant_similarity(
                name,
                cluster.canonical_name,
            )

            if score > best_score:
                best_score = score
                best_cluster = cluster

        if (
            best_cluster is not None
            and best_score >= threshold
        ):
            best_cluster.members.append(name)
        else:
            cluster_id = f"cluster_{len(clusters) + 1}"

            clusters.append(
                MerchantCluster(
                    cluster_id=cluster_id,
                    canonical_name=name,
                    merchant_id=None,
                    category=None,
                    members=[name],
                )
            )

    for cluster in clusters:
        (
            merchant_id,
            merchant_name,
            category,
        ) = resolve_cluster_merchant(
            cluster.canonical_name
        )

        if merchant_id is not None:
            cluster.merchant_id = merchant_id
            cluster.canonical_name = merchant_name
            cluster.category = category

    return clusters