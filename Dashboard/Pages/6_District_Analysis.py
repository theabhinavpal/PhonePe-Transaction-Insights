"""District Analysis - top districts and average-ticket hotspots."""
from dash_utils import get_top_districts, page_setup, period_sidebar
from src.visualizations import bar_top_districts
import streamlit as st

page_setup("District Analysis")
year, quarter = period_sidebar()
n = st.slider("Number of districts", 5, 30, 15)
td = get_top_districts(n, year, quarter)

st.subheader(f"Top {n} Districts by Transaction Value")
st.plotly_chart(bar_top_districts(td, n=n), use_container_width=True)
td = td.assign(avg_ticket=(td["txn_amount"] / td["txn_count"]).round(0))
st.dataframe(td, use_container_width=True, hide_index=True)
