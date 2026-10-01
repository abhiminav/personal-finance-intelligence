from datetime import date

import pytest

from data.pdf_ingestion import (
    extract_pdf_text,
    ingest_pdf,
    parse_pdf_date,
    parse_pdf_text,
)


def test_parse_pdf_date_slash_format():
    result = parse_pdf_date("30/09/2026")

    assert result == date(2026, 9, 30)


def test_parse_pdf_date_hyphen_format():
    result = parse_pdf_date("30-09-2026")

    assert result == date(2026, 9, 30)


def test_parse_pdf_date_two_digit_year():
    result = parse_pdf_date("30/09/26")

    assert result == date(2026, 9, 30)


def test_parse_pdf_date_invalid():
    with pytest.raises(ValueError):
        parse_pdf_date("2026-09-30")


def test_parse_pdf_text_debit_transaction():
    text = """
    Date Description Debit Credit Balance
    30/09/2026 UPI-ZOMATO-530151 160.29 0.00 41234.50
    """

    transactions = parse_pdf_text(
        text,
        source_file="statement.pdf",
    )

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction.date == date(2026, 9, 30)
    assert transaction.description == "UPI-ZOMATO-530151"
    assert transaction.debit == 160.29
    assert transaction.credit == 0.0
    assert transaction.balance == 41234.50
    assert transaction.transaction_type == "debit"
    assert transaction.source_file == "statement.pdf"


def test_parse_pdf_text_multiple_transactions():
    text = """
    Account Statement

    Date Description Debit Credit Balance
    28/09/2026 UPI-SWIGGY-123456 407.18 0.00 45000.00
    29/09/2026 NEFT-SALARY-SEPT 0.00 35000.00 80000.00
    30/09/2026 UPI-ZOMATO-530151 160.29 0.00 79839.71

    Closing Balance
    """

    transactions = parse_pdf_text(
        text,
        source_file="statement.pdf",
    )

    assert len(transactions) == 3

    assert transactions[0].description == "UPI-SWIGGY-123456"
    assert transactions[0].debit == 407.18
    assert transactions[0].transaction_type == "debit"

    assert transactions[1].description == "NEFT-SALARY-SEPT"
    assert transactions[1].credit == 35000.00
    assert transactions[1].transaction_type == "credit"

    assert transactions[2].description == "UPI-ZOMATO-530151"
    assert transactions[2].debit == 160.29


def test_parse_pdf_text_ignores_non_transaction_lines():
    text = """
    ABC BANK
    Account Number: XXXXXXXX1234
    Statement Period: 01/09/2026 - 30/09/2026

    Date Description Debit Credit Balance
    30/09/2026 UPI-ZOMATO-530151 160.29 0.00 41234.50

    Closing Balance
    """

    transactions = parse_pdf_text(
        text,
        source_file="statement.pdf",
    )

    assert len(transactions) == 1


def test_parse_pdf_text_no_transactions():
    text = """
    ABC BANK
    Account Statement
    No transactions found.
    """

    with pytest.raises(ValueError, match="No transaction rows"):
        parse_pdf_text(
            text,
            source_file="statement.pdf",
        )


def test_extract_pdf_text_requires_pdf(tmp_path):
    file_path = tmp_path / "statement.txt"

    file_path.write_text(
        "not a pdf",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Expected a PDF"):
        extract_pdf_text(str(file_path))


def test_ingest_pdf_preserves_blank_credit_column(tmp_path):
    """
    Regression test for PDFs where a debit amount is present and
    the credit cell is visually blank.
    """

    pdf_path = tmp_path / "statement.pdf"

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(pdf_path), pagesize=A4)

    c.drawString(30, 750, "DATE")
    c.drawString(150, 750, "DESCRIPTION")
    c.drawString(330, 750, "DEBIT")
    c.drawString(410, 750, "CREDIT")
    c.drawString(490, 750, "BALANCE")

    c.drawString(30, 735, "01/09/2026")
    c.drawString(150, 735, "UPI-ZOMATO-123")
    c.drawRightString(370, 735, "500.00")
    c.drawRightString(530, 735, "9500.00")

    c.save()

    transactions = ingest_pdf(str(pdf_path))

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction.debit == 500.00
    assert transaction.credit == 0.0
    assert transaction.balance == 9500.00
    assert transaction.transaction_type == "debit"


