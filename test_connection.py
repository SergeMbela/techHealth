from dbconnect.connection import SQLServerConnector
import os
from dotenv import load_dotenv

def test_db_connection():
    try:
        # Load environment variables
        load_dotenv(override=True)
        
        # Print environment variables (without password)
        print("\nDatabase Configuration:")
        print(f"Server: {os.getenv('DB_SERVER')}")
        print(f"Database: {os.getenv('DB_NAME')}")
        print(f"Username: {os.getenv('DB_USERNAME')}")
        print(f"Driver: {os.getenv('ODBC_DRIVER')}")
        
        # Create connector and test connection
        print("\nTesting connection...")
        connector = SQLServerConnector()
        
        if connector.test_connection():
            print("✅ Database connection successful!")
            
            # Test a simple query
            engine = connector.get_sqlalchemy_engine()
            with engine.connect() as connection:
                result = connection.execute("SELECT @@VERSION").scalar()
                print("\nSQL Server Version:")
                print(result)
                
            return True
        else:
            print("❌ Database connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_db_connection() 