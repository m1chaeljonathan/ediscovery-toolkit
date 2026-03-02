"""Reusable styled UI components for the eDiscovery Toolkit."""

import streamlit as st


def metric_card(label: str, value: str, delta: str = None):
    """Render a styled metric card with uppercase label and large value."""
    delta_html = (
        f'<div class="delta" style="color:var(--text-secondary);font-size:0.85rem">{delta}</div>'
        if delta else ''
    )
    st.markdown(f'''
    <div class="metric-card">
        <h3>{label}</h3>
        <div class="value">{value}</div>
        {delta_html}
    </div>
    ''', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    """Return HTML string for a colored status pill badge."""
    css_class = {
        'pass': 'badge-pass', 'passed': 'badge-pass', 'accepted': 'badge-pass',
        'fail': 'badge-fail', 'failed': 'badge-fail', 'rejected': 'badge-fail',
        'warning': 'badge-warning', 'modified': 'badge-warning',
        'info': 'badge-info', 'proposed': 'badge-info',
        'draft': 'badge-draft',
    }.get(status.lower(), 'badge-draft')
    return f'<span class="badge {css_class}">{status.upper()}</span>'


def result_panel(content: str, status: str = "info"):
    """Render content in a bordered panel with colored left accent."""
    css_class = {
        'pass': 'pass', 'fail': 'fail', 'warning': 'warn',
    }.get(status, '')
    st.markdown(f'''
    <div class="result-panel {css_class}">
        {content}
    </div>
    ''', unsafe_allow_html=True)


def empty_state(title: str, description: str):
    """Render a centered placeholder with guidance text."""
    st.markdown(f'''
    <div class="empty-state">
        <h3>{title}</h3>
        <p>{description}</p>
    </div>
    ''', unsafe_allow_html=True)
