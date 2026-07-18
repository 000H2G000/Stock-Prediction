import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# Ensure scripts directory is in path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from prediction_service import predict_and_reorder, load_prediction_model
from db_logger import update_decision_status, init_db

# Initialize DB on start
init_db()

# Load model
try:
    load_prediction_model()
except Exception as e:
    st.error(f"Error loading model: {e}. Please ensure xgb_demand_model.json and model_features.pkl are in the data/ directory.")

# Set Page Config
st.set_page_config(
    page_title="Pharma Stock AI Command Center",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    .stApp {
        background-color: #0d1117;
    }
    
    h1, h2, h3 {
        color: #58a6ff !important;
        font-weight: 700 !important;
    }
    
    .dashboard-card {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
    }
    
    .metric-value {
        font-size: 2.3rem;
        font-weight: 700;
        color: #58a6ff;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
        padding: 10px;
        transition: all 0.3s ease;
        border: 1px solid #30363d;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(88,166,255,0.2);
        border-color: #58a6ff;
    }
    
    .explanation-box {
        background: linear-gradient(135deg, #1f242c 0%, #161b22 100%);
        border: 1px dashed #58a6ff;
        padding: 20px;
        border-radius: 12px;
        color: #e6edf3;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# Product Mappings & Default Profiles
PRODUCT_MAP = {
    'Paracetamol': 'Painkiller',
    'Diclofenac': 'Painkiller',
    'Cough Syrup': 'Respiratory',
    'Amoxicillin': 'Antibiotic',
    'Azithromycin': 'Antibiotic',
    'Metformin': 'Diabetes',
    'Insulin': 'Diabetes',
    'Aspirin': 'Cardiology'
}

# Base profiles to populate product lists realistically
PRODUCT_PROFILES = {
    'Paracetamol': {'stock': 1200, 'capacity': 5000, 'safety': 400, 'sales_30d': 320, 'sales_7d': 80, 'sales_90d': 900},
    'Diclofenac': {'stock': 850, 'capacity': 4000, 'safety': 300, 'sales_30d': 250, 'sales_7d': 60, 'sales_90d': 700},
    'Cough Syrup': {'stock': 250, 'capacity': 3000, 'safety': 500, 'sales_30d': 180, 'sales_7d': 45, 'sales_90d': 500},
    'Amoxicillin': {'stock': 2100, 'capacity': 6000, 'safety': 450, 'sales_30d': 290, 'sales_7d': 75, 'sales_90d': 850},
    'Azithromycin': {'stock': 900, 'capacity': 4500, 'safety': 350, 'sales_30d': 210, 'sales_7d': 50, 'sales_90d': 600},
    'Metformin': {'stock': 3200, 'capacity': 8000, 'safety': 600, 'sales_30d': 450, 'sales_7d': 110, 'sales_90d': 1300},
    'Insulin': {'stock': 180, 'capacity': 2000, 'safety': 300, 'sales_30d': 120, 'sales_7d': 30, 'sales_90d': 360},
    'Aspirin': {'stock': 2500, 'capacity': 7000, 'safety': 500, 'sales_30d': 380, 'sales_7d': 90, 'sales_90d': 1100}
}

# --- SIDEBAR - SCENARIO CONTROL PANEL ---
st.sidebar.title("🛠️ Scenario Simulator")
st.sidebar.write("Simulate market events and current stock levels:")

# Product Selection
product_name = st.sidebar.selectbox("Select Product", list(PRODUCT_MAP.keys()), index=4)
category = PRODUCT_MAP[product_name]
st.sidebar.info(f"Category: **{category}**")

region = st.sidebar.selectbox("Region", ['Tunis', 'Sfax', 'Sousse', 'Gabes', 'Beja', 'Nabeul'], index=0)
season = st.sidebar.selectbox("Season", ['Winter', 'Spring', 'Summer', 'Autumn'], index=0)
event_type = st.sidebar.selectbox("Active Event Type", ['None', 'Flu_Outbreak', 'Cold_Wave', 'Allergy_Season', 'Heat_Wave', 'Ramadan'], index=1)

col_left, col_right = st.sidebar.columns(2)
with col_left:
    month = st.number_input("Month", min_value=1, max_value=12, value=12)
    quarter = st.number_input("Quarter", min_value=1, max_value=4, value=4)
with col_right:
    holiday_indicator = st.selectbox("Holiday?", [0, 1], index=0)
    impact_score = st.slider("Event Impact Score", 0, 100, 80 if event_type != 'None' else 0)

st.sidebar.markdown("---")
st.sidebar.subheader("📈 Internal Stock State")
current_stock = st.sidebar.slider("Current Stock", 0, 10000, 1200)
max_capacity = st.sidebar.slider("Max Capacity", 1000, 15000, 5000)
safety_stock = st.sidebar.slider("Safety Stock", 100, 3000, 400)
reserved_stock = st.sidebar.slider("Reserved Stock", 0, 1000, 50)

st.sidebar.markdown("---")
st.sidebar.subheader("🤝 Supplier Conditions")
supplier_lead_time = st.sidebar.slider("Lead Time (Days)", 1, 30, 5)
supplier_reliability = st.sidebar.slider("Supplier Reliability", 0.0, 1.0, 0.75, step=0.05)

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Search & News Signals")
search_trend_score = st.sidebar.slider("Google Trends Score", 0.0, 100.0, 85.0)
news_signal_score = st.sidebar.slider("News Signal Score", 0.0, 10.0, 8.2)

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Sales History")
avg_sales_30d = st.sidebar.slider("Avg Sales 30d", 0, 2000, 320)
avg_sales_7d = st.sidebar.slider("Avg Sales 7d", 0, 500, 80)
avg_sales_90d = st.sidebar.slider("Avg Sales 90d", 0, 6000, 900)

# Build Simulator Input Scenario (driven directly by sidebar)
sim_scenario = {
    'product_name': product_name,
    'category': category,
    'region': region,
    'season': season,
    'event_type': event_type,
    'current_stock': current_stock,
    'max_stock_capacity': max_capacity,
    'safety_stock': safety_stock,
    'reserved_stock': reserved_stock,
    'avg_sales_7d': avg_sales_7d,
    'avg_sales_30d': avg_sales_30d,
    'avg_sales_90d': avg_sales_90d,
    'quantity_sold': avg_sales_30d,
    'number_of_orders': avg_sales_30d // 8,
    'revenue': avg_sales_30d * 12,
    'returns': 2,
    'supplier_lead_time': supplier_lead_time,
    'supplier_reliability': supplier_reliability,
    'month': month,
    'quarter': quarter,
    'holiday_indicator': holiday_indicator,
    'impact_score': impact_score,
    'search_trend_score': search_trend_score,
    'news_signal_score': news_signal_score
}

# Run Prediction for Active Sidebar Scenario
sim_result = predict_and_reorder(sim_scenario)

# Store in session state
st.session_state['sim_decision_id'] = sim_result['decision_id']
st.session_state['sim_result'] = sim_result

# Process Batch Calculations for Product Status Grid & Visual Charts
all_results = []
for prod, profile in PRODUCT_PROFILES.items():
    if prod == product_name:
        prod_stock = current_stock
        prod_safety = safety_stock
        prod_sales30 = avg_sales_30d
        prod_sales7 = avg_sales_7d
        prod_sales90 = avg_sales_90d
        prod_capacity = max_capacity
    else:
        prod_stock = profile['stock']
        prod_safety = profile['safety']
        prod_sales30 = profile['sales_30d']
        prod_sales7 = profile['sales_7d']
        prod_sales90 = profile['sales_90d']
        prod_capacity = profile['capacity']

    scen = {
        'product_name': prod,
        'category': PRODUCT_MAP[prod],
        'region': region,
        'season': season,
        'event_type': event_type,
        'current_stock': prod_stock,
        'max_stock_capacity': prod_capacity,
        'safety_stock': prod_safety,
        'reserved_stock': reserved_stock,
        'avg_sales_7d': prod_sales7,
        'avg_sales_30d': prod_sales30,
        'avg_sales_90d': prod_sales90,
        'quantity_sold': prod_sales30,
        'number_of_orders': prod_sales30 // 8,
        'revenue': prod_sales30 * 12,
        'returns': 2,
        'supplier_lead_time': supplier_lead_time,
        'supplier_reliability': supplier_reliability,
        'month': month,
        'quarter': quarter,
        'holiday_indicator': holiday_indicator,
        'impact_score': impact_score,
        'search_trend_score': search_trend_score,
        'news_signal_score': news_signal_score
    }
    
    if prod == product_name:
        res = sim_result
    else:
        res = predict_and_reorder(scen)
        
    avail_stock = prod_stock - reserved_stock
    if res['reorder_quantity'] > 0 and avail_stock < prod_safety:
        status_lbl = "🚨 URGENT REORDER"
        action = "Stock below safety limit! Place emergency order immediately."
    elif res['reorder_quantity'] > 0:
        status_lbl = "⚠️ REORDER SUGGESTED"
        action = "Demand spike predicted. Replenish stock to cover lead times."
    elif res['predicted_demand'] < 15:
        status_lbl = "💤 LOW DEMAND"
        action = "Very low sales expected. Hold stock, do not buy."
    else:
        status_lbl = "✅ STOCK HEALTHY"
        action = "Available inventory sufficient to cover upcoming demand."

    all_results.append({
        'Product': prod,
        'Category': PRODUCT_MAP[prod],
        'Current Stock': prod_stock,
        'Safety Stock': prod_safety,
        'Forecast Demand': round(res['predicted_demand'], 0),
        'Suggested Order': round(res['reorder_quantity'], 0),
        'Inventory Status': status_lbl,
        'Manager Action Plan': action
    })

results_df = pd.DataFrame(all_results)

# --- MAIN DASHBOARD INTERFACE (SINGLE PAGE) ---
st.title("🏥 Pharma Stock AI Command Center")
st.write("Real-time automated inventory auditing, explainable recommendations, and demand forecasting.")

# Section 1: Product Health Auditing Grid
st.markdown("---")
st.subheader("📋 Product Inventory Health Audit")
st.write("Reviews stock levels against AI demand predictions and advises next steps:")
st.dataframe(
    results_df,
    column_config={
        "Forecast Demand": st.column_config.NumberColumn("Forecast Demand (Units)", format="%d"),
        "Suggested Order": st.column_config.NumberColumn("Suggested Order (Units)", format="%d"),
        "Current Stock": st.column_config.NumberColumn(format="%d"),
        "Safety Stock": st.column_config.NumberColumn(format="%d"),
    },
    use_container_width=True,
    hide_index=True
)

# Section 2: Simulator Forecast & AI Explanations
st.markdown("---")
st.subheader(f"🔬 Forecast & AI Explanation for {product_name}")
st.info(f"Simulating: **{product_name}** ({category}) in **{region}** during **{season}** ({event_type})")

# Metric Cards
sm_col1, sm_col2, sm_col3, sm_col4 = st.columns(4)
with sm_col1:
    st.markdown(f"""
        <div class="dashboard-card" style="text-align:center;">
            <div class="metric-label">Predicted Demand</div>
            <div class="metric-value">{sim_result['predicted_demand']:.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with sm_col2:
    st.markdown(f"""
        <div class="dashboard-card" style="text-align:center;">
            <div class="metric-label">Available Stock</div>
            <div class="metric-value">{current_stock - reserved_stock:.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with sm_col3:
    st.markdown(f"""
        <div class="dashboard-card" style="text-align:center;">
            <div class="metric-label">Safety Target</div>
            <div class="metric-value">{safety_stock:.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with sm_col4:
    col_c = "#ff7b72" if sim_result['reorder_quantity'] > 0 else "#56d364"
    st.markdown(f"""
        <div class="dashboard-card" style="text-align:center;">
            <div class="metric-label" style="color:{col_c}">Recommended Order</div>
            <div class="metric-value" style="color:{col_c}">{sim_result['reorder_quantity']:.0f}</div>
        </div>
    """, unsafe_allow_html=True)

# AI Agent Explanation Box
st.markdown(f"""
    <div class="explanation-box" style="margin-bottom: 20px;">
        <strong>AI Agent Explanation:</strong><br/>
        {sim_result['explanation']}
    </div>
""", unsafe_allow_html=True)

# Human Approval Actions
if sim_result['reorder_quantity'] > 0:
    act_c1, act_c2, _ = st.columns([1, 1, 2])
    with act_c1:
        if st.button("✅ Approve Reorder", key="sim_approve"):
            update_decision_status(st.session_state['sim_decision_id'], "Approved")
            st.success("🎉 Order successfully approved and transmitted to supplier!")
    with act_c2:
        if st.button("❌ Reject Reorder", key="sim_reject"):
            update_decision_status(st.session_state['sim_decision_id'], "Rejected")
            st.warning("⚠️ Order rejected. Log database updated.")
else:
    st.info("ℹ️ Current stock buffer is healthy. No reordering necessary.")

# Section 3: Visual Analytics Charts & Graphs
st.markdown("---")
st.subheader("📊 Stock vs. Forecast Demand Analysis")

# 1. Bar Chart comparing Stock vs Demand vs Safety
chart_df = results_df.set_index('Product')[['Current Stock', 'Safety Stock', 'Forecast Demand']]
st.bar_chart(chart_df, height=350, use_container_width=True)

# 2. Side-by-Side Area Breakdown
chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.write("**📦 Inventory vs Capacity Distribution**")
    cap_df = pd.DataFrame({
        'Current Stock': results_df['Current Stock'].tolist(),
        'Max Capacity Limit': [PRODUCT_PROFILES[p]['capacity'] if p != product_name else max_capacity for p in PRODUCT_PROFILES.keys()]
    }, index=results_df['Product'].tolist())
    st.area_chart(cap_df, height=220)
    
with chart_col2:
    st.write("**🏷️ Forecasted Demand by Category**")
    cat_demand = results_df.groupby('Category')['Forecast Demand'].sum().reset_index()
    st.bar_chart(cat_demand.set_index('Category'), height=220)
