from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
import pandas as pd
import time
import socket
# Fichier utile (système et variable d'environnement)
# Fichier utile (système et variable d'environnement)
from dotenv import load_dotenv
import sys
import os
from datetime import datetime
import csv
import numpy as np

from dotenv import load_dotenv
# Charger le fichier .env
# Recharger variables d'envronnements
load_dotenv(override=True)

sys.path.append('../dbconnect')
sys.path.append('../filepath')
def check_mongodb_port():
    """
    Vérifie si le port MongoDB est accessible
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 27017))
    sock.close()
    return result == 0

def connect_to_mongodb(max_retries=3, retry_delay=2):
    """
    Connect to MongoDB with retry mechanism and detailed error handling
    """
    if not check_mongodb_port():
        print("Erreur: Le port 27017 n'est pas accessible. Vérifiez que MongoDB est en cours d'exécution dans Docker.")
        print("Commande pour démarrer MongoDB: docker run -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=password mongodb/mongodb-atlas-local")
        return None

    for attempt in range(max_retries):
        try:
            print(f"Tentative de connexion {attempt + 1}/{max_retries}...")
            
            client = MongoClient(
                'mongodb://admin:password@localhost:27017/',
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            client.admin.command('ping')
            print("Connexion à MongoDB réussie!")
            return client
            
        except (ConnectionFailure, ServerSelectionTimeoutError, OperationFailure) as e:
            print(f"Erreur de connexion (tentative {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                print(f"Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
            else:
                print("Toutes les tentatives de connexion ont échoué.")
                return None

def create_indexes(collection, index_fields):
    """
    Create indexes on specified fields in the collection
    
    Args:
        collection: MongoDB collection object
        index_fields: List of dictionaries containing index specifications
                     Example: [{"field": "patient_id", "unique": True}, 
                             {"field": "admission_date", "unique": False}]
    
    Returns:
        bool: True if indexes were created successfully, False otherwise
    """
    try:
        for index_spec in index_fields:
            field = index_spec["field"]
            unique = index_spec.get("unique", False)
            
            # Create index
            collection.create_index(field, unique=unique)
            print(f"Index créé sur le champ '{field}' (unique: {unique})")
        
        return True
    except Exception as e:
        print(f"Erreur lors de la création des index: {e}")
        return False

def drop_all_indexes(collection):
    """
    Drop all indexes from the collection except the _id index
    
    Args:
        collection: MongoDB collection object
    """
    try:
        collection.drop_indexes()
        print("Tous les index ont été supprimés (sauf _id)")
    except Exception as e:
        print(f"Erreur lors de la suppression des index: {e}")

def create_collection(db, collection_name):
    """
    Create a collection without validation
    
    Args:
        db: MongoDB database object
        collection_name: Name of the collection to create
    
    Returns:
        collection: MongoDB collection object
    """
    try:
        # Drop existing collection if it exists
        if collection_name in db.list_collection_names():
            db[collection_name].drop()
            print(f"Collection existante '{collection_name}' supprimée")
        
        # Create collection without validator
        collection = db.create_collection(collection_name)
        print(f"Collection '{collection_name}' créée")
        
        return collection
        
    except Exception as e:
        print(f"Erreur lors de la création de la collection: {e}")
        return None

def validate_document(doc):
    """
    Validate a document against the schema before insertion
    
    Args:
        doc: Document to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Convert dates to proper format if needed
        for date_field in ['DateOfBirth', 'RegistrationDate', 'LastVisit']:
            if date_field in doc and doc[date_field]:
                if isinstance(doc[date_field], pd.Timestamp):
                    doc[date_field] = doc[date_field].strftime('%Y-%m-%d')
        
        # Convert Gender to standard format
        if 'Gender' in doc:
            gender = str(doc['Gender']).upper()
            if gender in ['MALE', 'M']:
                doc['Gender'] = 'M'
            elif gender in ['FEMALE', 'F']:
                doc['Gender'] = 'F'
            else:
                doc['Gender'] = 'Other'
        
        # Format phone numbers
        for phone_field in ['PhoneNumber', 'EmergencyContactPhone']:
            if phone_field in doc and doc[phone_field]:
                # Remove any non-digit characters except +, -, (, ), and space
                phone = str(doc[phone_field])
                phone = ''.join(c for c in phone if c.isdigit() or c in '+-() ')
                doc[phone_field] = phone
        
        return True, None
        
    except Exception as e:
        return False, str(e)

