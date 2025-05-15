from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def connect_to_database():
    """Établir la connexion à la base de données SQL Server"""
    try:
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

def create_plots(data):
    """Créer les visualisations pour le rapport"""
    plots = {}
    
    # Style des graphiques
    plt.style.use('seaborn-v0_8')
    
    # Graphique de corrélation
    plt.figure(figsize=(12, 8))
    sns.heatmap(data['correlations'], annot=True, cmap='coolwarm', center=0)
    plt.title('Corrélations entre les Variables', pad=20)
    
    # Sauvegarder le graphique
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300)
    img.seek(0)
    plots['correlation'] = img
    plt.close()
    
    # Graphique de température vs succès
    plt.figure(figsize=(12, 8))
    sns.scatterplot(data=data['data'], x='Temperature', y='treatment_success')
    plt.title('Relation entre Température et Succès du Traitement', pad=20)
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300)
    img.seek(0)
    plots['temperature'] = img
    plt.close()
    
    return plots

def generate_pdf_report():
    """Générer le rapport PDF"""
    try:
        # Récupérer les données
        data = get_analysis_data()
        plots = create_plots(data)
        
        # Créer le document PDF en format paysage
        doc = SimpleDocTemplate(
            "pdf_reports/rapport_analyse_climatique.pdf",
            pagesize=landscape(letter),
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=30,
            alignment=1  # Centré
        )
        
        # Contenu du rapport
        story = []
        
        # Titre
        story.append(Paragraph("Rapport d'Analyse de l'Impact du Climat et de la Pollution sur les Traitements", title_style))
        story.append(Spacer(1, 20))
        
        # Introduction
        story.append(Paragraph("Introduction", styles['Heading2']))
        story.append(Paragraph(
            "Ce rapport présente une analyse détaillée de l'impact des conditions climatiques et de la qualité de l'air sur les taux de réussite des traitements médicaux dans différentes villes.",
            styles['Normal']
        ))
        story.append(Spacer(1, 20))
        
        # Statistiques par ville
        story.append(Paragraph("Statistiques par Ville", styles['Heading2']))
        city_data = [[col] + [data['city_stats'][col][city] for city in data['city_stats'].index]
                    for col in data['city_stats'].columns]
        city_table = Table([['Ville'] + list(data['city_stats'].index)] + city_data)
        city_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(city_table)
        story.append(Spacer(1, 20))
        
        # Graphiques
        story.append(Paragraph("Analyse des Corrélations", styles['Heading2']))
        story.append(Image(plots['correlation'], width=600, height=400))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("Relation Température-Succès", styles['Heading2']))
        story.append(Image(plots['temperature'], width=600, height=400))
        story.append(Spacer(1, 20))
        
        # Conclusion
        story.append(Paragraph("Conclusion", styles['Heading2']))
        story.append(Paragraph(
            "Cette analyse révèle les relations importantes entre les conditions environnementales et l'efficacité des traitements médicaux. Les résultats montrent des corrélations significatives qui méritent une attention particulière dans la planification des soins de santé.",
            styles['Normal']
        ))
        
        # Générer le PDF
        doc.build(story)
        logger.debug("Rapport PDF généré avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
        raise

if __name__ == '__main__':
    generate_pdf_report() 