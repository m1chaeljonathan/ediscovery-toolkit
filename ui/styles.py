import streamlit as st

GLOBAL_CSS = """
<style>
/* -- Theme Variables (Light defaults) ------------------------------------- */
:root {
    --bg: #FFFFFF;
    --card-bg: #F8FAFC;
    --text: #1E293B;
    --text-secondary: #64748B;
    --text-muted: #94A3B8;
    --border: #E2E8F0;
    --panel-bg: #FFFFFF;
    --sidebar-bg: #1E293B;
    --sidebar-text: #E2E8F0;
    --sidebar-caption: #94A3B8;
    --shadow: rgba(0,0,0,0.05);
    --tab-border: #E2E8F0;

}

/* -- System Dark Mode Preference ------------------------------------------ */
@media (prefers-color-scheme: dark) {
    :root {
        --bg: #0F172A;
        --card-bg: #1E293B;
        --text: #E2E8F0;
        --text-secondary: #94A3B8;
        --text-muted: #94A3B8;
        --border: #334155;
        --panel-bg: #1E293B;
        --sidebar-bg: #0F172A;
        --sidebar-text: #E2E8F0;
        --sidebar-caption: #94A3B8;
        --shadow: rgba(0,0,0,0.3);
        --tab-border: #334155;
    }
    /* Main-panel buttons: dark text on Streamlit's white buttons */
    html body .stApp .stButton > button,
    html body .stApp .stButton > button *,
    html body .stApp .stButton > button:hover,
    html body .stApp .stButton > button:hover *,
    html body .stApp [data-testid="stBaseButton-secondary"],
    html body .stApp [data-testid="stBaseButton-secondary"] *,
    html body .stApp [data-testid="stBaseButton-secondary"]:hover,
    html body .stApp [data-testid="stBaseButton-secondary"]:hover *,
    html body .stApp [data-testid="stFileUploader"] button,
    html body .stApp [data-testid="stFileUploader"] button *,
    html body .stApp .stDownloadButton > button,
    html body .stApp .stDownloadButton > button * {
        color: #1E293B !important;
    }
    html body .stApp [data-testid="stBaseButton-primary"],
    html body .stApp [data-testid="stBaseButton-primary"] * {
        color: #FFFFFF !important;
    }
}

/* -- Typography ----------------------------------------------------------- */
.main h1 { font-weight: 700; letter-spacing: -0.02em; }
.main h2 { font-weight: 600; color: var(--text); margin-top: 2rem; }
.main .stCaption { color: var(--text-secondary); }

/* -- Cards ---------------------------------------------------------------- */
.metric-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
}
.metric-card h3 {
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0 0 0.5rem 0;
}
.metric-card .value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text);
}
.metric-card .delta {
    color: var(--text-secondary);
}

/* -- Status Badges -------------------------------------------------------- */
.badge {
    display: inline-block;
    padding: 0.125rem 0.625rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-pass    { background: #DCFCE7; color: #166534; }
.badge-fail    { background: #FEE2E2; color: #991B1B; }
.badge-warning { background: #FEF3C7; color: #92400E; }
.badge-info    { background: #DBEAFE; color: #1E40AF; }
.badge-draft   { background: #F1F5F9; color: #475569; }

/* -- Result Panels -------------------------------------------------------- */
.result-panel {
    background: var(--panel-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 1px 2px var(--shadow);
}
.result-panel.pass { border-left: 4px solid #16A34A; }
.result-panel.fail { border-left: 4px solid #DC2626; }
.result-panel.warn { border-left: 4px solid #D97706; }
.result-panel, .result-panel p, .result-panel li,
.result-panel h1, .result-panel h2, .result-panel h3 {
    color: var(--text) !important;
}

/* -- Empty States --------------------------------------------------------- */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: var(--text-muted);
}
.empty-state h3 { color: var(--text-secondary); margin-bottom: 0.5rem; }
.empty-state p { font-size: 0.95rem; }

/* -- Sidebar Polish ------------------------------------------------------- */
section[data-testid="stSidebar"] {
    background-color: var(--sidebar-bg);
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--sidebar-text) !important;
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: var(--sidebar-text) !important;
}
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] .stCaption p {
    color: var(--sidebar-caption) !important;
}
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] label {
    color: var(--sidebar-text) !important;
}

/* -- Tab Polish ----------------------------------------------------------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 2px solid var(--tab-border);
}
.stTabs [data-baseweb="tab"] {
    padding: 0.75rem 1.25rem;
    font-weight: 500;
}

/* -- Tables --------------------------------------------------------------- */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* -- Streamlit Element Theming (always active, driven by variables) ------- */
.stApp, .main .block-container {
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
.main { background-color: var(--bg) !important; }
.stApp header[data-testid="stHeader"] {
    background-color: var(--bg) !important;
}

/* Text */
.stMarkdown, .stMarkdown p, .stText {
    color: var(--text) !important;
}
h1, h2, h3, h4, h5, h6 { color: var(--text) !important; }

/* Re-assert sidebar headings (must come after the global heading rule) */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--sidebar-text) !important;
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stMarkdown p {
    color: var(--sidebar-text) !important;
}

/* Widget labels */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
.stTextArea > label, .stTextInput > label,
.stSelectbox > label, .stMultiSelect > label {
    color: var(--text) !important;
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background-color: var(--card-bg) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"] {
    background-color: var(--card-bg) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}

/* Placeholder text */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: var(--text-muted) !important;
    opacity: 0.6 !important;
}

/* Expanders */
details[data-testid="stExpander"] {
    background-color: var(--card-bg) !important;
    border-color: var(--border) !important;
}
details[data-testid="stExpander"] summary {
    color: var(--text) !important;
}
details[data-testid="stExpander"] .stMarkdown {
    color: var(--text) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--text) !important;
}

/* DataFrames */
.stDataFrame {
    background-color: var(--card-bg) !important;
}

/* Buttons — border styling */
.stButton > button,
[data-testid="stFileUploader"] button,
.stDownloadButton > button {
    border-color: var(--border) !important;
}

</style>
"""

