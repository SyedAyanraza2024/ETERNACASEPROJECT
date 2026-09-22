import streamlit as st
import plotly.graph_objects as go
from utils.theme import (
    apply_theme, page_header, section_card_start, section_card_end,
    plotly_dark_layout, sidebar_nav, PRIMARY_PURPLE, PRIMARY_PINK,
)
from utils.forecasting import load_data, run_forecast

st.set_page_config(page_title="Forecast", page_icon="📈", layout="wide")
apply_theme()
sidebar_nav("Forecast")

page_header("Product Forecast", "Predicted demand and restock planning")

df = load_data()
if df.empty:
    st.warning("No data found. Add sales_data.csv to the data/ folder.")
    st.stop()

horizon_map = {"7 days": 7, "30 days": 30, "90 days": 90}
horizon_label = st.selectbox("Forecast Horizon", list(horizon_map.keys()), index=1)
periods = horizon_map[horizon_label]

with st.spinner("Training forecast model..."):
    daily, forecast = run_forecast(df, periods=periods)

future_only = forecast.tail(periods)

c1, c2 = st.columns(2)
with c1:
    section_card_start("Historical Daily Demand", PRIMARY_PURPLE)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["ds"], y=daily["y"], mode="lines",
                              line=dict(color=PRIMARY_PURPLE, width=2)))
    fig = plotly_dark_layout(fig, height=300)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    section_card_end()

with c2:
    section_card_start(f"Predicted Demand — next {horizon_label}", PRIMARY_PINK)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=future_only["ds"], y=future_only["yhat"], mode="lines",
                               name="Predicted", line=dict(color=PRIMARY_PINK, width=3, dash="dash")))
    fig2.add_trace(go.Scatter(x=future_only["ds"], y=future_only["yhat_upper"], mode="lines",
                               line=dict(width=0), showlegend=False))
    fig2.add_trace(go.Scatter(x=future_only["ds"], y=future_only["yhat_lower"], mode="lines",
                               line=dict(width=0), fill="tonexty",
                               fillcolor="rgba(236,72,153,0.15)", showlegend=False))
    fig2 = plotly_dark_layout(fig2, height=300)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    section_card_end()

st.write("")
section_card_start("Restock Check", "#f59e0b")
total_predicted = max(0, future_only["yhat"].sum())
st.metric(f"Total predicted demand ({horizon_label})", f"{total_predicted:.0f} units")

current_stock = st.number_input("Current stock on hand", min_value=0, value=0, step=1)
if current_stock:
    if current_stock < total_predicted:
        st.error(f"⚠️ Restock alert: predicted demand ({total_predicted:.0f}) exceeds current stock ({current_stock}).")
    else:
        st.success(f"✅ Stock looks sufficient for the predicted demand ({total_predicted:.0f} units).")
section_card_end()

st.caption("⚠️ Forecast is based on current order history — accuracy improves as more sales data is added over time.")