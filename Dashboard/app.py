"""
dashboard/app.py
======================================================================
PhonePe Transaction Insights - Streamlit entry point (Home).

Run from the project root:
    streamlit run dashboard/app.py

Streamlit auto-discovers the sibling ``pages/`` folder to build the
multi-page navigation (Executive, Transactions, Users, Insurance, State,
District, Pincode, Trend, Business Insights).
"""

from __future__ import annotations

import streamlit as st

from dash_utils import (get_category, get_kpis, get_region_share,
                        get_state_ranking, kpi_card, page_setup, period_sidebar)
from src.utils import human_count, inr_compact
from src.visualizations import (bar_top_states, pie_category, treemap_states)

page_setup("PhonePe Transaction Insights")
year, quarter = period_sidebar()

st.markdown(
    "An end-to-end analytics platform over PhonePe Pulse-style digital-payment "
    "data across **36 states/UTs**, **6 years** and **4 quarters** - built with "
    "a Python ETL, a SQL star-schema warehouse and interactive Plotly dashboards."
)

# ---- KPI row -------------------------------------------------------- #
k = get_kpis(year, quarter)
c1, c2, c3, c4 = st.columns(4)
kpi_card(c1, "Total Transaction Value", inr_compact(k["total_value"]))
kpi_card(c2, "Total Transactions", human_count(k["total_volume"]))
kpi_card(c3, "Avg Ticket Size", f"Rs {k['avg_ticket']:,.0f}")
kpi_card(c4, "Registered Users", human_count(k["registered_users"]))

c5, c6, c7, c8 = st.columns(4)
kpi_card(c5, "App Opens (latest Q)", human_count(k["app_opens"]))
kpi_card(c6, "Insurance Premium", inr_compact(k["insurance_premium"]))
kpi_card(c7, "Insurance Policies", human_count(k["insurance_policies"]))
sr = get_state_ranking(year, quarter)
kpi_card(c8, "Top State",
         sr.iloc[0]["state"] if not sr.empty else "-",
         f"{sr.iloc[0]['market_share_pct']}% share" if not sr.empty else "")

st.divider()

# ---- Overview charts ------------------------------------------------ #
left, right = st.columns([3, 2])
with left:
    st.subheader("Top States by Value")
    st.plotly_chart(bar_top_states(sr, n=10), use_container_width=True)
with right:
    st.subheader("Category Mix")
    st.plotly_chart(pie_category(get_category(year, quarter)),
                    use_container_width=True)

st.subheader("Value Contribution by Region & State")
st.plotly_chart(treemap_states(sr), use_container_width=True)

st.subheader("Regional Share")
st.dataframe(get_region_share(year, quarter), use_container_width=True, hide_index=True)

st.caption("Use the left sidebar to filter by year and quarter, and the page "
           "navigation to drill into transactions, users, insurance and geography.")
