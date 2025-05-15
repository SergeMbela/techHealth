import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
import os
import numpy as np
from scipy import stats
from datetime import datetime
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

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

def get_climate_treatment_data():
    """Retrieve climate, pollution, and treatment data from the database."""
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
    return df

def is_value_within_reference(value, reference):
    """Check if a value is within the reference range."""
    try:
        value = float(value)
        if '<' in reference:
            threshold = float(reference.split('<')[1].strip())
            return value < threshold
        elif '>' in reference:
            threshold = float(reference.split('>')[1].strip())
            return value > threshold
        else:
            # Handle range format (e.g., "4.0 - 10.0")
            parts = reference.split('-')
            if len(parts) == 2:
                min_val = float(parts[0].strip())
                max_val = float(parts[1].strip())
                return min_val <= value <= max_val
            else:
                # Single value reference
                ref_val = float(reference.strip())
                return abs(value - ref_val) <= 0.1  # Allow small tolerance
    except (ValueError, TypeError):
        return False

def get_season(date):
    """Determine season from date."""
    m = pd.to_datetime(date).month
    if m in [12, 1, 2]:
        return 'Winter'
    elif m in [3, 4, 5]:
        return 'Spring'
    elif m in [6, 7, 8]:
        return 'Summer'
    else:
        return 'Fall'

def analyze_climate_impact():
    """Analyze the impact of climate and pollution on treatment effectiveness."""
    # Get data
    df = get_climate_treatment_data()
    
    # Calculate treatment success
    df['treatment_success'] = df.apply(
        lambda row: is_value_within_reference(row['valeur'], row['valeur_reference']), 
        axis=1
    )
    
    # Add season information
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
    
    # Print detailed correlation results
    print("\nDetailed Correlation Analysis with Treatment Success Rate:")
    print("=" * 80)
    print(f"{'Metric':<15} {'Correlation':<15} {'P-value':<15} {'Significance':<15}")
    print("-" * 80)
    for metric, corr in correlations.items():
        p_val = p_values[metric]
        significance = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
        print(f"{metric:<15} {corr:>15.3f} {p_val:>15.3f} {significance:>15}")
    
    # Seasonal analysis
    print("\nSeasonal Analysis of Treatment Success:")
    print("=" * 80)
    seasonal_stats = df.groupby('season')['treatment_success'].agg(['mean', 'std', 'count'])
    print(seasonal_stats)
    
    # Create enhanced visualizations
    plt.style.use('seaborn-v0_8')
    fig = plt.figure(figsize=(20, 15))
    
    # 1. Temperature vs Treatment Success with trend line
    plt.subplot(2, 2, 1)
    sns.regplot(data=city_stats, x='Temperature', y='treatment_success', 
                scatter_kws={'alpha':0.5}, line_kws={'color': 'red'})
    plt.title('Temperature vs Treatment Success Rate\nwith 95% Confidence Interval')
    plt.xlabel('Average Temperature (°C)')
    plt.ylabel('Treatment Success Rate')
    
    # 2. AQI vs Treatment Success with trend line
    plt.subplot(2, 2, 2)
    sns.regplot(data=city_stats, x='AQI', y='treatment_success',
                scatter_kws={'alpha':0.5}, line_kws={'color': 'red'})
    plt.title('Air Quality Index vs Treatment Success Rate\nwith 95% Confidence Interval')
    plt.xlabel('Average AQI')
    plt.ylabel('Treatment Success Rate')
    
    # 3. Seasonal Treatment Success Box Plot
    plt.subplot(2, 2, 3)
    sns.boxplot(data=df, x='season', y='treatment_success')
    plt.title('Treatment Success Rate by Season')
    plt.xlabel('Season')
    plt.ylabel('Treatment Success Rate')
    
    # 4. Correlation Heatmap
    plt.subplot(2, 2, 4)
    correlation_matrix = city_stats[['treatment_success', 'Temperature', 'AQI', 'PM25', 'PM10', 'NO2', 'O3', 'SO2', 'CO']].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f')
    plt.title('Correlation Heatmap')
    
    plt.tight_layout()
    plt.savefig('climate_pollution_impact_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Create city-specific pollution profiles
    plt.figure(figsize=(15, 8))
    top_cities = city_stats.nlargest(5, 'treatment_success').index
    pollution_metrics = ['PM25', 'PM10', 'NO2', 'O3', 'SO2', 'CO', 'AQI']
    
    # Normalize pollution metrics for comparison
    normalized_data = city_stats[pollution_metrics].apply(lambda x: (x - x.mean()) / x.std())
    normalized_data = normalized_data.loc[top_cities]
    
    # Plot normalized pollution profiles
    normalized_data.plot(kind='bar', width=0.8)
    plt.title('Pollution Profiles of Top 5 Cities by Treatment Success')
    plt.xlabel('City')
    plt.ylabel('Normalized Pollution Level')
    plt.xticks(rotation=45)
    plt.legend(title='Pollution Metric', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('city_pollution_profiles.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # Analyze and visualize the impact
    analyze_climate_impact()

if __name__ == "__main__":
    main() 