import io

import openpyxl
import streamlit as st

from modules.term_analytics import (
    TermStats, compute_stats, group_date_ranges, validate_syntax,
)
from modules.term_generator.generator import generate
from ui.components import metric_card, status_badge, empty_state

STATUS_OPTIONS = ['draft', 'proposed', 'accepted', 'rejected', 'modified']


def _init_state():
    if 'terms' not in st.session_state:
        st.session_state.terms = []
    if 'custodian_date_ranges' not in st.session_state:
        st.session_state.custodian_date_ranges = []


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


def _clear_session(key: str):
    """Render a clear session button. Key must be unique per tab."""
    st.divider()
    if st.button("Clear session", type="secondary", key=key):
        st.session_state.terms = []
        st.session_state.custodian_date_ranges = []
        st.rerun()


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
                        "and relevant time period...",
            help="Describe the matter, key allegations, custodians, relevant "
                 "time periods, and document types. The LLM extracts legal "
                 "concepts and drafts search terms from this text.")
        seeds_raw = st.text_area("Seed terms (optional — one per line)",
                                 height=60,
                                 help="Pre-existing search terms to include "
                                      "alongside LLM-generated terms. One term "
                                      "per line, in dtSearch or Lucene syntax.")
        seeds = [s.strip() for s in seeds_raw.splitlines() if s.strip()]

        col1, col2 = st.columns(2)
        with col1:
            proposed_by = st.selectbox(
                "Proposed by", ['pm', 'plaintiff', 'defense', 'attorney'],
                help="Track which party proposed these terms for negotiation "
                     "round tracking.")

        if st.button("Generate terms", type="primary",
                     help="Runs a two-stage LLM pipeline: (1) extracts legal "
                          "concepts, named entities, and date ranges from the "
                          "case text, (2) drafts dtSearch/Lucene terms with "
                          "rationale and risk notes. Includes deterministic "
                          "name proximity expansions.") and case_text:
            with st.spinner("Extracting concepts and drafting terms..."):
                concepts, raw_terms = generate(case_text, seeds)
            st.session_state['last_concepts'] = concepts
            st.session_state.custodian_date_ranges = concepts.get(
                'custodian_date_ranges', [])
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
        new_text = st.text_input("Term text (dtSearch syntax)",
                                 help="Enter a search term using dtSearch "
                                      "connector syntax (W/n for proximity, "
                                      "AND/OR/NOT for Boolean, * for wildcards, "
                                      "\"quotes\" for phrases).")
        new_syntax = st.selectbox("Syntax", ['dtsearch', 'lucene'],
                                   help="Select the search syntax format. "
                                        "dtSearch uses W/n proximity operators; "
                                        "Lucene uses ~n proximity and standard "
                                        "Boolean.")
        new_by = st.selectbox("Proposed by ",
                              ['pm', 'plaintiff', 'defense', 'attorney'],
                              help="Track which party proposed this term.")
        if st.button("Add term",
                     help="Add a manually entered term to the review list. "
                          "The term will be syntax-validated on entry.") and new_text:
            errors = validate_syntax(new_text, new_syntax)
            st.session_state.terms.append(TermStats(
                term_text=new_text, syntax=new_syntax,
                proposed_by=new_by, status='proposed',
                syntax_errors=errors,
                risk_flags=['SYNTAX ERROR'] if errors else [],
            ))
            st.rerun()

        _clear_session("d_clear_gen")

    # -- Review & QC tab -------------------------------------------------------
    with review_tab:
        terms = st.session_state.terms
        if not terms:
            empty_state("No terms yet", "Generate terms from a case description or add them manually on the Generate tab.")
        else:
            total_docs = st.number_input(
                "Total docs in scope (for % calculation)",
                min_value=1, value=10000,
                help="Enter the total document count in the review population. "
                     "Used to calculate the % of dataset each term hits. "
                     "Update this from your Relativity or review platform "
                     "stats.")

            terms_with_hits = compute_stats(
                [{'term_text': t.term_text, 'syntax': t.syntax,
                  'doc_hits': t.doc_hits, 'family_hits': t.family_hits,
                  'unique_hits': t.unique_hits,
                  'lucene_equivalent': t.lucene_equivalent,
                  'rationale': t.rationale, 'proposed_by': t.proposed_by,
                  'status': t.status}
                 for t in terms], total_docs)

            # -- Date range context -----------------------------------------------
            date_ranges = st.session_state.custodian_date_ranges
            if date_ranges:
                st.subheader("Custodian date ranges")
                st.caption(
                    "Informational — these date ranges apply at the "
                    "Relativity base search level, not as search terms."
                )
                grouped = group_date_ranges(date_ranges)
                for (start, end), custodians in grouped.items():
                    st.info(
                        f"**{start} — {end}**: {', '.join(custodians)}"
                    )

            # -- Risk flags -------------------------------------------------------
            flagged = sum(1 for t in terms_with_hits if t.risk_flags)
            if flagged:
                st.warning(f"{flagged} term(s) flagged")
            else:
                st.success("No risk flags")

            # Summary metric cards
            accepted_count = sum(1 for t in terms_with_hits if t.status == 'accepted')
            flagged_count = sum(1 for t in terms_with_hits if t.risk_flags)
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                metric_card("Total Terms", str(len(terms_with_hits)))
            with sc2:
                metric_card("Accepted", str(accepted_count))
            with sc3:
                metric_card("Flagged", str(flagged_count))

            for i, t in enumerate(terms_with_hits):
                status_label = t.status.upper()
                flags = f" `{'` `'.join(t.risk_flags)}`" if t.risk_flags else ""
                with st.expander(f"[{status_label}] {t.term_text[:70]}{flags}"):
                    st.markdown(status_badge(t.status), unsafe_allow_html=True)
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
                                             value=t.doc_hits, key=f"dh_{i}",
                                             help="Number of documents matching "
                                                  "this term. Enter from your "
                                                  "review platform search "
                                                  "results.")
                    with c2:
                        fh = st.number_input("Family hits", min_value=0,
                                             value=t.family_hits, key=f"fh_{i}",
                                             help="Number of family members "
                                                  "(attachments/embedded) pulled "
                                                  "in by this term. A family/doc "
                                                  "ratio above 3x triggers the "
                                                  "ATTACHMENT HEAVY flag.")
                    with c3:
                        uh = st.number_input("Unique hits", min_value=0,
                                             value=t.unique_hits, key=f"uh_{i}",
                                             help="Documents hit only by this "
                                                  "term and no other. A "
                                                  "unique/total ratio below 5% "
                                                  "triggers the SUBSUMED flag.")

                    new_status = st.selectbox(
                        "Status", STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(t.status),
                        key=f"st_{i}",
                        help="Term lifecycle status: draft (initial), proposed "
                             "(sent to opposing), accepted (agreed), rejected "
                             "(struck), modified (revised version pending).")

                    if st.button("Update", key=f"upd_{i}"):
                        st.session_state.terms[i].doc_hits = dh
                        st.session_state.terms[i].family_hits = fh
                        st.session_state.terms[i].unique_hits = uh
                        st.session_state.terms[i].status = new_status
                        st.rerun()

                    if st.button("Remove", key=f"rm_{i}"):
                        st.session_state.terms.pop(i)
                        st.rerun()

        _clear_session("d_clear_review")

    # -- Export tab -------------------------------------------------------------
    with export_tab:
        terms = st.session_state.terms
        st.subheader("Export to Excel")
        st.caption("Use file naming for versioning: "
                   "Round1_PlaintiffProposal.xlsx, Round2_DefenseCounter.xlsx")

        if not terms:
            empty_state("No terms to export", "Generate or add terms on the other tabs first.")
        else:
            accepted = [t for t in terms if t.status == 'accepted']
            ec1, ec2 = st.columns(2)
            with ec1:
                metric_card("Total terms", str(len(terms)))
            with ec2:
                metric_card("Accepted terms", str(len(accepted)))

            col1, col2 = st.columns(2)
            with col1:
                xl_all = _to_excel(terms)
                st.download_button(
                    "Download all terms",
                    xl_all, "search_terms_all.xlsx",
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet",
                    help="Export all terms (every status) as an Excel workbook "
                         "for negotiation tracking. Use file naming for "
                         "versioning (e.g. Round1_PlaintiffProposal.xlsx).")
            with col2:
                if accepted:
                    xl_acc = _to_excel(accepted)
                    st.download_button(
                        "Download accepted only",
                        xl_acc, "search_terms_accepted.xlsx",
                        "application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet",
                        help="Export only accepted terms as an Excel workbook. "
                             "Use this for the final agreed-upon search term "
                             "list.")

        _clear_session("d_clear_export")
