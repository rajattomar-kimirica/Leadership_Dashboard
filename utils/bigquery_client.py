"""
BigQuery client wrapper.

Auth: expects a service-account JSON stored in Streamlit secrets as
[gcp_service_account] (see .streamlit/secrets.toml.example).

Locally, you can instead set GOOGLE_APPLICATION_CREDENTIALS to a key file
and this will fall back to default credentials.
"""

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account


@st.cache_resource(show_spinner=False)
def get_bq_client() -> bigquery.Client:
    """Create (and cache) a single BigQuery client for the app session."""
    if "gcp_service_account" in st.secrets:
        credentials = service_account.Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        project = st.secrets["gcp_service_account"]["project_id"]
        return bigquery.Client(credentials=credentials, project=project)

    # Fallback: ADC (e.g. GOOGLE_APPLICATION_CREDENTIALS env var, local dev)
    return bigquery.Client()


@st.cache_data(ttl=600, show_spinner="Fetching data from BigQuery...")
def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """
    Run a parameterised SQL query against BigQuery and return a DataFrame.
    Results are cached for 10 minutes per unique (sql, params) pair.
    """
    client = get_bq_client()
    job_config = bigquery.QueryJobConfig(query_parameters=list(params))
    df = client.query(sql, job_config=job_config).to_dataframe()
    return df
