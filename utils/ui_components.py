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


def format_kpi_value(value, prefix="", suffix="", decimals=0, compact=False) -> str:
    """Public wrapper around the same formatting kpi_card uses internally —
    for pages (like the Executive Summary) that build their own compact
    layouts instead of using kpi_card's st.metric-based card."""
    return _fmt_number(value, prefix, suffix, decimals, compact=compact)


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

    # Pass a signed number string ("+5.1%" / "-5.1%"), not our own arrow glyph.
    # st.metric draws its own up/down arrow based on the leading sign — if we
    # prepend our own ▲/▼ character instead, Streamlit can't read it as
    # negative and always draws its own arrow pointing up, on top of our
    # (possibly contradicting) glyph. This way there's exactly one arrow,
    # and it's correct.
    delta_str = f"{delta:+.1f}%" if delta is not None else None

    st.metric(
        label=label,
        value=formatted_value,
        delta=delta_str,
        delta_color="normal" if delta_is_good_when_positive else "inverse",
        help=help_text,
    )


def _delta_html(delta, delta_is_good_when_positive=True, decimals=1) -> str:
    """Single colored arrow + %, for use inside compact_kpi_table rows."""
    if delta is None:
        return "<span style='color:#9CA3AF;'>—</span>"
    is_up = delta >= 0
    is_good = is_up if delta_is_good_when_positive else not is_up
    color = "#2B8A3E" if is_good else "#E03131"
    arrow = "▲" if is_up else "▼"
    return f"<span style='color:{color};font-weight:600;'>{arrow} {abs(delta):.{decimals}f}%</span>"


def headline_achievement(label: str, actual_str: str, target_str: str, achievement_pct) -> None:
    """
    One crisp line for an actual-vs-target headline, e.g.:
        FY27 Target Achievement (to date)
        ₹4.13Cr / ₹7.27Cr        56.8% achieved
        [======progress bar======          ]
    Use this instead of three separate kpi_card() cards for the same idea.
    """
    pct = achievement_pct or 0
    bar_pct = max(min(pct, 100), 0)
    st.markdown(
        f"""
        <div style='margin-bottom:14px;'>
            <div style='font-size:0.8rem;color:#6B7280;margin-bottom:2px;'>{label}</div>
            <div style='font-size:1.5rem;font-weight:700;color:#111827;line-height:1.3;'>
                {actual_str}
                <span style='color:#9CA3AF;font-weight:400;'>/</span>
                {target_str}
                <span style='color:#2B8A3E;font-weight:600;font-size:1rem;margin-left:12px;'>
                    {pct:.1f}% achieved
                </span>
            </div>
            <div style='background:#E6E8EC;border-radius:4px;height:6px;margin-top:6px;'>
                <div style='background:#4C6EF5;width:{bar_pct}%;height:6px;border-radius:4px;'></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compact_kpi_table(rows: list, value_col_label: str = "This Period", delta_col_label: str = "vs LY") -> None:
    """
    Renders a crisp, scannable table — one row per metric — instead of a
    grid of large st.metric cards. Each item in `rows` is a dict:
        {"label": str, "value": str (already formatted),
         "delta": float | None, "delta_is_good_when_positive": bool}
    """
    body = "".join(
        f"<tr style='border-bottom:1px solid #EEF0F2;"
        f"background:{'#FAFBFC' if i % 2 else 'transparent'};'>"
        f"<td style='padding:8px 6px;color:#374151;'>{r['label']}</td>"
        f"<td style='padding:8px 6px;text-align:right;font-weight:600;color:#111827;white-space:nowrap;'>{r['value']}</td>"
        f"<td style='padding:8px 6px;text-align:right;width:100px;white-space:nowrap;'>"
        f"{_delta_html(r.get('delta'), r.get('delta_is_good_when_positive', True))}</td>"
        f"</tr>"
        for i, r in enumerate(rows)
    )
    header = (
        "<tr style='border-bottom:2px solid #E6E8EC;'>"
        "<th style='padding:4px 6px;text-align:left;font-size:0.72rem;"
        "text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;font-weight:600;'>Metric</th>"
        f"<th style='padding:4px 6px;text-align:right;font-size:0.72rem;"
        f"text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;font-weight:600;'>{value_col_label}</th>"
        f"<th style='padding:4px 6px;text-align:right;font-size:0.72rem;"
        f"text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;font-weight:600;'>{delta_col_label}</th>"
        "</tr>"
    )
    st.markdown(
        f"<table style='width:100%;border-collapse:collapse;font-size:0.95rem;'>{header}{body}</table>",
        unsafe_allow_html=True,
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
