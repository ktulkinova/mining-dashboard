import io
from datetime import datetime

import matplotlib
import numpy as np
import pandas as pd
from fpdf import FPDF
from fpdf.fonts import FontFace
from matplotlib.figure import Figure

from charts import COLORS, anomaly_mask, trend_line

FONTS = matplotlib.get_data_path() + "/fonts/ttf/"


class PDF(FPDF):
    def header(self):
        self.set_font("DejaVu", "", 8)
        self.set_text_color(110)
        self.cell(self.epw / 2, 6, "Weyland-Yutani Corporation")
        self.cell(self.epw / 2, 6, "Mining output report", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(180)
        self.line(self.l_margin, self.get_y(), self.l_margin + self.epw, self.get_y())
        self.set_text_color(0)
        self.ln(6)

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(110)
        self.cell(0, 6, "Page " + str(self.page_no()) + " of {nb}", align="C")
        self.set_text_color(0)


def to_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    return buf


def overview_image(df, mines, anomalies, chart_type, degree):
    fig = Figure(figsize=(10, 6), layout="constrained")
    ax = fig.subplots()
    x = df["Date"]
    stack = np.zeros(len(df))
    width = 0.8 / len(mines)

    for n in range(len(mines)):
        col = mines[n]
        color = COLORS[n % len(COLORS)]
        y = df[col].values
        mask = anomaly_mask(df, anomalies, col)

        if chart_type == "Line":
            ax.plot(x, y, color=color, linewidth=1.2, label=col)
            ax.scatter(x[mask], y[mask], s=60, facecolors="none", edgecolors="red", linewidths=1.5, zorder=5)
            trend = trend_line(y, degree)
        elif chart_type == "Bar":
            pos = x + pd.Timedelta(days=n * width - 0.4 + width / 2)
            ax.bar(pos, y, width=width, color=color, label=col)
            ax.bar(pos[mask], y[mask], width=width, fill=False, edgecolor="red", linewidth=1.5)
            trend = trend_line(y, degree)
        else:
            ax.bar(x, y, width=0.8, bottom=stack, color=color, label=col)
            ax.bar(x[mask], y[mask], width=0.8, bottom=stack[mask], fill=False, edgecolor="red", linewidth=1.5)
            stack = stack + y
            trend = trend_line(stack, degree)
        ax.plot(x, trend, "--", color=color, linewidth=1)

    total = df["Total"].values
    mask = anomaly_mask(df, anomalies, "Total")
    tax = ax
    if chart_type == "Stacked":
        ax.set_ylabel("Output (stack height = Total)")
    else:
        ax.set_ylabel("Output per mine")
        tax = ax.twinx()
        tax.plot(x, total, color="black", linewidth=2, label="Total")
        tax.set_ylabel("Total")
    tax.plot(x, trend_line(total, degree), "--", color="black", linewidth=1.2, label="Total trend")
    tax.scatter(x[mask], total[mask], s=70, facecolors="none", edgecolors="red", linewidths=1.8, zorder=6,
                label="Anomaly")

    fig.legend(loc="outside lower center", ncol=7, fontsize=8)
    return to_png(fig)


def anomaly_image(df, col, date, color):
    fig = Figure(figsize=(9, 2.6), layout="constrained")
    ax = fig.subplots()
    ax.plot(df["Date"], df[col], color=color, linewidth=1.2)
    ax.axhline(df[col].mean(), color="gray", linestyle="--", linewidth=1)
    ax.axvline(date, color="red", alpha=0.2, linewidth=8)
    day = df[df["Date"] == date]
    ax.scatter(day["Date"], day[col], s=90, facecolors="none", edgecolors="red", linewidths=2, zorder=5)
    ax.set_ylabel(col)
    return to_png(fig)


def write(pdf, text, size=10, style=""):
    pdf.set_font("DejaVu", style, size)
    pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")


def heading(pdf, text, space=30):
    if pdf.will_page_break(space):
        pdf.add_page()
    pdf.ln(2)
    write(pdf, text, 13, "B")
    pdf.ln(1)


def add_table(pdf, df, widths, width=None):
    pdf.set_font("DejaVu", "", 9)
    pdf.set_draw_color(200)
    head = FontFace(emphasis="BOLD", fill_color=(225, 230, 238))
    with pdf.table(col_widths=widths, width=width, align="LEFT", text_align="CENTER", line_height=6,
                   headings_style=head, borders_layout="HORIZONTAL_LINES",
                   cell_fill_color=(246, 247, 249), cell_fill_mode="ROWS") as table:
        row = table.row()
        for col in df.columns:
            row.cell(col)
        for i in range(len(df)):
            row = table.row()
            for col in df.columns:
                row.cell(str(df[col].iloc[i]))
    pdf.ln(3)


def make_report(df, mines, stats, anomalies, settings, chart_type, degree):
    pdf = PDF()
    pdf.add_font("DejaVu", "", FONTS + "DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", FONTS + "DejaVuSans-Bold.ttf")
    pdf.set_margins(15, 12, 15)
    pdf.set_auto_page_break(True, 18)
    pdf.add_page()

    start = df["Date"].min().strftime("%Y-%m-%d")
    end = df["Date"].max().strftime("%Y-%m-%d")
    write(pdf, "Mining output report", 18, "B")
    write(pdf, f"Period: {start} to {end} ({len(df)} days), mines: {len(mines)}")
    write(pdf, "Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))

    heading(pdf, "Statistics")
    add_table(pdf, stats, (3, 2, 2, 2, 2))

    heading(pdf, "Test parameters")
    rows = []
    for name in settings:
        rows.append([name, str(settings[name])])
    add_table(pdf, pd.DataFrame(rows, columns=["Parameter", "Value"]), (3, 1), 120)

    heading(pdf, f"Anomalies ({len(anomalies)})")
    if len(anomalies) == 0:
        write(pdf, "No anomalies found with these test parameters.")
    else:
        table = anomalies.copy()
        table["Date"] = table["Date"].dt.strftime("%Y-%m-%d")
        table["Value"] = table["Value"].map("{:.1f}".format)
        add_table(pdf, table, (2, 3, 1.5, 1.5, 4))

    heading(pdf, f"Chart: {chart_type}, trendline degree {degree}", 130)
    pdf.image(overview_image(df, mines, anomalies, chart_type, degree), w=pdf.epw)

    for n in range(len(anomalies)):
        if n == 0:
            heading(pdf, "Anomaly details", 100)
        row = anomalies.iloc[n]
        col = row["Mine"]
        mean = df[col].mean()
        diff = row["Value"] - mean
        deviation = f"{diff:+.1f}"
        if mean != 0:
            deviation += f" ({diff / mean * 100:+.1f}%)"
        color = "black"
        if col in mines:
            color = COLORS[mines.index(col) % len(COLORS)]

        if pdf.will_page_break(85):
            pdf.add_page()
        write(pdf, f"{n + 1}. {row['Type']}: {col}, {row['Date'].strftime('%Y-%m-%d')}", 12, "B")
        write(pdf, f"Value: {row['Value']:.1f}    Mean: {mean:.1f}    Deviation from mean: {deviation}")
        write(pdf, "Detected by: " + row["Tests"])
        pdf.image(anomaly_image(df, col, row["Date"], color), w=pdf.epw)
        pdf.ln(4)

    return bytes(pdf.output())