def import_csv_to_mongodb(client, database_name, collection_name, csv_file_path=None):
    """
    Import data from a CSV file into MongoDB collection
    
    Args:
        client: MongoDB client instance
        database_name: Name of the database
        collection_name: Name of the collection
        csv_file_path: Optional path to the CSV file. If not provided, uses environment variable
    
    Returns:
        bool: True if import was successful, False otherwise
    """
    if not client:
        print("Erreur: Client MongoDB non connecté")
        return False
        
    try:
        # Get CSV file path from environment variable if not provided
        if csv_file_path is None:
            filecsv = os.environ.get("ETL_CSV_FILE")
            if not filecsv:
                print("Erreur: Variable d'environnement ETL_CSV_FILE non définie")
                return False
            csv_file_path = os.path.join(filecsv, 'patients_10000.csv')
        
        print(f"Lecture du fichier CSV: {csv_file_path}")
        
        # Read CSV file with explicit encoding and handle potential encoding issues
        try:
            df = pd.read_csv(csv_file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_file_path, encoding='latin-1')
            except Exception as e:
                print(f"Erreur de lecture du fichier CSV: {e}")
                return False
        
        if df.empty:
            print("Erreur: Le fichier CSV est vide")
            return False
            
        # Clean and validate data
        df = df.replace({pd.NaT: None})  # Replace NaT with None
        df = df.where(pd.notnull(df), None)  # Replace NaN with None
        
        print(f"Nombre de lignes dans le CSV: {len(df)}")
        print("Colonnes trouvées:", df.columns.tolist())
        
        # Convert DataFrame to list of dictionaries and ensure all data is serializable
        data = []
        
        for idx, row in df.iterrows():
            doc = {}
            for col in df.columns:
                value = row[col]
                # Convert numpy types to Python native types
                if pd.isna(value):
                    value = None
                elif isinstance(value, (np.int64, np.int32)):
                    value = int(value)
                elif isinstance(value, (np.float64, np.float32)):
                    value = float(value)
                doc[col] = value
            data.append(doc)
        
        print(f"Nombre de documents préparés pour l'insertion: {len(data)}")
        
        # Get database and create collection
        db = client[database_name]
        collection = create_collection(db, collection_name)
        
        if collection is None:
            print("Erreur: Impossible de créer la collection")
            return False
        
        # Insert data in batches to handle large files
        batch_size = 1000
        total_inserted = 0
        failed_inserts = 0
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            print(f"\nTraitement du batch {i//batch_size + 1} ({len(batch)} documents)")
            
            try:
                # Insert batch with ordered=False to continue on errors
                result = collection.insert_many(batch, ordered=False)
                inserted_count = len(result.inserted_ids)
                total_inserted += inserted_count
                print(f"Batch {i//batch_size + 1}: {inserted_count} documents insérés")
                print(f"Progression totale: {total_inserted}/{len(data)} documents")
                
            except Exception as e:
                print(f"Erreur lors de l'insertion du batch {i//batch_size + 1}: {e}")
                print("Tentative d'insertion document par document...")
                
                # Try inserting documents one by one
                for j, doc in enumerate(batch):
                    try:
                        result = collection.insert_one(doc)
                        total_inserted += 1
                        if (j + 1) % 100 == 0:  # Print progress every 100 documents
                            print(f"Progression du batch: {j + 1}/{len(batch)} documents")
                    except Exception as doc_error:
                        failed_inserts += 1
                        print(f"Échec de l'insertion du document {i + j + 1}: {doc_error}")
                        print(f"Document problématique: {doc}")
        
        print(f"\nRésumé de l'import:")
        print(f"Total des documents insérés: {total_inserted}")
        print(f"Documents en échec: {failed_inserts}")
        print(f"Taux de succès: {(total_inserted/len(data))*100:.2f}%")
        
        if failed_inserts > 0:
            print("\nAttention: Certains documents n'ont pas pu être insérés.")
            print("Vérifiez les messages d'erreur ci-dessus pour plus de détails.")
        
        # Verify final count
        final_count = collection.count_documents({})
        print(f"\nNombre total de documents dans la collection: {final_count}")
        
        return True
        
    except FileNotFoundError:
        print(f"Erreur: Le fichier {csv_file_path} n'existe pas")
        return False
    except pd.errors.EmptyDataError:
        print("Erreur: Le fichier CSV est vide")
        return False
    except Exception as e:
        print(f"Erreur lors de l'importation du CSV: {e}")
        return False

def close_mongodb_connection(client):
    """
    Safely close MongoDB connection
    """
    if client:
        try:
            client.close()
            print("Connexion à MongoDB fermée avec succès")
        except Exception as e:
            print(f"Erreur lors de la fermeture de la connexion: {e}")

if __name__ == "__main__":
    try:
        # Connect to MongoDB
        client = connect_to_mongodb()
        
        if client:
            database_name = "healthcare_db"
            collection_name = "healthcare_data_patients"
            
            # Import CSV file using environment variable path
            success = import_csv_to_mongodb(
                client,
                database_name,
                collection_name
            )
            
            if success:
                print("\nImport des données terminé avec succès")
            
            # Close the connection
            close_mongodb_connection(client)
            
    except Exception as e:
        print(f"Erreur dans le programme principal: {e}")