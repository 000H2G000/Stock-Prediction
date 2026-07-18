import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_ramadan_dates(year):
    # Approximations of Ramadan start and end dates
    if year == 2024:
        return datetime(2024, 3, 11), datetime(2024, 4, 9)
    elif year == 2025:
        return datetime(2025, 3, 1), datetime(2025, 3, 30)
    elif year == 2026:
        return datetime(2026, 2, 18), datetime(2026, 3, 19)
    else:
        # Generic fallback
        return datetime(year, 3, 1), datetime(year, 3, 30)

def generate_data():
    np.random.seed(42)
    
    start_date = datetime(2024, 7, 1)
    end_date = datetime(2026, 6, 30)
    
    # Generate weekly dates
    dates = []
    curr = start_date
    while curr <= end_date:
        dates.append(curr)
        curr += timedelta(weeks=1)
        
    products = {
        "Painkiller": {"base": 500, "flu_boost": 1.1, "heatwave_boost": 1.0, "ramadan_boost": 0.9, "noise": 30},
        "Cold & Flu Remedy": {"base": 200, "flu_boost": 2.8, "heatwave_boost": 0.4, "ramadan_boost": 1.0, "noise": 25},
        "Allergy Medicine": {"base": 150, "flu_boost": 0.8, "heatwave_boost": 2.2, "ramadan_boost": 1.0, "noise": 15},
        "Insulin": {"base": 300, "flu_boost": 1.0, "heatwave_boost": 1.2, "ramadan_boost": 0.85, "noise": 10},
        "Antibiotic": {"base": 250, "flu_boost": 1.3, "heatwave_boost": 0.9, "ramadan_boost": 0.95, "noise": 20}
    }
    
    regions = {
        "Tunis": 1.5,
        "Sfax": 1.0,
        "Sousse": 0.8
    }
    
    rows = []
    
    for date in dates:
        year = date.year
        month = date.month
        
        # Determine seasons
        is_winter = month in [11, 12, 1, 2]
        is_summer = month in [6, 7, 8]
        
        # Check Ramadan
        ram_start, ram_end = get_ramadan_dates(year)
        is_ramadan = ram_start <= date <= ram_end
        
        for prod_name, params in products.items():
            base = params["base"]
            
            # Apply multipliers
            mult = 1.0
            if is_winter:
                mult *= params["flu_boost"]
            if is_summer:
                mult *= params["heatwave_boost"]
            if is_ramadan:
                mult *= params["ramadan_boost"]
                
            for reg_name, reg_mult in regions.items():
                # Expected units sold
                expected = base * mult * reg_mult
                
                # Add noise
                noise = np.random.normal(0, params["noise"] * reg_mult)
                units_sold = max(0, int(round(expected + noise)))
                
                rows.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "product": prod_name,
                    "region": reg_name,
                    "units_sold": units_sold
                })
                
    df = pd.DataFrame(rows)
    
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/internal_stock_data.csv", index=False)
    print(f"Generated {len(df)} rows and saved to data/internal_stock_data.csv")

if __name__ == "__main__":
    generate_data()
