"""Module E — Litigation Readiness UI.

Four tabs: Data Map, Legal Hold, Risk Assessment, Export.
"""

import io

import openpyxl
import streamlit as st

from ui.components import metric_card, status_badge, empty_state
from modules.ai_lithold import (
    DataType, LegalHold,
    AI_CATEGORIES, TRADITIONAL_CATEGORIES, CATEGORIES, SCENARIO_TYPES,
    DEFAULT_AI_DATA_TYPES, DEFAULT_TRADITIONAL_DATA_TYPES,
    ALL_DEFAULT_DATA_TYPES,
    compute_risk_flags, compute_gap_analysis,
)
from modules.ai_lithold_generator import (
    generate_data_map, analyze_hold_scenario, generate_preservation_memo,
)


def _init_state():
    if 'e_data_types' not in st.session_state:
        st.session_state.e_data_types = []
    if 'e_holds' not in st.session_state:
        st.session_state.e_holds = []
    if 'e_memo' not in st.session_state:
        st.session_state.e_memo = ""


def _load_defaults(defaults: list[DataType]):
    """Load default data types, skipping IDs already present."""
    existing_ids = {dt.id for dt in st.session_state.e_data_types}
    added = 0
    for dt in defaults:
        if dt.id not in existing_ids:
            st.session_state.e_data_types.append(DataType(
                id=dt.id, category=dt.category, name=dt.name,
                description=dt.description, typical_volume=dt.typical_volume,
                typical_format=dt.typical_format,
                retention_policy=dt.retention_policy, custodian=dt.custodian,
                legal_risk=dt.legal_risk,
                preservation_complexity=dt.preservation_complexity,
                notes=dt.notes))
            added += 1
    return added


