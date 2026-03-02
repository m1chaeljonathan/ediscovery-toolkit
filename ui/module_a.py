import json
import tempfile

import pandas as pd
import streamlit as st

from modules.intake_qc import run_intake_qc
from ui.components import result_panel, empty_state


def render():
    st.header("Intake QC")
    st.caption("Validate incoming load files at receipt. Catch formatting and "
               "completeness issues before ingestion.")

    if 'intake_result' not in st.session_state:
        empty_state(
            "Upload a load file to begin",
            "Supports Concordance DAT and CSV formats. Validates delimiters, required fields, "
            "control numbers, family ranges, and date formats.")

    dat_file = st.file_uploader("Load file (DAT or CSV)", type=['dat', 'csv'],
                                key="intake_dat",
                                help="Upload the load file received from the producing party. "
                                     "Supports Concordance DAT (ASCII 020/254 delimiters) and CSV formats.")
    required = st.text_area("Required fields (one per line)",
                            "BEGDOC\nENDDOC\nCUSTODIAN\nDATE_SENT",
                            key="intake_fields",
                            help="List the metadata fields that must be present in every record. "
                                 "Field names should match the load file headers exactly (case-sensitive).")

    if st.button("Run Intake QC", type="primary", key="run_intake",
                  help="Checks delimiter/encoding detection, required field presence, "
                       "blank control numbers, duplicate control numbers, broken family "
                       "ranges, and Purview date format detection.") and dat_file:
        with st.spinner("Validating..."):
            with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as f:
                f.write(dat_file.read())
                path = f.name
            req_fields = [v.strip() for v in required.splitlines() if v.strip()]
            result = run_intake_qc(path, required_fields=req_fields)
            st.session_state['intake_result'] = result

    if 'intake_result' in st.session_state:
        result = st.session_state['intake_result']
        stats = result['stats']
        if stats['passed']:
            result_panel(
                f"<strong>PASSED</strong> — {stats['total_documents']} documents, 0 issues",
                status="pass")
        else:
            result_panel(
                f"<strong>FAILED</strong> — {stats['total_issues']} issues found",
                status="fail")

        st.subheader("Headers Received")
        st.write(result['headers_received'])
        st.subheader("Issues")
        issues = result['issues']
        rows = []
        for category, items in issues.items():
            for item in items:
                row = {'category': category}
                row.update(item)
                rows.append(row)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.info("No issues found.")
        st.download_button("Download results",
            json.dumps(result, indent=2), "intake_qc.json", "application/json",
            help="Export the full QC results as a JSON file for archival or downstream processing.")
