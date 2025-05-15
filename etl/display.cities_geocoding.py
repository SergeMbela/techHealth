import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster, Fullscreen, MeasureControl
import pyodbc
from dotenv import load_dotenv
import os
import branca.colormap as cm
import numpy as np

# Load environment variables
load_dotenv()

def connect_to_database():
    """Connect to SQL Server database using environment variables"""
    try:
        connection = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.getenv('DB_HOST', 'localhost,1433')};"
            f"DATABASE={os.getenv('DB_NAME', 'health')};"
            f"UID={os.getenv('DB_USER', 'sa')};"
            f"PWD={os.getenv('DB_PASSWORD', 'Mouscron2025?')};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )
        return connection
    except pyodbc.Error as err:
        print(f"Error connecting to database: {err}")
        return None

def get_cities_data():
    """Execute the SQL query and return results as a DataFrame"""
    query = """
    select COUNT(a.id_patient) as patient_count, a.ville, b.Latitude, b.Longitude
    from patients_cities a, villes b
    WHERE b.Ville = a.Ville
    group by a.ville, b.Latitude, b.Longitude
    order by a.ville
    """
    
    connection = connect_to_database()
    if connection is None:
        return None
        
    try:
        # Convert to DataFrame using cursor
        cursor = connection.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        df = pd.DataFrame.from_records(data, columns=columns)
        
        # Convert numeric columns to appropriate types
        df['patient_count'] = pd.to_numeric(df['patient_count'])
        df['Latitude'] = pd.to_numeric(df['Latitude'])
        df['Longitude'] = pd.to_numeric(df['Longitude'])
        
        return df
    except Exception as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        connection.close()

def create_map(df):
    """Create an interactive map with the cities data"""
    if df is None or df.empty:
        print("No data to display")
        return
    
    # Calculate statistics
    total_patients = df['patient_count'].sum()
    max_patients = df['patient_count'].max()
    min_patients = df['patient_count'].min()
    
    # Calculate the center of the map based on the data
    center_lat = df['Latitude'].mean()
    center_lon = df['Longitude'].mean()
    
    # Create a map centered on the mean coordinates
    m = folium.Map(location=[center_lat, center_lon], 
                  zoom_start=6,
                  tiles='CartoDB positron')
    
    # Add additional tile layers
    folium.TileLayer('OpenStreetMap').add_to(m)
    folium.TileLayer('Stamen Terrain').add_to(m)
    
    # Create a color scale for the markers
    colormap = cm.LinearColormap(
        colors=['green', 'yellow', 'red'],
        vmin=float(min_patients),
        vmax=float(max_patients),
        caption='Number of Patients'
    )
    colormap.add_to(m)
    
    # Create a marker cluster
    marker_cluster = MarkerCluster().add_to(m)
    
    # Add a heatmap layer
    heat_data = [[float(row['Latitude']), float(row['Longitude']), float(row['patient_count'])] 
                 for index, row in df.iterrows()]
    HeatMap(heat_data, 
            min_opacity=0.3,
            radius=25,
            blur=15,
            gradient={"0.4": 'blue', "0.65": 'lime', "1": 'red'}).add_to(m)
    
    # Add markers for each city
    for index, row in df.iterrows():
        # Calculate marker color based on patient count
        color = colormap(float(row['patient_count']))
        
        # Create popup content with better formatting
        popup_content = f"""
        <div style='width: 200px'>
            <h4 style='margin-bottom: 10px; color: #2c3e50;'>{row['ville']}</h4>
            <table style='width: 100%; border-collapse: collapse;'>
                <tr>
                    <td style='padding: 5px;'><b>Patients:</b></td>
                    <td style='padding: 5px;'>{int(row['patient_count']):,}</td>
                </tr>
                <tr>
                    <td style='padding: 5px;'><b>Latitude:</b></td>
                    <td style='padding: 5px;'>{float(row['Latitude']):.4f}</td>
                </tr>
                <tr>
                    <td style='padding: 5px;'><b>Longitude:</b></td>
                    <td style='padding: 5px;'>{float(row['Longitude']):.4f}</td>
                </tr>
                <tr>
                    <td style='padding: 5px;'><b>% of Total:</b></td>
                    <td style='padding: 5px;'>{(float(row['patient_count'])/total_patients*100):.1f}%</td>
                </tr>
            </table>
        </div>
        """
        
        # Calculate marker size (logarithmic scale)
        size = 5 + 20 * (np.log(float(row['patient_count'])) / np.log(float(max_patients)))
        
        # Add marker
        folium.CircleMarker(
            location=[float(row['Latitude']), float(row['Longitude'])],
            radius=size,
            popup=folium.Popup(popup_content, max_width=300),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            tooltip=f"{row['ville']}: {int(row['patient_count']):,} patients"
        ).add_to(marker_cluster)
    
    # Add additional controls
    folium.LayerControl().add_to(m)
    Fullscreen().add_to(m)
    MeasureControl().add_to(m)
    
    # Add a title
    title_html = f'''
        <h3 align="center" style="font-size:16px">
            <b>Patient Distribution Map</b><br>
            Total Patients: {int(total_patients):,} | Cities: {len(df):,}
        </h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save the map
    output_file = 'cities_map.html'
    m.save(output_file)
    print(f"Map has been saved to {output_file}")
    
    return m

def print_statistics(df):
    """Print detailed statistics about the data"""
    if df is None or df.empty:
        return
        
    total_patients = df['patient_count'].sum()
    total_cities = len(df)
    
    print("\n=== Detailed Statistics ===")
    print(f"Total number of cities: {total_cities:,}")
    print(f"Total number of patients: {total_patients:,}")
    print(f"Average patients per city: {df['patient_count'].mean():,.2f}")
    print(f"Median patients per city: {df['patient_count'].median():,.2f}")
    print(f"Standard deviation: {df['patient_count'].std():,.2f}")
    
    # Top 5 cities
    print("\nTop 5 Cities by Patient Count:")
    top_5 = df.nlargest(5, 'patient_count')
    for _, row in top_5.iterrows():
        percentage = (row['patient_count'] / total_patients) * 100
        print(f"- {row['ville']}: {row['patient_count']:,} patients ({percentage:.1f}%)")
    
    # Distribution statistics
    print("\nPatient Distribution:")
    print(f"Minimum: {df['patient_count'].min():,}")
    print(f"25th percentile: {df['patient_count'].quantile(0.25):,.0f}")
    print(f"50th percentile: {df['patient_count'].quantile(0.50):,.0f}")
    print(f"75th percentile: {df['patient_count'].quantile(0.75):,.0f}")
    print(f"Maximum: {df['patient_count'].max():,}")

def main():
    # Get the data
    df = get_cities_data()
    
    if df is not None:
        # Create and save the map
        create_map(df)
        
        # Print detailed statistics
        print_statistics(df)
    else:
        print("Failed to retrieve data from database")

if __name__ == "__main__":
    main()