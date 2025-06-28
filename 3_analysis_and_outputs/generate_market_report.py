# 3_analysis_and_outputs/generate_market_report.py
# PURPOSE: To generate a highly accurate and clean market intelligence report by
# focusing on a consistent timeframe (2010-2023) and excluding any data
# that cannot be reliably categorized into a known town/village sector.

import pandas as pd
import os
from sqlalchemy import create_engine
from openpyxl import Workbook

print("\n--- GENERATE DEFINITIVE MARKET REPORT ---")

# --- Configuration ---
INPUT_MASTER_PATH = os.path.join('reports', 'Master_Cambridgeshire_Data.csv')
OUTPUT_DIR = 'reports'
os.makedirs(OUTPUT_DIR, exist_ok=True)
db_engine = create_engine('sqlite:///:memory:')

# ---  Load Master Data into SQL Database ---
print(f"Loading master data from: {INPUT_MASTER_PATH}")
try:
    master_df = pd.read_csv(INPUT_MASTER_PATH)
    master_df.to_sql('cambridge_sites', db_engine, if_exists='replace', index=False)
    print(f" -> Successfully loaded {len(master_df)} sites into SQL database.")
except Exception as e:
    print(f" -> ERROR: Could not load master file. Please run script 1 first. Error: {e}")
    exit()

# --- 2. Use SQL to Query ALL Permissioned Sites ---
print("Using SQL to query for all permissioned sites...")
sql_query = "SELECT * FROM cambridge_sites WHERE PlanningStatus = 'permissioned';"
all_activity_df = pd.read_sql_query(sql_query, db_engine, parse_dates=['PermissionDate'])
all_activity_df['Dwellings'] = pd.to_numeric(all_activity_df['Dwellings'], errors='coerce').fillna(0)
print(f" -> Found {len(all_activity_df)} permissioned sites for analysis.")


# --- 3. Data Cleaning and Filtering ---
print("\nCleaning data: Filtering for dates since 2010 and parsing sectors...")

# --- Filter for a consistent timeframe from 2010 onwards ---
analysis_df = all_activity_df[all_activity_df['PermissionDate'] >= '2010-01-01'].copy()
print(f" -> Focusing on {len(analysis_df)} sites with permissions granted since 2010.")

# ---  Intelligent Sector Parsing ---
cambridgeshire_sectors = [
    'FULBOURN', 'GREAT SHELFORD', 'HISTON', 'OAKINGTON', 'IMPINGTON', 'TEVERSHAM',
    'LINTON', 'WATERBEACH', 'SAWSTON', 'MELDRETH', 'MELBOURN', 'FOXTON',
    'HARDWICK', 'CALDECOTE', 'SWAVESEY', 'PAPWORTH EVERARD', 'MILTON', 'HARSTON',
    'BASSINGBOURN', 'COTTENHAM', 'GAMLINGAY', 'COMBERTON', 'BARTON', 'ROYSTON', 'SANDY'
]
pattern = f'({"|".join(cambridgeshire_sectors)})'
analysis_df['Sector'] = analysis_df['Address'].str.upper().str.extract(pattern)

# --- Remove all uncategorized sites ---
initial_count = len(analysis_df)
analysis_df.dropna(subset=['Sector'], inplace=True)
removed_count = initial_count - len(analysis_df)
print(f" -> Removed {removed_count} sites that could not be categorized into a known sector.")
print(f" -> {len(analysis_df)} categorized sites remain for final analysis.")


# --- 4. Perform Final, Cleaned Analysis ---
print("\nPerforming final analysis on cleaned data...")

# Analysis A: Growth of Development Over Time (2010-Present)
analysis_df['Year'] = analysis_df['PermissionDate'].dt.year
growth_by_year = analysis_df.groupby('Year').agg(
    Total_Permissions_Granted=('SiteReference', 'count'),
    Total_Dwellings_in_Plans=('Dwellings', 'sum')
).sort_values(by='Year', ascending=False)
print(" -> Yearly growth analysis complete.")

# Hotspot Analysis (for sites providing new dwellings)
dwelling_dev_df = analysis_df[analysis_df['Dwellings'] >= 1].copy()
hotspot_analysis = dwelling_dev_df.groupby('Sector').agg(
    Total_Dwellings_Approved=('Dwellings', 'sum'),
    Number_of_Projects=('Sector', 'count')
).sort_values(by='Total_Dwellings_Approved', ascending=False)

total_dwellings = hotspot_analysis['Total_Dwellings_Approved'].sum()
hotspot_analysis['%_of_Total_Dwellings'] = ((hotspot_analysis['Total_Dwellings_Approved'] / total_dwellings) * 100).round(2)
print(" -> Hotspot and % Growth analysis complete.")


# --- Save the Final, Cleaned Intelligence Report ---
output_excel_path = os.path.join(OUTPUT_DIR, 'Cambridgeshire_Market_Analysis_FINAL.xlsx')
print(f"\nSaving final multi-tabbed Excel report to: {output_excel_path}")

with pd.ExcelWriter(output_excel_path) as writer:
    growth_by_year.to_excel(writer, sheet_name='Development Growth (2010-Present)')
    hotspot_analysis.to_excel(writer, sheet_name='Hotspot Analysis by Sector')
    analysis_df.to_excel(writer, sheet_name='Cleaned Data Used in Report', index=False)

print("\n✅ SUCCESS: Final, cleaned Market Analysis Report Generated.")