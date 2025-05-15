import pyodbc

# Connect to the database
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=localhost,1433;'
    'DATABASE=health;'
    'UID=sa;'
    'PWD=Mouscron2025?;'
    'TrustServerCertificate=yes;'
)

# Read and execute the SQL file
with open('etl/create_pollution_table.sql', 'r') as f:
    sql = f.read()
    
cursor = conn.cursor()
cursor.execute(sql)
conn.commit()

print("SQL script executed successfully") 