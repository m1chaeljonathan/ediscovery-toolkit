import json
import tempfile

import pandas as pd
import streamlit as st

from modules.privilege_log_qc import run_privilege_log_qc
from llm.esi_parser import extract_privlog_spec
from ui.components import result_panel, empty_state


def render():
    st.header("Privilege Log QC")
    st.caption("Validate privilege log format and required fields against "
               "court order specifications.")

    if 'privlog_result' not in st.session_state:
        empty_state(
            "Upload a privilege log to begin",
            "Supports Excel and CSV formats. Validates required columns, "
            "field completeness, and privilege basis codes.")

    log_file = st.file_uploader("Privilege log (Excel or CSV)", type=['xlsx', 'csv'],
                                key="privlog_file",
                                help="Upload the privilege log draft. Supports Excel (.xlsx) and CSV formats. Each row should represent one withheld or redacted document.")
    order_file = st.file_uploader("Privilege log order PDF (optional)", type=['pdf'],
                                  key="privlog_order",
                                  help="Upload the court order specifying privilege log requirements. The LLM will extract required columns and formatting rules automatically.")
    required_cols = st.text_area("Required columns (one per line)",
        "DATE\nAUTHOR\nRECIPIENTS\nDOC_TYPE\nPRIVILEGE_BASIS",
        key="privlog_cols",
        help="List the column headers that must be present and populated in the privilege log. These are overridden if an order PDF is uploaded and successfully parsed.")

    if st.button("Run Privilege Log QC", type="primary", key="run_privlog",
                  help="Validates required columns are present, required fields are populated (date, author, recipients, doc type, privilege basis), and privilege basis codes are valid (ACP, WP, common interest, etc.).") and log_file:
        with st.spinner("Validating..."):
            suffix = '.' + log_file.name.rsplit('.', 1)[-1]
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(log_file.read())
                log_path = f.name

            spec = {}
            if order_file:
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                    f.write(order_file.read())
                    try:
                        spec = extract_privlog_spec(f.name)
                        st.info(f"Order spec extracted: required columns = "
                                f"{spec.get('required_columns')}")
                    except Exception as e:
                        st.warning(f"Spec extraction failed (LLM may be offline): {e}")

            cols = spec.get('required_columns') or [
                v.strip() for v in required_cols.splitlines() if v.strip()
            ]
            result = run_privilege_log_qc(log_path, required_columns=cols)
            st.session_state['privlog_result'] = result

    if 'privlog_result' in st.session_state:
        result = st.session_state['privlog_result']
        stats = result['stats']
        if stats['passed']:
            result_panel(
                f"<strong>PASSED</strong> — {stats['total_entries']} entries conform to spec",
                status="pass")
        else:
            result_panel(
                f"<strong>FAILED</strong> — {stats['total_issues']} conformity issues found",
                status="fail")

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
            json.dumps(result, indent=2), "privlog_qc.json", "application/json",
            help="Export the full QC results as a JSON file for archival or downstream processing.")
