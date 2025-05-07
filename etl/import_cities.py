# Connexion à SQL Server
import pyodbc
# Libraries scientifiques (math)
import urllib
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
# Fichier utile (système et variable d'environnement)
from dotenv import load_dotenv
import sys
import os
from datetime import datetime
import csv

from dotenv import load_dotenv
# Charger le fichier .env
# Recharger variables d'envronnements
load_dotenv(override=True)

sys.path.append('../dbconnect')
sys.path.append('../filepath')
# Connexion à SQL Server
conn = pyodbc.connect("DRIVER={ODBC Driver 18 for SQL Server};"
                      "SERVER=localhost,1433;"
                      "DATABASE=health;"
                      "UID=sa;"
                      "PWD=Mouscron2025?;"
                      "Encrypt=yes;"
                      "TrustServerCertificate=yes;")

cursor = conn.cursor()
# Compteurs
inserted_rows = 0
error_rows = 0
# Charger les données depuis un CSV
filecsv = os.environ.get("ETL_CSV_FILE")
fichier_csv= filecsv + "/" + 'villes_americaines.csv'
# Fichier de log des erreurs
error_log_file = 'etl_errors.log'
with open(fichier_csv, newline='', encoding='utf-8')  as csvfile, \
     open(error_log_file, 'w', encoding='utf-8') as log_file:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            cursor.execute("""
                INSERT INTO dbo.Villes (
                    Ville, Latitude, Longitude
                )
                VALUES (?, ?, ?)
            """, 
            row['Ville'], row['Latitude'], row['Longitude'])

        except Exception as e:
            print(f"❌ Erreur sur la ligne {row}: {e}")
            continue  # Continue avec la ligne suivante

conn.commit()
cursor.close()
conn.close()
print("✅ ETL terminé.")
