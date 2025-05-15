from flask import Flask, send_from_directory, render_template, jsonify
import os
import pandas as pd
import json
import matplotlib
matplotlib.use('Agg')  # Utiliser le backend non-interactif
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from scipy import stats
import numpy as np
import logging
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load environment variables
load_dotenv()

def connect_to_database():
    """Établir la connexion à la base de données SQL Server"""
    try:
        # SQL Server connection string
        connection_string = (
            "mssql+pyodbc://sa:Mouscron2025?@localhost,1433/health?"
            "driver=ODBC+Driver+18+for+SQL+Server&"
            "TrustServerCertificate=yes"
        )
        engine = create_engine(connection_string)
        logger.debug("Connexion à la base de données établie")
        return engine
    except Exception as e:
        logger.error(f"Erreur de connexion à la base de données: {str(e)}")
        raise

def get_analysis_data():
    """Récupérer et traiter les données d'analyse depuis la base de données"""
    try:
        engine = connect_to_database()
        
        # Requête SQL pour obtenir les données
        query = """
        SELECT 
            pc.Ville,
            tj.Temperature,
            p.PM25,
            p.AQI,
            ra.valeur,
            pb.valeur_reference,
            a.date_analyse,
            DATEDIFF(YEAR, p2.DateOfBirth, '2024-01-01') as age,
            p2.Gender
        FROM patients_cities pc
        JOIN Analyse a ON pc.id_patient = a.PatientID
        JOIN ResultatAnalyse ra ON a.Id = ra.analyse_id
        JOIN ParametreBiologique pb ON ra.parametre_id = pb.id
        JOIN TemperaturesJournalieres tj ON pc.Ville = tj.Ville 
            AND CONVERT(date, a.date_analyse) = tj.DateMesure
        LEFT JOIN PollutionData p ON pc.Ville = p.Ville 
            AND CONVERT(date, a.date_analyse) = p.DateMesure
        JOIN Patients p2 ON pc.id_patient = p2.PatientID
        """
        
        df = pd.read_sql(query, engine)
        logger.debug("Données récupérées de la base de données")
        
        # Calculer le taux de réussite
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
        
        # Calculer les statistiques par ville
        city_stats = df.groupby('Ville').agg({
            'treatment_success': 'mean',
            'Temperature': 'mean',
            'AQI': 'mean',
            'PM25': 'mean'
        }).round(2)
        
        # Calculer les corrélations
        correlations = df[['treatment_success', 'Temperature', 'AQI', 'PM25']].corr()
        
        return {
            'data': df,
            'city_stats': city_stats,
            'correlations': correlations
        }
    except Exception as e:
        logger.error(f"Erreur dans get_analysis_data: {str(e)}")
        raise

def create_plots(df):
    """Créer les visualisations pour le dashboard"""
    try:
        plots = {}
        
        # Style des graphiques
        plt.style.use('seaborn-v0_8')
        
        # Graphique de corrélation
        plt.figure(figsize=(10, 6))
        sns.heatmap(df[['treatment_success', 'Temperature', 'AQI', 'PM25']].corr(), 
                    annot=True, cmap='coolwarm', center=0)
        plt.title('Corrélations entre les Variables')
        
        # Convertir en base64
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plots['correlation'] = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        # Graphique de température vs succès
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df, x='Temperature', y='treatment_success')
        plt.title('Relation entre Température et Succès du Traitement')
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plots['temperature'] = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return plots
    except Exception as e:
        logger.error(f"Erreur dans create_plots: {str(e)}")
        raise

@app.route('/')
def index():
    """Route principale qui affiche la page d'accueil avec les données d'analyse"""
    try:
        data = get_analysis_data()
        return render_template('index.html', data=data)
    except Exception as e:
        logger.error(f"Erreur dans la route index: {str(e)}")
        return f"Une erreur est survenue: {str(e)}", 500

@app.route('/api/data')
def get_data():
    """API endpoint pour obtenir les données d'analyse"""
    try:
        return jsonify(get_analysis_data())
    except Exception as e:
        logger.error(f"Erreur dans la route api/data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/pdf_reports/<path:filename>')
def serve_pdf(filename):
    """Servir les fichiers PDF"""
    try:
        return send_from_directory('pdf_reports', filename)
    except Exception as e:
        logger.error(f"Erreur dans la route pdf_reports: {str(e)}")
        return f"Fichier non trouvé: {filename}", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8085) 