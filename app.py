import streamlit as st

st.set_page_config(
    page_title="eDiscovery Toolkit",
    page_icon="\u2696",
    layout="wide",
)

st.title("eDiscovery Toolkit")
st.caption("Local-first QC tools for eDiscovery professionals")

tab_b, tab_a, tab_c = st.tabs([
    "Production QC (Module B)",
    "Intake QC (Module A)",
    "Privilege Log QC (Module C)",
])

with tab_b:
    from ui.module_b import render as render_b
    render_b()

with tab_a:
    from ui.module_a import render as render_a
    render_a()

with tab_c:
    from ui.module_c import render as render_c
    render_c()
