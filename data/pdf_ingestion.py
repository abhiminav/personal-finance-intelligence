from datetime import datetime
from pathlib import Path
import re

import pdfplumber

from data.schemas import Transaction


DATE_PATTERNS = (
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d/%m/%y",
    "%d-%m-%y",
)


def parse_pdf_date(value: str):
    """
    Parse a date commonly found in Indian bank statements.

    Supported formats:
        DD/MM/YYYY
        DD-MM-YYYY
        DD/MM/YY
        DD-MM-YY
    """

    value = value.strip()

    for pattern in DATE_PATTERNS:
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue

    raise ValueError(f"Unsupported PDF transaction date: {value}")


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text from a PDF statement.

    This function only handles ordinary, non-encrypted PDFs.
    Password-protected PDFs will be added in a later step.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Expected a PDF file.")

    pages = []

    with pdfplumber.open(path) as pdf:
        if not pdf.pages:
            raise ValueError("PDF file contains no pages.")

        for page in pdf.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

    if not pages:
        raise ValueError(
            "No extractable text was found in the PDF. "
            "The statement may be scanned or image-based."
        )

    return "\n".join(pages)


def _parse_amount(value: str) -> float:
    """Convert a bank statement amount into a float."""

    cleaned = value.strip()
    cleaned = cleaned.replace("₹", "")
    cleaned = cleaned.replace(",", "")
    cleaned = cleaned.replace(" ", "")

    if not cleaned:
        return 0.0

    return float(cleaned)


def _is_date(value: str) -> bool:
    """Return True when the value looks like a supported date."""

    try:
        parse_pdf_date(value)
        return True
    except ValueError:
        return False


def _parse_transaction_line(
    line: str,
    source_file: str,
) -> Transaction | None:
    """
    Parse a common single-line bank statement transaction.

    This text-only parser supports rows where debit and credit are
    explicitly represented by numeric values. It remains as a
    fallback for PDFs where column positions cannot be recovered.
    """

    line = line.strip()

    if not line:
        return None

    parts = line.split()

    if len(parts) < 4:
        return None

    if not _is_date(parts[0]):
        return None

    transaction_date = parse_pdf_date(parts[0])

    numeric_values = []
    numeric_start = None

    for index in range(1, len(parts)):
        remaining = parts[index:]

        if len(remaining) < 2:
            continue

        try:
            values = [_parse_amount(value) for value in remaining]
        except ValueError:
            continue

        if len(values) >= 2:
            numeric_start = index
            numeric_values = values
            break

    if numeric_start is None:
        return None

    description_parts = parts[1:numeric_start]

    if not description_parts:
        return None

    description = " ".join(description_parts)

    if len(numeric_values) == 3:
        debit = numeric_values[0]
        credit = numeric_values[1]
        balance = numeric_values[2]
    elif len(numeric_values) == 2:
        debit = numeric_values[0]
        credit = 0.0
        balance = numeric_values[1]
    else:
        return None

    transaction_type = (
        "credit"
        if credit > 0 and debit <= 0
        else "debit"
    )

    return Transaction(
        date=transaction_date,
        description=description,
        debit=debit,
        credit=credit,
        balance=balance,
        transaction_type=transaction_type,
        source_file=source_file,
    )


def parse_pdf_text(
    text: str,
    source_file: str,
) -> list[Transaction]:
    """
    Parse extracted PDF text into canonical transactions.

    Header rows and unrelated statement text are ignored.
    """

    transactions = []

    for line in text.splitlines():
        transaction = _parse_transaction_line(
            line,
            source_file,
        )

        if transaction is not None:
            transactions.append(transaction)

    if not transactions:
        raise ValueError(
            "No transaction rows could be parsed from the PDF."
        )

    return transactions


