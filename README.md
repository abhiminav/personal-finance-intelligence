# Personal Finance Intelligence

A personal finance analytics application that ingests Indian bank and UPI transaction statements, normalizes messy transaction descriptions, identifies merchants and P2P counterparties, categorizes spending, detects unusual spending patterns, and forecasts future spending.

The project combines a Python data-processing pipeline with a FastAPI backend and a React/Vite frontend.

---

## Features

### Statement ingestion

- CSV statement ingestion
- Support for multiple bank CSV layouts
- PDF statement ingestion
- Validation and normalization into a common transaction schema
- Sample CSV and PDF statements included for reproducible testing

### Transaction normalization

Bank statements often contain noisy transaction descriptions such as:

```text
UPI/824287/SWIGGY/ybl
POS 8243 MCDONALD'S
PHONEPE*DMART
OLA*ORDER917721
UPI/709931/RAJESH KUMAR/paytm
```

The application cleans these descriptions before classification.

### Merchant and counterparty identification

The classification pipeline distinguishes between:

- Merchants
- P2P counterparties
- Unresolved transactions

Merchant resolution uses a hybrid approach:

1. User overrides
2. Exact merchant matching
3. Fuzzy merchant matching
4. P2P/counterparty extraction
5. Machine-learning classification
6. Unresolved classification

Classification results include the method and confidence score.

### Spending categorization

Transactions are categorized into spending and income groups such as:

- Food & Dining
- Groceries
- Rent
- Utilities
- Subscriptions
- Transfers/P2P
- Shopping
- Transport
- Salary/Income
- Investments
- Other

### Anomaly detection

The application identifies transactions that differ significantly from historical spending patterns.

The anomaly system includes:

- Merchant-level spending baselines
- Category-level spending baselines
- Amount-spike detection
- Large one-off transactions
- Unusual purchases
- Monthly category spending anomalies
- Recurring-payment detection

The anomaly detector is intended to identify **statistical spending irregularities**. It is not a fraud-detection system.

### Spending forecast

The application generates a next-month spending forecast using historical monthly spending.

The current production baseline uses a cumulative historical average, with support for configurable historical windows.

### Interactive dashboard

The React frontend provides:

- Total spending
- Average monthly spending
- Largest spending category
- Detected anomaly count
- Key spending insights
- Monthly spending chart
- Category spending breakdown
- Next-month spending forecast
- Recent transactions
- Transaction Explorer
- Search and filtering
- Sorting
- Pagination
- Transaction detail panel
- Anomaly explanations


---

## Architecture

```text
Bank CSV / PDF
      │
      ▼
┌─────────────────────┐
│ Statement Ingestion │
│ CSV / PDF           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│ Cleaning & Classification   │
│                             │
│ Override → Exact → Fuzzy    │
│ → Counterparty → ML         │
│ → Unresolved                │
└──────────┬──────────────────┘
           │
           ├───────────────┐
           ▼               ▼
┌─────────────────┐ ┌──────────────────┐
│ Anomaly         │ │ Forecasting      │
│ Detection       │ │                  │
└────────┬────────┘ └────────┬─────────┘
         │                   │
         └─────────┬─────────┘
                   ▼
             ┌────────────┐
             │ FastAPI    │
             │ Backend    │
             └─────┬──────┘
                   │
                   ▼
             ┌────────────┐
             │ React/Vite │
             │ Frontend   │
             └────────────┘
```

---

## Tech Stack

### Backend & Data Processing

- Python
- pandas
- NumPy
- scikit-learn
- RapidFuzz
- pdfplumber
- ReportLab
- FastAPI
- Uvicorn

### Frontend

- React
- Vite
- Recharts

### Testing

- pytest


---

## Project Structure

```text
personal-finance-intelligence/
│
├── app.py
├── pipeline.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   ├── __init__.py
│   ├── ingestion.py
│   ├── pdf_ingestion.py
│   ├── schemas.py
│   ├── synthetic_generator.py
│   └── sample/
│       ├── bank_a_user_001.csv
│       ├── bank_b_user_001.csv
│       └── test_bank_statement.pdf
│
├── categorization/
│   ├── __init__.py
│   ├── cleaning.py
│   ├── counterparty.py
│   ├── merchant_clustering.py
│   ├── merchant_dictionary.py
│   ├── ml_classifier.py
│   ├── overrides.py
│   └── rule_based.py
│
├── anomaly/
│   ├── __init__.py
│   ├── baseline.py
│   ├── category_spending.py
│   ├── flagging.py
│   └── recurring.py
│
├── forecasting/
│   ├── __init__.py
│   └── forecast.py
│
├── evaluation/
│   ├── __init__.py
│   ├── diagnose_category_anomalies.py
│   ├── evaluate_anomalies.py
│   ├── evaluate_classifier.py
│   ├── evaluate_clustering.py
│   ├── evaluate_forecast.py
│   ├── evaluate_hybrid.py
│   ├── evaluate_ml.py
│   ├── evaluate_ml_confidence.py
│   ├── evaluate_ml_generalization.py
│   ├── evaluate_pipeline.py
│   ├── evaluate_rule_based.py
│   ├── generalization_dataset.py
│   ├── inspect_false_positives.py
│   ├── ml_dataset.py
│   └── test_category_thresholds.py
│
├── tests/
│   ├── __init__.py
│   ├── test_anomalies.py
│   ├── test_categorization.py
│   ├── test_category_spending.py
│   ├── test_cleaning.py
│   ├── test_forecast.py
│   ├── test_ingestion.py
│   ├── test_pdf_ingestion.py
│   ├── test_pipeline.py
│   └── test_recurring.py
│
├── backend/
│   ├── __init__.py
│   └── main.py
│
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── public/
│   └── src/
│
└── models/
    └── .gitkeep
```


