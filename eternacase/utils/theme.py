"""
Shared theme (CSS) and small UI helper components used across every page,
so the whole app keeps one consistent dark, card-based look.
"""

import streamlit as st

PRIMARY_PURPLE = "#7c5cff"
PRIMARY_PINK = "#ec4899"
PRIMARY_GREEN = "#10b981"
PRIMARY_ORANGE = "#f59e0b"
PRIMARY_BLUE = "#6366f1"
TEXT_MUTED = "#9ca3af"

CHART_COLORWAY = [PRIMARY_PURPLE, PRIMARY_PINK, PRIMARY_GREEN, PRIMARY_ORANGE, PRIMARY_BLUE]


def apply_theme():
    """Inject global CSS for the dark card-based theme. Call once per page, right after set_page_config."""
    st.markdown(
        """
        <style>
        /* ---- App background ---- */
        .stApp {
            background-color: #0f1117;
        }

        /* ---- Sidebar ---- */
        section[data-testid="stSidebar"] {
            background-color: #12141c;
            border-right: 1px solid #23252f;
        }

        /* ---- Headings ---- */
        h1, h2, h3 {
            color: #f5f5f7 !important;
        }

        /* ---- Card container (use with st.container(border=True)) ---- */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #171923;
            border: 1px solid #23252f !important;
            border-radius: 14px !important;
        }

        /* ---- Metric styling ---- */
        div[data-testid="stMetric"] {
            background-color: transparent;
        }
        div[data-testid="stMetricLabel"] {
            color: #9ca3af !important;
            font-size: 0.75rem !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        div[data-testid="stMetricValue"] {
            color: #f5f5f7 !important;
        }

        /* ---- Buttons ---- */
        .stButton > button {
            background-color: #1e2029;
            color: #f5f5f7;
            border: 1px solid #2e3140;
            border-radius: 8px;
        }
        .stButton > button:hover {
            border-color: #7c5cff;
            color: #7c5cff;
        }

        /* ---- Tabs ---- */
        button[data-baseweb="tab"] {
            color: #9ca3af;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #7c5cff;
        }

        /* ---- Divider color ---- */
        hr {
            border-color: #23252f !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = ""):
    """Gradient title + subtitle, matching the Lumina-style header."""
    st.markdown(
        f"""
        <div style="margin-bottom: 0.5rem;">
            <h1 style="
                background: linear-gradient(90deg, {PRIMARY_PURPLE}, {PRIMARY_PINK});
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 1.8rem;
                font-weight: 700;
                margin-bottom: 0.1rem;
            ">{title}</h1>
            <p style="color: {TEXT_MUTED}; margin-top: 0; font-size: 0.9rem;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, delta: str = "", delta_positive: bool = True, icon: str = ""):
    """A styled KPI card matching the screenshot's metric cards (label, big value, colored delta pill)."""
    delta_color = PRIMARY_GREEN if delta_positive else "#ef4444"
    delta_bg = "rgba(16,185,129,0.15)" if delta_positive else "rgba(239,68,68,0.15)"
    arrow = "↗" if delta_positive else "↘"

    delta_html = ""
    if delta:
        delta_html = f"""
        <span style="
            background-color: {delta_bg};
            color: {delta_color};
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 6px;
            margin-top: 6px;
            display: inline-block;
        ">{arrow} {delta}</span>
        """

    st.markdown(
        f"""
        <div style="
            background-color: #171923;
            border: 1px solid #23252f;
            border-radius: 14px;
            padding: 18px 20px;
        ">
            <div style="color: {TEXT_MUTED}; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em;">
                {label}
            </div>
            <div style="color: #f5f5f7; font-size: 1.6rem; font-weight: 700; margin-top: 6px;">
                {value}
            </div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_card_start(title: str, accent_color: str = PRIMARY_PURPLE):
    """Open a bordered section card with a colored left-accent title (call section_card_end() after content)."""
    st.markdown(
        f"""
        <div style="
            background-color: #171923;
            border: 1px solid #23252f;
            border-radius: 14px;
            padding: 18px 20px 8px 20px;
            margin-bottom: 1rem;
        ">
            <div style="
                border-left: 3px solid {accent_color};
                padding-left: 10px;
                color: #f5f5f7;
                font-weight: 600;
                font-size: 0.95rem;
                margin-bottom: 10px;
            ">{title}</div>
        """,
        unsafe_allow_html=True,
    )


def section_card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def plotly_dark_layout(fig, height=300):
    """Apply consistent dark styling to any plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f5f5f7"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        colorway=CHART_COLORWAY,
        legend=dict(font=dict(color="#9ca3af")),
    )
    fig.update_xaxes(gridcolor="#23252f", zerolinecolor="#23252f")
    fig.update_yaxes(gridcolor="#23252f", zerolinecolor="#23252f")
    return fig


def sidebar_nav(active: str = "Home"):
    """Consistent sidebar navigation across all pages."""
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 8px 0 20px 0;">
                <div style="
                    background: linear-gradient(90deg, {PRIMARY_PURPLE}, {PRIMARY_PINK});
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-size: 1.3rem;
                    font-weight: 700;
                ">📦 Eterna Case</div>
                <div style="color: {TEXT_MUTED}; font-size: 0.8rem;">Demand Forecasting</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        for path, label in [
            ("Home.py", "🏠 Home"),
            ("pages/1_📈_Forecast.py", "📈 Forecast"),
            ("pages/Upload_Data.py", "📤 Upload Data"),
            ("pages/Model_Insights.py", "🧠 Model Insights"),
        ]:
            try:
                st.page_link(path, label=label)
            except Exception:
                pass