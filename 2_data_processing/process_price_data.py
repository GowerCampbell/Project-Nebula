# 2_data_processing/process_price_data.py
# PURPOSE: To process the enormous national Price Paid dataset,
# filtering it down to a manageable CSV containing only Cambridgeshire sales
# from 2010 to 2023.

import pandas as pd
import os

print("\n--- PRICE DATA PROCESSING SCRIPT ---")

# --- Configuration ---
INPUT_PRICE_PAID_PATH = os.path.join('1_data_acquisition', 'raw_data', 'land_registry_data', 'pp-complete.csv')
OUTPUT_DIR = 'reports'
OUTPUT_CLEAN_PRICE_PATH = os.path.join(OUTPUT_DIR, 'Cambridgeshire_Price_Data_2010-2023.csv')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define the postcode prefixes for the Cambridgeshire area
TARGET_POSTCODE_PREFIXES = ('CB', 'PE', 'SG')

print(f"Loading national Price Paid data from: {INPUT_PRICE_PAID_PATH}")
print("This will be slow as the file is very large...")

try:
    # --- Load the data efficiently ---
    column_names = [
        'TransactionID', 'Price', 'DateOfTransfer', 'Postcode', 'PropertyType',
        'OldNew', 'Duration', 'PAON', 'SAON', 'Street', 'Locality',
        'TownCity', 'District', 'County', 'PPD_Category', 'Record_Status'
    ]
    # We only load the columns we need to save memory.
    use_cols = ['Price', 'DateOfTransfer', 'Postcode']
    
    df = pd.read_csv(INPUT_PRICE_PAID_PATH, header=None, names=column_names, usecols=use_cols)
    
    print(f" -> Loaded {len(df):,} records from the UK dataset.")

except FileNotFoundError:
    print(f" -> ERROR: File not found. Please check the filename in INPUT_PRICE_PAID_PATH.")
    exit()

# --- Filter by Postcode to get the Cambridgeshire Area ---
print(f"\nStep 1: Filtering for Cambridgeshire area postcodes ({', '.join(TARGET_POSTCODE_PREFIXES)})...")
df.dropna(subset=['Postcode'], inplace=True)
df_cambs = df[df['Postcode'].str.startswith(TARGET_POSTCODE_PREFIXES)].copy()
print(f" -> Found {len(df_cambs):,} sales records in the Cambridgeshire area.")

# --- Filter by Date (2010-2023) ---
print("\nStep 2: Filtering for sales between 2010 and 2023...")
# Convert 'DateOfTransfer' to a proper datetime object for filtering
df_cambs['DateOfTransfer'] = pd.to_datetime(df_cambs['DateOfTransfer'], errors='coerce')
# Keep only the rows within our target date range
df_cambs_filtered = df_cambs[
    (df_cambs['DateOfTransfer'] >= '2010-01-01') & 
    (df_cambs['DateOfTransfer'] <= '2023-12-31')
].copy()
print(f" -> {len(df_cambs_filtered):,} sales records remain after date filtering.")

# --- Save the Clean, Focused Dataset ---
df_cambs_filtered.to_csv(OUTPUT_CLEAN_PRICE_PATH, index=False)

print("\n--- DATA PROCESSING COMPLETE ---")
print(f"✅ SUCCESS: A clean, focused dataset of Cambridgeshire house sales has been saved to:")
print(f"   -> {OUTPUT_CLEAN_PRICE_PATH}")