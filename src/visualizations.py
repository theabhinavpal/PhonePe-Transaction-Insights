"""
src/visualizations.py
======================================================================
Reusable Plotly figure builders. Every function takes a tidy DataFrame
(from ``src.analytics``) and returns a ``plotly.graph_objects.Figure`` so
the same charts can be embedded in the Streamlit dashboard *and* exported
to PNG for the static report.

A single ``PHONEPE`` theme dict keeps colour and layout consistent.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# PhonePe-inspired palette (indigo/purple family) - not the brand asset.
PHONEPE = {
    "primary": "#5f259f",
    "secondary": "#7b3fbf",
    "accent": "#00baf2",
    "sequence": ["#5f259f", "#7b3fbf", "#00baf2", "#f7a600",
                 "#e4405f", "#2ecc71", "#34495e", "#95a5a6"],
    "font": "Inter, Segoe UI, sans-serif",
}


def _style(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0.02, font=dict(size=18, color=PHONEPE["primary"])),
        font=dict(family=PHONEPE["font"], size=13),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=40, r=20, t=55, b=40),
        colorway=PHONEPE["sequence"], hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#eee")
    return fig


def bar_top_states(df: pd.DataFrame, metric: str = "txn_amount", n: int = 10) -> go.Figure:
    """Horizontal bar chart of the top-N states by a metric."""
    d = df.nlargest(n, metric).sort_values(metric)
    fig = px.bar(d, x=metric, y="state", orientation="h",
                 color=metric, color_continuous_scale="Purples")
    fig.update_layout(coloraxis_showscale=False)
    return _style(fig, f"Top {n} States by {metric.replace('_', ' ').title()}")


def line_national_trend(df: pd.DataFrame) -> go.Figure:
    """Value trend line with a 4-quarter moving average overlay."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["period"], y=df["txn_amount"], mode="lines+markers",
                             name="Value", line=dict(color=PHONEPE["primary"], width=3)))
    if "ma_4q" in df:
        fig.add_trace(go.Scatter(x=df["period"], y=df["ma_4q"], mode="lines",
                                 name="4Q Moving Avg",
                                 line=dict(color=PHONEPE["accent"], dash="dash")))
    return _style(fig, "National Transaction Value Trend")


def area_category_trend(df: pd.DataFrame) -> go.Figure:
    """Stacked-area chart of category value over years."""
    fig = px.area(df, x="year", y="txn_amount", color="category")
    return _style(fig, "Category Value Mix Over Time")


def pie_category(df: pd.DataFrame) -> go.Figure:
    """Donut of category value share (appropriate: few, mutually exclusive parts)."""
    fig = px.pie(df, names="category", values="txn_amount", hole=0.45)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _style(fig, "Transaction Value by Category")


def treemap_states(df: pd.DataFrame) -> go.Figure:
    """Treemap of value by region -> state."""
    fig = px.treemap(df, path=[px.Constant("India"), "region", "state"],
                     values="txn_amount", color="txn_amount",
                     color_continuous_scale="Purples")
    return _style(fig, "Value Contribution: Region and State")


def bar_top_districts(df: pd.DataFrame, n: int = 15) -> go.Figure:
    d = df.nlargest(n, "txn_amount").sort_values("txn_amount")
    fig = px.bar(d, x="txn_amount", y="district", orientation="h",
                 color="txn_amount", color_continuous_scale="Purples")
    fig.update_layout(coloraxis_showscale=False)
    return _style(fig, f"Top {n} Districts by Value")


def bar_device_share(df: pd.DataFrame) -> go.Figure:
    fig = px.bar(df, x="brand", y="users", color="brand")
    fig.update_layout(showlegend=False)
    return _style(fig, "User Base by Device Brand")


def choropleth_states(df: pd.DataFrame, geojson: dict,
                      metric: str = "txn_amount") -> go.Figure:
    """India choropleth. ``geojson`` is a states GeoJSON with a 'ST_NM' key.

    The dashboard passes a GeoJSON loaded at runtime; this builder keeps the
    map logic in one place. Falls back gracefully if geojson is None.
    """
    if geojson is None:
        return bar_top_states(df, metric, n=15)
    fig = px.choropleth(
        df, geojson=geojson, featureidkey="properties.ST_NM",
        locations="state", color=metric, color_continuous_scale="Purples")
    fig.update_geos(fitbounds="locations", visible=False)
    return _style(fig, f"India: {metric.replace('_', ' ').title()} by State")
