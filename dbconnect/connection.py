import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus

class SQLServerConnector:
    def __init__(self, env_file: str = ".env"):
        # Load environment variables
        load_dotenv(env_file, override=True)
        
        # Get database connection parameters from environment
        self.server = os.getenv("DB_SERVER")
        self.database = os.getenv("DB_NAME")
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.driver = os.getenv("ODBC_DRIVER", "{ODBC Driver 18 for SQL Server}")
        self.port = os.getenv("DB_PORT", "1433")
        self.trusted_connection = os.getenv("DB_TRUSTED_CONNECTION", "no").lower() == "yes"
        self.encrypt = os.getenv("DB_ENCRYPT", "no").lower() == "yes"
        self.trust_server_certificate = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes").lower() == "yes"

        # Validate required parameters
        required_params = {
            "DB_SERVER": self.server,
            "DB_NAME": self.database,
            "DB_USERNAME": self.username,
            "DB_PASSWORD": self.password
        }
        
        missing_params = [param for param, value in required_params.items() if not value]
        if missing_params:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_params)}")

    def get_connection_string(self) -> str:
        """Generate the ODBC connection string."""
        params = [
            f"DRIVER={self.driver}",
            f"SERVER={self.server}",
            f"DATABASE={self.database}",
            f"Encrypt={'yes' if self.encrypt else 'no'}",
            f"TrustServerCertificate={'yes' if self.trust_server_certificate else 'no'}"
        ]

        if self.trusted_connection:
            params.append("Trusted_Connection=yes")
        else:
            params.extend([
                f"UID={self.username}",
                f"PWD={self.password}"
            ])

        if self.port != "1433":  # Only add port if it's not the default
            params.append(f"PORT={self.port}")

        return ";".join(params)

    def get_sqlalchemy_engine(self):
        """Create and return a SQLAlchemy engine instance."""
        try:
            connection_uri = (
                f"mssql+pyodbc:///?odbc_connect={quote_plus(self.get_connection_string())}"
            )
            return create_engine(
                connection_uri,
                pool_pre_ping=True,  # Enable connection health checks
                pool_recycle=3600,   # Recycle connections after 1 hour
                echo=False           # Set to True for SQL query logging
            )
        except Exception as e:
            raise Exception(f"Failed to create SQLAlchemy engine: {str(e)}")

    def test_connection(self):
        """Test the database connection."""
        try:
            engine = self.get_sqlalchemy_engine()
            with engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception as e:
            raise Exception(f"Database connection test failed: {str(e)}")

