import os
from dotenv import load_dotenv


class SQLServerConnector:
    def __init__(self, env_file: str = ".env"):
        load_dotenv(env_file)
        self.server = os.getenv("DB_SERVER")
        self.database = os.getenv("DB_NAME")
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.driver = os.getenv("ODBC_DRIVER", "{ODBC Driver 18 for SQL Server}")

    def get_connection_string(self) -> str:
        return (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"Encrypt=no;TrustServerCertificate=yes;"
        )
