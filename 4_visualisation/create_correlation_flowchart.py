# 4_visualisation/create_correlation_flowchart.py
# PURPOSE: To load the cleaned price data and brownfield analysis,
# correlate them by year, and generate a dual-axis chart to visualize
# the relationship between development activity and market spending.

import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

print("\n--- CORRELATION & VISUALIZATION SCRIPT ---")

# --- Configuration ---
INPUT_PRICE_DATA_PATH = os.path.join('reports', 'Cambridgeshire_Price_Data_2010-2023.csv')
INPUT_DEV_REPORT_PATH = os.path.join('reports', 'Cambridgeshire_Market_Analysis_FINAL.xlsx')
OUTPUT_DIR = 'reports'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Load Both Cleaned Datasets ---
print("Step 1: Loading cleaned price data and development analysis report...")
try:
    price_df = pd.read_csv(INPUT_PRICE_DATA_PATH, parse_dates=['DateOfTransfer'])
    # Load the specific sheet needed for the development data
    dev_df = pd.read_excel(INPUT_DEV_REPORT_PATH, sheet_name='Development Growth by Year')
    print(" -> Data loaded successfully.")
except FileNotFoundError:
    print(" -> ERROR: A required data file was not found. Please run previous scripts first.")
    exit()
except ValueError as e:
    print(f" -> ERROR: Could not find the required worksheet in the Excel file. Details: {e}")
    exit()


# --- Analyze Total Market Spending by Year ---
print("Calculating total property market spending per year...")
price_df['Price'] = pd.to_numeric(price_df['Price'], errors='coerce')
price_df['Year'] = price_df['DateOfTransfer'].dt.year

market_spend_by_year = price_df.groupby('Year')['Price'].sum().reset_index()
market_spend_by_year['Total_Spend_Millions'] = (market_spend_by_year['Price'] / 1_000_000).round(1)
print(" -> Market spending analysis complete.")

# --- Merge Development Data with Spending Data ---
print("Merging development and spending data for correlation...")
# The dev_df has 'Year' as an index, so we reset it to become a column for merging
dev_df.reset_index(inplace=True)
correlation_df = pd.merge(dev_df, market_spend_by_year, on='Year', how='inner')
print(" -> Data merged successfully.")

# --- Create the Dual-Axis Correlation Chart ---
print("Step 4: Generating final correlation chart...")
sns.set_theme(style="whitegrid")
fig, ax1 = plt.subplots(figsize=(14, 8))

# Bar chart for Total Dwellings Approved
color1 = 'cornflowerblue'
ax1.set_xlabel('Year', fontsize=12)
ax1.set_ylabel('Total Dwellings in Approved Plans', color=color1, fontsize=12, weight='bold')
ax1.bar(correlation_df['Year'], correlation_df['Total_Dwellings_in_Plans'], color=color1, label='Dwellings Approved')
ax1.tick_params(axis='y', labelcolor=color1)
# Add some padding to the y-axis limit
ax1.set_ylim(0, correlation_df['Total_Dwellings_in_Plans'].max() * 1.1)

# Line chart for Total Market Spend on the second Y-axis
ax2 = ax1.twinx()  # Create a second y-axis that shares the same x-axis
color2 = 'darkorange'
ax2.set_ylabel('Total Market Spend (£ Millions)', color=color2, fontsize=12, weight='bold')
ax2.plot(correlation_df['Year'], correlation_df['Total_Spend_Millions'], color=color2, marker='o', linestyle='--', label='Market Spend (£M)')
ax2.tick_params(axis='y', labelcolor=color2)
# Add some padding to the y-axis limit
ax2.set_ylim(0, correlation_df['Total_Spend_Millions'].max() * 1.1)

# Final Touches
plt.title('Cambridgeshire Development vs. Cambridge Market Spend (2010-2023)', fontsize=16, weight='bold')
fig.tight_layout()  
plt.xticks(correlation_df['Year'].unique(), rotation=45)

# Save the final chart
chart_output_path = os.path.join(OUTPUT_DIR, 'Development_vs_Market_Spend_Flowchart.png')
plt.savefig(chart_output_path, dpi=300)

print("\n--- VISUALIZATION COMPLETE ---")
print(f"✅ SUCCESS: Your correlation flowchart has been saved as a PNG file to:")
print(f"   -> {chart_output_path}")