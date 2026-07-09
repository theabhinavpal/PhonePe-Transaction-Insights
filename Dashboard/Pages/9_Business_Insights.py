"""Business Insights - renders the curated, data-grounded insights report."""
from pathlib import Path
from dash_utils import page_setup, period_sidebar
import streamlit as st

page_setup("Business Insights")
period_sidebar()

md_path = Path(__file__).resolve().parent.parent.parent / "reports" / "Business_Insights.md"
if md_path.exists():
    st.markdown(md_path.read_text(encoding="utf-8"))
else:
    st.info("Business_Insights.md not found - run the pipeline and report build.")
