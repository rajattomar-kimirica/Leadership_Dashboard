"""Small UI helpers for rendering consistent, styled KPI cards in Streamlit."""

import streamlit as st


def _fmt_number(value, prefix="", suffix="", decimals=0):
    if value is None:
        return "—"
    try:
        return f"{prefix}{value:,.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return "—"


def kpi_card(label: str, value, delta=None, prefix="", suffix="", decimals=0,
             help_text=None, delta_is_good_when_positive=True):
    """
    Render a single KPI in a card with optional delta (vs previous period).
    delta: numeric % change, or None to hide.
    """
    formatted_value = _fmt_number(value, prefix, suffix, decimals)

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
