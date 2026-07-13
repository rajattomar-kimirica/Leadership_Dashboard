"""Small UI helpers for rendering consistent, styled KPI cards in Streamlit."""

import streamlit as st


def _indian_compact(value: float) -> str:
    """
    Abbreviate large rupee amounts using Indian numbering: L = Lakh (1,00,000),
    Cr = Crore (1,00,00,000). Keeps KPI cards from truncating long numbers.
    """
    sign = "-" if value < 0 else ""
    abs_v = abs(value)
    if abs_v >= 1_00_00_000:
        return f"{sign}{abs_v / 1_00_00_000:.2f}Cr"
    if abs_v >= 1_00_000:
        return f"{sign}{abs_v / 1_00_000:.2f}L"
    if abs_v >= 1_000:
        return f"{sign}{abs_v / 1_000:.1f}K"
    return f"{sign}{abs_v:,.0f}"


def _fmt_number(value, prefix="", suffix="", decimals=0, compact=False):
    if value is None:
        return "—"
    try:
        if compact:
            return f"{prefix}{_indian_compact(value)}{suffix}"
        return f"{prefix}{value:,.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return "—"


def kpi_card(label: str, value, delta=None, prefix="", suffix="", decimals=0,
             help_text=None, delta_is_good_when_positive=True, compact=False):
    """
    Render a single KPI in a card with optional delta (vs previous period).
    delta: numeric % change, or None to hide.
    compact: if True, abbreviates large currency values as L (Lakh) / Cr
        (Crore) instead of the full number with commas — use this for big
        revenue-style figures that would otherwise overflow the card.
    """
    formatted_value = _fmt_number(value, prefix, suffix, decimals, compact=compact)

    delta_str = None
    if delta is not None:
        arrow = "▲" if delta >= 0 else "▼"
        delta_str = f"{arrow} {abs(delta):.1f}%"

    st.metric(
        label=label,
        value=formatted_value,
        delta=delta_str,
        delta_color="normal" if delta_is_good_when_positive else "inverse",
        help=help_text,
    )


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def placeholder_note(text="MANUAL ENTRY", color="#FFF3CD", text_color="#856404"):
    badge = (
        f"<span style='background-color:{color};color:{text_color};padding:2px 8px;"
        f"border-radius:10px;font-size:0.75em;font-weight:600;'>{text}</span>"
    )
    st.markdown(badge, unsafe_allow_html=True)
