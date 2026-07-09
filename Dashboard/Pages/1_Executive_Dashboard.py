"""Executive Dashboard - headline KPIs, YoY growth and category mix."""
from dash_utils import (get_category, get_kpis, get_state_ranking, get_trend,
                        get_yoy, kpi_card, page_setup, period_sidebar)
from src.utils import human_count, inr_compact
from src.visualizations import (area_category_trend, bar_top_states,
                                line_national_trend, pie_category)
from dash_utils import get_category_by_year
import streamlit as st

page_setup("Executive Dashboard")
year, quarter = period_sidebar()
k = get_kpis(year, quarter)

c = st.columns(4)
kpi_card(c[0], "Transaction Value", inr_compact(k["total_value"]))
kpi_card(c[1], "Transaction Volume", human_count(k["total_volume"]))
kpi_card(c[2], "Avg Ticket", f"Rs {k['avg_ticket']:,.0f}")
kpi_card(c[3], "Registered Users", human_count(k["registered_users"]))

yoy = get_yoy()
st.subheader("Year-over-Year Value Growth")
st.dataframe(yoy.assign(txn_value=yoy["txn_amount"].map(inr_compact))
             [["year", "txn_value", "yoy_pct"]],
             use_container_width=True, hide_index=True)

l, r = st.columns(2)
with l:
    st.subheader("National Trend")
    st.plotly_chart(line_national_trend(get_trend()), use_container_width=True)
with r:
    st.subheader("Category Mix Over Time")
    st.plotly_chart(area_category_trend(get_category_by_year()), use_container_width=True)

l2, r2 = st.columns([3, 2])
with l2:
    st.plotly_chart(bar_top_states(get_state_ranking(year, quarter), n=10),
                    use_container_width=True)
with r2:
    st.plotly_chart(pie_category(get_category(year, quarter)), use_container_width=True)
