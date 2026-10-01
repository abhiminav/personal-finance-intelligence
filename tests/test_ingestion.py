from datetime import date
from data.ingestion import parse_date
import pytest

from data.ingestion import (
    detect_bank_format,
    ingest_csv,
    load_csv,
)
import pandas as pd


BANK_A_PATH = "data/sample/bank_a_user_001.csv"
BANK_B_PATH = "data/sample/bank_b_user_001.csv"
BANK_C_PATH = "data/sample/bank_c_user_001.csv"


def test_detect_bank_a():
    df = pd.DataFrame(
        columns=[
            "Date",
            "Description",
            "Debit",
            "Credit",
            "Balance",
        ]
    )

    assert detect_bank_format(df) == "bank_a"


def test_detect_bank_b():
    df = pd.DataFrame(
        columns=[
            "Txn Date",
            "Value Date",
            "Narration",
            "Withdrawal Amt",
            "Deposit Amt",
            "Closing Balance",
        ]
    )

    assert detect_bank_format(df) == "bank_b"


def test_reject_unknown_format():
    df = pd.DataFrame(
        columns=[
            "Date",
            "Merchant",
            "Amount",
        ]
    )

    with pytest.raises(ValueError):
        detect_bank_format(df)


def test_ingest_bank_a():
    transactions = ingest_csv(BANK_A_PATH)

    assert len(transactions) == 471

    first = transactions[0]

    assert first.date == date(2025, 10, 2)
    assert first.description == "PHONEPE*DMART"
    assert first.debit == 341.63
    assert first.credit == 0.0
    assert first.balance == 29258.37
    assert first.transaction_type == "debit"
    assert first.source_file == "bank_a_user_001.csv"


def test_ingest_bank_b():
    transactions = ingest_csv(BANK_B_PATH)

    assert len(transactions) == 471

    first = transactions[0]

    assert first.date == date(2025, 10, 2)
    assert first.description == "PHONEPE*DMART"
    assert first.debit == 341.63
    assert first.credit == 0.0
    assert first.balance == 29258.37
    assert first.transaction_type == "debit"
    assert first.source_file == "bank_b_user_001.csv"


def test_bank_formats_produce_same_transactions():
    bank_a = ingest_csv(BANK_A_PATH)
    bank_b = ingest_csv(BANK_B_PATH)

    assert len(bank_a) == len(bank_b)

    for transaction_a, transaction_b in zip(bank_a, bank_b):

        assert transaction_a.date == transaction_b.date
        assert transaction_a.description == transaction_b.description
        assert transaction_a.debit == transaction_b.debit
        assert transaction_a.credit == transaction_b.credit
        assert transaction_a.balance == transaction_b.balance
        assert (
            transaction_a.transaction_type
            == transaction_b.transaction_type
        )


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_csv("data/sample/does_not_exist.csv")


def test_detect_bank_c():
    df = pd.DataFrame(
        columns=[
            "Sl. No.",
            "Transaction Date",
            "Value Date",
            "Description",
            "Chq /Ref No.",
            "Amount",
            "Dr / Cr",
            "Balance",
        ]
    )

    assert detect_bank_format(df) == "bank_c"


def test_ingest_bank_c():
    transactions = ingest_csv(BANK_C_PATH)

    assert len(transactions) > 0

    first = transactions[0]

    assert first.date == date(2026, 9, 1)
    assert first.debit > 0
    assert first.credit == 0.0
    assert first.transaction_type == "debit"
    assert first.source_file == "bank_c_user_001.csv"


def test_parse_bank_a_iso_date():
    assert parse_date(
        "2025-10-02",
        "bank_a",
    ) == date(2025, 10, 2)