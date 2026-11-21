"""Minimal, consistent visual system for the Streamlit pilot dashboard."""

from __future__ import annotations


def apply_theme(st) -> None:
    """Apply a calm, high-contrast interface with restrained visual hierarchy."""
    st.markdown(
        """
        <style>
        :root {
          --eo-ink: #172033;
          --eo-muted: #687386;
          --eo-line: #e6eaf0;
          --eo-accent: #2563eb;
          --eo-surface: #ffffff;
          --eo-bg: #f6f8fb;
        }
        .stApp { background: var(--eo-bg); color: var(--eo-ink); }
        [data-testid="stHeader"] { background: rgba(246,248,251,.88); }
        .block-container { max-width: 1440px; padding-top: 1.35rem; padding-bottom: 3rem; }
        h1, h2, h3 { color: var(--eo-ink); letter-spacing: -.035em; }
        h1 { font-size: clamp(1.8rem, 3vw, 2.45rem) !important; font-weight: 720 !important; }
        h2 { font-size: 1.45rem !important; font-weight: 680 !important; }
        h3 { font-size: 1.12rem !important; font-weight: 650 !important; }
        p, label, [data-testid="stCaptionContainer"] { color: var(--eo-muted); }
        .eo-topbar {
          display:flex; align-items:center; gap:12px; padding:10px 0 22px;
          border-bottom:1px solid var(--eo-line); margin-bottom:28px;
        }
        .eo-brand-mark {
          width:42px; height:42px; display:grid; place-items:center; border-radius:13px;
          background:#eaf1ff; color:#1d4ed8; font-size:21px;
        }
        .eo-brand-name { color:var(--eo-ink); font-size:16px; font-weight:750; letter-spacing:-.02em; }
        .eo-brand-subtitle { color:var(--eo-muted); font-size:12px; margin-top:2px; }
        .eo-topbar-spacer { flex:1; }
        .eo-status {
          display:flex; align-items:center; gap:8px; color:#526174; font-size:12px;
          background:#fff; border:1px solid var(--eo-line); border-radius:999px; padding:7px 11px;
        }
        .eo-status span { width:7px; height:7px; border-radius:50%; background:#d97706; display:inline-block; }
        [data-testid="stAlert"] { border-radius:12px; border:1px solid var(--eo-line); }
        [data-testid="stMetric"] {
          background:var(--eo-surface); border:1px solid var(--eo-line); border-radius:14px;
          padding:16px 18px; box-shadow:0 1px 2px rgba(16,24,40,.025);
        }
        [data-testid="stMetricLabel"] { color:var(--eo-muted); font-size:12px; }
        [data-testid="stMetricValue"] { color:var(--eo-ink); font-weight:720; }
        [data-testid="stTabs"] [role="tablist"] {
          gap:8px; border-bottom:1px solid var(--eo-line); margin-bottom:22px;
        }
        [data-testid="stTabs"] button[role="tab"] {
          border-radius:10px 10px 0 0; padding:12px 16px; color:#657187; font-weight:600;
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
          color:var(--eo-accent); border-bottom:2px solid var(--eo-accent);
        }
        [data-testid="stFileUploader"] section {
          background:#fff; border:1px dashed #cbd5e1; border-radius:12px;
        }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
          border:1px solid var(--eo-line); border-radius:12px; overflow:hidden;
        }
        .stButton button, .stDownloadButton button {
          border-radius:10px; font-weight:620; min-height:42px;
        }
        div[data-baseweb="select"] > div, .stTextInput input {
          border-radius:10px;
        }
        hr { border-color:var(--eo-line); }
        @media (max-width: 700px) {
          .block-container { padding-left:1rem; padding-right:1rem; }
          .eo-status { display:none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
