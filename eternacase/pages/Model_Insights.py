import streamlit as st
import plotly.graph_objects as go
from utils.theme import (
    apply_theme, page_header, section_card_start, section_card_end,
    plotly_dark_layout, sidebar_nav, kpi_card, PRIMARY_PURPLE, PRIMARY_PINK,
)
from utils.forecasting import load_data, evaluate_model

st.set_page_config(page_title="Model Insights", page_icon="🧠", layout="wide")
apply_theme()
sidebar_nav("Model Insights")

page_header("Model Insights", "Forecast accuracy and performance details")

df = load_data()
if df.empty:
    st.warning("No data found. Add sales_data.csv to the data/ folder.")
    st.stop()

test_days = st.slider("Test period (days held out for evaluation)", min_value=7, max_value=30, value=15)

with st.spinner("Evaluating model..."):
    result = evaluate_model(df, test_days=test_days)

if result is None:
    st.warning("Not enough data yet to reliably evaluate the model. Add more sales history first.")
    st.stop()

k1, k2 = st.columns(2)
with k1:
    kpi_card("MAE (avg error)", f"{result['mae']:.2f} units")
with k2:
    kpi_card("RMSE", f"{result['rmse']:.2f} units")

st.write("")

section_card_start(f"Actual vs Predicted — last {test_days} days", PRIMARY_PURPLE)
comp = result["comparison"]
fig = go.Figure()
fig.add_trace(go.Scatter(x=comp["Date"], y=comp["Actual"], mode="lines+markers",
                          name="Actual", line=dict(color=PRIMARY_PURPLE, width=2)))
fig.add_trace(go.Scatter(x=comp["Date"], y=comp["Predicted"], mode="lines+markers",
                          name="Predicted", line=dict(color=PRIMARY_PINK, width=2, dash="dash")))
fig = plotly_dark_layout(fig, height=320)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
section_card_end()

st.caption(
    "MAE = average number of units the model was off by per day. "
    "RMSE is similar but penalizes bigger misses more. Lower is better for both. "
    "Accuracy will improve as more real sales history is added."
)

st.write("")
section_card_start("Dataset Summary", "#10b981")
st.write(f"**Records:** {len(df)}  |  **Date range:** {df['Date'].min().date()} to {df['Date'].max().date()}  |  **Products:** {df['Product'].nunique()}")
section_card_end()