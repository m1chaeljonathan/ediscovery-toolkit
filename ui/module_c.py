import json
import tempfile

import streamlit as st

from modules.privilege_log_qc import run_privilege_log_qc
from llm.esi_parser import extract_privlog_spec


def render():
    st.header("Privilege Log QC")
    st.caption("Validate privilege log format and required fields against "
               "court order specifications.")

    log_file = st.file_uploader("Privilege log (Excel or CSV)", type=['xlsx', 'csv'],
                                key="privlog_file")
    order_file = st.file_uploader("Privilege log order PDF (optional)", type=['pdf'],
                                  key="privlog_order")
    required_cols = st.text_area("Required columns (one per line)",
        "DATE\nAUTHOR\nRECIPIENTS\nDOC_TYPE\nPRIVILEGE_BASIS",
        key="privlog_cols")

    if st.button("Run Privilege Log QC", type="primary", key="run_privlog") and log_file:
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

        stats = result['stats']
        if stats['passed']:
            st.success(f"PASSED — {stats['total_entries']} entries conform to spec")
        else:
            st.error(f"FAILED — {stats['total_issues']} conformity issues found")

        st.subheader("Issues")
        st.json(result['issues'])
        st.download_button("Download results",
            json.dumps(result, indent=2), "privlog_qc.json", "application/json")
