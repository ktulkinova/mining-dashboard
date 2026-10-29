import numpy as np
import plotly.graph_objects as go

COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#8c564b",
          "#e377c2", "#7f7f7f", "#bcbd22", "#17becf", "#aec7e8"]


def trend_line(values, degree):
    x = np.arange(len(values))
    degree = min(degree, len(values) - 1)
    return np.polyval(np.polyfit(x, values, degree), x)


def anomaly_mask(df, anomalies, col):
    dates = anomalies[anomalies["Mine"] == col]["Date"]
    return df["Date"].isin(dates).values


def add_marks(fig, x, y, axis, legend):
    fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="Anomaly", legendgroup="anomaly",
                             showlegend=legend, yaxis=axis,
                             marker=dict(color="red", size=12, symbol="circle-open", line_width=2.5)))


def make_chart(df, mines, anomalies, chart_type, degree):
    fig = go.Figure()
    x = df["Date"]
    stack = np.zeros(len(df))

    for n in range(len(mines)):
        col = mines[n]
        color = COLORS[n % len(COLORS)]
        y = df[col].values
        mask = anomaly_mask(df, anomalies, col)

        if chart_type == "Line":
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=col, legendgroup=col, line_color=color))
            add_marks(fig, x[mask], y[mask], "y", False)
            trend = trend_line(y, degree)
        else:
            group = str(n)
            base = None
            if chart_type == "Stacked":
                group = None
                base = stack[mask]
            fig.add_trace(go.Bar(x=x, y=y, name=col, legendgroup=col, offsetgroup=group, marker_color=color))
            fig.add_trace(go.Bar(x=x[mask], y=y[mask], base=base, name=col + " anomaly", legendgroup=col,
                                 offsetgroup=group, showlegend=False, hoverinfo="skip",
                                 marker=dict(color="rgba(0,0,0,0)", line=dict(color="red", width=3))))
            if chart_type == "Bar":
                trend = trend_line(y, degree)
            else:
                stack = stack + y
                trend = trend_line(stack, degree)

        fig.add_trace(go.Scatter(x=x, y=trend, mode="lines", name=col + " trend", legendgroup=col,
                                 showlegend=False, line=dict(color=color, dash="dash", width=1.5)))

    total = df["Total"].values
    mask = anomaly_mask(df, anomalies, "Total")
    axis = "y"
    if chart_type != "Stacked":
        axis = "y2"
        fig.add_trace(go.Scatter(x=x, y=total, mode="lines", name="Total", legendgroup="Total",
                                 yaxis=axis, line=dict(color="black", width=2.5)))
    fig.add_trace(go.Scatter(x=x, y=trend_line(total, degree), mode="lines", name="Total trend",
                             legendgroup="Total", yaxis=axis, line=dict(color="black", dash="dash", width=1.5)))
    add_marks(fig, x[mask], total[mask], axis, True)

    fig.update_layout(height=560, barmode="group", yaxis_title="Output per mine",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    if chart_type == "Stacked":
        fig.update_layout(barmode="stack", yaxis_title="Output (stack height = Total)")
    else:
        fig.update_layout(yaxis2=dict(title="Total", overlaying="y", side="right", showgrid=False))
    return fig
