import re


def clean_description(description: str) -> str:
    """
    Normalize a raw bank transaction description.

    The function removes common payment-provider noise,
    transaction references, and formatting differences while
    preserving the merchant-identifying text.
    """

    if not isinstance(description, str):
        raise TypeError(
            "description must be a string"
        )

    text = description.upper().strip()

    # Remove common payment gateways.
    text = re.sub(
        r"\b(PAYTM|PHONEPE|GPAY|BHIM)\b",
        " ",
        text,
    )

    # Remove UPI prefixes.
    text = re.sub(
        r"\bUPI\b",
        " ",
        text,
    )

    # Remove POS prefix and terminal number.
    text = re.sub(
        r"\bPOS\s*\d+\b",
        " ",
        text,
    )

    # Remove common UPI reference numbers.
    text = re.sub(
        r"\b\d{6,12}\b",
        " ",
        text,
    )

    # Remove order/reference identifiers.
    text = re.sub(
        r"\bORDER\d+\b",
        " ",
        text,
    )

    # Remove common UPI suffixes.
    text = re.sub(
        r"\b(OKAXIS|OKSBI|OKICICI|YBL|PAYTM)\b",
        " ",
        text,
    )

    # Remove common location suffixes.
    text = re.sub(
        r"(BLR|DEL|MUM|BOM|HYD|CHE)\b",
        " ",
        text,
    )

    # Replace separators with spaces.
    text = re.sub(
        r"[/_*|-]+",
        " ",
        text,
    )

    # Remove apostrophes and other punctuation.
    text = re.sub(
        r"[^A-Z0-9\s]",
        " ",
        text,
    )

    # Normalize whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text.lower()