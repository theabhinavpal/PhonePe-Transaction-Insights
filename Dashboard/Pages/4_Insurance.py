"""Insurance - premium, policies and penetration by state/region."""
from dash_utils import get_insurance, get_kpis, kpi_card, page_setup, period_sidebar
from src.utils import human_count, inr_compact
import plotly.express as px
import streamlit as st

page_setup("Insurance")
year, quarter = period_sidebar()
k = get_kpis(year, quarter)

c = st.columns(3)
kpi_card(c[0], "Insurance Premium", inr_compact(k["insurance_premium"]))
kpi_card(c[1], "Policies Sold", human_count(k["insurance_policies"]))
avp = k["insurance_premium"] / k["insurance_policies"] if k["insurance_policies"] else 0
kpi_card(c[2], "Avg Premium / Policy", f"Rs {avp:,.0f}")

ins = get_insurance(year, quarter)
st.subheader("Insurance Premium by State")
st.plotly_chart(px.bar(ins.nlargest(15, "premium").sort_values("premium"),
                       x="premium", y="state", orientation="h", color="premium",
                       color_continuous_scale="Purples"),
                use_container_width=True)
st.subheader("Premium by Region")
reg = ins.groupby("region", as_index=False)["premium"].sum()
st.plotly_chart(px.pie(reg, names="region", values="premium", hole=0.4),
                use_container_width=True)
st.dataframe(ins, use_container_width=True, hide_index=True)
