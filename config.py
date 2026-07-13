"""
Central configuration for the Leadership KPI Dashboard.
Edit values here as the business confirms exact filter values -
no need to touch query logic elsewhere.
"""

# ---------------------------------------------------------------------------
# BigQuery project / dataset / table references
# ---------------------------------------------------------------------------
BQ_PROJECT = "aerobic-copilot-494105-b6"

ORDERS_TABLE = f"{BQ_PROJECT}.shopify_kimirica.master_orders_flat"
# Day-level, channel-wise sales targets. Schema: sales_date, channel, revenue,
# daily_target, last_updated. (Switched from Sales_Vs_Targets, which was
# returning no rows for recent periods.)
TARGETS_TABLE = f"{BQ_PROJECT}.Datachannel.Overall_Sales"

# TODO: fill in once shared
GA4_TABLE = f"{BQ_PROJECT}.analytics_288570553.GA4Dashboard"

# Ad spend (Meta + Google) - lives in a manually maintained Google Sheet,
# not BigQuery. "Daily Data" tab.
AD_SPEND_SHEET_ID = "1or00eLSossBJebrkbrVSELfVxzcpOvdnjpmZV8mqW_c"
AD_SPEND_SHEET_GID = "1763473104"  # tab gid for "Daily Data"

# Online E-commerce vertical: Secondary Sales by channel. Primary Sales will
# live in a separate table once it exists — Revenue for this vertical is
# Secondary-only until then (see ONLINE_ECOMMERCE_CHANNEL_MAP below).
CHANNEL_SALES_TABLE = f"{BQ_PROJECT}.Datachannel.Channel_Sales_Combined"

# ---------------------------------------------------------------------------
# Channel identification
# CONFIRMED via:
#   SELECT DISTINCT order_channel, source_name, COUNT(*) c
#   FROM `...master_orders_flat` GROUP BY 1,2 ORDER BY c DESC
# Result: order_channel = 'Website' cleanly captures all website orders
# (incl. Shopflo checkout, draft orders, web). 'Store' = in-store POS.
# source_name is NOT reliable as a filter (messy: checkout app names,
# numeric IDs, etc.) - order_channel alone is sufficient.
# ---------------------------------------------------------------------------
WEBSITE_ORDER_CHANNEL_VALUES = ["Website"]   # order_channel values that mean "Website"

# Name used to match against the `channel` column in Overall_Sales.
WEBSITE_TARGET_CHANNEL_NAME = "Website"

# ---------------------------------------------------------------------------
# Online E-commerce: sub-vertical -> channel values in
# Channel_Sales_Combined.channel. Every non-Website, non-EBO channel in that
# table is already assigned between Quick Commerce and Marketplaces — Beauty
# Commerce and International E-Commerce have no channels here yet:
#   - International: will be added into this same table later.
#   - Beauty Commerce: data source not yet confirmed.
# Both render as "coming soon" on the dashboard until a channel list exists.
# ---------------------------------------------------------------------------
ONLINE_ECOMMERCE_CHANNEL_MAP = {
    "Quick Commerce": ["Zepto", "Swiggy", "Blinkit"],
    "Marketplaces": ["Amazon-SC", "Amazon-VC", "Nykaa", "Myntra", "Tira", "Flipkart"],
    # "Beauty Commerce": [...],           # TODO: confirm data source
    # "International E-Commerce": [...],  # TODO: will live in this same table later
}

# Each Online E-commerce sub-vertical tracks a different "Efficiency" metric
# per the original KPI sheet — this is just the label shown until each is
# actually wired up to a data source (ad spend, sessions, logistics cost).
ONLINE_ECOMMERCE_EFFICIENCY_METRIC = {
    "Quick Commerce": "ACOS",
    "Marketplaces": "ROAS",
    "Beauty Commerce": "TACOS %",
    "International E-Commerce": "Conversion % / Logistics Cost % / CAC",
}

# ---------------------------------------------------------------------------
# KPI definitions / business rules
# ---------------------------------------------------------------------------
# Revenue metric used everywhere unless stated otherwise.
# NOTE: set to "mrp_price" (MRP/list price, not net/discounted revenue) —
# this is a deliberate, confirmed choice; every revenue/AOV/ROAS/TACOS figure
# on the dashboard is measured on this basis. See the MRP disclaimer shown
# on both dashboard pages.
REVENUE_COLUMN = "mrp_price"

# Retention definition: customers in the selected period whose lifetime_orders > 1
# (i.e. this wasn't their first order). Alternative cohort-based logic can be
# swapped in later in utils/kpi_calculations.py
RETENTION_BASIS = "repeat_purchase_rate"

# Vertical registry - add more verticals here as they're built
VERTICALS = {
    "Website": {
        "icon": "🌐",
        "status": "live",
    },
    "Online E-commerce": {
        "icon": "🛒",
        "status": "live",
    },
    # "Retail/POS": {"icon": "🏬", "status": "coming_soon"},
    # "B2B": {"icon": "🤝", "status": "coming_soon"},
}

CURRENCY_SYMBOL = "₹"
