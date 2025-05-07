import urllib
import os
from dotenv import load_dotenv
server = os.environ.get("SERVER")
database = os.environ.get("DATABASE")
username = os.environ.get("PWD")
password = os.environ.get("SQL_PASSWORD")
odbc = os.environ.get("ODBC_DRIVER")
print(odbc)
from sqlalchemy import create_engine

class DbConfig:
    def __init__(self,
                 server=server,
                 database=database,
                 username=username,
                 password=password,
                 driver='ODBC Driver 18 for SQL Server'):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver

    def get_connection_string(self):
        conn_str = (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
        
        )
        print(conn_str)
        return urllib.parse.quote_plus(conn_str)

    def get_engine(self):
        connection_url = f"mssql+pyodbc:///?odbc_connect={self.get_connection_string()}"
        return create_engine(connection_url)
