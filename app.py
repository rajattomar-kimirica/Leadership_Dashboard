"""
App entry point / page router.

Uses Streamlit's st.navigation() (Streamlit >=1.36) instead of the automatic
`pages/` folder convention. This repo kept hitting a GitHub web-UI limitation
that won't turn a mistakenly-created *file* named `pages` into a proper
folder in one step — st.navigation sidesteps that entirely, since page
scripts can live anywhere with any filename; there's no magic folder name
Streamlit is watching for.

To add a new page: write its script anywhere in the repo (own imports,
own layout code — same as before), then add one more st.Page(...) line
below. Don't call st.set_page_config() inside individual page scripts;
it must only be called once, here, before st.navigation(...).run().
"""

import streamlit as st

st.set_page_config(
    page_title="Kimirica | Leadership Dashboard",
    page_icon="Kimirica",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("executive_summary.py", title="Executive Summary", icon="📈", default=True),
    st.Page("website_detail.py", title="Website — Detail", icon="Kimirica.shop"),
])
pg.run()
