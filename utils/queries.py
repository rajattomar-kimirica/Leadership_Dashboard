"""
SQL query builders for the Website vertical.

Every function returns (sql_string, bq_params) ready to hand to
utils.bigquery_client.run_query(). Keeping queries here (not inline in the
Streamlit page) makes them independently testable and easy to reuse across
verticals later.
"""

from google.cloud import bigquery
from config import ORDERS_TABLE, TARGETS_TABLE, GA4_TABLE, WEBSITE_ORDER_CHANNEL_VALUES, \
    WEBSITE_TARGET_CHANNEL_NAME, REVENUE_COLUMN


def _channel_filter_clause(column: str = "order_channel") -> str:
    """Builds an IN (...) clause from the configured website channel values."""
    values = ", ".join(f"'{v}'" for v in WEBSITE_ORDER_CHANNEL_VALUES)
    return f"{column} IN ({values})"


def orders_summary_sql(start_date, end_date):
    """
    One row per day: order count, unique customers, revenue, discounts -
    deduplicated at the order level (the source table is line-item grain).
    """
    sql = f"""
    WITH order_level AS (
        SELECT
            order_id,
            order_date,
            customer_id,
            new_vs_returning,
            ANY_VALUE({REVENUE_COLUMN}) AS order_net_revenue,
            ANY_VALUE(total_discounts) AS order_total_discounts,
            ANY_VALUE(is_cancelled) AS is_cancelled,
            ANY_VALUE(is_refunded) AS is_refunded
        FROM `{ORDERS_TABLE}`
        WHERE order_date BETWEEN @start_date AND @end_date
          AND {_channel_filter_clause()}
        GROUP BY order_id, order_date, customer_id, new_vs_returning
    )
    SELECT
        order_date,
        COUNT(DISTINCT order_id) AS orders,
        COUNT(DISTINCT customer_id) AS unique_customers,
        SUM(order_net_revenue) AS net_revenue,
        SUM(order_total_discounts) AS total_discounts,
        SUM(CASE WHEN new_vs_returning = 'New' THEN 1 ELSE 0 END) AS new_customer_orders,
        SUM(CASE WHEN new_vs_returning = 'Returning' THEN 1 ELSE 0 END) AS returning_customer_orders,
        COUNT(DISTINCT CASE WHEN new_vs_returning = 'New' THEN customer_id END) AS new_customers,
        COUNT(DISTINCT CASE WHEN new_vs_returning = 'Returning' THEN customer_id END) AS returning_customers,
        SUM(CASE WHEN is_cancelled THEN 1 ELSE 0 END) AS cancelled_orders,
        SUM(CASE WHEN is_refunded THEN 1 ELSE 0 END) AS refunded_orders
    FROM order_level
    GROUP BY order_date
    ORDER BY order_date
    """
    params = (
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    )
    return sql, params


def targets_sql(start_date, end_date):
    """Daily target/achievement rows for the Website channel."""
    sql = f"""
    SELECT
        sales_date,
        channel,
        revenue,
        monthly_target,
        daily_target,
        achievement_pct
    FROM `{TARGETS_TABLE}`
    WHERE sales_date BETWEEN @start_date AND @end_date
      AND channel = @channel
    ORDER BY sales_date
    """
    params = (
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        bigquery.ScalarQueryParameter("channel", "STRING", WEBSITE_TARGET_CHANNEL_NAME),
    )
    return sql, params


def retention_sql(start_date, end_date):
    """
    Repeat purchase rate: of the distinct customers who ordered in this
    window, what % had already ordered before (lifetime_orders > 1 as of
    that order, i.e. they are not on their first-ever purchase).
    """
    sql = f"""
    SELECT
        COUNT(DISTINCT customer_id) AS customers_in_period,
        COUNT(DISTINCT CASE WHEN customer_order_number > 1 THEN customer_id END) AS repeat_customers
    FROM `{ORDERS_TABLE}`
    WHERE order_date BETWEEN @start_date AND @end_date
      AND {_channel_filter_clause()}
    """
    params = (
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    )
    return sql, params


def ga4_traffic_sql(start_date, end_date):
    """
    Daily sessions + on-site funnel from the GA4Dashboard table (session
    grain - one row per session, with had_* flags marking how far that
    session progressed). No channel filter needed: this table is GA4 for
    the website itself.
    """
    sql = f"""
    SELECT
        date,
        COUNT(DISTINCT IF(had_session = 1, session_id, NULL)) AS sessions,
        COUNT(DISTINCT IF(had_view_item = 1, session_id, NULL)) AS sessions_viewed_item,
        COUNT(DISTINCT IF(had_atc = 1, session_id, NULL)) AS sessions_added_to_cart,
        COUNT(DISTINCT IF(had_checkout = 1, session_id, NULL)) AS sessions_checkout,
        COUNT(DISTINCT IF(had_purchase = 1, session_id, NULL)) AS sessions_purchased,
        SUM(purchase_revenue_inr) AS ga4_purchase_revenue
    FROM `{GA4_TABLE}`
    WHERE date BETWEEN @start_date AND @end_date
    GROUP BY date
    ORDER BY date
    """
    params = (
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    )
    return sql, params


def channel_distinct_values_sql():
    """Diagnostic query - helps confirm the right channel filter values."""
    sql = f"""
    SELECT order_channel, source_name, COUNT(*) AS orders
    FROM `{ORDERS_TABLE}`
    GROUP BY 1, 2
    ORDER BY orders DESC
    """
    return sql, ()
