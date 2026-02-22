import streamlit as st

st.set_page_config(
    page_title="eDiscovery Toolkit",
    page_icon="\u2696",
    layout="wide",
)

st.title("eDiscovery Toolkit")
st.caption("Local-first QC tools for eDiscovery professionals")

tab_intake, tab_production, tab_privlog, tab_search = st.tabs([
    "Intake QC",
    "Production QC",
    "Privilege Log QC",
    "Search Term Workbench",
])

with tab_intake:
    from ui.module_a import render as render_a
    render_a()

with tab_production:
    from ui.module_b import render as render_b
    render_b()

with tab_privlog:
    from ui.module_c import render as render_c
    render_c()

with tab_search:
    from ui.module_d import render as render_d
    render_d()
