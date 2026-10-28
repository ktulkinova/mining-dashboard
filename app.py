import streamlit as st
import pandas as pd

from analysis import basic_stats, find_anomalies
from charts import make_chart
from report import make_report

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuN-XYs0681xmjFkQMMspB9EZiv9IaUR5iLKDRdKvU1c5IH5tY7ET6SYGjV17OLRxqye0wL6zcyA8y/pub?gid=1069165709&single=true&output=csv"

st.set_page_config(page_title="Weyland-Yutani Mining Dashboard", layout="wide")


@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df.dropna(subset=["Date"])
    df["Date"] = pd.to_datetime(df["Date"])

    mines = []
    for c in df.columns:
        if c != "Date" and c != "Total":
            mines.append(c)
    df["Total"] = df[mines].sum(axis=1).round(1)
    return df


st.sidebar.header("Anomaly settings")
k = st.sidebar.slider("IQR multiplier (k)", 0.5, 3.0, 1.5, 0.1)
z = st.sidebar.slider("Z-score threshold", 1.0, 4.0, 2.5, 0.1)
window = st.sidebar.slider("Moving average window (days)", 3, 15, 7)
percent = st.sidebar.slider("Max distance from moving average (%)", 5, 100, 40, 5)
alpha = st.sidebar.selectbox("Grubbs alpha", [0.01, 0.05, 0.10], index=1)

st.sidebar.header("Chart settings")
chart_type = st.sidebar.radio("Chart type", ["Line", "Bar", "Stacked"])
degree = st.sidebar.selectbox("Trendline degree", [1, 2, 3, 4])

st.title("Weyland-Yutani Mining Dashboard")

if st.button("Refresh data"):
    st.cache_data.clear()

df = load_data()

mines = []
for c in df.columns:
    if c != "Date" and c != "Total":
        mines.append(c)
columns = mines + ["Total"]

st.header("Statistics")
stats = basic_stats(df, columns)
st.dataframe(stats, hide_index=True)

st.header("Anomalies")
anomalies = find_anomalies(df, columns, k, z, window, percent, alpha)
st.dataframe(anomalies, hide_index=True)

st.header("Chart")
fig = make_chart(df, mines, anomalies, chart_type, degree)
st.plotly_chart(fig)

settings = {
    "IQR multiplier (k)": k,
    "Z-score threshold": z,
    "Moving average window (days)": window,
    "Max distance from moving average (%)": percent,
    "Grubbs alpha": alpha,
}
pdf = make_report(df, mines, stats, anomalies, settings, chart_type, degree)
st.download_button("Download PDF report", pdf, "mining_report.pdf", "application/pdf")