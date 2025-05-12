import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import random
from datetime import date, timedelta
from sqlalchemy import create_engine, text

# Charger les variables d'environnement
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
    "&MultipleActiveResultSets=true"
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
    d += timedelta(days=(2 - d.weekday()) % 7)  # 2 représente mercredi
    while d.year == year:
        yield d
        d += timedelta(weeks=1)

wednesdays_2024 = list(get_wednesdays())

# 3. Sélectionner 50% des patients qui auront des symptômes
patients_avec_symptomes = set(random.sample(patient_ids, k=int(len(patient_ids) * 0.5)))

# 4. Générer les analyses
analyses = []
for patient_id in patient_ids:
    for d in wednesdays_2024:
        if patient_id in patients_avec_symptomes:
            # Déterminer si nous sommes en période hivernale
            is_hiver = d.month in [1, 2, 3, 11, 12]
            
            # Ajuster les probabilités en fonction de la période
            if is_hiver:
                proba_fievre = 0.9  # 90% en hiver
                proba_courbatures = 0.8  # 80% en hiver
                proba_fatigue = 0.7  # 70% en hiver
                proba_toux = 0.6  # 60% en hiver
            else:
                proba_fievre = 0.3  # 30% hors hiver
                proba_courbatures = 0.2  # 20% hors hiver
                proba_fatigue = 0.3  # 30% hors hiver
                proba_toux = 0.2  # 20% hors hiver
            
            # Générer des symptômes aléatoires avec les probabilités ajustées
            symptomes = []
            if random.random() < proba_fievre:
                symptomes.append(f"Fièvre {round(random.uniform(37.5, 39.5), 1)}°C")
            if random.random() < proba_courbatures:
                symptomes.append("Courbatures")
            if random.random() < proba_fatigue:
                symptomes.append("Fatigue")
            if random.random() < proba_toux:
                symptomes.append("Toux")
            
            commentaires = "Symptômes grippaux : " + ", ".join(symptomes) if symptomes else "Pas de symptômes grippaux"
        else:
            commentaires = "Pas de symptômes grippaux"
        
        analyses.append({
            "patient_id": patient_id,
            "date_analyse": d,
            "type_analyse": "Analyse grippe saisonnière",
            "commentaires": commentaires
        })

# 5. Insertion batch dans Analyse
insert_analyses_sql = text("""
INSERT INTO Analyse (patient_id, date_analyse, type_analyse, commentaires)
VALUES (:patient_id, :date_analyse, :type_analyse, :commentaires)
""")

with engine.begin() as conn:
    for batch in chunked(analyses, batch_size=1000):
        conn.execute(insert_analyses_sql, batch)

print("✅ Analyses insérées (batchs de 1000).") 