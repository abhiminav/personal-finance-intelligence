import re

from data.schemas import Counterparty


COUNTERPARTY_NAMES = {
    "RAJESH KUMAR",
    "ROHIT S",
    "PRIYA SHARMA",
    "AMIT VERMA",
    "NEHA GUPTA",
    "VIKAS JAIN",
}


def extract_counterparty(
    description: str,
) -> Counterparty | None:
    """
    Extract a known P2P counterparty from a raw transaction
    description.

    Supported formats include:

        UPI/123456/RAJESH KUMAR/paytm
        UPI-123456-AMIT VERMA
        IMPS/P2A/123456/Amit Verma

    Returns:
        Counterparty object if a known person is detected,
        otherwise None.
    """

    if not isinstance(description, str):
        raise TypeError(
            "description must be a string"
        )

    text = description.upper().strip()

    # Normalize separators.
    normalized = re.sub(
        r"[/_-]+",
        " ",
        text,
    )

    # Remove numeric transaction references.
    normalized = re.sub(
        r"\b\d{6,12}\b",
        " ",
        normalized,
    )

    # Remove common payment-system keywords.
    normalized = re.sub(
        r"\b(UPI|IMPS|P2A|PAYTM|PHONEPE|GPAY|BHIM)\b",
        " ",
        normalized,
    )

    # Normalize whitespace.
    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()

    for name in COUNTERPARTY_NAMES:

        if name in normalized:

            counterparty_id = (
                name.lower()
                .replace(" ", "_")
            )

            return Counterparty(
                counterparty_id=counterparty_id,
                name=name.title(),
            )

    return None