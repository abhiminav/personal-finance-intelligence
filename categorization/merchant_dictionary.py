from data.synthetic_generator import MERCHANTS


MERCHANT_ALIASES = {
    # Food & dining
    "swiggy": "swiggy",
    "zomato": "zomato",
    "dominos": "dominos",
    "mcdonalds": "mcdonalds",

    # Groceries
    "blinkit": "blinkit",
    "zepto": "zepto",
    "bigbasket": "bigbasket",
    "dmart": "dmart",

    # Shopping
    "amazon": "amazon",
    "flipkart": "flipkart",
    "myntra": "myntra",
    "croma": "croma",

    # Transport
    "uber": "uber",
    "ola": "ola",
    "rapido": "rapido",

    # Subscriptions
    "netflix": "netflix",
    "spotify": "spotify",
    "youtube": "youtube",
    "youtube premium": "youtube",

    # Utilities
    "electricity": "electricity",
    "internet": "internet",
    "mobile recharge": "mobile",

    # Other recurring transactions
    "gym": "gym",
    "rent": "rent",
    "landlord rent": "rent",

    # Salary / income
    "salary": "salary",
    "neft hdfc0001234 salary oct": "salary",
    "neft hdfc0001234 salary nov": "salary",
    "neft hdfc0001234 salary dec": "salary",
    "neft hdfc0001234 salary jan": "salary",
    "neft hdfc0001234 salary feb": "salary",
    "neft hdfc0001234 salary mar": "salary",
    "neft hdfc0001234 salary apr": "salary",
    "neft hdfc0001234 salary may": "salary",
    "neft hdfc0001234 salary jun": "salary",
    "neft hdfc0001234 salary jul": "salary",
    "neft hdfc0001234 salary aug": "salary",
    "neft hdfc0001234 salary sep": "salary",

    # Investments
    "groww sip": "investment",
    "zerodha sip": "investment",
    "mutual fund sip": "investment",
    "nifty index sip": "investment",
    "investment": "investment",
}


MERCHANT_LOOKUP = {
    merchant.merchant_id: merchant
    for merchant in MERCHANTS
}


def get_merchant_by_id(merchant_id: str):
    """
    Return the Merchant object for a merchant ID.
    """

    return MERCHANT_LOOKUP.get(merchant_id)


def resolve_exact_merchant(
    cleaned_description: str,
):
    """
    Resolve a cleaned description using exact dictionary matching.

    Returns:
        Merchant object if matched, otherwise None.
    """

    merchant_id = MERCHANT_ALIASES.get(
        cleaned_description
    )

    if merchant_id is None:
        return None

    return get_merchant_by_id(merchant_id)