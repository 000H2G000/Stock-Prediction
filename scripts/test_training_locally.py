import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import os

def test_train():
    dataset_path = 'data/pharmacy_inventory_dataset_10000_rows.csv'
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Missing file: {dataset_path}")
        
    df = pd.read_csv(dataset_path)
    print(f"Loaded dataset: {df.shape}")
    
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
                
        score += np.random.uniform(-5, 5)
        return min(100.0, max(0.0, score))

    def calculate_news_signal_score(row):
        score = (float(row['impact_score']) / 10.0)
        score += np.random.uniform(-0.5, 0.5)
        return min(10.0, max(0.0, score))
        
    df['search_trend_score'] = df.apply(calculate_search_trend_score, axis=1)
    df['news_signal_score'] = df.apply(calculate_news_signal_score, axis=1)
    
    # Preprocessing
    id_cols = ['product_id', 'supplier_id']
    df_prepped = df.drop(columns=id_cols)
    df_prepped['future_demand'] = df_prepped['future_demand'].astype(float)
    df_prepped = df_prepped.fillna({'returns': 0, 'holiday_indicator': 0, 'impact_score': 0})
    
    categorical_cols = ['product_name', 'category', 'season', 'event_type', 'region']
    df_encoded = pd.get_dummies(df_prepped, columns=categorical_cols, drop_first=False)
    
    bool_cols = df_encoded.select_dtypes(include=['bool']).columns
    df_encoded[bool_cols] = df_encoded[bool_cols].astype(int)
    
    # Chronological Split
    train_mask = df_encoded['date'] < '2025-01'
    test_mask = df_encoded['date'] >= '2025-01'
    
    train_df = df_encoded[train_mask].drop(columns=['date'])
    test_df = df_encoded[test_mask].drop(columns=['date'])
    
    X_train = train_df.drop(columns=['future_demand'])
    y_train = train_df['future_demand']
    X_test = test_df.drop(columns=['future_demand'])
    y_test = test_df['future_demand']
    
    print(f"Train/Test sizes: {X_train.shape} / {X_test.shape}")
    
    model = xgb.XGBRegressor(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.08,
        random_state=42,
        objective='reg:squarederror'
    )
    model.fit(X_train, y_train)
    print("Model fitted successfully.")
    
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    print(f"MAE: {mae:.2f}")
    print(f"R2: {r2:.4f}")
    
    # Save test artifacts
    os.makedirs('data', exist_ok=True)
    model.save_model('data/xgb_demand_model.json')
    with open('data/model_features.pkl', 'wb') as f:
        pickle.dump(list(X_train.columns), f)
    print("Test outputs saved successfully to data/ directory.")

if __name__ == "__main__":
    test_train()
