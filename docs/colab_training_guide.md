# Google Colab Model Training Guide

This guide walks you through uploading your dataset (`pharmacy_inventory_dataset_10000_rows.csv`), preprocessing it, training an XGBoost model, visualizing feature importance, and generating order quantities.

---

## Step 1: Open Google Colab

1. Navigate to [colab.research.google.com](https://colab.research.google.com/).
2. Create a new Python 3 notebook.
3. In the left-hand panel, click the **Folder icon** and upload your `pharmacy_inventory_dataset_10000_rows.csv` file.

---

## Step 2: Install Required Libraries

Run this command in the first cell of your notebook to ensure all dependencies are present:

```python
!pip install xgboost pandas numpy scikit-learn matplotlib
```

---

## Step 3: Run the Training Code

Create a new cell, copy the entire block of code below, paste it, and run it. This script handles:
- Loading the dataset
- Creating the external `search_trend_score` and `news_signal_score` signals
- Data cleaning and one-hot encoding
- Splitting the data chronologically (training on 2022–2024, testing on 2025)
- Training the XGBoost model
- Evaluating performance (MAE and R² score)
- Saving the trained model files for deployment

```python
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import pickle
import os

# --- 1. Load the Dataset ---
dataset_path = 'pharmacy_inventory_dataset_10000_rows.csv'
if not os.path.exists(dataset_path):
    raise FileNotFoundError(f"Please upload '{dataset_path}' to your Google Colab folder.")

df = pd.read_csv(dataset_path)
print(f"Dataset successfully loaded. Shape: {df.shape}")

# --- 2. Feature Engineering for External Signals ---
np.random.seed(42)

def calculate_search_trend_score(row):
    score = 40.0
    category = str(row['category'])
    season = str(row['season'])
    event_type = str(row['event_type'])
    
    if category == 'Respiratory' or category == 'Antibiotic':
        if season == 'Winter' or event_type in ['Flu_Outbreak', 'Cold_Wave']:
            score += 35.0
    elif category == 'Allergy' or event_type == 'Allergy_Season':
        score += 40.0
        
    if event_type == 'Heat_Wave':
        if category in ['Diabetes', 'Cardiology']:
            score += 15.0
            
    # Add minor noise
    score += np.random.uniform(-5, 5)
    return min(100.0, max(0.0, score))

def calculate_news_signal_score(row):
    score = (float(row['impact_score']) / 10.0)
    score += np.random.uniform(-0.5, 0.5)
    return min(10.0, max(0.0, score))

print("Engineering search_trend_score and news_signal_score...")
df['search_trend_score'] = df.apply(calculate_search_trend_score, axis=1)
df['news_signal_score'] = df.apply(calculate_news_signal_score, axis=1)

# --- 3. Preprocessing and One-Hot Encoding ---
# Drop identifiers that are not predictive inputs
id_cols = ['product_id', 'supplier_id']
df_prepped = df.drop(columns=id_cols)

# Ensure target column is float
df_prepped['future_demand'] = df_prepped['future_demand'].astype(float)

# Handle missing values
df_prepped = df_prepped.fillna({
    'returns': 0,
    'holiday_indicator': 0,
    'impact_score': 0
})

# Identify categorical columns to encode
categorical_cols = ['product_name', 'category', 'season', 'event_type', 'region']

# One-hot encode categoricals
df_encoded = pd.get_dummies(df_prepped, columns=categorical_cols, drop_first=False)

# Convert boolean columns created by pd.get_dummies to 0/1 integers
bool_cols = df_encoded.select_dtypes(include=['bool']).columns
df_encoded[bool_cols] = df_encoded[bool_cols].astype(int)

# --- 4. Chronological Train/Test Split ---
# Training set: 2022 to 2024
# Test set: 2025 and onwards
train_mask = df_encoded['date'] < '2025-01'
test_mask = df_encoded['date'] >= '2025-01'

train_df = df_encoded[train_mask].drop(columns=['date'])
test_df = df_encoded[test_mask].drop(columns=['date'])

X_train = train_df.drop(columns=['future_demand'])
y_train = train_df['future_demand']
X_test = test_df.drop(columns=['future_demand'])
y_test = test_df['future_demand']

print(f"Training rows: {len(X_train)} | Testing rows: {len(X_test)}")

# --- 5. Train XGBoost Model ---
model = xgb.XGBRegressor(
    n_estimators=150,
    max_depth=6,
    learning_rate=0.08,
    random_state=42,
    objective='reg:squarederror'
)
model.fit(X_train, y_train)
print("XGBoost model training complete!")

# Save the columns structure for mapping input parameters locally
with open('model_features.pkl', 'wb') as f:
    pickle.dump(list(X_train.columns), f)
print("Saved feature structure to 'model_features.pkl'")

# --- 6. Evaluation ---
predictions = model.predict(X_test)
mae = mean_absolute_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print("\n=== Evaluation Results (Test Set - 2025) ===")
print(f"Mean Absolute Error (MAE): {mae:.2f} units")
print(f"R² Score: {r2:.4f}")

# --- 7. Plot Feature Importance ---
importance = model.feature_importances_
feature_names = X_train.columns
imp_df = pd.DataFrame({'feature': feature_names, 'importance': importance})
imp_df = imp_df.sort_values(by='importance', ascending=False).head(10)

plt.figure(figsize=(10, 6))
plt.barh(imp_df['feature'], imp_df['importance'], color='skyblue')
plt.gca().invert_yaxis()
plt.title('Top 10 Most Important Features')
plt.xlabel('Importance Score')
plt.tight_layout()
plt.savefig('feature_importance.png')
plt.show()
print("Saved feature importance chart to 'feature_importance.png'")

# --- 8. Save Trained Model ---
# Save as JSON (best compatibility for XGBoost loads)
model.save_model('xgb_demand_model.json')
print("Model saved to 'xgb_demand_model.json' successfully!")
```

---

## Step 4: Reorder Quantity Calculation Demo

Copy and paste this second block of code into another cell to test the exact reorder quantity formula on a few sample test predictions.

```python
# Select a few rows to test
test_samples = test_df.sample(5, random_state=42).copy()
test_samples['predicted_demand'] = model.predict(test_samples.drop(columns=['future_demand']))

reorder_results = []
for idx, row in test_samples.iterrows():
    pred_demand = row['predicted_demand']
    safety_stock = row['safety_stock']
    curr_stock = row['current_stock']
    reserved_stock = row['reserved_stock']
    lead_time = row['supplier_lead_time']
    reliability = row['supplier_reliability']
    avg_sales_30d = row['avg_sales_30d']
    max_cap = row['max_stock_capacity']
    
    # 1. Lead Time Buffer
    lt_buffer = (avg_sales_30d / 30.0) * lead_time
    
    # 2. Adjust for reliability
    if reliability < 0.8:
        lt_buffer *= (2.0 - reliability)
    else:
        lt_buffer *= 1.0
        
    # 3. Base Reorder Formula
    reorder_qty = pred_demand + safety_stock - (curr_stock - reserved_stock) + lt_buffer
    
    # 4. Cap and Clip constraints
    reorder_qty = max(0.0, reorder_qty) # Never negative
    if curr_stock + reorder_qty > max_cap:
        reorder_qty = max_cap - curr_stock
        reorder_qty = max(0.0, reorder_qty)
        flag = "CAPPED"
    else:
        flag = "NORMAL"
        
    reorder_results.append({
        'Predicted Demand': round(pred_demand, 1),
        'Current Stock': curr_stock,
        'Max Capacity': max_cap,
        'Calculated Order Qty': round(reorder_qty, 1),
        'Status': flag
    })

print("=== Reorder Quantity Calculations Sample ===")
print(pd.DataFrame(reorder_results).to_string())
```

---

## Step 5: Download the Artifacts

From the left file browser in Colab, download these three files to your project workspace:
1. `xgb_demand_model.json` (the trained model)
2. `model_features.pkl` (the list of features used to align input columns)
3. `feature_importance.png` (optional visualization)
