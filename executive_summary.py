"""
Executive Summary
==================
Single-page, all-verticals overview for leadership.

Every metric on this page is Financial-Year-to-date (April 1 through today)
vs the same FY-to-date window one year earlier — one consistent basis for
every number, not a mix of MTD and FY. Nothing here is user-selectable
(unlike the per-vertical detail page), so every vertical is judged the
same way.

Adding a new vertical: write a loader function (fetches data) and a
renderer function (draws it, assuming it's already inside the vertical's
container) — see the Website and Online E-commerce pairs below for the
pattern — then register both in VERTICAL_RENDERERS and add the vertical to
VERTICALS in config.py.
"""

from datetime import date

import streamlit as st

from config import VERTICALS, CURRENCY_SYMBOL, ONLINE_ECOMMERCE_CHANNEL_MAP, \
    ONLINE_ECOMMERCE_EFFICIENCY_METRIC
from utils.bigquery_client import run_query
from utils.queries import (
    orders_summary_sql, targets_sql, retention_sql, ga4_traffic_sql,
    channel_sales_revenue_sql,
)
from utils.kpi_calculations import (
    summarize_orders, targets_summary, retention_rate,
    pct_change, cac, roas, tacos, conversion_rate, summarize_ga4,
    summarize_channel_sales,
)
from utils.ui_components import format_kpi_value, headline_achievement, compact_kpi_table
from utils.ad_spend import load_daily_ad_spend, total_spend
from utils.date_utils import same_period_last_year, fy_mtd_window, fy_label

with st.sidebar:
    st.image("assets/logo.png", width=110)

st.title("Executive Summary")

today = date.today()
fy_start_d, fy_end_d = fy_mtd_window(today)
fy_ly_start, fy_ly_end = same_period_last_year(fy_start_d, fy_end_d)
this_fy_label = fy_label(today)

st.caption(
    f"{this_fy_label} to date: {fy_start_d.strftime('%d %b %Y')} – {fy_end_d.strftime('%d %b %Y')}  |  "
    f"vs same period last year: {fy_ly_start.strftime('%d %b %Y')} – {fy_ly_end.strftime('%d %b %Y')}"
)
st.caption(
    "💡 Revenue, AOV, and related figures below are currently calculated on "
    "**MRP (list price)**, not net/discounted revenue — see `config.py: "
    "REVENUE_COLUMN`."
)


# =============================================================================
# Website
# =============================================================================
def load_website_summary() -> dict:
    """
    Pulls everything needed for the Website vertical's block: FY-to-date vs
    FY-to-date-last-year for every headline metric. Mirrors app.py's
    data-fetch logic but with fixed date windows instead of sidebar-driven
    ones, and no manual-override inputs (this page is read-only — if a
    source fails, that vertical's block shows an error instead of falling
    back to a manual entry).
    """
    return {
        "orders": run_query(*orders_summary_sql(fy_start_d, fy_end_d)),
        "orders_ly": run_query(*orders_summary_sql(fy_ly_start, fy_ly_end)),
        "targets": run_query(*targets_sql(fy_start_d, fy_end_d)),
        "ret": run_query(*retention_sql(fy_start_d, fy_end_d)),
        "ret_ly": run_query(*retention_sql(fy_ly_start, fy_ly_end)),
        "ga4": run_query(*ga4_traffic_sql(fy_start_d, fy_end_d)),
        "ga4_ly": run_query(*ga4_traffic_sql(fy_ly_start, fy_ly_end)),
        "spend": load_daily_ad_spend(fy_start_d, fy_end_d),
        "spend_ly": load_daily_ad_spend(fy_ly_start, fy_ly_end),
    }


