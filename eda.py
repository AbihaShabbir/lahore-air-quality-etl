"""STAGE 5 - EDA: read the data back FROM THE DATABASE, then explore it.

Run `python eda.py` to produce every chart + table in outputs/.
Each fig_* function also works on its own inside the notebook.
"""
import sqlite3
import sys

import matplotlib

if "ipykernel" not in sys.modules:      # plain script -> draw to files only
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

import config

# ---- look: one accent colour, quiet grid, no clutter ---------------------
INK, MUTED, GRID = "#1f2937", "#6b7280", "#e5e7eb"
ACCENT, WARN = "#2563eb", "#c2410c"
DIVERGING = LinearSegmentedColormap.from_list(
    "div", ["#2563eb", "#f3f4f6", "#c2410c"])   # blue - neutral - orange

plt.rcParams.update({
    "figure.figsize": (8, 4.5), "font.size": 10, "text.color": INK,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "axes.titlesize": 12,
    "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "xtick.color": MUTED, "ytick.color": MUTED,
})

UG = "µg/m³"
LABELS = {"pm2_5": "PM2.5", "pm10": "PM10", "temperature_2m": "Temperature",
          "relative_humidity_2m": "Humidity", "wind_speed_10m": "Wind speed",
          "surface_pressure": "Pressure", "precipitation": "Rain"}


def _finish(fig, name):
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(config.OUTPUT_DIR / name, dpi=150)
    if "ipykernel" not in sys.modules:
        plt.close(fig)
    return fig


# ---- data -----------------------------------------------------------------
def load_data() -> pd.DataFrame:
    """Read the table back from the database (this is the 'L -> EDA' link)."""
    if not config.DB_PATH.exists():
        raise FileNotFoundError(f"{config.DB_PATH.name} not found - run load.py first")
    conn = sqlite3.connect(config.DB_PATH)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {config.TABLE}", conn,
                               parse_dates=["time"])
    finally:
        conn.close()
    df["date"] = df["time"].dt.date
    df["hour"] = df["time"].dt.hour
    df["month"] = df["time"].dt.to_period("M").astype(str)
    return df


def daily_table(df: pd.DataFrame) -> pd.DataFrame:
    """One row per day. Days with fewer than 18 hourly readings are ignored."""
    g = df.groupby("date")
    daily = g.agg(hours=("pm2_5", "size"), pm2_5_mean=("pm2_5", "mean"),
                  pm10_mean=("pm10", "mean")).reset_index()
    daily = daily[daily["hours"] >= 18].copy()
    daily["month"] = pd.to_datetime(daily["date"]).dt.to_period("M").astype(str)
    daily["over_who_pm25"] = daily["pm2_5_mean"] > config.WHO_PM25_DAILY
    daily["over_who_pm10"] = daily["pm10_mean"] > config.WHO_PM10_DAILY
    return daily


# ---- tables ---------------------------------------------------------------
def save_tables(df, daily):
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stats = df[config.VALUE_COLS].describe().T.round(2)
    stats.to_csv(config.OUTPUT_DIR / "summary_stats.csv")
    miss = df[config.VALUE_COLS].isna().sum().to_frame("missing")
    miss["percent"] = (miss["missing"] / len(df) * 100).round(2)
    miss.to_csv(config.OUTPUT_DIR / "missing_values.csv")
    daily.to_csv(config.OUTPUT_DIR / "daily_pm_vs_who.csv", index=False)
    return stats, miss


# ---- figures --------------------------------------------------------------
def fig_distribution(df):
    fig, ax = plt.subplots()
    ax.hist(df["pm2_5"], bins=50, color=ACCENT, edgecolor="white", linewidth=0.5)
    ax.axvline(config.WHO_PM25_DAILY, color=WARN, ls="--", lw=1.5)
    ax.text(config.WHO_PM25_DAILY, 0.96, f"  WHO 24-h guideline: {config.WHO_PM25_DAILY}",
            transform=ax.get_xaxis_transform(), color=WARN, va="top")
    ax.set(title="Distribution of hourly PM2.5 in Lahore",
           xlabel=f"PM2.5 ({UG})", ylabel="Number of hours")
    return _finish(fig, "01_pm25_distribution.png")


def fig_hourly(df):
    h = df.groupby("hour")["pm2_5"].mean()
    fig, ax = plt.subplots()
    ax.plot(h.index, h.values, color=ACCENT, lw=2, marker="o", ms=4,
            markeredgecolor="white")
    ax.set(title="Average PM2.5 by hour of day", xlabel="Hour of day (Pakistan time)",
           ylabel=f"Mean PM2.5 ({UG})", xticks=range(0, 24, 3))
    return _finish(fig, "02_pm25_by_hour.png")


def fig_monthly(df):
    m = df.groupby("month")["pm2_5"].mean()
    fig, ax = plt.subplots()
    bars = ax.bar(m.index, m.values, color=ACCENT, width=0.7)
    ax.axhline(config.WHO_PM25_DAILY, color=WARN, ls="--", lw=1.5,
               label=f"WHO 24-h guideline ({config.WHO_PM25_DAILY})")
    ax.legend(loc="upper right", frameon=False)
    for b, v in zip(bars, m.values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}", ha="center",
                va="bottom", color=MUTED, fontsize=8)
    ax.set(title="Average PM2.5 by month", ylabel=f"Mean PM2.5 ({UG})")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="x", visible=False)
    return _finish(fig, "03_pm25_by_month.png")