def _group_words_by_line(words: list[dict]) -> list[list[dict]]:
    """Group pdfplumber words into visual text lines."""

    lines = []

    for word in sorted(words, key=lambda item: (item["top"], item["x0"])):
        placed = False

        for line in lines:
            reference_top = line[0]["top"]

            if abs(word["top"] - reference_top) <= 3:
                line.append(word)
                placed = True
                break

        if not placed:
            lines.append([word])

    for line in lines:
        line.sort(key=lambda item: item["x0"])

    return lines


def detect_pdf_layout(words: list[dict]) -> dict[str, str] | None:
    """
    Detect the canonical transaction-column roles used by a PDF statement.

    Supports common Indian bank-statement header variants, including
    headers that pdfplumber may merge when adjacent columns are close.
    """

    if not words:
        return None

    header_top = min(
        float(word["top"])
        for word in words
    )

    header_tokens = []

    for word in words:
        if abs(float(word["top"]) - header_top) > 3:
            continue

        normalized = re.sub(
            r"[^A-Z]",
            "",
            word["text"].upper(),
        )

        if normalized:
            header_tokens.append(normalized)

    header_text = "".join(header_tokens)

    has_date = (
        "DATE" in header_text
        or "TXNDATE" in header_text
    )

    has_description = (
        "DESCRIPTION" in header_text
        or "NARRATION" in header_text
        or "PARTICULARS" in header_text
    )

    has_debit = (
        "DEBIT" in header_text
        or "WITHDRAWAL" in header_text
    )

    has_credit = (
        "CREDIT" in header_text
        or "DEPOSIT" in header_text
    )

    has_balance = (
        "BALANCE" in header_text
    )

    if not all(
        (
            has_date,
            has_description,
            has_debit,
            has_credit,
            has_balance,
        )
    ):
        return None

    return {
        "date": "date",
        "description": "description",
        "debit": "debit",
        "credit": "credit",
        "balance": "balance",
    }


def _find_column_positions(words: list[dict]) -> dict[str, float] | None:
    """
    Find the horizontal centers of the canonical transaction columns.

    Handles common bank-statement header variants and cases where
    pdfplumber merges adjacent headers.
    """

    if not words:
        return None

    layout = detect_pdf_layout(words)

    if layout is None:
        return None

    header_top = min(
        float(word["top"])
        for word in words
    )

    header_words = {}

    for word in words:
        if abs(float(word["top"]) - header_top) > 3:
            continue

        normalized = re.sub(
            r"[^A-Z]",
            "",
            word["text"].upper(),
        )

        x0 = float(word["x0"])
        x1 = float(word["x1"])
        center = (x0 + x1) / 2

        if normalized in {"DATE", "TXNDATE"}:
            header_words["date"] = center

        elif normalized in {
            "DESCRIPTION",
            "NARRATION",
            "PARTICULARS",
        }:
            header_words["description"] = center

        elif normalized in {"DEBIT", "WITHDRAWAL"}:
            header_words["debit"] = center

        elif normalized in {"CREDIT", "DEPOSIT"}:
            header_words["credit"] = center

        elif normalized == "BALANCE":
            header_words["balance"] = center

        elif normalized in {
            "WITHDRAWALDEPOSIT",
            "DEBITCREDIT",
        }:
            if normalized == "WITHDRAWALDEPOSIT":
                left_label = "WITHDRAWAL"
                right_label = "DEPOSIT"
            else:
                left_label = "DEBIT"
                right_label = "CREDIT"

            left_length = len(left_label)
            right_length = len(right_label)
            total_length = left_length + right_length

            split_x = x0 + (
                (x1 - x0)
                * left_length
                / total_length
            )

            header_words["debit"] = (
                x0 + split_x
            ) / 2

            header_words["credit"] = (
                split_x + x1
            ) / 2

        elif normalized == "CLOSINGBALANCE":
            header_words["balance"] = center

    # Handle "CLOSING BALANCE" when pdfplumber extracts
    # the two words separately.
    closing_word = None
    balance_word = None

    for word in words:
        if abs(float(word["top"]) - header_top) > 3:
            continue

        normalized = re.sub(
            r"[^A-Z]",
            "",
            word["text"].upper(),
        )

        if normalized == "CLOSING":
            closing_word = word

        elif normalized == "BALANCE":
            balance_word = word

    if closing_word is not None and balance_word is not None:
        combined_x0 = min(
            float(closing_word["x0"]),
            float(balance_word["x0"]),
        )

        combined_x1 = max(
            float(closing_word["x1"]),
            float(balance_word["x1"]),
        )

        header_words["balance"] = (
            combined_x0 + combined_x1
        ) / 2

    required = {
        "date",
        "description",
        "debit",
        "credit",
        "balance",
    }

    if not required.issubset(header_words):
        return None

    return {
        "date": header_words["date"],
        "description": header_words["description"],
        "debit": header_words["debit"],
        "credit": header_words["credit"],
        "balance": header_words["balance"],
    }