def test_ingest_pdf_preserves_blank_debit_column(tmp_path):
    """
    Regression test for PDFs where a credit amount is present and
    the debit cell is visually blank.
    """

    pdf_path = tmp_path / "statement.pdf"

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(pdf_path), pagesize=A4)

    c.drawString(30, 750, "DATE")
    c.drawString(150, 750, "DESCRIPTION")
    c.drawString(330, 750, "DEBIT")
    c.drawString(410, 750, "CREDIT")
    c.drawString(490, 750, "BALANCE")

    c.drawString(30, 735, "02/09/2026")
    c.drawString(150, 735, "NEFT-SALARY")
    c.drawRightString(450, 735, "35000.00")
    c.drawRightString(530, 735, "44500.00")

    c.save()

    transactions = ingest_pdf(str(pdf_path))

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction.debit == 0.0
    assert transaction.credit == 35000.00
    assert transaction.balance == 44500.00
    assert transaction.transaction_type == "credit"


def test_ingest_pdf_handles_multiple_pages(tmp_path):
    """
    A statement can span multiple PDF pages. Transactions from all
    pages should be returned in a single normalized list.
    """

    pdf_path = tmp_path / "multi_page_statement.pdf"

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(pdf_path), pagesize=A4)

    for page_number in range(2):
        c.drawString(30, 750, "DATE")
        c.drawString(150, 750, "DESCRIPTION")
        c.drawString(330, 750, "DEBIT")
        c.drawString(410, 750, "CREDIT")
        c.drawString(490, 750, "BALANCE")

        if page_number == 0:
            c.drawString(30, 735, "01/09/2026")
            c.drawString(150, 735, "UPI-SWIGGY-123")
            c.drawRightString(370, 735, "450.00")
            c.drawRightString(530, 735, "9500.00")
        else:
            c.drawString(30, 735, "02/09/2026")
            c.drawString(150, 735, "NEFT-SALARY")
            c.drawRightString(450, 735, "35000.00")
            c.drawRightString(530, 735, "44500.00")

        c.showPage()

    c.save()

    transactions = ingest_pdf(str(pdf_path))

    assert len(transactions) == 2

    assert transactions[0].description == "UPI-SWIGGY-123"
    assert transactions[0].debit == 450.00
    assert transactions[0].credit == 0.0

    assert transactions[1].description == "NEFT-SALARY"
    assert transactions[1].debit == 0.0
    assert transactions[1].credit == 35000.00


def test_ingest_pdf_handles_comma_formatted_amounts(tmp_path):
    """
    Indian bank statements commonly display amounts with commas,
    such as 35,000.00.
    """

    pdf_path = tmp_path / "comma_amounts.pdf"

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(pdf_path), pagesize=A4)

    c.drawString(30, 750, "DATE")
    c.drawString(150, 750, "DESCRIPTION")
    c.drawString(330, 750, "DEBIT")
    c.drawString(410, 750, "CREDIT")
    c.drawString(490, 750, "BALANCE")

    c.drawString(30, 735, "01/09/2026")
    c.drawString(150, 735, "MONTHLY RENT")
    c.drawRightString(370, 735, "9,000.00")
    c.drawRightString(530, 735, "1,25,500.00")

    c.save()

    transactions = ingest_pdf(str(pdf_path))

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction.debit == 9000.00
    assert transaction.credit == 0.0
    assert transaction.balance == 125500.00


def test_ingest_pdf_preserves_descriptions_with_spaces(tmp_path):
    """
    Transaction descriptions may contain multiple words rather than
    a compact merchant identifier.
    """

    pdf_path = tmp_path / "spaced_description.pdf"

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(pdf_path), pagesize=A4)

    c.drawString(30, 750, "DATE")
    c.drawString(150, 750, "DESCRIPTION")
    c.drawString(330, 750, "DEBIT")
    c.drawString(410, 750, "CREDIT")
    c.drawString(490, 750, "BALANCE")

    c.drawString(30, 735, "03/09/2026")
    c.drawString(150, 735, "ATM CASH WITHDRAWAL")
    c.drawRightString(370, 735, "5,000.00")
    c.drawRightString(530, 735, "120,000.00")

    c.save()

    transactions = ingest_pdf(str(pdf_path))

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction.description == "ATM CASH WITHDRAWAL"
    assert transaction.debit == 5000.00
    assert transaction.credit == 0.0


