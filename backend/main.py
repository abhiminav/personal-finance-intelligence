from pathlib import Path
from tempfile import NamedTemporaryFile
import os
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from anomaly.baseline import (
    build_category_baselines,
    build_merchant_baselines,
)
from anomaly.flagging import flag_transactions
from categorization.rule_based import classify_transaction
from data.ingestion import ingest_csv
from forecasting.forecast import forecast_user_spending
from data.pdf_ingestion import ingest_pdf


MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


app = FastAPI(
    title="Personal Finance Intelligence API",
    description=(
        "Backend API for the Personal Finance Intelligence application."
    ),
    version="0.1.0",
)


CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "personal-finance-intelligence",
    }


def process_csv(file_path: str):
    transactions = ingest_csv(file_path)

    classified_transactions = []

    for transaction in transactions:
        classification = classify_transaction(
            transaction.description
        )

        classified_transactions.append(
            {
                "date": transaction.date.isoformat(),
                "description": transaction.description,
                "debit": transaction.debit,
                "credit": transaction.credit,
                "balance": transaction.balance,
                "transaction_type": transaction.transaction_type,
                "merchant_id": classification.merchant_id,
                "merchant_name": classification.merchant_name,
                "counterparty_id": classification.counterparty_id,
                "counterparty_name": classification.counterparty_name,
                "category": classification.category,
                "classification_method": classification.method,
                "classification_confidence": classification.confidence,
            }
        )

    return classified_transactions


def process_pdf(file_path: str):
    transactions = ingest_pdf(file_path)

    classified_transactions = []

    for transaction in transactions:
        classification = classify_transaction(
            transaction.description
        )

        classified_transactions.append(
            {
                "date": transaction.date.isoformat(),
                "description": transaction.description,
                "debit": transaction.debit,
                "credit": transaction.credit,
                "balance": transaction.balance,
                "transaction_type": transaction.transaction_type,
                "merchant_id": classification.merchant_id,
                "merchant_name": classification.merchant_name,
                "counterparty_id": classification.counterparty_id,
                "counterparty_name": classification.counterparty_name,
                "category": classification.category,
                "classification_method": classification.method,
                "classification_confidence": classification.confidence,
            }
        )

    return classified_transactions


def process_uploaded_file(file_path: str, file_extension: str):
    if file_extension == ".csv":
        return process_csv(file_path)

    if file_extension == ".pdf":
        return process_pdf(file_path)

    raise ValueError("Unsupported file type. Use CSV or PDF.")


def build_spending_dataframe(
    transactions: list[dict],
) -> pd.DataFrame:
    rows = []

    for index, transaction in enumerate(transactions):
        debit = float(transaction["debit"])

        if debit <= 0:
            continue

        if transaction["category"] is None:
            continue

        rows.append(
            {
                "transaction_id": f"uploaded_{index}",
                "user_id": "uploaded_user",
                "date": transaction["date"],
                "amount": debit,
                "category": transaction["category"],
                "merchant_id": transaction["merchant_id"],
                "merchant_name": transaction["merchant_name"],
                "counterparty_id": transaction["counterparty_id"],
                "counterparty_name": transaction["counterparty_name"],
                "description": transaction["description"],
                "classification_method": transaction[
                    "classification_method"
                ],
                "classification_confidence": transaction[
                    "classification_confidence"
                ],
            }
        )

    return pd.DataFrame(rows)


def build_monthly_spending(spending_df: pd.DataFrame):
    data = spending_df.copy()

    data["date"] = pd.to_datetime(data["date"])
    data["month"] = data["date"].dt.to_period("M")

    monthly = (
        data.groupby("month", as_index=False)["amount"]
        .sum()
        .sort_values("month")
    )

    monthly["month"] = monthly["month"].astype(str)

    return [
        {
            "month": row["month"],
            "amount": float(row["amount"]),
        }
        for _, row in monthly.iterrows()
    ]


def build_category_spending(spending_df: pd.DataFrame):
    category = (
        spending_df.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )

    return [
        {
            "category": row["category"],
            "amount": float(row["amount"]),
        }
        for _, row in category.iterrows()
    ]


