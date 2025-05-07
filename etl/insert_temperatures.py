import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
# Charger les variables d'environnement
from dotenv import load_dotenv
from sqlalchemy import create_engine
# Charger le fichier .env
# Recharger variables d'envronnements
load_dotenv(override=True)
server = os.getenv("DB_SERVER") 
database = os.getenv("DB_NAME")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = os.getenv("ODBC_DRIVER", "{ODBC Driver 18 for SQL Server}")

# Chaîne de connexion SQLAlchemy
engine = create_engine(
    "mssql+pyodbc://sa:Mouscron2025?@localhost:1433/health?"
    "driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes"
)
# Récupérer la liste des villes
villes = pd.read_sql("SELECT Ville FROM Villes", engine)['Ville'].tolist()

# Générer les dates de 2024
dates = pd.date_range(start='2024-01-01', end='2024-12-31')

# Définir les plages de températures selon le mois
def get_temp_range(month):
    if month in [1, 2]: return -10, 3
    elif month == 3: return 8, 22
    elif month in [4, 5, 6]: return 8, 22
    elif month in [7, 8, 9]: return 22, 30
    elif month in [10, 11, 12]: return -6, 22
    return -10, 30

# Créer les enregistrements
records = []
for date in dates:
    low, high = get_temp_range(date.month)
    for ville in villes:
        temp = round(np.random.uniform(low, high), 1)
        records.append({'Ville': ville, 'DateMesure': date, 'Temperature': temp})

# Convertir en DataFrame
df = pd.DataFrame(records)

# Insérer dans la base de données
df.to_sql('TemperaturesJournalieres', con=engine, if_exists='append', index=False)