def fig_corr(df):
    cols = ["pm2_5", "pm10", "temperature_2m", "relative_humidity_2m",
            "wind_speed_10m", "surface_pressure", "precipitation"]
    c = df[cols].corr()
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(c.values, cmap=DIVERGING, vmin=-1, vmax=1)
    names = [LABELS[x] for x in cols]
    ax.set_xticks(range(len(cols)), names, rotation=45, ha="right")
    ax.set_yticks(range(len(cols)), names)
    ax.grid(False)
    for i in range(len(cols)):
        for j in range(len(cols)):
            v = c.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=9,
                    color="white" if abs(v) > 0.6 else INK)
    fig.colorbar(im, ax=ax, shrink=0.8, label="Correlation (-1 to +1)")
    ax.set_title("Correlation between pollution and weather")
    return _finish(fig, "04_correlation_heatmap.png")


def fig_scatter(df):
    pairs = [("wind_speed_10m", "Wind speed (km/h)"),
             ("relative_humidity_2m", "Humidity (%)"),
             ("temperature_2m", "Temperature (°C)")]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, (col, label) in zip(axes, pairs):
        ax.scatter(df[col], df["pm2_5"], s=5, alpha=0.12, color=ACCENT, linewidths=0)
        bins = pd.cut(df[col], 15)
        med = df.groupby(bins, observed=True).agg(x=(col, "mean"), y=("pm2_5", "median"))
        ax.plot(med["x"], med["y"], color=INK, lw=2)
        ax.set_xlabel(label)
    axes[0].set_ylabel(f"PM2.5 ({UG})")
    fig.suptitle("PM2.5 vs weather (dark line = median per bin)",
                 x=0.01, ha="left", fontweight="bold")
    return _finish(fig, "05_pm25_vs_weather.png")


def fig_who(daily):
    g = daily.groupby("month").agg(over=("over_who_pm25", "sum"),
                                   days=("over_who_pm25", "size"))
    fig, ax = plt.subplots()
    bars = ax.bar(g.index, g["over"], color=ACCENT, width=0.7)
    for b, (o, d) in zip(bars, zip(g["over"], g["days"])):
        ax.text(b.get_x() + b.get_width() / 2, o, f"{o}/{d}", ha="center",
                va="bottom", color=MUTED, fontsize=8)
    ax.set(title=f"Days above the WHO PM2.5 guideline ({config.WHO_PM25_DAILY} {UG})",
           ylabel="Days (label = days over / days measured)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="x", visible=False)
    return _finish(fig, "06_days_over_who.png")


# ---- written findings (numbers computed from the data) ---------------------
def write_findings(df, daily):
    pm = df["pm2_5"]
    peak = df.loc[pm.idxmax()]
    month_mean = df.groupby("month")["pm2_5"].mean()
    hour_mean = df.groupby("hour")["pm2_5"].mean()
    corr = df[["pm2_5"] + config.WEATHER_VARS].corr()["pm2_5"].drop("pm2_5")
    strongest = corr.abs().idxmax()
    n_days, n_over = len(daily), int(daily["over_who_pm25"].sum())
    n_over10 = int(daily["over_who_pm10"].sum())

    lines = [
        "# EDA findings (auto-generated from the database)", "",
        f"- Period: {df['time'].min():%d %b %Y} to {df['time'].max():%d %b %Y}, "
        f"{len(df):,} hourly records.",
        f"- PM2.5: mean {pm.mean():.1f}, median {pm.median():.1f}, "
        f"max {pm.max():.1f} {UG} (on {peak['time']:%d %b %Y, %H:%M}).",
        f"- {n_over} of {n_days} measured days ({n_over / n_days:.0%}) had a daily mean "
        f"PM2.5 above the WHO guideline of {config.WHO_PM25_DAILY} {UG}; "
        f"{n_over10} days exceeded the PM10 guideline of {config.WHO_PM10_DAILY}.",
        f"- Worst month: {month_mean.idxmax()} (mean {month_mean.max():.1f}). "
        f"Cleanest month: {month_mean.idxmin()} (mean {month_mean.min():.1f}).",
        f"- Daily pattern: highest average at {hour_mean.idxmax()}:00 "
        f"({hour_mean.max():.1f}), lowest at {hour_mean.idxmin()}:00 ({hour_mean.min():.1f}).",
    ]
    winter = df["time"].dt.month.isin([11, 12, 1, 2])
    if winter.any() and (~winter).any():
        lines.append(f"- Winter (Nov-Feb) mean PM2.5 {pm[winter].mean():.1f} vs "
                     f"{pm[~winter].mean():.1f} in the other months.")
    lines.append("- Correlation of PM2.5 with weather: " + ", ".join(
        f"{LABELS[k]} {v:+.2f}" for k, v in corr.items()) +
        f". Strongest: {LABELS[strongest]}.")
    rain = df["precipitation"] > 0
    if rain.any() and (~rain).any():
        lines.append(f"- Mean PM2.5 in hours with rain: {pm[rain].mean():.1f} vs "
                     f"{pm[~rain].mean():.1f} in dry hours.")
    lines += ["", "Note: correlation shows association, not proof that one thing causes another."]
    text = "\n".join(lines)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (config.OUTPUT_DIR / "findings.md").write_text(text, encoding="utf-8")
    return text


def main():
    df = load_data()
    if df.empty:
        raise ValueError("The database table is empty - nothing to analyse")
    daily = daily_table(df)
    save_tables(df, daily)
    for fn, arg in [(fig_distribution, df), (fig_hourly, df), (fig_monthly, df),
                    (fig_corr, df), (fig_scatter, df), (fig_who, daily)]:
        fn(arg)
    print(write_findings(df, daily))
    print(f"\nCharts and tables saved in {config.OUTPUT_DIR}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"EDA FAILED: {e}")
        sys.exit(1)
