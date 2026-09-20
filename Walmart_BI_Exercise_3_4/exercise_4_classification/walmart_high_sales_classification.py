import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, classification_report
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data', 'Walmart_Sales_Cleaned.csv')
OUT = os.path.join(BASE, 'exercise_4_classification', 'outputs')
os.makedirs(OUT, exist_ok=True)

# 1. Load weekly Walmart data.
df = pd.read_csv(DATA)
df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
df['Week_of_Year'] = df['Date'].dt.isocalendar().week.astype(int)

# 2. Define a store-relative classification target.
#    A week is High Sales when its sales exceed that store's historical median.
#    This avoids simply labelling all naturally large stores as High Sales.
store_median = df.groupby('Store')['Weekly_Sales'].transform('median')
df['High_Sales'] = (df['Weekly_Sales'] > store_median).astype(int)

# Weekly sales is the target source and is deliberately excluded from model features.
features = [
    'Store', 'Holiday_Flag', 'Temperature', 'Fuel_Price',
    'CPI', 'Unemployment', 'Year', 'Month', 'Week_of_Year'
]
categorical = ['Store', 'Holiday_Flag', 'Month', 'Week_of_Year']
numeric = ['Temperature', 'Fuel_Price', 'CPI', 'Unemployment', 'Year']

X = df[features]
y = df['High_Sales']

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

preprocessor = ColumnTransformer([
    ('categorical', OneHotEncoder(handle_unknown='ignore'), categorical),
    ('numeric', StandardScaler(), numeric),
])

model = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', LogisticRegression(max_iter=3000)),
])
model.fit(X_train, y_train)

pred = model.predict(X_test)
prob = model.predict_proba(X_test)[:, 1]
cm = confusion_matrix(y_test, pred)

accuracy = accuracy_score(y_test, pred)
precision = precision_score(y_test, pred, zero_division=0)
recall = recall_score(y_test, pred, zero_division=0)
f1 = f1_score(y_test, pred, zero_division=0)
auc = roc_auc_score(y_test, prob)

metrics = pd.DataFrame([{
    'Model': 'Logistic Regression',
    'Target': 'High_Sales (store-week sales above store median)',
    'Train_Rows': len(X_train),
    'Test_Rows': len(X_test),
    'Accuracy': accuracy,
    'Precision': precision,
    'Recall': recall,
    'F1_Score': f1,
    'ROC_AUC': auc,
}])
metrics.to_csv(os.path.join(OUT, 'classification_metrics.csv'), index=False)

# Confusion matrix as a CSV for documentation.
pd.DataFrame(
    cm,
    index=['Actual Low', 'Actual High'],
    columns=['Predicted Low', 'Predicted High']
).to_csv(os.path.join(OUT, 'confusion_matrix.csv'))

# Test predictions for traceability.
predictions = X_test.copy()
predictions['Actual_High_Sales'] = y_test.values
predictions['Predicted_High_Sales'] = pred
predictions['Predicted_Probability'] = prob
predictions.to_csv(os.path.join(OUT, 'predictions.csv'), index=False)

# Classification report.
report = classification_report(y_test, pred, target_names=['Low Sales', 'High Sales'], output_dict=True)
pd.DataFrame(report).transpose().to_csv(os.path.join(OUT, 'classification_report.csv'))

# Confusion matrix chart.
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(cm)
ax.set_xticks([0, 1], ['Predicted Low', 'Predicted High'])
ax.set_yticks([0, 1], ['Actual Low', 'Actual High'])
ax.set_title('Logistic Regression Confusion Matrix')
for i in range(2):
    for j in range(2):
        ax.text(j, i, cm[i, j], ha='center', va='center', fontsize=14)
ax.set_xlabel('Predicted Class')
ax.set_ylabel('Actual Class')
fig.colorbar(im, ax=ax)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'confusion_matrix.png'), dpi=180)
plt.close()

# Class distribution chart.
counts = y.value_counts().sort_index()
plt.figure(figsize=(7, 5))
plt.bar(['Low Sales', 'High Sales'], [counts.get(0, 0), counts.get(1, 0)])
plt.title('High-Sales Classification Target Distribution')
plt.ylabel('Number of Store-Weeks')
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'class_distribution.png'), dpi=180)
plt.close()

print('Exercise 4 completed.')
print(f'Accuracy: {accuracy:.4f}')
print(f'Precision: {precision:.4f}')
print(f'Recall: {recall:.4f}')
print(f'F1: {f1:.4f}')
print(f'ROC-AUC: {auc:.4f}')
print('Confusion matrix:')
print(cm)
