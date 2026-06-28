# Kimirica Leadership KPI Dashboard

A Streamlit dashboard giving the founder a single view of vertical-wise KPIs.
**Live now:** Website vertical. Built to extend to other verticals.

## What it shows (Website)

| KPI | Source | Status |
|---|---|---|
| Revenue (Target vs Achieved) | `Datachannel.Sales_Vs_Targets` | ✅ Live |
| Growth % | `master_orders_flat` (vs previous period) | ✅ Live |
| Traffic | `analytics_288570553.GA4Dashboard` | ✅ Live |
| Conversion % | Shopify orders ÷ GA4 sessions | ✅ Live |
| AOV | `master_orders_flat` | ✅ Live |
| New Customers | `master_orders_flat` (`new_vs_returning`) | ✅ Live |
| Retention % | `master_orders_flat` (`customer_order_number`) | ✅ Live |
| CAC | KIMIRICA Reporting Data sheet ("Daily Data" tab) ÷ new customers | ✅ Live |
| ROAS | Revenue ÷ ad spend (same sheet) | ✅ Live |
| Overall TACOS | Ad spend (same sheet) ÷ revenue | ✅ Live |

All 10 KPIs are now wired to live sources. Each card carries a green
"LIVE" badge or amber "MANUAL ENTRY" badge depending on whether its sidebar
override is switched on (useful if a source is temporarily down).

## Project structure

```
.
├── app.py                      # Main Streamlit page
├── config.py                   # All business constants (tables, channel filters, KPI rules)
├── requirements.txt
├── utils/
│   ├── bigquery_client.py      # Cached BigQuery connection + query runner
│   ├── queries.py               # SQL builders (one function per data need)
│   ├── kpi_calculations.py     # Pure Python KPI math (unit-testable)
│   └── ui_components.py        # Reusable KPI card / section header widgets
└── .streamlit/
    └── secrets.toml.example     # Template - copy to secrets.toml, fill in, never commit
```

## Local setup

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a GCP Service Account with **BigQuery Data Viewer** + **BigQuery
   Job User** roles on `aerobic-copilot-494105-b6`, generate a JSON key.

3. Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` and
   paste in your service account JSON fields.

4. **Share the ad spend Google Sheet** ("KIMIRICA- Reporting Data-2024-25")
   with your service account's email (the `client_email` value from the
   JSON key) as **Viewer**. Without this, CAC/ROAS/TACOS will show a
   sidebar warning and fall back to ₹0 — use the "Override ad spend
   manually" checkbox in the sidebar as a stopgap.

5. Run:
   ```bash
   streamlit run app.py
   ```

## Deploying on Streamlit Community Cloud

1. Push this repo to GitHub (secrets.toml is gitignored — don't force-add it).
2. On [share.streamlit.io](https://share.streamlit.io), create a new app
   pointing at this repo, `app.py` as the entry point.
3. In the app's **Settings → Secrets**, paste the same contents as your local
   `secrets.toml` (TOML format, `[gcp_service_account]` block).
4. Deploy. Every push to `main` auto-redeploys.

## Website filter (confirmed)

`order_channel = 'Website'` is the confirmed filter — verified against:

```sql
SELECT order_channel, source_name, COUNT(*) AS orders
FROM `aerobic-copilot-494105-b6.shopify_kimirica.master_orders_flat`
GROUP BY 1, 2
ORDER BY orders DESC;
```

| order_channel | source_name | orders |
|---|---|---|
| Website | Created by Shopflo | 167,460 |
| Store | pos | 60,308 (excluded — in-store POS) |
| Website | shopify_draft_order | 7,561 |
| Website | web | 2,912 |
| Website | (numeric source ids) | 35 |

`source_name` is too messy to filter on directly (checkout app names, draft
orders, raw numeric IDs) — `order_channel = 'Website'` alone cleanly covers
every website order. This is set in `config.py::WEBSITE_ORDER_CHANNEL_VALUES`.

## Adding a new vertical

1. Add an entry to `VERTICALS` in `config.py`.
2. Duplicate the query/calculation pattern in `utils/queries.py` and
   `utils/kpi_calculations.py` for the new vertical's data source.
3. Either branch inside `app.py` on the selected vertical, or split into a
   multipage app (`pages/2_Marketplace.py`, etc.) once there are 2+ verticals
   — recommended once this grows past Website.

## Known notes

- **Conversion %** is defined as Shopify orders ÷ GA4 sessions — a
  cross-source rate, not GA4's native purchase-event conversion rate.
  Swap to `sessions_purchased ÷ sessions` from `ga4_traffic_sql()` in
  `utils/queries.py` if you'd rather match GA4's own definition exactly.
- **Retention %** is currently defined as repeat-purchase rate within the
  selected window (customers with `customer_order_number > 1`). Swap in
  cohort-based retention in `utils/kpi_calculations.py::retention_rate` if a
  different definition is preferred.
- Every sidebar "Override manually" checkbox is a safety net — if a live
  source (sheet permissions lapse, GA4 table renamed, etc.) breaks, the app
  shows a clear warning instead of crashing, and you can switch to manual
  entry for that one section while it's fixed.
