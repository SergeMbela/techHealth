# Database connection and scientific libraries
import pyodbc
import urllib
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
import sys
import os
from datetime import datetime
import csv

# Load environment variables
load_dotenv(override=True)

# Add custom paths
sys.path.append('../dbconnect')
sys.path.append('../filepath')

def validate_city_data(row):
    """Validate city data fields"""
    try:
        # Validate required fields
        if not row['Ville'].strip():
            raise ValueError("City name cannot be empty")
            
        # Validate numeric fields
        population = int(row['Population'])
        if population <= 0:
            raise ValueError(f"Invalid population: {population}")
            
        # Validate coordinates
        latitude = float(row['Latitude'])
        longitude = float(row['Longitude'])
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Invalid latitude: {latitude}")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Invalid longitude: {longitude}")
            
        # Validate pollution metrics
        pm25 = float(row['PM2.5 (µg/m³)'])
        no2 = float(row['NO2 (ppb)'])
        o3 = float(row['O3 (ppb)'])
        if any(x < 0 for x in [pm25, no2, o3]):
            raise ValueError("Pollution metrics cannot be negative")
            
        # Validate health metrics
        grippe_cas = int(row['Grippe (cas/100k hab.)'])
        hosp_rate = float(row['Hospitalisations grippe (taux %)'])
        if grippe_cas < 0:
            raise ValueError(f"Invalid flu cases: {grippe_cas}")
        if not (0 <= hosp_rate <= 100):
            raise ValueError(f"Invalid hospitalization rate: {hosp_rate}")
            
        return {
            'Ville': row['Ville'].strip(),
            'Latitude': latitude,
            'Longitude': longitude,
            'Population': population,
            'PM25': pm25,
            'NO2': no2,
            'O3': o3,
            'Grippe_Cas_100k': grippe_cas,
            'Hospitalisations_Grippe_Pourcentage': hosp_rate
        }
    except (ValueError, KeyError) as e:
        raise ValueError(f"Data validation error: {str(e)}")

# Create database connection
conn = pyodbc.connect("DRIVER={ODBC Driver 18 for SQL Server};"
                      "SERVER=localhost,1433;"
                      "DATABASE=health;"
                      "UID=sa;"
                      "PWD=Mouscron2025?;"
                      "Encrypt=yes;"
                      "TrustServerCertificate=yes;")

cursor = conn.cursor()

# Initialize counters
inserted_rows = 0
error_rows = 0
skipped_rows = 0
error_details = []

# Get existing cities
cursor.execute("SELECT Ville FROM [dbo].[Villes]")
existing_cities = {row[0].lower() for row in cursor.fetchall()}
print(f"Found {len(existing_cities)} existing cities in database")

# Load CSV data
filecsv = os.environ.get("ETL_CSV_FILE")
fichier_csv = filecsv + "/" + 'villes_americaines.csv'

# Process CSV file
error_log_file = 'etl_errors.log'
with open(fichier_csv, newline='', encoding='utf-8') as csvfile, \
     open(error_log_file, 'w', encoding='utf-8') as log_file:
    reader = csv.DictReader(csvfile)
    
    # Process each row
    for row in reader:
        try:
            # Check for duplicate city
            city_name = row['Ville'].strip().lower()
            if city_name in existing_cities:
                skipped_rows += 1
                print(f"⚠️ Skipping duplicate city: {row['Ville']}")
                continue
            
            # Validate data
            validated_data = validate_city_data(row)
            
            # Insert data
            cursor.execute("""
                INSERT INTO [dbo].[Villes]
                ([Ville], [Latitude], [Longitude], [Population],
                [PM25], [NO2], [O3], [Grippe_Cas_100k], [Hospitalisations_Grippe_Pourcentage])
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
            validated_data['Ville'],
            validated_data['Latitude'],
            validated_data['Longitude'],
            validated_data['Population'],
            validated_data['PM25'],
            validated_data['NO2'],
            validated_data['O3'],
            validated_data['Grippe_Cas_100k'],
            validated_data['Hospitalisations_Grippe_Pourcentage'])
            
            inserted_rows += 1
            existing_cities.add(city_name)
            
        except Exception as e:
            error_rows += 1
            error_msg = f"❌ Error on city {row.get('Ville', 'Unknown')}: {e}\n"
            print(error_msg)
            log_file.write(error_msg)
            
            # Save error details
            error_details.append({
                'Ville': row.get('Ville', ''),
                'Error': str(e)
            })
            
            # Save to error CSV
            error_df = pd.DataFrame([row])
            error_df.to_csv('error_insert_cities.csv', 
                          mode='a', 
                          index=False, 
                          header=not os.path.exists('error_insert_cities.csv'))
            continue

# Commit transaction
try:
    conn.commit()
    print("✅ Transaction committed successfully")
except Exception as e:
    conn.rollback()
    print(f"❌ Transaction failed: {e}")
    raise
finally:
    cursor.close()
    conn.close()

# Print summary
print("\nETL Process Summary Report")
print("=" * 50)
print(f"Total rows processed: {inserted_rows + error_rows + skipped_rows}")
print(f"Successfully inserted: {inserted_rows}")
print(f"Skipped (duplicates): {skipped_rows}")
print(f"Failed rows: {error_rows}")
print(f"Success rate: {(inserted_rows/(inserted_rows + error_rows + skipped_rows))*100:.2f}%")

if error_details:
    print("\nError Details:")
    error_df = pd.DataFrame(error_details)
    print(error_df.head())
    
    # Save error details to CSV
    error_df.to_csv('error_details_cities.csv', index=False)
    print("\nError details saved to 'error_details_cities.csv'")

