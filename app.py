from flask import Flask, render_template
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from scipy import stats

# Load environment variables
load_dotenv()

app = Flask(__name__)

def connect_to_database():
    """Connect to SQL Server database using SQLAlchemy"""
    try:
        connection_string = (
            f"mssql+pyodbc://{os.getenv('DB_USER', 'sa')}:{os.getenv('DB_PASSWORD', 'Mouscron2025?')}@"
            f"{os.getenv('DB_HOST', 'localhost,1433')}/{os.getenv('DB_NAME', 'health')}?"
            "driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        )
        engine = create_engine(connection_string)
        return engine
    except Exception as err:
        print(f"Error connecting to database: {err}")
        return None

def get_analysis_data():
    """Retrieve and process analysis data"""
    engine = connect_to_database()
    
    query = """
    SELECT 
        pc.Ville,
        a.date_analyse,
        a.PatientID,
        ra.valeur,
        pb.valeur_reference,
        tj.Temperature,
        p.PM25,
        p.PM10,
        p.NO2,
        p.O3,
        p.SO2,
        p.CO,
        p.AQI
    FROM patients_cities pc
    JOIN Analyse a ON pc.id_patient = a.PatientID
    JOIN ResultatAnalyse ra ON a.id = ra.analyse_id
    JOIN ParametreBiologique pb ON ra.parametre_id = pb.id
    JOIN TemperaturesJournalieres tj ON pc.Ville = tj.Ville 
        AND CONVERT(date, a.date_analyse) = tj.DateMesure
    LEFT JOIN PollutionData p ON pc.Ville = p.Ville 
        AND CONVERT(date, a.date_analyse) = p.DateMesure
    """
    
    df = pd.read_sql(query, engine)
    
    # Calculate treatment success
    def is_value_within_reference(value, reference):
        try:
            value = float(value)
            if '<' in reference:
                threshold = float(reference.split('<')[1].strip())
                return value < threshold
            elif '>' in reference:
                threshold = float(reference.split('>')[1].strip())
                return value > threshold
            else:
                parts = reference.split('-')
                if len(parts) == 2:
                    min_val = float(parts[0].strip())
                    max_val = float(parts[1].strip())
                    return min_val <= value <= max_val
                else:
                    ref_val = float(reference.strip())
                    return abs(value - ref_val) <= 0.1
        except (ValueError, TypeError):
            return False
    
    df['treatment_success'] = df.apply(
        lambda row: is_value_within_reference(row['valeur'], row['valeur_reference']), 
        axis=1
    )
    
    # Add season information
    def get_season(date):
        m = pd.to_datetime(date).month
        if m in [12, 1, 2]:
            return 'Hiver'
        elif m in [3, 4, 5]:
            return 'Printemps'
        elif m in [6, 7, 8]:
            return 'Été'
        else:
            return 'Automne'
    
    df['season'] = df['date_analyse'].apply(get_season)
    
    # Aggregate data by city
    city_stats = df.groupby('Ville').agg({
        'treatment_success': 'mean',
        'Temperature': 'mean',
        'PM25': 'mean',
        'PM10': 'mean',
        'NO2': 'mean',
        'O3': 'mean',
        'SO2': 'mean',
        'CO': 'mean',
        'AQI': 'mean',
        'PatientID': 'count'
    }).rename(columns={'PatientID': 'patient_count'})
    
    # Calculate correlations with p-values
    correlation_data = city_stats[['treatment_success', 'Temperature', 'PM25', 'PM10', 'NO2', 'O3', 'SO2', 'CO', 'AQI']]
    correlations = {}
    p_values = {}
    
    for col in correlation_data.columns:
        if col != 'treatment_success':
            corr, p_val = stats.pearsonr(correlation_data['treatment_success'], correlation_data[col])
            correlations[col] = corr
            p_values[col] = p_val
    
    # Get top 5 cities
    top_cities = city_stats.nlargest(5, 'treatment_success')
    
    # Seasonal analysis
    seasonal_stats = df.groupby('season')['treatment_success'].agg(['mean', 'std', 'count'])
    
    # French explanations
    explanations = {
        'title': 'Analyse de l\'Impact du Climat et de la Pollution sur les Traitements',
        'top_cities': {
            'title': 'Top 5 des Villes par Taux de Réussite des Traitements',
            'description': 'Les villes présentées ci-dessous montrent les meilleurs taux de réussite des traitements, avec leurs conditions environnementales moyennes.'
        },
        'correlations': {
            'title': 'Corrélations avec le Taux de Réussite des Traitements',
            'description': 'Ce graphique montre l\'influence des différents facteurs environnementaux sur l\'efficacité des traitements. Une corrélation positive indique que des valeurs plus élevées sont associées à un meilleur taux de réussite, tandis qu\'une corrélation négative suggère l\'inverse.'
        },
        'city_comparison': {
            'title': 'Comparaison des Villes',
            'description': 'Ce graphique radar permet de comparer les différentes villes selon plusieurs métriques clés. Chaque axe représente un facteur différent, permettant de visualiser les forces et faiblesses de chaque ville en termes de conditions environnementales.'
        },
        'metrics': {
            'Temperature': 'Température moyenne en degrés Celsius',
            'PM25': 'Particules fines (PM2.5) en μg/m³',
            'PM10': 'Particules en suspension (PM10) en μg/m³',
            'NO2': 'Dioxyde d\'azote en ppb',
            'O3': 'Ozone en ppb',
            'SO2': 'Dioxyde de soufre en ppb',
            'CO': 'Monoxyde de carbone en ppm',
            'AQI': 'Indice de qualité de l\'air'
        }
    }
    
    return {
        'correlations': correlations,
        'p_values': p_values,
        'top_cities': top_cities.to_dict('index'),
        'city_stats': city_stats.to_dict('index'),
        'seasonal_stats': seasonal_stats.to_dict(),
        'explanations': explanations
    }

@app.route('/')
def index():
    """Render the main analysis dashboard"""
    data = get_analysis_data()
    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8085) 