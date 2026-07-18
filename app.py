import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Load environment variables from .env if present
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

# Ensure scripts directory is in path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from prediction_service import predict_and_reorder, load_prediction_model
from db_logger import init_db, log_decision, update_decision_status

# Load model
try:
    load_prediction_model()
except Exception as e:
    st.error(f"Error loading model: {e}. Please ensure xgb_demand_model.json and model_features.pkl are in the data/ directory.")

init_db()

# Set Page Config
st.set_page_config(
    page_title="Pharma Stock AI Command Center",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dashboard styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background-color: #0b1220;
        color: #c9d1d9;
    }
    
    .stApp {
        background: radial-gradient(circle at 78% -10%, #17365d 0%, #0b1220 42%, #080d17 100%);
    }
    
    h1, h2, h3 {
        color: #eaf4ff !important;
        font-weight: 700 !important;
    }
    
    .dashboard-card {
        background: linear-gradient(145deg, rgba(25, 39, 61, .92), rgba(15, 24, 39, .92));
        border: 1px solid rgba(125, 184, 255, .16);
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,.18);
    }
    
    .metric-value {
        font-size: 2.3rem;
        font-weight: 700;
        color: #7dc0ff;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #9eb0c8;
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
        background: linear-gradient(135deg, #17365d 0%, #101d30 100%);
        border: 1px solid rgba(125, 192, 255, .35);
        padding: 20px;
        border-radius: 12px;
        color: #e6edf3;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    .eyebrow { color: #74d4c0; font-size: .78rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
    .hero-title { font-size: 2.4rem; font-weight: 700; margin: .1rem 0 .3rem; color: #f4f9ff; }
    .hero-copy { color: #9eb0c8; font-size: 1rem; }
    [data-testid="stSidebar"] { background: #0d1727; border-right: 1px solid rgba(125,184,255,.12); }
    [data-testid="stSidebar"] h2 { color: #eaf4ff !important; }
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

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 LLM Recommendation")
st.sidebar.caption("Put your key in .env as GOOGLE_API_KEY to avoid pasting it each time.")
llm_api_key = st.sidebar.text_input(
    "Paste Google AI Studio API key",
    type="password",
    help="Leave blank to use the key from .env if present."
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Automation")
auto_buy_enabled = st.sidebar.checkbox("Enable auto-buy supplier workflow", value=True)
require_human_confirmation = st.sidebar.checkbox("Require human confirmation", value=True)

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
sim_result = predict_and_reorder(sim_scenario, llm_api_key=llm_api_key)

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
available_stock = max(current_stock - reserved_stock, 0)
reorder_count = int((results_df['Suggested Order'] > 0).sum())
stock_cover = available_stock / max(sim_result['predicted_demand'], 1)
order_color = "#ff8f8f" if sim_result['reorder_quantity'] > 0 else "#74d4c0"

st.markdown('<div class="eyebrow">Live inventory intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Pharma Stock Command Center</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-copy">{region} · {season} · {event_type.replace("_", " ")} &nbsp;|&nbsp; AI-driven automation with human approval for supplier replenishment.</div>', unsafe_allow_html=True)

kpi_cols = st.columns(5)
kpis = [
    ("Selected demand", f"{sim_result['predicted_demand']:.0f}", "Forecast units"),
    ("Available stock", f"{available_stock:,.0f}", f"{stock_cover:.1f}x demand cover"),
    ("Safety buffer", f"{safety_stock:,.0f}", f"{available_stock - safety_stock:+,.0f} vs target"),
    ("Reorder recommendation", f"{sim_result['reorder_quantity']:,.0f}", "Units to replenish"),
    ("Portfolio alerts", str(reorder_count), "Products needing attention"),
]
for col, (label, value, caption) in zip(kpi_cols, kpis):
    color = order_color if label == "Reorder recommendation" else "#7dc0ff"
    col.markdown(f'<div class="dashboard-card"><div class="metric-label">{label}</div><div class="metric-value" style="color:{color}">{value}</div><div style="color:#9eb0c8;font-size:.82rem">{caption}</div></div>', unsafe_allow_html=True)

left, right = st.columns([1.65, 1])
with left:
    st.subheader(f"Forecast outlook · {product_name}")
    daily_rate = max(avg_sales_30d / 30, sim_result['predicted_demand'] / 14)
    forecast_days = pd.date_range(pd.Timestamp.today().normalize(), periods=14, freq="D")
    pulse = np.linspace(.84, 1.15, 14) + np.sin(np.linspace(0, 2.6 * np.pi, 14)) * .08
    forecast_df = pd.DataFrame({"Projected daily demand": np.maximum(0, daily_rate * pulse)}, index=forecast_days)
    st.line_chart(forecast_df, height=280, use_container_width=True)
with right:
    st.subheader("Stock position")
    position_df = pd.DataFrame({"Units": [available_stock, safety_stock, sim_result['predicted_demand'], sim_result['reorder_quantity']]}, index=["Available", "Safety target", "Forecast", "Recommended order"])
    st.bar_chart(position_df, height=280, use_container_width=True)

insight_col, action_col = st.columns([1.65, 1])
with insight_col:
    source_label = "AI-generated explanation" if llm_api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") else "Rule-based explanation"
    st.markdown(f'<div class="explanation-box"><strong>Recommendation for {product_name}</strong><br/><div style="font-size:.82rem;color:#74d4c0;margin-bottom:.5rem">{source_label}</div>{sim_result["explanation"]}</div>', unsafe_allow_html=True)
with action_col:
    st.markdown('<div class="dashboard-card"><div class="metric-label">Inventory health</div>', unsafe_allow_html=True)
    st.progress(min(1.0, available_stock / max(safety_stock * 2, 1)))
    health = "Needs replenishment" if sim_result['reorder_quantity'] > 0 else "Stock buffer is healthy"
    st.markdown(f'<div style="font-size:1.2rem;font-weight:700;color:{order_color};margin-top:.55rem">{health}</div><div style="color:#9eb0c8;margin-top:.3rem">Supplier lead time: {supplier_lead_time} days · Reliability: {supplier_reliability:.0%}</div></div>', unsafe_allow_html=True)

    if sim_result['reorder_quantity'] > 0:
        supplier_action = f"Auto-create supplier replenishment for {product_name}: {sim_result['reorder_quantity']:.0f} units to {region}"
        st.markdown('<div class="dashboard-card" style="border: 1px solid #58a6ff; background: linear-gradient(135deg, rgba(24, 44, 69, 0.98), rgba(10, 24, 41, 0.98));">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label" style="color:#74d4c0">⚡ Automation decision</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:1.35rem;font-weight:700;color:#f4f9ff;margin-bottom:.35rem">{product_name} replenishment request</div>', unsafe_allow_html=True)
        st.write(supplier_action)
        st.markdown('<div style="margin: .4rem 0 .7rem; color:#74d4c0; font-weight:600">AI recommendation ready · human approval required</div>', unsafe_allow_html=True)
        if auto_buy_enabled and require_human_confirmation:
            confirm_col, reject_col = st.columns(2)
            with confirm_col:
                if st.button("✅ Approve & send to supplier", key="confirm_supplier_order", use_container_width=True):
                    decision_id = log_decision(
                        product=product_name,
                        region=region,
                        predicted_demand=sim_result['predicted_demand'],
                        safety_stock=safety_stock,
                        current_stock=current_stock,
                        reserved_stock=reserved_stock,
                        avg_sales_30d=avg_sales_30d,
                        lead_time=supplier_lead_time,
                        reliability=supplier_reliability,
                        max_capacity=max_capacity,
                        reorder_quantity=sim_result['reorder_quantity'],
                        status="Approved",
                        explanation=sim_result['explanation'],
                        supplier_action=supplier_action,
                        approved_by="Human"
                    )
                    st.success(f"✅ Supplier order approved and queued. Decision ID: {decision_id}")
            with reject_col:
                if st.button("❌ Reject order", key="reject_supplier_order", use_container_width=True):
                    decision_id = log_decision(
                        product=product_name,
                        region=region,
                        predicted_demand=sim_result['predicted_demand'],
                        safety_stock=safety_stock,
                        current_stock=current_stock,
                        reserved_stock=reserved_stock,
                        avg_sales_30d=avg_sales_30d,
                        lead_time=supplier_lead_time,
                        reliability=supplier_reliability,
                        max_capacity=max_capacity,
                        reorder_quantity=sim_result['reorder_quantity'],
                        status="Rejected",
                        explanation=sim_result['explanation'],
                        supplier_action=supplier_action,
                        approved_by="Human"
                    )
                    st.warning(f"Order rejected. Decision ID: {decision_id}")
        elif auto_buy_enabled:
            st.info("⚙️ Automation is enabled; this order will be submitted without manual confirmation.")
        else:
            st.info("⚪ Auto-buy is disabled. The recommendation remains visible but no supplier action is triggered.")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('### Portfolio analytics')
chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.caption("Inventory, safety buffer, and forecast by product")
    st.bar_chart(results_df.set_index('Product')[["Current Stock", "Safety Stock", "Forecast Demand"]], height=310, use_container_width=True)
with chart_col2:
    st.caption("Demand velocity across the product portfolio")
    velocity_df = pd.DataFrame({
        "7-day daily rate": [avg_sales_7d / 7 if p == product_name else PRODUCT_PROFILES[p]['sales_7d'] / 7 for p in results_df['Product']],
        "30-day daily rate": [avg_sales_30d / 30 if p == product_name else PRODUCT_PROFILES[p]['sales_30d'] / 30 for p in results_df['Product']],
    }, index=results_df['Product'])
    st.bar_chart(velocity_df, height=310, use_container_width=True)

bottom_left, bottom_right = st.columns(2)
with bottom_left:
    st.subheader("Capacity utilization")
    capacity_df = pd.DataFrame({"Current stock": results_df['Current Stock'].tolist(), "Available capacity": [max((max_capacity if p == product_name else PRODUCT_PROFILES[p]['capacity']) - stock, 0) for p, stock in zip(results_df['Product'], results_df['Current Stock'])]}, index=results_df['Product'])
    st.area_chart(capacity_df, height=240, use_container_width=True)
with bottom_right:
    st.subheader("Demand by category")
    st.bar_chart(results_df.groupby('Category')['Forecast Demand'].sum().to_frame(), height=240, use_container_width=True)

st.markdown('### Product inventory health')
st.dataframe(results_df.drop(columns=['Manager Action Plan']), column_config={"Forecast Demand": st.column_config.NumberColumn("Forecast demand", format="%d units"), "Suggested Order": st.column_config.NumberColumn("Suggested order", format="%d units")}, use_container_width=True, hide_index=True)

# The legacy log/actions layout below is intentionally bypassed; this page is dashboard-only.
st.stop()
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
