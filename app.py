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
    page_icon="assets/logo.png",  # browser tab favicon — actual logo works here
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    # NOTE: icon= here is validated as emoji-only by Streamlit itself (see
    # StreamlitAPIException/validate_emoji if you try a real image or URL) —
    # it's a hard platform limit on this specific nav-list icon slot, not
    # something fixable in our code. The actual logo shows up instead in
    # the browser tab (page_icon above) and the sidebar brand block on
    # each page.
    st.Page("executive_summary.py", title="Executive Summary", icon="📈", default=True),
    st.Page("website_detail.py", title="Vertical Detail", icon="📋"),
])
pg.run()
