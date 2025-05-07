import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import random
from datetime import date, timedelta
# Charger les variables d'environnement
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
# Charger le fichier .env
# Recharger variables d'envronnements
load_dotenv(override=True)
server = os.getenv("DB_SERVER") 
database = os.getenv("DB_NAME")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = os.getenv("ODBC_DRIVER", "{ODBC Driver 18 for SQL Server}")

# Chaîne de connexion SQLAlchemy
connection_string = (
    f"mssql+pyodbc://{username}:{password}@{server}/{database}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Encrypt=no&TrustServerCertificate=yes"
)

engine = create_engine(connection_string, fast_executemany=True)

# Fonction pour découper en batchs
def chunked(data, batch_size=1000):
    for i in range(0, len(data), batch_size):
        yield data[i:i+batch_size]

# 1. Charger les patients
df_patients = pd.read_sql("SELECT PatientID FROM Patients", engine)
patient_ids = df_patients['PatientID'].tolist()

# 2. Générer les mercredis de 2024
def get_wednesdays(year=2024):
    d = date(year, 1, 1)
    d += timedelta(days=(2 - d.weekday()) % 7)
    while d.year == year:
        yield d
        d += timedelta(weeks=1)

wednesdays_2024 = list(get_wednesdays())

# 3. Générer les prises de sang
analyses = []
for patient_id in patient_ids:
    for d in wednesdays_2024:
        crp = round(random.uniform(5, 50), 1)
        leucocytes = round(random.uniform(3, 8), 1)
        lymphocytes = round(random.uniform(30, 60), 1)
        neutrophiles = round(random.uniform(30, 60), 1)
        remarque = "Suivi grippe hebdomadaire"
        hiver = d.month in [1, 2, 3, 11, 12]
        positif = 1 if (hiver and crp > 30 and lymphocytes > 45) else 0

        analyses.append({
            "patient_id": patient_id,
            "date_analyse": d,
            "crp": crp,
            "leucocytes": leucocytes,
            "lymphocytes": lymphocytes,
            "neutrophiles": neutrophiles,
            "remarque": remarque,
            "positif_grippe": positif
        })

# 4. Insertion batch dans prises_sang
insert_analyses_sql = text("""
INSERT INTO prises_sang (
    patient_id, date_analyse, crp, leucocytes,
    lymphocytes, neutrophiles, remarque, positif_grippe
)
VALUES (
    :patient_id, :date_analyse, :crp, :leucocytes,
    :lymphocytes, :neutrophiles, :remarque, :positif_grippe
)
""")

with engine.begin() as conn:
    for batch in chunked(analyses, batch_size=1000):
        conn.execute(insert_analyses_sql, batch)

print("✅ Prises de sang insérées (batchs de 1000).")

# 5. Simuler les vaccinations (60 %)
vaccinations = []
for patient_id in random.sample(patient_ids, k=int(len(patient_ids) * 0.6)):
    date_vaccin = date(2023, 10, 15) + timedelta(days=random.randint(0, 30))
    lot = f"FLU-{random.randint(1000, 9999)}"
    vaccinations.append({
        "patient_id": patient_id,
        "date_vaccination": date_vaccin,
        "lot_vaccin": lot
    })

# 6. Insertion batch dans vaccinations_grippe
insert_vaccin_sql = text("""
INSERT INTO vaccinations_grippe (patient_id, date_vaccination, lot_vaccin)
VALUES (:patient_id, :date_vaccination, :lot_vaccin)
""")

with engine.begin() as conn:
    for batch in chunked(vaccinations, batch_size=1000):
        conn.execute(insert_vaccin_sql, batch)

print("✅ Vaccinations insérées (batchs de 1000).")