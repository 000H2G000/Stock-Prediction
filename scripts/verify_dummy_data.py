import pandas as pd
import numpy as np

def verify():
    df = pd.read_csv("data/internal_stock_data.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    print("=== Dataset Overview ===")
    print(df.head())
    print(f"\nTotal Rows: {len(df)}")
    
    # 1. Check date range and weekly granularity
    min_date = df['date'].min()
    max_date = df['date'].max()
    unique_dates = df['date'].nunique()
    print(f"Date range: {min_date.date()} to {max_date.date()} ({unique_dates} unique weeks)")
    assert unique_dates >= 52 * 1.9, "Dataset should cover at least 1-2 years of weekly data"
    
    # 2. Check region multipliers
    print("\n=== Avg Sales by Region ===")
    region_sales = df.groupby('region')['units_sold'].mean()
    print(region_sales)
    assert region_sales['Tunis'] > region_sales['Sfax'] > region_sales['Sousse'], "Region baseline demand must follow expected ordering"
    
    # 3. Check Winter vs Summer for Cold & Flu Remedy
    print("\n=== Seasonality for Cold & Flu Remedy ===")
    cold_flu = df[df['product'] == 'Cold & Flu Remedy'].copy()
    cold_flu['month'] = cold_flu['date'].dt.month
    winter_sales = cold_flu[cold_flu['month'].isin([11, 12, 1, 2])]['units_sold'].mean()
    summer_sales = cold_flu[cold_flu['month'].isin([6, 7, 8])]['units_sold'].mean()
    print(f"Average Winter Sales: {winter_sales:.2f}")
    print(f"Average Summer Sales: {summer_sales:.2f}")
    assert winter_sales > 2 * summer_sales, "Winter sales of Cold & Flu should be substantially higher than summer sales"
    
    # 4. Check that data is not perfectly smooth (standard deviation is non-zero)
    print("\n=== Standard Deviation of Sales ===")
    std_devs = df.groupby(['product', 'region'])['units_sold'].std()
    print(std_devs.head())
    assert (std_devs > 0).all(), "Data should not be perfectly smooth"
    
    print("\nAll validation checks PASSED successfully! [OK]")

if __name__ == "__main__":
    verify()
