# Walmart BI Exercise 3 & 4

This project uses the supplied Walmart cleaned and raw datasets.

## Exercise 3 — Time-Series Model to Forecast Monthly Sales

- Source: `data/Walmart_Sales_Cleaned.csv`
- Weekly store sales are aggregated to network-level monthly sales.
- The final 6 months are held out for evaluation.
- Candidate SARIMA models are compared using AIC on the training period only.
- The selected seasonal ARIMA model is evaluated using MAE, RMSE and MAPE.
- A final model is refit on all observed months and produces a 6-month future forecast.

### Actual run result

- Best model selected by training AIC: SARIMA(1,1,2)x(0,0,1,12)
- MAE: 26,670,814.82
- RMSE: 31,266,273.42
- MAPE: 13.06%

The hold-out period is May 2012 through October 2012.

## Exercise 4 — Classification Model to Predict High-Sales Weeks

The original workbook wording refers to customer churn, but the supplied Walmart dataset has no customer identifier or churn target. Therefore, this implementation adapts the classification task to a Walmart-specific target: **High-Sales Week**.

A store-week is labelled High Sales (`1`) when its Weekly_Sales is above that store's historical median; otherwise it is Low Sales (`0`). Weekly_Sales itself is not used as a model feature.

Model: Logistic Regression.

Features:
- Store
- Holiday_Flag
- Temperature
- Fuel_Price
- CPI
- Unemployment
- Year
- Month
- Week_of_Year

### Actual run result

- Accuracy: 0.6900
- Precision: 0.6869
- Recall: 0.6901
- F1 Score: 0.6885
- ROC-AUC: 0.7638
- Confusion matrix:

| | Predicted Low | Predicted High |
|---|---:|---:|
| Actual Low | 447 | 201 |
| Actual High | 198 | 441 |

## Run

From the project root:

```bash
pip install -r requirements.txt
python exercise_3_forecasting/walmart_sales_forecasting.py
python exercise_4_classification/walmart_high_sales_classification.py
```

Outputs are written to each exercise's `outputs` folder.
