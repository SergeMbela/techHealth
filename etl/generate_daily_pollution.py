import pyodbc
import random
from datetime import datetime, timedelta

# List of all cities (from your analysis)
cities = [
    'New York', 'Chicago', 'Los Angeles', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego',
    'Dallas', 'San Jose', 'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco',
    'Indianapolis', 'Seattle', 'Denver', 'Washington', 'Boston', 'El Paso', 'Nashville', 'Detroit',
    'Portland', 'Memphis', 'Oklahoma City', 'Las Vegas', 'Louisville', 'Baltimore'
]

# Pollution base values by season (approximate, for realism)
seasonal_base = {
    'winter': {'PM25': 14, 'PM10': 28, 'NO2': 36, 'O3': 28, 'SO2': 4.5, 'CO': 0.8, 'AQI': 45},
    'spring': {'PM25': 11, 'PM10': 23, 'NO2': 30, 'O3': 45, 'SO2': 3.5, 'CO': 0.7, 'AQI': 38},
    'summer': {'PM25': 9,  'PM10': 20, 'NO2': 27, 'O3': 65, 'SO2': 2.8, 'CO': 0.6, 'AQI': 32},
    'fall':   {'PM25': 11, 'PM10': 23, 'NO2': 32, 'O3': 35, 'SO2': 3.8, 'CO': 0.7, 'AQI': 37},
}

def get_season(date):
    m = date.month
    if m in [12, 1, 2]:
        return 'winter'
    elif m in [3, 4, 5]:
        return 'spring'
    elif m in [6, 7, 8]:
        return 'summer'
    else:
        return 'fall'

def randomize(val, percent=0.15):
    """Add random noise to a value."""
    return round(val * (1 + random.uniform(-percent, percent)), 2)

def main():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 18 for SQL Server};'
        'SERVER=localhost,1433;'
        'DATABASE=health;'
        'UID=sa;'
        'PWD=Mouscron2025?;'
        'TrustServerCertificate=yes;'
    )
    cursor = conn.cursor()
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    delta = timedelta(days=1)
    rows = []
    for city in cities:
        date = start_date
        while date <= end_date:
            season = get_season(date)
            base = seasonal_base[season]
            PM25 = randomize(base['PM25'])
            PM10 = randomize(base['PM10'])
            NO2 = randomize(base['NO2'])
            O3 = randomize(base['O3'])
            SO2 = randomize(base['SO2'])
            CO = randomize(base['CO'])
            AQI = int(randomize(base['AQI'], percent=0.2))
            rows.append((city, date.strftime('%Y-%m-%d'), PM25, PM10, NO2, O3, SO2, CO, AQI))
            date += delta
    print(f"Inserting {len(rows)} rows...")
    cursor.fast_executemany = True
    cursor.execute("DELETE FROM PollutionData")  # Clear old data
    cursor.executemany(
        """
        INSERT INTO PollutionData (Ville, DateMesure, PM25, PM10, NO2, O3, SO2, CO, AQI)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows
    )
    conn.commit()
    print("Done.")
    conn.close()

if __name__ == "__main__":
    main() 