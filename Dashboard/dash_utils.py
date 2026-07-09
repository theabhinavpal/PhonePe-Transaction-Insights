"""
dashboard/dash_utils.py
======================================================================
Shared helpers for every Streamlit page: sys.path bootstrap (so ``src``
is importable when Streamlit runs ``dashboard/app.py``), cached data
accessors, KPI-card rendering, sidebar filters and consistent theming.
"""

from __future__ import annotations

import sys
from pathlib import Path

# --- make the project root importable ------------------------------- #
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from src import analytics as A  # noqa: E402
from src.utils import inr_compact, human_count  # noqa: E402
from src.visualizations import PHONEPE  # noqa: E402

PAGE_ICON = "📊"


def page_setup(title: str) -> None:
    """Standard page config + header + light CSS."""
    st.set_page_config(page_title=f"PhonePe Insights · {title}",
                       page_icon=PAGE_ICON, layout="wide")
    st.markdown(f"""
        <style>
        .stApp {{ background: #faf9fd; }}
        .kpi-card {{
            background: linear-gradient(135deg, {PHONEPE['primary']}, {PHONEPE['secondary']});
            color: white; border-radius: 14px; padding: 18px 20px;
            box-shadow: 0 4px 14px rgba(95,37,159,0.25);
        }}
        .kpi-card h2 {{ margin: 0; font-size: 1.7rem; }}
        .kpi-card p  {{ margin: 0; opacity: 0.85; font-size: 0.85rem; }}
        h1, h2, h3 {{ color: {PHONEPE['primary']}; }}
        </style>
    """, unsafe_allow_html=True)
    st.title(f"{PAGE_ICON} {title}")


def kpi_card(col, label: str, value: str, sub: str = "") -> None:
    """Render a single gradient KPI card into a column."""
    col.markdown(
        f"<div class='kpi-card'><p>{label}</p><h2>{value}</h2>"
        f"<p>{sub}</p></div>", unsafe_allow_html=True)


# --------------------------------------------------------------------- #
# Cached data accessors (thin wrappers around analytics)
# --------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def get_kpis(year=None, quarter=None):
    return A.kpi_summary(year, quarter)


@st.cache_data(show_spinner=False)
def get_state_ranking(year=None, quarter=None):
    return A.state_ranking(year, quarter)


@st.cache_data(show_spinner=False)
def get_region_share(year=None, quarter=None):
    return A.region_share(year, quarter)


@st.cache_data(show_spinner=False)
def get_category(year=None, quarter=None):
    return A.category_breakdown(year, quarter)


@st.cache_data(show_spinner=False)
def get_category_by_year():
    return A.category_by_year()


@st.cache_data(show_spinner=False)
def get_trend():
    return A.national_trend()


@st.cache_data(show_spinner=False)
def get_yoy():
    return A.yoy_growth()


@st.cache_data(show_spinner=False)
def get_top_districts(limit=15, year=None, quarter=None):
    return A.top_districts(limit, year, quarter)


@st.cache_data(show_spinner=False)
def get_top_pincodes(limit=15, year=None, quarter=None):
    return A.top_pincodes(limit, year, quarter)


@st.cache_data(show_spinner=False)
def get_device_share():
    return A.device_share()


@st.cache_data(show_spinner=False)
def get_top_states_users(limit=10):
    return A.top_states_by_users(limit)


@st.cache_data(show_spinner=False)
def get_insurance(year=None, quarter=None):
    return A.insurance_by_state(year, quarter)


@st.cache_data(show_spinner=False)
def get_filter_options():
    return A.available_years(), A.available_quarters()


def period_sidebar():
    """Render year/quarter filters in the sidebar; returns (year, quarter)."""
    years, quarters = get_filter_options()
    st.sidebar.header("Filters")
    y = st.sidebar.selectbox("Year", ["All"] + years, index=0)
    q = st.sidebar.selectbox("Quarter", ["All"] + quarters, index=0)
    st.sidebar.caption("Data: PhonePe Pulse-style dataset · "
                       f"{years[0]}–{years[-1]}")
    return (None if y == "All" else int(y),
            None if q == "All" else int(q))
