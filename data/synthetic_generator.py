"""
Synthetic Indian bank/UPI transaction generator.

This module generates realistic synthetic financial transactions with:
- recurring income and expenses
- everyday UPI/POS transactions
- deliberately noisy merchant descriptions
- ground-truth merchant/category labels
- injected anomalies

The generated data is intended for developing and evaluating
the personal finance intelligence pipeline.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
import numpy as np

import calendar


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

CATEGORIES = [
    "food & dining",
    "groceries",
    "rent",
    "utilities",
    "subscriptions",
    "transfers/P2P",
    "shopping",
    "transport",
    "salary/income",
    "investments",
    "other",
]


# ---------------------------------------------------------------------------
# Merchant definition
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Merchant:
    """Canonical representation of a merchant."""

    merchant_id: str
    name: str
    category: str


# ---------------------------------------------------------------------------
# Merchant registry
# ---------------------------------------------------------------------------

MERCHANTS = [
    # Food & dining
    Merchant("swiggy", "Swiggy", "food & dining"),
    Merchant("zomato", "Zomato", "food & dining"),
    Merchant("dominos", "Dominos", "food & dining"),
    Merchant("mcdonalds", "McDonald's", "food & dining"),

    # Groceries
    Merchant("blinkit", "Blinkit", "groceries"),
    Merchant("zepto", "Zepto", "groceries"),
    Merchant("bigbasket", "BigBasket", "groceries"),
    Merchant("dmart", "DMart", "groceries"),

    # Shopping
    Merchant("amazon", "Amazon", "shopping"),
    Merchant("flipkart", "Flipkart", "shopping"),
    Merchant("myntra", "Myntra", "shopping"),
    Merchant("croma", "Croma", "shopping"),

    # Transport
    Merchant("uber", "Uber", "transport"),
    Merchant("ola", "Ola", "transport"),
    Merchant("rapido", "Rapido", "transport"),

    # Subscriptions
    Merchant("netflix", "Netflix", "subscriptions"),
    Merchant("spotify", "Spotify", "subscriptions"),
    Merchant("youtube", "YouTube Premium", "subscriptions"),

    # Utilities
    Merchant("electricity", "Electricity", "utilities"),
    Merchant("internet", "Internet", "utilities"),
    Merchant("mobile", "Mobile Recharge", "utilities"),

    # Fitness
    Merchant("gym", "Gym", "subscriptions"),

    Merchant("rent", "Rent", "rent"),
    Merchant("salary", "Salary", "salary/income"),
    Merchant("investment", "Investment", "investments"),
]


COUNTERPARTIES = [
    "RAJESH KUMAR",
    "ROHIT S",
    "PRIYA SHARMA",
    "AMIT VERMA",
    "NEHA GUPTA",
    "VIKAS JAIN",
]


# ---------------------------------------------------------------------------
# Merchant noise configuration
# ---------------------------------------------------------------------------

PAYMENT_GATEWAYS = [
    "PAYTM",
    "PHONEPE",
    "GPAY",
    "BHIM",
]

UPI_SUFFIXES = [
    "paytm",
    "ybl",
    "okaxis",
    "oksbi",
    "okicici",
]

REFERENCE_LENGTH = 6


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

@dataclass
class UserProfile:
    user_id: str
    monthly_salary: float
    monthly_rent: float
    typical_dining: float
    typical_groceries: float
    typical_transport: float
    typical_shopping: float
    typical_utilities: float
    monthly_investment: float
    opening_balance: float


# ---------------------------------------------------------------------------
# Ground-truth transaction
# ---------------------------------------------------------------------------

@dataclass
class SyntheticTransaction:
    transaction_id: str
    user_id: str
    date: date
    raw_description: str
    canonical_merchant: str
    merchant_id: str
    category: str
    amount: float
    transaction_type: str
    balance: Optional[float] = None
    is_injected_anomaly: bool = False
    anomaly_type: Optional[str] = None


# ---------------------------------------------------------------------------
# User profile generation
# ---------------------------------------------------------------------------

def generate_user_profile(user_id: str, rng: np.random.Generator) -> UserProfile:
    salary = float(
        rng.choice(
            [35000, 42000, 50000, 60000, 70000, 85000, 100000, 125000]
        )
    )

    # Fixed obligations
    rent_ratio = rng.uniform(0.20, 0.32)
    monthly_rent = round((salary * rent_ratio) / 500) * 500

    utility_ratio = rng.uniform(0.04, 0.07)
    typical_utilities = salary * utility_ratio

    investment_ratio = rng.uniform(0.05, 0.15)
    monthly_investment = round((salary * investment_ratio) / 500) * 500

    # Allocate a realistic discretionary spending budget.
    # This keeps normal spending below income while still allowing
    # meaningful variation between users.
    discretionary_budget = salary * rng.uniform(0.25, 0.35)

    dining_share = rng.uniform(0.15, 0.25)
    groceries_share = rng.uniform(0.25, 0.35)
    transport_share = rng.uniform(0.10, 0.20)
    shopping_share = 1 - (
        dining_share + groceries_share + transport_share
    )

    typical_dining = discretionary_budget * dining_share
    typical_groceries = discretionary_budget * groceries_share
    typical_transport = discretionary_budget * transport_share
    typical_shopping = discretionary_budget * shopping_share

    opening_balance = round(
        salary * rng.uniform(0.75, 1.5) / 100
    ) * 100

    return UserProfile(
        user_id=user_id,
        monthly_salary=salary,
        monthly_rent=monthly_rent,
        typical_dining=round(typical_dining, 2),
        typical_groceries=round(typical_groceries, 2),
        typical_transport=round(typical_transport, 2),
        typical_shopping=round(typical_shopping, 2),
        typical_utilities=round(typical_utilities, 2),
        monthly_investment=monthly_investment,
        opening_balance=opening_balance,
    )



# ---------------------------------------------------------------------------
# Transaction helpers
# ---------------------------------------------------------------------------

def random_day_in_range(
    year: int,
    month: int,
    start_day: int,
    end_day: int,
    rng,
) -> date:
    """
    Return a random valid date within a day range for a given month.
    """

    last_day = calendar.monthrange(year, month)[1]

    start = min(start_day, last_day)
    end = min(end_day, last_day)

    day = int(rng.integers(start, end + 1))

    return date(year, month, day)


def create_transaction(
    transaction_id: str,
    user_id: str,
    transaction_date: date,
    description: str,
    merchant: Merchant,
    amount: float,
    transaction_type: str,
) -> SyntheticTransaction:
    """
    Create a ground-truth synthetic transaction.
    """

    return SyntheticTransaction(
        transaction_id=transaction_id,
        user_id=user_id,
        date=transaction_date,
        raw_description=description,
        canonical_merchant=merchant.name,
        merchant_id=merchant.merchant_id,
        category=merchant.category,
        amount=round(float(amount), 2),
        transaction_type=transaction_type,
    )


def generate_noisy_description(
    merchant: Merchant,
    rng,
) -> str:
    """
    Generate a deliberately noisy bank/UPI transaction description.

    The same canonical merchant can produce many different raw
    representations.
    """

    name = merchant.name.upper()

    # Remove characters that aren't useful in synthetic bank narrations.
    compact_name = (
        name.replace(" ", "")
        .replace("'", "")
        .replace("-", "")
    )

    pattern = int(rng.integers(0, 8))

    reference = int(rng.integers(100000, 999999))
    gateway = rng.choice(PAYMENT_GATEWAYS)
    suffix = rng.choice(UPI_SUFFIXES)

    if pattern == 0:
        return name

    if pattern == 1:
        return f"{gateway}*{compact_name}"

    if pattern == 2:
        return f"{compact_name}*ORDER{reference}"

    if pattern == 3:
        return f"UPI/{reference}/{name}/{suffix}"

    if pattern == 4:
        return f"UPI-{compact_name}-{reference}"

    if pattern == 5:
        pos_number = int(rng.integers(1000, 9999))
        return f"POS {pos_number} {name}"

    if pattern == 6:
        return f"{gateway}*{compact_name}BLR"

    return f"UPI/{reference}/{compact_name}/{suffix}"




# ---------------------------------------------------------------------------
# Recurring transactions
# ---------------------------------------------------------------------------

def generate_salary(
    profile: UserProfile,
    year: int,
    month: int,
    transaction_id: str,
    rng,
) -> SyntheticTransaction:
    """
    Generate the user's monthly salary credit.
    """

    transaction_date = random_day_in_range(
        year,
        month,
        28,
        31,
        rng,
    )

    description = f"NEFT-HDFC0001234-SALARY-{calendar.month_abbr[month].upper()}"

    merchant = Merchant(
        "salary",
        "Salary",
        "salary/income",
    )

    return create_transaction(
        transaction_id=transaction_id,
        user_id=profile.user_id,
        transaction_date=transaction_date,
        description=description,
        merchant=merchant,
        amount=profile.monthly_salary,
        transaction_type="credit",
    )


def generate_rent(
    profile: UserProfile,
    year: int,
    month: int,
    transaction_id: str,
    rng,
) -> SyntheticTransaction:
    """
    Generate monthly rent payment.
    """

    transaction_date = random_day_in_range(
        year,
        month,
        1,
        5,
        rng,
    )

    description = "UPI/423819271/LANDLORD/RENT"

    merchant = Merchant(
        "rent",
        "Rent",
        "rent",
    )

    return create_transaction(
        transaction_id=transaction_id,
        user_id=profile.user_id,
        transaction_date=transaction_date,
        description=description,
        merchant=merchant,
        amount=profile.monthly_rent,
        transaction_type="debit",
    )


def generate_subscriptions(
    profile: UserProfile,
    year: int,
    month: int,
    transaction_id_start: int,
    rng,
) -> list[SyntheticTransaction]:
    """
    Generate recurring subscription transactions.
    """

    subscriptions = [
        ("netflix", 649),
        ("spotify", 119),
        ("youtube", 149),
        ("gym", 1499),
    ]

    transactions = []

    for offset, (merchant_id, amount) in enumerate(subscriptions):
        merchant = next(
            merchant
            for merchant in MERCHANTS
            if merchant.merchant_id == merchant_id
        )

        transaction_date = random_day_in_range(
            year,
            month,
            5,
            15,
            rng,
        )

        description = f"UPI/{rng.integers(100000, 999999)}/{merchant.name.upper()}"

        transactions.append(
            create_transaction(
                transaction_id=f"txn_{transaction_id_start + offset:06d}",
                user_id=profile.user_id,
                transaction_date=transaction_date,
                description=description,
                merchant=merchant,
                amount=amount,
                transaction_type="debit",
            )
        )

    return transactions



# ---------------------------------------------------------------------------
# Everyday spending
# ---------------------------------------------------------------------------

def get_merchant(merchant_id: str) -> Merchant:
    """Return a merchant from the merchant registry."""

    for merchant in MERCHANTS:
        if merchant.merchant_id == merchant_id:
            return merchant

    raise ValueError(f"Unknown merchant: {merchant_id}")


def generate_spending_amount(
    category: str,
    profile: UserProfile,
    rng,
) -> float:
    """
    Generate a realistic individual transaction amount based on
    the user's typical spending for that category.
    """

    if category == "food & dining":
        base = profile.typical_dining

        # Individual food orders are a fraction of monthly spending.
        amount = rng.lognormal(
            mean=np.log(max(base / 8, 100)),
            sigma=0.45,
        )

    elif category == "groceries":
        base = profile.typical_groceries

        amount = rng.lognormal(
            mean=np.log(max(base / 6, 150)),
            sigma=0.40,
        )

    elif category == "transport":
        base = profile.typical_transport

        amount = rng.lognormal(
            mean=np.log(max(base / 8, 100)),
            sigma=0.45,
        )

    elif category == "shopping":
        base = profile.typical_shopping

        amount = rng.lognormal(
            mean=np.log(max(base / 3, 300)),
            sigma=0.65,
        )

    else:
        amount = rng.uniform(100, 1000)

    return round(float(np.clip(amount, 50, 15000)), 2)


def choose_merchant_for_category(
    category: str,
    rng,
) -> Merchant:
    """Choose a merchant appropriate for a spending category."""

    merchants = [
        merchant
        for merchant in MERCHANTS
        if merchant.category == category
    ]

    if not merchants:
        raise ValueError(
            f"No merchants available for category: {category}"
        )

    index = int(rng.integers(0, len(merchants)))

    return merchants[index]


def generate_everyday_spending(
    profile: UserProfile,
    year: int,
    month: int,
    transaction_id_start: int,
    rng,
) -> list[SyntheticTransaction]:
    """
    Generate variable everyday spending for one month.

    Spending frequency varies by category and by user.
    """

    spending_config = {
        "food & dining": (5, 14),
        "groceries": (4, 9),
        "transport": (4, 12),
        "shopping": (1, 5),
    }

    transactions = []
    transaction_number = transaction_id_start

    for category, (minimum, maximum) in spending_config.items():

        transaction_count = int(
            rng.integers(minimum, maximum + 1)
        )

        for _ in range(transaction_count):

            merchant = choose_merchant_for_category(
                category,
                rng,
            )

            transaction_date = random_day_in_range(
                year,
                month,
                1,
                calendar.monthrange(year, month)[1],
                rng,
            )

            amount = generate_spending_amount(
                category,
                profile,
                rng,
            )

            description = generate_noisy_description(
                merchant,
                rng,
            )

            transactions.append(
                create_transaction(
                    transaction_id=f"txn_{transaction_number:06d}",
                    user_id=profile.user_id,
                    transaction_date=transaction_date,
                    description=description,
                    merchant=merchant,
                    amount=amount,
                    transaction_type="debit",
                )
            )

            transaction_number += 1

    return transactions


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def generate_utilities(
    profile: UserProfile,
    year: int,
    month: int,
    transaction_id_start: int,
    rng,
) -> list[SyntheticTransaction]:
    """Generate monthly utility payments."""

    utility_merchants = [
        ("electricity", "BBPS/ELECTRICITY/BESCOM"),
        ("internet", "UPI/928371/AIRTELFIBER"),
        ("mobile", "UPI/728391/JIORECHARGE"),
    ]

    transactions = []

    utility_amounts = {
        "electricity": rng.normal(
            profile.typical_utilities * 0.45,
            250,
        ),
        "internet": rng.choice([799, 899, 999]),
        "mobile": rng.choice([299, 399, 499, 599]),
    }

    for offset, (merchant_id, default_description) in enumerate(
        utility_merchants
    ):
        merchant = get_merchant(merchant_id)

        amount = max(
            100,
            utility_amounts[merchant_id],
        )

        # Electricity keeps its bank-bill style narration.
        if merchant_id == "electricity":
            description = default_description
        else:
            description = generate_noisy_description(
                merchant,
                rng,
            )

        transaction_date = random_day_in_range(
            year,
            month,
            10,
            25,
            rng,
        )

        transactions.append(
            create_transaction(
                transaction_id=f"txn_{transaction_id_start + offset:06d}",
                user_id=profile.user_id,
                transaction_date=transaction_date,
                description=description,
                merchant=merchant,
                amount=amount,
                transaction_type="debit",
            )
        )

    return transactions


# ---------------------------------------------------------------------------
# P2P transfers
# ---------------------------------------------------------------------------

P2P_NAMES = [
    "RAJESH KUMAR",
    "ROHIT S",
    "PRIYA SHARMA",
    "AMIT VERMA",
    "NEHA GUPTA",
    "VIKAS JAIN",
]


def generate_p2p_transfers(
    profile: UserProfile,
    year: int,
    month: int,
    transaction_id_start: int,
    rng,
) -> list[SyntheticTransaction]:
    """Generate person-to-person UPI transfers."""

    transaction_count = int(rng.integers(2, 7))

    transactions = []

    merchant = Merchant(
        "p2p",
        "Person-to-Person Transfer",
        "transfers/P2P",
    )

    for offset in range(transaction_count):

        person = rng.choice(P2P_NAMES)
        reference = int(rng.integers(100000, 999999))

        pattern = int(rng.integers(0, 3))

        if pattern == 0:
            description = (
                f"UPI/{reference}/{person}/paytm"
            )

        elif pattern == 1:
            description = (
                f"IMPS/P2A/{reference}/{person.title()}"
            )

        else:
            description = (
                f"UPI-{reference}-{person}"
            )

        transaction_date = random_day_in_range(
            year,
            month,
            1,
            calendar.monthrange(year, month)[1],
            rng,
        )

        amount = round(
            float(rng.lognormal(np.log(1200), 0.65)),
            2,
        )

        amount = min(max(amount, 100), 10000)

        transactions.append(
            create_transaction(
                transaction_id=f"txn_{transaction_id_start + offset:06d}",
                user_id=profile.user_id,
                transaction_date=transaction_date,
                description=description,
                merchant=merchant,
                amount=amount,
                transaction_type="debit",
            )
        )

    return transactions


# ---------------------------------------------------------------------------
# Investments
# ---------------------------------------------------------------------------

def generate_investment(
    profile: UserProfile,
    year: int,
    month: int,
    transaction_id: str,
    rng,
) -> SyntheticTransaction:
    """Generate a monthly investment/SIP transaction."""

    transaction_date = random_day_in_range(
        year,
        month,
        5,
        15,
        rng,
    )

    investment_names = [
        "GROWW SIP",
        "ZERODHA SIP",
        "MUTUAL FUND SIP",
        "NIFTY INDEX SIP",
    ]

    description = str(rng.choice(investment_names))

    merchant = Merchant(
        "investment",
        "Investment",
        "investments",
    )

    return create_transaction(
        transaction_id=transaction_id,
        user_id=profile.user_id,
        transaction_date=transaction_date,
        description=description,
        merchant=merchant,
        amount=profile.monthly_investment,
        transaction_type="debit",
    )


def generate_month(
    profile: UserProfile,
    year: int,
    month: int,
    transaction_id_start: int,
    rng,
) -> list[SyntheticTransaction]:
    """
    Generate a complete month of transactions for one user.
    """

    transactions = []
    next_id = transaction_id_start

    # ---------------------------------------------------------------
    # Salary
    # ---------------------------------------------------------------

    transactions.append(
        generate_salary(
            profile=profile,
            year=year,
            month=month,
            transaction_id=f"txn_{next_id:06d}",
            rng=rng,
        )
    )

    next_id += 1

    # ---------------------------------------------------------------
    # Rent
    # ---------------------------------------------------------------

    transactions.append(
        generate_rent(
            profile=profile,
            year=year,
            month=month,
            transaction_id=f"txn_{next_id:06d}",
            rng=rng,
        )
    )

    next_id += 1

    # ---------------------------------------------------------------
    # Subscriptions
    # ---------------------------------------------------------------

    subscriptions = generate_subscriptions(
        profile=profile,
        year=year,
        month=month,
        transaction_id_start=next_id,
        rng=rng,
    )

    transactions.extend(subscriptions)
    next_id += len(subscriptions)

    # ---------------------------------------------------------------
    # Everyday spending
    # ---------------------------------------------------------------

    everyday = generate_everyday_spending(
        profile=profile,
        year=year,
        month=month,
        transaction_id_start=next_id,
        rng=rng,
    )

    transactions.extend(everyday)
    next_id += len(everyday)

    # ---------------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------------

    utilities = generate_utilities(
        profile=profile,
        year=year,
        month=month,
        transaction_id_start=next_id,
        rng=rng,
    )

    transactions.extend(utilities)
    next_id += len(utilities)

    # ---------------------------------------------------------------
    # P2P transfers
    # ---------------------------------------------------------------

    p2p = generate_p2p_transfers(
        profile=profile,
        year=year,
        month=month,
        transaction_id_start=next_id,
        rng=rng,
    )

    transactions.extend(p2p)
    next_id += len(p2p)

    # ---------------------------------------------------------------
    # Investment
    # ---------------------------------------------------------------

    investment = generate_investment(
        profile=profile,
        year=year,
        month=month,
        transaction_id=f"txn_{next_id:06d}",
        rng=rng,
    )

    transactions.append(investment)

    return transactions


def calculate_running_balances(
    transactions: list[SyntheticTransaction],
    profiles: list[UserProfile],
) -> list[SyntheticTransaction]:
    """
    Calculate chronological running balances for each synthetic user.

    Transactions are sorted by:
    1. user_id
    2. transaction date
    3. transaction_id

    Credits increase the balance.
    Debits decrease the balance.
    """

    profile_map = {
        profile.user_id: profile
        for profile in profiles
    }

    # Sort without modifying the original list.
    sorted_transactions = sorted(
        transactions,
        key=lambda transaction: (
            transaction.user_id,
            transaction.date,
            transaction.transaction_id,
        ),
    )

    balances = {
        profile.user_id: profile.opening_balance
        for profile in profiles
    }

    for transaction in sorted_transactions:
        if transaction.transaction_type == "credit":
            balances[transaction.user_id] += transaction.amount

        elif transaction.transaction_type == "debit":
            balances[transaction.user_id] -= transaction.amount

        else:
            raise ValueError(
                f"Unknown transaction type: "
                f"{transaction.transaction_type}"
            )

        transaction.balance = round(
            balances[transaction.user_id],
            2,
        )

    return sorted_transactions


def inject_anomalies(
    transactions: list[SyntheticTransaction],
    profiles: list[UserProfile],
    rng: np.random.Generator,
) -> list[SyntheticTransaction]:
    """
    Inject known anomalies into the synthetic dataset.

    Anomaly types:
    1. large_one_off       - unusually large individual transaction
    2. category_spike      - unusually high spending in one category/month
    3. unusual_purchase    - one-off purchase outside the user's normal pattern
    """

    profile_map = {
        profile.user_id: profile
        for profile in profiles
    }

    transactions_by_user = {}

    for transaction in transactions:
        transactions_by_user.setdefault(
            transaction.user_id,
            []
        ).append(transaction)

    # ---------------------------------------------------------
    # 1. Large one-off purchase
    # ---------------------------------------------------------

    user_id = str(rng.choice(list(transactions_by_user.keys())))
    user_transactions = transactions_by_user[user_id]

    candidates = [
        transaction
        for transaction in user_transactions
        if transaction.transaction_type == "debit"
        and transaction.category in {
            "shopping",
            "food & dining",
            "transport",
        }
    ]

    target = rng.choice(candidates)

    original_amount = target.amount

    target.amount = round(
        max(
            original_amount * 8,
            profile_map[user_id].monthly_salary * 0.5,
        ),
        2,
    )

    target.is_injected_anomaly = True
    target.anomaly_type = "large_one_off"

    # ---------------------------------------------------------
    # 2. Category spending spike
    # ---------------------------------------------------------

    user_id = str(rng.choice(list(transactions_by_user.keys())))
    user_transactions = transactions_by_user[user_id]

    categories = [
        "food & dining",
        "groceries",
        "shopping",
        "transport",
    ]

    category = str(rng.choice(categories))

    # Pick a month only after enough historical months exist.
    #
    # The first 4 months are reserved as warm-up history.
    # This gives the detector at least 4 prior months when
    # evaluating the injected category spike.
    months = sorted(
        {
            (transaction.date.year, transaction.date.month)
            for transaction in user_transactions
        }
    )

    minimum_history_months = 4

    if len(months) <= minimum_history_months:
        raise ValueError(
            "Not enough historical months to inject "
            "a category spike."
        )

    eligible_months = months[
        minimum_history_months:
    ]

    year, month = eligible_months[
        int(rng.integers(0, len(eligible_months)))
    ]

    category_transactions = [
        transaction
        for transaction in user_transactions
        if (
            transaction.category == category
            and transaction.date.year == year
            and transaction.date.month == month
            and transaction.transaction_type == "debit"
        )
    ]

    # Increase several existing transactions rather than
    # creating an obviously artificial single transaction.
    if category_transactions:
        spike_factor = float(
            rng.uniform(2.0, 3.0)
        )

        for transaction in category_transactions:
            transaction.amount = round(
                transaction.amount * spike_factor,
                2,
            )

            transaction.is_injected_anomaly = True
            transaction.anomaly_type = "category_spike"

    # ---------------------------------------------------------
    # 3. Unusual one-off purchase
    # ---------------------------------------------------------

    user_id = str(rng.choice(list(transactions_by_user.keys())))
    user_transactions = transactions_by_user[user_id]

    # Create a deliberately unusual purchase using an existing
    # merchant but an unusually large amount.
    shopping_transactions = [
        transaction
        for transaction in user_transactions
        if (
            transaction.category == "shopping"
            and transaction.transaction_type == "debit"
        )
    ]

    if shopping_transactions:
        target = rng.choice(shopping_transactions)

        target.amount = round(
        max(
            target.amount * float(rng.uniform(6.0, 10.0)),
            profile_map[user_id].monthly_salary * 0.25,
        ),
        2,
    )

        target.is_injected_anomaly = True
        target.anomaly_type = "unusual_purchase"

    return transactions


def validate_injected_anomalies(
    transactions: list[SyntheticTransaction],
) -> None:
    """Print a summary of the anomalies injected into the dataset."""

    anomalies = [
        transaction
        for transaction in transactions
        if transaction.is_injected_anomaly
    ]

    print("\nINJECTED ANOMALIES")
    print("----------------------------------------")
    print(f"Total anomaly transactions: {len(anomalies)}")

    if not anomalies:
        print("WARNING: No anomalies were injected.")
        return

    anomaly_counts = {}

    for transaction in anomalies:
        anomaly_counts[transaction.anomaly_type] = (
            anomaly_counts.get(transaction.anomaly_type, 0) + 1
        )

    for anomaly_type, count in sorted(anomaly_counts.items()):
        print(f"{anomaly_type}: {count}")

    print("\nANOMALY DETAILS")
    print("----------------------------------------")

    for transaction in anomalies:
        print(
            f"{transaction.transaction_id} | "
            f"{transaction.user_id} | "
            f"{transaction.date} | "
            f"{transaction.raw_description} | "
            f"₹{transaction.amount:,.2f} | "
            f"{transaction.anomaly_type}"
        )


def validate_balances(
    transactions: list[SyntheticTransaction],
    profiles: list[UserProfile],
) -> None:
    """Verify that every running balance reconciles correctly."""

    profile_map = {
        profile.user_id: profile
        for profile in profiles
    }

    transactions_by_user = {}

    for transaction in transactions:
        transactions_by_user.setdefault(
            transaction.user_id,
            []
        ).append(transaction)

    print("\nBALANCE VALIDATION")
    print("----------------------------------------")

    total_checked = 0

    for user_id, user_transactions in transactions_by_user.items():

        user_transactions = sorted(
            user_transactions,
            key=lambda transaction: (
                transaction.date,
                transaction.transaction_id,
            ),
        )

        expected_balance = profile_map[user_id].opening_balance

        for transaction in user_transactions:

            if transaction.transaction_type == "credit":
                expected_balance += transaction.amount

            elif transaction.transaction_type == "debit":
                expected_balance -= transaction.amount

            else:
                raise ValueError(
                    f"Unknown transaction type: "
                    f"{transaction.transaction_type}"
                )

            expected_balance = round(expected_balance, 2)

            if transaction.balance != expected_balance:
                raise AssertionError(
                    f"Balance mismatch for "
                    f"{transaction.transaction_id}: "
                    f"expected {expected_balance}, "
                    f"got {transaction.balance}"
                )

            total_checked += 1

        print(
            f"{user_id}: PASS "
            f"({len(user_transactions)} transactions)"
        )

    print("----------------------------------------")
    print(f"Total transactions checked: {total_checked}")
    print("All balances reconcile successfully.")


def export_bank_a(
    transactions: list[SyntheticTransaction],
    output_path: str,
) -> None:
    """
    Export transactions in Bank A's CSV format.

    Format:
        Date, Description, Debit, Credit, Balance
    """

    import csv

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "Date",
            "Description",
            "Debit",
            "Credit",
            "Balance",
        ])

        for transaction in transactions:
            debit = (
                transaction.amount
                if transaction.transaction_type == "debit"
                else ""
            )

            credit = (
                transaction.amount
                if transaction.transaction_type == "credit"
                else ""
            )

            writer.writerow([
                transaction.date.strftime("%d/%m/%Y"),
                transaction.raw_description,
                debit,
                credit,
                transaction.balance,
            ])


def export_bank_b(
    transactions: list[SyntheticTransaction],
    output_path: str,
) -> None:
    """
    Export transactions in Bank B's CSV format.

    Format:
        Txn Date, Value Date, Narration,
        Withdrawal Amt, Deposit Amt, Closing Balance
    """

    import csv

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "Txn Date",
            "Value Date",
            "Narration",
            "Withdrawal Amt",
            "Deposit Amt",
            "Closing Balance",
        ])

        for transaction in transactions:
            withdrawal = (
                transaction.amount
                if transaction.transaction_type == "debit"
                else ""
            )

            deposit = (
                transaction.amount
                if transaction.transaction_type == "credit"
                else ""
            )

            writer.writerow([
                transaction.date.strftime("%d-%m-%Y"),
                transaction.date.strftime("%d-%m-%Y"),
                transaction.raw_description,
                withdrawal,
                deposit,
                transaction.balance,
            ])


# ---------------------------------------------------------------------------
# Multi-month dataset generation
# ---------------------------------------------------------------------------

def generate_dataset(
    n_users: int = 5,
    months: int = 12,
    seed: int = 42,
) -> tuple[list[SyntheticTransaction], list[UserProfile]]:
    """
    Generate a multi-user, multi-month synthetic transaction dataset.

    Parameters
    ----------
    n_users : int
        Number of synthetic users.

    months : int
        Number of months of transaction history.

    seed : int
        Random seed for reproducibility.

    Returns
    -------
    transactions : list[SyntheticTransaction]
        All generated transactions.

    profiles : list[UserProfile]
        Financial profiles for all generated users.
    """

    rng = np.random.default_rng(seed)

    transactions = []
    profiles = []

    # Start 12 months before the current reference month.
    start_year = 2025
    start_month = 10

    transaction_counter = 1

    for user_number in range(1, n_users + 1):

        user_id = f"user_{user_number:03d}"

        profile = generate_user_profile(
            user_id=user_id,
            rng=rng,
        )

        profiles.append(profile)

        for month_offset in range(months):

            total_months = (
                start_year * 12
                + (start_month - 1)
                + month_offset
            )

            year = total_months // 12
            month = total_months % 12 + 1

            monthly_transactions = generate_month(
                profile=profile,
                year=year,
                month=month,
                transaction_id_start=transaction_counter,
                rng=rng,
            )

            transactions.extend(monthly_transactions)

            transaction_counter += len(monthly_transactions)

    transactions = inject_anomalies(
        transactions=transactions,
        profiles=profiles,
        rng=rng,
    )

    transactions = calculate_running_balances(
        transactions=transactions,
        profiles=profiles,
    )

    return transactions, profiles


if __name__ == "__main__":
    transactions, profiles = generate_dataset(
        n_users=5,
        months=12,
        seed=42,
    )

    user_001_transactions = [
        transaction
        for transaction in transactions
        if transaction.user_id == "user_001"
    ]

    export_bank_a(
        transactions=user_001_transactions,
        output_path="data/sample/bank_a_user_001.csv",
    )

    print("\nBank A CSV exported:")
    print("data/sample/bank_a_user_001.csv")

    export_bank_b(
        transactions=user_001_transactions,
        output_path="data/sample/bank_b_user_001.csv",
    )

    print("\nBank B CSV exported:")
    print("data/sample/bank_b_user_001.csv")


    validate_balances(
        transactions=transactions,
        profiles=profiles,
    )

    print("\nDATASET SUMMARY")
    print("-" * 40)

    print(f"Users: {len(profiles)}")
    print(f"Transactions: {len(transactions)}")

    print("\nUSER PROFILES")
    print("-" * 40)

    for profile in profiles:
        print(profile)

    print("\nFIRST 10 TRANSACTIONS")
    print("-" * 40)

    for transaction in transactions[:10]:
        print(transaction)

    print("\nLAST 10 TRANSACTIONS")
    print("-" * 40)

    for transaction in transactions[-10:]:
        print(transaction)