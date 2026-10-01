import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const transactionsPerPage = 15;

function formatCurrency(value) {
  return `₹${Math.round(value).toLocaleString("en-IN")}`;
}

function formatCurrencyExact(value) {
  return `₹${Number(value).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatMonth(value) {
  const date = new Date(`${value}-01`);
  return date.toLocaleDateString("en-IN", {
    month: "short",
    year: "numeric",
  });
}

function MonthlyTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  return (
    <div className="chart-tooltip">
      <div className="tooltip-label">{formatMonth(label)}</div>
      <div className="tooltip-value">
        {formatCurrencyExact(payload[0].value)}
      </div>
    </div>
  );
}

function CategoryTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const item = payload[0];
  const percentage = item.payload.percentage ?? 0;

  return (
    <div className="chart-tooltip">
      <div className="tooltip-label">{item.name}</div>
      <div className="tooltip-value">
        {formatCurrencyExact(item.value)}
      </div>
      <div className="tooltip-percentage">
        {percentage.toFixed(1)}% of spending
      </div>
    </div>
  );
}

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [transactionSearch, setTransactionSearch] = useState("");
  const [transactionCategory, setTransactionCategory] = useState("all");
  const [transactionStatus, setTransactionStatus] = useState("all");
  const [transactionSort, setTransactionSort] = useState("date_desc");
  const [transactionPage, setTransactionPage] = useState(1);
  const [selectedTransaction, setSelectedTransaction] = useState(null);


  async function analyzeFile() {
    if (!file) {
      setError("Please select a CSV or PDF file first.");
      return;
    }

    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(body || "Analysis failed.");
      }

      const data = await response.json();
      setResult(data);
      setTransactionPage(1);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  const transactions = result?.transactions ?? [];

  const transactionCategories = useMemo(() => {
    return [...new Set(
      transactions
        .map((transaction) => transaction.category)
        .filter(Boolean)
    )].sort();
  }, [transactions]);

  const filteredTransactions = useMemo(() => {
    const search = transactionSearch.trim().toLowerCase();

    const filtered = transactions.filter((transaction) => {
      const merchant = transaction.merchant_name || "";
      const counterparty = transaction.counterparty_name || "";
      const description = transaction.description || "";
      const category = transaction.category || "";

      const matchesSearch =
        !search ||
        merchant.toLowerCase().includes(search) ||
        counterparty.toLowerCase().includes(search) ||
        description.toLowerCase().includes(search) ||
        category.toLowerCase().includes(search);

      const matchesCategory =
        transactionCategory === "all" ||
        category === transactionCategory;

      const matchesStatus =
        transactionStatus === "all" ||
        (transactionStatus === "anomalies" && transaction.anomaly);

      return matchesSearch && matchesCategory && matchesStatus;
    });

    return [...filtered].sort((a, b) => {
      if (transactionSort === "date_desc") {
        return new Date(b.date) - new Date(a.date);
      }

      if (transactionSort === "date_asc") {
        return new Date(a.date) - new Date(b.date);
      }

      if (transactionSort === "amount_desc") {
        return Number(b.amount) - Number(a.amount);
      }

      if (transactionSort === "amount_asc") {
        return Number(a.amount) - Number(b.amount);
      }

      return 0;
    });
  }, [
    transactions,
    transactionSearch,
    transactionCategory,
    transactionStatus,
    transactionSort,
  ]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredTransactions.length / transactionsPerPage)
  );

  useEffect(() => {
    if (transactionPage > totalPages) {
      setTransactionPage(totalPages);
    }
  }, [transactionPage, totalPages]);

  const paginatedTransactions = useMemo(() => {
    const start =
      (transactionPage - 1) * transactionsPerPage;

    return filteredTransactions.slice(
      start,
      start + transactionsPerPage
    );
  }, [filteredTransactions, transactionPage]);

  const transactionStart =
    filteredTransactions.length === 0
      ? 0
      : (transactionPage - 1) * transactionsPerPage + 1;

  const transactionEnd = Math.min(
    transactionPage * transactionsPerPage,
    filteredTransactions.length
  );

  function resetExplorerPage() {
    setTransactionPage(1);
  }

  const highestSpendingMonth = useMemo(() => {
    if (!result?.monthly_spending?.length) {
      return null;
    }

    return [...result.monthly_spending].sort(
      (a, b) => b.amount - a.amount
    )[0];
  }, [result]);

  const largestCategory = useMemo(() => {
    if (!result?.category_spending?.length) {
      return null;
    }

    return [...result.category_spending].sort(
      (a, b) => b.amount - a.amount
    )[0];
  }, [result]);

  const categoryChartData = useMemo(() => {
    if (!result?.category_spending?.length) {
      return [];
    }

    const total = result.category_spending.reduce(
      (sum, item) => sum + Number(item.amount || 0),
      0
    );

    return result.category_spending.map((item) => ({
      ...item,
      percentage:
        total > 0 ? (Number(item.amount) / total) * 100 : 0,
    }));
  }, [result]);

  const totalSpending = result?.category_spending?.reduce(
    (sum, item) => sum + Number(item.amount || 0),
    0
  ) ?? 0;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand">Expense Intelligence</div>
          <div className="brand-subtitle">
            Personal finance analytics
          </div>
        </div>

        <div className="upload-area">
          <label className="file-input">
            <input
              type="file"
              accept=".csv, .pdf"
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setError("");
              }}
            />
            <span>{file ? file.name : "Choose CSV or PDF"}</span>
          </label>

          <button
            className="analyze-button"
            onClick={analyzeFile}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {!result && !loading && (
        <main className="empty-state">
          <div className="empty-card">
            <h1>Understand where your money goes.</h1>
            <p>
              Upload an Indian bank or UPI CSV statement to analyze
              spending, merchants, anomalies and future expenses.
            </p>
          </div>
        </main>
      )}

      {loading && (
        <main className="loading-state">
          <div className="loading-card">
            <div className="loading-spinner" />
            <h2>Analyzing your statement</h2>
            <p>
              Cleaning transactions, identifying merchants and
              calculating spending patterns...
            </p>
          </div>
        </main>
      )}

      {result && !loading && (
        <main className="dashboard">
          <section className="dashboard-heading">
            <div>
              <h1>Financial Overview</h1>
              <p>{result.filename}</p>
            </div>
          </section>

          <section className="metrics-grid">
            <div className="metric-card">
              <span className="metric-label">
                Total Spending
              </span>
              <strong className="metric-value">
                {formatCurrency(totalSpending)}
              </strong>
            </div>

            <div className="metric-card">
              <span className="metric-label">
                Average Monthly Spending
              </span>
              <strong className="metric-value">
                {formatCurrency(
                  result.insights?.average_monthly_spending ?? 0
                )}
              </strong>
            </div>

            <div className="metric-card">
              <span className="metric-label">
                Largest Category
              </span>
              <strong className="metric-value metric-value-category">
                {largestCategory?.category || "—"}
              </strong>
            </div>

            <div className="metric-card">
              <span className="metric-label">
                Anomalies Detected
              </span>
              <strong className="metric-value">
                {result.anomaly_count}
              </strong>
            </div>
          </section>

          <section className="insights-section">
            <div className="section-heading">
              <div>
                <h2>Key Insights</h2>
                <p>A quick summary of your spending patterns.</p>
              </div>
            </div>

            <div className="insights-grid">
              <div className="insight-card">
                <span className="insight-label">
                  Highest spending month
                </span>

                <strong className="insight-value">
                  {highestSpendingMonth
                    ? formatMonth(highestSpendingMonth.month)
                    : "—"}
                </strong>

                <span className="insight-detail">
                  {highestSpendingMonth
                    ? `${formatCurrencyExact(highestSpendingMonth.amount)} spent`
                    : "No spending data available"}
                </span>
              </div>

              <div className="insight-card">
                <span className="insight-label">
                  Largest category
                </span>

                <strong className="insight-value">
                  {largestCategory?.category || "—"}
                </strong>

                <span className="insight-detail">
                  {largestCategory
                    ? `${formatCurrencyExact(largestCategory.amount)} spent`
                    : "No category data available"}
                </span>
              </div>

              <div className="insight-card">
                <span className="insight-label">
                  Average monthly spending
                </span>

                <strong className="insight-value">
                  {formatCurrency(
                    result.insights?.average_monthly_spending ?? 0
                  )}
                </strong>

                <span className="insight-detail">
                  Across available statement history
                </span>
              </div>

              <div className="insight-card anomaly-insight">
                <span className="insight-label">
                  Largest detected anomaly
                </span>

                <strong className="insight-value">
                  {result.insights?.anomaly_summary?.largest_amount != null
                    ? formatCurrency(
                        result.insights.anomaly_summary.largest_amount
                      )
                    : "None"}
                </strong>

                <span className="insight-detail">
                  {result.insights?.anomaly_summary?.largest_merchant ||
                    "No unusual spending detected"}
                </span>
              </div>
            </div>
          </section>

          <section className="charts-grid">
            <div className="chart-card">
              <div className="card-heading">
                <div>
                  <h2>Monthly Spending</h2>
                  <p>Spending over time</p>
                </div>
              </div>

              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={result.monthly_spending}
                    margin={{
                      top: 10,
                      right: 10,
                      left: 0,
                      bottom: 5,
                    }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                    />

                    <XAxis
                      dataKey="month"
                      tickFormatter={formatMonth}
                      tickLine={false}
                      axisLine={false}
                    />

                    <YAxis
                      tickFormatter={(value) =>
                        `₹${Math.round(value / 1000)}k`
                      }
                      tickLine={false}
                      axisLine={false}
                      width={48}
                    />

                    <Tooltip content={<MonthlyTooltip />} />

                    <Bar
                      dataKey="amount"
                      radius={[5, 5, 0, 0]}
                      maxBarSize={42}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="chart-card">
              <div className="card-heading">
                <div>
                  <h2>Spending by Category</h2>
                  <p>Where your money is going</p>
                </div>
              </div>

              <div className="category-chart-layout">
                <div className="category-pie">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categoryChartData}
                        dataKey="amount"
                        nameKey="category"
                        innerRadius={65}
                        outerRadius={105}
                        paddingAngle={2}
                      >
                        {categoryChartData.map((entry, index) => (
                          <Cell key={entry.category || index} />
                        ))}
                      </Pie>
                      <Tooltip content={<CategoryTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="category-list">
                  {categoryChartData.map((item) => (
                    <div
                      className="category-row"
                      key={item.category}
                    >
                      <div className="category-name">
                        <span>{item.category}</span>
                        <small>
                          {item.percentage.toFixed(1)}%
                        </small>
                      </div>

                      <strong>
                        {formatCurrency(item.amount)}
                      </strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="forecast-card">
            <div>
              <span className="forecast-label">
                Next Month Spending Forecast
              </span>
              <h2>
                {formatCurrencyExact(
                  result.forecast.forecast_amount
                )}
              </h2>
              <p>
                Based on {result.forecast.historical_months} months
                of spending history.
              </p>
            </div>

            <div className="forecast-meta">
              <span>Historical average</span>
              <strong>
                {formatCurrencyExact(
                  result.forecast.average_monthly_spend
                )}
              </strong>
            </div>
          </section>

          <section className="transactions-section">
            <div className="section-heading">
              <div>
                <h2>Recent Transactions</h2>
                <p>Latest spending activity</p>
              </div>
            </div>

            <div className="transactions-card">
              <div className="transactions-table-wrapper">
                <table className="transactions-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Payee</th>
                      <th>Category</th>
                      <th>Description</th>
                      <th>Amount</th>
                      <th>Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {result.recent_transactions.map(
                      (transaction, index) => (
                        <tr key={`${transaction.date}-${index}`}>
                          <td>{transaction.date}</td>

                          <td>
                            <div className="payee-cell">
                              <strong>
                                {transaction.merchant_name ||
                                  transaction.counterparty_name ||
                                  "Unresolved"}
                              </strong>

                              {!transaction.merchant_name &&
                                transaction.counterparty_name && (
                                  <small>P2P</small>
                                )}
                            </div>
                          </td>

                          <td>
                            <span className="category-pill">
                              {transaction.category}
                            </span>
                          </td>

                          <td className="description-cell">
                            {transaction.description}
                          </td>

                          <td className="amount-cell">
                            {formatCurrencyExact(transaction.amount)}
                          </td>

                          <td>
                            {transaction.anomaly ? (
                              <span className="status-pill anomaly">
                                  Anomaly
                                </span>
                            ) : (
                              <span className="status-pill normal">
                                Normal
                              </span>
                            )}
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* TRANSACTION EXPLORER */}
          <section className="transactions-section explorer-section">
            <div className="section-heading">
              <div>
                <h2>Transaction Explorer</h2>
                <p>
                  Search, filter and inspect every analyzed transaction.
                </p>
              </div>
            </div>

            <div className="explorer-card">
              <div className="explorer-controls">
                <div className="explorer-search">
                  <input
                    type="text"
                    placeholder="Search merchant, description, category..."
                    value={transactionSearch}
                    onChange={(event) => {
                      setTransactionSearch(event.target.value);
                      resetExplorerPage();
                    }}
                  />
                </div>

                <select
                  value={transactionCategory}
                  onChange={(event) => {
                    setTransactionCategory(event.target.value);
                    resetExplorerPage();
                  }}
                >
                  <option value="all">All categories</option>

                  {transactionCategories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>

                <select
                  value={transactionStatus}
                  onChange={(event) => {
                    setTransactionStatus(event.target.value);
                    resetExplorerPage();
                  }}
                >
                  <option value="all">All transactions</option>
                  <option value="anomalies">
                    Anomalies only
                  </option>
                </select>

                <select
                  value={transactionSort}
                  onChange={(event) => {
                    setTransactionSort(event.target.value);
                    resetExplorerPage();
                  }}
                >
                  <option value="date_desc">
                    Newest first
                  </option>
                  <option value="date_asc">
                    Oldest first
                  </option>
                  <option value="amount_desc">
                    Highest amount
                  </option>
                  <option value="amount_asc">
                    Lowest amount
                  </option>
                </select>
              </div>

              <div className="explorer-summary">
                <span>
                  Showing{" "}
                  <strong>
                    {transactionStart}-{transactionEnd}
                  </strong>{" "}
                  of{" "}
                  <strong>
                    {filteredTransactions.length}
                  </strong>{" "}
                  transactions
                </span>

                {transactionSearch ||
                transactionCategory !== "all" ||
                transactionStatus !== "all" ? (
                  <button
                    className="clear-filters"
                    onClick={() => {
                      setTransactionSearch("");
                      setTransactionCategory("all");
                      setTransactionStatus("all");
                      setTransactionPage(1);
                    }}
                  >
                    Clear filters
                  </button>
                ) : null}
              </div>

              <div className="transactions-table-wrapper">
                <table className="transactions-table explorer-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Payee</th>
                      <th>Category</th>
                      <th>Description</th>
                      <th>Amount</th>
                      <th>Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {paginatedTransactions.length > 0 ? (
                      paginatedTransactions.map(
                        (transaction) => (
                          <tr
                            key={transaction.transaction_id}
                            className="clickable-transaction"
                            onClick={() => setSelectedTransaction(transaction)}
                          >
                            <td>{transaction.date}</td>

                            <td>
                              <div className="payee-cell">
                                <strong>
                                  {transaction.merchant_name ||
                                    transaction.counterparty_name ||
                                    "Unresolved"}
                                </strong>

                                {!transaction.merchant_name &&
                                  transaction.counterparty_name && (
                                    <small>P2P</small>
                                  )}
                              </div>
                            </td>

                            <td>
                              <span className="category-pill">
                                {transaction.category}
                              </span>
                            </td>

                            <td className="description-cell">
                              {transaction.description}
                            </td>

                            <td className="amount-cell">
                              {formatCurrencyExact(
                                transaction.amount
                              )}
                            </td>

                            <td>
                              {transaction.anomaly ? (
                                <span className="status-pill anomaly">
                                  Anomaly
                                </span>
                              ) : (
                                <span className="status-pill normal">
                                  Normal
                                </span>
                              )}
                            </td>
                          </tr>
                        )
                      )
                    ) : (
                      <tr>
                        <td
                          colSpan="6"
                          className="no-results"
                        >
                          No transactions match your filters.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {filteredTransactions.length > 0 && (
                <div className="pagination">
                  <button
                    disabled={transactionPage === 1}
                    onClick={() =>
                      setTransactionPage((page) =>
                        Math.max(1, page - 1)
                      )
                    }
                  >
                    Previous
                  </button>

                  <div className="page-indicator">
                    Page {transactionPage} of {totalPages}
                  </div>

                  <button
                    disabled={transactionPage === totalPages}
                    onClick={() =>
                      setTransactionPage((page) =>
                        Math.min(totalPages, page + 1)
                      )
                    }
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </section>

          {result.anomalies?.length > 0 && (
            <section className="transactions-section">
              <div className="section-heading">
                <div>
                  <h2>Detected Anomalies</h2>
                  <p>
                    Transactions that differ significantly from
                    historical spending patterns.
                  </p>
                </div>
              </div>

              <div className="anomalies-grid">
                {result.anomalies.map((anomaly, index) => (
                  <div
                    className="anomaly-card"
                    key={`${anomaly.date}-${index}`}
                  >
                    <div className="anomaly-top">
                      <span className="status-pill anomaly">
                        {anomaly.anomaly_type === "amount_spike"
                          ? "Amount spike"
                          : anomaly.anomaly_type === "category_spike"
                            ? "Category spike"
                            : anomaly.anomaly_type === "large_one_off"
                              ? "Large one-off"
                              : anomaly.anomaly_type === "unusual_purchase"
                                ? "Unusual purchase"
                                : "Anomaly"}
                      </span>

                      <span className="anomaly-score">
                        Score {Number(anomaly.anomaly_score || 0).toFixed(2)}
                      </span>
                    </div>

                    <h3>
                      {anomaly.merchant_name ||
                        anomaly.counterparty_name ||
                        anomaly.category ||
                        "Unresolved transaction"}
                    </h3>

                    <div className="anomaly-amount">
                      {formatCurrencyExact(anomaly.amount)}
                    </div>

                    <p>
                      {anomaly.anomaly_reason ||
                        "Spending differs from the historical baseline."}
                    </p>

                    <span className="anomaly-date">
                      {anomaly.date}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}
          {selectedTransaction && (
            <div
              className="transaction-detail-overlay"
              onClick={() => setSelectedTransaction(null)}
            >
              <aside
                className="transaction-detail-panel"
                onClick={(event) => event.stopPropagation()}
              >
                <div className="transaction-detail-header">
                  <div>
                    <span className="detail-eyebrow">
                      Transaction details
                    </span>

                    <h2>
                      {selectedTransaction.merchant_name ||
                        selectedTransaction.counterparty_name ||
                        "Unresolved transaction"}
                    </h2>
                  </div>

                  <button
                    className="detail-close"
                    onClick={() => setSelectedTransaction(null)}
                    aria-label="Close transaction details"
                  >
                    ×
                  </button>
                </div>

                <div className="detail-status-row">
                  {selectedTransaction.anomaly ? (
                    <span className="status-pill anomaly">
                      Anomaly
                    </span>
                  ) : (
                    <span className="status-pill normal">
                      Normal
                    </span>
                  )}

                  <span className="detail-date">
                    {selectedTransaction.date}
                  </span>
                </div>

                <div className="detail-amount">
                  {formatCurrencyExact(selectedTransaction.amount)}
                </div>

                <div className="detail-grid">
                  <div className="detail-field">
                    <span>Category</span>
                    <strong>
                      {selectedTransaction.category || "Unresolved"}
                    </strong>
                  </div>

                  <div className="detail-field">
                    <span>Payee type</span>
                    <strong>
                      {selectedTransaction.merchant_name
                        ? "Merchant"
                        : selectedTransaction.counterparty_name
                          ? "P2P / Counterparty"
                          : "Unknown"}
                    </strong>
                  </div>

                  <div className="detail-field">
                    <span>Merchant</span>
                    <strong>
                      {selectedTransaction.merchant_name || "—"}
                    </strong>
                  </div>

                  <div className="detail-field">
                    <span>Counterparty</span>
                    <strong>
                      {selectedTransaction.counterparty_name || "—"}
                    </strong>
                  </div>
                </div>

                <div className="detail-description">
                  <span>Raw transaction description</span>

                  <div>
                    {selectedTransaction.description || "No description"}
                  </div>
                </div>

                <div className="classification-detail">
                  <div className="classification-detail-header">
                    <span>Classification</span>

                    <strong>
                      {selectedTransaction.classification_confidence != null
                        ? `${Number(
                            selectedTransaction.classification_confidence
                          ).toFixed(1)}% confidence`
                        : "Confidence unavailable"}
                    </strong>
                  </div>

                  <div className="classification-method">
                    <span className="classification-method-icon">
                      ✓
                    </span>

                    <div>
                      <strong>
                        {selectedTransaction.classification_method === "exact"
                          ? "Exact merchant match"
                          : selectedTransaction.classification_method === "fuzzy"
                            ? "Fuzzy merchant match"
                            : selectedTransaction.classification_method ===
                                "counterparty"
                              ? "Counterparty match"
                              : selectedTransaction.classification_method === "ml"
                                ? "ML classification"
                                : "Unresolved classification"}
                      </strong>

                      <p>
                        {selectedTransaction.classification_method === "exact"
                          ? "The transaction narration directly matched a known merchant pattern."
                          : selectedTransaction.classification_method === "fuzzy"
                            ? "The narration was matched to the closest known merchant using fuzzy matching."
                            : selectedTransaction.classification_method ===
                                "counterparty"
                              ? "The narration was identified as a person-to-person transfer."
                              : selectedTransaction.classification_method === "ml"
                                ? "The transaction was classified using the machine-learning classifier."
                                : "No sufficiently confident merchant or counterparty match was found."}
                      </p>
                    </div>
                  </div>
                </div>

                {selectedTransaction.anomaly && (
                  <div className="detail-anomaly">
                    <div className="detail-anomaly-heading">
                      <span>Anomaly detected</span>

                      {selectedTransaction.anomaly_score != null && (
                        <strong>
                          Score{" "}
                          {Number(
                            selectedTransaction.anomaly_score
                          ).toFixed(2)}
                        </strong>
                      )}
                    </div>

                    <p>
                      {selectedTransaction.anomaly_reason ||
                        "This transaction differs significantly from the historical spending baseline."}
                    </p>

                    {selectedTransaction.anomaly_type && (
                      <div className="detail-anomaly-type">
                        {selectedTransaction.anomaly_type}
                      </div>
                    )}
                  </div>
                )}

                <div className="detail-footer">
                  <span>Transaction ID</span>
                  <code>
                    {selectedTransaction.transaction_id}
                  </code>
                </div>
              </aside>
            </div>
          )}
        </main>
      )}
    </div>
  );
}

export default App;