def test_ingest_pdf_handles_mixed_debit_and_credit_transactions(tmp_path):
    """
    A statement should preserve transaction direction when debit and
    credit rows occur together.
    """

    pdf_path = tmp_path / "mixed_transactions.pdf"

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(pdf_path), pagesize=A4)

    c.drawString(30, 750, "DATE")
    c.drawString(150, 750, "DESCRIPTION")
    c.drawString(330, 750, "DEBIT")
    c.drawString(410, 750, "CREDIT")
    c.drawString(490, 750, "BALANCE")

    c.drawString(30, 735, "01/09/2026")
    c.drawString(150, 735, "UPI-ZOMATO")
    c.drawRightString(370, 735, "800.00")
    c.drawRightString(530, 735, "19200.00")

    c.drawString(30, 720, "02/09/2026")
    c.drawString(150, 720, "SALARY CREDIT")
    c.drawRightString(450, 720, "35000.00")
    c.drawRightString(530, 720, "54200.00")

    c.drawString(30, 705, "03/09/2026")
    c.drawString(150, 705, "GROCERY STORE")
    c.drawRightString(370, 705, "2,500.00")
    c.drawRightString(530, 705, "51700.00")

    c.save()

    transactions = ingest_pdf(str(pdf_path))

    assert len(transactions) == 3

    assert transactions[0].transaction_type == "debit"
    assert transactions[0].debit == 800.00

    assert transactions[1].transaction_type == "credit"
    assert transactions[1].credit == 35000.00
    assert transactions[1].debit == 0.0

    assert transactions[2].transaction_type == "debit"
    assert transactions[2].debit == 2500.00


def test_detect_standard_pdf_layout():
    from data.pdf_ingestion import detect_pdf_layout

    words = [
        {"text": "DATE", "x0": 30, "x1": 62, "top": 82},
        {"text": "DESCRIPTION", "x0": 150, "x1": 232, "top": 82},
        {"text": "DEBIT", "x0": 330, "x1": 365, "top": 82},
        {"text": "CREDIT", "x0": 410, "x1": 455, "top": 82},
        {"text": "BALANCE", "x0": 490, "x1": 546, "top": 82},
    ]

    layout = detect_pdf_layout(words)

    assert layout == {
        "date": "date",
        "description": "description",
        "debit": "debit",
        "credit": "credit",
        "balance": "balance",
    }


def test_detect_alternate_pdf_layout():
    from data.pdf_ingestion import detect_pdf_layout

    words = [
        {"text": "TXN", "x0": 30, "x1": 55, "top": 82},
        {"text": "DATE", "x0": 56, "x1": 88, "top": 82},
        {"text": "NARRATION", "x0": 150, "x1": 220, "top": 82},
        {"text": "WITHDRAWAL", "x0": 330, "x1": 405, "top": 82},
        {"text": "DEPOSIT", "x0": 410, "x1": 460, "top": 82},
        {"text": "CLOSING", "x0": 490, "x1": 540, "top": 82},
        {"text": "BALANCE", "x0": 541, "x1": 590, "top": 82},
    ]

    layout = detect_pdf_layout(words)

    assert layout == {
        "date": "date",
        "description": "description",
        "debit": "debit",
        "credit": "credit",
        "balance": "balance",
    }


def test_detect_pdf_layout_returns_none_for_unknown_headers():
    from data.pdf_ingestion import detect_pdf_layout

    words = [
        {"text": "CUSTOMER", "x0": 30, "x1": 100, "top": 82},
        {"text": "REFERENCE", "x0": 150, "x1": 220, "top": 82},
        {"text": "VALUE", "x0": 330, "x1": 380, "top": 82},
    ]

    assert detect_pdf_layout(words) is None


def test_ingest_pdf_supports_alternate_column_names(tmp_path):
    """
    Bank statements may use different names for the same canonical
    transaction fields.
    """

    pdf_path = tmp_path / "alternate_layout.pdf"

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(pdf_path), pagesize=A4)

    c.drawString(30, 750, "TXN DATE")
    c.drawString(150, 750, "NARRATION")
    c.drawString(330, 750, "WITHDRAWAL")
    c.drawString(410, 750, "DEPOSIT")
    c.drawString(490, 750, "CLOSING BALANCE")

    c.drawString(30, 735, "01/09/2026")
    c.drawString(150, 735, "UPI-SWIGGY")
    c.drawRightString(370, 735, "450.00")
    c.drawRightString(530, 735, "9500.00")

    c.drawString(30, 720, "02/09/2026")
    c.drawString(150, 720, "SALARY CREDIT")
    c.drawRightString(450, 720, "35000.00")
    c.drawRightString(530, 720, "44500.00")

    c.save()

    transactions = ingest_pdf(str(pdf_path))

    assert len(transactions) == 2

    assert transactions[0].description == "UPI-SWIGGY"
    assert transactions[0].debit == 450.00
    assert transactions[0].credit == 0.0
    assert transactions[0].transaction_type == "debit"

    assert transactions[1].description == "SALARY CREDIT"
    assert transactions[1].debit == 0.0
    assert transactions[1].credit == 35000.00
    assert transactions[1].transaction_type == "credit"