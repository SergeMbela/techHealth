import os
import random
import sys
import time
import pandas as pd
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv
from sqlalchemy import text


# Charger les variables d'environnement
load_dotenv(override=True)
sys.path.append(os.getenv("DBCONNECT_PARENT"))
from dbconnect.connection import SQLServerConnector
# Connexion SQLAlchemy
conn = SQLServerConnector()
engine = conn.get_sqlalchemy_engine()

# Étape 1 : Récupérer les villes et leurs populations
with engine.connect() as connection:
    villes_df = pd.read_sql("SELECT Ville, Population FROM Villes", connection)

# Analyse des données des villes
print("\nStatistiques des populations par ville:")
print(villes_df['Population'].describe())

# Étape 2 : Tirage pondéré de 100 000 villes
villes_choisies = random.choices(
    villes_df["Ville"].tolist(),
    weights=villes_df["Population"].tolist(),
    k=100_000
)

# Créer un DataFrame pour les villes choisies
villes_choisies_df = pd.DataFrame({
    'id_patient': range(1, len(villes_choisies) + 1),
    'Ville': villes_choisies
})

# Analyse de la distribution
distribution = villes_choisies_df['Ville'].value_counts()
print("\nDistribution des patients par ville:")
print(f"Nombre total de villes utilisées: {len(distribution)}")
print(f"Villes avec le plus de patients:")
print(distribution.head())

# Étape 3 : Préparer les tuples (id_patient, Ville)
associations = list(zip(villes_choisies_df['id_patient'], villes_choisies_df['Ville']))

# Étape 4 : Insertion en batch avec barre de progression
insert_query = text("INSERT INTO patients_cities (id_patient, Ville) VALUES (:id_patient, :Ville)")
batch_size = 10_000
start_time = time.time()

with engine.begin() as connection:  # engine.begin() gère commit automatiquement
    for i in tqdm(range(0, len(associations), batch_size), desc="Insertion des données"):
        batch = associations[i:i+batch_size]
        connection.execute(insert_query, [
            {"id_patient": id_patient, "Ville": ville}
            for id_patient, ville in batch
        ])

elapsed = time.time() - start_time
print(f"\nInsertion terminée en {elapsed:.2f} secondes.")

# Vérification finale
with engine.connect() as connection:
    verification_df = pd.read_sql("""
        SELECT COUNT(*) as total_patients, 
               COUNT(DISTINCT Ville) as total_villes
        FROM patients_cities
    """, connection)
    print("\nVérification finale:")
    print(verification_df)
