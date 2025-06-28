# 2_data_processing/load_and_combine.py
# PURPOSE: To build a custom Cambridgeshire boundary by combining local GML files,
# then use it to filter the national brownfield dataset, clean the results,
# and save a single, master CSV file.

import pandas as pd
import geopandas as gpd
import os

print("--- LOAD AND COMBINE ---")

# --- Configuration ---
DATA_DIR = os.path.join('1_data_acquisition', 'raw_data')
OUTPUT_DIR = 'reports'
MASTER_CSV_PATH = os.path.join(OUTPUT_DIR, 'Brownsfrield_Cambridgeshire_Data.csv')
os.makedirs(OUTPUT_DIR, exist_ok=True)

NATIONAL_SITES_PATH = os.path.join(DATA_DIR, 'brownfield_registers', 'uk_brownfield_sites.csv')

GML_DIR = os.path.join(DATA_DIR, 'land_registry_data')
gml_paths = {
    "Cambridge_City": os.path.join(GML_DIR, 'Cambridge_City_Council', 'Land_Registry_Cadastral_Parcels.gml'),
    "East_Cambs": os.path.join(GML_DIR, 'East_Cambridgeshire_District_Council', 'Land_Registry_Cadastral_Parcels.gml'),
    "South_Cambs": os.path.join(GML_DIR, 'South_Cambridgeshire_District_Council', 'Land_Registry_Cadastral_Parcels.gml')
}

# --- Load and Create a Custom Cambridgeshire Boundary from GML files ---
print("\nStep 1: Loading GML files to build a custom Cambridgeshire boundary...")
all_parcels = []
for council, path in gml_paths.items():
    try:
        gdf = gpd.read_file(path)
        all_parcels.append(gdf)
        print(f" -> Successfully loaded GML for {council}")
    except Exception as e:
        print(f" -> WARNING: Could not load GML for {council}. Check the path in the script. Error: {e}")

if not all_parcels:
    print(" -> FATAL ERROR: No GML files were loaded. Cannot create a boundary. Exiting.")
    exit()

combined_parcels_gdf = pd.concat(all_parcels, ignore_index=True)
print(" -> Dissolving internal boundaries to create a single county shape...")
cambridgeshire_boundary = combined_parcels_gdf.union_all()
cambridgeshire_boundary_gdf = gpd.GeoDataFrame(geometry=[cambridgeshire_boundary], crs="EPSG:27700")
print(" -> Custom Cambridgeshire boundary created successfully.")

# --- Load National Brownfield Data ---
print("\nLoading national brownfield dataset...")
try:
    # --- UPDATED: Using the correct column names from your file ---
    use_cols = ['point', 'reference', 'site-address', 'planning-permission-date', 
                'hectares', 'planning-permission-status', 'maximum-net-dwellings', 'organisation']
    
    national_df = pd.read_csv(NATIONAL_SITES_PATH, usecols=use_cols, low_memory=False)
    
    print(" -> Extracting longitude and latitude from the 'point' column...")
    coords = national_df['point'].str.extract(r'POINT\(([-\d\.]+) ([-\d\.]+)\)')
    national_df['longitude'] = pd.to_numeric(coords[0], errors='coerce')
    national_df['latitude'] = pd.to_numeric(coords[1], errors='coerce')
    national_df.dropna(subset=['longitude', 'latitude'], inplace=True)
    
    national_gdf = gpd.GeoDataFrame(
        national_df,
        geometry=gpd.points_from_xy(national_df.longitude, national_df.latitude),
        crs="EPSG:4326"
    )
    print(f" -> Loaded and processed {len(national_gdf):,} sites from the national register.")
except Exception as e:
    print(f" -> FATAL ERROR: Could not process national brownfield CSV. Error: {e}")
    exit()

# --- Spatially Filter to Cambridgeshire using our Custom Boundary ---
print("\nGeographically filtering for sites within your custom boundary...")
cambridgeshire_boundary_gdf = cambridgeshire_boundary_gdf.to_crs(national_gdf.crs)
cambridgeshire_sites_gdf = gpd.sjoin(national_gdf, cambridgeshire_boundary_gdf, how="inner", predicate="within")
print(f" -> Found {len(cambridgeshire_sites_gdf)} sites within the Cambridgeshire area.")

# --- Clean, De-duplicate, and Save the Final Master CSV ---
print("\nCleaning and de-duplicating the local dataset...")
cambridgeshire_sites_gdf.rename(columns={
    'reference': 'SiteReference', 'site-address': 'Address',
    'planning-permission-date': 'PermissionDate', 'hectares': 'Hectares',
    'planning-permission-status': 'PlanningStatus', 'maximum-net-dwellings': 'Dwellings',
    'organisation': 'Council'
}, inplace=True)

cambridgeshire_sites_gdf['PermissionDate'] = pd.to_datetime(cambridgeshire_sites_gdf['PermissionDate'], errors='coerce')
cambridgeshire_sites_gdf.sort_values(by='PermissionDate', ascending=False, inplace=True)
cambridgeshire_sites_gdf.drop_duplicates(subset=['SiteReference'], keep='first', inplace=True)
print(f" -> {len(cambridgeshire_sites_gdf)} unique sites remain after cleaning.")

final_df = pd.DataFrame(cambridgeshire_sites_gdf.drop(columns=['geometry', 'index_right']))
final_df.to_csv(MASTER_CSV_PATH, index=False)

print(f"\n✅ SUCCESS: A clean master data file for Cambridgeshire has been created at: {MASTER_CSV_PATH}")