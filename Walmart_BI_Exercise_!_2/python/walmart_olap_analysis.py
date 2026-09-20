"""
WALMART OLAP ANALYSIS — Exercise 2
Business Intelligence for Decision Making (24CAC624)

This script is intentionally self-contained and reproducible.

It:
1. Loads the cleaned Walmart dataset from Exercise 1.
2. Validates the analytical grain and required columns.
3. Documents the OLAP model: fact/business event, measure, dimensions and hierarchy.
4. Builds the main multidimensional cube using pandas pivot_table.
5. Produces normalized cube results suitable for inspection/Power BI.
6. Performs a required SLICE.
7. Performs a required DICE.
8. Performs a focused DICE with three simultaneous filters.
9. Demonstrates ROLL-UP and DRILL-DOWN on Year -> Month -> Week.
10. Recalculates/validates the Exercise 1 KPI baselines.
11. Generates presentation-ready analytical CSVs.
12. Generates a rich set of readable PNG visuals with:
      - meaningful titles,
      - axis labels,
      - benchmark/reference lines where applicable,
      - direct data labels where useful,
      - explanatory subtitles/annotations,
      - readable currency/percentage formatting.
13. Generates a visual catalog so each PNG has a clear analytical purpose.

No seaborn is required. All visualizations use matplotlib.

The Power BI dashboard is intentionally separate:
Python = reproducible OLAP analysis/evidence.
Power BI = interactive dashboard, slicers, visual interactions and drill-down.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# ============================================================
# 0. PROJECT PATHS
# ============================================================
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "Walmart_Sales_Cleaned.csv"
RESULTS_DIR = BASE_DIR / "olap_results"
CHART_DIR = BASE_DIR / "outputs" / "charts"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 1. DISPLAY / PLOT HELPERS
# ============================================================
pd.set_option("display.max_columns", 100)
pd.set_option("display.width", 180)
pd.set_option("display.max_rows", 100)

def money(x, pos=None):
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    if abs(x) >= 1_000:
        return f"${x/1_000:.0f}K"
    return f"${x:,.0f}"

money_formatter = FuncFormatter(money)

def pct(x, pos=None):
    return f"{x:.0f}%"

pct_formatter = FuncFormatter(pct)

def save_figure(fig, filename):
    path = CHART_DIR / filename
    fig.tight_layout()
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Chart generated: {path}")

def add_value_labels(ax, orientation="vertical", decimals=0, percent=False):
    for patch in ax.patches:
        if orientation == "vertical":
            value = patch.get_height()
            x = patch.get_x() + patch.get_width() / 2
            y = patch.get_height()
            label = f"{value:.{decimals}f}" + ("%" if percent else "")
            ax.annotate(
                label,
                (x, y),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8
            )
        else:
            value = patch.get_width()
            x = patch.get_width()
            y = patch.get_y() + patch.get_height() / 2
            label = f"{value:.{decimals}f}" + ("%" if percent else "")
            ax.annotate(
                label,
                (x, y),
                xytext=(5, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=8
            )

# ============================================================
# 2. LOAD + VALIDATE DATA
# ============================================================
print("=" * 90)
print("WALMART OLAP ANALYSIS — EXERCISE 2")
print("=" * 90)

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Cleaned dataset not found: {DATA_PATH}\n"
        "Place Walmart_Sales_Cleaned.csv inside the project's data folder."
    )

df = pd.read_csv(DATA_PATH)

required_columns = [
    "Store", "Date", "Weekly_Sales", "Holiday_Flag",
    "Temperature", "Fuel_Price", "CPI", "Unemployment",
    "Is_Holiday_Week", "Year", "Month", "Week_of_Year",
    "WoW_Sales_Growth_%"
]

missing = [c for c in required_columns if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
df["Store"] = df["Store"].astype(str)
df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
df["Month"] = pd.to_numeric(df["Month"], errors="coerce").astype("Int64")
df["Week_of_Year"] = pd.to_numeric(df["Week_of_Year"], errors="coerce").astype("Int64")

if df["Date"].isna().any():
    raise ValueError("Date conversion produced missing dates.")

df = df.sort_values(["Store", "Date"]).reset_index(drop=True)

print(f"Dataset: {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"Date range: {df['Date'].min().date()} -> {df['Date'].max().date()}")
print(f"Stores: {df['Store'].nunique()}")

# ============================================================
# 3. OLAP MODEL
# ============================================================
print("\n" + "=" * 90)
print("OLAP MODEL")
print("=" * 90)
print("Grain      : One Walmart store's sales for one specific week")
print("Measure    : Weekly_Sales")
print("Dimensions : Store, Date, Holiday")
print("Hierarchy  : Year -> Month -> Week")
print("Primary analytical question:")
print("How can Walmart compare store performance, time trends and holiday effects?")
print()

# Save model definition as machine-readable documentation.
model_definition = pd.DataFrame([
    ["Business Grain", "Store + Week", "One store's sales observation for one week"],
    ["Primary Measure", "Weekly_Sales", "Core sales measure used throughout the OLAP analysis"],
    ["Dimension 1", "Store", "Walmart store identifier"],
    ["Dimension 2", "Date", "Date / Year / Month / Week analysis"],
    ["Dimension 3", "Holiday", "Holiday versus non-holiday weekly context"],
    ["Hierarchy", "Year -> Month -> Week", "Used for roll-up and drill-down"],
], columns=["Component", "Definition", "Business Meaning"])
model_definition.to_csv(RESULTS_DIR / "olap_model_definition.csv", index=False)

# ============================================================
# 4. MAIN DATA CUBE
# ============================================================
cube = pd.pivot_table(
    df,
    index="Store",
    columns=["Year", "Is_Holiday_Week"],
    values="Weekly_Sales",
    aggfunc=["sum", "mean"],
    observed=True
)

cube.columns = [
    f"{metric.title().replace(' ', '_')}_Sales_{int(year)}_{holiday}"
    for metric, year, holiday in cube.columns
]
cube = cube.reset_index()

print("CUBE: Store x Year x Holiday -> Weekly Sales")
print(cube.head(10).to_string(index=False))
cube.to_csv(RESULTS_DIR / "cube_store_year_holiday.csv", index=False)

# Normalized cube = easier to inspect and load into BI tools.
cube_normalized = (
    df.groupby(["Store", "Year", "Is_Holiday_Week"], observed=True)
      .agg(
          Total_Sales=("Weekly_Sales", "sum"),
          Avg_Weekly_Sales=("Weekly_Sales", "mean"),
          Median_Weekly_Sales=("Weekly_Sales", "median"),
          Min_Weekly_Sales=("Weekly_Sales", "min"),
          Max_Weekly_Sales=("Weekly_Sales", "max"),
          Weeks=("Weekly_Sales", "count"),
          Avg_Temperature=("Temperature", "mean"),
          Avg_Fuel_Price=("Fuel_Price", "mean"),
          Avg_CPI=("CPI", "mean"),
          Avg_Unemployment=("Unemployment", "mean"),
          Avg_WoW_Growth=("WoW_Sales_Growth_%", "mean"),
      )
      .reset_index()
)
cube_normalized.to_csv(RESULTS_DIR / "cube_normalized.csv", index=False)

# ============================================================
# 5. SLICE — ONE DIMENSION FIXED
# ============================================================
SLICE_YEAR = 2011

slice_df = df[df["Year"] == SLICE_YEAR].copy()

slice_result = (
    slice_df.pivot_table(
        index="Store",
        columns="Is_Holiday_Week",
        values="Weekly_Sales",
        aggfunc="mean",
        observed=True
    )
    .reset_index()
)

slice_result = slice_result.rename(columns={
    "No": "Non_Holiday_Avg_Sales",
    "Yes": "Holiday_Avg_Sales"
})

slice_result["Holiday_Uplift_%"] = (
    (slice_result["Holiday_Avg_Sales"] - slice_result["Non_Holiday_Avg_Sales"])
    / slice_result["Non_Holiday_Avg_Sales"]
    * 100
)

slice_result = slice_result.sort_values("Holiday_Uplift_%", ascending=False)

print("\nSLICE: Year = 2011")
print("Question: During 2011, how did average weekly sales differ across Walmart")
print("stores between holiday and non-holiday weeks?")
print(slice_result.head(10).to_string(index=False))
slice_result.to_csv(RESULTS_DIR / "slice_year_2011.csv", index=False)

# More visual-friendly slice table.
slice_summary = (
    slice_df.groupby(["Is_Holiday_Week"], observed=True)
            .agg(
                Avg_Weekly_Sales=("Weekly_Sales", "mean"),
                Total_Sales=("Weekly_Sales", "sum"),
                Store_Count=("Store", "nunique"),
                Week_Count=("Weekly_Sales", "count")
            )
            .reset_index()
)
slice_summary.to_csv(RESULTS_DIR / "slice_2011_holiday_summary.csv", index=False)

# ============================================================
# 6. DICE — MULTIPLE DIMENSIONS FILTERED
# ============================================================
DICE_YEAR = 2011

dice_result = (
    df[
        (df["Year"] == DICE_YEAR) &
        (df["Is_Holiday_Week"] == "Yes")
    ]
    .groupby("Store", observed=True)
    .agg(
        Holiday_Weeks=("Weekly_Sales", "count"),
        Avg_Holiday_Sales=("Weekly_Sales", "mean"),
        Total_Holiday_Sales=("Weekly_Sales", "sum"),
        Median_Holiday_Sales=("Weekly_Sales", "median"),
        Avg_WoW_Growth=("WoW_Sales_Growth_%", "mean"),
        Avg_Unemployment=("Unemployment", "mean"),
        Avg_Fuel_Price=("Fuel_Price", "mean")
    )
    .reset_index()
    .sort_values("Avg_Holiday_Sales", ascending=False)
)

print("\nDICE: Year = 2011 AND Holiday = Yes")
print("Question: Which stores generated the highest average weekly sales during")
print("holiday weeks in 2011?")
print(dice_result.head(15).to_string(index=False))
dice_result.to_csv(RESULTS_DIR / "dice_2011_holiday.csv", index=False)

# Focused three-filter dice.
dice_december = (
    df[
        (df["Year"] == 2011) &
        (df["Month"] == 12) &
        (df["Is_Holiday_Week"] == "Yes")
    ]
    .groupby("Store", observed=True)
    .agg(
        Holiday_Weeks=("Weekly_Sales", "count"),
        Avg_Dec_Holiday_Sales=("Weekly_Sales", "mean"),
        Total_Dec_Holiday_Sales=("Weekly_Sales", "sum")
    )
    .reset_index()
    .sort_values("Avg_Dec_Holiday_Sales", ascending=False)
)

dice_december.to_csv(RESULTS_DIR / "dice_2011_december_holiday.csv", index=False)

# ============================================================
# 7. ROLL-UP / DRILL-DOWN — BONUS
# ============================================================
rollup_year = (
    df.groupby("Year", observed=True)
      .agg(
          Total_Sales=("Weekly_Sales", "sum"),
          Avg_Weekly_Sales=("Weekly_Sales", "mean"),
          Median_Weekly_Sales=("Weekly_Sales", "median"),
          Store_Count=("Store", "nunique"),
          Week_Count=("Weekly_Sales", "count")
      )
      .reset_index()
)
rollup_year.to_csv(RESULTS_DIR / "rollup_year.csv", index=False)

drilldown = (
    df.groupby(["Year", "Month", "Week_of_Year"], observed=True)
      .agg(
          Total_Sales=("Weekly_Sales", "sum"),
          Avg_Weekly_Sales=("Weekly_Sales", "mean"),
          Store_Count=("Store", "nunique")
      )
      .reset_index()
      .sort_values(["Year", "Month", "Week_of_Year"])
)
drilldown.to_csv(RESULTS_DIR / "drilldown_year_month_week.csv", index=False)

monthly_trend = (
    df.groupby(["Year", "Month"], observed=True)
      .agg(
          Avg_Weekly_Sales=("Weekly_Sales", "mean"),
          Total_Sales=("Weekly_Sales", "sum")
      )
      .reset_index()
)
monthly_trend["Year_Month"] = pd.to_datetime(
    monthly_trend["Year"].astype(str) + "-" +
    monthly_trend["Month"].astype(str).str.zfill(2) + "-01"
)
monthly_trend.to_csv(RESULTS_DIR / "monthly_rollup.csv", index=False)

# ============================================================
# 8. KPI VALIDATION
# ============================================================
NETWORK_BENCHMARK = 1_050_000
HOLIDAY_UPLIFT_BENCHMARK = 7.8
CV_BENCHMARK = 0.13
UNEMP_CORR_BENCHMARK = -0.11
FUEL_CORR_BENCHMARK = 0.01


# ------------------------------------------------------------
# NETWORK-LEVEL KPI CALCULATIONS
# ------------------------------------------------------------

# KPI 1: Network Average Weekly Sales
network_avg = df["Weekly_Sales"].mean()


# KPI 2: Holiday Sales Uplift
holiday_avg = df.loc[
    df["Is_Holiday_Week"] == "Yes",
    "Weekly_Sales"
].mean()

nonholiday_avg = df.loc[
    df["Is_Holiday_Week"] == "No",
    "Weekly_Sales"
].mean()

holiday_uplift = (
    (holiday_avg - nonholiday_avg)
    / nonholiday_avg
    * 100
)


# KPI 4: Network-level correlation with unemployment
network_unemp_corr = (
    df["Weekly_Sales"].corr(
        df["Unemployment"]
    )
)


# KPI 5: Network-level correlation with fuel price
network_fuel_corr = (
    df["Weekly_Sales"].corr(
        df["Fuel_Price"]
    )
)


# ------------------------------------------------------------
# STORE-LEVEL KPI SCORECARD
# ------------------------------------------------------------

store_kpi = (
    df.groupby("Store", observed=True)
      .agg(
          Total_Sales=("Weekly_Sales", "sum"),
          Weeks_Reported=("Weekly_Sales", "count"),
          Avg_Weekly_Sales=("Weekly_Sales", "mean"),
          Sales_Std_Dev=("Weekly_Sales", "std"),
      )
      .reset_index()
)


# ------------------------------------------------------------
# STORE-LEVEL HOLIDAY PERFORMANCE
# ------------------------------------------------------------

store_holiday = (
    df.pivot_table(
        index="Store",
        columns="Is_Holiday_Week",
        values="Weekly_Sales",
        aggfunc="mean",
        observed=True
    )
    .reset_index()
)

store_holiday = store_holiday.rename(columns={
    "No": "Non_Holiday_Avg_Sales",
    "Yes": "Holiday_Avg_Sales"
})


# Merge holiday metrics into store scorecard
store_kpi = store_kpi.merge(
    store_holiday,
    on="Store",
    how="left"
)


# ------------------------------------------------------------
# STORE-LEVEL HOLIDAY UPLIFT
# ------------------------------------------------------------

store_kpi["Holiday_Uplift_%"] = (
    (
        store_kpi["Holiday_Avg_Sales"]
        - store_kpi["Non_Holiday_Avg_Sales"]
    )
    / store_kpi["Non_Holiday_Avg_Sales"]
    * 100
)


# ------------------------------------------------------------
# STORE-LEVEL SALES VOLATILITY
# ------------------------------------------------------------

# Coefficient of Variation for each individual store:
#
# Store CV = Standard Deviation / Mean
#
# This follows the Exercise 1 KPI definition.

store_kpi["Sales_CV"] = (
    store_kpi["Sales_Std_Dev"]
    / store_kpi["Avg_Weekly_Sales"]
)


# Network Sales Volatility:
# Average of the individual store-level CVs.

network_cv = store_kpi["Sales_CV"].mean()


# ------------------------------------------------------------
# STORE PERFORMANCE VS NETWORK AVERAGE
# ------------------------------------------------------------

store_kpi["Vs_Network_Avg_%"] = (
    (
        store_kpi["Avg_Weekly_Sales"]
        / network_avg
    ) - 1
) * 100


# ------------------------------------------------------------
# BELOW-NETWORK PERFORMANCE FLAG
# ------------------------------------------------------------

store_kpi["Below_15pct_Network_Flag"] = (
    store_kpi["Avg_Weekly_Sales"]
    < NETWORK_BENCHMARK * 0.85
)

wow_by_store = (
    df.groupby("Store", observed=True)["WoW_Sales_Growth_%"]
      .mean()
      .rename("Avg_WoW_Growth_%")
      .reset_index()
)
store_kpi = store_kpi.merge(wow_by_store, on="Store", how="left")

def corr_by_store(data, target):
    records = []
    for store, group in data.groupby("Store", observed=True):
        if group["Weekly_Sales"].nunique() < 2 or group[target].nunique() < 2:
            corr = np.nan
        else:
            corr = group["Weekly_Sales"].corr(group[target])
        records.append((store, corr))
    return pd.DataFrame(records, columns=["Store", f"{target}_Correlation"])

store_kpi = store_kpi.merge(
    corr_by_store(df, "Unemployment"),
    on="Store",
    how="left"
)
store_kpi = store_kpi.merge(
    corr_by_store(df, "Fuel_Price"),
    on="Store",
    how="left"
)

store_kpi = store_kpi.sort_values("Avg_Weekly_Sales", ascending=False)
store_kpi.to_csv(RESULTS_DIR / "store_kpi_scorecard.csv", index=False)

validation = pd.DataFrame([
    ["Network Average Weekly Sales", network_avg, NETWORK_BENCHMARK, network_avg / NETWORK_BENCHMARK - 1],
    ["Holiday Sales Uplift %", holiday_uplift, HOLIDAY_UPLIFT_BENCHMARK, holiday_uplift - HOLIDAY_UPLIFT_BENCHMARK],
    ["Network Sales CV", network_cv, CV_BENCHMARK, network_cv - CV_BENCHMARK],
    ["Network Unemployment Correlation", network_unemp_corr, UNEMP_CORR_BENCHMARK, network_unemp_corr - UNEMP_CORR_BENCHMARK],
    ["Network Fuel Price Correlation", network_fuel_corr, FUEL_CORR_BENCHMARK, network_fuel_corr - FUEL_CORR_BENCHMARK],
], columns=["Metric", "Python_Result", "Exercise_1_Benchmark", "Difference"])
validation.to_csv(RESULTS_DIR / "kpi_validation.csv", index=False)

# ============================================================
# 9. CHART 01 — STORE PERFORMANCE
# ============================================================
store_plot = store_kpi.sort_values("Avg_Weekly_Sales", ascending=True)

fig, ax = plt.subplots(figsize=(12, 9))
ax.barh(store_plot["Store"], store_plot["Avg_Weekly_Sales"])
ax.axvline(
    NETWORK_BENCHMARK,
    linestyle="--",
    linewidth=1.8,
    label=f"Exercise 1 benchmark: {money(NETWORK_BENCHMARK)}"
)
ax.set_title("Walmart Store Performance — Average Weekly Sales", fontsize=16, pad=15)
ax.set_xlabel("Average Weekly Sales")
ax.set_ylabel("Store")
ax.xaxis.set_major_formatter(money_formatter)
ax.legend(loc="lower right")
ax.grid(axis="x", linestyle=":", alpha=0.4)
save_figure(fig, "01_store_performance_avg_weekly_sales.png")

# ============================================================
# 10. CHART 02 — HOLIDAY UPLIFT BY STORE
# ============================================================
uplift_plot = store_kpi.sort_values("Holiday_Uplift_%", ascending=True)

fig, ax = plt.subplots(figsize=(12, 9))
ax.barh(uplift_plot["Store"], uplift_plot["Holiday_Uplift_%"])
ax.axvline(0, linewidth=1)
ax.axvline(
    HOLIDAY_UPLIFT_BENCHMARK,
    linestyle="--",
    linewidth=1.8,
    label=f"Exercise 1 baseline: {HOLIDAY_UPLIFT_BENCHMARK:.1f}%"
)
ax.set_title(
    "Holiday Sales Uplift by Walmart Store",
    fontsize=16, pad=15
)
ax.set_xlabel("Holiday Uplift (%)")
ax.set_ylabel("Store")
ax.xaxis.set_major_formatter(pct_formatter)
ax.legend(loc="lower right")
ax.grid(axis="x", linestyle=":", alpha=0.4)
save_figure(fig, "02_holiday_uplift_by_store.png")

# ============================================================
# 11. CHART 03 — 2011 SLICE HEATMAP
# ============================================================
heat = slice_result.copy().set_index("Store")[[
    "Non_Holiday_Avg_Sales", "Holiday_Avg_Sales"
]]

fig, ax = plt.subplots(figsize=(8, 12))
im = ax.imshow(heat.values, aspect="auto")
ax.set_title(
    "SLICE: 2011 Store × Holiday Sales\n"
    "Date dimension fixed to Year = 2011",
    fontsize=15, pad=15
)
ax.set_xticks(range(2))
ax.set_xticklabels(["Non-Holiday", "Holiday"])
ax.set_yticks(range(len(heat.index)))
ax.set_yticklabels(heat.index)
ax.set_xlabel("Holiday Status")
ax.set_ylabel("Store")
cbar = fig.colorbar(im, ax=ax)
cbar.set_label("Average Weekly Sales")
for i in range(heat.shape[0]):
    for j in range(heat.shape[1]):
        ax.text(
            j, i, f"${heat.iloc[i, j]/1_000_000:.2f}M",
            ha="center", va="center", fontsize=7
        )
save_figure(fig, "03_slice_2011_store_holiday_heatmap.png")

# ============================================================
# 12. CHART 04 — DICE RESULT
# ============================================================
dice_plot = dice_result.sort_values("Avg_Holiday_Sales", ascending=True)

fig, ax = plt.subplots(figsize=(12, 9))
ax.barh(dice_plot["Store"], dice_plot["Avg_Holiday_Sales"])
ax.set_title(
    "DICE: 2011 Holiday Weeks — Average Sales by Store",
    fontsize=16, pad=15
)
ax.set_xlabel("Average Holiday Weekly Sales")
ax.set_ylabel("Store")
ax.xaxis.set_major_formatter(money_formatter)
ax.grid(axis="x", linestyle=":", alpha=0.4)

# Emphasize the top 5 with annotations rather than decorative color coding.
top5 = dice_result.head(5)
for _, row in top5.iterrows():
    ax.annotate(
        f"Top {list(top5['Store']).index(row['Store']) + 1}",
        (row["Avg_Holiday_Sales"], row["Store"]),
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        fontsize=9,
        fontweight="bold"
    )
save_figure(fig, "04_dice_2011_holiday_store_ranking.png")

# ============================================================
# 13. CHART 05 — TIME TREND / HIERARCHY
# ============================================================
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(
    monthly_trend["Year_Month"],
    monthly_trend["Avg_Weekly_Sales"],
    marker="o",
    linewidth=2
)
ax.set_title(
    "Walmart Average Weekly Sales Trend\n"
    "Hierarchy view: Year → Month → Week",
    fontsize=16, pad=15
)
ax.set_xlabel("Month")
ax.set_ylabel("Average Weekly Sales")
ax.yaxis.set_major_formatter(money_formatter)
ax.grid(True, linestyle=":", alpha=0.4)
fig.autofmt_xdate()
save_figure(fig, "05_monthly_sales_trend_hierarchy.png")

# ============================================================
# 14. CHART 06 — WoW GROWTH BY STORE
# ============================================================
wow_plot = store_kpi.sort_values("Avg_WoW_Growth_%", ascending=True)

fig, ax = plt.subplots(figsize=(12, 9))
ax.barh(wow_plot["Store"], wow_plot["Avg_WoW_Growth_%"])
ax.axvline(0, linewidth=1.8)
ax.set_title(
    "Average Week-over-Week Sales Growth by Store",
    fontsize=16, pad=15
)
ax.set_xlabel("Average WoW Sales Growth (%)")
ax.set_ylabel("Store")
ax.xaxis.set_major_formatter(pct_formatter)
ax.grid(axis="x", linestyle=":", alpha=0.4)
save_figure(fig, "06_store_wow_growth.png")

# ============================================================
# 15. CHART 07 — SALES VOLATILITY
# ============================================================
cv_plot = store_kpi.sort_values("Sales_CV", ascending=True)

fig, ax = plt.subplots(figsize=(12, 9))
ax.barh(cv_plot["Store"], cv_plot["Sales_CV"])
ax.axvline(
    CV_BENCHMARK,
    linestyle="--",
    linewidth=1.8,
    label=f"Exercise 1 network baseline: {CV_BENCHMARK:.2f}"
)
ax.set_title(
    "Store Sales Volatility — Coefficient of Variation",
    fontsize=16, pad=15
)
ax.set_xlabel("Coefficient of Variation")
ax.set_ylabel("Store")
ax.legend(loc="lower right")
ax.grid(axis="x", linestyle=":", alpha=0.4)
save_figure(fig, "07_store_sales_volatility_cv.png")

# ============================================================
# 16. CHART 08 — UNEMPLOYMENT SENSITIVITY
# ============================================================
fig, ax = plt.subplots(figsize=(10, 7))
ax.scatter(
    store_kpi["Unemployment_Correlation"],
    store_kpi["Avg_Weekly_Sales"],
    s=60
)
ax.axvline(
    UNEMP_CORR_BENCHMARK,
    linestyle="--",
    linewidth=1.8,
    label=f"Exercise 1 baseline: {UNEMP_CORR_BENCHMARK:.2f}"
)
ax.set_title(
    "Sales vs Unemployment Sensitivity by Store",
    fontsize=16, pad=15
)
ax.set_xlabel("Weekly Sales ↔ Unemployment Correlation")
ax.set_ylabel("Average Weekly Sales")
ax.yaxis.set_major_formatter(money_formatter)
ax.legend(loc="best")
ax.grid(True, linestyle=":", alpha=0.4)

for _, row in store_kpi.nlargest(5, "Avg_Weekly_Sales").iterrows():
    ax.annotate(
        f"Store {row['Store']}",
        (row["Unemployment_Correlation"], row["Avg_Weekly_Sales"]),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=8
    )
save_figure(fig, "08_unemployment_sensitivity.png")

# ============================================================
# 17. CHART 09 — FUEL PRICE SENSITIVITY
# ============================================================
fig, ax = plt.subplots(figsize=(10, 7))
ax.scatter(
    store_kpi["Fuel_Price_Correlation"],
    store_kpi["Avg_Weekly_Sales"],
    s=60
)
ax.axvline(
    FUEL_CORR_BENCHMARK,
    linestyle="--",
    linewidth=1.8,
    label=f"Exercise 1 baseline: {FUEL_CORR_BENCHMARK:.2f}"
)
ax.set_title(
    "Sales vs Fuel Price Sensitivity by Store",
    fontsize=16, pad=15
)
ax.set_xlabel("Weekly Sales ↔ Fuel Price Correlation")
ax.set_ylabel("Average Weekly Sales")
ax.yaxis.set_major_formatter(money_formatter)
ax.legend(loc="best")
ax.grid(True, linestyle=":", alpha=0.4)
save_figure(fig, "09_fuel_price_sensitivity.png")

# ============================================================
# 18. CHART 10 — NETWORK KPI BENCHMARKS
# ============================================================
kpi_visual = pd.DataFrame({
    "KPI": [
        "Network Avg Weekly Sales",
        "Holiday Uplift %",
        "Network Sales CV",
        "Unemployment Corr.",
        "Fuel Price Corr."
    ],
    "Python_Value": [
        network_avg,
        holiday_uplift,
        network_cv,
        network_unemp_corr,
        network_fuel_corr
    ],
    "Benchmark": [
        NETWORK_BENCHMARK,
        HOLIDAY_UPLIFT_BENCHMARK,
        CV_BENCHMARK,
        UNEMP_CORR_BENCHMARK,
        FUEL_CORR_BENCHMARK
    ]
})
kpi_visual.to_csv(RESULTS_DIR / "kpi_benchmark_visual_data.csv", index=False)

# Use indexed comparison so different units do not share a misleading axis.
indices = np.arange(len(kpi_visual))
python_indexed = []
benchmark_indexed = []

for _, r in kpi_visual.iterrows():
    if r["Benchmark"] == 0:
        python_indexed.append(np.nan)
        benchmark_indexed.append(np.nan)
    else:
        python_indexed.append(r["Python_Value"] / r["Benchmark"] * 100)
        benchmark_indexed.append(100)

fig, ax = plt.subplots(figsize=(11, 6))
ax.bar(indices - 0.2, python_indexed, width=0.4, label="Python result")
ax.bar(indices + 0.2, benchmark_indexed, width=0.4, label="Exercise 1 benchmark")
ax.axhline(100, linestyle="--", linewidth=1.2)
ax.set_xticks(indices)
ax.set_xticklabels(kpi_visual["KPI"], rotation=20, ha="right")
ax.set_ylabel("Indexed value (benchmark = 100)")
ax.set_title(
    "Walmart KPI Validation — Python Result vs Exercise 1 Benchmark",
    fontsize=16, pad=15
)
ax.legend()
ax.grid(axis="y", linestyle=":", alpha=0.4)
save_figure(fig, "10_kpi_validation_indexed.png")

# ============================================================
# 19. VISUAL CATALOG
# ============================================================
catalog = pd.DataFrame([
    ["01_store_performance_avg_weekly_sales.png", "Store Performance", "Compares average weekly sales of all stores and shows the Exercise 1 network benchmark.", "Task 2b / Store comparison"],
    ["02_holiday_uplift_by_store.png", "Holiday Impact", "Shows which stores gain or lose sales during holiday weeks relative to non-holiday weeks and compares with the 7.8% baseline.", "KPI / Holiday analysis"],
    ["03_slice_2011_store_holiday_heatmap.png", "SLICE", "Visual representation of the 2011 slice: Year fixed at 2011; Store × Holiday status remains.", "Task 2a / Slice"],
    ["04_dice_2011_holiday_store_ranking.png", "DICE", "Visual representation of the 2011 holiday dice: Year=2011 AND Holiday=Yes, ranked by average holiday sales.", "Task 2a / Dice"],
    ["05_monthly_sales_trend_hierarchy.png", "Hierarchy Trend", "Shows monthly roll-up and supports the Year → Month → Week analytical hierarchy.", "Task 2a bonus / Task 2b"],
    ["06_store_wow_growth.png", "WoW Growth", "Compares average weekly growth by store and shows the zero-growth reference.", "KPI analysis"],
    ["07_store_sales_volatility_cv.png", "Sales Volatility", "Ranks stores by coefficient of variation and shows the Exercise 1 CV baseline.", "KPI analysis"],
    ["08_unemployment_sensitivity.png", "Unemployment Sensitivity", "Shows the relationship between store-level sales performance and unemployment correlation.", "KPI analysis"],
    ["09_fuel_price_sensitivity.png", "Fuel Sensitivity", "Shows the relationship between store-level sales performance and fuel-price correlation.", "KPI analysis"],
    ["10_kpi_validation_indexed.png", "KPI Validation", "Compares Python-calculated network KPI values against Exercise 1 benchmarks on a common indexed scale.", "Validation"],
], columns=["File", "Visual", "What It Answers", "Purpose"])
catalog.to_csv(RESULTS_DIR / "visual_catalog.csv", index=False)

# ============================================================
# 20. EXECUTION SUMMARY
# ============================================================
summary = pd.DataFrame([
    ["Input rows", len(df)],
    ["Input columns", len(df.columns)],
    ["Stores", df["Store"].nunique()],
    ["Date range", f"{df['Date'].min().date()} to {df['Date'].max().date()}"],
    ["Cube", "Store x Year x Holiday -> Weekly_Sales"],
    ["Slice", "Year = 2011"],
    ["Dice", "Year = 2011 AND Holiday = Yes"],
    ["Focused Dice", "Year = 2011 AND Month = 12 AND Holiday = Yes"],
    ["Hierarchy", "Year -> Month -> Week"],
], columns=["Item", "Value"])
summary.to_csv(RESULTS_DIR / "project_summary.csv", index=False)

print("\n" + "=" * 90)
print("OLAP ANALYSIS COMPLETE")
print("=" * 90)
print(f"Generated analytical CSVs in: {RESULTS_DIR}")
print(f"Generated visual PNGs in:      {CHART_DIR}")
print(f"Network Average Weekly Sales: ${network_avg:,.2f}")
print(f"Holiday Sales Uplift:         {holiday_uplift:.2f}%")
print(f"Network Sales CV:              {network_cv:.4f}")
print(f"Unemployment Correlation:     {network_unemp_corr:.4f}")
print(f"Fuel Price Correlation:        {network_fuel_corr:.4f}")
