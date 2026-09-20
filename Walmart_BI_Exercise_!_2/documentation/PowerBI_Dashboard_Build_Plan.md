# Power BI Dashboard Build Plan

## Dashboard title
WALMART WEEKLY SALES PERFORMANCE

### Suggested subtitle
Store Performance • Holiday Impact • Sales Trends • Economic Sensitivity

## Required KPI cards
- Average Weekly Sales per Store
- Holiday Sales Uplift %
- Average WoW Sales Growth
- Optional: Sales Volatility (CV)

## Required / recommended visuals
1. Line chart — Weekly/Monthly Average Sales Trend
2. Bar chart — Average Weekly Sales by Store
3. Clustered column — Holiday vs Non-Holiday Sales
4. Bar chart — Store Sales Volatility
5. Scatter — Average Weekly Sales vs Unemployment
6. Scatter — Average Weekly Sales vs Fuel Price

## Interactive slicers
- Year / Date
- Store
- Holiday Week

Make sure at least two slicers affect multiple visuals.

## Drill-down
Create a date hierarchy:
Year → Month → Week

Use it on the trend chart so the reviewer can move from annual to monthly to weekly detail.

## Design principles
- Keep one page.
- Put KPI cards at the top.
- Put the main time trend centrally.
- Put store comparison and holiday analysis below.
- Keep sensitivity/volatility visuals in the lower section.
- Use clear axis labels and titles.
- Use color intentionally, especially for KPI target/flag states.
- Avoid overcrowding.

## Power BI deliverables
Save:
`powerbi/Walmart_OLAP_Dashboard.pbix`

Export:
`powerbi/Walmart_OLAP_Dashboard.pdf` or `.png`
