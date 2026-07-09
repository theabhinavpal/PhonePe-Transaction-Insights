"""Users - registered users, engagement and device-brand mix."""
from dash_utils import (get_device_share, get_kpis, get_top_states_users,
                        kpi_card, page_setup, period_sidebar)
from src.utils import human_count
from src.visualizations import bar_device_share
import plotly.express as px
import streamlit as st

page_setup("Users & Engagement")
period_sidebar()
k = get_kpis()

c = st.columns(3)
kpi_card(c[0], "Registered Users (latest Q)", human_count(k["registered_users"]))
kpi_card(c[1], "App Opens (latest Q)", human_count(k["app_opens"]))
opu = k["app_opens"] / k["registered_users"] if k["registered_users"] else 0
kpi_card(c[2], "App Opens / User", f"{opu:,.1f}")

l, r = st.columns(2)
with l:
    st.subheader("Device Brand Share")
    st.plotly_chart(bar_device_share(get_device_share()), use_container_width=True)
with r:
    st.subheader("Top States by Registered Users")
    tsu = get_top_states_users(10)
    st.plotly_chart(px.bar(tsu.sort_values("registered_users"),
                           x="registered_users", y="state", orientation="h",
                           color="registered_users",
                           color_continuous_scale="Purples"),
                    use_container_width=True)
st.dataframe(get_device_share(), use_container_width=True, hide_index=True)
