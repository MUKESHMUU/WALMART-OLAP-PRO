import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings('ignore')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data', 'Walmart_Sales_Cleaned.csv')
OUT = os.path.join(BASE, 'exercise_3_forecasting', 'outputs')
os.makedirs(OUT, exist_ok=True)

# 1. Load and prepare weekly Walmart data
df = pd.read_csv(DATA)
df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)

# 2. Aggregate store-week sales into a network-level monthly time series.
monthly = (
    df.groupby(df['Date'].dt.to_period('M'))['Weekly_Sales']
      .sum()
      .rename('Monthly_Sales')
      .to_frame()
      .reset_index()
)
monthly['Date'] = monthly['Date'].dt.to_timestamp()
monthly.to_csv(os.path.join(OUT, 'monthly_sales.csv'), index=False)

# 3. Hold out the final six months for objective evaluation.
TEST_MONTHS = 6
series = monthly.set_index('Date')['Monthly_Sales'].asfreq('MS')
train = series.iloc[:-TEST_MONTHS]
test = series.iloc[-TEST_MONTHS:]

# 4. Select a SARIMA model by AIC on the training period only.
#    Seasonal period = 12 months to capture annual sales patterns.
candidates = []
orders = [(0,1,1), (1,1,0), (1,1,1), (2,1,1), (1,1,2), (2,1,2)]
seasonal_orders = [(0,0,1,12), (1,0,0,12), (1,0,1,12)]
for order in orders:
    for seasonal_order in seasonal_orders:
        try:
            model = SARIMAX(
                train,
                order=order,
                seasonal_order=seasonal_order,
                trend='n',
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)
            candidates.append({
                'Order': str(order),
                'Seasonal_Order': str(seasonal_order),
                'AIC': model.aic,
            })
        except Exception:
            continue

model_selection = pd.DataFrame(candidates).sort_values('AIC').reset_index(drop=True)
model_selection.to_csv(os.path.join(OUT, 'model_selection_aic.csv'), index=False)

best_order = eval(model_selection.loc[0, 'Order'])
best_seasonal = eval(model_selection.loc[0, 'Seasonal_Order'])

# 5. Fit selected model on training data and forecast the hold-out period.
model = SARIMAX(
    train,
    order=best_order,
    seasonal_order=best_seasonal,
    trend='n',
    enforce_stationarity=False,
    enforce_invertibility=False,
).fit(disp=False)
forecast_obj = model.get_forecast(steps=TEST_MONTHS)
forecast = forecast_obj.predicted_mean
conf = forecast_obj.conf_int()

# 6. Evaluate against the hold-out period.
mae = mean_absolute_error(test, forecast)
rmse = np.sqrt(mean_squared_error(test, forecast))
mape = np.mean(np.abs((test - forecast) / test)) * 100
metrics = pd.DataFrame([{
    'Model': f'SARIMA{best_order}x{best_seasonal}',
    'Train_Months': len(train),
    'Test_Months': len(test),
    'MAE': mae,
    'RMSE': rmse,
    'MAPE_%': mape,
    'AIC': model.aic,
}])
metrics.to_csv(os.path.join(OUT, 'forecast_metrics.csv'), index=False)

results = pd.DataFrame({
    'Date': test.index,
    'Actual_Sales': test.values,
    'Forecast_Sales': forecast.values,
    'Absolute_Error': np.abs(test.values - forecast.values),
    'Absolute_Percentage_Error_%': np.abs((test.values - forecast.values) / test.values) * 100,
})
results.to_csv(os.path.join(OUT, 'forecast_results.csv'), index=False)

# 7. Refit on all observed months and generate a six-month future forecast.
full_model = SARIMAX(
    series,
    order=best_order,
    seasonal_order=best_seasonal,
    trend='n',
    enforce_stationarity=False,
    enforce_invertibility=False,
).fit(disp=False)
future_obj = full_model.get_forecast(steps=6)
future = future_obj.predicted_mean
future_conf = future_obj.conf_int()
future_results = pd.DataFrame({
    'Date': future.index,
    'Forecast_Sales': future.values,
    'Lower_CI': future_conf.iloc[:, 0].values,
    'Upper_CI': future_conf.iloc[:, 1].values,
})
future_results.to_csv(os.path.join(OUT, 'future_6_month_forecast.csv'), index=False)

# 8. Actual vs forecast chart.
plt.figure(figsize=(12, 6))
plt.plot(train.index, train.values, label='Training Actual')
plt.plot(test.index, test.values, label='Hold-out Actual', linewidth=2)
plt.plot(forecast.index, forecast.values, label='SARIMA Forecast', linewidth=2)
plt.fill_between(forecast.index, conf.iloc[:, 0], conf.iloc[:, 1], alpha=0.15, label='95% Confidence Interval')
plt.title('Walmart Monthly Sales: Actual vs SARIMA Forecast')
plt.xlabel('Month')
plt.ylabel('Monthly Sales')
plt.legend()
plt.grid(alpha=0.25)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'actual_vs_forecast.png'), dpi=180)
plt.close()

print('Exercise 3 completed.')
print('Best model:', f'SARIMA{best_order}x{best_seasonal}')
print(f'MAE: {mae:,.2f}')
print(f'RMSE: {rmse:,.2f}')
print(f'MAPE: {mape:.2f}%')
