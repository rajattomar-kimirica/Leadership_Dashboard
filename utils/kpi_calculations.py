"""
Pure calculation functions: take DataFrames already pulled from BigQuery
(or manual-entry numbers) and return the KPI numbers the dashboard displays.
Kept free of Streamlit/BigQuery calls so they're easy to unit test.
"""

import pandas as pd
import numpy as np


def pct_change(current: float, previous: float) -> float | None:
    """Safe percentage change; returns None if previous is 0/missing."""
    if previous in (0, None) or pd.isna(previous):
        return None
    return (current - previous) / previous * 100


def safe_div(numerator: float, denominator: float) -> float | None:
    if not denominator:
        return None
    return numerator / denominator


def summarize_orders(df: pd.DataFrame) -> dict:
    """Aggregate the daily orders_summary_sql() output into period totals."""
    if df.empty:
        return {
            "net_revenue": 0, "orders": 0, "unique_customers": 0,
            "new_customers": 0, "returning_customers": 0,
            "total_discounts": 0, "aov": 0,
        }
    net_revenue = df["net_revenue"].sum()
    orders = df["orders"].sum()
    return {
        "net_revenue": net_revenue,
        "orders": orders,
        "unique_customers": df["unique_customers"].sum(),
        "new_customers": df["new_customers"].sum(),
        "returning_customers": df["returning_customers"].sum(),
        "total_discounts": df["total_discounts"].sum(),
        "aov": safe_div(net_revenue, orders) or 0,
    }


def retention_rate(retention_df: pd.DataFrame) -> float:
    """% of customers in the period who were repeat purchasers."""
    if retention_df.empty or retention_df.loc[0, "customers_in_period"] == 0:
        return 0.0
    row = retention_df.iloc[0]
    return round(row["repeat_customers"] / row["customers_in_period"] * 100, 2)


def targets_summary(targets_df: pd.DataFrame) -> dict:
    """Sum target vs actual revenue for the period and compute achievement %."""
    if targets_df.empty:
        return {"target_revenue": 0, "actual_revenue": 0, "achievement_pct": 0}
    target_total = targets_df["daily_target"].sum()
    actual_total = targets_df["revenue"].sum()
    return {
        "target_revenue": target_total,
        "actual_revenue": actual_total,
        "achievement_pct": round(safe_div(actual_total, target_total) * 100, 2)
        if target_total else 0,
    }


def cac(total_spend: float, new_customers: int) -> float | None:
    """Customer Acquisition Cost = ad spend / new customers acquired."""
    return safe_div(total_spend, new_customers)


def roas(revenue: float, total_spend: float) -> float | None:
    """Return on Ad Spend = revenue / ad spend."""
    return safe_div(revenue, total_spend)


def tacos(total_ad_spend: float, total_revenue: float) -> float | None:
    """Total Advertising Cost of Sale = total ad spend / total revenue * 100."""
    val = safe_div(total_ad_spend, total_revenue)
    return round(val * 100, 2) if val is not None else None

def conversion_rate(orders: int, sessions: int) -> float | None:
    """Conversion % = orders / website sessions * 100."""
    val = safe_div(orders, sessions)
    return round(val * 100, 2) if val is not None else None


def summarize_ga4(df: pd.DataFrame) -> dict:
    """Sum the daily GA4 traffic/funnel rows into period totals."""
    if df.empty:
        return {
            "sessions": 0, "sessions_viewed_item": 0, "sessions_added_to_cart": 0,
            "sessions_checkout": 0, "sessions_purchased": 0,
        }
    return {
        "sessions": int(df["sessions"].sum()),
        "sessions_viewed_item": int(df["sessions_viewed_item"].sum()),
        "sessions_added_to_cart": int(df["sessions_added_to_cart"].sum()),
        "sessions_checkout": int(df["sessions_checkout"].sum()),
        "sessions_purchased": int(df["sessions_purchased"].sum()),
    }


def summarize_channel_sales(df: pd.DataFrame) -> dict:
    """
    Sums channel_sales_revenue_sql() output (Online E-commerce, Secondary
    Sales) into period totals. Revenue here is Secondary Sales only —
    Primary Sales will be added once that table exists.
    """
    if df.empty:
        return {"revenue": 0, "quantity": 0}
    return {
        "revenue": df["revenue"].sum(),
        "quantity": df["quantity"].sum(),
    }
