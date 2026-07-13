"""
Executive Summary
==================
Single-page, all-verticals overview for leadership.

Unlike the per-vertical detail page (app.py), nothing here is user-selectable:
every metric is MTD (month-to-date) vs the same calendar days one year
earlier — a fixed comparison so every vertical is judged on the same basis.
Each vertical also gets a headline "FY-to-date target achievement" card,
covering April 1 (start of FY) through today.

Adding a new vertical: write a loader function the same shape as
load_website_summary() below, register it in VERTICAL_LOADERS, and add the
vertical to VERTICALS in config.py. Everything else (layout, FY math,
delta formatting) is shared automatically.
"""

from datetime import date

import streamlit as st

from config import VERTICALS, CURRENCY_SYMBOL
from utils.bigquery_client import run_query
from utils.queries import orders_summary_sql, targets_sql, retention_sql, ga4_traffic_sql
from utils.kpi_calculations import (
    summarize_orders, targets_summary, retention_rate,
    pct_change, cac, roas, tacos, conversion_rate, summarize_ga4,
)
from utils.ui_components import format_kpi_value, headline_achievement, compact_kpi_table
from utils.ad_spend import load_daily_ad_spend, total_spend
from utils.date_utils import mtd_window, same_period_last_year, fy_mtd_window, fy_label

with st.sidebar:
    st.image("assets/logo.png", width=110)

st.title("Executive Summary")

today = date.today()
mtd_start, mtd_end = mtd_window(today)
ly_start, ly_end = same_period_last_year(mtd_start, mtd_end)
fy_start_d, fy_end_d = fy_mtd_window(today)
this_fy_label = fy_label(today)

st.caption(
    f"MTD: {mtd_start.strftime('%d %b %Y')} – {mtd_end.strftime('%d %b %Y')}  |  "
    f"vs same period last year: {ly_start.strftime('%d %b %Y')} – {ly_end.strftime('%d %b %Y')}  |  "
    f"{this_fy_label} to date: {fy_start_d.strftime('%d %b %Y')} – {fy_end_d.strftime('%d %b %Y')}"
)


def load_website_summary() -> dict:
    """
    Pulls everything needed for the Website vertical's block: MTD vs
    MTD-last-year for the headline KPIs, plus FY-to-date targets.
    Mirrors app.py's data-fetch logic but with fixed date windows instead
    of sidebar-driven ones, and no manual-override inputs (this page is
    read-only — if a source fails, that vertical's block shows an error
    instead of falling back to a manual entry).
    """
    return {
        "orders": run_query(*orders_summary_sql(mtd_start, mtd_end)),
        "orders_ly": run_query(*orders_summary_sql(ly_start, ly_end)),
        "targets": run_query(*targets_sql(mtd_start, mtd_end)),
        "targets_ly": run_query(*targets_sql(ly_start, ly_end)),
        "ret": run_query(*retention_sql(mtd_start, mtd_end)),
        "ret_ly": run_query(*retention_sql(ly_start, ly_end)),
        "ga4": run_query(*ga4_traffic_sql(mtd_start, mtd_end)),
        "ga4_ly": run_query(*ga4_traffic_sql(ly_start, ly_end)),
        "spend": load_daily_ad_spend(mtd_start, mtd_end),
        "spend_ly": load_daily_ad_spend(ly_start, ly_end),
        "fy_targets": run_query(*targets_sql(fy_start_d, fy_end_d)),
    }


# Register one loader per live vertical. Verticals in config.VERTICALS with
# no entry here render as "coming soon" automatically.
VERTICAL_LOADERS = {
    "Website": load_website_summary,
}


def render_vertical_block(vertical_name: str, meta: dict) -> None:
    icon = meta.get("icon", "")
    st.divider()
    st.header(f"{icon} {vertical_name}")

    if meta.get("status") != "live" or vertical_name not in VERTICAL_LOADERS:
        st.info(f"{vertical_name} isn't wired up on this page yet — coming soon.")
        return

    try:
        data = VERTICAL_LOADERS[vertical_name]()
    except Exception as e:
        st.error(f"Couldn't load {vertical_name} data: {e}")
        return

    # -----------------------------------------------------------------
    # Crisp headline: FY-to-date and MTD actual-vs-target, one line each
    # -----------------------------------------------------------------
    fy_tgt = targets_summary(data["fy_targets"])
    headline_achievement(
        f"{this_fy_label} Revenue — Achieved vs Target (to date)",
        format_kpi_value(fy_tgt["actual_revenue"], prefix=CURRENCY_SYMBOL, compact=True),
        format_kpi_value(fy_tgt["target_revenue"], prefix=CURRENCY_SYMBOL, compact=True),
        fy_tgt["achievement_pct"],
    )

    cur = summarize_orders(data["orders"])
    prev = summarize_orders(data["orders_ly"])
    tgt = targets_summary(data["targets"])
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

    headline_achievement(
        "MTD Revenue — Achieved vs Target",
        format_kpi_value(tgt["actual_revenue"], prefix=CURRENCY_SYMBOL, compact=True),
        format_kpi_value(tgt["target_revenue"], prefix=CURRENCY_SYMBOL, compact=True),
        tgt["achievement_pct"],
    )

    # -----------------------------------------------------------------
    # Everything else: one crisp table, one row per metric, all vs LY
    # -----------------------------------------------------------------
    growth = pct_change(cur["net_revenue"], prev["net_revenue"])
    rows = [
        {"label": "Growth % (YoY)",
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
    compact_kpi_table(rows)


for name, meta in VERTICALS.items():
    render_vertical_block(name, meta)
