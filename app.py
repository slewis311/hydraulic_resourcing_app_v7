import streamlit as st
import requests

def require_login():
    st.set_page_config(page_title="Hydraulic Resourcing App", layout="wide")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return

    st.markdown(
        '''
        <style>
          .login-wrap { max-width: 520px; margin: 5vh auto 0 auto; }
          .login-card { border: 1px solid rgba(49, 51, 63, 0.12); border-radius: 16px; padding: 18px 18px; background: white; }
          .login-title { font-size: 1.6rem; font-weight: 750; margin-bottom: 0.2rem; }
          .login-sub { color: rgba(49, 51, 63, 0.70); margin-bottom: 1rem; }
        </style>
        ''',
        unsafe_allow_html=True
    )

    st.markdown('<div class="login-wrap"><div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Hydraulic Resourcing App</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-sub">Admin login required</div>', unsafe_allow_html=True)

    pwd = st.text_input("Password", type="password")
    col1, col2 = st.columns([1, 2])
    with col1:
        sign_in = st.button("Sign in", use_container_width=True)
    with col2:
        st.caption("Set APP_PASSWORD in Streamlit secrets")

    if sign_in:
        expected = st.secrets.get("APP_PASSWORD", "")
        if expected and pwd == expected:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

require_login()

import pandas as pd
from datetime import date, timedelta

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
      .cal-date { font-weight: 680; font-size: 0.85rem; margin-bottom: 6px; color: #1f3c4f; }
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
        color: #1c5b72;
        background: linear-gradient(90deg, rgba(36,167,179,0.18), rgba(239,231,63,0.28));
        border: 1px solid rgba(31,126,151,0.25);
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
SUPABASE_STATE_ID = "main"

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

def get_supabase_config() -> tuple[str, str, bool]:
    url = st.secrets.get("SUPABASE_URL", "").strip().rstrip("/")
    key = st.secrets.get("SUPABASE_ANON_KEY", "").strip()
    return url, key, bool(url and key)

def _safe_date(value) -> date | None:
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.date()

def _default_member_settings(members: list[str]) -> dict:
    out = {}
    for m in members:
        out[m] = {"weekdays": {0, 1, 2, 3, 4}, "leave_dates": [], "start_date": date.today()}
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
        start = _safe_date(cfg.get("start_date", date.today()))
        settings_records[str(member)] = {
            "weekdays": weekdays,
            "leave_dates": leave_dates,
            "start_date": date.today().isoformat() if start is None else start.isoformat(),
        }

    return {"team": team_records, "jobs_raw": jobs_records, "member_settings": settings_records}

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
            start = _safe_date(cfg.get("start_date"))
            loaded[m] = {
                "weekdays": weekdays,
                "leave_dates": leave_dates,
                "start_date": date.today() if start is None else start,
            }
    for m in members:
        if m not in loaded:
            loaded[m] = defaults[m]
    st.session_state["member_settings"] = loaded

def fetch_state_from_cloud() -> tuple[dict | None, str]:
    url, key, ready = get_supabase_config()
    if not ready:
        return None, "SUPABASE_URL or SUPABASE_ANON_KEY is missing in Streamlit secrets."
    endpoint = f"{url}/rest/v1/{SUPABASE_STATE_TABLE}"
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    params = {"select": "payload", "id": f"eq.{SUPABASE_STATE_ID}", "limit": "1"}
    try:
        resp = requests.get(endpoint, headers=headers, params=params, timeout=12)
        if resp.status_code >= 400:
            return None, f"Cloud load failed ({resp.status_code}): {resp.text[:180]}"
        rows = resp.json()
        if not rows:
            return None, "No cloud snapshot found yet."
        payload = rows[0].get("payload")
        if not isinstance(payload, dict):
            return None, "Cloud payload is invalid."
        return payload, "Cloud snapshot loaded."
    except Exception as exc:
        return None, f"Cloud load failed: {exc}"

def save_state_to_cloud() -> tuple[bool, str]:
    url, key, ready = get_supabase_config()
    if not ready:
        return False, "SUPABASE_URL or SUPABASE_ANON_KEY is missing in Streamlit secrets."
    endpoint = f"{url}/rest/v1/{SUPABASE_STATE_TABLE}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    body = [{"id": SUPABASE_STATE_ID, "payload": serialize_state_payload()}]
    try:
        resp = requests.post(endpoint, headers=headers, json=body, timeout=12)
        if resp.status_code >= 400:
            return False, f"Cloud save failed ({resp.status_code}): {resp.text[:180]}"
        return True, "Saved to cloud."
    except Exception as exc:
        return False, f"Cloud save failed: {exc}"

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

def schedule_member_jobs(df_member_active: pd.DataFrame, start_date: date, daily_hours: float, weekdays: set[int], non_working_dates: set[date]) -> pd.DataFrame:
    df = df_member_active.copy()
    df = df.sort_values(["Priority", "Job name"], ascending=[True, True]).reset_index(drop=True)

    working_dates = build_working_dates(start_date, weekdays, non_working_dates, horizon_days=3650)
    if len(working_dates) == 0:
        raise ValueError("No working days available for this member calendar")

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
        day_index = int(h // daily_hours)
        if day_index < 0:
            day_index = 0
        if day_index >= len(working_dates):
            return working_dates[-1]
        return working_dates[day_index]

    def finish_hour_to_date(h: float) -> date:
        eps = 1e-9
        return hour_index_to_date(max(h - eps, 0.0))

    df["Start date"] = [hour_index_to_date(h) for h in df["Start hour index"]]
    df["Finish date"] = [finish_hour_to_date(h) for h in df["Finish hour index"]]
    return df

def allocate_member_hours(schedule_df: pd.DataFrame, start_date: date, daily_hours: float, weekdays: set[int], non_working_dates: set[date], horizon_workdays: int = 20) -> pd.DataFrame:
    working_dates = build_working_dates(start_date, weekdays, non_working_dates, horizon_days=3650)
    working_dates = working_dates[:max(horizon_workdays, 1)]
    alloc = pd.DataFrame({"Date": working_dates})
    alloc["Allocated hours"] = 0.0

    if schedule_df is None or schedule_df.empty:
        alloc["Free hours"] = daily_hours
        return alloc

    for _, row in schedule_df.iterrows():
        sh = float(row["Start hour index"])
        fh = float(row["Finish hour index"])
        start_day = int(sh // daily_hours)
        end_day = int((fh - 1e-9) // daily_hours)
        for d in range(start_day, end_day + 1):
            if d >= len(alloc):
                break
            day_start_h = d * daily_hours
            day_end_h = (d + 1) * daily_hours
            overlap = max(0.0, min(fh, day_end_h) - max(sh, day_start_h))
            alloc.loc[d, "Allocated hours"] = float(alloc.loc[d, "Allocated hours"]) + overlap

    alloc["Free hours"] = (daily_hours - alloc["Allocated hours"]).clip(lower=0.0)
    return alloc

def build_day_job_details(schedule_df: pd.DataFrame, start_date: date, daily_hours: float, weekdays: set[int], non_working_dates: set[date], horizon_workdays: int = 20) -> dict[date, list[str]]:
    working_dates = build_working_dates(start_date, weekdays, non_working_dates, horizon_days=3650)
    working_dates = working_dates[:max(horizon_workdays, 1)]
    day_jobs = {d: [] for d in working_dates}

    if schedule_df is None or schedule_df.empty:
        return day_jobs

    for _, row in schedule_df.iterrows():
        sh = float(row["Start hour index"])
        fh = float(row["Finish hour index"])
        start_day = int(sh // daily_hours)
        end_day = int((fh - 1e-9) // daily_hours)
        job_name = str(row.get("Job name", "")).strip()
        for d in range(start_day, end_day + 1):
            if d >= len(working_dates):
                break
            day_start_h = d * daily_hours
            day_end_h = (d + 1) * daily_hours
            overlap = max(0.0, min(fh, day_end_h) - max(sh, day_start_h))
            if overlap <= 0:
                continue
            name = job_name if job_name else "Unnamed job"
            day_jobs[working_dates[d]].append(f"{name} ({overlap:.1f}h)")
    return day_jobs

def ensure_member_settings(members: list[str]) -> None:
    if "member_settings" not in st.session_state:
        st.session_state["member_settings"] = {}
    ms = st.session_state["member_settings"]
    for m in members:
        if m not in ms:
            ms[m] = {"weekdays": {0, 1, 2, 3, 4}, "leave_dates": [], "start_date": date.today()}
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
if "cloud_load_attempted" not in st.session_state:
    st.session_state["cloud_load_attempted"] = True
    payload, msg = fetch_state_from_cloud()
    st.session_state["cloud_sync_message"] = msg
    if payload is not None:
        apply_state_payload(payload)

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
    return df.style.apply(apply_styles, axis=None)

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
            if not in_range:
                html += "<td style='background: rgba(49,51,63,0.02);'></td>"
                continue
            if not is_workday:
                html += f"<td style='background: rgba(49,51,63,0.03);'><div class='cal-date'>{d}</div><div class='mini'>Non working</div></td>"
                continue

            free = free_map.get(d, None)
            used = alloc_map.get(d, None)
            if free is None:
                html += f"<td><div class='cal-date'>{d}</div><span class='pill pill-amber'>No data</span></td>"
            else:
                used = 0.0 if used is None else used
                if used <= 0.001:
                    pill = "pill-green"
                elif free <= 0.001:
                    pill = "pill-red"
                else:
                    pill = "pill-amber"
                html += (
                    f"<td><div class='cal-date'>{d}</div>"
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

with st.sidebar:
    st.subheader("Team")

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
    team_df = team_df.dropna(subset=["Member", "Daily hours"], how="any")
    team_df = team_df[team_df["Member"].astype(str).str.len() > 0].reset_index(drop=True)
    st.session_state["team"] = team_df

    st.divider()
    st.subheader("Cloud sync")
    st.caption("Uses SUPABASE_URL and SUPABASE_ANON_KEY from Streamlit secrets.")
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

    jobs_clean = clean_jobs_df(jobs_input)
    jobs_norm = normalize_active_priorities(jobs_clean)
    st.session_state["jobs_raw"] = jobs_norm
    if not jobs_norm[JOB_COLS].reset_index(drop=True).equals(jobs_clean[JOB_COLS].reset_index(drop=True)):
        st.session_state.pop("jobs_editor", None)
        st.rerun()
    jobs_norm = add_status_columns(jobs_norm)

    st.divider()
    st.subheader("Schedule output")

    scheduled_all = []
    hold_rows = []

    for member in team_members:
        member_jobs = jobs_norm[jobs_norm["Assignee"] == member].copy()
        if member_jobs.empty:
            continue

        active = member_jobs[member_jobs["Priority"] >= 1].copy()
        hold = member_jobs[member_jobs["Priority"] == 0].copy()
        if not hold.empty:
            hold_rows.append(hold)

        if active.empty:
            continue

        ms = st.session_state["member_settings"][member]
        weekdays = ms["weekdays"]
        non_working = set(ms["leave_dates"])
        sdate = ms.get("start_date", date.today())
        daily_hours = float(member_hours.get(member, 8.0))

        sched = schedule_member_jobs(active, sdate, daily_hours, weekdays, non_working)
        sched["Assignee"] = member
        scheduled_all.append(sched)

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
    forecast_finish = max(active_only["Finish date"].dropna().tolist()) if not active_only.empty else None
    total_hours_active = float(active_only["Required hours"].sum()) if not active_only.empty else 0.0
    total_jobs = int(len(show))
    active_members = int(active_only["Assignee"].nunique()) if not active_only.empty else 0

    cols = st.columns([1.2,1.2,1.2,1.2])
    with cols[0]:
        render_kpi(
            "Forecast finish date",
            "" if forecast_finish is None else str(forecast_finish),
            "Latest finish across active work",
        )
    with cols[1]:
        render_kpi(
            "Active scheduled hours",
            f"{total_hours_active:.1f}",
            "Sum of active job durations",
        )
    with cols[2]:
        render_kpi("Jobs", f"{total_jobs}", "Active and on hold")
    with cols[3]:
        render_kpi("Active members", f"{active_members}", "Members with active work")

    st.dataframe(style_schedule(show), use_container_width=True)

    st.divider()
    st.subheader("Export")
    csv_bytes = show.to_csv(index=False).encode("utf-8")
    st.download_button("Download schedule CSV", data=csv_bytes, file_name="hydraulic_resourcing_schedule.csv", mime="text/csv")

with tabs[1]:
    st.markdown('<div class="section-title">Staff pages</div>', unsafe_allow_html=True)
    selected_member = st.selectbox("Select staff member", options=team_members, index=0)

    left, right = st.columns([1, 2])

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
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

        leave_key = f"leave_{selected_member}"
        if leave_key not in st.session_state:
            st.session_state[leave_key] = pd.DataFrame({"Date": pd.Series(dtype="datetime64[ns]")})
            existing = st.session_state["member_settings"][selected_member]["leave_dates"]
            if len(existing) > 0:
                st.session_state[leave_key] = pd.DataFrame({"Date": pd.to_datetime(existing)})

        st.caption("Leave dates and shutdown dates")
        leave_df = st.data_editor(
            st.session_state[leave_key],
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={"Date": st.column_config.DateColumn(required=False)},
            key=f"leave_editor_{selected_member}",
        )
        if "Date" in leave_df.columns:
            leave_df["Date"] = pd.to_datetime(leave_df["Date"], errors="coerce").dt.date
        st.session_state[leave_key] = leave_df
        st.session_state["member_settings"][selected_member]["leave_dates"] = [d for d in leave_df["Date"].dropna().tolist()]

        st.write("Daily hours")
        st.write(f"{member_hours.get(selected_member, 8.0):.1f}")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write("Jobs for selected staff member")

        jobs_all = clean_jobs_df(st.session_state.get("jobs_raw", pd.DataFrame(columns=JOB_COLS)))
        member_jobs = jobs_all[jobs_all["Assignee"] == selected_member].copy()
        if member_jobs.empty:
            member_jobs = pd.DataFrame(columns=JOB_COLS)

        editor_key = f"member_jobs_editor_{selected_member}"
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

        edited = clean_jobs_df(edited)
        if not edited.empty:
            edited["Assignee"] = selected_member

        jobs_all = jobs_all[jobs_all["Assignee"] != selected_member].copy()
        combined_clean = clean_jobs_df(pd.concat([jobs_all, edited], ignore_index=True))
        combined_norm = normalize_active_priorities(combined_clean)
        st.session_state["jobs_raw"] = combined_norm
        selected_norm = combined_norm[combined_norm["Assignee"] == selected_member][JOB_COLS].reset_index(drop=True)
        edited_cmp = edited[JOB_COLS].reset_index(drop=True)
        if not selected_norm.equals(edited_cmp):
            st.session_state.pop(editor_key, None)
            st.rerun()

        ms = st.session_state["member_settings"][selected_member]
        weekdays = ms["weekdays"]
        non_working = set(ms["leave_dates"])
        daily_hours = float(member_hours.get(selected_member, 8.0))

        jobs_norm = normalize_active_priorities(clean_jobs_df(combined_norm))
        jobs_norm = add_status_columns(jobs_norm)
        member_norm = jobs_norm[jobs_norm["Assignee"] == selected_member].copy()

        active = member_norm[member_norm["Priority"] >= 1].copy()
        hold = member_norm[member_norm["Priority"] == 0].copy()
        hold["Start date"] = None
        hold["Finish date"] = None

        frames = []
        if not active.empty:
            sched = schedule_member_jobs(active, ms.get("start_date", date.today()), daily_hours, weekdays, non_working)
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
            st.dataframe(style_schedule(view), use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    st.markdown('<div class="section-title">Availability</div>', unsafe_allow_html=True)
    st.caption("Next available date for active work, and next available date if on hold backlog is scheduled after active work")

    jobs_all = clean_jobs_df(st.session_state.get("jobs_raw", pd.DataFrame(columns=JOB_COLS)))
    jobs_norm = normalize_active_priorities(jobs_all)
    jobs_norm = add_status_columns(jobs_norm)

    horizon = st.slider("Workdays to show", min_value=5, max_value=3650, value=20, step=5)

    rows = []
    grids_active = {}
    grids_all = {}

    for member in team_members:
        ms = st.session_state["member_settings"][member]
        weekdays = ms["weekdays"]
        non_working = set(ms["leave_dates"])
        sdate = ms.get("start_date", date.today())
        daily_hours = float(member_hours.get(member, 8.0))

        member_jobs = jobs_norm[jobs_norm["Assignee"] == member].copy()
        active = member_jobs[member_jobs["Priority"] >= 1].copy()
        hold = member_jobs[member_jobs["Priority"] == 0].copy()
        if not hold.empty:
            hold = hold.sort_values(["Due date","Job name"], ascending=[True, True])

        if active.empty:
            next_free_active = sdate
            sched_active = pd.DataFrame()
        else:
            sched_active = schedule_member_jobs(active, sdate, daily_hours, weekdays, non_working)
            last_finish = max(sched_active["Finish date"].tolist())
            work_days = build_working_dates(last_finish + timedelta(days=1), weekdays, non_working, horizon_days=3650)
            next_free_active = work_days[0] if len(work_days) else last_finish + timedelta(days=1)

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
            sched_all = schedule_member_jobs(combined, sdate, daily_hours, weekdays, non_working)
            last_finish_all = max(sched_all["Finish date"].tolist())
            work_days_all = build_working_dates(last_finish_all + timedelta(days=1), weekdays, non_working, horizon_days=3650)
            next_free_all = work_days_all[0] if len(work_days_all) else last_finish_all + timedelta(days=1)

        alloc_active = allocate_member_hours(sched_active if isinstance(sched_active, pd.DataFrame) else pd.DataFrame(), sdate, daily_hours, weekdays, non_working, horizon_workdays=horizon)
        alloc_all = allocate_member_hours(sched_all if isinstance(sched_all, pd.DataFrame) else pd.DataFrame(), sdate, daily_hours, weekdays, non_working, horizon_workdays=horizon)
        jobs_active = build_day_job_details(sched_active if isinstance(sched_active, pd.DataFrame) else pd.DataFrame(), sdate, daily_hours, weekdays, non_working, horizon_workdays=horizon)
        jobs_all_days = build_day_job_details(sched_all if isinstance(sched_all, pd.DataFrame) else pd.DataFrame(), sdate, daily_hours, weekdays, non_working, horizon_workdays=horizon)

        grids_active[member] = (alloc_active, sdate, weekdays, non_working, jobs_active)
        grids_all[member] = (alloc_all, sdate, weekdays, non_working, jobs_all_days)

        rows.append(
            {
                "Member": member,
                "Next available date, active only": next_free_active,
                "Next available date, including on hold backlog": next_free_all,
            }
        )

    summary = pd.DataFrame(rows).sort_values(["Member"]).reset_index(drop=True)
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Capacity calendar")

    chosen_member = st.selectbox("Member", options=team_members, index=0, key="avail_member")
    mode = st.radio("Mode", options=["Active only", "Active plus on hold backlog"], horizontal=True)

    if mode == "Active only":
        alloc, sdate, weekdays, non_working, day_jobs = grids_active[chosen_member]
    else:
        alloc, sdate, weekdays, non_working, day_jobs = grids_all[chosen_member]

    work_dates = build_working_dates(sdate, weekdays, non_working, horizon_days=3650)
    work_dates = work_dates[:max(horizon, 1)]
    if len(work_dates) == 0:
        st.info("No working days available for this member")
    else:
        render_capacity_calendar(alloc, work_dates[0], work_dates[-1], weekdays, day_jobs=day_jobs)
