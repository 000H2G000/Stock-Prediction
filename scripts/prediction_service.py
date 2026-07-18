import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
import os
import requests
import json
try:
    from scripts.db_logger import log_decision, update_decision_status
except ModuleNotFoundError:
    try:
        from db_logger import log_decision, update_decision_status
    except ModuleNotFoundError:
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from db_logger import log_decision, update_decision_status

MODEL_PATH = os.path.join("data", "xgb_demand_model.json")
FEATURES_PATH = os.path.join("data", "model_features.pkl")

# Load model and feature names
model = None
feature_names = None

def load_prediction_model():
    global model, feature_names
    if not os.path.exists(MODEL_PATH) or not os.path.exists(FEATURES_PATH):
        raise FileNotFoundError("Model or features file missing from data/ folder.")
    
    # Load feature alignment
    with open(FEATURES_PATH, 'rb') as f:
        feature_names = pickle.load(f)
        
    # Load XGBoost Regressor
    model = xgb.XGBRegressor()
    model.load_model(MODEL_PATH)
    print("XGBoost model loaded successfully.")

def explain_decision_with_llm(scenario_data, predicted_demand, reorder_qty, status):
    groq_api_key = os.environ.get("GROQ_API_KEY")
    
    prompt = f"""
    Product: {scenario_data['product_name']}
    Category: {scenario_data['category']}
    Region: {scenario_data['region']}
    Season: {scenario_data['season']}
    Event: {scenario_data['event_type']} (Impact Score: {scenario_data['impact_score']})
    Current Stock: {scenario_data['current_stock']}
    Max Capacity: {scenario_data['max_stock_capacity']}
    Safety Stock: {scenario_data['safety_stock']}
    Average Sales (30 days): {scenario_data['avg_sales_30d']}
    Predicted Future Demand: {predicted_demand:.1f}
    Recommended Reorder Quantity: {reorder_qty:.1f}
    Reorder Status: {status}
    
    Based on the above details, provide a clear, professional, and friendly 2-4 sentence explanation for a pharmacy manager on why this order recommendation was made. Keep it simple, avoid technical data science terms, and focus on the real-world factors.
    """
    
    if groq_api_key:
        try:
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are a pharma stock advisor. Explain demand prediction decisions in plain, simple language for pharmacy managers."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 150
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=5)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            print("Groq API error, falling back to rule-based explanation:", e)
            
    # Rule-based fallback explanation
    if status == "No Action Needed" or reorder_qty <= 0:
        return f"We do not recommend a reorder for {scenario_data['product_name']} in {scenario_data['region']}. The current stock level of {scenario_data['current_stock']} is sufficient to cover the predicted demand of {predicted_demand:.1f} units during this period."
    
    explanation = f"We recommend ordering {reorder_qty:.1f} units of {scenario_data['product_name']} for {scenario_data['region']}. "
    if scenario_data['event_type'] != 'None':
        explanation += f"This is driven by the upcoming {scenario_data['event_type'].replace('_', ' ')} (impact score: {scenario_data['impact_score']}) and seasonal {scenario_data['season']} trends. "
    else:
        explanation += f"This order accounts for a predicted future demand of {predicted_demand:.1f} units. "
        
    explanation += f"Ordering now ensures safety stock is maintained and avoids stockout risk, given the supplier's {scenario_data['supplier_lead_time']}-day lead time."
    return explanation

