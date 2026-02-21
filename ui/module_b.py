import json
import tempfile

import streamlit as st

from modules.production_qc import run_production_qc, generate_qc_summary
from llm.esi_parser import extract_esi_spec
from llm.client import LLMClient


def render():
    st.header("Module B — Production QC")
    st.caption("Upload outgoing production load files. Flags privileged/PII content "
               "and spec violations before documents leave the firm.")

    col1, col2 = st.columns(2)
    with col1:
        dat_file = st.file_uploader("Production DAT file", type=['dat', 'csv'],
                                    key="prod_dat")
    with col2:
        opt_file = st.file_uploader("OPT image load file (optional)", type=['opt'],
                                    key="prod_opt")

    esi_file = st.file_uploader("ESI Order PDF (optional — auto-extracts spec)",
                                type=['pdf'], key="prod_esi")

    with st.expander("Manual spec overrides"):
        prefix = st.text_input("Expected Bates prefix (e.g. PROD)")
        confidentiality = st.text_area(
            "Valid confidentiality values (one per line)",
            "CONFIDENTIAL\nHIGHLY CONFIDENTIAL - ATTORNEYS EYES ONLY",
        )

    if st.button("Run Production QC", type="primary", key="run_prod") and dat_file:
        with st.spinner("Running QC checks..."):
            with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as f:
                f.write(dat_file.read())
                dat_path = f.name

            opt_path = None
            if opt_file:
                with tempfile.NamedTemporaryFile(suffix='.opt', delete=False) as f:
                    f.write(opt_file.read())
                    opt_path = f.name

            spec = {}
            if esi_file:
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                    f.write(esi_file.read())
                    try:
                        spec = extract_esi_spec(f.name)
                        st.info(f"ESI spec extracted: {spec.get('required_fields', 'N/A')}")
                    except Exception as e:
                        st.warning(f"ESI extraction failed (LLM may be offline): {e}")

            if prefix:
                spec['expected_prefix'] = prefix
            if confidentiality:
                spec['valid_confidentiality'] = [
                    v.strip() for v in confidentiality.splitlines() if v.strip()
                ]

            result = run_production_qc(dat_path, opt_path, spec)

        stats = result['stats']
        if stats['passed']:
            st.success(f"PASSED — {stats['total_documents']} documents, 0 issues found")
        else:
            st.error(f"FAILED — {stats['total_issues']} issues across "
                     f"{stats['total_documents']} documents")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Docs", stats['total_documents'])
        col2.metric("Bates Issues", stats['bates_issues'])
        col3.metric("Coding Issues", stats['coding_issues'], delta_color="inverse")
        col4.metric("Family Issues", stats['family_issues'])

        if result['issues']['coding']:
            st.subheader("Privilege/PII Flags (immediate review required)")
            st.dataframe(result['issues']['coding'])

        # Store result in session state for summary generation
        st.session_state['prod_qc_result'] = result

        st.subheader("Full QC Results")
        st.json(result['issues'])

        st.download_button("Download stats.json",
            json.dumps(stats, indent=2), "stats.json", "application/json")

    # LLM summary generation — separate from QC run (requires Ollama)
    if 'prod_qc_result' in st.session_state:
        st.divider()
        if st.button("Generate Counsel Summary (requires Ollama)", key="gen_summary"):
            with st.spinner("Generating summary memo via LLM..."):
                try:
                    memo = generate_qc_summary(st.session_state['prod_qc_result'])
                    st.subheader("Counsel Summary Memo")
                    st.markdown(memo)
                    st.download_button("Download summary.md", memo,
                        "summary.md", "text/markdown", key="dl_summary")
                except Exception as e:
                    st.error(f"LLM generation failed: {e}\n\n"
                             "Ensure Ollama is running: `ollama serve`")
