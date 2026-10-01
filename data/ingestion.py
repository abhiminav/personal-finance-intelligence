import csv

from datetime import datetime

from pathlib import Path

import pandas as pd

from data.schemas import Transaction


BANK_A_COLUMNS = {
    "Date",
    "Description",
    "Debit",
    "Credit",
    "Balance",
}


BANK_B_COLUMNS = {
    "Txn Date",
    "Value Date",
    "Narration",
    "Withdrawal Amt",
    "Deposit Amt",
    "Closing Balance",
}


BANK_C_COLUMNS = {
    "Sl. No.",
    "Transaction Date",
    "Value Date",
    "Description",
    "Chq /Ref No.",
    "Amount",
    "Dr / Cr",
    "Balance",
}


def _find_header_row(file_path: str) -> int:
    """
    Find the row containing the actual transaction-table header.

    Some bank CSV exports include account/customer metadata before
    the transaction table. This function scans the raw CSV until
    it finds a supported header.
    """

    path = Path(file_path)

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.reader(file)

        for row_index, row in enumerate(reader):
            columns = {
                str(value).strip()
                for value in row
                if str(value).strip()
            }

            if BANK_A_COLUMNS.issubset(columns):
                return row_index

            if BANK_B_COLUMNS.issubset(columns):
                return row_index

            if BANK_C_COLUMNS.issubset(columns):
                return row_index

    raise ValueError(
        "Could not find a supported transaction-table header "
        "in the CSV file."
    )


def detect_bank_format(df: pd.DataFrame) -> str:
    """
    Detect which supported bank CSV format was provided.

    Returns:

        "bank_a", "bank_b", or "bank_c"

    Raises:

        ValueError if the CSV format is not recognized.
    """

    columns = {
        str(column).strip()
        for column in df.columns
    }

    if BANK_A_COLUMNS.issubset(columns):
        return "bank_a"

    if BANK_B_COLUMNS.issubset(columns):
        return "bank_b"

    if BANK_C_COLUMNS.issubset(columns):
        return "bank_c"

    raise ValueError(
        "Unsupported bank CSV format. "
        f"Found columns: {list(df.columns)}"
    )


