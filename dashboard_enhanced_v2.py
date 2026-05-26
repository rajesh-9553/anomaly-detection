import streamlit as st
import requests
import pandas as pd
import altair as alt
import json

# CONFIG
API = "https://anomaly-detection-vvhh.onrender.com"
ANOMALIES_ENDPOINT = f"{API}/anomalies"

SEVERITY_COLORS = {
    "LOW": "#2ecc71",
    "MEDIUM": "#f1c40f",
    "HIGH": "#e67e22",
    "CRITICAL": "#e74c3c",
}

st.set_page_config(
    page_title="Anomaly Detection Dashboard",
    layout="wide"
)
st.title("Anomaly Detection — Dashboard (Interactive)")
st.markdown(
    """
    <style>
    /* Perfect circular donut container (NO GLOW) */
    .donut-wrapper {
        width: 260px;
        height: 260px;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: auto;
        border-radius: 50%;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.header("Controls")

    limit = st.number_input(
        "Max rows to fetch",
        min_value=100,
        max_value=3000,
        value=300,
        step=100
    )

    minutes = st.slider(
        "Window (minutes)",
        min_value=1,
        max_value=1440,
        value=120
    )

    auto = st.checkbox("Auto-refresh (5s)", value=False)
    refresh = st.button("Refresh now")

    st.markdown("---")
    st.subheader("Model info")

    try:
        mi = requests.get(f"{API}/model_info", timeout=10).json()
        st.json(mi)
    except Exception:
        st.warning("Model info not available")

@st.cache_data(ttl=5)
def fetch_anomalies(limit: int):
    r = requests.get(
        f"{ANOMALIES_ENDPOINT}?limit={limit}",
        timeout=30
    )
    r.raise_for_status()
    return r.json()["anomalies"]

try:
    anoms = fetch_anomalies(limit)
except Exception as e:
    st.error(f"Failed to fetch anomalies: {e}")
    st.stop()

if not anoms:
    st.info("No anomalies found.")
    st.stop()

#  DATAFRAME 
df = pd.DataFrame(anoms)
selected_ips = []


df["ingest_time"] = pd.to_datetime(
    df["ingest_time"],
    errors="coerce",
    utc=True
)
df = df.dropna(subset=["ingest_time"])

if "severity" not in df.columns:
    df["severity"] = "UNKNOWN"

def try_parse_raw(x):
    try:
        return json.loads(x)
    except Exception:
        return {}

if "raw" in df.columns:
    raw_parsed = df["raw"].apply(try_parse_raw)
    raw_df = pd.json_normalize(raw_parsed).add_prefix("r_")
    raw_df.index = df.index
    df = pd.concat([df, raw_df], axis=1)

def first_existing(df, candidates):
    for c in candidates:
        if c in df.columns:
            return df[c].astype(str)
    return ""

df["srcip"] = ""

for c in ["r_srcip", "r_col_0", "srcip", "col_0"]:
    if c in df.columns:
        df["srcip"] = df["srcip"].mask(df["srcip"] == "", df[c].astype(str))

df["dstip"] = first_existing(df, ["r_dstip", "r_col_1", "dstip", "col_1"])

cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=minutes)
df_recent = df[df["ingest_time"] >= cutoff].copy()
# SEVERITY TREND DATA 
sev_trend = (
    df_recent
    .set_index("ingest_time")
    .groupby("severity")
    .resample("1min")
    .size()
    .rename("count")
    .reset_index()
)

df_trend = df_recent.copy()

sev_trend = (
    df_trend
    .set_index("ingest_time")
    .groupby("severity")
    .resample("1min")
    .size()
    .rename("count")
    .reset_index()
)

if df_recent.empty:
    st.warning("No anomalies in selected time window.")
    st.stop()

left, right = st.columns([3, 1])

# RIGHT COLUMN

with right:

    # TOP OFFENDERS
    st.subheader("Top offenders (srcip)")

    top_src = (
        df_recent["srcip"]
        .replace("", "UNKNOWN")
        .value_counts()
        .head(10)
        .reset_index()
    )
    top_src.columns = ["srcip", "count"]

    st.dataframe(top_src, height=250, use_container_width=True)

    selected_ips = st.multiselect(
        "Select IPs to inspect",
        options=top_src["srcip"].tolist(),
        default=top_src["srcip"].tolist()[:3]
    )

    # SEVERITY OVERVIEW
    st.subheader("Severity overview")

    selected_severities = st.multiselect(
        "Filter by severity",
        options=list(SEVERITY_COLORS.keys()),
        default=list(SEVERITY_COLORS.keys())
    )

    df_sev = df_recent[df_recent["severity"].isin(selected_severities)]

    sev_counts = (
        df_sev["severity"]
        .value_counts()
        .reindex(SEVERITY_COLORS.keys(), fill_value=0)
        .reset_index()
    )
    sev_counts.columns = ["severity", "count"]

    donut = alt.Chart(sev_counts).mark_arc(
        innerRadius=55,
        outerRadius=85
    ).encode(
        theta=alt.Theta("count:Q"),
        color=alt.Color(
            "severity:N",
            scale=alt.Scale(
                domain=list(SEVERITY_COLORS.keys()),
                range=list(SEVERITY_COLORS.values())
            ),
            legend=None 
        ),
        tooltip=["severity:N", "count:Q"]
    ).properties(
        width=220,
        height=220
    )

    spacer_l, donut_col, spacer_r = st.columns([1, 2, 1])

    with donut_col:
        st.altair_chart(donut, use_container_width=False)


# LEFT COLUMN

with left:
    st.subheader("Anomalies time-series")

    agg = (
        df_recent
        .set_index("ingest_time")
        .resample("1min")
        .size()
        .rename("count")
        .reset_index()
    )

    if not agg.empty:
        brush = alt.selection_interval(encodings=["x"])

        upper = alt.Chart(agg).mark_area(opacity=0.4).encode(
            x="ingest_time:T",
            y="count:Q",
            tooltip=["ingest_time:T", "count:Q"]
        ).add_params(brush).properties(height=200)

        lower = alt.Chart(agg).mark_line().encode(
            x="ingest_time:T",
            y="count:Q",
            tooltip=["ingest_time:T", "count:Q"]
        ).transform_filter(brush).properties(height=200)

        st.altair_chart(
            alt.vconcat(upper, lower),
            use_container_width=True
        )
    else:
        st.info("No anomaly time-series data available.")

    st.subheader("Severity trend over time")

    if not sev_trend.empty:
        sev_chart = alt.Chart(sev_trend).mark_line(point=True).encode(
            x=alt.X("ingest_time:T", title="Time"),
            y=alt.Y("count:Q", title="Count"),
            color=alt.Color(
                "severity:N",
                scale=alt.Scale(
                    domain=list(SEVERITY_COLORS.keys()),
                    range=list(SEVERITY_COLORS.values())
                ),
                legend=alt.Legend(title="Severity")
            ),
            tooltip=["severity:N", "count:Q", "ingest_time:T"]
        ).properties(height=260)

        st.altair_chart(sev_chart, use_container_width=True)
    else:
        st.info("No severity trend data available.")


# ALERTS PANEL

st.markdown("---")
st.subheader("🚨 Live Security Alerts")

@st.cache_data(ttl=5)
def fetch_alerts():
    try:
        r = requests.get(f"{API}/alerts?limit=50", timeout=5)
        r.raise_for_status()
        return r.json()["alerts"]
    except Exception:
        return []

alerts = fetch_alerts()

if not alerts:
    st.success("✅ No active alerts")
else:
    for a in reversed(alerts):
        if "CRITICAL" in a:
            st.error(a)
        elif "HIGH" in a:
            st.warning(a)
        else:
            st.info(a)

    # EXPORT
    st.markdown("---")
    st.download_button(
        "Export recent anomalies (CSV)",
        data=df_recent.to_csv(index=False),
        file_name="anomalies_recent.csv",
        mime="text/csv"
    )


# PER-IP TIMELINES

if selected_ips:
    st.subheader("Per-IP anomaly timelines")

    per_ip = []
    for ip in selected_ips:
        tmp = df_recent[df_recent["srcip"] == ip]
        if not tmp.empty:
            t = (
                tmp.set_index("ingest_time")
                .resample("1min")
                .size()
                .rename("count")
                .reset_index()
            )
            t["srcip"] = ip
            per_ip.append(t)

    if per_ip:
        ip_df = pd.concat(per_ip)

        ip_chart = alt.Chart(ip_df).mark_line(point=True).encode(
            x="ingest_time:T",
            y="count:Q",
            color="srcip:N",
            facet=alt.Facet("srcip:N", columns=2)
        ).properties(height=140)

        st.altair_chart(ip_chart, use_container_width=True)

st.subheader("Recent anomalies")

display_cols = [
    c for c in ["id", "ingest_time", "srcip", "dstip", "score", "severity"]
    if c in df_recent.columns
]

st.dataframe(
    df_recent
    .sort_values("ingest_time", ascending=False)[display_cols]
    .head(500),
    height=320,
    use_container_width=True
)

if refresh or auto:
    st.experimental_rerun()
