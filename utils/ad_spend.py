from datetime import date, timedelta

import gspread
import pandas as pd
import streamlit as st
from google.oauth2 import service_account

from config import AD_SPEND_SHEET_ID, AD_SPEND_SHEET_GID

EXCEL_EPOCH = pd.Timestamp("1899-12-30")

# Column layout of the "Daily Data" tab (0-indexed), per the header rows.
# Update here if the sheet's column order ever changes.
COLS = {
    "date": 0,             # A
    "overall_revenue": 1,  # B
    "overall_spend": 2,    # C  (Facebook + Google combined)
    "fb_revenue": 8,        # I
    "fb_spend": 9,          # J
    "fb_conversions": 11,   # L
    "google_revenue": 20,   # V  (col U is blank/merged in the sheet)
    "google_spend": 21,     # W
    "google_conversions": 23,  # Y
}


@st.cache_resource(show_spinner=False)
def _get_sheets_client():
    creds_info = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )
    return gspread.authorize(credentials)


def _excel_serial_to_date(serial) -> date:
    return (EXCEL_EPOCH + pd.Timedelta(days=serial)).date()


@st.cache_data(ttl=600, show_spinner="Fetching ad spend data...")
def load_daily_ad_spend(start_date: date, end_date: date) -> pd.DataFrame:
    """
    Returns a DataFrame with one row per calendar day in [start_date, end_date]:
    date, overall_revenue, overall_spend, fb_spend, google_spend,
    fb_conversions, google_conversions.

    Rows that are weekly/monthly rollups (text dates) are skipped entirely.
    """
    gc = _get_sheets_client()
    sh = gc.open_by_key(AD_SPEND_SHEET_ID)
    worksheet = next(ws for ws in sh.worksheets() if str(ws.id) == str(AD_SPEND_SHEET_GID))

    raw_values = worksheet.get_all_values(value_render_option="UNFORMATTED_VALUE")

    records = []
    for row in raw_values:
        if not row or len(row) <= max(COLS.values()):
            continue
        raw_date = row[COLS["date"]]
        if not isinstance(raw_date, (int, float)) or raw_date <= 0:
            continue  # skip weekly/monthly rollup or blank rows (text labels)
        try:
            row_date = _excel_serial_to_date(raw_date)
        except (ValueError, OverflowError):
            continue

        def _num(col_key):
            v = row[COLS[col_key]]
            return float(v) if isinstance(v, (int, float)) else 0.0

        records.append({
            "date": row_date,
            "overall_revenue": _num("overall_revenue"),
            "overall_spend": _num("overall_spend"),
            "fb_spend": _num("fb_spend"),
            "fb_conversions": _num("fb_conversions"),
            "google_spend": _num("google_spend"),
            "google_conversions": _num("google_conversions"),
        })

    df = pd.DataFrame(records)
    if df.empty:
        return df
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    return df.sort_values("date").reset_index(drop=True)


def total_spend(df: pd.DataFrame) -> float:
    return float(df["overall_spend"].sum()) if not df.empty else 0.0