def parse_date(value: str, bank_format: str):
    """
    Parse a bank-specific date into a Python date object.
    """

    value = str(value).strip()

    if bank_format == "bank_a":
        for date_format in (
            "%d/%m/%Y",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(
                    value,
                    date_format,
                ).date()
            except ValueError:
                continue

        raise ValueError(
            f"Unsupported date format for bank_a: {value}"
        )

    if bank_format == "bank_b":
        return datetime.strptime(
            value,
            "%d-%m-%Y",
        ).date()

    if bank_format == "bank_c":
        for date_format in (
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y",
        ):
            try:
                return datetime.strptime(
                    value,
                    date_format,
                ).date()
            except ValueError:
                continue

        raise ValueError(
            f"Unsupported date format for bank_c: {value}"
        )

    raise ValueError(
        f"Unsupported bank format: {bank_format}"
    )


def _parse_amount(value) -> float:
    """
    Parse a bank amount such as:

        4278.88

        4,278.88

    into a float.
    """

    if pd.isna(value):
        return 0.0

    text = str(value).strip()

    if not text:
        return 0.0

    text = (
        text
        .replace(",", "")
        .replace("₹", "")
        .strip()
    )

    return float(text)


def load_csv(file_path: str) -> pd.DataFrame:
    """
    Load a bank CSV file into a pandas DataFrame.

    The actual transaction-table header may appear after
    metadata rows, so the header position is detected first.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {file_path}"
        )

    if path.suffix.lower() != ".csv":
        raise ValueError(
            "Expected a CSV file."
        )

    header_row = _find_header_row(file_path)

    df = pd.read_csv(
        path,
        skiprows=header_row,
    )

    if df.empty:
        raise ValueError(
            "CSV file is empty."
        )

    return df


def normalize_bank_a(
    df: pd.DataFrame,
    source_file: str,
) -> list[Transaction]:
    """
    Convert Bank A data into the canonical Transaction schema.
    """

    transactions = []

    for _, row in df.iterrows():

        debit = (
            float(row["Debit"])
            if pd.notna(row["Debit"])
            else 0.0
        )

        credit = (
            float(row["Credit"])
            if pd.notna(row["Credit"])
            else 0.0
        )

        transaction_type = (
            "credit"
            if credit > 0
            else "debit"
        )

        balance = (
            float(row["Balance"])
            if pd.notna(row["Balance"])
            else None
        )

        transactions.append(
            Transaction(
                date=parse_date(
                    str(row["Date"]),
                    "bank_a",
                ),
                description=str(
                    row["Description"]
                ),
                debit=debit,
                credit=credit,
                balance=balance,
                transaction_type=transaction_type,
                source_file=source_file,
                reference_number=None,
            )
        )

    return transactions


def normalize_bank_b(
    df: pd.DataFrame,
    source_file: str,
) -> list[Transaction]:
    """
    Convert Bank B data into the canonical Transaction schema.
    """

    transactions = []

    for _, row in df.iterrows():

        debit = (
            float(row["Withdrawal Amt"])
            if pd.notna(row["Withdrawal Amt"])
            else 0.0
        )

        credit = (
            float(row["Deposit Amt"])
            if pd.notna(row["Deposit Amt"])
            else 0.0
        )

        transaction_type = (
            "credit"
            if credit > 0
            else "debit"
        )

        balance = (
            float(row["Closing Balance"])
            if pd.notna(row["Closing Balance"])
            else None
        )

        transactions.append(
            Transaction(
                date=parse_date(
                    str(row["Txn Date"]),
                    "bank_b",
                ),
                description=str(
                    row["Narration"]
                ),
                debit=debit,
                credit=credit,
                balance=balance,
                transaction_type=transaction_type,
                source_file=source_file,
                reference_number=None,
            )
        )

    return transactions


def normalize_bank_c(
    df: pd.DataFrame,
    source_file: str,
) -> list[Transaction]:
    """
    Convert Bank C data into the canonical Transaction schema.

    Bank C provides:

        Transaction Date
        Value Date
        Description
        Chq /Ref No.
        Amount
        Dr / Cr
        Balance

    The first Dr / Cr describes the transaction direction.
    """

    transactions = []

    for _, row in df.iterrows():

        serial_number = row.get(
            "Sl. No.",
            None,
        )

        # Ignore footer rows such as:
        # "Closing Balance"
        # "Important Note:"
        #
        # Pandas may parse numeric serial numbers as floats
        # (for example, 1.0), so checking with str.isdigit()
        # would incorrectly skip valid transaction rows.
        if pd.isna(serial_number):
            continue

        try:
            float(serial_number)
        except (TypeError, ValueError):
            continue

        direction = str(
            row["Dr / Cr"]
        ).strip().upper()

        amount = _parse_amount(
            row["Amount"]
        )

        if direction == "DR":
            debit = amount
            credit = 0.0
            transaction_type = "debit"

        elif direction == "CR":
            debit = 0.0
            credit = amount
            transaction_type = "credit"

        else:
            raise ValueError(
                "Unsupported transaction direction "
                f"'{direction}' in bank_c statement."
            )

        balance = (
            _parse_amount(row["Balance"])
            if pd.notna(row["Balance"])
            else None
        )

        raw_reference = row.get(
            "Chq /Ref No.",
            None,
        )

        if pd.isna(raw_reference):
            reference_number = None
        else:
            reference_number = str(
                raw_reference
            ).strip()

            if not reference_number:
                reference_number = None

        transactions.append(
            Transaction(
                date=parse_date(
                    str(row["Transaction Date"]),
                    "bank_c",
                ),
                description=str(
                    row["Description"]
                ),
                debit=debit,
                credit=credit,
                balance=balance,
                transaction_type=transaction_type,
                source_file=source_file,
                reference_number=reference_number,
            )
        )

    return transactions


def ingest_csv(
    file_path: str,
) -> list[Transaction]:
    """
    Load and normalize a supported bank CSV statement.

    The function automatically detects the bank format and
    converts the data into the canonical Transaction schema.
    """

    path = Path(file_path)

    df = load_csv(file_path)

    bank_format = detect_bank_format(df)

    source_file = path.name

    if bank_format == "bank_a":
        return normalize_bank_a(
            df,
            source_file,
        )

    if bank_format == "bank_b":
        return normalize_bank_b(
            df,
            source_file,
        )

    if bank_format == "bank_c":
        return normalize_bank_c(
            df,
            source_file,
        )

    raise ValueError(
        f"Unsupported bank format: {bank_format}"
    )