def _to_excel_datamap(data_types: list[DataType]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data Map"
    headers = ['ID', 'Category', 'Name', 'Description', 'Typical Volume',
               'Typical Format', 'Retention Policy', 'Custodian',
               'Legal Risk', 'Preservation Complexity', 'Notes']
    ws.append(headers)
    for dt in data_types:
        ws.append([dt.id, dt.category, dt.name, dt.description,
                   dt.typical_volume, dt.typical_format,
                   dt.retention_policy, dt.custodian,
                   dt.legal_risk, dt.preservation_complexity, dt.notes])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _to_excel_holds(holds: list[LegalHold]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Legal Holds"
    headers = ['Scenario', 'Type', 'Affected Data Types', 'Scope Summary',
               'Estimated Volume', 'Custodians', 'Preservation Actions',
               'Privilege Considerations', 'Cross-Border Flags']
    ws.append(headers)
    for h in holds:
        ws.append([
            h.scenario, h.scenario_type,
            ', '.join(h.affected_data_types),
            h.hold_scope_summary, h.estimated_volume,
            ', '.join(h.custodians),
            '\n'.join(h.preservation_actions),
            '\n'.join(h.privilege_considerations),
            '\n'.join(h.cross_border_flags),
        ])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _clear_session(key: str):
    """Render a clear session button. Key must be unique per tab."""
    st.divider()
    if st.button("Clear session", type="secondary", key=key):
        st.session_state.e_data_types = []
        st.session_state.e_holds = []
        st.session_state.e_memo = ""
        st.rerun()


def render():
    _init_state()
    st.header("Litigation Readiness")
    st.caption("AI-specific and enterprise data mapping, legal hold workflow, "
               "and preservation memo generation.")

    tab_map, tab_hold, tab_risk, tab_export = st.tabs(
        ["Data Map", "Legal Hold", "Risk Assessment", "Export"])

    # -- Data Map tab ----------------------------------------------------------
    with tab_map:
        st.subheader("Data Type Registry")
        st.caption("Build your data map from defaults, LLM generation, or manual entry.")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Load traditional defaults", type="secondary",
                         help="Load 10 traditional enterprise data types (email, file shares, HR systems, financial records, etc.) as a starting registry."):
                added = _load_defaults(DEFAULT_TRADITIONAL_DATA_TYPES)
                st.success(f"Added {added} traditional data types")
                if added:
                    st.rerun()
        with col2:
            if st.button("Load AI defaults", type="secondary",
                         help="Load 20 AI-specific data types (training data, model artifacts, evaluation records, API logs, etc.) for AI/ML companies."):
                added = _load_defaults(DEFAULT_AI_DATA_TYPES)
                st.success(f"Added {added} AI data types")
                if added:
                    st.rerun()
        with col3:
            if st.button("Load all defaults", type="secondary",
                         help="Load all 30 default data types (traditional + AI). Duplicates are automatically skipped if some are already loaded."):
                added = _load_defaults(ALL_DEFAULT_DATA_TYPES)
                st.success(f"Added {added} data types")
                if added:
                    st.rerun()

        st.divider()

        # LLM-powered generation
        st.subheader("Generate from company description")
        company_desc = st.text_area(
            "Describe the organization (industry, AI usage, data sources)",
            height=100,
            placeholder="e.g. AI research lab building large language models, "
                        "with 500 employees, using cloud infrastructure...",
            help="Describe the company's industry, size, data infrastructure, and AI/ML usage. The LLM generates a tailored data map based on this description.")
        if st.button("Generate data map", type="primary",
                     help="Uses the LLM to analyze the company description and suggest relevant data types with categories, volumes, formats, and risk levels. Requires a running Ollama instance.") and company_desc:
            with st.spinner("Analyzing company profile..."):
                result = generate_data_map(company_desc)
            if result.get("parse_error"):
                st.error("LLM returned invalid JSON. Check your LLM server.")
            else:
                st.info(f"Company type: **{result.get('company_type', 'unknown')}**")
                raw_types = result.get("data_types", [])
                existing_names = {dt.name.lower() for dt in st.session_state.e_data_types}
                added = 0
                for i, rt in enumerate(raw_types):
                    if rt.get("name", "").lower() in existing_names:
                        continue
                    dt_id = f"gen_{i}_{rt.get('category', 'unknown')}"
                    st.session_state.e_data_types.append(DataType(
                        id=dt_id,
                        category=rt.get("category", ""),
                        name=rt.get("name", ""),
                        description=rt.get("description", ""),
                        typical_volume=rt.get("typical_volume", ""),
                        typical_format=rt.get("typical_format", ""),
                        retention_policy="undefined",
                        custodian="unassigned",
                        legal_risk=rt.get("legal_risk", "medium"),
                        preservation_complexity=rt.get("preservation_complexity", "medium"),
                    ))
                    added += 1
                st.success(f"Added {added} suggested data types. "
                           "Review and edit below.")
                if added:
                    st.rerun()

        st.divider()

        # Display and edit data types
        data_types = st.session_state.e_data_types
        if not data_types:
            st.info("Load defaults or generate a data map to get started.")
        else:
            st.caption(f"{len(data_types)} data types in map")

            # Group data types by AI vs Traditional categories
            ai_types = [(i, dt) for i, dt in enumerate(data_types)
                        if dt.category in AI_CATEGORIES]
            trad_types = [(i, dt) for i, dt in enumerate(data_types)
                          if dt.category in TRADITIONAL_CATEGORIES]
            other_types = [(i, dt) for i, dt in enumerate(data_types)
                           if dt.category not in AI_CATEGORIES
                           and dt.category not in TRADITIONAL_CATEGORIES]

            def _render_data_type(i, dt):
                badge_html = status_badge(dt.legal_risk)
                with st.expander(f"[{dt.category}] {dt.name}"):
                    st.markdown(f"**Risk**: {badge_html}", unsafe_allow_html=True)
                    st.write(f"**Description**: {dt.description}")
                    st.write(f"**Volume**: {dt.typical_volume} | "
                             f"**Format**: {dt.typical_format}")

                    c1, c2 = st.columns(2)
                    with c1:
                        new_retention = st.text_input(
                            "Retention policy", value=dt.retention_policy,
                            key=f"e_ret_{i}",
                            help="Define how long this data type must be retained (e.g. '7 years', 'indefinite', 'per litigation hold'). 'undefined' triggers a risk flag.")
                    with c2:
                        new_custodian = st.text_input(
                            "Custodian", value=dt.custodian,
                            key=f"e_cust_{i}",
                            help="Person or team responsible for preserving this data type. 'unassigned' triggers a risk flag.")

                    c3, c4 = st.columns(2)
                    with c3:
                        risk_opts = ["high", "medium", "low"]
                        new_risk = st.selectbox(
                            "Legal risk", risk_opts,
                            index=risk_opts.index(dt.legal_risk)
                            if dt.legal_risk in risk_opts else 1,
                            key=f"e_risk_{i}",
                            help="Litigation exposure level. High-risk types without retention policies or custodians are flagged as critical.")
                    with c4:
                        cx_opts = ["high", "medium", "low"]
                        new_cx = st.selectbox(
                            "Preservation complexity", cx_opts,
                            index=cx_opts.index(dt.preservation_complexity)
                            if dt.preservation_complexity in cx_opts else 1,
                            key=f"e_cx_{i}",
                            help="Difficulty of preserving this data type in place. High complexity without a retention plan triggers a risk flag.")

                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.button("Update", key=f"e_upd_{i}"):
                            dt.retention_policy = new_retention
                            dt.custodian = new_custodian
                            dt.legal_risk = new_risk
                            dt.preservation_complexity = new_cx
                            st.rerun()
                    with bc2:
                        if st.button("Remove", key=f"e_rm_{i}"):
                            st.session_state.e_data_types.pop(i)
                            st.rerun()

            if ai_types:
                st.markdown("#### AI Data Types")
                for i, dt in ai_types:
                    _render_data_type(i, dt)
            if trad_types:
                st.markdown("#### Traditional Data Types")
                for i, dt in trad_types:
                    _render_data_type(i, dt)
            if other_types:
                st.markdown("#### Other Data Types")
                for i, dt in other_types:
                    _render_data_type(i, dt)

        # Add custom
        st.divider()
        st.subheader("Add custom data type")
        with st.form("add_custom_dt"):
            fc1, fc2 = st.columns(2)
            with fc1:
                c_name = st.text_input("Name",
                                       help="Descriptive name for the data type (e.g. 'Training Data Provenance Records').")
                c_cat = st.selectbox("Category", CATEGORIES,
                                     help="Data classification category. AI categories include training_data, model_artifacts, safety_evaluations, etc. Traditional categories include email, file_shares, hr_systems, etc.")
                c_desc = st.text_input("Description",
                                       help="Brief description of what this data type contains and where it is stored.")
                c_vol = st.text_input("Typical volume", placeholder="e.g. 10TB+",
                                      help="Estimated data volume (e.g. '10TB+', '500GB', '< 1GB').")
            with fc2:
                c_fmt = st.text_input("Typical format", placeholder="e.g. JSONL, parquet",
                                      help="Common file formats (e.g. 'JSONL, parquet', 'PST, MSG', 'PDF, DOCX').")
                c_risk = st.selectbox("Legal risk", ["high", "medium", "low"],
                                      help="Litigation exposure if this data is lost or improperly handled.")
                c_cx = st.selectbox("Preservation complexity", ["high", "medium", "low"],
                                    help="Difficulty of implementing a litigation hold on this data type.")
                c_notes = st.text_input("Notes (optional)",
                                        help="Additional context, known issues, or preservation instructions.")
            if st.form_submit_button("Add data type") and c_name:
                dt_id = f"custom_{c_cat}_{c_name.lower().replace(' ', '_')}"
                st.session_state.e_data_types.append(DataType(
                    id=dt_id, category=c_cat, name=c_name,
                    description=c_desc, typical_volume=c_vol,
                    typical_format=c_fmt, retention_policy="undefined",
                    custodian="unassigned", legal_risk=c_risk,
                    preservation_complexity=c_cx, notes=c_notes))
                st.rerun()

        _clear_session("e_clear_map")

    # -- Legal Hold tab --------------------------------------------------------
    with tab_hold:
        st.subheader("Legal Hold Analysis")
        data_types = st.session_state.e_data_types
        if not data_types:
            st.info("Build a data map first (Data Map tab).")
        else:
            scenario_type = st.selectbox("Scenario type", SCENARIO_TYPES,
                                         help="Select the litigation scenario category. Maps to specific data types and preservation actions (e.g. 'copyright_training_data' focuses on training pipeline data).")
            scenario_text = st.text_area(
                "Describe the litigation scenario",
                height=100,
                placeholder="e.g. Plaintiff alleges our training data included "
                            "copyrighted works without license...",
                help="Describe the specific legal claim or regulatory inquiry. The LLM maps this to affected data types in your registry and suggests preservation actions.")

            if st.button("Analyze scenario", type="primary",
                         help="Uses the LLM to identify affected data types, suggest custodians, preservation actions, privilege considerations, and cross-border flags based on your data map.") and scenario_text:
                with st.spinner("Mapping scenario to data types..."):
                    result = analyze_hold_scenario(scenario_text, data_types)
                if result.get("parse_error"):
                    st.error("LLM returned invalid JSON. Check your LLM server.")
                else:
                    # Validate affected IDs exist in data map
                    valid_ids = {dt.id for dt in data_types}
                    affected_ids = [
                        dtid for dtid in result.get("affected_data_type_ids", [])
                        if dtid in valid_ids]

                    hold = LegalHold(
                        scenario=scenario_text,
                        scenario_type=result.get("scenario_type", scenario_type),
                        affected_data_types=affected_ids,
                        hold_scope_summary=result.get("hold_scope_summary", ""),
                        estimated_volume=result.get("estimated_volume", ""),
                        custodians=result.get("suggested_custodians", []),
                        preservation_actions=result.get("preservation_actions", []),
                        privilege_considerations=result.get("privilege_considerations", []),
                        cross_border_flags=result.get("cross_border_flags", []),
                    )

                    st.success(f"Hold analysis complete — "
                               f"{len(affected_ids)} data types affected")

                    if hold.hold_scope_summary:
                        st.write(f"**Scope**: {hold.hold_scope_summary}")
                    if hold.estimated_volume:
                        st.write(f"**Estimated volume**: {hold.estimated_volume}")

                    if affected_ids:
                        dt_lookup = {dt.id: dt for dt in data_types}
                        with st.expander("Affected data types"):
                            for dtid in affected_ids:
                                dt = dt_lookup.get(dtid)
                                if dt:
                                    st.write(f"- **{dt.name}** ({dt.category})")

                    if hold.custodians:
                        with st.expander("Suggested custodians"):
                            for c in hold.custodians:
                                st.write(f"- {c}")

                    if hold.preservation_actions:
                        with st.expander("Preservation actions"):
                            for a in hold.preservation_actions:
                                st.write(f"- {a}")

                    if hold.privilege_considerations:
                        with st.expander("Privilege considerations"):
                            for p in hold.privilege_considerations:
                                st.write(f"- {p}")

                    if hold.cross_border_flags:
                        with st.expander("Cross-border flags"):
                            for cb in hold.cross_border_flags:
                                st.write(f"- {cb}")

                    if st.button("Save hold", key="e_save_hold"):
                        st.session_state.e_holds.append(hold)
                        st.success("Hold saved.")

            # Show saved holds
            holds = st.session_state.e_holds
            if holds:
                st.divider()
                st.subheader(f"Saved holds ({len(holds)})")
                for i, h in enumerate(holds):
                    with st.expander(f"{h.scenario_type}: {h.scenario[:80]}..."):
                        st.write(f"**Scope**: {h.hold_scope_summary}")
                        st.write(f"**Affected**: {len(h.affected_data_types)} data types")
                        st.write(f"**Volume**: {h.estimated_volume}")
                        if st.button("Remove hold", key=f"e_rmhold_{i}"):
                            st.session_state.e_holds.pop(i)
                            st.rerun()

        _clear_session("e_clear_hold")

    # -- Risk Assessment tab ---------------------------------------------------
    with tab_risk:
        st.subheader("Risk Assessment")
        data_types = st.session_state.e_data_types
        if not data_types:
            st.info("Build a data map first (Data Map tab).")
        else:
            gap = compute_gap_analysis(data_types)
            flags = compute_risk_flags(data_types)

            # Metrics row
            score = gap['readiness_score']
            if score > 70:
                score_color = "#16A34A"
            elif score >= 40:
                score_color = "#D97706"
            else:
                score_color = "#DC2626"

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                metric_card("Total data types", str(gap["total_data_types"]))
            with m2:
                metric_card("No retention policy", str(gap["no_retention_policy"]))
            with m3:
                metric_card("No custodian", str(gap["no_custodian"]))
            with m4:
                st.markdown(f'''
                <div class="metric-card">
                    <h3>Readiness score</h3>
                    <div class="value" style="color:{score_color}">{score}/100</div>
                </div>
                ''', unsafe_allow_html=True)

            st.divider()

            # Risk flags
            if not flags:
                st.success("No risk flags — all data types have policies and custodians.")
            else:
                st.warning(f"{len(flags)} risk flag(s) detected")
                for rf in flags:
                    if rf.severity == "critical":
                        st.error(f"**CRITICAL** [{rf.flag_type}] {rf.detail}")
                    elif rf.severity == "high":
                        st.warning(f"**HIGH** [{rf.flag_type}] {rf.detail}")
                    else:
                        st.info(f"**MEDIUM** [{rf.flag_type}] {rf.detail}")

            st.divider()

            # Gap analysis detail
            st.subheader("Gap Analysis")
            st.write(f"**Category coverage**: {gap['coverage_pct']}% "
                     f"({len(CATEGORIES) - len(gap['missing_categories'])}/{len(CATEGORIES)})")
            if gap["missing_categories"]:
                st.write("**Missing categories**: " +
                         ", ".join(gap["missing_categories"]))
            st.write(f"**High-risk data types**: {gap['high_risk_total']} "
                     f"({gap['high_risk_exposed']} exposed)")

            st.divider()

            # Preservation memo generation
            st.subheader("Preservation Memo")
            holds = st.session_state.e_holds
            if not holds:
                st.info("Save at least one legal hold (Legal Hold tab) to generate a memo.")
            else:
                hold_options = [
                    f"{h.scenario_type}: {h.scenario[:60]}" for h in holds]
                selected_idx = st.selectbox(
                    "Select hold for memo", range(len(hold_options)),
                    format_func=lambda i: hold_options[i],
                    help="Choose which saved legal hold to generate a preservation memo for.")
                if st.button("Generate preservation memo", type="primary",
                             help="Generates a professional preservation scope memo in legal format, covering affected data types, custodians, preservation actions, and privilege considerations."):
                    with st.spinner("Drafting preservation memo..."):
                        memo = generate_preservation_memo(
                            holds[selected_idx], data_types)
                    st.session_state.e_memo = memo
                    st.rerun()

            if st.session_state.e_memo:
                st.markdown(st.session_state.e_memo)

        _clear_session("e_clear_risk")

    # -- Export tab -------------------------------------------------------------
    with tab_export:
        st.subheader("Export")
        data_types = st.session_state.e_data_types
        holds = st.session_state.e_holds

        if not data_types and not holds:
            st.info("No data to export yet.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                if data_types:
                    xl_map = _to_excel_datamap(data_types)
                    st.download_button(
                        "Download data map (Excel)",
                        xl_map, "litigation_readiness_datamap.xlsx",
                        "application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet",
                        help="Export the full data type registry as an Excel workbook for distribution to IT, legal, and compliance teams.")
                    st.caption(f"{len(data_types)} data types")
            with col2:
                if holds:
                    xl_holds = _to_excel_holds(holds)
                    st.download_button(
                        "Download hold details (Excel)",
                        xl_holds, "litigation_readiness_holds.xlsx",
                        "application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet",
                        help="Export all saved legal holds as an Excel workbook with affected data types, custodians, and preservation actions.")
                    st.caption(f"{len(holds)} holds")

            if st.session_state.e_memo:
                st.download_button(
                    "Download preservation memo (Markdown)",
                    st.session_state.e_memo,
                    "preservation_memo.md",
                    "text/markdown",
                    help="Export the preservation memo as a Markdown file for conversion to Word or PDF.")

        _clear_session("e_clear_export")