def render_website(data: dict) -> None:
    # -------------------------------------------------------------
    # Crisp headline: FY-to-date revenue, achieved vs target
    # -------------------------------------------------------------
    tgt = targets_summary(data["targets"])
    headline_achievement(
        f"{this_fy_label} Revenue — Achieved vs Target (to date)",
        format_kpi_value(tgt["actual_revenue"], prefix=CURRENCY_SYMBOL, compact=True),
        format_kpi_value(tgt["target_revenue"], prefix=CURRENCY_SYMBOL, compact=True),
        tgt["achievement_pct"],
    )
    st.markdown("<hr style='border:none;border-top:1px solid #EEF0F2;margin:4px 0 12px 0;'>",
                unsafe_allow_html=True)

    # -------------------------------------------------------------
    # Everything else: one crisp table, one row per metric — all
    # FY-to-date vs the same FY-to-date window last year
    # -------------------------------------------------------------
    cur = summarize_orders(data["orders"])
    prev = summarize_orders(data["orders_ly"])
    ret_pct = retention_rate(data["ret"])
    ret_pct_ly = retention_rate(data["ret_ly"])
    ga4_cur = summarize_ga4(data["ga4"])
    ga4_ly = summarize_ga4(data["ga4_ly"])
    ad_spend_cur = total_spend(data["spend"])
    ad_spend_ly = total_spend(data["spend_ly"])

    conv_pct = conversion_rate(cur["orders"], ga4_cur["sessions"]) if ga4_cur["sessions"] else None
    conv_pct_ly = conversion_rate(prev["orders"], ga4_ly["sessions"]) if ga4_ly["sessions"] else None
    cac_val = cac(ad_spend_cur, cur["new_customers"]) if ad_spend_cur else None
    cac_val_ly = cac(ad_spend_ly, prev["new_customers"]) if ad_spend_ly else None
    roas_val = roas(cur["net_revenue"], ad_spend_cur) if ad_spend_cur else None
    roas_val_ly = roas(prev["net_revenue"], ad_spend_ly) if ad_spend_ly else None
    tacos_val = tacos(ad_spend_cur, cur["net_revenue"]) if ad_spend_cur else None
    tacos_val_ly = tacos(ad_spend_ly, prev["net_revenue"]) if ad_spend_ly else None

    growth = pct_change(cur["net_revenue"], prev["net_revenue"])
    rows = [
        {"label": "Growth % (FY YTD vs LY)",
         "value": format_kpi_value(growth, suffix="%", decimals=1),
         "delta": None},
        {"label": "Traffic (Sessions)",
         "value": format_kpi_value(ga4_cur["sessions"] or None),
         "delta": pct_change(ga4_cur["sessions"], ga4_ly["sessions"]) if ga4_ly["sessions"] else None},
        {"label": "Conversion %",
         "value": format_kpi_value(conv_pct, suffix="%", decimals=2),
         "delta": pct_change(conv_pct, conv_pct_ly) if conv_pct and conv_pct_ly else None},
        {"label": "AOV",
         "value": format_kpi_value(cur["aov"], prefix=CURRENCY_SYMBOL, decimals=0),
         "delta": pct_change(cur["aov"], prev["aov"])},
        {"label": "New Customers",
         "value": format_kpi_value(cur["new_customers"]),
         "delta": pct_change(cur["new_customers"], prev["new_customers"])},
        {"label": "Retention %",
         "value": format_kpi_value(ret_pct, suffix="%", decimals=1),
         "delta": pct_change(ret_pct, ret_pct_ly)},
        {"label": "CAC",
         "value": format_kpi_value(cac_val, prefix=CURRENCY_SYMBOL, decimals=0),
         "delta": pct_change(cac_val, cac_val_ly) if cac_val and cac_val_ly else None,
         "delta_is_good_when_positive": False},
        {"label": "ROAS",
         "value": format_kpi_value(roas_val, suffix="x", decimals=2),
         "delta": pct_change(roas_val, roas_val_ly) if roas_val and roas_val_ly else None},
        {"label": "Overall TACOS",
         "value": format_kpi_value(tacos_val, suffix="%", decimals=2),
         "delta": pct_change(tacos_val, tacos_val_ly) if tacos_val and tacos_val_ly else None,
         "delta_is_good_when_positive": False},
        {"label": "ASP / Discount % / UTP",
         "value": "Not wired up yet",
         "delta": None},
    ]
    compact_kpi_table(rows, value_col_label=f"{this_fy_label} YTD", delta_col_label="vs LY")


