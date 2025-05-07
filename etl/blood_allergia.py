import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
# Connexion à SQL Server
from sqlalchemy import create_engine
import urllib
import seaborn as sns
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import sys
import os

# Recharger variables d'envronnements
load_dotenv(override=True)
sys.path.append(os.getenv("DBCONNECT_PARENT"))  # The parent of `dbconnect`
from dbconnect.connection import SQLServerConnector
# Use the class
conn = SQLServerConnector()
print(conn.get_connection_string())
# Build connection string
conn_str = conn.get_connection_string()
params = urllib.parse.quote_plus(conn_str)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
#Requête SQL 
query = "SELECT BloodType,Allergies FROM health.dbo.Patients"
df = pd.read_sql(query, con=engine)

#Analyse statistique avec le test du chi2
from scipy.stats import chi2_contingency
#Table de contigence
contigence= pd.crosstab(df['BloodType'],df['Allergies'])
print("Table de contigence")
print(contigence)

#Test du chi2
chi2, p, dof, expected = chi2_contingency(contigence)
print(f"\nStatistique chi2: {chi2:.2f}")
print(f"p-value: {p:.4f}")
if p < 0.05:
    print("=>Association significative entre le groupe sanguin et les allergies")
else:
    print("=>Aucune association trouvée.")