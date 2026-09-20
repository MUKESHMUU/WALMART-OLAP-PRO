# Walmart OLAP Cube Design & Operations

## 1. Cube Design

### Business grain
Each record represents the weekly sales of one Walmart store for one specific week.

### Measure
**Weekly_Sales** is the primary analytical measure because the Exercise 1 KPI framework is centered on store-level sales performance.

### Dimensions
1. **Store** — identifies the Walmart store.
2. **Date** — supports Year, Month and Week analysis.
3. **Holiday** — identifies holiday versus non-holiday weeks.

### Hierarchy
**Year → Month → Week**

This hierarchy supports moving between high-level annual performance and detailed weekly performance.

### Conceptual cube

Store × Date × Holiday → Weekly_Sales

The cube allows the same sales measure to be analyzed across combinations of store, time and holiday status.

---

## 2. Slice Operation

### Operation
**Slice: Year = 2011**

The Date dimension is fixed to one value (2011), leaving Store and Holiday as the main analytical dimensions.

### Business question
How did average weekly sales differ across Walmart stores between holiday and non-holiday weeks during 2011?

### Output
`olap_results/slice_year_2011.csv`

Insert the generated screenshot/table here.

### Interpretation
Write 2–3 sentences describing the strongest/weakest store patterns and the holiday effect observed in the 2011 slice.

---

## 3. Dice Operation

### Operation
**Dice: Year = 2011 AND Holiday = Yes**

Two dimensions are filtered simultaneously: Date (Year) and Holiday.

### Business question
Which Walmart stores generated the highest average weekly sales during holiday weeks in 2011?

### Output
`olap_results/dice_2011_holiday.csv`

Insert the generated screenshot/table here.

### Interpretation
Write 2–3 sentences explaining which stores stand out and what this suggests for holiday inventory/staffing decisions.

---

## 4. Optional Drill-down / Roll-up

Hierarchy:

**Year → Month → Week**

- Roll-up summarizes detailed weekly observations to year level.
- Drill-down moves from year to month and then week.

Outputs:
- `olap_results/rollup_year.csv`
- `olap_results/drilldown_year_month_week.csv`

---

## 5. Link to the Business Problem and KPIs

The dashboard should help decision-makers monitor store sales performance, holiday demand uplift, sales growth and sales volatility, while also exploring sensitivity to local unemployment and fuel prices. The dashboard should use interactive filters so a decision-maker can isolate stores, years and holiday periods and investigate the causes of performance differences.
