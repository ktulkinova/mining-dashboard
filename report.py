import io

import numpy as np
import pandas as pd
from fpdf import FPDF
from matplotlib.figure import Figure

from charts import trend_line


def to_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    return buf


def overview_image(df, mines, anomalies, chart_type, degree):
    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()
    columns = mines + ["Total"]
    stack = np.zeros(len(df))
    width = 0.8 / len(columns)

    for n in range(len(columns)):
        col = columns[n]
        color = "C" + str(n % 10)
        if col == "Total":
            color = "gray"
        x = df["Date"]
        y = df[col].values

        if chart_type == "Line":
            ax.plot(x, y, color=color, label=col)
        elif chart_type == "Bar":
            x = x + pd.Timedelta(days=n * width - 0.4 + width / 2)
            ax.bar(x, y, width=width, color=color, label=col)
        elif col != "Total":
            ax.bar(x, y, bottom=stack, color=color, label=col)
            stack = stack + y
            y = stack

        mask = df["Date"].isin(anomalies[anomalies["Mine"] == col]["Date"]).values
        ax.scatter(x[mask], y[mask], s=70, facecolors="none", edgecolors="red",
                   linewidths=2, zorder=5)

        if chart_type != "Stacked" or col == "Total":
            ax.plot(df["Date"], trend_line(y, degree), "--", color=color, label=col + " trend")

    ax.set_ylabel("Output")
    ax.legend(fontsize=8, ncol=6, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    return to_png(fig)


def anomaly_image(df, col, date):
    fig = Figure(figsize=(10, 3))
    ax = fig.subplots()
    ax.plot(df["Date"], df[col])
    day = df[df["Date"] == date]
    ax.scatter(day["Date"], day[col], s=120, facecolors="none", edgecolors="red",
               linewidths=2, zorder=5)
    ax.set_ylabel(col)
    return to_png(fig)


def write(pdf, text, size=10, style=""):
    pdf.set_font("Helvetica", style, size)
    pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")


def add_table(pdf, df):
    pdf.set_font("Helvetica", "", 9)
    with pdf.table(text_align="CENTER") as table:
        row = table.row()
        for col in df.columns:
            row.cell(col)
        for i in range(len(df)):
            row = table.row()
            for col in df.columns:
                row.cell(str(df[col].iloc[i]))
    pdf.ln(4)


def make_report(df, mines, stats, anomalies, settings, chart_type, degree):
    pdf = FPDF()
    pdf.add_page()

    start = df["Date"].min().strftime("%Y-%m-%d")
    end = df["Date"].max().strftime("%Y-%m-%d")
    write(pdf, "Mining report", 16, "B")
    write(pdf, "Period: " + start + " to " + end + " (" + str(len(df)) + " days)")

    write(pdf, "Statistics", 13, "B")
    add_table(pdf, stats)

    write(pdf, "Test parameters", 13, "B")
    for name in settings:
        write(pdf, name + ": " + str(settings[name]))

    anomalies = anomalies.sort_values(["Date", "Mine"])
    table = anomalies.copy()
    table["Date"] = table["Date"].dt.strftime("%Y-%m-%d")
    write(pdf, "Anomalies", 13, "B")
    add_table(pdf, table)

    pdf.add_page()
    write(pdf, "Chart: " + chart_type + ", trendline degree " + str(degree), 13, "B")
    pdf.image(overview_image(df, mines, anomalies, chart_type, degree), w=pdf.epw)

    pdf.add_page()
    n = 1
    for i in anomalies.index:
        row = anomalies.loc[i]
        if pdf.get_y() > 200:
            pdf.add_page()
        date = row["Date"].strftime("%Y-%m-%d")
        write(pdf, str(n) + ". " + row["Type"] + ": " + row["Mine"] + ", " + date, 12, "B")
        write(pdf, "Value: " + str(row["Value"]))
        write(pdf, "Detected by: " + row["Tests"])
        pdf.image(anomaly_image(df, row["Mine"], row["Date"]), w=pdf.epw * 0.8)
        pdf.ln(6)
        n = n + 1

    return bytes(pdf.output())
