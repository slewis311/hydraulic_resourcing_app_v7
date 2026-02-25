import streamlit as st
import requests
from bisect import bisect_right
import base64
import hashlib
import secrets as pysecrets
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlencode

PRIMARY_DATASET_ID = "main"
SECONDARY_DATASET_ID = "scott"
MANUAL_QUERY_KEY = "manual"
MANUAL_MARKDOWN_PATH = Path(__file__).resolve().parent / "docs" / "hydraulic_resourcing_user_manual.md"

def _query_param_str(key: str) -> str:
    try:
        value = st.query_params.get(key, "")
    except Exception:
        return ""
    if isinstance(value, list):
        if len(value) == 0:
            return ""
        return str(value[0]).strip()
    return str(value).strip()

def is_manual_mode() -> bool:
    return _query_param_str(MANUAL_QUERY_KEY).lower() in {"1", "true", "yes"}

def set_manual_mode(enabled: bool) -> None:
    if enabled:
        st.query_params[MANUAL_QUERY_KEY] = "1"
    else:
        if MANUAL_QUERY_KEY in st.query_params:
            del st.query_params[MANUAL_QUERY_KEY]

def render_quickstart_manual_page() -> None:
    st.markdown(
        '''
        <style>
          .manual-hero {
            background: linear-gradient(135deg, #167f99, #24a7b3 55%, #59c0c9);
            border: 1px solid rgba(255,255,255,0.35);
            border-radius: 16px;
            padding: 18px 20px;
            margin-bottom: 0.8rem;
            color: #f7fcff;
            box-shadow: 0 14px 30px rgba(22, 92, 113, 0.24);
            position: relative;
            overflow: hidden;
          }
          .manual-hero::after {
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            height: 4px;
            background: linear-gradient(90deg, #efe73f, rgba(239,231,63,0.2));
          }
          .manual-title {
            font-family: "Manrope", sans-serif;
            font-size: 1.8rem;
            font-weight: 800;
            margin-bottom: 0.1rem;
          }
          .manual-sub {
            color: rgba(240, 249, 252, 0.96);
            margin: 0;
          }
        </style>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="manual-hero"><div class="manual-title">Quickstart Manual</div><p class="manual-sub">Hydraulic Resourcing App setup and user guide</p></div>',
        unsafe_allow_html=True,
    )

    label = "Back to app" if bool(st.session_state.get("authenticated", False)) else "Back to sign in"
    c1, c2 = st.columns([1.2, 4.2])
    with c1:
        if st.button(label, use_container_width=True, key="manual_back_btn"):
            set_manual_mode(False)
            st.rerun()
    with c2:
        st.caption("Tip: Use browser Print -> Save as PDF for a shareable copy.")

    if MANUAL_MARKDOWN_PATH.exists():
        manual_text = MANUAL_MARKDOWN_PATH.read_text(encoding="utf-8")
        st.markdown(manual_text)
    else:
        st.error(f"Manual file not found: {MANUAL_MARKDOWN_PATH}")

def require_login():
    st.set_page_config(page_title="Hydraulic Resourcing App", layout="wide")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if is_manual_mode():
        render_quickstart_manual_page()
        st.stop()

    if st.session_state["authenticated"]:
        if "state_dataset_id" not in st.session_state:
            st.session_state["state_dataset_id"] = PRIMARY_DATASET_ID
        return

    st.markdown(
        '''
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');
          .stApp {
            background:
              linear-gradient(120deg, rgba(36,167,179,0.08), transparent 35%),
              radial-gradient(900px 360px at 88% -8%, rgba(36,167,179,0.22), transparent 60%),
              radial-gradient(700px 280px at 8% 2%, rgba(239,231,63,0.14), transparent 58%),
              linear-gradient(180deg, #f6fbfd, #edf7fa);
          }
          html, body, [class*="css"] { font-family: "Plus Jakarta Sans", sans-serif; color: #10242f; }
          .login-wrap { max-width: 560px; margin: 9vh auto 0 auto; }
          .login-card {
            border: 1px solid rgba(16, 36, 47, 0.12);
            border-radius: 18px;
            padding: 20px 20px;
            background: rgba(255,255,255,0.88);
            backdrop-filter: blur(6px);
            box-shadow: 0 14px 30px rgba(16, 35, 47, 0.10);
          }
          .login-hero {
            background: linear-gradient(135deg, #167f99, #24a7b3 55%, #59c0c9);
            border: 1px solid rgba(255,255,255,0.35);
            border-radius: 14px;
            padding: 14px 16px 12px 16px;
            margin-bottom: 14px;
            box-shadow:
              0 12px 24px rgba(22, 92, 113, 0.24),
              0 0 0 1px rgba(255,255,255,0.24) inset;
            position: relative;
            overflow: hidden;
          }
          .login-hero::after {
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            height: 4px;
            background: linear-gradient(90deg, #efe73f, rgba(239, 231, 63, 0.22));
          }
          .login-hero::before {
            content: "";
            position: absolute;
            width: 180px;
            height: 180px;
            right: -64px;
            top: -96px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.34), rgba(255,255,255,0.03));
          }
          .login-title { font-family: "Manrope", sans-serif; font-size: 2rem; font-weight: 800; margin-bottom: 0.15rem; color: #f7fcff; letter-spacing: -0.01em; }
          .login-sub { color: rgba(237, 248, 252, 0.95); margin-bottom: 0; }
          .login-card [data-testid="stTextInput"] input {
            border-radius: 12px;
            border: 1px solid rgba(31,126,151,0.26);
            background: rgba(255,255,255,0.9);
          }
          .login-card .stButton > button {
            border-radius: 12px;
            border: 1px solid rgba(31,126,151,0.34);
            background: linear-gradient(135deg, rgba(36,167,179,0.14), rgba(255,255,255,0.96));
          }
          .login-card .stButton > button:hover {
            border-color: #24a7b3;
            box-shadow: 0 6px 16px rgba(31,126,151,0.16);
          }
          header[data-testid="stHeader"],
          div[data-testid="stToolbar"],
          div[data-testid="stDecoration"],
          div[data-testid="stStatusWidget"],
          div[data-testid="stAppDeployButton"],
          #MainMenu,
          footer {
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
            display: none !important;
          }
        </style>
        ''',
        unsafe_allow_html=True
    )

    left_spacer, center_col, right_spacer = st.columns([1.2, 2.2, 1.2])
    with center_col:
        st.markdown('<div class="login-hero"><div class="login-title">Hydraulic Resourcing App</div><div class="login-sub">Admin login required</div></div>', unsafe_allow_html=True)
        pwd = st.text_input("Password", type="password")
        col1, col2 = st.columns([1, 1.4])
        with col1:
            sign_in = st.button("Sign in", use_container_width=True)
        with col2:
            if st.button("Quickstart manual", use_container_width=True):
                set_manual_mode(True)
                st.rerun()

    if sign_in:
        primary_pwd = st.secrets.get("APP_PASSWORD", "")
        secondary_pwd = st.secrets.get("APP_PASSWORD_SCOTT", "scott")
        if primary_pwd and pwd == primary_pwd:
            st.session_state["authenticated"] = True
            st.session_state["state_dataset_id"] = PRIMARY_DATASET_ID
            st.session_state["login_profile"] = "primary"
            st.rerun()
        elif secondary_pwd and pwd == secondary_pwd:
            st.session_state["authenticated"] = True
            st.session_state["state_dataset_id"] = SECONDARY_DATASET_ID
            st.session_state["login_profile"] = "secondary"
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()

require_login()

import pandas as pd
from datetime import date, datetime, timedelta, timezone

st.markdown(
    '''
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');
      :root {
        --bg-a: #f6fbfd;
        --bg-b: #edf7fa;
        --ink-1: #10242f;
        --ink-2: #4a6270;
        --line: rgba(16, 36, 47, 0.10);
        --brand: #24a7b3;
        --brand-dark: #1f7e97;
        --accent: #efe73f;
        --card: #ffffff;
      }
      .stApp {
        background:
          linear-gradient(120deg, rgba(36,167,179,0.08), transparent 35%),
          radial-gradient(900px 360px at 88% -8%, rgba(36,167,179,0.22), transparent 60%),
          radial-gradient(700px 280px at 8% 2%, rgba(239,231,63,0.14), transparent 58%),
          linear-gradient(180deg, var(--bg-a), var(--bg-b));
      }
      .block-container { padding-top: 3.8rem; padding-bottom: 2rem; max-width: 1320px; }
      html, body, [class*="css"] { font-family: "Plus Jakarta Sans", sans-serif; color: var(--ink-1); }
      .main .block-container {
        position: relative;
      }
      .main .block-container::before {
        content: "";
        position: absolute;
        inset: 0;
        background-image:
          linear-gradient(rgba(31,126,151,0.04) 1px, transparent 1px),
          linear-gradient(90deg, rgba(31,126,151,0.04) 1px, transparent 1px);
        background-size: 28px 28px;
        pointer-events: none;
        mask-image: linear-gradient(180deg, rgba(0,0,0,0.45), rgba(0,0,0,0.08) 28%, transparent 55%);
      }
      .app-hero {
        background: linear-gradient(135deg, #167f99, #24a7b3 55%, #59c0c9);
        border: 1px solid rgba(255,255,255,0.35);
        border-radius: 18px;
        padding: 22px 24px 20px 24px;
        margin-bottom: 0.75rem;
        box-shadow:
          0 18px 40px rgba(22, 92, 113, 0.28),
          0 0 0 1px rgba(255,255,255,0.26) inset;
        position: relative;
        overflow: hidden;
      }
      .app-hero::after {
        content: "";
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 5px;
        background: linear-gradient(90deg, var(--accent), rgba(239, 231, 63, 0.2));
        border-radius: 0 0 18px 18px;
      }
      .app-hero::before {
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        right: -80px;
        top: -120px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255,255,255,0.36), rgba(255,255,255,0.03));
      }
      .hero-chip {
        display: inline-block;
        background: rgba(239, 231, 63, 0.22);
        color: #fffce0;
        border: 1px solid rgba(255, 247, 151, 0.62);
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 10px;
      }
      .app-title { font-family: "Manrope", sans-serif; font-size: 2.15rem; font-weight: 800; margin-bottom: 0.12rem; color: #f8fdff; letter-spacing: -0.02em; }
      .app-sub { color: rgba(240, 249, 252, 0.94); margin-top: 0.1rem; font-size: 1rem; }
      .card {
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 14px 16px;
        background: rgba(255,255,255,0.86);
        backdrop-filter: blur(6px);
        box-shadow:
          0 10px 28px rgba(16, 35, 47, 0.08),
          0 0 0 1px rgba(255,255,255,0.75) inset;
      }
      .metric-note { font-size: 0.84rem; color: var(--ink-2); margin-top: 0.15rem; }
      .section-title {
        font-family: "Manrope", sans-serif;
        font-size: 1.24rem;
        font-weight: 800;
        margin-top: 0.25rem;
        color: #133242;
        letter-spacing: -0.01em;
      }
      .calendar-table { border-collapse: collapse; width: 100%; table-layout: fixed; }
      .calendar-table th { text-align: left; font-size: 0.82rem; padding: 8px; color: var(--ink-2); border-bottom: 1px solid var(--line); }
      .calendar-table td { vertical-align: top; padding: 10px; border: 1px solid rgba(18,38,48,0.1); height: 86px; background: rgba(255,255,255,0.9); }
      .cal-date { font-weight: 700; font-size: 0.9rem; margin-bottom: 6px; color: #1f3c4f; }
      .cal-nav {
        text-align: center;
        font-family: "Manrope", sans-serif;
        font-size: 1.02rem;
        font-weight: 800;
        color: #114357;
        padding-top: 6px;
      }
      .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.78rem; }
      .pill-green { background: rgba(28, 170, 108, 0.2); }
      .pill-red { background: rgba(207, 79, 66, 0.2); }
      .pill-amber { background: rgba(239, 231, 63, 0.34); }
      .mini { color: var(--ink-2); font-size: 0.8rem; margin-top: 4px; }
      .mini-job { color: #27485c; font-size: 0.78rem; margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      [data-testid="stSidebar"] {
        background:
          linear-gradient(180deg, #f0f9fc, #e6f3f7);
        border-right: 1px solid rgba(31,126,151,0.20);
      }
      [data-testid="stSidebar"] h3 { color: #1d3b4f; font-family: "Manrope", sans-serif; }
      [data-testid="stSidebar"] .stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(31,126,151,0.30);
        background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(232,246,250,0.9));
        transition: all 140ms ease;
      }
      [data-testid="stSidebar"] .stButton > button:hover {
        border-color: var(--brand);
        color: var(--brand-dark);
        background: linear-gradient(135deg, rgba(239,231,63,0.28), rgba(255,255,255,0.92));
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(31,126,151,0.14);
      }
      .stTabs [role="tablist"] { gap: 8px; border-bottom: none; }
      .stTabs [role="tab"] {
        background: rgba(255,255,255,0.7);
        border: 1px solid rgba(18,38,48,0.08);
        border-radius: 999px;
        padding: 8px 14px;
      }
      .stTabs [aria-selected="true"] {
        border-color: rgba(31,126,151,0.35);
        box-shadow:
          0 0 0 2px rgba(239,231,63,0.45) inset,
          0 8px 20px rgba(31,126,151,0.15);
        color: var(--brand-dark);
        font-weight: 700;
        background: rgba(255,255,255,0.95);
      }
      [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
        background: rgba(255,255,255,0.88);
      }
      [data-testid="stDataFrame"] [role="columnheader"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(238,247,250,0.95));
        color: #1f4658;
        font-weight: 700;
        border-bottom: 1px solid rgba(31,126,151,0.2);
      }
      [data-testid="stDataFrame"] [role="gridcell"] {
        border-color: rgba(16,36,47,0.08);
      }
      [data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {
        background: rgba(36,167,179,0.08);
      }
      [data-testid="stDataEditor"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
        background: rgba(255,255,255,0.9);
      }
      [data-testid="stDataEditor"] [role="columnheader"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(239,248,251,0.95));
        color: #1d4a5c;
        font-weight: 700;
        border-bottom: 1px solid rgba(31,126,151,0.2);
      }
      [data-testid="stDataEditor"] [role="gridcell"] {
        border-color: rgba(16,36,47,0.08);
      }
      [data-testid="stDataEditor"] [role="row"]:hover [role="gridcell"] {
        background: rgba(36,167,179,0.08);
      }
      .kpi-card {
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 10px 12px 12px 12px;
        background: rgba(255,255,255,0.9);
        box-shadow: 0 8px 18px rgba(31,126,151,0.1);
      }
      .kpi-head {
        font-size: 0.8rem;
        font-weight: 700;
        color: var(--brand-dark);
        background: rgba(255,255,255,0.96);
        border: 1px solid rgba(31,126,151,0.30);
        border-radius: 999px;
        padding: 4px 10px;
        display: inline-block;
        margin-bottom: 8px;
      }
      .kpi-value {
        font-family: "Manrope", sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #143746;
        line-height: 1.05;
      }
      .health-wrap {
        margin-top: 10px;
        margin-bottom: 8px;
      }
      .health-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border-radius: 999px;
        padding: 7px 12px;
        border: 1px solid rgba(16,36,47,0.15);
        background: rgba(255,255,255,0.9);
        font-weight: 700;
        color: #143746;
      }
      .health-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
      }
      .health-healthy .health-dot { background: #2dbb77; }
      .health-warning .health-dot { background: #f29d2d; }
      .health-early .health-dot { background: #f0c92d; }
      .health-critical .health-dot { background: #d9534f; }
      .kpi-health-value {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: "Manrope", sans-serif;
        font-size: 1.55rem;
        font-weight: 800;
        color: #143746;
        line-height: 1.1;
      }
      .dot-healthy { background: #2dbb77; }
      .dot-warning { background: #f29d2d; }
      .dot-early { background: #f0c92d; }
      .dot-critical { background: #d9534f; }
      .table-shell {
        border: 1px solid rgba(31,126,151,0.20);
        border-radius: 16px;
        padding: 8px;
        background: rgba(255,255,255,0.74);
        box-shadow: 0 10px 24px rgba(16,35,47,0.08);
        margin: 4px 0 8px 0;
      }
      .table-toolbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 6px 8px 10px 8px;
      }
      .table-title {
        font-family: "Manrope", sans-serif;
        font-weight: 800;
        color: #134457;
        letter-spacing: -0.01em;
      }
      .table-meta {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      .table-chip {
        font-size: 0.72rem;
        font-weight: 700;
        border-radius: 999px;
        padding: 3px 9px;
        border: 1px solid rgba(31,126,151,0.24);
        background: rgba(255,255,255,0.92);
        color: #1d5d74;
      }
      .table-chip-hold {
        border-color: rgba(239,231,63,0.55);
        background: rgba(239,231,63,0.18);
        color: #605a19;
      }
      .table-chip-active {
        border-color: rgba(31,126,151,0.35);
        background: rgba(36,167,179,0.12);
      }
      .leave-cal .stButton > button {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 2rem;
        min-width: 2.2rem;
        padding: 0 !important;
        border-radius: 9px;
        font-size: 0.78rem;
        font-weight: 700;
        line-height: 1;
        white-space: nowrap !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
        letter-spacing: 0.01em;
      }
      .leave-cal .stButton > button * {
        white-space: nowrap !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
        hyphens: none !important;
        text-align: center !important;
        line-height: 1 !important;
      }
      .leave-cal .stButton > button p {
        margin: 0 !important;
      }
      .leave-cal .mini {
        margin-top: 2px;
        margin-bottom: 2px;
        text-align: center;
      }
      .leave-cal .cal-nav {
        padding-top: 2px;
        padding-bottom: 2px;
      }
      .leave-day {
        min-height: 2rem;
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.78rem;
        font-weight: 700;
        white-space: nowrap;
        line-height: 1;
        text-align: center;
      }
      .leave-day-past {
        border: 1px solid rgba(18,38,48,0.10);
        background: rgba(49,51,63,0.10);
        color: rgba(49,51,63,0.60);
      }
      .leave-mini .calendar-table th {
        font-size: 0.78rem;
        padding: 6px;
      }
      .leave-mini .calendar-table td {
        height: 58px;
        padding: 7px;
      }
      .leave-mini .cal-date {
        font-size: 0.8rem;
        margin-bottom: 4px;
      }
      .leave-mini .mini {
        font-size: 0.74rem;
        margin-top: 2px;
      }
      .stDownloadButton button {
        border-radius: 12px;
        border: 1px solid rgba(31,126,151,0.36);
        background: linear-gradient(135deg, rgba(36,167,179,0.16), rgba(255,255,255,0.96));
        box-shadow: 0 8px 18px rgba(31,126,151,0.12);
      }
      .stButton > button {
        border-radius: 12px;
      }
      .stButton > button:hover {
        box-shadow: 0 6px 16px rgba(31,126,151,0.16);
      }
      header[data-testid="stHeader"],
      div[data-testid="stToolbar"],
      div[data-testid="stDecoration"],
      div[data-testid="stStatusWidget"],
      div[data-testid="stAppDeployButton"],
      #MainMenu,
      footer {
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        display: none !important;
      }
      @media (max-width: 900px) {
        .block-container { padding-top: 4.4rem; }
        .app-title { font-size: 1.76rem; }
        .app-hero { padding: 16px; }
      }
    </style>
    ''',
    unsafe_allow_html=True
)

st.markdown(
    '''
    <div class="app-hero">
      <div class="app-title">Hydraulic Resourcing App</div>
      <div class="app-sub">Team scheduling, priority queues, and completion forecasting</div>
    </div>
    ''',
    unsafe_allow_html=True
)

WEEKDAY_MAP = [("Mon", 0), ("Tue", 1), ("Wed", 2), ("Thu", 3), ("Fri", 4), ("Sat", 5), ("Sun", 6)]
LABEL_TO_INT = {k: v for k, v in WEEKDAY_MAP}
INT_TO_LABEL = {v: k for k, v in WEEKDAY_MAP}

JOB_COLS = ["Job name", "Required hours", "Priority", "Assignee", "Due date", "Notes"]
SUPABASE_STATE_TABLE = "app_state"
SUPABASE_DEFAULT_STATE_ID = PRIMARY_DATASET_ID
MS_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
MS_DEFAULT_SCOPES = ["offline_access", "openid", "profile", "User.Read", "Calendars.Read"]
MS_SNAPSHOT_HORIZON_DAYS = 60

DEFAULT_TEAM_ROWS = [
    {"Member": "SL", "Daily hours": 8.0},
    {"Member": "LS", "Daily hours": 8.0},
    {"Member": "LB", "Daily hours": 8.0},
]

DEFAULT_JOBS_ROWS = [
    {"Job name": "Job B", "Required hours": 8.0, "Priority": 1, "Assignee": "SL", "Due date": None, "Notes": ""},
    {"Job name": "Job A", "Required hours": 16.0, "Priority": 2, "Assignee": "SL", "Due date": None, "Notes": ""},
    {"Job name": "Backlog item", "Required hours": 6.0, "Priority": 0, "Assignee": "SL", "Due date": None, "Notes": "On hold"},
]

def build_working_dates(start_date: date, weekdays: set[int], non_working_dates: set[date], horizon_days: int = 3650) -> list[date]:
    dates = []
    d = start_date
    for _ in range(horizon_days):
        if d.weekday() in weekdays and d not in non_working_dates:
            dates.append(d)
        d = d + timedelta(days=1)
    return dates

def normalize_unavailable_hours(unavailable_hours: dict | None, daily_hours: float) -> dict[date, float]:
    out: dict[date, float] = {}
    if unavailable_hours is None:
        return out
    for k, v in unavailable_hours.items():
        kd = _safe_date(k)
        if kd is None:
            continue
        try:
            hv = float(v)
        except Exception:
            continue
        if hv <= 0:
            continue
        out[kd] = min(hv, float(daily_hours))
    return out

def build_capacity_days(
    start_date: date,
    weekdays: set[int],
    non_working_dates: set[date],
    daily_hours: float,
    unavailable_hours: dict | None = None,
    horizon_days: int = 3650,
) -> list[tuple[date, float]]:
    unavail = normalize_unavailable_hours(unavailable_hours, daily_hours)
    days: list[tuple[date, float]] = []
    d = start_date
    for _ in range(horizon_days):
        if d.weekday() in weekdays and d not in non_working_dates:
            cap = max(float(daily_hours) - float(unavail.get(d, 0.0)), 0.0)
            days.append((d, cap))
        d = d + timedelta(days=1)
    return days

def get_supabase_config() -> tuple[str, str, bool]:
    url = st.secrets.get("SUPABASE_URL", "").strip().rstrip("/")
    key = st.secrets.get("SUPABASE_ANON_KEY", "").strip()
    return url, key, bool(url and key)

def get_active_state_id() -> str:
    state_id = str(st.session_state.get("state_dataset_id", SUPABASE_DEFAULT_STATE_ID)).strip()
    return state_id if state_id else SUPABASE_DEFAULT_STATE_ID

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _safe_date(value) -> date | None:
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.date()

def _safe_datetime(value) -> datetime | None:
    dt = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(dt):
        return None
    return dt.to_pydatetime()

def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)

def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)

def _normalize_scope_list(raw_scopes) -> list[str]:
    if isinstance(raw_scopes, (list, tuple, set)):
        items = [str(x).strip() for x in raw_scopes]
    else:
        items = str(raw_scopes or "").replace(",", " ").split()
    out: list[str] = []
    for s in items:
        if s and s not in out:
            out.append(s)
    for req in MS_DEFAULT_SCOPES:
        if req not in out:
            out.append(req)
    return out

def get_microsoft_calendar_config() -> dict:
    tenant_raw = st.secrets.get("MS_TENANT_ID", "common")
    client_id_raw = st.secrets.get("MS_CLIENT_ID", "")
    client_secret_raw = st.secrets.get("MS_CLIENT_SECRET", "")
    redirect_uri_raw = st.secrets.get("MS_REDIRECT_URI", "")
    scopes_raw = st.secrets.get("MS_SCOPES", MS_DEFAULT_SCOPES)

    tenant_id = str(tenant_raw).strip() if tenant_raw is not None else "common"
    tenant_id = tenant_id or "common"
    client_id = str(client_id_raw).strip() if client_id_raw is not None else ""
    client_secret = str(client_secret_raw).strip() if client_secret_raw is not None else ""
    redirect_uri = str(redirect_uri_raw).strip() if redirect_uri_raw is not None else ""
    scopes = _normalize_scope_list(scopes_raw)

    return {
        "tenant_id": tenant_id,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "scopes": scopes,
        "scope_text": " ".join(scopes),
        "authorize_url": f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
        "device_code_url": f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/devicecode",
        "token_url": f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        "ready": bool(client_id and redirect_uri),
    }

def _default_calendar_sync_state() -> dict:
    return {
        "provider": "microsoft",
        "tenant_id": "",
        "client_id": "",
        "linked_email": "",
        "access_token": "",
        "access_token_expires_at": "",
        "refresh_token": "",
        "device_code": "",
        "device_expires_at": "",
        "device_interval": 5,
        "verification_uri": "",
        "user_code": "",
        "last_snapshot_at": "",
        "last_snapshot_member": "",
        "last_snapshot_event_count": 0,
        "last_snapshot_hours": 0.0,
        "oauth_state": "",
        "oauth_code_verifier": "",
        "oauth_created_at": "",
    }

def ensure_calendar_sync_state() -> None:
    default = _default_calendar_sync_state()
    current = st.session_state.get("calendar_sync")
    if not isinstance(current, dict):
        st.session_state["calendar_sync"] = default
        return
    merged = default.copy()
    for k in default.keys():
        if k in current:
            merged[k] = current[k]
    st.session_state["calendar_sync"] = merged

def get_effective_unavailable_hours(cfg: dict, daily_hours: float) -> dict[date, float]:
    manual_map = normalize_unavailable_hours(cfg.get("unavailable_hours", {}), daily_hours)
    calendar_map = normalize_unavailable_hours(cfg.get("calendar_unavailable_hours", {}), daily_hours)
    out: dict[date, float] = {}
    for d in set(list(manual_map.keys()) + list(calendar_map.keys())):
        total = float(manual_map.get(d, 0.0)) + float(calendar_map.get(d, 0.0))
        if total > 0:
            out[d] = min(float(daily_hours), total)
    return out

def _default_member_settings(members: list[str]) -> dict:
    out = {}
    for m in members:
        out[m] = {
            "weekdays": {0, 1, 2, 3, 4},
            "leave_dates": [],
            "start_date": date.today(),
            "unavailable_hours": {},
            "calendar_unavailable_hours": {},
        }
    return out

def _normalize_team_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(DEFAULT_TEAM_ROWS)
    out = df.copy()
    if "Member" not in out.columns:
        out["Member"] = None
    if "Daily hours" not in out.columns:
        out["Daily hours"] = None
    out = out[["Member", "Daily hours"]]
    out = out.dropna(subset=["Member", "Daily hours"], how="any")
    out = out[out["Member"].astype(str).str.len() > 0]
    out["Daily hours"] = pd.to_numeric(out["Daily hours"], errors="coerce")
    out = out[out["Daily hours"] >= 1.0]
    out = out.reset_index(drop=True)
    return out if not out.empty else pd.DataFrame(DEFAULT_TEAM_ROWS)

def init_local_state_if_missing() -> None:
    if "team" not in st.session_state:
        st.session_state["team"] = pd.DataFrame(DEFAULT_TEAM_ROWS)
    if "jobs_raw" not in st.session_state:
        st.session_state["jobs_raw"] = pd.DataFrame(DEFAULT_JOBS_ROWS)
    if "member_settings" not in st.session_state:
        members = st.session_state["team"]["Member"].astype(str).tolist()
        st.session_state["member_settings"] = _default_member_settings(members)
    ensure_calendar_sync_state()

def serialize_state_payload() -> dict:
    team_df = _normalize_team_df(st.session_state.get("team", pd.DataFrame(DEFAULT_TEAM_ROWS)))
    jobs_df = clean_jobs_df(st.session_state.get("jobs_raw", pd.DataFrame(columns=JOB_COLS)))
    ms = st.session_state.get("member_settings", {})

    team_records = team_df.to_dict(orient="records")
    jobs_records = []
    for row in jobs_df.to_dict(orient="records"):
        due = _safe_date(row.get("Due date"))
        jobs_records.append(
            {
                "Job name": str(row.get("Job name", "")),
                "Required hours": float(row.get("Required hours", 0.0)),
                "Priority": int(row.get("Priority", 0)),
                "Assignee": str(row.get("Assignee", "")),
                "Due date": None if due is None else due.isoformat(),
                "Notes": str(row.get("Notes", "")),
            }
        )

    settings_records = {}
    for member, cfg in ms.items():
        weekdays = sorted([int(x) for x in cfg.get("weekdays", {0, 1, 2, 3, 4})])
        leave_dates = []
        for d in cfg.get("leave_dates", []):
            parsed = _safe_date(d)
            if parsed is not None:
                leave_dates.append(parsed.isoformat())
        unavailable_hours = {}
        for k, v in (cfg.get("unavailable_hours", {}) or {}).items():
            kd = _safe_date(k)
            if kd is None:
                continue
            try:
                hv = float(v)
            except Exception:
                continue
            if hv > 0:
                unavailable_hours[kd.isoformat()] = hv
        calendar_unavailable_hours = {}
        for k, v in (cfg.get("calendar_unavailable_hours", {}) or {}).items():
            kd = _safe_date(k)
            if kd is None:
                continue
            try:
                hv = float(v)
            except Exception:
                continue
            if hv > 0:
                calendar_unavailable_hours[kd.isoformat()] = hv
        start = _safe_date(cfg.get("start_date", date.today()))
        settings_records[str(member)] = {
            "weekdays": weekdays,
            "leave_dates": leave_dates,
            "start_date": date.today().isoformat() if start is None else start.isoformat(),
            "unavailable_hours": unavailable_hours,
            "calendar_unavailable_hours": calendar_unavailable_hours,
        }

    ensure_calendar_sync_state()
    sync = st.session_state.get("calendar_sync", _default_calendar_sync_state())
    sync_record = _calendar_state_clean_for_save(sync)

    return {
        "team": team_records,
        "jobs_raw": jobs_records,
        "member_settings": settings_records,
        "calendar_sync": sync_record,
    }

def apply_state_payload(payload: dict) -> None:
    team_df = _normalize_team_df(pd.DataFrame(payload.get("team", DEFAULT_TEAM_ROWS)))
    st.session_state["team"] = team_df

    jobs_df = pd.DataFrame(payload.get("jobs_raw", DEFAULT_JOBS_ROWS))
    if "Due date" in jobs_df.columns:
        jobs_df["Due date"] = pd.to_datetime(jobs_df["Due date"], errors="coerce").dt.date
    st.session_state["jobs_raw"] = clean_jobs_df(jobs_df)

    members = team_df["Member"].astype(str).tolist()
    defaults = _default_member_settings(members)
    incoming = payload.get("member_settings", {})
    loaded = {}
    if isinstance(incoming, dict):
        for m in members:
            cfg = incoming.get(m, {})
            weekdays_raw = cfg.get("weekdays", [0, 1, 2, 3, 4])
            weekdays = set()
            for w in weekdays_raw:
                try:
                    wi = int(w)
                except Exception:
                    continue
                if 0 <= wi <= 6:
                    weekdays.add(wi)
            if len(weekdays) == 0:
                weekdays = {0, 1, 2, 3, 4}
            leave_dates = []
            for d in cfg.get("leave_dates", []):
                parsed = _safe_date(d)
                if parsed is not None:
                    leave_dates.append(parsed)
            unavailable_hours = {}
            for kd, hv in (cfg.get("unavailable_hours", {}) or {}).items():
                parsed = _safe_date(kd)
                if parsed is None:
                    continue
                try:
                    h = float(hv)
                except Exception:
                    continue
                if h > 0:
                    unavailable_hours[parsed] = h
            calendar_unavailable_hours = {}
            for kd, hv in (cfg.get("calendar_unavailable_hours", {}) or {}).items():
                parsed = _safe_date(kd)
                if parsed is None:
                    continue
                try:
                    h = float(hv)
                except Exception:
                    continue
                if h > 0:
                    calendar_unavailable_hours[parsed] = h
            start = _safe_date(cfg.get("start_date"))
            loaded[m] = {
                "weekdays": weekdays,
                "leave_dates": leave_dates,
                "start_date": date.today() if start is None else start,
                "unavailable_hours": unavailable_hours,
                "calendar_unavailable_hours": calendar_unavailable_hours,
            }
    for m in members:
        if m not in loaded:
            loaded[m] = defaults[m]
    st.session_state["member_settings"] = loaded

    ensure_calendar_sync_state()
    incoming_sync = payload.get("calendar_sync", {})
    if isinstance(incoming_sync, dict):
        sync = st.session_state.get("calendar_sync", _default_calendar_sync_state())
        sync.update(_calendar_state_clean_for_save(incoming_sync))
        st.session_state["calendar_sync"] = sync

def fetch_state_from_cloud() -> tuple[dict | None, str]:
    url, key, ready = get_supabase_config()
    if not ready:
        return None, "SUPABASE_URL or SUPABASE_ANON_KEY is missing in Streamlit secrets."
    state_id = get_active_state_id()
    endpoint = f"{url}/rest/v1/{SUPABASE_STATE_TABLE}"
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    params = {"select": "payload", "id": f"eq.{state_id}", "limit": "1"}
    try:
        resp = requests.get(endpoint, headers=headers, params=params, timeout=12)
        if resp.status_code >= 400:
            return None, f"Cloud load failed ({resp.status_code}): {resp.text[:180]}"
        rows = resp.json()
        if not rows:
            return None, f"No cloud snapshot found yet (dataset: {state_id})."
        payload = rows[0].get("payload")
        if not isinstance(payload, dict):
            return None, "Cloud payload is invalid."
        return payload, f"Cloud snapshot loaded (dataset: {state_id})."
    except Exception as exc:
        return None, f"Cloud load failed: {exc}"

def save_state_to_cloud() -> tuple[bool, str]:
    url, key, ready = get_supabase_config()
    if not ready:
        return False, "SUPABASE_URL or SUPABASE_ANON_KEY is missing in Streamlit secrets."
    state_id = get_active_state_id()
    endpoint = f"{url}/rest/v1/{SUPABASE_STATE_TABLE}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    body = [{"id": state_id, "payload": serialize_state_payload()}]
    try:
        resp = requests.post(endpoint, headers=headers, json=body, timeout=12)
        if resp.status_code >= 400:
            return False, f"Cloud save failed ({resp.status_code}): {resp.text[:180]}"
        return True, f"Saved to cloud (dataset: {state_id})."
    except Exception as exc:
        return False, f"Cloud save failed: {exc}"

def _graph_parse_datetime(dt_obj: dict | None) -> datetime | None:
    if not isinstance(dt_obj, dict):
        return None
    dt_raw = str(dt_obj.get("dateTime", "")).strip()
    if len(dt_raw) == 0:
        return None
    parsed = pd.to_datetime(dt_raw, errors="coerce")
    if pd.isna(parsed):
        return None
    dt_val = parsed.to_pydatetime()
    tz_raw = str(dt_obj.get("timeZone", "")).strip()
    if dt_val.tzinfo is None:
        if tz_raw:
            try:
                dt_val = dt_val.replace(tzinfo=ZoneInfo(tz_raw))
            except Exception:
                dt_val = dt_val.replace(tzinfo=timezone.utc)
        else:
            dt_val = dt_val.replace(tzinfo=timezone.utc)
    return dt_val.astimezone(timezone.utc)

def _calendar_state_clean_for_save(sync: dict) -> dict:
    clean = _default_calendar_sync_state()
    clean["provider"] = str(sync.get("provider", "microsoft"))
    clean["tenant_id"] = str(sync.get("tenant_id", ""))
    clean["client_id"] = str(sync.get("client_id", ""))
    clean["linked_email"] = str(sync.get("linked_email", ""))
    clean["access_token"] = str(sync.get("access_token", ""))
    clean["access_token_expires_at"] = "" if _safe_datetime(sync.get("access_token_expires_at")) is None else _safe_datetime(sync.get("access_token_expires_at")).isoformat()
    clean["refresh_token"] = str(sync.get("refresh_token", ""))
    clean["device_code"] = str(sync.get("device_code", ""))
    clean["device_expires_at"] = "" if _safe_datetime(sync.get("device_expires_at")) is None else _safe_datetime(sync.get("device_expires_at")).isoformat()
    clean["device_interval"] = _safe_int(sync.get("device_interval", 5) or 5, 5)
    clean["verification_uri"] = str(sync.get("verification_uri", ""))
    clean["user_code"] = str(sync.get("user_code", ""))
    clean["last_snapshot_at"] = "" if _safe_datetime(sync.get("last_snapshot_at")) is None else _safe_datetime(sync.get("last_snapshot_at")).isoformat()
    clean["last_snapshot_member"] = str(sync.get("last_snapshot_member", ""))
    clean["last_snapshot_event_count"] = _safe_int(sync.get("last_snapshot_event_count", 0) or 0, 0)
    clean["last_snapshot_hours"] = _safe_float(sync.get("last_snapshot_hours", 0.0) or 0.0, 0.0)
    clean["oauth_state"] = str(sync.get("oauth_state", ""))
    clean["oauth_code_verifier"] = str(sync.get("oauth_code_verifier", ""))
    clean["oauth_created_at"] = "" if _safe_datetime(sync.get("oauth_created_at")) is None else _safe_datetime(sync.get("oauth_created_at")).isoformat()
    return clean

def _code_challenge_s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

def build_microsoft_authorize_url() -> tuple[str | None, str]:
    cfg = get_microsoft_calendar_config()
    if not cfg["ready"]:
        if str(st.secrets.get("MS_CLIENT_ID", "")).strip():
            return None, "Set MS_REDIRECT_URI in Streamlit secrets to enable redirect login."
        return None, "Set MS_CLIENT_ID and MS_REDIRECT_URI in Streamlit secrets to enable redirect login."
    ensure_calendar_sync_state()
    sync = st.session_state["calendar_sync"]
    sync["provider"] = "microsoft"
    sync["tenant_id"] = cfg["tenant_id"]
    sync["client_id"] = cfg["client_id"]
    now = _utc_now()
    created = _safe_datetime(sync.get("oauth_created_at"))
    state_is_fresh = created is not None and created > now - timedelta(minutes=20)
    if not state_is_fresh or not str(sync.get("oauth_state", "")).strip():
        sync["oauth_state"] = pysecrets.token_urlsafe(24)
        sync["oauth_code_verifier"] = pysecrets.token_urlsafe(72)
        sync["oauth_created_at"] = now.isoformat()
    use_pkce = len(cfg["client_secret"]) == 0
    params = {
        "client_id": cfg["client_id"],
        "response_type": "code",
        "redirect_uri": cfg["redirect_uri"],
        "response_mode": "query",
        "scope": cfg["scope_text"],
        "state": str(sync.get("oauth_state", "")),
    }
    if use_pkce:
        verifier = str(sync.get("oauth_code_verifier", ""))
        if len(verifier) == 0:
            verifier = pysecrets.token_urlsafe(72)
            sync["oauth_code_verifier"] = verifier
            sync["oauth_created_at"] = now.isoformat()
        params["code_challenge"] = _code_challenge_s256(verifier)
        params["code_challenge_method"] = "S256"

    st.session_state["calendar_sync"] = sync
    auth_url = f"{cfg['authorize_url']}?{urlencode(params)}"
    return auth_url, "Open Microsoft login to link calendar."

def _store_graph_tokens(token_data: dict, clear_oauth: bool = True) -> None:
    ensure_calendar_sync_state()
    sync = st.session_state["calendar_sync"]
    sync["access_token"] = str(token_data.get("access_token", ""))
    sync["refresh_token"] = str(token_data.get("refresh_token", sync.get("refresh_token", "")))
    expires_in = _safe_int(token_data.get("expires_in", 3600) or 3600, 3600)
    sync["access_token_expires_at"] = (_utc_now() + timedelta(seconds=expires_in)).isoformat()
    if clear_oauth:
        sync["oauth_state"] = ""
        sync["oauth_code_verifier"] = ""
        sync["oauth_created_at"] = ""
    st.session_state["calendar_sync"] = sync

def _fetch_graph_identity(access_token: str) -> str:
    if len(access_token.strip()) == 0:
        return ""
    try:
        resp = requests.get(
            f"{MS_GRAPH_BASE_URL}/me?$select=mail,userPrincipalName",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        if resp.status_code >= 400:
            return ""
        data = resp.json()
    except Exception:
        return ""
    mail = str(data.get("mail", "")).strip()
    upn = str(data.get("userPrincipalName", "")).strip()
    return mail or upn

def _clear_oauth_query_params() -> None:
    for k in ["code", "state", "error", "error_description", "session_state"]:
        if k in st.query_params:
            del st.query_params[k]

def process_microsoft_oauth_callback_if_present() -> None:
    code = _query_param_str("code")
    err = _query_param_str("error")
    if len(code) == 0 and len(err) == 0:
        return

    if err:
        desc = _query_param_str("error_description")
        msg = f"Calendar link failed: {err}" if not desc else f"Calendar link failed: {desc}"
        st.session_state["calendar_sync_message"] = msg
        _clear_oauth_query_params()
        return

    cfg = get_microsoft_calendar_config()
    if not cfg["ready"]:
        st.session_state["calendar_sync_message"] = "Set MS_CLIENT_ID and MS_REDIRECT_URI in Streamlit secrets before linking."
        _clear_oauth_query_params()
        return

    ensure_calendar_sync_state()
    sync = st.session_state["calendar_sync"]
    returned_state = _query_param_str("state")
    expected_state = str(sync.get("oauth_state", "")).strip()
    if expected_state and returned_state and returned_state != expected_state:
        st.session_state["calendar_sync_message"] = "Calendar link failed: state mismatch. Click Link calander and try again."
        _clear_oauth_query_params()
        return

    token_body = {
        "client_id": cfg["client_id"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": cfg["redirect_uri"],
        "scope": cfg["scope_text"],
    }
    if len(cfg["client_secret"]) > 0:
        token_body["client_secret"] = cfg["client_secret"]
    else:
        verifier = str(sync.get("oauth_code_verifier", "")).strip()
        if len(verifier) == 0:
            st.session_state["calendar_sync_message"] = "Calendar link failed: missing PKCE verifier. Click Link calander and try again."
            _clear_oauth_query_params()
            return
        token_body["code_verifier"] = verifier

    try:
        token_resp = requests.post(cfg["token_url"], data=token_body, timeout=15)
        token_data = token_resp.json()
    except Exception as exc:
        st.session_state["calendar_sync_message"] = f"Calendar link failed: {exc}"
        _clear_oauth_query_params()
        return

    if token_resp.status_code >= 400 or not str(token_data.get("access_token", "")).strip():
        err_desc = str(token_data.get("error_description", token_data))[:220]
        st.session_state["calendar_sync_message"] = f"Calendar link failed ({token_resp.status_code}): {err_desc}"
        _clear_oauth_query_params()
        return

    _store_graph_tokens(token_data, clear_oauth=True)
    sync2 = st.session_state["calendar_sync"]
    identity = _fetch_graph_identity(sync2.get("access_token", ""))
    if identity:
        sync2["linked_email"] = identity
        st.session_state["calendar_sync"] = sync2
    st.session_state["calendar_sync_message"] = "Microsoft calendar linked."
    _clear_oauth_query_params()

def get_microsoft_access_token() -> tuple[str | None, str]:
    cfg = get_microsoft_calendar_config()
    if not cfg["ready"]:
        return None, "Set MS_CLIENT_ID and MS_REDIRECT_URI in Streamlit secrets to enable Microsoft calendar sync."

    ensure_calendar_sync_state()
    sync = st.session_state["calendar_sync"]
    sync["tenant_id"] = cfg["tenant_id"]
    sync["client_id"] = cfg["client_id"]
    st.session_state["calendar_sync"] = sync

    now = _utc_now()
    access_token = str(sync.get("access_token", ""))
    access_exp = _safe_datetime(sync.get("access_token_expires_at"))
    if access_token and access_exp is not None and access_exp > now + timedelta(minutes=2):
        return access_token, "Using existing Microsoft calendar token."

    refresh_token = str(sync.get("refresh_token", ""))
    if refresh_token:
        refresh_body = {
            "client_id": cfg["client_id"],
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": cfg["scope_text"],
        }
        if len(cfg["client_secret"]) > 0:
            refresh_body["client_secret"] = cfg["client_secret"]
        try:
            refresh_resp = requests.post(cfg["token_url"], data=refresh_body, timeout=15)
            refresh_data = refresh_resp.json()
        except Exception as exc:
            return None, f"Calendar token refresh failed: {exc}"
        if refresh_resp.status_code < 400 and str(refresh_data.get("access_token", "")).strip():
            _store_graph_tokens(refresh_data, clear_oauth=False)
            fresh_sync = st.session_state["calendar_sync"]
            identity = _fetch_graph_identity(fresh_sync.get("access_token", ""))
            if identity:
                fresh_sync["linked_email"] = identity
                st.session_state["calendar_sync"] = fresh_sync
            return fresh_sync.get("access_token", ""), "Microsoft calendar linked."

    return None, "Calendar not linked yet. Click Link calander and sign in with Microsoft."

def fetch_microsoft_calendar_events(access_token: str, start_dt: datetime, end_dt: datetime) -> tuple[list[dict] | None, str]:
    start_iso = start_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    end_iso = end_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Prefer": 'outlook.timezone="UTC"',
    }
    params = {
        "startDateTime": start_iso,
        "endDateTime": end_iso,
        "$select": "id,subject,start,end,isCancelled,showAs",
    }
    events: list[dict] = []
    next_url = f"{MS_GRAPH_BASE_URL}/me/calendarView"
    try:
        while next_url:
            if next_url.endswith("/calendarView"):
                resp = requests.get(next_url, headers=headers, params=params, timeout=20)
            else:
                resp = requests.get(next_url, headers=headers, timeout=20)
            data = resp.json()
            if resp.status_code >= 400:
                err = str(data.get("error", data))[:240]
                return None, f"Calendar fetch failed ({resp.status_code}): {err}"
            values = data.get("value", [])
            if isinstance(values, list):
                events.extend([v for v in values if isinstance(v, dict)])
            next_url = data.get("@odata.nextLink")
    except Exception as exc:
        return None, f"Calendar fetch failed: {exc}"
    return events, f"Fetched {len(events)} calendar events."

def map_events_to_daily_unavailable(events: list[dict], start_day: date, end_day: date) -> tuple[dict[date, float], int]:
    if end_day < start_day:
        return {}, 0
    range_start = datetime.combine(start_day, datetime.min.time(), tzinfo=timezone.utc)
    range_end = datetime.combine(end_day + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    totals: dict[date, float] = {}
    counted_events = 0
    for ev in events:
        if bool(ev.get("isCancelled", False)):
            continue
        show_as = str(ev.get("showAs", "")).strip().lower()
        if show_as == "free":
            continue
        st_dt = _graph_parse_datetime(ev.get("start"))
        en_dt = _graph_parse_datetime(ev.get("end"))
        if st_dt is None or en_dt is None or en_dt <= st_dt:
            continue
        st_dt = max(st_dt, range_start)
        en_dt = min(en_dt, range_end)
        if en_dt <= st_dt:
            continue
        counted_events += 1

        cursor = st_dt
        while cursor < en_dt:
            day_boundary = datetime.combine(cursor.date() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
            segment_end = min(en_dt, day_boundary)
            hrs = max((segment_end - cursor).total_seconds() / 3600.0, 0.0)
            if hrs > 0:
                totals[cursor.date()] = totals.get(cursor.date(), 0.0) + hrs
            cursor = segment_end
    return totals, counted_events

def resolve_calendar_target_member(members: list[str]) -> str | None:
    if len(members) == 0:
        return None
    secret_pref = str(st.secrets.get("MS_CALENDAR_MEMBER", "")).strip()
    if secret_pref in members:
        return secret_pref
    return members[0]

def refresh_microsoft_calendar_snapshot(target_member: str | None, horizon_days: int = MS_SNAPSHOT_HORIZON_DAYS) -> tuple[bool, str]:
    if target_member is None:
        return False, "No team member available for calendar sync."
    access_token, token_msg = get_microsoft_access_token()
    if access_token is None:
        return False, token_msg

    start_day = date.today()
    end_day = start_day + timedelta(days=max(int(horizon_days), 1))
    start_dt = datetime.combine(start_day, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_day + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

    events, fetch_msg = fetch_microsoft_calendar_events(access_token, start_dt, end_dt)
    if events is None:
        return False, fetch_msg
    unavailable_by_day, counted_events = map_events_to_daily_unavailable(events, start_day, end_day)

    ms = st.session_state.get("member_settings", {})
    cfg = ms.get(target_member, {})
    cfg["calendar_unavailable_hours"] = {d: float(h) for d, h in unavailable_by_day.items() if float(h) > 0.0}
    ms[target_member] = cfg
    st.session_state["member_settings"] = ms

    ensure_calendar_sync_state()
    sync = st.session_state["calendar_sync"]
    sync["last_snapshot_at"] = _utc_now().isoformat()
    sync["last_snapshot_member"] = target_member
    sync["last_snapshot_event_count"] = counted_events
    sync["last_snapshot_hours"] = float(sum(unavailable_by_day.values()))
    st.session_state["calendar_sync"] = sync

    return True, (
        f"Calendar snapshot refreshed for {target_member}: "
        f"{counted_events} events, {float(sum(unavailable_by_day.values())):.1f}h unavailable over next {horizon_days} days."
    )

def normalize_active_priorities(jobs: pd.DataFrame) -> pd.DataFrame:
    if jobs.empty:
        return jobs

    jobs = jobs.copy()
    jobs["Priority"] = pd.to_numeric(jobs["Priority"], errors="coerce").fillna(0).astype(int)

    active = jobs[jobs["Priority"] >= 1].copy()
    hold = jobs[jobs["Priority"] == 0].copy()

    if not active.empty:
        groups = []
        for member, g in active.groupby("Assignee", dropna=False, sort=False):
            g = g.copy()
            g["_row_order"] = range(len(g))
            ordered = []
            for _, row in g.sort_values("_row_order").iterrows():
                p = int(row["Priority"])
                if p < 1:
                    p = 1
                idx = p - 1
                if idx >= len(ordered):
                    ordered.append(row)
                else:
                    ordered.insert(idx, row)
            out = pd.DataFrame(ordered).reset_index(drop=True)
            out["Priority"] = range(1, len(out) + 1)
            out = out.drop(columns=["_row_order"], errors="ignore")
            groups.append(out)
        active = pd.concat(groups, ignore_index=True)

    if not hold.empty:
        hold = hold.reset_index(drop=True)

    return pd.concat([active, hold], ignore_index=True)

def _capacity_segments(capacity_days: list[tuple[date, float]]) -> tuple[list[tuple[int, date, float, float]], float]:
    segments: list[tuple[int, date, float, float]] = []
    running = 0.0
    for day_idx, (d, cap) in enumerate(capacity_days):
        cap_val = float(cap)
        if cap_val <= 1e-9:
            continue
        seg_start = running
        running = running + cap_val
        segments.append((day_idx, d, seg_start, running))
    return segments, running

def schedule_member_jobs(
    df_member_active: pd.DataFrame,
    start_date: date,
    daily_hours: float,
    weekdays: set[int],
    non_working_dates: set[date],
    unavailable_hours: dict | None = None,
) -> pd.DataFrame:
    df = df_member_active.copy()
    df = df.sort_values(["Priority", "Job name"], ascending=[True, True]).reset_index(drop=True)

    capacity_days = build_capacity_days(
        start_date,
        weekdays,
        non_working_dates,
        daily_hours,
        unavailable_hours=unavailable_hours,
        horizon_days=3650,
    )
    if len(capacity_days) == 0:
        raise ValueError("No working days available for this member calendar")
    segments, total_capacity = _capacity_segments(capacity_days)
    if total_capacity <= 1e-9 or len(segments) == 0:
        raise ValueError("No project capacity available for this member calendar")
    seg_ends = [seg_end for _, _, _, seg_end in segments]

    start_hour_index = []
    finish_hour_index = []
    running = 0.0
    for hrs in df["Required hours"].astype(float).tolist():
        start_hour_index.append(running)
        running = running + float(hrs)
        finish_hour_index.append(running)

    df["Start hour index"] = start_hour_index
    df["Finish hour index"] = finish_hour_index

    def hour_index_to_date(h: float) -> date:
        if h < 0:
            h = 0.0
        if h >= total_capacity:
            return segments[-1][1]
        seg_pos = bisect_right(seg_ends, h)
        if seg_pos >= len(segments):
            seg_pos = len(segments) - 1
        return segments[seg_pos][1]

    def finish_hour_to_date(h: float) -> date:
        eps = 1e-9
        return hour_index_to_date(max(h - eps, 0.0))

    df["Start date"] = [hour_index_to_date(h) for h in df["Start hour index"]]
    df["Finish date"] = [finish_hour_to_date(h) for h in df["Finish hour index"]]
    return df

def allocate_member_hours(
    schedule_df: pd.DataFrame,
    start_date: date,
    daily_hours: float,
    weekdays: set[int],
    non_working_dates: set[date],
    horizon_workdays: int = 20,
    unavailable_hours: dict | None = None,
) -> pd.DataFrame:
    capacity_days = build_capacity_days(
        start_date,
        weekdays,
        non_working_dates,
        daily_hours,
        unavailable_hours=unavailable_hours,
        horizon_days=3650,
    )
    capacity_days = capacity_days[:max(horizon_workdays, 1)]
    alloc = pd.DataFrame({"Date": [d for d, _ in capacity_days]})
    if len(capacity_days) == 0:
        alloc["Allocated hours"] = []
        alloc["Free hours"] = []
        return alloc
    capacity_vals = [float(c) for _, c in capacity_days]
    alloc["Allocated hours"] = 0.0
    segments, total_capacity = _capacity_segments(capacity_days)
    seg_ends = [seg_end for _, _, _, seg_end in segments]

    if schedule_df is None or schedule_df.empty:
        alloc["Free hours"] = capacity_vals
        return alloc

    for _, row in schedule_df.iterrows():
        if len(segments) == 0:
            break
        sh = float(row["Start hour index"])
        fh = float(row["Finish hour index"])
        if fh <= 0 or sh >= total_capacity:
            continue
        sh_clip = max(0.0, sh)
        fh_clip = min(fh, total_capacity)
        if fh_clip <= sh_clip:
            continue

        start_seg = bisect_right(seg_ends, sh_clip)
        end_seg = bisect_right(seg_ends, max(fh_clip - 1e-9, 0.0))
        if start_seg >= len(segments):
            continue
        if end_seg >= len(segments):
            end_seg = len(segments) - 1

        for seg_pos in range(start_seg, end_seg + 1):
            day_idx, _, seg_start, seg_end = segments[seg_pos]
            overlap = max(0.0, min(fh_clip, seg_end) - max(sh_clip, seg_start))
            if overlap <= 0.0:
                continue
            alloc.loc[day_idx, "Allocated hours"] = float(alloc.loc[day_idx, "Allocated hours"]) + overlap

    alloc["Free hours"] = (pd.Series(capacity_vals) - alloc["Allocated hours"]).clip(lower=0.0)
    return alloc

def build_day_job_details(
    schedule_df: pd.DataFrame,
    start_date: date,
    daily_hours: float,
    weekdays: set[int],
    non_working_dates: set[date],
    horizon_workdays: int = 20,
    unavailable_hours: dict | None = None,
) -> dict[date, list[str]]:
    capacity_days = build_capacity_days(
        start_date,
        weekdays,
        non_working_dates,
        daily_hours,
        unavailable_hours=unavailable_hours,
        horizon_days=3650,
    )
    capacity_days = capacity_days[:max(horizon_workdays, 1)]
    day_jobs = {d: [] for d, _ in capacity_days}

    if schedule_df is None or schedule_df.empty:
        return day_jobs

    segments, total_capacity = _capacity_segments(capacity_days)
    seg_ends = [seg_end for _, _, _, seg_end in segments]

    for _, row in schedule_df.iterrows():
        if len(segments) == 0:
            break
        sh = float(row["Start hour index"])
        fh = float(row["Finish hour index"])
        if fh <= 0 or sh >= total_capacity:
            continue
        sh_clip = max(0.0, sh)
        fh_clip = min(fh, total_capacity)
        if fh_clip <= sh_clip:
            continue
        start_seg = bisect_right(seg_ends, sh_clip)
        end_seg = bisect_right(seg_ends, max(fh_clip - 1e-9, 0.0))
        if start_seg >= len(segments):
            continue
        if end_seg >= len(segments):
            end_seg = len(segments) - 1
        job_name = str(row.get("Job name", "")).strip()
        for seg_pos in range(start_seg, end_seg + 1):
            _, seg_date, seg_start, seg_end = segments[seg_pos]
            overlap = max(0.0, min(fh_clip, seg_end) - max(sh_clip, seg_start))
            if overlap <= 0:
                continue
            name = job_name if job_name else "Unnamed job"
            day_jobs[seg_date].append(f"{name} ({overlap:.1f}h)")
    return day_jobs

def ordinal_day(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def month_start(d: date) -> date:
    return date(d.year, d.month, 1)

def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, 1)

def month_end(d: date) -> date:
    return add_months(month_start(d), 1) - timedelta(days=1)

def due_cutoff_hours(due_date: date, capacity_days: list[tuple[date, float]]) -> float:
    # Capacity available up to and including due_date, based on member calendar.
    total = 0.0
    for d, cap in capacity_days:
        if d > due_date:
            break
        total += float(cap)
    return total

def ensure_member_settings(members: list[str]) -> None:
    if "member_settings" not in st.session_state:
        st.session_state["member_settings"] = {}
    ms = st.session_state["member_settings"]
    for m in members:
        if m not in ms:
            ms[m] = {
                "weekdays": {0, 1, 2, 3, 4},
                "leave_dates": [],
                "start_date": date.today(),
                "unavailable_hours": {},
                "calendar_unavailable_hours": {},
            }
        if "weekdays" not in ms[m]:
            ms[m]["weekdays"] = {0, 1, 2, 3, 4}
        if "leave_dates" not in ms[m]:
            ms[m]["leave_dates"] = []
        if "start_date" not in ms[m]:
            ms[m]["start_date"] = date.today()
        if "unavailable_hours" not in ms[m] or not isinstance(ms[m]["unavailable_hours"], dict):
            ms[m]["unavailable_hours"] = {}
        if "calendar_unavailable_hours" not in ms[m] or not isinstance(ms[m]["calendar_unavailable_hours"], dict):
            ms[m]["calendar_unavailable_hours"] = {}
    for m in list(ms.keys()):
        if m not in members:
            del ms[m]

def clean_jobs_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(columns=JOB_COLS)

    df = df.copy()
    for c in JOB_COLS:
        if c not in df.columns:
            df[c] = None
    df = df[JOB_COLS]

    df = df.dropna(subset=["Job name", "Required hours", "Priority", "Assignee"], how="any")
    df = df[df["Job name"].astype(str).str.len() > 0]

    df["Required hours"] = pd.to_numeric(df["Required hours"], errors="coerce")
    df = df[df["Required hours"] >= 0]

    df["Priority"] = pd.to_numeric(df["Priority"], errors="coerce").fillna(0).astype(int)
    df["Assignee"] = df["Assignee"].astype(str)

    df["Due date"] = pd.to_datetime(df["Due date"], errors="coerce").dt.date
    df["Notes"] = df["Notes"].astype(str).replace("nan", "")

    return df.reset_index(drop=True)

init_local_state_if_missing()
cloud_load_key = f"cloud_load_attempted_{get_active_state_id()}"
if cloud_load_key not in st.session_state:
    st.session_state[cloud_load_key] = True
    payload, msg = fetch_state_from_cloud()
    st.session_state["cloud_sync_message"] = msg
    if payload is not None:
        apply_state_payload(payload)

process_microsoft_oauth_callback_if_present()

def add_status_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Status"] = df["Priority"].apply(lambda p: "Active" if int(p) >= 1 else "On hold")
    return df

def style_schedule(df: pd.DataFrame):
    def apply_styles(data: pd.DataFrame):
        styles = pd.DataFrame("", index=data.index, columns=data.columns)

        if "Status" in data.columns:
            for i in data.index:
                s = str(data.loc[i, "Status"])
                if s == "Active":
                    styles.loc[i, "Status"] = "background-color: rgba(46, 204, 113, 0.25);"
                else:
                    styles.loc[i, "Status"] = "background-color: rgba(231, 76, 60, 0.25);"

        if "Due date" in data.columns and "Finish date" in data.columns:
            for i in data.index:
                due = data.loc[i, "Due date"]
                fin = data.loc[i, "Finish date"]
                if pd.isna(due) or due is None or pd.isna(fin) or fin is None:
                    continue
                if fin < due:
                    styles.loc[i, "Due date"] = "background-color: rgba(46, 204, 113, 0.25);"
                elif fin == due:
                    styles.loc[i, "Due date"] = "background-color: rgba(241, 196, 15, 0.25);"
                else:
                    styles.loc[i, "Due date"] = "background-color: rgba(231, 76, 60, 0.25);"
        return styles
    styler = df.style.apply(apply_styles, axis=None)
    if "Required hours" in df.columns:
        styler = styler.format({"Required hours": "{:.1f}"})
    return styler

def render_kpi(label: str, value: str, note: str) -> None:
    st.markdown(
        (
            "<div class='kpi-card'>"
            f"<div class='kpi-head'>{label}</div>"
            f"<div class='kpi-value'>{value}</div>"
            f"<div class='metric-note'>{note}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

def _priority_signature(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(columns=["Assignee", "Job name", "Priority"])
    out = df.copy()
    for c in ["Assignee", "Job name", "Priority"]:
        if c not in out.columns:
            out[c] = None
    out = out[["Assignee", "Job name", "Priority"]].copy()
    out["Assignee"] = out["Assignee"].astype(str)
    out["Job name"] = out["Job name"].astype(str)
    out["Priority"] = pd.to_numeric(out["Priority"], errors="coerce").fillna(0).astype(int)
    return out.reset_index(drop=True)

def render_capacity_calendar(alloc: pd.DataFrame, start: date, end: date, weekdays: set[int], day_jobs: dict[date, list[str]] | None = None):
    free_map = {}
    alloc_map = {}
    for _, r in alloc.iterrows():
        d = r["Date"]
        free_map[d] = float(r.get("Free hours", 0.0))
        alloc_map[d] = float(r.get("Allocated hours", 0.0))
    day_jobs = day_jobs or {}

    first = start
    week_start = first - timedelta(days=first.weekday())
    last = end
    week_end = last + timedelta(days=(6 - last.weekday()))

    grid_days = []
    d = week_start
    while d <= week_end:
        grid_days.append(d)
        d = d + timedelta(days=1)

    rows = []
    for i in range(0, len(grid_days), 7):
        rows.append(grid_days[i:i+7])

    header = "".join([f"<th>{lab}</th>" for lab, _ in WEEKDAY_MAP])
    html = f"<table class='calendar-table'><thead><tr>{header}</tr></thead><tbody>"

    for week in rows:
        html += "<tr>"
        for d in week:
            in_range = (d >= start and d <= end)
            is_workday = d.weekday() in weekdays
            is_past = d < date.today()
            if not in_range:
                html += "<td style='background: rgba(49,51,63,0.02);'></td>"
                continue
            if is_past:
                html += f"<td style='background: rgba(49,51,63,0.03);'><div class='cal-date'>{ordinal_day(d.day)}</div><div class='mini'>Past day</div></td>"
                continue
            if not is_workday:
                html += f"<td style='background: rgba(49,51,63,0.03);'><div class='cal-date'>{ordinal_day(d.day)}</div><div class='mini'>Non working</div></td>"
                continue

            free = free_map.get(d, None)
            used = alloc_map.get(d, None)
            if free is None:
                html += f"<td><div class='cal-date'>{ordinal_day(d.day)}</div><span class='pill pill-amber'>No data</span></td>"
            else:
                used = 0.0 if used is None else used
                if used <= 0.001:
                    pill = "pill-green"
                elif free <= 0.001:
                    pill = "pill-red"
                else:
                    pill = "pill-amber"
                html += (
                    f"<td><div class='cal-date'>{ordinal_day(d.day)}</div>"
                    f"<span class='pill {pill}'>Free {free:.1f}h</span>"
                )
                jobs_today = day_jobs.get(d, [])
                if jobs_today:
                    jobs_html = "".join([f"<div class='mini-job'>{j}</div>" for j in jobs_today])
                    html += jobs_html
                html += "</td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

def render_leave_month_preview(anchor_month: date, leave_dates: set[date], unavailable_hours: dict[date, float] | None = None):
    unavailable_hours = unavailable_hours or {}
    start = month_start(anchor_month)
    end = month_end(anchor_month)
    week_start = start - timedelta(days=start.weekday())
    week_end = end + timedelta(days=(6 - end.weekday()))

    grid_days = []
    d = week_start
    while d <= week_end:
        grid_days.append(d)
        d = d + timedelta(days=1)
    rows = [grid_days[i:i+7] for i in range(0, len(grid_days), 7)]

    header = "".join([f"<th>{lab}</th>" for lab, _ in WEEKDAY_MAP])
    html = f"<table class='calendar-table'><thead><tr>{header}</tr></thead><tbody>"
    for week in rows:
        html += "<tr>"
        for d in week:
            in_month = (d.month == anchor_month.month and d.year == anchor_month.year)
            if not in_month:
                html += "<td style='background: rgba(49,51,63,0.02);'></td>"
                continue
            if d < date.today():
                html += f"<td style='background: rgba(49,51,63,0.03);'><div class='cal-date'>{ordinal_day(d.day)}</div><div class='mini'>Past day</div></td>"
                continue
            if d in leave_dates:
                html += f"<td><div class='cal-date'>{ordinal_day(d.day)}</div><span class='pill pill-red'>Non working</span></td>"
            elif d in unavailable_hours and float(unavailable_hours.get(d, 0.0)) > 0:
                html += f"<td><div class='cal-date'>{ordinal_day(d.day)}</div><span class='pill pill-amber'>Unavailable {float(unavailable_hours[d]):.1f}h</span></td>"
            else:
                html += f"<td><div class='cal-date'>{ordinal_day(d.day)}</div></td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown("<div class='leave-mini'>" + html + "</div>", unsafe_allow_html=True)

with st.sidebar:
    st.subheader("Team")

    st.markdown('<div class="table-shell">', unsafe_allow_html=True)
    team_df = st.data_editor(
        st.session_state["team"],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Member": st.column_config.TextColumn(required=True),
            "Daily hours": st.column_config.NumberColumn(min_value=1.0, max_value=24.0, step=0.5, required=True),
        },
        key="team_editor",
    )
    st.markdown('</div>', unsafe_allow_html=True)
    team_df = team_df.dropna(subset=["Member", "Daily hours"], how="any")
    team_df = team_df[team_df["Member"].astype(str).str.len() > 0].reset_index(drop=True)
    st.session_state["team"] = team_df

    st.divider()
    st.subheader("Cloud sync")
    if st.button("Save to cloud", use_container_width=True):
        ok, msg = save_state_to_cloud()
        st.session_state["cloud_sync_message"] = msg
        if ok:
            st.success(msg)
        else:
            st.error(msg)
    if st.button("Reload from cloud", use_container_width=True):
        payload, msg = fetch_state_from_cloud()
        st.session_state["cloud_sync_message"] = msg
        if payload is not None:
            apply_state_payload(payload)
            st.success(msg)
            st.rerun()
        else:
            st.info(msg)
    if "cloud_sync_message" in st.session_state:
        st.caption(f"Status: {st.session_state['cloud_sync_message']}")
    if st.button("Refresh outputs", key="refresh_outputs_btn_sidebar", use_container_width=True):
        st.session_state.pop("jobs_editor", None)
        staff_keys = [k for k in list(st.session_state.keys()) if str(k).startswith("member_jobs_editor_")]
        for k in staff_keys:
            st.session_state.pop(k, None)
        st.rerun()

    st.divider()
    st.subheader("Calander sync")
    sidebar_members = team_df["Member"].astype(str).tolist() if not team_df.empty else []
    sync_member = None
    if len(sidebar_members) > 0:
        default_sync_member = resolve_calendar_target_member(sidebar_members)
        default_idx = sidebar_members.index(default_sync_member) if default_sync_member in sidebar_members else 0
        sync_member = st.selectbox(
            "Snapshot member",
            options=sidebar_members,
            index=default_idx,
            key="calendar_sync_member_sidebar",
        )

    auth_url, auth_msg = build_microsoft_authorize_url()
    if auth_url:
        st.link_button("Link calander", auth_url, use_container_width=True)
    else:
        st.button("Link calander", key="link_calander_btn_sidebar_disabled", use_container_width=True, disabled=True)
        st.caption(auth_msg)

    if st.button("Refresh calander snapshot", key="refresh_calander_snapshot_btn_sidebar", use_container_width=True):
        ok, msg = refresh_microsoft_calendar_snapshot(sync_member)
        st.session_state["calendar_sync_message"] = msg
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    ensure_calendar_sync_state()
    sync_state = st.session_state.get("calendar_sync", {})
    linked_email = str(sync_state.get("linked_email", "")).strip()
    if linked_email:
        st.caption(f"Linked: {linked_email}")
    if "calendar_sync_message" in st.session_state:
        st.caption(f"Status: {st.session_state['calendar_sync_message']}")

    st.divider()
    st.subheader("Quickstart manual")
    if st.button("Open quickstart manual", key="open_quickstart_manual_sidebar", use_container_width=True):
        set_manual_mode(True)
        st.rerun()

team_members = team_df["Member"].astype(str).tolist() if not team_df.empty else []
member_hours = {row["Member"]: float(row["Daily hours"]) for _, row in team_df.iterrows()} if not team_df.empty else {}

if len(team_members) == 0:
    st.warning("Add at least 1 team member")
    st.stop()

ensure_member_settings(team_members)

tabs = st.tabs(["Team dashboard", "Staff pages", "Availability"])

with tabs[0]:
    st.markdown('<div class="section-title">Team dashboard</div>', unsafe_allow_html=True)
    st.subheader("All jobs input")
    st.caption("Priority 1 or higher means active, Priority 0 means on hold")

    preview_jobs = clean_jobs_df(st.session_state.get("jobs_raw", pd.DataFrame(columns=JOB_COLS)))
    active_count = int((preview_jobs["Priority"] >= 1).sum()) if not preview_jobs.empty else 0
    hold_count = int((preview_jobs["Priority"] == 0).sum()) if not preview_jobs.empty else 0
    total_count = int(len(preview_jobs))

    st.markdown('<div class="table-shell">', unsafe_allow_html=True)
    st.markdown(
        (
            "<div class='table-toolbar'>"
            "<div class='table-title'>Work Queue</div>"
            "<div class='table-meta'>"
            f"<span class='table-chip'>Total {total_count}</span>"
            f"<span class='table-chip table-chip-active'>Active {active_count}</span>"
            f"<span class='table-chip table-chip-hold'>On hold {hold_count}</span>"
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    jobs_input = st.data_editor(
        st.session_state["jobs_raw"],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Job name": st.column_config.TextColumn(required=True),
            "Required hours": st.column_config.NumberColumn(min_value=0.0, step=0.5, required=True),
            "Priority": st.column_config.NumberColumn(min_value=0, step=1, required=True),
            "Assignee": st.column_config.SelectboxColumn(options=team_members, required=True),
            "Due date": st.column_config.DateColumn(required=False),
            "Notes": st.column_config.TextColumn(required=False),
        },
        key="jobs_editor",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    jobs_clean = clean_jobs_df(jobs_input)
    jobs_norm = normalize_active_priorities(jobs_clean)
    st.session_state["jobs_raw"] = jobs_norm
    if not _priority_signature(jobs_norm).equals(_priority_signature(jobs_clean)):
        st.session_state.pop("jobs_editor", None)
        st.rerun()
    jobs_norm = add_status_columns(jobs_norm)

    st.divider()
    st.subheader("Schedule output")

    scheduled_all = []
    hold_rows = []
    member_working_cfg = {}
    member_active_sched = {}

    for member in team_members:
        ms = st.session_state["member_settings"][member]
        weekdays = ms["weekdays"]
        non_working = set(ms["leave_dates"])
        daily_hours = float(member_hours.get(member, 8.0))
        unavailable_hours = get_effective_unavailable_hours(ms, daily_hours)
        sdate = ms.get("start_date", date.today())
        member_working_cfg[member] = {
            "capacity_days": build_capacity_days(
                sdate,
                weekdays,
                non_working,
                daily_hours,
                unavailable_hours=unavailable_hours,
                horizon_days=3650,
            ),
            "daily_hours": daily_hours,
            "weekdays": weekdays,
            "non_working": non_working,
            "unavailable_hours": unavailable_hours,
            "sdate": sdate,
        }

        member_jobs = jobs_norm[jobs_norm["Assignee"] == member].copy()
        if member_jobs.empty:
            continue

        active = member_jobs[member_jobs["Priority"] >= 1].copy()
        hold = member_jobs[member_jobs["Priority"] == 0].copy()
        if not hold.empty:
            hold_rows.append(hold)

        if active.empty:
            continue

        sched = schedule_member_jobs(
            active,
            sdate,
            daily_hours,
            weekdays,
            non_working,
            unavailable_hours=unavailable_hours,
        )
        sched["Assignee"] = member
        scheduled_all.append(sched)
        member_active_sched[member] = sched.copy()

    show_frames = []
    if len(scheduled_all) > 0:
        scheduled = pd.concat(scheduled_all, ignore_index=True)
        scheduled = add_status_columns(scheduled)
        show_active = scheduled[["Assignee","Job name","Priority","Status","Required hours","Start date","Finish date","Due date","Notes"]].copy()
        show_frames.append(show_active)

    if len(hold_rows) > 0:
        hold_all = pd.concat(hold_rows, ignore_index=True)
        hold_all = add_status_columns(hold_all)
        hold_all["Start date"] = None
        hold_all["Finish date"] = None
        show_hold = hold_all[["Assignee","Job name","Priority","Status","Required hours","Start date","Finish date","Due date","Notes"]].copy()
        show_frames.append(show_hold)

    if len(show_frames) == 0:
        st.info("No jobs to schedule yet")
        st.stop()

    show = pd.concat(show_frames, ignore_index=True)
    show = show.sort_values(["Assignee","Status","Priority","Job name"], ascending=[True, True, True, True]).reset_index(drop=True)

    active_only = show[show["Status"] == "Active"].copy()
    overtime_needed_hours = 0.0
    overtime_members = set()
    overtime_due_dates = []
    # Compute overtime as max deficit per member (not sum per job) to avoid double-counting.
    for member, sched_member in member_active_sched.items():
        if sched_member is None or sched_member.empty:
            continue
        cfg = member_working_cfg.get(member, {})
        capacity_days = cfg.get("capacity_days", [])
        if not capacity_days:
            continue

        due_rows = sched_member.dropna(subset=["Due date"]).copy()
        if due_rows.empty:
            continue

        member_max_deficit = 0.0
        for _, row in due_rows.iterrows():
            due = row.get("Due date")
            cutoff = due_cutoff_hours(due, capacity_days)
            finish_h = float(row.get("Finish hour index", 0.0))
            deficit = max(0.0, finish_h - cutoff)
            if deficit > member_max_deficit:
                member_max_deficit = deficit
            if deficit > 0.0:
                overtime_due_dates.append(due)

        overtime_needed_hours += member_max_deficit
        if member_max_deficit > 0.0:
            overtime_members.add(member)

    def compute_offset_capacity_until(cutoff_date: date) -> float:
        total = 0.0
        # Use all team members except overloaded ones so idle capacity is counted.
        helper_members = [m for m in team_members if m not in overtime_members]
        for member in helper_members:
            cfg = member_working_cfg.get(member, {})
            weekdays = cfg.get("weekdays", st.session_state["member_settings"][member]["weekdays"])
            non_working = set(cfg.get("non_working", set(st.session_state["member_settings"][member]["leave_dates"])))
            sdate = cfg.get("sdate", st.session_state["member_settings"][member].get("start_date", date.today()))
            daily_hours = float(cfg.get("daily_hours", member_hours.get(member, 8.0)))
            unavailable_hours = cfg.get(
                "unavailable_hours",
                get_effective_unavailable_hours(st.session_state["member_settings"][member], daily_hours),
            )
            sched_member = member_active_sched.get(member, pd.DataFrame())

            capacity_days = cfg.get("capacity_days")
            if capacity_days is None:
                capacity_days = build_capacity_days(
                    sdate,
                    weekdays,
                    non_working,
                    daily_hours,
                    unavailable_hours=unavailable_hours,
                    horizon_days=3650,
                )
            horizon_workdays = len([d for d, _ in capacity_days if d <= cutoff_date])
            if horizon_workdays <= 0:
                continue

            alloc = allocate_member_hours(
                sched_member,
                sdate,
                daily_hours,
                weekdays,
                non_working,
                horizon_workdays=horizon_workdays,
                unavailable_hours=unavailable_hours,
            )
            alloc = alloc[(alloc["Date"] >= date.today()) & (alloc["Date"] <= cutoff_date)].copy()
            if not alloc.empty:
                total += float(alloc["Free hours"].sum())
        return total

    offset_capacity_hours = 0.0
    offset_before_first_overtime_hours = 0.0
    if overtime_needed_hours > 0 and len(overtime_due_dates) > 0:
        offset_capacity_hours = compute_offset_capacity_until(max(overtime_due_dates))
        offset_before_first_overtime_hours = compute_offset_capacity_until(min(overtime_due_dates))

    due_tracked = active_only.dropna(subset=["Due date", "Finish date"]).copy() if not active_only.empty else pd.DataFrame()
    if due_tracked.empty:
        on_time_pct_text = "N/A"
        on_time_note = "Set due dates to track on-time %"
    else:
        on_time_count = int((due_tracked["Finish date"] <= due_tracked["Due date"]).sum())
        on_time_pct = (on_time_count / len(due_tracked)) * 100.0
        on_time_pct_text = f"{on_time_pct:.0f}%"
        on_time_note = f"{on_time_count} of {len(due_tracked)} due-dated active jobs on time"

    if overtime_needed_hours <= 0:
        health_label = "Healthy"
        health_note = "No overtime currently required"
        dot_class = "dot-healthy"
    elif overtime_needed_hours > offset_before_first_overtime_hours and overtime_needed_hours > offset_capacity_hours:
        health_label = "Critical"
        health_note = "Offset capacity is below overtime needed"
        dot_class = "dot-critical"
    elif overtime_needed_hours > offset_before_first_overtime_hours:
        health_label = "Warning"
        health_note = "Overtime required to achieve due dates; immediate rebalance needed"
        dot_class = "dot-warning"
    else:
        health_label = "Early warning"
        health_note = "Resource overload; consider reallocation"
        dot_class = "dot-early"

    cols = st.columns([1,1,1,1,1])
    with cols[0]:
        if overtime_needed_hours <= 0:
            render_kpi("Offset before first overtime (hrs)", "-", "No overtime currently required")
        else:
            render_kpi(
                "Offset before first overtime (hrs)",
                f"{offset_before_first_overtime_hours:.1f}",
                "Free hours from other team members before first overtime due date",
            )
    with cols[1]:
        if overtime_needed_hours <= 0:
            render_kpi("Offset capacity (hrs)", "-", "No overtime currently required")
        else:
            render_kpi(
                "Offset capacity (hrs)",
                f"{offset_capacity_hours:.1f}",
                "Free hours from other team members before overtime due dates",
            )
    with cols[2]:
        render_kpi(
            "Overtime needed (hrs)",
            f"{overtime_needed_hours:.1f}",
            "Additional hours needed to recover overdue due-dated active jobs",
        )
    with cols[3]:
        render_kpi("On-time jobs %", on_time_pct_text, on_time_note)
    with cols[4]:
        st.markdown(
            (
                "<div class='kpi-card'>"
                "<div class='kpi-head'>Delivery health</div>"
                f"<div class='kpi-health-value'><span class='health-dot {dot_class}'></span>{health_label}</div>"
                f"<div class='metric-note'>{health_note}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    st.markdown('<div class="table-shell">', unsafe_allow_html=True)
    st.dataframe(style_schedule(show), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("Export")
    csv_bytes = show.to_csv(index=False).encode("utf-8")
    st.download_button("Download schedule CSV", data=csv_bytes, file_name="hydraulic_resourcing_schedule.csv", mime="text/csv")

with tabs[1]:
    st.markdown('<div class="section-title">Staff pages</div>', unsafe_allow_html=True)
    selected_member = st.selectbox("Select staff member", options=team_members, index=0)

    left, right = st.columns([1, 2])

    with left:
        st.write("Calendar")

        s_key = f"start_{selected_member}"
        if s_key not in st.session_state:
            st.session_state[s_key] = st.session_state["member_settings"][selected_member].get("start_date", date.today())
        sdate = st.date_input("Schedule start date", value=st.session_state[s_key], key=s_key)
        st.session_state["member_settings"][selected_member]["start_date"] = sdate

        weekday_labels = [INT_TO_LABEL[i] for i in sorted(list(st.session_state["member_settings"][selected_member]["weekdays"]))]
        chosen = st.multiselect(
            "Working weekdays",
            options=[k for k, _ in WEEKDAY_MAP],
            default=weekday_labels,
            key=f"weekdays_{selected_member}",
        )
        st.session_state["member_settings"][selected_member]["weekdays"] = set(LABEL_TO_INT[x] for x in chosen)

        st.caption("Leave dates and shutdown dates")
        st.markdown('<div class="table-shell" style="padding:6px;">', unsafe_allow_html=True)
        st.markdown('<div class="leave-cal">', unsafe_allow_html=True)
        leave_month_key = f"leave_month_{selected_member}"
        if leave_month_key not in st.session_state:
            st.session_state[leave_month_key] = month_start(date.today())
        st.session_state[leave_month_key] = month_start(st.session_state[leave_month_key])

        nav_l, nav_c, nav_r = st.columns([0.75, 3.6, 0.75], gap="small")
        with nav_l:
            if st.button("◀", key=f"leave_prev_{selected_member}", use_container_width=True):
                st.session_state[leave_month_key] = add_months(st.session_state[leave_month_key], -1)
                st.rerun()
        with nav_c:
            st.markdown(
                f"<div class='cal-nav'>{st.session_state[leave_month_key].strftime('%B %Y')}</div>",
                unsafe_allow_html=True,
            )
        with nav_r:
            if st.button("▶", key=f"leave_next_{selected_member}", use_container_width=True):
                st.session_state[leave_month_key] = add_months(st.session_state[leave_month_key], 1)
                st.rerun()

        leave_set = set()
        for d in st.session_state["member_settings"][selected_member]["leave_dates"]:
            parsed = pd.to_datetime(d, errors="coerce")
            if pd.notna(parsed):
                leave_set.add(parsed.date())
        manual_unavailable_map = {}
        for kd, hv in (st.session_state["member_settings"][selected_member].get("unavailable_hours", {}) or {}).items():
            parsed = pd.to_datetime(kd, errors="coerce")
            if pd.isna(parsed):
                continue
            try:
                hours_val = float(hv)
            except Exception:
                continue
            if hours_val > 0:
                manual_unavailable_map[parsed.date()] = hours_val
        selected_daily_hours = float(member_hours.get(selected_member, 8.0))
        preview_unavailable_map = get_effective_unavailable_hours(
            st.session_state["member_settings"][selected_member],
            selected_daily_hours,
        )

        render_leave_month_preview(st.session_state[leave_month_key], leave_set, unavailable_hours=preview_unavailable_map)

        pick_key = f"leave_pick_{selected_member}"
        if pick_key not in st.session_state:
            st.session_state[pick_key] = date.today()
        picked = st.date_input("Select day to update", value=st.session_state[pick_key], key=pick_key)
        picked_date = pd.to_datetime(picked, errors="coerce").date()
        unavail_hours = st.number_input(
            "Unavailable hours for selected day",
            min_value=0.0,
            max_value=24.0,
            step=0.5,
            value=float(manual_unavailable_map.get(picked_date, 0.0)),
            key=f"unavail_hours_input_{selected_member}",
        )
        act1, act2, act3 = st.columns(3, gap="small")
        with act1:
            if st.button("Mark non-working", key=f"leave_mark_off_{selected_member}", use_container_width=True):
                leave_set.add(picked_date)
                if picked_date in manual_unavailable_map:
                    del manual_unavailable_map[picked_date]
                st.session_state["member_settings"][selected_member]["leave_dates"] = sorted(list(leave_set))
                st.session_state["member_settings"][selected_member]["unavailable_hours"] = manual_unavailable_map
                st.rerun()
        with act2:
            if st.button("Mark working", key=f"leave_mark_on_{selected_member}", use_container_width=True):
                if picked_date in leave_set:
                    leave_set.remove(picked_date)
                if picked_date in manual_unavailable_map:
                    del manual_unavailable_map[picked_date]
                st.session_state["member_settings"][selected_member]["leave_dates"] = sorted(list(leave_set))
                st.session_state["member_settings"][selected_member]["unavailable_hours"] = manual_unavailable_map
                st.rerun()
        with act3:
            if st.button("Mark unavailable", key=f"leave_mark_unavailable_{selected_member}", use_container_width=True):
                if picked_date in leave_set:
                    leave_set.remove(picked_date)
                if float(unavail_hours) <= 0:
                    if picked_date in manual_unavailable_map:
                        del manual_unavailable_map[picked_date]
                else:
                    manual_unavailable_map[picked_date] = float(unavail_hours)
                st.session_state["member_settings"][selected_member]["leave_dates"] = sorted(list(leave_set))
                st.session_state["member_settings"][selected_member]["unavailable_hours"] = manual_unavailable_map
                st.rerun()

        st.caption("Use buttons to mark full non-working days, clear to working, or set partial unavailable hours.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.write("Jobs for selected staff member")

        jobs_all = clean_jobs_df(st.session_state.get("jobs_raw", pd.DataFrame(columns=JOB_COLS)))
        member_jobs = jobs_all[jobs_all["Assignee"] == selected_member].copy()
        if member_jobs.empty:
            member_jobs = pd.DataFrame(columns=JOB_COLS)
        active_count_staff = int((member_jobs["Priority"] >= 1).sum()) if not member_jobs.empty else 0
        hold_count_staff = int((member_jobs["Priority"] == 0).sum()) if not member_jobs.empty else 0
        total_count_staff = int(len(member_jobs))

        editor_key = f"member_jobs_editor_{selected_member}"
        st.markdown('<div class="table-shell">', unsafe_allow_html=True)
        st.markdown(
            (
                "<div class='table-toolbar'>"
                f"<div class='table-title'>{selected_member} queue</div>"
                "<div class='table-meta'>"
                f"<span class='table-chip'>Total {total_count_staff}</span>"
                f"<span class='table-chip table-chip-active'>Active {active_count_staff}</span>"
                f"<span class='table-chip table-chip-hold'>On hold {hold_count_staff}</span>"
                "</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        edited = st.data_editor(
            member_jobs,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Job name": st.column_config.TextColumn(required=True),
                "Required hours": st.column_config.NumberColumn(min_value=0.0, step=0.5, required=True),
                "Priority": st.column_config.NumberColumn(min_value=0, step=1, required=True),
                "Assignee": st.column_config.SelectboxColumn(options=[selected_member], required=True),
                "Due date": st.column_config.DateColumn(required=False),
                "Notes": st.column_config.TextColumn(required=False),
            },
            key=editor_key,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        edited = clean_jobs_df(edited)
        if not edited.empty:
            edited["Assignee"] = selected_member

        jobs_all = jobs_all[jobs_all["Assignee"] != selected_member].copy()
        combined_clean = clean_jobs_df(pd.concat([jobs_all, edited], ignore_index=True))
        combined_norm = normalize_active_priorities(combined_clean)
        st.session_state["jobs_raw"] = combined_norm
        selected_norm = combined_norm[combined_norm["Assignee"] == selected_member][JOB_COLS].reset_index(drop=True)
        edited_cmp = edited[JOB_COLS].reset_index(drop=True)
        selected_norm_cmp = clean_jobs_df(selected_norm).reset_index(drop=True)
        edited_norm_cmp = clean_jobs_df(edited_cmp).reset_index(drop=True)
        if len(selected_norm_cmp) == 0 and len(edited_norm_cmp) == 0:
            pass
        elif not _priority_signature(selected_norm_cmp).equals(_priority_signature(edited_norm_cmp)):
            st.session_state.pop(editor_key, None)
            st.rerun()

        ms = st.session_state["member_settings"][selected_member]
        weekdays = ms["weekdays"]
        non_working = set(ms["leave_dates"])
        daily_hours = float(member_hours.get(selected_member, 8.0))
        unavailable_hours = get_effective_unavailable_hours(ms, daily_hours)

        jobs_norm = normalize_active_priorities(clean_jobs_df(combined_norm))
        jobs_norm = add_status_columns(jobs_norm)
        member_norm = jobs_norm[jobs_norm["Assignee"] == selected_member].copy()

        active = member_norm[member_norm["Priority"] >= 1].copy()
        hold = member_norm[member_norm["Priority"] == 0].copy()
        hold["Start date"] = None
        hold["Finish date"] = None

        frames = []
        if not active.empty:
            sched = schedule_member_jobs(
                active,
                ms.get("start_date", date.today()),
                daily_hours,
                weekdays,
                non_working,
                unavailable_hours=unavailable_hours,
            )
            sched = add_status_columns(sched)
            frames.append(sched)
        if not hold.empty:
            frames.append(hold)

        if len(frames) == 0:
            st.info("No jobs for this member")
        else:
            view = pd.concat(frames, ignore_index=True)
            view = view[["Job name","Priority","Status","Required hours","Start date","Finish date","Due date","Notes"]].copy()
            view = view.sort_values(["Status","Priority","Job name"], ascending=[True, True, True]).reset_index(drop=True)
            st.markdown('<div class="table-shell">', unsafe_allow_html=True)
            st.dataframe(style_schedule(view), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    st.markdown('<div class="section-title">Availability</div>', unsafe_allow_html=True)
    st.caption("Next available date for active work, and next available date if on hold backlog is scheduled after active work")

    jobs_all = clean_jobs_df(st.session_state.get("jobs_raw", pd.DataFrame(columns=JOB_COLS)))
    jobs_norm = normalize_active_priorities(jobs_all)
    jobs_norm = add_status_columns(jobs_norm)

    rows = []
    member_context = {}

    for member in team_members:
        ms = st.session_state["member_settings"][member]
        weekdays = ms["weekdays"]
        non_working = set(ms["leave_dates"])
        daily_hours = float(member_hours.get(member, 8.0))
        unavailable_hours = get_effective_unavailable_hours(ms, daily_hours)
        sdate = ms.get("start_date", date.today())

        member_jobs = jobs_norm[jobs_norm["Assignee"] == member].copy()
        active = member_jobs[member_jobs["Priority"] >= 1].copy()
        hold = member_jobs[member_jobs["Priority"] == 0].copy()
        if not hold.empty:
            hold = hold.sort_values(["Due date","Job name"], ascending=[True, True])

        if active.empty:
            next_free_active = sdate
            sched_active = pd.DataFrame()
        else:
            sched_active = schedule_member_jobs(
                active,
                sdate,
                daily_hours,
                weekdays,
                non_working,
                unavailable_hours=unavailable_hours,
            )
            last_finish = max(sched_active["Finish date"].tolist())
            future_caps = build_capacity_days(
                last_finish + timedelta(days=1),
                weekdays,
                non_working,
                daily_hours,
                unavailable_hours=unavailable_hours,
                horizon_days=3650,
            )
            future_days = [d for d, cap in future_caps if cap > 1e-9]
            next_free_active = future_days[0] if len(future_days) else last_finish + timedelta(days=1)

        if active.empty and hold.empty:
            next_free_all = sdate
            sched_all = pd.DataFrame()
        else:
            if not active.empty:
                if not hold.empty:
                    maxp = int(active["Priority"].max())
                    hold2 = hold.copy()
                    hold2["Priority"] = range(maxp + 1, maxp + 1 + len(hold2))
                    combined = pd.concat([active, hold2], ignore_index=True)
                else:
                    combined = active.copy()
            else:
                combined = hold.copy()
                combined["Priority"] = range(1, len(combined) + 1)

            combined = combined.sort_values(["Priority","Job name"], ascending=[True, True])
            sched_all = schedule_member_jobs(
                combined,
                sdate,
                daily_hours,
                weekdays,
                non_working,
                unavailable_hours=unavailable_hours,
            )
            last_finish_all = max(sched_all["Finish date"].tolist())
            future_caps_all = build_capacity_days(
                last_finish_all + timedelta(days=1),
                weekdays,
                non_working,
                daily_hours,
                unavailable_hours=unavailable_hours,
                horizon_days=3650,
            )
            future_days_all = [d for d, cap in future_caps_all if cap > 1e-9]
            next_free_all = future_days_all[0] if len(future_days_all) else last_finish_all + timedelta(days=1)

        member_context[member] = {
            "sched_active": sched_active if isinstance(sched_active, pd.DataFrame) else pd.DataFrame(),
            "sched_all": sched_all if isinstance(sched_all, pd.DataFrame) else pd.DataFrame(),
            "sdate": sdate,
            "weekdays": weekdays,
            "non_working": non_working,
            "daily_hours": daily_hours,
            "unavailable_hours": unavailable_hours,
        }

        rows.append(
            {
                "Member": member,
                "Next available date, active only": next_free_active,
                "Next available date, including on hold backlog": next_free_all,
            }
        )

    summary = pd.DataFrame(rows).sort_values(["Member"]).reset_index(drop=True)
    st.markdown('<div class="table-shell">', unsafe_allow_html=True)
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("Capacity calendar")

    chosen_member = st.selectbox("Member", options=team_members, index=0, key="avail_member")
    mode = st.radio("Mode", options=["Active only", "Active plus on hold backlog"], horizontal=True)

    ctx = member_context[chosen_member]
    sdate = ctx["sdate"]
    weekdays = ctx["weekdays"]
    non_working = ctx["non_working"]
    daily_hours = ctx["daily_hours"]
    unavailable_hours = ctx.get("unavailable_hours", {})

    month_key = "avail_month_anchor"
    if month_key not in st.session_state:
        st.session_state[month_key] = month_start(sdate)
    st.session_state[month_key] = month_start(st.session_state[month_key])

    nav1, nav2, nav3 = st.columns([1, 5, 1])
    with nav1:
        if st.button("◀", key="avail_prev_month", use_container_width=True):
            st.session_state[month_key] = add_months(st.session_state[month_key], -1)
            st.rerun()
    with nav2:
        st.markdown(f"<div class='cal-nav'>{st.session_state[month_key].strftime('%B %Y')}</div>", unsafe_allow_html=True)
    with nav3:
        if st.button("▶", key="avail_next_month", use_container_width=True):
            st.session_state[month_key] = add_months(st.session_state[month_key], 1)
            st.rerun()

    view_start = month_start(st.session_state[month_key])
    view_end = month_end(st.session_state[month_key])

    all_capacity_days = build_capacity_days(
        sdate,
        weekdays,
        non_working,
        daily_hours,
        unavailable_hours=unavailable_hours,
        horizon_days=3650,
    )
    horizon_workdays = max(1, len([d for d, _ in all_capacity_days if d <= view_end]))

    sched_used = ctx["sched_active"] if mode == "Active only" else ctx["sched_all"]
    alloc = allocate_member_hours(
        sched_used,
        sdate,
        daily_hours,
        weekdays,
        non_working,
        horizon_workdays=horizon_workdays,
        unavailable_hours=unavailable_hours,
    )
    day_jobs = build_day_job_details(
        sched_used,
        sdate,
        daily_hours,
        weekdays,
        non_working,
        horizon_workdays=horizon_workdays,
        unavailable_hours=unavailable_hours,
    )

    if len(all_capacity_days) == 0:
        st.info("No working days available for this member")
    else:
        render_capacity_calendar(alloc, view_start, view_end, weekdays, day_jobs=day_jobs)