def predict_and_reorder(scenario_data):
    if model is None:
        load_prediction_model()
        
    # Create aligned input row
    input_row = {col: 0.0 for col in feature_names}
    
    # Populate numeric inputs
    numeric_keys = [
        'current_stock', 'max_stock_capacity', 'safety_stock', 'reserved_stock',
        'avg_sales_7d', 'avg_sales_30d', 'avg_sales_90d', 'quantity_sold',
        'number_of_orders', 'revenue', 'returns', 'supplier_lead_time',
        'supplier_reliability', 'month', 'quarter', 'holiday_indicator',
        'impact_score', 'search_trend_score', 'news_signal_score'
    ]
    for key in numeric_keys:
        if key in scenario_data:
            input_row[key] = float(scenario_data[key])
            
    # Populate one-hot categoricals
    cats = {
        'product_name': scenario_data.get('product_name'),
        'category': scenario_data.get('category'),
        'season': scenario_data.get('season'),
        'event_type': scenario_data.get('event_type'),
        'region': scenario_data.get('region')
    }
    for cat_name, cat_val in cats.items():
        col_name = f"{cat_name}_{cat_val}"
        if col_name in input_row:
            input_row[col_name] = 1.0
            
    # Convert to DataFrame
    input_df = pd.DataFrame([input_row])
    
    # Predict
    predicted_demand = float(model.predict(input_df)[0])
    
    # Calculate Lead Time Buffer
    avg_sales_30d = float(scenario_data.get('avg_sales_30d', 0.0))
    lead_time = float(scenario_data.get('supplier_lead_time', 0.0))
    reliability = float(scenario_data.get('supplier_reliability', 1.0))
    
    lt_buffer = (avg_sales_30d / 30.0) * lead_time
    if reliability < 0.8:
        lt_buffer *= (2.0 - reliability)
        
    # Reorder quantity formula
    curr_stock = float(scenario_data['current_stock'])
    res_stock = float(scenario_data['reserved_stock'])
    safety_stock = float(scenario_data['safety_stock'])
    max_cap = float(scenario_data['max_stock_capacity'])
    
    reorder_qty = predicted_demand + safety_stock - (curr_stock - res_stock) + lt_buffer
    reorder_qty = max(0.0, reorder_qty)
    
    status = "Pending"
    if reorder_qty <= 0:
        status = "No Action Needed"
    elif curr_stock + reorder_qty > max_cap:
        reorder_qty = max(0.0, max_cap - curr_stock)
        status = "Pending"
        
    explanation = explain_decision_with_llm(scenario_data, predicted_demand, reorder_qty, status)
    
    # Log to SQLite
    decision_id = log_decision(
        product=scenario_data['product_name'],
        region=scenario_data['region'],
        predicted_demand=predicted_demand,
        safety_stock=safety_stock,
        current_stock=curr_stock,
        reserved_stock=res_stock,
        avg_sales_30d=avg_sales_30d,
        lead_time=lead_time,
        reliability=reliability,
        max_capacity=max_cap,
        reorder_quantity=reorder_qty,
        status=status,
        explanation=explanation
    )
    
    return {
        "decision_id": decision_id,
        "predicted_demand": round(predicted_demand, 1),
        "reorder_quantity": round(reorder_qty, 1),
        "status": status,
        "explanation": explanation
    }

if __name__ == "__main__":
    # Quick self-test with a mock scenario
    load_prediction_model()
    test_scenario = {
        'product_name': 'Paracetamol',
        'category': 'Painkiller',
        'region': 'Tunis',
        'season': 'Winter',
        'event_type': 'Flu_Outbreak',
        'current_stock': 1200,
        'max_stock_capacity': 5000,
        'safety_stock': 400,
        'reserved_stock': 50,
        'avg_sales_7d': 80,
        'avg_sales_30d': 320,
        'avg_sales_90d': 900,
        'quantity_sold': 300,
        'number_of_orders': 40,
        'revenue': 12000,
        'returns': 2,
        'supplier_lead_time': 5,
        'supplier_reliability': 0.75,
        'month': 12,
        'quarter': 4,
        'holiday_indicator': 0,
        'impact_score': 80,
        'search_trend_score': 85.0,
        'news_signal_score': 8.2
    }
    
    result = predict_and_reorder(test_scenario)
    print("\nSelf-Test Prediction Result:")
    print(json.dumps(result, indent=2))
