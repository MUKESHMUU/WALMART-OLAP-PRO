# Walmart OLAP & Interactive BI Dashboard — Exercise 2

## Project purpose
This project implements the Walmart Exercise 2 OLAP workflow using Python/pandas for the cube, Slice, Dice, and optional Roll-up/Drill-down, followed by an interactive Power BI dashboard.

## Dataset
Cleaned Walmart weekly-sales dataset from Exercise 1.

- Rows: 6,435
- Columns: 14
- Stores: 45
- Date range: 2010-01-10 to 2012-12-10
- Grain: one store-week record

## OLAP model
- **Fact/business event:** weekly sales for a Walmart store
- **Primary measure:** Weekly_Sales
- **Dimensions:** Store, Date, Holiday
- **Hierarchy:** Year → Month → Week

## Required OLAP operations
### Slice
**Year = 2011**

Cross-tab:
- Store
- Holiday status
- Average Weekly Sales

Output:
`olap_results/slice_year_2011.csv`

### Dice
**Year = 2011 AND Holiday = Yes**

Output:
`olap_results/dice_2011_holiday.csv`

### Focused Dice
**Year = 2011 AND Month = 12 AND Holiday = Yes**

Output:
`olap_results/dice_2011_december_holiday.csv`

### Bonus
- Roll-up: Year
- Drill-down: Year → Month → Week

Outputs:
- `olap_results/rollup_year.csv`
- `olap_results/drilldown_year_month_week.csv`

## Power BI
Use the cleaned dataset/model for the interactive dashboard. The Python OLAP result tables are evidence/validation outputs and can also be imported when a static OLAP visual is useful.

Recommended dashboard components:
1. KPI Card — Average Weekly Sales per Store
2. KPI Card — Holiday Sales Uplift %
3. KPI Card — Average WoW Sales Growth
4. Line chart — Weekly/Monthly Sales Trend
5. Bar chart — Store Performance
6. Bar/column chart — Holiday vs Non-Holiday Sales
7. Scatter — Sales vs Unemployment or Fuel Price
8. Optional volatility ranking

Recommended slicers:
- Year / Date
- Store
- Holiday Week

Recommended hierarchy:
- Year → Month → Week

## Validation
`olap_results/kpi_validation.csv` contains the Python-calculated network values that can be used to cross-check corresponding Power BI measures.

## Files
- `data/` — source datasets
- `python/` — reproducible OLAP script
- `olap_results/` — cube, slice, dice, drill-down and KPI outputs
- `outputs/charts/` — supporting analytical charts
- `documentation/` — assignment documentation templates
- `powerbi/` — place the final `.pbix` and exported `.pdf/.png` here
