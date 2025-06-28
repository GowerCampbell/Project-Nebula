# 4_visualisation/create_final_visuals.py
# FINAL DEFINITIVE VERSION (with advanced map features)
# PURPOSE: To create a professional static chart and a powerful, multi-layer
# interactive map with zoomable, semi-transparent circles and individual site markers.

import pandas as pd
import geopandas as gpd
import os
import folium
import matplotlib.pyplot as plt
import seaborn as sns

print("\n--- SCRIPT 3 (ADVANCED MAP): GENERATE FINAL VISUALS ---")

# --- Configuration ---
INPUT_REPORT_PATH = os.path.join('reports', 'Cambridgeshire_Market_Analysis_FINAL.xlsx')
INPUT_MASTER_PATH = os.path.join('reports', 'Master_Cambridgeshire_Data.csv')
OUTPUT_DIR = 'reports'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- 1. Load the Final Analysis Data ---
print(f"Loading final analysis data from: {INPUT_REPORT_PATH}")
try:
    growth_by_year_df = pd.read_excel(INPUT_REPORT_PATH, sheet_name='Development Growth by Year')
    hotspot_analysis_df = pd.read_excel(INPUT_REPORT_PATH, sheet_name='Hotspot Analysis by Sector')
    all_sites_df = pd.read_csv(INPUT_MASTER_PATH)
    print(" -> Successfully loaded analysis data.")
except Exception as e:
    print(f" -> FATAL ERROR: Could not load required files. Please run previous scripts first. Details: {e}")
    exit()

# --- 2. Create and Save the Yearly Growth Chart (.png) ---
print("\nGenerating static bar chart for yearly development growth...")
growth_by_year_df.set_index('Year', inplace=True)
start_year = growth_by_year_df.index.min()
end_year = growth_by_year_df.index.max()
dynamic_title = f'Total Dwellings in Approved Plans per Year ({start_year}-{end_year})'

sns.set_theme(style="whitegrid")
plt.figure(figsize=(12, 7))
barplot = sns.barplot(x=growth_by_year_df.index, y='Total_Dwellings_in_Plans', data=growth_by_year_df, palette='viridis')
plt.title(dynamic_title, fontsize=16, weight='bold')
plt.xlabel('Year of Planning Permission', fontsize=12)
plt.ylabel('Total Number of Dwellings Approved', fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()
chart_output_path = os.path.join(OUTPUT_DIR, 'Yearly_Development_Growth.png')
plt.savefig(chart_output_path, dpi=300)
print(f"✅ SUCCESS: Yearly growth chart saved to: {chart_output_path}")


# --- 3. Create the Advanced Interactive Hotspot Map (.html) ---
print("\nGenerating advanced interactive map with multiple layers...")

# Prepare data for mapping
all_sites_df['Sector'] = all_sites_df['Address'].str.upper().str.extract(f"({'|'.join(hotspot_analysis_df.Sector.unique())})")
all_sites_df.dropna(subset=['Sector', 'longitude', 'latitude'], inplace=True)

all_sites_gdf = gpd.GeoDataFrame(
    all_sites_df,
    geometry=gpd.points_from_xy(all_sites_df.longitude, all_sites_df.latitude),
    crs="EPSG:4326"
)

sector_locations = all_sites_gdf.groupby('Sector')[['longitude', 'latitude']].mean().reset_index()
hotspot_map_data = pd.merge(hotspot_analysis_df, sector_locations, on='Sector', how='left')
hotspot_map_gdf = gpd.GeoDataFrame(
    hotspot_map_data,
    geometry=gpd.points_from_xy(hotspot_map_data.longitude, hotspot_map_data.latitude),
    crs="EPSG:4326"
)

# Create the base map
map_center = [52.3, 0.1]
site_map = folium.Map(location=map_center, zoom_start=10, tiles='CartoDB positron')

# --- LAYER 1: Hotspot Circles ---
hotspot_layer = folium.FeatureGroup(name='Development Hotspots (by Sector)', show=True)
for idx, row in hotspot_map_gdf.iterrows():
    total_dwellings = row['Total_Dwellings_Approved']
    radius_in_meters = (total_dwellings**0.5) * 100
    color = 'green' if total_dwellings <= 10 else 'orange' if total_dwellings <= 50 else 'red'
    popup_text = f"<h3>{row['Sector']}</h3><b>Total Dwellings Approved:</b> {int(total_dwellings)}"
    
    if pd.notna(row.geometry.y) and pd.notna(row.geometry.x):
        folium.Circle(
            location=[row.geometry.y, row.geometry.x],
            radius=radius_in_meters,
            color=color,
            fill=True,
            fill_opacity=0.5, # Make circles semi-transparent
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(hotspot_layer)
hotspot_layer.add_to(site_map)

# --- LAYER 2: Individual Project Markers ---
projects_layer = folium.FeatureGroup(name='Individual Projects', show=False) # Off by default
for idx, row in all_sites_gdf.iterrows():
    dwellings = row['Dwellings']
    if pd.notna(dwellings) and dwellings >= 1:
        popup_text = f"<b>Address:</b> {row['Address']}<br><b>Dwellings:</b> {int(dwellings)}"
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=3, # Small, consistent size
            color='navy',
            fill=True,
            fill_opacity=0.8,
            popup=popup_text
        ).add_to(projects_layer)
projects_layer.add_to(site_map)

# Add the Layer Control panel to the map
folium.LayerControl().add_to(site_map)

# Save the final map
map_output_path = os.path.join(OUTPUT_DIR, 'Final_Interactive_Dashboard_Map.html')
site_map.save(map_output_path)
print(f"✅ SUCCESS: Advanced Interactive Map saved to: {map_output_path}")

print("\n--- PROJECT VISUALS COMPLETE ---")