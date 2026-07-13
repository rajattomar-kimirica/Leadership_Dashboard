"""
Date helpers for the Executive Summary page.

Kept separate from app/page logic (no Streamlit/BigQuery imports) so these
are trivially unit-testable — pure date-in, date-out functions.
"""

import calendar
from datetime import date


def mtd_window(today: date | None = None) -> tuple[date, date]:
    """Month-to-date: the 1st of this month through today."""
    today = today or date.today()
    return today.replace(day=1), today


def same_period_last_year(start: date, end: date) -> tuple[date, date]:
    """
    Shifts a date window back exactly one year, clamping to the last valid
    day of that month if the prior year's month is shorter (e.g. today is
    Feb 29 on a leap year — last year's Feb might only go to 28).
    """
    def _shift(d: date) -> date:
        year = d.year - 1
        last_day_of_month = calendar.monthrange(year, d.month)[1]
        day = min(d.day, last_day_of_month)
        return date(year, d.month, day)

    return _shift(start), _shift(end)


def fy_start(today: date | None = None, fy_start_month: int = 4) -> date:
    """
    Start of the current Financial Year. Default fy_start_month=4 matches
    the April–March Indian FY. If today falls before that month, the FY
    began in the previous calendar year.
    """
    today = today or date.today()
    if today.month >= fy_start_month:
        return date(today.year, fy_start_month, 1)
    return date(today.year - 1, fy_start_month, 1)


def fy_mtd_window(today: date | None = None, fy_start_month: int = 4) -> tuple[date, date]:
    """Financial-year-to-date: FY start through today."""
    today = today or date.today()
    return fy_start(today, fy_start_month), today


def fy_label(today: date | None = None, fy_start_month: int = 4) -> str:
    """
    e.g. 'FY26' for the year ending March 2026 — matches the Indian
    convention of naming a financial year after the calendar year it ends in.
    """
    today = today or date.today()
    end_year = fy_start(today, fy_start_month).year + 1
    return f"FY{str(end_year)[-2:]}"
