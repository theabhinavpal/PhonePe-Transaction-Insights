"""Transactions - category breakdown, ticket size and value/volume tables."""
from dash_utils import get_category, get_state_ranking, page_setup, period_sidebar
from src.utils import inr_compact
from src.visualizations import bar_top_states, pie_category
import streamlit as st

page_setup("Transactions")
year, quarter = period_sidebar()

cat = get_category(year, quarter)
st.subheader("Payment Category Breakdown")
st.plotly_chart(pie_category(cat), use_container_width=True)
st.dataframe(
    cat.assign(value=cat["txn_amount"].map(inr_compact),
               avg_ticket=cat["avg_ticket"].map(lambda v: f"Rs {v:,.0f}"))
       [["category", "value", "txn_count", "pct_value", "avg_ticket"]],
    use_container_width=True, hide_index=True)

st.subheader("State Value Leaderboard")
sr = get_state_ranking(year, quarter)
metric = st.radio("Rank by", ["txn_amount", "txn_count"], horizontal=True)
st.plotly_chart(bar_top_states(sr, metric=metric, n=15), use_container_width=True)
st.dataframe(sr[["rank", "state", "region", "txn_amount", "txn_count",
                 "market_share_pct", "avg_ticket"]],
             use_container_width=True, hide_index=True)
