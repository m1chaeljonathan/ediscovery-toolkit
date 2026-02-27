import streamlit as st

from config import is_setup_complete, reload_config
from ui.setup_wizard import render_wizard, detect_providers, test_llm_connection

st.set_page_config(
    page_title="eDiscovery Toolkit",
    page_icon="\u2696",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar — always visible
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("\u2696 eDiscovery Toolkit")

    if is_setup_complete():
        from config import load_config
        cfg = load_config()
        llm = cfg['llm']
        st.caption(f"**LLM**: {llm['model']}")
        st.caption(f"**Endpoint**: {llm['base_url']}")

        if st.button("Reconfigure LLM",
                      help="Re-run the setup wizard to change LLM provider, "
                           "model, or endpoint."):
            # Reset setup_complete so wizard shows
            cfg['setup_complete'] = False
            from config import save_config
            save_config(cfg)
            reload_config()
            # Clear wizard state
            for key in list(st.session_state.keys()):
                if key.startswith('wizard_'):
                    del st.session_state[key]
            st.rerun()

    st.divider()
    st.caption("Local-first. No data leaves your machine.")

# ---------------------------------------------------------------------------
# Main content — wizard or app
# ---------------------------------------------------------------------------

if not is_setup_complete():
    render_wizard()
else:
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