---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/abhiminav/personal-finance-intelligence.git
cd personal-finance-intelligence
```

### 2. Create the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Running the Application

The application consists of a FastAPI backend and a React frontend.

### Start the backend

From the project root:

```bash
source .venv/bin/activate
python -m uvicorn backend.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### Start the frontend

In another terminal:

```bash
cd frontend
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```


---

## Supported Statement Formats

The ingestion layer currently supports two CSV layouts.

### Bank A

```text
Date
Description
Debit
Credit
Balance
```

### Bank B

```text
Txn Date
Value Date
Narration
Withdrawal Amt
Deposit Amt
Closing Balance
```

PDF ingestion supports common bank-statement layouts using both text parsing and position-aware column detection.

---

## Example Transaction Classification

The application can normalize transaction descriptions such as:

| Raw description | Identified entity | Category | Method |
|---|---|---|---|
| `PHONEPE*DMART` | DMart | Groceries | Exact |
| `POS 9104 BLINKIT` | Blinkit | Groceries | Exact |
| `OLA*ORDER917721` | Ola | Transport | Exact |
| `UPI/423819271/LANDLORD/RENT` | Rent | Rent | Exact |
| `UPI/709931/RAJESH KUMAR/paytm` | Rajesh Kumar | Transfers/P2P | Counterparty |
| `UPI/550316/NETFLIX` | Netflix | Subscriptions | Exact |
| `POS 8243 MCDONALD'S` | McDonald's | Food & Dining | Fuzzy |
| `UPI/824287/SWIGGY/ybl` | Swiggy | Food & Dining | Exact |
| `IMPS/P2A/651206/Amit Verma` | Amit Verma | Transfers/P2P | Counterparty |
| `GROWW SIP` | Investment | Investments | Exact |
| `BBPS/ELECTRICITY/BESCOM` | Electricity | Utilities | Fuzzy |
| `NEFT-HDFC0001234-SALARY-OCT` | Salary | Salary/Income | Exact |  


---

## Synthetic Data

The project includes a synthetic transaction generator for development and evaluation.

The generated dataset models:

- Multiple users
- Monthly salary
- Rent
- Investments
- Food and dining
- Groceries
- Shopping
- Transport
- Utilities
- Subscriptions
- P2P transfers
- Realistic merchant-description noise
- Recurring transactions
- Injected spending anomalies

The benchmark dataset used during development contains:

```text
Users: 5
Transactions: 2,393
History: 12 months
Random seed: 42
```

Synthetic data is used for development and evaluation because real personal bank statements are not included in the repository.

---

## Evaluation

The project includes dedicated evaluation scripts for:

- Classification
- Hybrid classification
- ML generalization
- Merchant clustering
- Anomaly detection
- Category-level anomalies
- Forecasting
- End-to-end pipeline behavior
- False-positive inspection

The final automated test suite currently contains:

```text
140 passed
```

Run the complete test suite with:

```bash
pytest -q
```


---

## Forecasting

The current production forecasting baseline estimates future spending using the historical monthly average.

For a category or user, positive spending transactions are aggregated by month and averaged across the available historical period.

The implementation also supports restricting the calculation to a recent historical window.

This is intentionally a simple and interpretable baseline rather than a complex time-series model.

---

## Anomaly Detection

The anomaly system uses historical spending baselines rather than a supervised fraud model.

Merchant-level baselines consider statistics including:

- Transaction count
- Mean amount
- Median amount
- Standard deviation
- 95th percentile

Category-level monthly anomaly detection uses robust statistics including:

- Historical monthly median
- Median absolute deviation (MAD)
- Robust z-score
- Minimum historical observations
- Minimum spending increase ratio

The system is designed to surface transactions or spending patterns that deserve inspection.

It should **not** be interpreted as a financial-fraud or banking-security system.