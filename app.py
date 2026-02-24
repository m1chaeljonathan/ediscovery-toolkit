import streamlit as st

st.set_page_config(
    page_title="eDiscovery Toolkit",
    page_icon="\u2696",
    layout="wide",
)

st.title("eDiscovery Toolkit")
st.caption("Local-first QC tools for eDiscovery professionals")

tab_litready, tab_intake, tab_search, tab_production, tab_privlog = st.tabs([
    "Litigation Readiness",
    "Intake QC",
    "Search Term Workbench",
    "Production QC",
    "Privilege Log QC",
])

with tab_litready:
    from ui.module_e import render as render_e
    render_e()

with tab_intake:
    from ui.module_a import render as render_a
    render_a()

with tab_search:
    from ui.module_d import render as render_d
    render_d()

with tab_production:
    from ui.module_b import render as render_b
    render_b()

with tab_privlog:
    from ui.module_c import render as render_c
    render_c()
