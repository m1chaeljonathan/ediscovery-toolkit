import json
import tempfile

import streamlit as st

from modules.intake_qc import run_intake_qc


def render():
    st.header("Module A — Load File Intake QC")
    st.caption("Validate incoming load files at receipt. Catch formatting and "
               "completeness issues before ingestion.")

    dat_file = st.file_uploader("Load file (DAT or CSV)", type=['dat', 'csv'],
                                key="intake_dat")
    required = st.text_area("Required fields (one per line)",
                            "BEGDOC\nENDDOC\nCUSTODIAN\nDATE_SENT",
                            key="intake_fields")

    if st.button("Run Intake QC", type="primary", key="run_intake") and dat_file:
        with st.spinner("Validating..."):
            with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as f:
                f.write(dat_file.read())
                path = f.name
            req_fields = [v.strip() for v in required.splitlines() if v.strip()]
            result = run_intake_qc(path, required_fields=req_fields)

        stats = result['stats']
        if stats['passed']:
            st.success(f"PASSED — {stats['total_documents']} documents, 0 issues")
        else:
            st.error(f"FAILED — {stats['total_issues']} issues found")

        st.subheader("Headers Received")
        st.write(result['headers_received'])
        st.subheader("Issues")
        st.json(result['issues'])
        st.download_button("Download results",
            json.dumps(result, indent=2), "intake_qc.json", "application/json")
