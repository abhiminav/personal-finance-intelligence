from dataclasses import dataclass

import pandas as pd

from data.schemas import Transaction


@dataclass(frozen=True)
class DuplicateResult:
    """
    Result of duplicate detection for a transaction.

    A strong duplicate means we have enough evidence to consider
    two transactions the same underlying bank transaction.

    A possible duplicate is deliberately weaker and should not be
    automatically removed.
    """

    is_duplicate: bool
    is_possible_duplicate: bool
    reason: str | None


def normalize_reference_number(
    reference_number: str | None,
) -> str | None:
    """
    Normalize a bank-provided transaction reference number.

    Bank statements may represent missing reference numbers as
    strings such as "nan", "none", or "null". These are treated
    as missing rather than as real reference numbers.
    """

    if reference_number is None:
        return None

    normalized = str(
        reference_number
    ).strip().upper()

    if not normalized:
        return None

    if normalized in {
        "NAN",
        "NONE",
        "NULL",
    }:
        return None

    return normalized


def transactions_look_identical(
    first: Transaction,
    second: Transaction,
) -> bool:
    """
    Check whether two transactions have the same visible
    transaction details.

    This is only a possible-duplicate signal because two legitimate
    transactions can share the same date, description, and amount.
    """

    return (
        first.date == second.date
        and first.description.strip().casefold()
        == second.description.strip().casefold()
        and first.debit == second.debit
        and first.credit == second.credit
    )


def detect_duplicate(
    transaction: Transaction,
    previous_transactions: list[Transaction],
) -> DuplicateResult:
    """
    Determine whether a transaction appears to be duplicated.

    Rules:

    1. Matching non-empty bank reference numbers are treated as a
       strong duplicate signal.

    2. Transactions without matching reference numbers are never
       automatically marked as duplicates.

    3. Identical visible transaction details are marked only as
       possible duplicates.
    """

    current_reference = normalize_reference_number(
        transaction.reference_number
    )

    if current_reference is not None:
        for previous in previous_transactions:
            previous_reference = normalize_reference_number(
                previous.reference_number
            )

            if (
                previous_reference is not None
                and previous_reference == current_reference
            ):
                return DuplicateResult(
                    is_duplicate=True,
                    is_possible_duplicate=False,
                    reason=(
                        "Matching bank transaction reference number."
                    ),
                )

    for previous in previous_transactions:
        if transactions_look_identical(
            transaction,
            previous,
        ):
            return DuplicateResult(
                is_duplicate=False,
                is_possible_duplicate=True,
                reason=(
                    "Transaction has identical date, description, "
                    "debit, and credit values."
                ),
            )

    return DuplicateResult(
        is_duplicate=False,
        is_possible_duplicate=False,
        reason=None,
    )


def detect_duplicates(
    transactions: list[Transaction],
) -> list[DuplicateResult]:
    """
    Run duplicate detection across a transaction list.

    Transactions are evaluated in their existing order. The first
    occurrence is retained as the original; later matching
    transactions receive duplicate signals.
    """

    results: list[DuplicateResult] = []
    previous_transactions: list[Transaction] = []

    for transaction in transactions:
        result = detect_duplicate(
            transaction,
            previous_transactions,
        )

        results.append(result)
        previous_transactions.append(transaction)

    return results


def flag_dataframe_duplicates(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add duplicate-detection metadata to a transaction DataFrame.

    No transactions are removed.

    Expected columns:

        date
        description
        debit
        credit

    Optional column:

        reference_number

    Added columns:

        is_duplicate
        is_possible_duplicate
        duplicate_reason
    """

    required_columns = {
        "date",
        "description",
        "debit",
        "credit",
    }

    missing = required_columns - set(
        transactions.columns
    )

    if missing:
        raise ValueError(
            f"Missing required columns for duplicate detection: "
            f"{sorted(missing)}"
        )

    data = transactions.copy()

    data["is_duplicate"] = False
    data["is_possible_duplicate"] = False
    data["duplicate_reason"] = None

    seen_references: dict[str, int] = {}
    seen_visible_transactions: dict[
        tuple,
        int,
    ] = {}

    has_reference_column = (
        "reference_number" in data.columns
    )

    for index, row in data.iterrows():
        reference = None

        if has_reference_column:
            reference = normalize_reference_number(
                row["reference_number"]
            )

        if reference is not None:
            if reference in seen_references:
                data.at[
                    index,
                    "is_duplicate",
                ] = True

                data.at[
                    index,
                    "duplicate_reason",
                ] = (
                    "Matching bank transaction reference number."
                )
            else:
                seen_references[reference] = index

        visible_key = (
            pd.Timestamp(row["date"]).date(),
            str(row["description"]).strip().casefold(),
            float(row["debit"]),
            float(row["credit"]),
        )

        if visible_key in seen_visible_transactions:
            if not data.at[
                index,
                "is_duplicate"
            ]:
                data.at[
                    index,
                    "is_possible_duplicate",
                ] = True

                data.at[
                    index,
                    "duplicate_reason",
                ] = (
                    "Transaction has identical date, description, "
                    "debit, and credit values."
                )
        else:
            seen_visible_transactions[
                visible_key
            ] = index

    return data