def build_recent_transactions(
    spending_df: pd.DataFrame,
    limit: int = 10,
):
    data = spending_df.copy()

    data["date"] = pd.to_datetime(data["date"])

    recent = (
        data.sort_values("date", ascending=False)
        .head(limit)
    )

    transactions = []

    for _, row in recent.iterrows():
        merchant_name = row["merchant_name"]

        if pd.isna(merchant_name):
            merchant_name = None
        else:
            merchant_name = str(merchant_name)

        counterparty_name = row["counterparty_name"]

        if pd.isna(counterparty_name):
            counterparty_name = None
        else:
            counterparty_name = str(counterparty_name)

        category = row["category"]

        if pd.isna(category):
            category = None
        else:
            category = str(category)

        description = row["description"]

        if pd.isna(description):
            description = None
        else:
            description = str(description)

        transactions.append(
            {
                "transaction_id": str(row["transaction_id"]),
                "date": row["date"].date().isoformat(),
                "description": description,
                "amount": float(row["amount"]),
                "category": category,
                "merchant_name": merchant_name,
                "counterparty_name": counterparty_name,
            }
        )

    return transactions


def build_transaction_records(
    analyzed_transactions: pd.DataFrame,
):
    data = analyzed_transactions.copy()

    records = []

    for _, row in data.iterrows():
        merchant_name = row.get("merchant_name")

        if pd.isna(merchant_name):
            merchant_name = None
        else:
            merchant_name = str(merchant_name)

        counterparty_name = row.get("counterparty_name")

        if pd.isna(counterparty_name):
            counterparty_name = None
        else:
            counterparty_name = str(counterparty_name)

        category = row.get("category")

        if pd.isna(category):
            category = None
        else:
            category = str(category)

        description = row.get("description")

        if pd.isna(description):
            description = None
        else:
            description = str(description)

        anomaly = row.get("anomaly", False)

        if pd.isna(anomaly):
            anomaly = False
        else:
            anomaly = bool(anomaly)

        anomaly_type = row.get("anomaly_type")

        if pd.isna(anomaly_type):
            anomaly_type = None
        else:
            anomaly_type = str(anomaly_type)

        anomaly_score = row.get("anomaly_score")

        if pd.isna(anomaly_score):
            anomaly_score = None
        else:
            anomaly_score = float(anomaly_score)

        anomaly_reason = row.get("anomaly_reason")

        if pd.isna(anomaly_reason):
            anomaly_reason = None
        else:
            anomaly_reason = str(anomaly_reason)

        classification_method = row.get(
            "classification_method"
        )

        if pd.isna(classification_method):
            classification_method = None
        else:
            classification_method = str(classification_method)

        classification_confidence = row.get(
            "classification_confidence"
        )

        if pd.isna(classification_confidence):
            classification_confidence = None
        else:
            classification_confidence = float(
                classification_confidence
            )

        records.append(
            {
                "transaction_id": str(row["transaction_id"]),
                "date": pd.to_datetime(
                    row["date"]
                ).date().isoformat(),
                "description": description,
                "amount": float(row["amount"]),
                "category": category,
                "merchant_name": merchant_name,
                "counterparty_name": counterparty_name,
                "classification_method": classification_method,
                "classification_confidence": classification_confidence,
                "anomaly": anomaly,
                "anomaly_type": anomaly_type,
                "anomaly_score": anomaly_score,
                "anomaly_reason": anomaly_reason,
            }
        )

    return records


def build_insights(
    spending_df: pd.DataFrame,
    monthly_spending: list[dict],
    category_spending: list[dict],
    anomalies: list[dict],
):
    total_spending = float(
        spending_df["amount"].sum()
    )

    highest_month = max(
        monthly_spending,
        key=lambda item: item["amount"],
    )

    highest_category = max(
        category_spending,
        key=lambda item: item["amount"],
    )

    category_share = (
        highest_category["amount"]
        / total_spending
        * 100
        if total_spending > 0
        else 0
    )

    anomaly_total = len(anomalies)

    largest_anomaly = None

    if anomalies:
        largest_anomaly = max(
            anomalies,
            key=lambda item: item["amount"],
        )

    return {
        "highest_spending_month": {
            "month": highest_month["month"],
            "amount": highest_month["amount"],
        },
        "highest_spending_category": {
            "category": highest_category["category"],
            "amount": highest_category["amount"],
            "percentage": category_share,
        },
        "anomaly_summary": {
            "count": anomaly_total,
            "largest_amount": (
                largest_anomaly["amount"]
                if largest_anomaly
                else None
            ),
            "largest_merchant": (
                largest_anomaly["merchant_name"]
                if largest_anomaly
                else None
            ),
        },
        "average_monthly_spending": (
            total_spending / len(monthly_spending)
            if monthly_spending
            else 0
        ),
    }


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in {".csv", ".pdf"}:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and PDF files are supported.",
        )

    temp_path = None

    try:
        contents = await file.read(
            MAX_UPLOAD_SIZE + 1
        )

        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=(
                    "File is too large. "
                    "Maximum allowed size is 10 MB."
                ),
            )

        with NamedTemporaryFile(
            delete=False,
            suffix=file_extension,
        ) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name

        transactions = process_uploaded_file(
            temp_path,
            file_extension,
        )

        return {
            "filename": file.filename,
            "transaction_count": len(transactions),
            "transactions": transactions,
        }

    except HTTPException:
        raise

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded file contains invalid or "
                "unsupported transaction data."
            ),
        ) from None

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to process file.",
        ) from None

    finally:
        if temp_path:
            Path(temp_path).unlink(
                missing_ok=True
            )


