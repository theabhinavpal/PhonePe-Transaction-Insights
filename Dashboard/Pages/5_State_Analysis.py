"""State Analysis - leaderboard, market share, treemap and drill-down."""
from dash_utils import (get_region_share, get_state_ranking, get_top_districts,
                        page_setup, period_sidebar)
from src.visualizations import bar_top_states, treemap_states
import plotly.express as px
import streamlit as st

page_setup("State Analysis")
year, quarter = period_sidebar()
sr = get_state_ranking(year, quarter)

st.plotly_chart(treemap_states(sr), use_container_width=True)

l, r = st.columns([3, 2])
with l:
    st.subheader("State Leaderboard")
    st.plotly_chart(bar_top_states(sr, n=15), use_container_width=True)
with r:
    st.subheader("Regional Share")
    reg = get_region_share(year, quarter)
    st.plotly_chart(px.pie(reg, names="region", values="txn_amount", hole=0.4),
                    use_container_width=True)

st.subheader("Full State Table")
st.dataframe(sr[["rank", "state", "region", "txn_amount", "txn_count",
                 "market_share_pct", "avg_ticket"]],
             use_container_width=True, hide_index=True)
