import io
import json
import tempfile

import pandas as pd
import streamlit as st

from modules.production_qc import run_production_qc, generate_qc_summary
from llm.esi_parser import extract_esi_spec
from llm.client import LLMClient


def _issues_to_dataframe(issues: dict) -> pd.DataFrame:
    """Flatten all issue categories into a single DataFrame."""
    rows = []
    for category, items in issues.items():
        for item in items:
            row = {'category': category}
            row.update(item)
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _df_to_xlsx(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to XLSX bytes."""
    buf = io.BytesIO()
    df.to_excel(buf, index=False, sheet_name='QC Issues')
    return buf.getvalue()


def render():
    st.header("Production QC")
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
                    f.flush()
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
            st.session_state['prod_qc_result'] = result
            # Clear any previous memo when new QC is run
            st.session_state.pop('prod_qc_memo', None)

    # Display results from session state (persists across reruns)
    if 'prod_qc_result' in st.session_state:
        result = st.session_state['prod_qc_result']
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

        # Issue breakdown chart
        st.subheader("Issue Breakdown")
        chart_data = pd.DataFrame({
            'Category': ['Bates', 'Family', 'Coding', 'Cross-Ref'],
            'Issues': [
                stats['bates_issues'], stats['family_issues'],
                stats['coding_issues'], stats['crossref_issues'],
            ],
        })
        chart_data = chart_data[chart_data['Issues'] > 0]
        if not chart_data.empty:
            st.bar_chart(chart_data, x='Category', y='Issues')

        # Full results table
        st.subheader("Full QC Results")
        issues_df = _issues_to_dataframe(result['issues'])
        if not issues_df.empty:
            st.dataframe(issues_df, use_container_width=True)
        else:
            st.info("No issues found.")

        with st.expander("Raw JSON"):
            st.json(result['issues'])

        # Downloads
        st.subheader("Export")
        dl1, dl2, dl3 = st.columns(3)
        with dl1:
            st.download_button("Download JSON",
                json.dumps(result['issues'], indent=2),
                "qc_issues.json", "application/json", key="dl_json")
        with dl2:
            if not issues_df.empty:
                st.download_button("Download CSV",
                    issues_df.to_csv(index=False),
                    "qc_issues.csv", "text/csv", key="dl_csv")
        with dl3:
            if not issues_df.empty:
                st.download_button("Download XLSX",
                    _df_to_xlsx(issues_df),
                    "qc_issues.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_xlsx")

        # LLM summary generation
        st.divider()
        if st.button("Generate Counsel Summary (requires Ollama)", key="gen_summary"):
            with st.spinner("Generating summary memo via LLM..."):
                try:
                    memo = generate_qc_summary(result)
                    st.session_state['prod_qc_memo'] = memo
                except Exception as e:
                    st.error(f"LLM generation failed: {e}\n\n"
                             "Ensure Ollama is running: `ollama serve`")

        if 'prod_qc_memo' in st.session_state:
            st.subheader("Counsel Summary Memo")
            st.markdown(st.session_state['prod_qc_memo'])
            st.download_button("Download summary.md",
                st.session_state['prod_qc_memo'],
                "summary.md", "text/markdown", key="dl_summary")
