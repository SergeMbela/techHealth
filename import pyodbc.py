import pyodbc
import os

server = os.environ.get("SERVER")
database = os.environ.get("DATABASE")
username = os.environ.get("PWD")
password = os.environ.get("SQL_PASSWORD")

conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
)
print(f"DataSettings = {conn_str}")
# Get the variable
value = os.environ.get("MY_VARIABLE")


conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=172.25.64.1,1433;'
    'DATABASE=health;'
    'UID=sa;'
    'PWD=Mouscron2025?;'
    'Encrypt=no;TrustServerCertificate=yes;'
)

cursor = conn.cursor()
cursor.execute("SELECT name FROM sys.databases;")
for row in cursor.fetchall():
    print(row)
conn.close()
