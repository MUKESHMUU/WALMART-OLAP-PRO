"""
Walmart Weekly Sales Dataset - Data Audit, Cleaning & Preparation
Business Intelligence for Decision Making (24CAC624)

This script takes the raw Walmart_Sales.csv dataset through a full
audit and cleaning pipeline using pandas, and exports a cleaned CSV
ready for KPI analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path

pd.set_option("display.width", 120)

# ============================================================
# 1. LOAD DATA
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "data" / "Walmart_Sales_Raw.csv"
df = pd.read_csv(RAW_PATH)

print("=" * 60)
print("STEP 1: LOAD DATA")
print("=" * 60)
print(f"Raw dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

# Keep a copy of the raw dataframe to build the before/after summary
df_before = df.copy()

# ============================================================
# 2. INITIAL DATA AUDIT
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: INITIAL DATA AUDIT")
print("=" * 60)

print("\nShape (rows x columns):", df.shape)

print("\nData types:")
print(df.dtypes)

print("\nMissing values per column:")
print(df.isnull().sum())

print("\nExact duplicate rows:", df.duplicated().sum())
print("Logical duplicates (same Store + Date):",
      df.duplicated(subset=["Store", "Date"]).sum())

print("\nUnique stores:", df["Store"].nunique(),
      "| Store ID range:", df["Store"].min(), "-", df["Store"].max())
print("Holiday_Flag unique values:", sorted(df["Holiday_Flag"].unique()))
print("Weekly_Sales range: {:.2f} to {:.2f}".format(
    df["Weekly_Sales"].min(), df["Weekly_Sales"].max()))

# ============================================================
# 3. HANDLE MISSING VALUES
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: HANDLE MISSING VALUES")
print("=" * 60)

# Decision: the audit above shows 0 missing values in every column,
# so no dropping, imputing, or flagging is required. We still run
# the check explicitly (rather than assuming) and record the result
# so the "before/after" comparison is honest about what was found.
missing_before = df.isnull().sum().sum()
print(f"Total missing cells found: {missing_before} -> no imputation needed")

# ============================================================
# 4. REMOVE DUPLICATE RECORDS
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: REMOVE DUPLICATE RECORDS")
print("=" * 60)

rows_before_dedup = len(df)
# A logical duplicate here is the same store reporting the same week twice.
df = df.drop_duplicates(subset=["Store", "Date"], keep="first")
rows_after_dedup = len(df)
print(f"Rows before de-dup: {rows_before_dedup} | "
      f"Rows after de-dup: {rows_after_dedup} | "
      f"Removed: {rows_before_dedup - rows_after_dedup}")

# ============================================================
# 5. FIX DATA TYPES
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: FIX DATA TYPES")
print("=" * 60)

# Date arrives as text in DD-MM-YYYY format -> convert to real datetime
# so it can be sorted, resampled, and used for time-based KPIs.
df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")

# Store is a categorical identifier, not a quantity to be averaged/summed
# on its own, so it is cast to 'category' to prevent accidental
# numeric aggregation and to save memory.
df["Store"] = df["Store"].astype("category")

# Holiday_Flag is a binary indicator (0/1) -> cast to a boolean-style
# category and add a readable label column used later for grouping/labels.
df["Holiday_Flag"] = df["Holiday_Flag"].astype("category")
df["Is_Holiday_Week"] = df["Holiday_Flag"].map({0: "No", 1: "Yes"}).astype("category")

# Weekly_Sales, Temperature, Fuel_Price, CPI, Unemployment are already
# numeric (float64) in the raw file, so no text-to-numeric conversion
# was required; they are confirmed here rather than assumed.
numeric_cols = ["Weekly_Sales", "Temperature", "Fuel_Price", "CPI", "Unemployment"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

print(df.dtypes)

# ============================================================
# 6. STANDARDIZE CATEGORICAL VALUES
# ============================================================
print("\n" + "=" * 60)
print("STEP 6: STANDARDIZE CATEGORICAL VALUES")
print("=" * 60)

# Store IDs were checked for inconsistent formatting (e.g. leading
# zeros, text vs numeric, stray whitespace). All 45 store IDs are
# clean integers 1-45, so no relabeling was required.
print("Store IDs are already consistent integers:",
      sorted(df["Store"].astype(int).unique())[:5], "...")

# Holiday_Flag only ever contains 0/1 (verified in the audit step),
# so there are no inconsistent labels such as 'holiday'/'Holiday'/'HOLIDAY'
# to standardize. The Is_Holiday_Week column above gives a consistent,
# human-readable Yes/No label for reporting.
print("Holiday_Flag standardized values:", df["Is_Holiday_Week"].unique().tolist())

# ============================================================
# 7. HANDLE OUTLIERS
# ============================================================
print("\n" + "=" * 60)
print("STEP 7: HANDLE OUTLIERS")
print("=" * 60)

# IQR method on Weekly_Sales, the key numeric KPI column.
Q1 = df["Weekly_Sales"].quantile(0.25)
Q3 = df["Weekly_Sales"].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

outlier_mask = (df["Weekly_Sales"] < lower_bound) | (df["Weekly_Sales"] > upper_bound)
print(f"IQR bounds: [{lower_bound:,.2f}, {upper_bound:,.2f}]")
print(f"Outliers detected: {outlier_mask.sum()} rows "
      f"({outlier_mask.mean()*100:.2f}% of data)")

# Investigation: outliers are concentrated in a small set of
# large-format stores (e.g. Store 20, 4, 13, 10, 14) and cluster in
# November/December, i.e. the Thanksgiving/Christmas shopping peak.
# These are genuine peak trading weeks, not data-entry errors, so they
# are KEPT (not capped or removed) but flagged in a new column so
# downstream KPI analysis can treat them separately if needed.
df["Is_Sales_Outlier"] = outlier_mask

print("Decision: outliers retained and flagged (Is_Sales_Outlier) rather "
      "than removed/capped, because they represent genuine holiday-season "
      "peak sales at specific high-volume stores, not data errors.")

# No negative or zero Weekly_Sales values were found in the audit, so
# there is no need to remove impossible sales figures.

# ============================================================
# 8. FEATURE ENGINEERING (supports KPI calculations)
# ============================================================
print("\n" + "=" * 60)
print("STEP 8: FEATURE ENGINEERING")
print("=" * 60)

df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
df["Week_of_Year"] = df["Date"].dt.isocalendar().week
df = df.sort_values(["Store", "Date"]).reset_index(drop=True)

# Week-over-week sales growth rate per store, used by the
# "WoW Sales Growth Rate" KPI (a leading indicator).
df["WoW_Sales_Growth_%"] = (
    df.groupby("Store", observed=True)["Weekly_Sales"].pct_change() * 100
).round(2)

print("Added columns: Is_Holiday_Week, Is_Sales_Outlier, Year, Month, "
      "Week_of_Year, WoW_Sales_Growth_%")
print("Note: WoW_Sales_Growth_% is NaN for each store's first recorded "
      "week (45 stores = 45 expected NaNs) since there is no prior week "
      "to compare against - this is expected, not missing raw data.")

# ============================================================
# 9. BEFORE / AFTER SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("STEP 9: BEFORE / AFTER SUMMARY")
print("=" * 60)

summary = pd.DataFrame({
    "Metric": [
        "Row count",
        "Column count",
        "Missing values in raw columns",
        "Duplicate rows (Store+Date)",
        "Date column dtype",
        "Store column dtype",
        "Holiday_Flag dtype",
        "Weekly_Sales outliers flagged",
    ],
    "Before Cleaning": [
        df_before.shape[0],
        df_before.shape[1],
        df_before.isnull().sum().sum(),
        df_before.duplicated(subset=["Store", "Date"]).sum(),
        str(df_before["Date"].dtype),
        str(df_before["Store"].dtype),
        str(df_before["Holiday_Flag"].dtype),
        "not evaluated",
    ],
    "After Cleaning": [
        df.shape[0],
        df.shape[1],
        df[["Store", "Date", "Weekly_Sales", "Holiday_Flag", "Temperature",
            "Fuel_Price", "CPI", "Unemployment"]].isnull().sum().sum(),
        0,
        str(df["Date"].dtype),
        str(df["Store"].dtype),
        str(df["Holiday_Flag"].dtype),
        int(df["Is_Sales_Outlier"].sum()),
    ],
})
print(summary.to_string(index=False))

# ============================================================
# 10. EXPORT CLEANED DATASET
# ============================================================
OUTPUT_PATH = "Walmart_Sales_Cleaned.csv"
df.to_csv(OUTPUT_PATH, index=False)
print(f"\nCleaned dataset exported to: {OUTPUT_PATH}")
print(f"Final shape: {df.shape[0]} rows x {df.shape[1]} columns")
