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
# TODO: confirm this is the exact string used in Overall_Sales.channel for
# the website (case/spelling can differ table to table) — see the debug
# query in the README/chat if targets still come back empty after this change.
WEBSITE_TARGET_CHANNEL_NAME = "Website"

# ---------------------------------------------------------------------------
# KPI definitions / business rules
# ---------------------------------------------------------------------------
# Revenue metric used everywhere unless stated otherwise.
REVENUE_COLUMN = """"
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
# TODO: confirm this is the exact string used in Overall_Sales.channel for
# the website (case/spelling can differ table to table) — see the debug
# query in the README/chat if targets still come back empty after this change.
WEBSITE_TARGET_CHANNEL_NAME = "Website"

# ---------------------------------------------------------------------------
# KPI definitions / business rules
# ---------------------------------------------------------------------------
# Revenue metric used everywhere unless stated otherwise.
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
    # "Marketplace": {"icon": "🛒", "status": "coming_soon"},
    # "Retail/POS": {"icon": "🏬", "status": "coming_soon"},
    # "B2B": {"icon": "🤝", "status": "coming_soon"},
}

CURRENCY_SYMBOL = "₹""

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
    # "Marketplace": {"icon": "🛒", "status": "coming_soon"},
    # "Retail/POS": {"icon": "🏬", "status": "coming_soon"},
    # "B2B": {"icon": "🤝", "status": "coming_soon"},
}

CURRENCY_SYMBOL = "₹"
