"""Pincode Analysis - hyper-local transaction hotspots."""
from dash_utils import get_top_pincodes, page_setup, period_sidebar
import plotly.express as px
import streamlit as st

page_setup("Pincode Analysis")
year, quarter = period_sidebar()
n = st.slider("Number of pincodes", 5, 30, 20)
tp = get_top_pincodes(n, year, quarter)

st.subheader(f"Top {n} Pincodes by Value")
st.plotly_chart(px.bar(tp.sort_values("txn_amount"),
                       x="txn_amount", y="pincode", orientation="h",
                       color="txn_amount", color_continuous_scale="Purples"),
                use_container_width=True)
st.dataframe(tp, use_container_width=True, hide_index=True)