@app.post("/api/analyze")
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in {".csv", ".pdf"}:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and PDF files are supported.",
        )

    temp_path = None

    try:
        contents = await file.read(
            MAX_UPLOAD_SIZE + 1
        )

        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=(
                    "File is too large. "
                    "Maximum allowed size is 10 MB."
                ),
            )

        with NamedTemporaryFile(
            delete=False,
            suffix=file_extension,
        ) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name

        classified_transactions = process_uploaded_file(
            temp_path,
            file_extension,
        )

        spending_df = build_spending_dataframe(
            classified_transactions
        )

        if spending_df.empty:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No spending transactions "
                    "could be analyzed."
                ),
            )

        category_baselines = build_category_baselines(
            spending_df
        )

        merchant_baselines = build_merchant_baselines(
            spending_df
        )

        analyzed_transactions = flag_transactions(
            transactions=spending_df,
            baselines=category_baselines,
            merchant_baselines=merchant_baselines,
        )

        forecast = forecast_user_spending(
            spending_df,
            user_id="uploaded_user",
        )

        anomaly_rows = analyzed_transactions[
            analyzed_transactions["anomaly"] == True
        ]

        anomalies = anomaly_rows.to_dict(
            orient="records"
        )

        for anomaly in anomalies:
            if hasattr(
                anomaly.get("date"),
                "isoformat",
            ):
                anomaly["date"] = anomaly[
                    "date"
                ].isoformat()

            for key, value in list(
                anomaly.items()
            ):
                if pd.isna(value):
                    anomaly[key] = None

        monthly_spending = build_monthly_spending(
            spending_df
        )

        category_spending = build_category_spending(
            spending_df
        )

        recent_transactions = (
            build_recent_transactions(
                spending_df
            )
        )

        transaction_records = (
            build_transaction_records(
                analyzed_transactions
            )
        )

        insights = build_insights(
            spending_df=spending_df,
            monthly_spending=monthly_spending,
            category_spending=category_spending,
            anomalies=anomalies,
        )

        return {
            "filename": file.filename,
            "total_transactions": len(
                classified_transactions
            ),
            "spending_transactions": len(
                spending_df
            ),
            "analyzed_transactions": len(
                analyzed_transactions
            ),
            "anomaly_count": len(anomalies),
            "forecast": {
                "historical_months": (
                    forecast.historical_months
                ),
                "average_monthly_spend": (
                    forecast.average_monthly_spend
                ),
                "forecast_amount": (
                    forecast.forecast_amount
                ),
            },
            "monthly_spending": monthly_spending,
            "category_spending": category_spending,
            "recent_transactions": (
                recent_transactions
            ),
            "transactions": transaction_records,
            "insights": insights,
            "anomalies": anomalies,
        }

    except HTTPException:
        raise

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded file contains invalid or "
                "unsupported transaction data."
            ),
        ) from None

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze file.",
        ) from None

    finally:
        if temp_path:
            Path(temp_path).unlink(
                missing_ok=True
            )


def test_concurrent_uploads_are_isolated():
    csv_a = (
        b"Date,Description,Debit,Credit,Balance\n"
        b"2026-09-01,SWIGGY ORDER,500,,9500\n"
    )

    csv_b = (
        b"Date,Description,Debit,Credit,Balance\n"
        b"2026-09-01,AMAZON ORDER,1200,,8800\n"
    )

    def upload(filename, content):
        return client.post(
            "/api/upload",
            files={
                "file": (
                    filename,
                    content,
                    "text/csv",
                )
            },
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(
            upload,
            "user_a.csv",
            csv_a,
        )
        future_b = executor.submit(
            upload,
            "user_b.csv",
            csv_b,
        )

        response_a = future_a.result()
        response_b = future_b.result()

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    data_a = response_a.json()
    data_b = response_b.json()

    assert data_a["filename"] == "user_a.csv"
    assert data_b["filename"] == "user_b.csv"

    assert data_a["transaction_count"] == 1
    assert data_b["transaction_count"] == 1

    assert data_a["transactions"][0]["description"] == "SWIGGY ORDER"
    assert data_b["transactions"][0]["description"] == "AMAZON ORDER"