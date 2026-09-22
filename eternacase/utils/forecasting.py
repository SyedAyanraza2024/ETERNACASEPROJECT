"""
Data loading + forecasting logic shared by the app pages.
"""

import pandas as pd
import os
import warnings

warnings.filterwarnings("ignore")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sales_data.csv")


def load_data():
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame(columns=["Date", "Product", "Quantity", "Revenue", "Profit"])
    df = pd.read_csv(DATA_PATH)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def daily_totals(df, value_col="Quantity"):
    daily = df.groupby("Date")[value_col].sum().reset_index()
    return daily.sort_values("Date")


def run_forecast(df, periods=30):
    """Train a Prophet model on daily quantity sold and forecast forward."""
    from prophet import Prophet

    daily = df.groupby("Date")["Quantity"].sum().reset_index()
    daily.columns = ["ds", "y"]

    full_range = pd.date_range(daily["ds"].min(), daily["ds"].max(), freq="D")
    daily = daily.set_index("ds").reindex(full_range, fill_value=0).rename_axis("ds").reset_index()

    model = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=False)
    model.fit(daily)

    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    # Demand can never be negative — Prophet's additive model can dip below 0
    # on sparse/spiky data, so clip predictions and their confidence bands at 0.
    for col in ["yhat", "yhat_lower", "yhat_upper"]:
        forecast[col] = forecast[col].clip(lower=0)

    return daily, forecast


def evaluate_model(df, test_days=15):
    """
    Train on all data except the last `test_days`, predict that period,
    and compare against what actually happened. Returns MAE, RMSE,
    and a dataframe with actual vs predicted for plotting.
    """
    from prophet import Prophet
    import numpy as np

    daily = df.groupby("Date")["Quantity"].sum().reset_index()
    daily.columns = ["ds", "y"]

    full_range = pd.date_range(daily["ds"].min(), daily["ds"].max(), freq="D")
    daily = daily.set_index("ds").reindex(full_range, fill_value=0).rename_axis("ds").reset_index()

    if len(daily) <= test_days + 10:
        return None  # not enough data to split meaningfully

    train = daily.iloc[:-test_days]
    test = daily.iloc[-test_days:]

    model = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=False)
    model.fit(train)

    future = model.make_future_dataframe(periods=test_days)
    forecast = model.predict(future)

    predicted = forecast.set_index("ds").loc[test["ds"], "yhat"].clip(lower=0).values
    actual = test["y"].values

    mae = np.mean(np.abs(predicted - actual))
    rmse = np.sqrt(np.mean((predicted - actual) ** 2))

    comparison = pd.DataFrame({
        "Date": test["ds"].values,
        "Actual": actual,
        "Predicted": predicted,
    })

    return {"mae": mae, "rmse": rmse, "comparison": comparison, "test_days": test_days}


# ---------------------------------------------------------------------------
# Data-writing helpers for the Upload Data page
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = ["Date", "Product", "Quantity"]


def get_product_stats(df):
    """Per-product average revenue-per-unit and profit-per-unit, learned from history.
    Used to estimate Revenue/Profit for new rows that only specify Quantity."""
    if df.empty:
        return pd.DataFrame(columns=["Product", "avg_revenue_per_unit", "avg_profit_per_unit"])

    grouped = df.groupby("Product").agg(
        total_qty=("Quantity", "sum"),
        total_rev=("Revenue", "sum"),
        total_profit=("Profit", "sum"),
    ).reset_index()

    grouped["avg_revenue_per_unit"] = grouped.apply(
        lambda r: r["total_rev"] / r["total_qty"] if r["total_qty"] else 0, axis=1
    )
    grouped["avg_profit_per_unit"] = grouped.apply(
        lambda r: r["total_profit"] / r["total_qty"] if r["total_qty"] else 0, axis=1
    )
    return grouped[["Product", "avg_revenue_per_unit", "avg_profit_per_unit"]]


def estimate_revenue_profit(df, new_rows):
    """
    Fill in missing Revenue/Profit on new_rows using historical per-unit averages
    for that product. Unknown products fall back to the overall dataset average.
    Rows that already have Revenue/Profit are left untouched.
    """
    out = new_rows.copy()
    if "Revenue" not in out.columns:
        out["Revenue"] = pd.NA
    if "Profit" not in out.columns:
        out["Profit"] = pd.NA

    total_qty = df["Quantity"].sum() if not df.empty else 0
    overall_rev = (df["Revenue"].sum() / total_qty) if total_qty else 0
    overall_profit = (df["Profit"].sum() / total_qty) if total_qty else 0

    stats_map = get_product_stats(df).set_index("Product").to_dict("index")

    for i, row in out.iterrows():
        prod_stats = stats_map.get(row["Product"], None)
        rev_rate = prod_stats["avg_revenue_per_unit"] if prod_stats else overall_rev
        profit_rate = prod_stats["avg_profit_per_unit"] if prod_stats else overall_profit

        if pd.isna(out.at[i, "Revenue"]):
            out.at[i, "Revenue"] = round(float(row["Quantity"]) * rev_rate, 2)
        if pd.isna(out.at[i, "Profit"]):
            out.at[i, "Profit"] = round(float(row["Quantity"]) * profit_rate, 2)

    return out


def validate_new_rows(new_rows):
    """Check required columns exist and basic types are sane. Returns (ok, error_message)."""
    missing = [c for c in REQUIRED_COLUMNS if c not in new_rows.columns]
    if missing:
        return False, f"Missing required column(s): {', '.join(missing)}"
    if new_rows.empty:
        return False, "No rows to add."
    try:
        pd.to_datetime(new_rows["Date"])
    except Exception:
        return False, "Some Date values couldn't be parsed. Use a format like 2026-01-05."
    if not pd.to_numeric(new_rows["Quantity"], errors="coerce").notna().all():
        return False, "Quantity column must be numeric."
    return True, ""


def append_to_dataset(new_rows):
    """Validate, fill missing Revenue/Profit, append to the CSV, and persist to disk.
    Returns the full updated dataframe."""
    ok, msg = validate_new_rows(new_rows)
    if not ok:
        raise ValueError(msg)

    df = load_data()
    prepared = estimate_revenue_profit(df, new_rows)
    prepared["Date"] = pd.to_datetime(prepared["Date"])
    prepared["Quantity"] = pd.to_numeric(prepared["Quantity"]).astype(int)
    prepared["Revenue"] = pd.to_numeric(prepared["Revenue"]).round(2)
    prepared["Profit"] = pd.to_numeric(prepared["Profit"]).round(2)

    combined = pd.concat([df, prepared[["Date", "Product", "Quantity", "Revenue", "Profit"]]], ignore_index=True)
    combined = combined.sort_values("Date").reset_index(drop=True)
    save_data(combined)
    return combined


def save_data(df):
    """Persist the full dataframe back to the CSV on disk (used by the editable table too)."""
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(DATA_PATH, index=False)