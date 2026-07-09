"""Trend Analysis - QoQ growth, moving average and cumulative value."""
from dash_utils import get_trend, get_yoy, page_setup, period_sidebar
from src.visualizations import line_national_trend
import plotly.express as px
import streamlit as st

page_setup("Trend Analysis")
period_sidebar()
tr = get_trend()

st.subheader("Value Trend with 4-Quarter Moving Average")
st.plotly_chart(line_national_trend(tr), use_container_width=True)

l, r = st.columns(2)
with l:
    st.subheader("Quarter-over-Quarter Growth %")
    st.plotly_chart(px.bar(tr, x="period", y="qoq_pct", color="qoq_pct",
                           color_continuous_scale="RdYlGn"),
                    use_container_width=True)
with r:
    st.subheader("Cumulative Value")
    st.plotly_chart(px.area(tr, x="period", y="running_total"),
                    use_container_width=True)

st.subheader("Year-over-Year Growth")
st.dataframe(get_yoy()[["year", "txn_amount", "yoy_pct"]],
             use_container_width=True, hide_index=True)
