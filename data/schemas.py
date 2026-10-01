from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Transaction:
    """
    Canonical transaction schema used throughout the application.

    All bank-specific CSV formats are converted into this structure
    during ingestion.
    """

    date: date
    description: str

    debit: float
    credit: float

    balance: Optional[float]

    transaction_type: str

    source_file: Optional[str] = None

    reference_number: Optional[str] = None


@dataclass
class Counterparty:
    """
    Represents a person or account involved in a
    transfer/P2P transaction.
    """

    counterparty_id: str
    name: str
    category: str = "transfers/P2P"


@dataclass
class ClassificationResult:
    """
    Result produced by the transaction classifier.

    A transaction may resolve either to a merchant
    or to a counterparty, but not necessarily both.
    """

    merchant_id: Optional[str]
    merchant_name: Optional[str]
    counterparty_id: Optional[str]
    counterparty_name: Optional[str]
    category: Optional[str]
    method: str
    confidence: float