# =============================================================================
# Online E-commerce
# =============================================================================
def load_online_ecommerce_summary() -> dict:
    """
    Pulls FY-to-date vs FY-to-date-last-year Secondary Sales revenue for
    each Online E-commerce sub-vertical that has channels mapped in
    config.ONLINE_ECOMMERCE_CHANNEL_MAP. Sub-verticals with no channels
    mapped yet (Beauty Commerce, International E-Commerce) simply won't
    have a key in the returned dict — the renderer shows those as
    "coming soon" rather than erroring.
    """
    data = {}
    for sub_vertical, channels in ONLINE_ECOMMERCE_CHANNEL_MAP.items():
        cur_query = channel_sales_revenue_sql(fy_start_d, fy_end_d, channels)
        ly_query = channel_sales_revenue_sql(fy_ly_start, fy_ly_end, channels)
        if cur_query is None or ly_query is None:
            continue
        data[sub_vertical] = {
            "cur": run_query(*cur_query),
            "ly": run_query(*ly_query),
        }
    return data


def render_online_ecommerce(data: dict) -> None:
    # Every sub-vertical from the KPI sheet, in order — whether or not it
    # has channels mapped yet, so the missing ones are visibly "coming
    # soon" rather than silently absent.
    all_sub_verticals = list(ONLINE_ECOMMERCE_EFFICIENCY_METRIC.keys())

    for sub in all_sub_verticals:
        st.markdown(
            f"<div style='font-weight:600;color:#374151;margin:16px 0 6px 0;'>{sub}</div>",
            unsafe_allow_html=True,
        )
        if sub not in data:
            st.caption("Coming soon — no channels mapped to this sub-vertical yet.")
            continue

        cur = summarize_channel_sales(data[sub]["cur"])
        ly = summarize_channel_sales(data[sub]["ly"])
        growth = pct_change(cur["revenue"], ly["revenue"])
        efficiency_label = ONLINE_ECOMMERCE_EFFICIENCY_METRIC.get(sub, "Efficiency")

        rows = [
            {"label": "Revenue (Secondary Sales)",
             "value": format_kpi_value(cur["revenue"], prefix=CURRENCY_SYMBOL, compact=True),
             "delta": None},
            {"label": "Growth %",
             "value": format_kpi_value(growth, suffix="%", decimals=1),
             "delta": None},
            {"label": "Discounting %", "value": "Not wired up yet", "delta": None},
            {"label": efficiency_label, "value": "Not wired up yet", "delta": None},
        ]
        compact_kpi_table(rows, value_col_label=f"{this_fy_label} YTD", delta_col_label="vs LY")

    st.markdown(
        "<div style='font-weight:600;color:#374151;margin:16px 0 6px 0;'>"
        "Gifting vs Non-Gifting Split (vertical-wide)</div>",
        unsafe_allow_html=True,
    )
    st.caption("Not wired up yet.")


# =============================================================================
# Registry + generic render loop
# =============================================================================
# Each entry: (loader, renderer). loader() fetches data; renderer(data)
# draws it, assuming it's already inside the vertical's bordered container.
# Verticals in config.VERTICALS with no entry here render as "coming soon"
# automatically.
VERTICAL_RENDERERS = {
    "Website": (load_website_summary, render_website),
    "Online E-commerce": (load_online_ecommerce_summary, render_online_ecommerce),
}


def render_vertical_block(vertical_name: str, meta: dict) -> None:
    icon = meta.get("icon", "")

    with st.container(border=True):
        st.markdown(
            f"<div style='font-size:1.3rem;font-weight:700;color:#111827;margin-bottom:10px;'>"
            f"{icon} &nbsp;{vertical_name}</div>",
            unsafe_allow_html=True,
        )

        if meta.get("status") != "live" or vertical_name not in VERTICAL_RENDERERS:
            st.info(f"{vertical_name} isn't wired up on this page yet — coming soon.")
            return

        loader, renderer = VERTICAL_RENDERERS[vertical_name]
        try:
            data = loader()
        except Exception as e:
            st.error(f"Couldn't load {vertical_name} data: {e}")
            return

        renderer(data)


for name, meta in VERTICALS.items():
    render_vertical_block(name, meta)
    st.write("")  # a little breathing room between vertical cards
