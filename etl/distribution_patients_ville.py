import pyodbc
import random
# Fichier utile (système et variable d'environnement)
from dotenv import load_dotenv
import sys
import os
# Connexion à SQL Server
conn = pyodbc.connect(
   "DRIVER={ODBC Driver 18 for SQL Server};"
                      "SERVER=localhost,1433;"
                      "DATABASE=health;"
                      "UID=sa;"
                      "PWD=Mouscron2025?;"
                      "Encrypt=yes;"
                      "TrustServerCertificate=yes;"
)
cursor = conn.cursor()

# Étape 1 : Récupérer les villes et leurs populations
cursor.execute("SELECT Id_Ville, Population FROM Villes")
villes = cursor.fetchall()  # [(Id_ville, Population)]

ville_ids = [v[0] for v in villes]
populations = [v[1] for v in villes]

# Étape 2 : Tirage pondéré de 100 000 villes
villes_choisies = random.choices(ville_ids, weights=populations, k=100_000)

# Étape 3 : Préparer les tuples (id_patient, ville_id)
# On suppose que les PatientID dans la table patients vont de 1 à 100000
associations = [(i + 1, villes_choisies[i]) for i in range(100_000)]

# Étape 4 : Insertion dans patients_cities
batch_size = 10000
for i in range(0, len(associations), batch_size):
    batch = associations[i:i+batch_size]
    print(batch)
    cursor.executemany("INSERT INTO patients_cities (id_patient, ville_id) VALUES (?, ?)", batch)
    conn.commit()

conn.close()
