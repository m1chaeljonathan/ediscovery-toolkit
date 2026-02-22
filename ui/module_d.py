import io

import openpyxl
import streamlit as st

from modules.term_analytics import TermStats, compute_stats, validate_syntax
from modules.term_generator.generator import generate

STATUS_OPTIONS = ['draft', 'proposed', 'accepted', 'rejected', 'modified']
STATUS_ICONS = {
    'draft': '🔘', 'proposed': '🔵', 'accepted': '🟢',
    'rejected': '🔴', 'modified': '🟡',
}


def _init_state():
    if 'terms' not in st.session_state:
        st.session_state.terms = []


def _to_excel(terms: list) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Search Terms"
    headers = ['Term', 'Syntax', 'Lucene Equivalent', 'Status',
               'Proposed By', 'Doc Hits', 'Family Hits', 'Unique Hits',
               '% Dataset', 'Risk Flags', 'Rationale']
    ws.append(headers)
    for t in terms:
        ws.append([
            t.term_text, t.syntax, t.lucene_equivalent,
            t.status, t.proposed_by,
            t.doc_hits, t.family_hits, t.unique_hits,
            t.pct_of_dataset,
            ', '.join(t.risk_flags) or 'OK',
            t.rationale,
        ])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def render():
    _init_state()
    st.header("Search Term Workbench")
    st.caption("Generate, review, and export search terms for negotiation rounds.")

    gen_tab, review_tab, export_tab = st.tabs(
        ["Generate", "Review & QC", "Export"])

    # -- Generate tab ----------------------------------------------------------
    with gen_tab:
        st.subheader("Generate terms from case description")
        case_text = st.text_area(
            "Case description / ESI order text", height=140,
            placeholder="Describe the matter, key allegations, custodians, "
                        "and relevant time period...")
        seeds_raw = st.text_area("Seed terms (optional — one per line)",
                                 height=60)
        seeds = [s.strip() for s in seeds_raw.splitlines() if s.strip()]

        col1, col2 = st.columns(2)
        with col1:
            proposed_by = st.selectbox(
                "Proposed by", ['pm', 'plaintiff', 'defense', 'attorney'])

        if st.button("Generate terms", type="primary") and case_text:
            with st.spinner("Extracting concepts and drafting terms..."):
                concepts, raw_terms = generate(case_text, seeds)
            st.session_state['last_concepts'] = concepts
            st.info(f"Domain: **{concepts.get('industry_domain', 'unknown')}** · "
                    f"{len(raw_terms)} terms drafted")

            new_terms = []
            for t in raw_terms:
                errors = validate_syntax(
                    t.get('term_text', ''),
                    t.get('syntax', 'dtsearch'))
                flags = ['SYNTAX ERROR'] if errors else []
                ts = TermStats(
                    term_text=t.get('term_text', ''),
                    syntax=t.get('syntax', 'dtsearch'),
                    lucene_equivalent=t.get('lucene_equivalent', ''),
                    rationale=t.get('rationale', ''),
                    proposed_by=proposed_by,
                    status='draft',
                    syntax_errors=errors,
                    risk_flags=flags,
                )
                new_terms.append(ts)
            st.session_state.terms.extend(new_terms)
            st.success(f"Added {len(new_terms)} terms to Review tab.")

        st.divider()
        st.subheader("Add term manually")
        new_text = st.text_input("Term text (dtSearch syntax)")
        new_syntax = st.selectbox("Syntax", ['dtsearch', 'lucene'])
        new_by = st.selectbox("Proposed by ",
                              ['pm', 'plaintiff', 'defense', 'attorney'])
        if st.button("Add term") and new_text:
            errors = validate_syntax(new_text, new_syntax)
            st.session_state.terms.append(TermStats(
                term_text=new_text, syntax=new_syntax,
                proposed_by=new_by, status='proposed',
                syntax_errors=errors,
                risk_flags=['SYNTAX ERROR'] if errors else [],
            ))
            st.rerun()

    # -- Review & QC tab -------------------------------------------------------
    with review_tab:
        terms = st.session_state.terms
        if not terms:
            st.info("Generate or add terms first.")
        else:
            total_docs = st.number_input(
                "Total docs in scope (for % calculation)",
                min_value=1, value=10000)

            terms_with_hits = compute_stats(
                [{'term_text': t.term_text, 'syntax': t.syntax,
                  'doc_hits': t.doc_hits, 'family_hits': t.family_hits,
                  'unique_hits': t.unique_hits,
                  'lucene_equivalent': t.lucene_equivalent,
                  'rationale': t.rationale, 'proposed_by': t.proposed_by,
                  'status': t.status}
                 for t in terms], total_docs)

            flagged = sum(1 for t in terms_with_hits if t.risk_flags)
            if flagged:
                st.warning(f"{flagged} term(s) flagged")
            else:
                st.success("No risk flags")

            for i, t in enumerate(terms_with_hits):
                icon = STATUS_ICONS.get(t.status, '⚪')
                flags = f" `{'` `'.join(t.risk_flags)}`" if t.risk_flags else ""
                with st.expander(f"{icon} {t.term_text[:70]}{flags}"):
                    st.code(t.term_text)
                    if t.lucene_equivalent:
                        st.caption(f"Lucene: `{t.lucene_equivalent}`")
                    if t.rationale:
                        st.write(f"**Rationale**: {t.rationale}")
                    if t.syntax_errors:
                        st.error("Syntax errors: " +
                                 " · ".join(t.syntax_errors))

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        dh = st.number_input("Doc hits", min_value=0,
                                             value=t.doc_hits, key=f"dh_{i}")
                    with c2:
                        fh = st.number_input("Family hits", min_value=0,
                                             value=t.family_hits, key=f"fh_{i}")
                    with c3:
                        uh = st.number_input("Unique hits", min_value=0,
                                             value=t.unique_hits, key=f"uh_{i}")

                    new_status = st.selectbox(
                        "Status", STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(t.status),
                        key=f"st_{i}")

                    if st.button("Update", key=f"upd_{i}"):
                        st.session_state.terms[i].doc_hits = dh
                        st.session_state.terms[i].family_hits = fh
                        st.session_state.terms[i].unique_hits = uh
                        st.session_state.terms[i].status = new_status
                        st.rerun()

                    if st.button("Remove", key=f"rm_{i}"):
                        st.session_state.terms.pop(i)
                        st.rerun()

    # -- Export tab -------------------------------------------------------------
    with export_tab:
        terms = st.session_state.terms
        st.subheader("Export to Excel")
        st.caption("Use file naming for versioning: "
                   "Round1_PlaintiffProposal.xlsx, Round2_DefenseCounter.xlsx")

        if not terms:
            st.info("No terms to export yet.")
        else:
            accepted = [t for t in terms if t.status == 'accepted']
            st.metric("Total terms", len(terms))
            st.metric("Accepted terms", len(accepted))

            col1, col2 = st.columns(2)
            with col1:
                xl_all = _to_excel(terms)
                st.download_button(
                    "Download all terms",
                    xl_all, "search_terms_all.xlsx",
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet")
            with col2:
                if accepted:
                    xl_acc = _to_excel(accepted)
                    st.download_button(
                        "Download accepted only",
                        xl_acc, "search_terms_accepted.xlsx",
                        "application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet")

            if st.button("Clear session", type="secondary"):
                st.session_state.terms = []
                st.rerun()
