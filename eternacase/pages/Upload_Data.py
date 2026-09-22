import streamlit as st
import pandas as pd
from datetime import date
from utils.theme import apply_theme, page_header, section_card_start, section_card_end, sidebar_nav, PRIMARY_PURPLE
from utils.forecasting import load_data, append_to_dataset, save_data
from utils.simple_parser import simple_parse_raw_text

st.set_page_config(page_title="Upload Data", page_icon="📤", layout="wide")
apply_theme()
sidebar_nav("Upload Data")

page_header("Upload / Update Data", "Add new sales records to the dataset")

df = load_data()

tab1, tab2, tab3 = st.tabs(["📁 Clean File Upload", "🪄 Smart Import (Raw → Structured)", "➕ Manual Entry"])

# ---------------------------------------------------------------------------
# Tab 1 — Clean file upload
# ---------------------------------------------------------------------------
with tab1:
    section_card_start("Upload a structured file", PRIMARY_PURPLE)
    st.write("File must already have **Date, Product, Quantity** columns (Revenue/Profit optional — "
             "estimated automatically from past data if missing).")
    file = st.file_uploader("Choose a file", type=["csv", "xlsx"], key="clean_upload")

    if file:
        try:
            if file.name.lower().endswith(".csv"):
                preview_df = pd.read_csv(file)
            else:
                preview_df = pd.read_excel(file)
        except Exception as e:
            st.error(f"Couldn't read that file: {e}")
            preview_df = None

        if preview_df is not None:
            missing = [c for c in ["Date", "Product", "Quantity"] if c not in preview_df.columns]
            if missing:
                st.error(f"Missing required column(s): {', '.join(missing)}. "
                         f"Found columns: {', '.join(preview_df.columns)}")
            else:
                st.write(f"Preview — {len(preview_df)} row(s):")
                st.dataframe(preview_df, use_container_width=True, height=220)
                if st.button("Confirm & Add to Dataset", key="confirm_clean"):
                    try:
                        append_to_dataset(preview_df)
                        st.success(f"✅ Added {len(preview_df)} row(s) to the dataset.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Couldn't add data: {e}")
    section_card_end()

# ---------------------------------------------------------------------------
# Tab 2 — Smart Import (AI-powered, via Claude API)
# ---------------------------------------------------------------------------
with tab2:
    section_card_start("Paste raw / messy order text", PRIMARY_PURPLE)
    st.caption(
        "Free built-in parser — no API key needed. Works best with lines like "
        "\"5 Jan ko Ali ne 2 case liye\" (day + month name + a number followed by "
        "case/unit/piece/box/etc). Always review the preview before confirming."
    )

    raw_text = st.text_area(
        "Raw data (typed text, WhatsApp messages, notes)",
        placeholder="e.g. 5 Jan ko Ali ne 2 case liye, 7 Jan ko 3 case + 1 cover bheji...",
        height=150,
    )

    if st.button("Convert to Table", key="convert_raw"):
        if not raw_text.strip():
            st.warning("Type or paste some text first.")
        else:
            parsed_rows = simple_parse_raw_text(raw_text)
            st.session_state["smart_import_preview"] = parsed_rows

    if "smart_import_preview" in st.session_state:
        rows = st.session_state["smart_import_preview"]
        if not rows:
            st.info(
                "No orders could be recognized. Try a format like \"5 Jan ko Ali ne 2 case liye\" "
                "— each line needs a day + month name, and a number followed by case/unit/piece/box/etc."
            )
        else:
            st.write(f"Found {len(rows)} order(s) — review and edit before adding:")
            preview_df = pd.DataFrame(rows)
            preview_df["Date"] = pd.to_datetime(preview_df["Date"], errors="coerce")

            edited_df = st.data_editor(
                preview_df,
                use_container_width=True,
                num_rows="dynamic",
                key="smart_import_editor",
                column_config={
                    "Date": st.column_config.DateColumn("Date"),
                    "Quantity": st.column_config.NumberColumn("Quantity", min_value=1, step=1),
                },
            )

            col_confirm, col_discard = st.columns([1, 1])
            with col_confirm:
                if st.button("Confirm & Add to Dataset", key="confirm_smart"):
                    clean = edited_df.dropna(subset=["Date", "Product", "Quantity"])
                    if clean.empty:
                        st.warning("No valid rows to add.")
                    else:
                        try:
                            append_to_dataset(clean)
                            st.success(f"✅ Added {len(clean)} row(s) to the dataset.")
                            del st.session_state["smart_import_preview"]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Couldn't add data: {e}")
            with col_discard:
                if st.button("Discard", key="discard_smart"):
                    del st.session_state["smart_import_preview"]
                    st.rerun()
    section_card_end()

# ---------------------------------------------------------------------------
# Tab 3 — Manual entry
# ---------------------------------------------------------------------------
with tab3:
    section_card_start("Add a single order", PRIMARY_PURPLE)
    existing_products = sorted(df["Product"].dropna().unique().tolist()) if not df.empty else []

    with st.form("manual_entry_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            entry_date = st.date_input("Date", value=date.today())
        with col2:
            if existing_products:
                choice = st.selectbox("Product", existing_products + ["+ Add new product..."])
                product_name = st.text_input("New product name") if choice == "+ Add new product..." else choice
            else:
                product_name = st.text_input("Product name")
        with col3:
            quantity = st.number_input("Quantity", min_value=1, step=1)

        submitted = st.form_submit_button("Add Order")
        if submitted:
            if not product_name or not product_name.strip():
                st.error("Please enter a product name.")
            else:
                new_row = pd.DataFrame([{"Date": entry_date, "Product": product_name.strip(), "Quantity": quantity}])
                try:
                    append_to_dataset(new_row)
                    st.success(f"✅ Added order: {quantity} × {product_name.strip()} on {entry_date}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Couldn't add data: {e}")
    section_card_end()

# ---------------------------------------------------------------------------
# Current dataset — editable + exportable
# ---------------------------------------------------------------------------
st.write("")
section_card_start("Current Dataset", "#10b981")

if df.empty:
    st.info("No data yet — add some using the tabs above.")
else:
    st.caption("Edit cells directly, add/delete rows, then click Save Changes. Or export a CSV copy below.")
    editable = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        height=320,
        key="dataset_editor",
        column_config={"Date": st.column_config.DateColumn("Date")},
    )

    col_save, col_export = st.columns([1, 1])
    with col_save:
        if st.button("💾 Save Changes"):
            try:
                save_data(editable)
                st.success("✅ Dataset updated.")
                st.rerun()
            except Exception as e:
                st.error(f"Couldn't save changes: {e}")
    with col_export:
        st.download_button(
            "⬇ Export as CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="sales_data_export.csv",
            mime="text/csv",
        )

section_card_end()