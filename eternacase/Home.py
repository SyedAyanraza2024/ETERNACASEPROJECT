import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from utils.theme import (
    apply_theme, page_header, kpi_card, section_card_start, section_card_end,
    plotly_dark_layout, sidebar_nav, PRIMARY_PURPLE, PRIMARY_PINK, PRIMARY_GREEN,
)
from utils.forecasting import load_data, daily_totals, append_to_dataset

st.set_page_config(page_title="Eterna Case | Sales Analytics", page_icon="📦", layout="wide")
apply_theme()
sidebar_nav("Home")

df = load_data()

# ---- Top header row ----
col_title, col_btns = st.columns([3, 1])
with col_title:
    page_header("Eterna Case Sales Analytics", "Real-time performance metrics")
with col_btns:
    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button("⬆ Import"):
            st.switch_page("pages/Upload_Data.py")

    with b2:
        st.download_button(
            "⬇ Export",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="sales_data_export.csv",
            mime="text/csv",
        )

    with b3:
        with st.popover("+ New Entry"):
            st.caption("Quick add — for more options (files, smart import) use the Upload Data page.")
            existing_products = sorted(df["Product"].dropna().unique().tolist()) if not df.empty else []

            with st.form("quick_new_entry_form"):
                entry_date = st.date_input("Date", value=date.today())
                if existing_products:
                    choice = st.selectbox("Product", existing_products + ["+ Add new product..."])
                    product_name = st.text_input("New product name") if choice == "+ Add new product..." else choice
                else:
                    product_name = st.text_input("Product name")
                quantity = st.number_input("Quantity", min_value=1, step=1)

                submitted = st.form_submit_button("Add Order")
                if submitted:
                    if not product_name or not product_name.strip():
                        st.error("Please enter a product name.")
                    else:
                        new_row_df = pd.DataFrame(
                            [{"Date": entry_date, "Product": product_name.strip(), "Quantity": quantity}]
                        )
                        try:
                            append_to_dataset(new_row_df)
                            st.success(f"✅ Added {quantity} × {product_name.strip()}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Couldn't add data: {e}")

st.write("")

if df.empty:
    st.warning("No data found. Add sales_data.csv to the data/ folder.")
    st.stop()

# ---- KPI cards (real values from dataset) ----
total_revenue = df["Revenue"].sum()
total_orders = len(df)
total_units = df["Quantity"].sum()
avg_order_value = df["Revenue"].mean()

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("Total Revenue", f"Rs {total_revenue:,.0f}")
with k2:
    kpi_card("Total Orders", f"{total_orders}")
with k3:
    kpi_card("Total Units Sold", f"{total_units}")
with k4:
    kpi_card("Avg Order Value", f"Rs {avg_order_value:,.0f}")

st.write("")

# ---- Row: Monthly trend + product mix ----
c1, c2 = st.columns([2, 1])

with c1:
    section_card_start("Daily Units Sold Trend", PRIMARY_PURPLE)
    trend = daily_totals(df, "Quantity")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["Date"], y=trend["Quantity"], mode="lines",
                              name="Units", line=dict(color=PRIMARY_PURPLE, width=2)))
    fig = plotly_dark_layout(fig, height=280)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    section_card_end()

with c2:
    section_card_start("Order Size Split", PRIMARY_PINK)
    qty_counts = df["Quantity"].value_counts().sort_index()
    fig2 = go.Figure()
    fig2.add_trace(go.Pie(labels=[f"{q} unit(s)" for q in qty_counts.index],
                           values=qty_counts.values, hole=0.6))
    fig2 = plotly_dark_layout(fig2, height=280)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    section_card_end()

# ---- Row: Monthly revenue + quantity split ----
c3, c4 = st.columns(2)

with c3:
    section_card_start("Monthly Revenue", PRIMARY_GREEN)
    monthly = df.copy()
    monthly["Month"] = monthly["Date"].dt.to_period("M").astype(str)
    monthly_rev = monthly.groupby("Month")["Revenue"].sum().reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=monthly_rev["Month"], y=monthly_rev["Revenue"], marker_color=PRIMARY_GREEN))
    fig3 = plotly_dark_layout(fig3, height=260)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    section_card_end()

with c4:
    section_card_start("Monthly Orders", "#f59e0b")
    monthly_orders = monthly.groupby("Month").size().reset_index(name="Orders")
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(x=monthly_orders["Month"], y=monthly_orders["Orders"], marker_color="#f59e0b"))
    fig4 = plotly_dark_layout(fig4, height=260)
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
    section_card_end()