import numpy as np
import pandas as pd
from scipy import stats


def basic_stats(df, columns):
    rows = []
    for col in columns:
        values = df[col]
        iqr = values.quantile(0.75) - values.quantile(0.25)
        rows.append([col, values.mean(), values.std(), values.median(), iqr])
    return pd.DataFrame(rows, columns=["Mine", "Mean", "Std", "Median", "IQR"]).round(1)


def iqr_test(values, k):
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    return (values < q1 - k * iqr) | (values > q3 + k * iqr)


def zscore_test(values, threshold):
    z = (values - values.mean()) / values.std()
    return z.abs() > threshold


def moving_avg_test(values, window, percent):
    ma = values.rolling(window, center=True, min_periods=1).mean()
    distance = (values - ma) / ma * 100
    return distance.abs() > percent


def grubbs_test(values, alpha):
    result = pd.Series(False, index=values.index)
    data = values.copy()

    while len(data) > 2:
        n = len(data)
        mean = data.mean()
        std = data.std()
        if std == 0:
            break
        idx = (data - mean).abs().idxmax()
        g = abs(data[idx] - mean) / std

        t = stats.t.ppf(1 - alpha / (2 * n), n - 2)
        g_crit = (n - 1) / np.sqrt(n) * np.sqrt(t ** 2 / (n - 2 + t ** 2))

        if g > g_crit:
            result[idx] = True
            data = data.drop(idx)
        else:
            break

    return result


def find_anomalies(df, columns, k, z, window, percent, alpha):
    rows = []
    for col in columns:
        values = df[col]
        tests = {
            "IQR": iqr_test(values, k),
            "Z-score": zscore_test(values, z),
            "Moving avg": moving_avg_test(values, window, percent),
            "Grubbs": grubbs_test(values, alpha),
        }

        for i in values.index:
            found = [name for name in tests if tests[name][i]]
            if len(found) == 0:
                continue
            if values[i] > values.median():
                kind = "Spike"
            else:
                kind = "Drop"
            rows.append([df.loc[i, "Date"], col, values[i], kind, ", ".join(found)])

    return pd.DataFrame(rows, columns=["Date", "Mine", "Value", "Type", "Tests"])