DARK_CSS = """
<style>
/* -- Explicit Dark Mode Override ------------------------------------------ */
:root {
    --bg: #0F172A;
    --card-bg: #1E293B;
    --text: #E2E8F0;
    --text-secondary: #94A3B8;
    --text-muted: #94A3B8;
    --border: #334155;
    --panel-bg: #1E293B;
    --sidebar-bg: #0F172A;
    --sidebar-text: #E2E8F0;
    --sidebar-caption: #94A3B8;
    --shadow: rgba(0,0,0,0.3);
    --tab-border: #334155;
}

/* Buttons — Streamlit keeps non-primary buttons white in dark mode.
   Hardcoded #1E293B (not var) to avoid resolution issues.
   High-specificity selectors + all interaction states. */
html body .stApp .stButton > button,
html body .stApp .stButton > button *,
html body .stApp .stButton > button:hover,
html body .stApp .stButton > button:hover *,
html body .stApp .stButton > button:focus,
html body .stApp .stButton > button:focus *,
html body .stApp .stButton > button:active,
html body .stApp .stButton > button:active *,
html body .stApp [data-testid="stBaseButton-secondary"],
html body .stApp [data-testid="stBaseButton-secondary"] *,
html body .stApp [data-testid="stBaseButton-secondary"]:hover,
html body .stApp [data-testid="stBaseButton-secondary"]:hover *,
html body .stApp [data-testid="stFileUploader"] button,
html body .stApp [data-testid="stFileUploader"] button *,
html body .stApp [data-testid="stFileUploader"] button:hover,
html body .stApp [data-testid="stFileUploader"] button:hover *,
html body .stApp .stDownloadButton > button,
html body .stApp .stDownloadButton > button *,
html body .stApp .stDownloadButton > button:hover,
html body .stApp .stDownloadButton > button:hover * {
    color: #1E293B !important;
}
/* Primary buttons keep their own styling */
html body .stApp [data-testid="stBaseButton-primary"],
html body .stApp [data-testid="stBaseButton-primary"] * {
    color: #FFFFFF !important;
}
</style>
"""

LIGHT_CSS = """
<style>
/* -- Explicit Light Mode Override ----------------------------------------- */
/* Overrides @media (prefers-color-scheme: dark) when toggle is off */
:root {
    --bg: #FFFFFF;
    --card-bg: #F8FAFC;
    --text: #1E293B;
    --text-secondary: #64748B;
    --text-muted: #94A3B8;
    --border: #E2E8F0;
    --panel-bg: #FFFFFF;
    --sidebar-bg: #1E293B;
    --sidebar-text: #E2E8F0;
    --sidebar-caption: #94A3B8;
    --shadow: rgba(0,0,0,0.05);
    --tab-border: #E2E8F0;

}
</style>
"""


def inject_styles(dark=None):
    """Call once at top of app.py to apply global styles.

    Always emits exactly two st.markdown() calls to keep the Streamlit
    component tree stable across reruns (prevents tab resets on toggle).

    dark=None  – first load; @media prefers-color-scheme in GLOBAL_CSS
                 automatically follows the OS setting
    dark=True  – user toggled dark on; DARK_CSS overrides the media query
    dark=False – user toggled dark off; LIGHT_CSS overrides the media query
    """
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    # Second <style> block — always present for stable component tree.
    if dark is True:
        st.markdown(DARK_CSS, unsafe_allow_html=True)
    elif dark is False:
        st.markdown(LIGHT_CSS, unsafe_allow_html=True)
    else:
        st.markdown("<style>/* theme: auto */</style>", unsafe_allow_html=True)
