import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
import os
import requests
import json
from pathlib import Path

GOOGLE_AI_STUDIO_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
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
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load model and feature names
model = None
feature_names = None


def resolve_llm_api_key(env_path=None):
    candidate_paths = []
    if env_path:
        candidate_paths.append(env_path)
    candidate_paths.extend([
        os.path.join(os.getcwd(), ".env"),
        str(PROJECT_ROOT / ".env"),
        str(Path(__file__).resolve().parent / ".env"),
    ])

    for env_file in candidate_paths:
        if not env_file or not os.path.exists(env_file):
            continue
        with open(env_file, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key in {"GOOGLE_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY"}:
                    return value

    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")


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

def explain_decision_with_llm(scenario_data, predicted_demand, reorder_qty, status, llm_api_key=None):
    api_key = llm_api_key or resolve_llm_api_key()
    product_name = scenario_data['product_name']
    category = scenario_data['category']
    region = scenario_data['region']
    season = scenario_data['season']
    event_type = scenario_data['event_type']
    current_stock = float(scenario_data['current_stock'])
    safety_stock = float(scenario_data['safety_stock'])
    reserved_stock = float(scenario_data['reserved_stock'])
    available_stock = max(current_stock - reserved_stock, 0.0)
    lead_time = int(scenario_data['supplier_lead_time'])
    event_text = event_type.replace('_', ' ') if event_type != 'None' else 'routine demand'
    stock_gap = safety_stock - available_stock
    if stock_gap > 0:
        stock_pressure = f"stock is {stock_gap:.0f} units below the safety target"
    else:
        stock_pressure = "stock is above the safety target"

    if event_type != 'None':
        event_pressure = f"the {event_text} and {season.lower()} conditions"
    else:
        event_pressure = f"the {season.lower()} demand pattern"

    prompt = f"""
    You are writing a short recommendation note for a pharmacy manager.
    Create a fresh, specific explanation for this exact scenario. Do not reuse a generic template.

    Scenario details:
    - Product: {product_name}
    - Category: {category}
    - Region: {region}
    - Season: {season}
    - Event: {event_type} (impact score: {scenario_data['impact_score']})
    - Current stock: {current_stock}
    - Reserved stock: {reserved_stock}
    - Available stock after reservations: {available_stock}
    - Safety stock target: {safety_stock}
    - Stock situation: {stock_pressure}
    - Average sales over 30 days: {scenario_data['avg_sales_30d']}
    - Predicted future demand: {predicted_demand:.1f}
    - Recommended reorder quantity: {reorder_qty:.1f}
    - Supplier lead time: {lead_time} days
    - Status: {status}

    Instructions:
    1. Write 2-4 sentences.
    2. Mention the exact product name, region, and at least one concrete factor such as the stock gap, event, season, or supplier lead time.
    3. Make the explanation sound natural and practical, not like a template.
    4. Use a different opening and different wording than a generic stock message.
    5. Explicitly connect the recommendation to this specific pressure: {event_pressure}.
    6. Keep the tone simple and suitable for a pharmacy manager.
    """
    
    if api_key:
        try:
            if "GROQ_API_KEY" in (os.environ.get("GROQ_API_KEY"),) and llm_api_key is None:
                headers = {
                    "Authorization": f"Bearer {api_key}",
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
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=15)
                if res.status_code == 200:
                    return res.json()['choices'][0]['message']['content'].strip()
            else:
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.95, "maxOutputTokens": 220}
                }
                res = requests.post(f"{GOOGLE_AI_STUDIO_BASE_URL}/gemini-2.0-flash:generateContent?key={api_key}", json=payload, timeout=20)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        except Exception as e:
            print("LLM API error, falling back to rule-based explanation:", e)
            
    # Rule-based fallback explanation
    if status == "No Action Needed" or reorder_qty <= 0:
        return f"{product_name} in {region} looks well covered right now, with {available_stock:.0f} units available against a safety goal of {safety_stock:.0f}. The forecast is calm enough that no replenishment is needed at this moment."
    
    explanation = f"{product_name} in {region} needs attention because the forecasted demand of {predicted_demand:.1f} units is outpacing the available stock of {available_stock:.0f} units. "
    if event_type != 'None':
        explanation += f"The {season.lower()} season and the {event_text} are increasing pressure on this item, so the order should cover that risk. "
    else:
        explanation += f"The current demand pattern is strong enough that replenishment should be planned now. "
    
    explanation += f"With a {lead_time}-day supplier lead time and a safety target of {safety_stock:.0f}, ordering {reorder_qty:.1f} units now helps maintain service levels."
    return explanation

def predict_and_reorder(scenario_data, record_decision=False, llm_api_key=None):
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
        
    explanation = explain_decision_with_llm(scenario_data, predicted_demand, reorder_qty, status, llm_api_key=llm_api_key)
    
    decision_id = None
    if record_decision:
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
