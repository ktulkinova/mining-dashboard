import pandas as pd
import streamlit as st

from analysis import basic_stats, find_anomalies
from charts import make_chart
from report import make_report

CSV_URL = "https://docs.google.com/spreadsheets/d/1dNwzX7SrcsHLi-euElt04qqk9pvYpfvInsZsBwTOc8I/export?format=csv&gid=425583512"
st.set_page_config(page_title="Weyland-Yutani Mining Dashboard", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df.drop(columns="Total", errors="ignore")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    for col in df.columns:
        if col != "Date":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(axis=1, how="all").fillna(0).reset_index(drop=True)

    mines = []
    for col in df.columns:
        if col != "Date":
            mines.append(col)
    df["Total"] = df[mines].sum(axis=1).round(1)
    return df, mines


st.sidebar.header("Anomaly tests")
k = st.sidebar.slider("IQR multiplier (k)", 0.5, 3.0, 1.5, 0.1)
z = st.sidebar.slider("Z-score threshold", 1.0, 4.0, 2.5, 0.1)
window = st.sidebar.slider("Moving average window (days)", 3, 15, 7)
percent = st.sidebar.slider("Max distance from moving average (%)", 5, 100, 40, 5)
alpha = st.sidebar.selectbox("Grubbs alpha", [0.01, 0.05, 0.10], index=1)

st.sidebar.header("Chart")
chart_type = st.sidebar.radio("Chart type", ["Line", "Bar", "Stacked"])
degree = st.sidebar.selectbox("Trendline degree", [1, 2, 3, 4])

st.title("Weyland-Yutani Mining Dashboard")
if st.button("Refresh data"):
    load_data.clear()
df, mines = load_data()
columns = mines + ["Total"]

st.header("Statistics")
stats = basic_stats(df, columns)
st.dataframe(stats, hide_index=True)

st.header("Anomalies")
anomalies = find_anomalies(df, columns, k, z, window, percent, alpha)
if len(anomalies) == 0:
    st.write("No anomalies found with these test parameters.")
else:
    st.dataframe(anomalies, hide_index=True,
                 column_config={"Date": st.column_config.DateColumn(format="YYYY-MM-DD")})

st.header("Chart")
st.plotly_chart(make_chart(df, mines, anomalies, chart_type, degree))

settings = {
    "IQR multiplier (k)": k,
    "Z-score threshold": z,
    "Moving average window (days)": window,
    "Max distance from moving average (%)": percent,
    "Grubbs alpha": alpha,
}
if st.button("Generate PDF report"):
    pdf = make_report(df, mines, stats, anomalies, settings, chart_type, degree)
    st.download_button("Download PDF report", pdf, "mining_report.pdf", "application/pdf", on_click="ignore")