def _nearest_column(x_center: float, columns: dict[str, float]) -> str:
    """Return the statement column nearest to an extracted word."""

    return min(
        columns,
        key=lambda name: abs(x_center - columns[name]),
    )


def _parse_positioned_page(
    page,
    source_file: str,
) -> list[Transaction]:
    """
    Parse a PDF page using word coordinates.

    This handles the important case where a bank statement leaves
    either Debit or Credit blank: PDF text extraction normally removes
    the blank cell, but the original x-coordinate remains available.

    Only numeric words are assigned to financial columns. This prevents
    ordinary description text such as "SALARY CREDIT" from being
    mistaken for the CREDIT column.
    """

    words = page.extract_words()

    if not words:
        return []

    columns = _find_column_positions(words)

    if columns is None:
        return []

    transactions = []

    for line_words in _group_words_by_line(words):
        if not line_words:
            continue

        first_text = line_words[0]["text"]

        if not _is_date(first_text):
            continue

        transaction_date = parse_pdf_date(first_text)

        description_parts = []
        debit = 0.0
        credit = 0.0
        balance = None

        for word in line_words[1:]:
            text = word["text"].strip()

            if not text:
                continue

            # Only numeric values can belong to financial columns.
            # All other text belongs to the transaction description.
            try:
                amount = _parse_amount(text)
            except ValueError:
                description_parts.append(text)
                continue

            x_center = (
                float(word["x0"]) + float(word["x1"])
            ) / 2

            column = _nearest_column(
                x_center,
                columns,
            )

            if column == "debit":
                debit += amount

            elif column == "credit":
                credit += amount

            elif column == "balance":
                balance = amount

            else:
                # A numeric value unexpectedly falling into the
                # description/date region should not silently become
                # part of the description.
                continue

        if not description_parts or balance is None:
            continue

        if debit <= 0 and credit <= 0:
            continue

        transaction_type = (
            "credit"
            if credit > 0 and debit <= 0
            else "debit"
        )

        transactions.append(
            Transaction(
                date=transaction_date,
                description=" ".join(description_parts),
                debit=debit,
                credit=credit,
                balance=balance,
                transaction_type=transaction_type,
                source_file=source_file,
            )
        )

    return transactions


def _extract_positioned_transactions(
    file_path: str,
    source_file: str,
) -> list[Transaction]:
    """Extract transactions from all PDF pages using coordinates."""

    transactions = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            transactions.extend(
                _parse_positioned_page(
                    page,
                    source_file,
                )
            )

    return transactions


def ingest_pdf(
    file_path: str,
) -> list[Transaction]:
    """
    Extract and normalize transactions from an ordinary PDF
    bank statement.

    The parser first attempts coordinate-aware extraction so blank
    debit/credit cells remain distinguishable. If the PDF does not
    expose the expected column headers/positions, it falls back to
    the text-only parser.
    """

    path = Path(file_path)

    # Validate the file and make sure it contains extractable text.
    text = extract_pdf_text(file_path)

    positioned_transactions = _extract_positioned_transactions(
        file_path,
        source_file=path.name,
    )

    if positioned_transactions:
        return positioned_transactions

    return parse_pdf_text(
        text,
        source_file=path.name,
    )