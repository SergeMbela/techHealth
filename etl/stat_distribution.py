import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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



# Remplace ces informations par les tiennes
server = server
database = database
username = username
password = password
# Chaîne de connexion SQLAlchemy avec driver ODBC
connection_string = (
    f"mssql+pyodbc://{username}:{password}@{server}/{database}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Encrypt=no&TrustServerCertificate=yes"
)

# Créer un moteur SQLAlchemy
engine = create_engine(connection_string)

# Requête SQL
query = """
SELECT 
    v.Id_Ville, 
    v.Ville, 
    COUNT(pc.id_patient_city) AS nb_patients,
    v.population AS population_ville
FROM 
    Villes v
JOIN 
    patients_cities pc ON v.Id_Ville = pc.ville_id
GROUP BY 
    v.Id_Ville, v.Ville, v.population
"""

# Lire les résultats dans un DataFrame
df = pd.read_sql(query, engine)

# Traitement pandas (statistiques, visualisation, etc.)
df['pourcentage_patients'] = (df['nb_patients'] / df['nb_patients'].sum()) * 100
df['pourcentage_population'] = (df['population_ville'] / df['population_ville'].sum()) * 100

print(df)
# Graphique
plt.figure(figsize=(12, 6))
sns.barplot(x='Ville', y='pourcentage_patients', data=df)
plt.title("Nombre de patients par ville")
plt.xlabel("Ville")
plt.ylabel("Nombre de patients")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()