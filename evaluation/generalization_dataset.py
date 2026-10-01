from dataclasses import dataclass


@dataclass(frozen=True)
class GeneralizationExample:
    description: str
    category: str


GENERALIZATION_EXAMPLES = [
    # ---------------------------------------------------------
    # Food & dining
    # ---------------------------------------------------------
    GeneralizationExample(
        "SWIGGY INDIA ONLINE",
        "food & dining",
    ),
    GeneralizationExample(
        "SWIGGY BANGALORE ORDER",
        "food & dining",
    ),
    GeneralizationExample(
        "FOOD DELIVERY SWIGGY",
        "food & dining",
    ),
    GeneralizationExample(
        "ZOMATO LTD",
        "food & dining",
    ),
    GeneralizationExample(
        "ZOMATO FOOD ORDER",
        "food & dining",
    ),
    GeneralizationExample(
        "DOMINOS PIZZA INDIA",
        "food & dining",
    ),
    GeneralizationExample(
        "MCDONALDS ONLINE",
        "food & dining",
    ),

    # ---------------------------------------------------------
    # Groceries
    # ---------------------------------------------------------
    GeneralizationExample(
        "BLINKIT INDIA",
        "groceries",
    ),
    GeneralizationExample(
        "BLINKIT QUICK COMMERCE",
        "groceries",
    ),
    GeneralizationExample(
        "ZEpto QUICK COMMERCE",
        "groceries",
    ),
    GeneralizationExample(
        "BIGBASKET ONLINE ORDER",
        "groceries",
    ),
    GeneralizationExample(
        "DMART INDIA",
        "groceries",
    ),
    GeneralizationExample(
        "DMART SUPERMARKET",
        "groceries",
    ),

    # ---------------------------------------------------------
    # Shopping
    # ---------------------------------------------------------
    GeneralizationExample(
        "AMZN INDIA",
        "shopping",
    ),
    GeneralizationExample(
        "AMAZON PAY IN",
        "shopping",
    ),
    GeneralizationExample(
        "AMAZON ONLINE STORE",
        "shopping",
    ),
    GeneralizationExample(
        "FLIPKART ONLINE SHOP",
        "shopping",
    ),
    GeneralizationExample(
        "MYNTRA INDIA",
        "shopping",
    ),
    GeneralizationExample(
        "CROMA ELECTRONICS",
        "shopping",
    ),
    GeneralizationExample(
        "ONLINE PURCHASE AMAZON",
        "shopping",
    ),

    # ---------------------------------------------------------
    # Transport
    # ---------------------------------------------------------
    GeneralizationExample(
        "UBER INDIA TRIP",
        "transport",
    ),
    GeneralizationExample(
        "UBER DELHI",
        "transport",
    ),
    GeneralizationExample(
        "OLA CAB SERVICES",
        "transport",
    ),
    GeneralizationExample(
        "RAPIDO MOBILITY",
        "transport",
    ),
    GeneralizationExample(
        "CAB RIDE UBER",
        "transport",
    ),
    GeneralizationExample(
        "OLA RIDE PAYMENT",
        "transport",
    ),

    # ---------------------------------------------------------
    # Subscriptions
    # ---------------------------------------------------------
    GeneralizationExample(
        "NETFLIX INDIA",
        "subscriptions",
    ),
    GeneralizationExample(
        "NETFLIX MONTHLY",
        "subscriptions",
    ),
    GeneralizationExample(
        "SPOTIFY PREMIUM",
        "subscriptions",
    ),
    GeneralizationExample(
        "YOUTUBE PREMIUM INDIA",
        "subscriptions",
    ),
    GeneralizationExample(
        "GYM MEMBERSHIP",
        "subscriptions",
    ),
    GeneralizationExample(
        "MONTHLY GYM FEE",
        "subscriptions",
    ),

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------
    GeneralizationExample(
        "ELECTRICITY BILL PAYMENT",
        "utilities",
    ),
    GeneralizationExample(
        "POWER BILL",
        "utilities",
    ),
    GeneralizationExample(
        "INTERNET BILL",
        "utilities",
    ),
    GeneralizationExample(
        "BROADBAND PAYMENT",
        "utilities",
    ),
    GeneralizationExample(
        "MOBILE RECHARGE",
        "utilities",
    ),
    GeneralizationExample(
        "PHONE RECHARGE",
        "utilities",
    ),

    # ---------------------------------------------------------
    # Investments
    # ---------------------------------------------------------
    GeneralizationExample(
        "GROWW MONTHLY SIP",
        "investments",
    ),
    GeneralizationExample(
        "ZERODHA MONTHLY SIP",
        "investments",
    ),
    GeneralizationExample(
        "MUTUAL FUND INVESTMENT",
        "investments",
    ),
    GeneralizationExample(
        "NIFTY INDEX FUND",
        "investments",
    ),
    GeneralizationExample(
        "MONTHLY SIP INVESTMENT",
        "investments",
    ),

    # ---------------------------------------------------------
    # Rent
    # ---------------------------------------------------------
    GeneralizationExample(
        "HOUSE RENT PAYMENT",
        "rent",
    ),
    GeneralizationExample(
        "MONTHLY HOUSE RENT",
        "rent",
    ),
    GeneralizationExample(
        "RENT TRANSFER",
        "rent",
    ),

    # ---------------------------------------------------------
    # Salary / income
    # ---------------------------------------------------------
    GeneralizationExample(
        "MONTHLY SALARY CREDIT",
        "salary/income",
    ),
    GeneralizationExample(
        "SALARY NEFT CREDIT",
        "salary/income",
    ),
    GeneralizationExample(
        "MONTHLY PAYROLL",
        "salary/income",
    ),
    GeneralizationExample(
        "SALARY CREDIT",
        "salary/income",
    ),

    # ---------------------------------------------------------
    # Transfers / P2P
    # ---------------------------------------------------------
    GeneralizationExample(
        "UPI TRANSFER TO RAJESH KUMAR",
        "transfers/P2P",
    ),
    GeneralizationExample(
        "MONEY SENT TO AMIT VERMA",
        "transfers/P2P",
    ),
    GeneralizationExample(
        "IMPS TRANSFER PRIYA SHARMA",
        "transfers/P2P",
    ),
    GeneralizationExample(
        "UPI PAYMENT TO ROHIT S",
        "transfers/P2P",
    ),
    GeneralizationExample(
        "TRANSFER TO NEHA GUPTA",
        "transfers/P2P",
    ),
    GeneralizationExample(
        "PAYMENT TO VIKAS JAIN",
        "transfers/P2P",
    ),
]


def get_generalization_dataset():
    """
    Return descriptions and ground-truth categories
    for the unseen narration benchmark.
    """

    descriptions = [
        example.description
        for example in GENERALIZATION_EXAMPLES
    ]

    categories = [
        example.category
        for example in GENERALIZATION_EXAMPLES
    ]

    return descriptions, categories