"""
Kimirica Leadership KPI Dashboard
==================================
Founder-facing view of vertical-wise KPIs. Currently live: Website.
Run locally:  streamlit run app.py
"""

from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import VERTICALS, CURRENCY_SYMBOL
from utils.bigquery_client import run_query
from utils.queries import orders_summary_sql, targets_sql, retention_sql, ga4_traffic_sql
from utils.kpi_calculations import (
    summarize_orders, targets_summary, retention_rate,
    pct_change, cac, roas, tacos, conversion_rate, summarize_ga4,
)
from utils.ui_components import kpi_card, section_header, placeholder_note
from utils.ad_spend import load_daily_ad_spend, total_spend

st.set_page_config(
    page_title="Kimirica | Leadership Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Light styling
# NOTE: card background is deliberately light regardless of the viewer's
# Streamlit theme (light/dark), so every text color inside the card is
# force-set here too — otherwise dark-theme users get near-invisible white
# text on a light card. font-size + overflow-wrap on the value keep long
# numbers (e.g. full-rupee revenue figures) from being clipped/truncated.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #F8F9FB;
        border: 1px solid #E6E8EC;
        border-radius: 12px;
        padding: 14px 16px 10px 16px;
    }
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] * {
        font-weight: 600;
        opacity: 0.75;
        color: #1F2937 !important;
    }
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] * {
        color: #111827 !important;
        font-size: 1.6rem !important;
        white-space: normal !important;
        overflow-wrap: anywhere;
        line-height: 1.2 !important;
    }
    div[data-testid="stMetricDelta"],
    div[data-testid="stMetricDelta"] * {
        font-size: 0.85rem !important;
    }
    .block-container { padding-top: 1.8rem; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — vertical, date range, manual inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style='font-size:1.5rem; font-weight:700; letter-spacing:0.14em;
                    color:#111827; margin-bottom:0;'>
            KIMIRICA
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Leadership KPI Dashboard")

    vertical = st.selectbox("Vertical", options=list(VERTICALS.keys()), index=0)

    st.divider()
    st.subheader("Date range")

    preset = st.radio(
        "Quick select",
        ["MTD", "Last 7 days", "Last 30 days", "QTD", "YTD", "Custom"],
        index=0,
    )

    today = date.today()
    if preset == "MTD":
        start_date, end_date = today.replace(day=1), today
    elif preset == "Last 7 days":
        start_date, end_date = today - timedelta(days=7), today
    elif preset == "Last 30 days":
        start_date, end_date = today - timedelta(days=30), today
    elif preset == "QTD":
        q_start_month = 3 * ((today.month - 1) // 3) + 1
        start_date, end_date = today.replace(month=q_start_month, day=1), today
    elif preset == "YTD":
        start_date, end_date = today.replace(month=1, day=1), today
    else:
        c1, c2 = st.columns(2)
        start_date = c1.date_input("Start", today - timedelta(days=30))
        end_date = c2.date_input("End", today)

    st.divider()
    st.subheader("Compare to")

    compare_mode = st.radio(
        "Comparison period",
        ["Previous period (same length)", "Same period last year", "Custom range"],
        index=0,
    )

    period_len = (end_date - start_date).days + 1
    if compare_mode == "Previous period (same length)":
        prev_start = start_date - timedelta(days=period_len)
        prev_end = start_date - timedelta(days=1)
    elif compare_mode == "Same period last year":
        try:
            prev_start = start_date.replace(year=start_date.year - 1)
            prev_end = end_date.replace(year=end_date.year - 1)
        except ValueError:
            # Feb 29 with no matching date the year before — fall back to
            # a straight 365-day offset instead of crashing.
            prev_start = start_date - timedelta(days=365)
            prev_end = end_date - timedelta(days=365)
    else:
        cc1, cc2 = st.columns(2)
        prev_start = cc1.date_input(
            "Compare start", start_date - timedelta(days=period_len), key="compare_start")
        prev_end = cc2.date_input(
            "Compare end", start_date - timedelta(days=1), key="compare_end")

    st.caption(f"Comparing to: {prev_start} → {prev_end}")

    st.divider()
    st.subheader("⚙️ Manual overrides")
    st.caption("Use these only if a live source is temporarily unavailable.")

    use_manual_traffic = st.checkbox("Override traffic manually", value=False)
    if use_manual_traffic:
        sessions_current = st.number_input(
            "Website sessions (current period)", min_value=0, value=0, step=1000)
        sessions_prev = st.number_input(
            "Website sessions (comparison period)", min_value=0, value=0, step=1000)

    use_manual_spend = st.checkbox(
        "Override ad spend manually",
        value=False,
    )
    if use_manual_spend:
        ad_spend_current = st.number_input(
            f"Ad spend {CURRENCY_SYMBOL} (current period)", min_value=0.0, value=0.0, step=1000.0)
        ad_spend_prev = st.number_input(
            f"Ad spend {CURRENCY_SYMBOL} (comparison period)", min_value=0.0, value=0.0, step=1000.0)


# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------
def load_period(start_d, end_d):
    orders_df = run_query(*orders_summary_sql(start_d, end_d))
    targets_df = run_query(*targets_sql(start_d, end_d))
    retention_df = run_query(*retention_sql(start_d, end_d))
    return orders_df, targets_df, retention_df


try:
    orders_df, targets_df, ret_df = load_period(start_date, end_date)
    orders_prev_df, targets_prev_df, ret_prev_df = load_period(prev_start, prev_end)
    data_error = None
except Exception as e:
    data_error = str(e)
    orders_df = targets_df = ret_df = pd.DataFrame()
    orders_prev_df = targets_prev_df = ret_prev_df = pd.DataFrame()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title(f"{VERTICALS[vertical]['icon']} {vertical} — Leadership KPIs")
st.caption(f"{start_date.strftime('%d %b %Y')} – {end_date.strftime('%d %b %Y')}")

if data_error:
    st.error(
        "Couldn't load data from BigQuery. Check that your service-account "
        "credentials are set in Streamlit secrets and have access to the "
        f"required tables.\n\nDetails: {data_error}"
    )
    st.stop()

# ---------------------------------------------------------------------------
# Ad spend (live from Google Sheet, unless manually overridden in sidebar)
# ---------------------------------------------------------------------------
spend_source_label = "MANUAL ENTRY"
if not use_manual_spend:
    try:
        spend_df = load_daily_ad_spend(start_date, end_date)
        spend_prev_df = load_daily_ad_spend(prev_start, prev_end)
        ad_spend_current = total_spend(spend_df)
        ad_spend_prev = total_spend(spend_prev_df)
        spend_source_label = "LIVE (Sheet)"
    except Exception as e:
        st.sidebar.warning(
            f"Couldn't load the ad spend sheet ({e}). Falling back to ₹0 — "
            "tick 'Override ad spend manually' to enter it by hand, or check "
            "that the sheet is shared with the service account email."
        )
        ad_spend_current, ad_spend_prev = 0.0, 0.0

# ---------------------------------------------------------------------------
# Traffic (live from GA4Dashboard, unless manually overridden in sidebar)
# ---------------------------------------------------------------------------
traffic_source_label = "MANUAL ENTRY"
ga4_df, ga4_cur = pd.DataFrame(), summarize_ga4(pd.DataFrame())
if not use_manual_traffic:
    try:
        ga4_df = run_query(*ga4_traffic_sql(start_date, end_date))
        ga4_prev_df = run_query(*ga4_traffic_sql(prev_start, prev_end))
        ga4_cur = summarize_ga4(ga4_df)
        ga4_prev = summarize_ga4(ga4_prev_df)
        sessions_current = ga4_cur["sessions"]
        sessions_prev = ga4_prev["sessions"]
        traffic_source_label = "LIVE (GA4)"
    except Exception as e:
        st.sidebar.warning(
            f"Couldn't load GA4 traffic ({e}). Falling back to 0 sessions — "
            "tick 'Override traffic manually' to enter it by hand."
        )
        sessions_current, sessions_prev = 0, 0

# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------
cur = summarize_orders(orders_df)
prev = summarize_orders(orders_prev_df)
tgt = targets_summary(targets_df)
ret_pct = retention_rate(ret_df)
ret_pct_prev = retention_rate(ret_prev_df)

conv_pct = conversion_rate(cur["orders"], sessions_current) if sessions_current else None
conv_pct_prev = conversion_rate(prev["orders"], sessions_prev) if sessions_prev else None

cac_val = cac(ad_spend_current, cur["new_customers"]) if ad_spend_current else None
cac_val_prev = cac(ad_spend_prev, prev["new_customers"]) if ad_spend_prev else None

roas_val = roas(cur["net_revenue"], ad_spend_current) if ad_spend_current else None
roas_val_prev = roas(prev["net_revenue"], ad_spend_prev) if ad_spend_prev else None

tacos_val = tacos(ad_spend_current, cur["net_revenue"]) if ad_spend_current else None
tacos_val_prev = tacos(ad_spend_prev, prev["net_revenue"]) if ad_spend_prev else None

# ---------------------------------------------------------------------------
# Row 1: Revenue / Target / Growth
# ---------------------------------------------------------------------------
section_header("Revenue & Growth")
r1c1, r1c2, r1c3, r1c4 = st.columns(4)
with r1c1:
    kpi_card("Revenue (Actual)", tgt["actual_revenue"], prefix=CURRENCY_SYMBOL, compact=True,
             delta=pct_change(tgt["actual_revenue"], targets_prev_df["revenue"].sum() if not targets_prev_df.empty else 0))
with r1c2:
    kpi_card("Revenue Target", tgt["target_revenue"], prefix=CURRENCY_SYMBOL, compact=True)
with r1c3:
    achievement = tgt["achievement_pct"]
    st.metric("Target Achievement %", f"{achievement:.1f}%")
    st.progress(min(achievement / 100, 1.0) if achievement else 0)
with r1c4:
    growth = pct_change(cur["net_revenue"], prev["net_revenue"])
    kpi_card("Growth % (vs prev. period)", growth, suffix="%", decimals=1)

# ---------------------------------------------------------------------------
# Row 2: Traffic / Conversion / AOV / New Customers
# ---------------------------------------------------------------------------
section_header("Acquisition & Conversion")
r2c1, r2c2, r2c3, r2c4 = st.columns(4)
with r2c1:
    placeholder_note(traffic_source_label, color="#D3F9D8" if traffic_source_label.startswith("LIVE") else "#FFF3CD",
                      text_color="#2B8A3E" if traffic_source_label.startswith("LIVE") else "#856404")
    kpi_card("Traffic (Sessions)", sessions_current or None,
             delta=pct_change(sessions_current, sessions_prev) if sessions_prev else None)
with r2c2:
    placeholder_note(traffic_source_label, color="#D3F9D8" if traffic_source_label.startswith("LIVE") else "#FFF3CD",
                      text_color="#2B8A3E" if traffic_source_label.startswith("LIVE") else "#856404")
    kpi_card("Conversion %", conv_pct, suffix="%", decimals=2,
             delta=pct_change(conv_pct, conv_pct_prev) if conv_pct and conv_pct_prev else None)
with r2c3:
    kpi_card("AOV", cur["aov"], prefix=CURRENCY_SYMBOL, decimals=0,
             delta=pct_change(cur["aov"], prev["aov"]))
with r2c4:
    kpi_card("New Customers", cur["new_customers"],
             delta=pct_change(cur["new_customers"], prev["new_customers"]))

# ---------------------------------------------------------------------------
# Row 3: Retention / CAC / ROAS / TACOS
# ---------------------------------------------------------------------------
section_header("Retention & Efficiency")
r3c1, r3c2, r3c3, r3c4 = st.columns(4)
with r3c1:
    kpi_card("Retention %", ret_pct, suffix="%", decimals=1,
             delta=pct_change(ret_pct, ret_pct_prev))
with r3c2:
    placeholder_note(spend_source_label, color="#D3F9D8" if spend_source_label.startswith("LIVE") else "#FFF3CD",
                      text_color="#2B8A3E" if spend_source_label.startswith("LIVE") else "#856404")
    kpi_card("CAC", cac_val, prefix=CURRENCY_SYMBOL, decimals=0,
             delta=pct_change(cac_val, cac_val_prev) if cac_val and cac_val_prev else None,
             delta_is_good_when_positive=False)
with r3c3:
    placeholder_note(spend_source_label, color="#D3F9D8" if spend_source_label.startswith("LIVE") else "#FFF3CD",
                      text_color="#2B8A3E" if spend_source_label.startswith("LIVE") else "#856404")
    kpi_card("ROAS", roas_val, suffix="x", decimals=2,
             delta=pct_change(roas_val, roas_val_prev) if roas_val and roas_val_prev else None)
with r3c4:
    placeholder_note(spend_source_label, color="#D3F9D8" if spend_source_label.startswith("LIVE") else "#FFF3CD",
                      text_color="#2B8A3E" if spend_source_label.startswith("LIVE") else "#856404")
    kpi_card("Overall TACOS", tacos_val, suffix="%", decimals=2,
             delta=pct_change(tacos_val, tacos_val_prev) if tacos_val and tacos_val_prev else None,
             delta_is_good_when_positive=False)

st.divider()

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
section_header("Revenue vs Target — Daily Trend")
if not targets_df.empty:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=targets_df["sales_date"], y=targets_df["revenue"],
                          name="Actual Revenue", marker_color="#4C6EF5"))
    fig.add_trace(go.Scatter(x=targets_df["sales_date"], y=targets_df["daily_target"],
                              name="Daily Target", mode="lines+markers",
                              line=dict(color="#FA5252", dash="dash")))
    fig.update_layout(height=380, hovermode="x unified",
                       legend=dict(orientation="h", y=1.1),
                       margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No target data available for this period.")

c1, c2 = st.columns(2)
with c1:
    section_header("New vs Returning Customers")
    if not orders_df.empty:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=orders_df["order_date"], y=orders_df["new_customers"],
                               name="New", marker_color="#4C6EF5"))
        fig2.add_trace(go.Bar(x=orders_df["order_date"], y=orders_df["returning_customers"],
                               name="Returning", marker_color="#82C91E"))
        fig2.update_layout(barmode="stack", height=340,
                            margin=dict(l=10, r=10, t=10, b=10),
                            legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No order data for this period.")

with c2:
    section_header("Daily Net Revenue")
    if not orders_df.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=orders_df["order_date"], y=orders_df["net_revenue"],
                                   fill="tozeroy", mode="lines",
                                   line=dict(color="#4C6EF5")))
        fig3.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No order data for this period.")

if traffic_source_label.startswith("LIVE") and ga4_cur["sessions"]:
    section_header("Website Funnel", "Sessions → Viewed Item → Added to Cart → Checkout → Purchased")
    funnel_stages = ["Sessions", "Viewed Item", "Added to Cart", "Checkout", "Purchased"]
    funnel_values = [
        ga4_cur["sessions"], ga4_cur["sessions_viewed_item"],
        ga4_cur["sessions_added_to_cart"], ga4_cur["sessions_checkout"],
        ga4_cur["sessions_purchased"],
    ]
    fig4 = go.Figure(go.Funnel(
        y=funnel_stages, x=funnel_values,
        marker=dict(color=["#4C6EF5", "#5C7CFA", "#748FFC", "#91A7FF", "#82C91E"]),
        textinfo="value+percent initial",
    ))
    fig4.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig4, use_container_width=True)

st.caption(
    "Revenue, AOV, New Customers, Retention, CAC, ROAS, TACOS and Traffic are "
    "pulled live from BigQuery/Sheets/GA4 (badges on each card show the exact "
    "source). Anything marked MANUAL ENTRY is a sidebar override currently "
    "switched on in place of its live source."
)
