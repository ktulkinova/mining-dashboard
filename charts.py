import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative


def trend_line(values, degree):
    x = np.arange(len(values))
    return np.polyval(np.polyfit(x, values, degree), x)


def make_chart(df, mines, anomalies, chart_type, degree):
    fig = go.Figure()
    columns = mines + ["Total"]
    stack = np.zeros(len(df))
    width = 0.8 / len(columns)

    for n in range(len(columns)):
        col = columns[n]
        color = qualitative.D3[n % 10]
        if col == "Total":
            color = "gray"
        x = df["Date"]
        y = df[col].values

        if chart_type == "Line":
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=col, line_color=color))
        elif chart_type == "Bar":
            fig.add_trace(go.Bar(x=x, y=y, name=col, marker_color=color))
            x = x + pd.Timedelta(days=n * width - 0.4 + width / 2)
        elif col != "Total":
            fig.add_trace(go.Bar(x=x, y=y, name=col, marker_color=color))
            stack = stack + y
            y = stack

        mask = df["Date"].isin(anomalies[anomalies["Mine"] == col]["Date"]).values
        fig.add_trace(go.Scatter(x=x[mask], y=y[mask], mode="markers", name=col + " outliers",
                                 showlegend=False,
                                 marker=dict(color="red", size=12, symbol="circle-open",
                                             line_width=3)))

        if chart_type != "Stacked" or col == "Total":
            fig.add_trace(go.Scatter(x=df["Date"], y=trend_line(y, degree), mode="lines",
                                     name=col + " trend", line=dict(color=color, dash="dash")))

    if chart_type == "Stacked":
        fig.update_layout(barmode="stack")
    fig.update_layout(height=550, yaxis_title="Output")
    return fig
