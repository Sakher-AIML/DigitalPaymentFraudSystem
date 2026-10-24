"""Streamlit user interface for the fraud monitoring system."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
from datetime import date
from typing import Any, Callable

import pandas as pd
import streamlit as st

from app.database import mysql_db
from app.database.mongo_db import MongoDatabase
from app.services import alert_service, investigation_service, transaction_service

st.set_page_config(page_title="Payment Risk Operations", page_icon="◈", layout="wide")

PAGES = [
    "Dashboard",
    "Transaction Monitoring",
    "Submit / Simulate",
    "Fraud Alerts",
    "Investigation Cases",
    "System Status",
]

RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

st.markdown(
    """
<style>
:root {
    --navy: #081b33;
    --navy-soft: #102d4c;
    --teal: #0b8f87;
    --teal-dark: #076c67;
    --blue: #2b6cb0;
    --ink: #142b40;
    --muted: #617488;
    --surface: #ffffff;
    --canvas: #f4f7fa;
    --border: #dce5ec;
    --success: #167c59;
    --warning: #a56709;
    --danger: #ba3d4f;
}

.stApp { background: var(--canvas); color: var(--ink); }
.main .block-container { max-width: 1480px; padding: 2.25rem 3rem 3.5rem; }
[data-testid="stSidebar"] { background: var(--navy); border-right: 1px solid #173652; }
[data-testid="stSidebar"] > div:first-child { padding: 1.5rem 1rem; }
[data-testid="stSidebar"] * { color: #e8f1f7; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding: .55rem .7rem; border-radius: 7px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: var(--navy-soft); }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] { gap: .2rem; }
[data-testid="stMetric"] { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1rem 1.1rem; box-shadow: 0 2px 8px rgba(14, 44, 70, .04); }
[data-testid="stMetricLabel"] { color: var(--muted); font-size: .78rem; font-weight: 600; }
[data-testid="stMetricValue"] { color: var(--ink); font-size: 1.45rem; }
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }
[data-testid="stForm"] { border: 1px solid var(--border); border-radius: 12px; background: var(--surface); padding: 1.2rem; }
.brand-mark { display: inline-flex; align-items: center; justify-content: center; width: 2rem; height: 2rem; border-radius: 8px; background: var(--teal); color: white; font-weight: 800; margin-right: .55rem; }
.brand-name { font-size: 1.05rem; font-weight: 700; letter-spacing: -.01em; }
.brand-subtitle { color: #9eb6ca !important; font-size: .75rem; margin: .35rem 0 1.4rem 2.55rem; }
.sidebar-footer { color: #88a4ba !important; font-size: .7rem; line-height: 1.45; border-top: 1px solid #23415b; padding-top: 1rem; margin-top: 2rem; }
.page-header { border-bottom: 1px solid var(--border); padding-bottom: 1.35rem; margin-bottom: 1.5rem; }
.page-header h1 { color: var(--ink); font-size: 1.85rem; letter-spacing: -.025em; margin: 0; }
.page-header p { color: var(--muted); font-size: .92rem; margin: .4rem 0 0; }
.section-heading { color: var(--ink); font-size: 1rem; font-weight: 700; margin: 1.6rem 0 .75rem; }
.section-caption { color: var(--muted); font-size: .8rem; margin: -.4rem 0 .8rem; }
.panel { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.15rem; box-shadow: 0 2px 8px rgba(14, 44, 70, .035); }
.panel-title { color: var(--ink); font-size: 1rem; font-weight: 700; margin-bottom: .75rem; }
.empty-state { background: var(--surface); border: 1px dashed #b8c8d5; border-radius: 10px; color: var(--muted); padding: 1.5rem; text-align: center; }
.risk-pill, .status-pill { display: inline-block; border-radius: 999px; font-size: .72rem; font-weight: 700; padding: .18rem .55rem; }
.risk-low { background: #e5f5ed; color: var(--success); }
.risk-medium { background: #fff3d9; color: var(--warning); }
.risk-high, .risk-critical { background: #fde8eb; color: var(--danger); }
.status-ok { color: var(--success); font-weight: 700; }
.status-error { color: var(--danger); font-weight: 700; }
.result-card { border-left: 4px solid var(--teal); background: #edf9f7; border-radius: 8px; padding: .95rem 1rem; }
button[kind="primary"] { background: var(--teal-dark); border-color: var(--teal-dark); }
button[kind="primary"]:hover { background: var(--teal); border-color: var(--teal); }
</style>
""",
    unsafe_allow_html=True,
)


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="page-header"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def section_heading(title: str, caption: str | None = None) -> None:
    st.markdown(f'<div class="section-heading">{title}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="section-caption">{caption}</div>', unsafe_allow_html=True)


def safe_query(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    try:
        return mysql_db.fetch_all(query, params)
    except Exception as exc:
        st.error(f"Database unavailable: {exc}")
        return []


def currency(value: Any) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


def compact_timestamp(value: Any) -> str:
    if value is None:
        return "—"
    parsed = pd.to_datetime(value, errors="coerce")
    return "—" if pd.isna(parsed) else parsed.strftime("%d %b %Y, %H:%M")


def compact_date(value: Any) -> str:
    if value is None:
        return "—"
    parsed = pd.to_datetime(value, errors="coerce")
    return "—" if pd.isna(parsed) else parsed.strftime("%d %b %Y")


def risk_badge(level: Any) -> str:
    normalized = str(level or "UNEVALUATED").upper()
    css = normalized.lower().replace("unevaluated", "medium")
    return f'<span class="risk-pill risk-{css}">{normalized}</span>'


def status_badge(status: Any) -> str:
    normalized = str(status or "UNKNOWN").upper()
    css = "ok" if normalized in {"SETTLED", "RESOLVED", "CLOSED", "CONNECTED"} else "error" if normalized in {"DECLINED", "CRITICAL", "ERROR"} else "warning"
    return f'<span class="status-pill status-{css}">{normalized.replace("_", " ")}</span>'


def show_empty(message: str) -> None:
    st.markdown(f'<div class="empty-state">{message}</div>', unsafe_allow_html=True)


def transaction_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    if "amount" in frame:
        frame["amount"] = frame["amount"].map(currency)
    if "transaction_timestamp" in frame:
        frame["transaction_timestamp"] = frame["transaction_timestamp"].map(compact_timestamp)
    return frame


def dashboard() -> None:
    page_header("Risk command center", "A focused view of payment activity, exposure, alerts, and analyst workload.")
    summary = safe_query(
        """SELECT COUNT(*) AS transactions, COALESCE(SUM(amount),0) AS value,
        SUM(risk_level IN ('MEDIUM','HIGH','CRITICAL')) AS flagged,
        SUM(risk_level = 'CRITICAL') AS critical FROM transactions"""
    )
    alerts = safe_query("SELECT COUNT(*) AS critical_alerts FROM fraud_alerts WHERE severity = 'CRITICAL' AND status <> 'RESOLVED'")
    cases = safe_query("SELECT COUNT(*) AS pending FROM investigation_cases WHERE status <> 'CLOSED'")
    row = summary[0] if summary else {}
    metrics = [
        ("Transactions", row.get("transactions", 0)),
        ("Total value", currency(row.get("value", 0))),
        ("Flagged for review", row.get("flagged", 0)),
        ("Critical alerts", (alerts[0] if alerts else {}).get("critical_alerts", 0)),
        ("Pending cases", (cases[0] if cases else {}).get("pending", 0)),
    ]
    columns = st.columns(5)
    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)

    left, right = st.columns([1, 1.35], gap="medium")
    with left:
        section_heading("Risk distribution", "Current transaction mix by evaluated risk level.")
        distribution = safe_query(
            "SELECT risk_level, COUNT(*) AS count FROM transactions GROUP BY risk_level ORDER BY count DESC"
        )
        if distribution:
            chart = pd.DataFrame(distribution)
            st.bar_chart(
                chart,
                x="count",
                y="risk_level",
                horizontal=True,
                color="#0b8f87",
                height=250,
                width="stretch",
            )
        else:
            show_empty("Risk distribution will appear after transactions are available.")
    with right:
        section_heading("Recent activity", "Latest transactions with customer and merchant context.")
        recent = transaction_service.list_transactions(limit=8) if row else []
        if recent:
            frame = transaction_frame(recent)
            if "transaction_timestamp" in frame:
                frame["transaction_timestamp"] = frame["transaction_timestamp"].map(
                    lambda value: compact_date(value)
                )
            visible = [
                column
                for column in [
                    "transaction_id",
                    "customer_name",
                    "merchant_name",
                    "amount",
                    "risk_level",
                    "status",
                    "transaction_timestamp",
                ]
                if column in frame
            ]
            st.dataframe(
                frame[visible],
                width="stretch",
                height=250,
                hide_index=True,
                column_config={
                    "transaction_id": st.column_config.NumberColumn("ID", width="small"),
                    "customer_name": st.column_config.TextColumn("Customer", width="medium"),
                    "merchant_name": st.column_config.TextColumn("Merchant", width="medium"),
                    "amount": st.column_config.TextColumn("Amount", width="medium"),
                    "risk_level": st.column_config.TextColumn("Risk", width="small"),
                    "status": st.column_config.TextColumn("Status", width="small"),
                    "transaction_timestamp": st.column_config.TextColumn("Date", width="medium"),
                },
            )
        else:
            show_empty("No recent transaction activity is available.")


def transaction_monitoring() -> None:
    page_header("Transaction monitoring", "Search, filter, and inspect joined payment records without losing operational context.")
    filter_columns = st.columns([1.1, 1.1, 1.2, 1.2, 1.2], gap="medium")
    risk = filter_columns[0].selectbox("Risk level", ["All"] + RISK_LEVELS)
    status = filter_columns[1].selectbox("Status", ["All", "PENDING", "SETTLED", "DECLINED", "REVERSED"])
    search = filter_columns[2].text_input("Search", placeholder="Customer or merchant")
    limit = filter_columns[3].slider("Rows", 10, 200, 50)
    min_amount = filter_columns[4].number_input("Minimum INR", min_value=0.0, value=0.0, step=500.0)
    rows = []
    try:
        rows = transaction_service.list_transactions(
            {"risk_level": None if risk == "All" else risk, "status": None if status == "All" else status,
             "min_amount": min_amount or None},
            limit,
        )
    except Exception as exc:
        st.error(f"Could not retrieve transactions: {exc}")
    if search:
        needle = search.casefold()
        rows = [row for row in rows if needle in str(row.get("customer_name", "")).casefold() or needle in str(row.get("merchant_name", "")).casefold()]
    if not rows:
        show_empty("No transactions match the selected filters.")
        return
    frame = transaction_frame(rows)
    visible = [column for column in ["transaction_id", "customer_name", "merchant_name", "amount", "transaction_type", "channel", "risk_score", "risk_level", "status", "transaction_timestamp"] if column in frame]
    st.dataframe(
        frame[visible],
        width="stretch",
        hide_index=True,
        column_config={"transaction_id": "ID", "customer_name": "Customer", "merchant_name": "Merchant", "risk_score": st.column_config.NumberColumn("Score", format="%d/100"), "transaction_timestamp": "Time"},
    )
    section_heading("Transaction detail", "Select a record to review the full joined context.")
    selected = st.selectbox("Transaction", [row["transaction_id"] for row in rows], label_visibility="collapsed")
    detail = next(row for row in rows if row["transaction_id"] == selected)
    detail_left, detail_right = st.columns([1.2, 1], gap="large")
    with detail_left:
        st.markdown(f'<div class="panel"><div class="panel-title">Transaction {detail["transaction_id"]}</div><p><b>Customer</b> {detail.get("customer_name", "—")}<br><b>Merchant</b> {detail.get("merchant_name", "—")}<br><b>Amount</b> {currency(detail.get("amount"))}<br><b>Channel</b> {detail.get("channel", "—")}<br><b>Time</b> {compact_timestamp(detail.get("transaction_timestamp"))}</p></div>', unsafe_allow_html=True)
    with detail_right:
        st.markdown(f'<div class="panel"><div class="panel-title">Risk assessment</div><p>Score: <b>{detail.get("risk_score", "—")}</b> / 100</p>{risk_badge(detail.get("risk_level"))}<p style="margin-top:.8rem">Status: {status_badge(detail.get("status"))}</p></div>', unsafe_allow_html=True)


def submit_simulate() -> None:
    page_header("Submit / simulate", "Evaluate a fictional payment with the live, explainable rule engine.")
    accounts = safe_query("SELECT account_id, customer_id, balance FROM accounts WHERE status = 'ACTIVE' ORDER BY account_id")
    merchants = safe_query("SELECT merchant_id, merchant_name, mcc FROM merchants WHERE status = 'ACTIVE' ORDER BY merchant_name")
    if not accounts or not merchants:
        show_empty("Active accounts and merchants are required. Import the schema and seed data, then refresh.")
        return
    with st.form("transaction_form"):
        section_heading("Payment details", "Required fields are marked by Streamlit. Use fictional values for demonstration.")
        first, second = st.columns(2, gap="large")
        with first:
            account = st.selectbox("Source account", [account["account_id"] for account in accounts])
            merchant = st.selectbox("Merchant", [merchant["merchant_id"] for merchant in merchants])
            amount = st.number_input("Amount (INR)", min_value=0.01, max_value=1_000_000.0, value=1_000.0, step=100.0)
        with second:
            channel = st.selectbox("Channel", ["WEB", "MOBILE", "POS", "ATM"])
            device = st.text_input("Device ID", placeholder="device-demo-01")
            location = st.text_input("Location", placeholder="Pune, IN")
        submitted = st.form_submit_button("Evaluate and submit", type="primary", width="stretch")
    if submitted:
        try:
            result = transaction_service.submit_transaction(
                {"source_account_id": account, "merchant_id": merchant, "amount": amount, "channel": channel, "device_id": device.strip(), "location": location.strip()}
            )
            assessment = result["assessment"]
            st.markdown(f'<div class="result-card"><b>Transaction {result["transaction_id"]} recorded</b><br>Risk score: <b>{assessment.score}/100</b> &nbsp; {risk_badge(assessment.level)}</div>', unsafe_allow_html=True)
            section_heading("Rule explanations")
            for reason in assessment.explanations or ["No configured rules were triggered."]:
                st.write(f"• {reason}")
            if result.get("telemetry_error"):
                st.warning(f"MySQL write succeeded, but MongoDB telemetry failed: {result['telemetry_error']}")
        except Exception as exc:
            st.error(f"Submission failed; no success is claimed: {exc}")


def fraud_alerts() -> None:
    page_header("Fraud alerts", "Prioritize rule-triggered activity for review; a score is not proof of criminal activity.")
    filters = st.columns([1, 1, 2], gap="medium")
    severity = filters[0].selectbox("Severity", ["All"] + RISK_LEVELS[1:])
    status = filters[1].selectbox("Status", ["All", "OPEN", "ACKNOWLEDGED", "RESOLVED", "FALSE_POSITIVE"])
    filters[2].markdown("<div style='padding-top:1.8rem;color:#617488;font-size:.8rem'>Alerts are generated from deterministic rules and remain review signals.</div>", unsafe_allow_html=True)
    try:
        rows = alert_service.list_alerts(None if severity == "All" else severity, None if status == "All" else status)
        if not rows:
            show_empty("No alerts match the selected filters.")
            return
        frame = pd.DataFrame(rows)
        for column in ["created_at"]:
            if column in frame:
                frame[column] = frame[column].map(compact_timestamp)
        frame["score"] = frame["score"].map(lambda value: f"{value}/100")
        st.dataframe(frame, width="stretch", hide_index=True, column_config={"alert_id": "Alert", "transaction_id": "Transaction", "severity": "Severity", "status": "Status", "created_at": "Created"})
        section_heading("Alert action", "Update the lifecycle only after reviewing the explanation and triggered rules.")
        selected = st.selectbox("Alert", [row["alert_id"] for row in rows], label_visibility="collapsed")
        action_col, button_col = st.columns([1, 1], gap="medium")
        new_status = action_col.selectbox("New status", ["OPEN", "ACKNOWLEDGED", "RESOLVED", "FALSE_POSITIVE"])
        if button_col.button("Save alert status", type="primary", width="stretch"):
            alert_service.update_alert_status(selected, new_status)
            st.success("Alert status updated.")
        detail = next(row for row in rows if row["alert_id"] == selected)
        st.markdown(f'<div class="panel"><div class="panel-title">Alert {selected} · Transaction {detail["transaction_id"]}</div><p>{detail.get("explanation", "No explanation recorded.")}</p><b>Triggered rules:</b> {detail.get("rules") or "None recorded"}</div>', unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"Could not retrieve alerts: {exc}")


def investigation_cases() -> None:
    page_header("Investigation cases", "Assign, review, and close cases with an auditable analyst workflow.")
    try:
        rows = investigation_service.list_cases()
        if rows:
            frame = pd.DataFrame(rows)
            for column in ["created_at", "updated_at"]:
                if column in frame:
                    frame[column] = frame[column].map(compact_timestamp)
            st.dataframe(frame, width="stretch", hide_index=True, column_config={"case_id": "Case", "alert_id": "Alert", "transaction_id": "Transaction", "assigned_investigator": "Investigator", "updated_at": "Updated"})
        else:
            show_empty("No investigation cases have been created.")
        alerts = alert_service.list_alerts(status="OPEN")
        with st.expander("Create a case from an open alert"):
            if alerts:
                with st.form("case_form"):
                    alert_id = st.selectbox("Alert", [alert["alert_id"] for alert in alerts])
                    investigator = st.text_input("Investigator")
                    notes = st.text_area("Notes")
                    if st.form_submit_button("Create case", type="primary", width="stretch"):
                        case_id = investigation_service.create_case(alert_id, investigator, notes)
                        st.success(f"Case {case_id} created.")
            else:
                st.info("There are no open alerts available for case creation.")
        if rows:
            section_heading("Update a case", "Valid transitions are enforced by the investigation service.")
            selected_case = st.selectbox("Case", [row["case_id"] for row in rows], label_visibility="collapsed")
            selected_row = next(row for row in rows if row["case_id"] == selected_case)
            update_columns = st.columns(2, gap="large")
            target = update_columns[0].selectbox("Target status", ["OPEN", "IN_REVIEW", "CLOSED"])
            resolution = update_columns[1].text_input("Resolution", value=selected_row.get("resolution") or "")
            notes = st.text_area("Updated notes", value=selected_row.get("notes") or "")
            if st.button("Save case update", type="primary"):
                investigation_service.update_case(selected_case, selected_row["status"], target, resolution, notes)
                st.success("Case updated and audit event recorded.")
    except Exception as exc:
        st.error(f"Investigation workflow unavailable: {exc}")


def system_status() -> None:
    page_header("System status", "Connection health and setup diagnostics. Credentials are never displayed.")
    status_columns = st.columns(2, gap="large")
    checks: list[tuple[str, Callable[[], Any], str]] = [
        ("MySQL", lambda: mysql_db.fetch_one("SELECT 1 AS healthy"), "Authoritative financial records"),
        ("MongoDB", lambda: MongoDatabase().ping(), "Telemetry and investigation audit logs"),
    ]
    for column, (name, check, description) in zip(status_columns, checks):
        with column:
            try:
                check()
                st.markdown(f'<div class="panel"><div class="panel-title">{name}</div><p>{description}</p><span class="status-pill status-ok">CONNECTED</span></div>', unsafe_allow_html=True)
            except Exception as exc:
                st.markdown(f'<div class="panel"><div class="panel-title">{name}</div><p>{description}</p><span class="status-pill status-error">UNAVAILABLE</span><p style="margin-top:.75rem;color:#617488;font-size:.8rem">{exc}</p></div>', unsafe_allow_html=True)
    section_heading("Setup checklist")
    st.info("Run `python scripts/setup_check.py` after importing `sql/schema.sql` and `sql/seed.sql`. The application reports actual service state and does not fabricate successful writes.")


st.sidebar.markdown(
    '<div><span class="brand-mark">PR</span><span class="brand-name">Payment Risk</span></div>'
    '<div class="brand-subtitle">Payment Risk Operations</div>',
    unsafe_allow_html=True,
)
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")
st.sidebar.markdown(
    '<div class="sidebar-footer">Academic demonstration<br>Fictional payment data only<br><br>Database-backed risk operations console</div>',
    unsafe_allow_html=True,
)

{
    "Dashboard": dashboard,
    "Transaction Monitoring": transaction_monitoring,
    "Submit / Simulate": submit_simulate,
    "Fraud Alerts": fraud_alerts,
    "Investigation Cases": investigation_cases,
    "System Status": system_status,
}[page]()
