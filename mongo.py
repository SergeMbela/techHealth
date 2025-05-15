#1. Pour ceux qui utilisent docker
#docker run -p 27017:27017 mongodb/mongodb-atlas-local
#mongodb://admin:password@localhost:27017/
#In our case the login is admin et the password is password adapt with your our credentials, vérifier dans le code et remplacer si nécessaire.
 
#2.  Installation des dépendances Python nécessaires :
# pip install pymongo
# pip install pandas
# pip install dnspython  # Pour la résolution DNS (optionnel mais recommandé)

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
import pandas as pd
import time
import socket

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
    # Vérification du port
    if not check_mongodb_port():
        print("Erreur: Le port 27017 n'est pas accessible. Vérifiez que MongoDB est en cours d'exécution dans Docker.")
        print("Commande pour démarrer MongoDB: docker run -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=password mongodb/mongodb-atlas-local")
        return None

    for attempt in range(max_retries):
        try:
            print(f"Tentative de connexion {attempt + 1}/{max_retries}...")
            
            # Connexion à MongoDB avec authentification
            client = MongoClient(
                'mongodb://admin:password@localhost:27017/',
                serverSelectionTimeoutMS=5000,  # 5 secondes timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Vérification de la connexion
            client.admin.command('ping')
            print("Connexion à MongoDB réussie!")
            
            # Vérification de la connexion sans lister les bases de données
            print("Connexion établie avec succès!")
            
            return client
            
        except ConnectionFailure as e:
            print(f"Erreur de connexion (tentative {attempt + 1}): Impossible de se connecter au serveur MongoDB")
            print(f"Détails: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
            else:
                print("Toutes les tentatives de connexion ont échoué.")
                print("Vérifiez que:")
                print("1. Docker est en cours d'exécution")
                print("2. Le conteneur MongoDB est démarré avec les bonnes variables d'environnement")
                print("3. Le port 27017 n'est pas utilisé par un autre processus")
                return None
                
        except ServerSelectionTimeoutError as e:
            print(f"Erreur de timeout (tentative {attempt + 1}): Le serveur MongoDB ne répond pas")
            print(f"Détails: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
            else:
                print("Toutes les tentatives de connexion ont échoué.")
                return None
                
        except OperationFailure as e:
            print(f"Erreur d'authentification (tentative {attempt + 1}): {str(e)}")
            print("Vérifiez que les identifiants sont corrects et que MongoDB est démarré avec l'authentification activée")
            return None
            
        except Exception as e:
            print(f"Erreur inattendue (tentative {attempt + 1}): {str(e)}")
            return None

def insert_data_to_mongodb(client, database_name, collection_name, data):
    """
    Insert data into MongoDB with validation
    """
    if not client:
        print("Erreur: Client MongoDB non connecté")
        return None
        
    try:
        # Sélection de la base de données
        db = client[database_name]
        
        # Sélection de la collection
        collection = db[collection_name]
        
        # Validation des données
        if not data:
            print("Erreur: Aucune donnée à insérer")
            return None
            
        # Insertion des données
        if isinstance(data, pd.DataFrame):
            if data.empty:
                print("Erreur: DataFrame vide")
                return None
            # Conversion du DataFrame en liste de dictionnaires
            data_dict = data.to_dict('records')
            result = collection.insert_many(data_dict)
        else:
            if not isinstance(data, list):
                print("Erreur: Les données doivent être un DataFrame ou une liste")
                return None
            result = collection.insert_many(data)
            
        print(f"{len(result.inserted_ids)} documents insérés avec succès!")
        return result
    except Exception as e:
        print(f"Erreur lors de l'insertion des données: {e}")
        return None

def get_data_from_mongodb(client, database_name, collection_name, query=None):
    """
    Get data from MongoDB with validation
    """
    if not client:
        print("Erreur: Client MongoDB non connecté")
        return None
        
    try:
        # Sélection de la base de données
        db = client[database_name]
        
        # Sélection de la collection
        collection = db[collection_name]
        
        # Récupération des données
        if query is None:
            query = {}
        elif not isinstance(query, dict):
            print("Erreur: La requête doit être un dictionnaire")
            return None
            
        data = list(collection.find(query))
        
        if not data:
            print("Aucun document trouvé")
            return []
            
        print(f"{len(data)} documents récupérés avec succès!")
        return data
    except Exception as e:
        print(f"Erreur lors de la récupération des données: {e}")
        return None

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

def import_csv_to_mongodb(client, database_name, collection_name, csv_file_path):
    """
    Import data from a CSV file into MongoDB collection
    
    Args:
        client: MongoDB client instance
        database_name: Name of the database
        collection_name: Name of the collection
        csv_file_path: Path to the CSV file
    
    Returns:
        bool: True if import was successful, False otherwise
    """
    if not client:
        print("Erreur: Client MongoDB non connecté")
        return False
        
    try:
        # Read CSV file
        df = pd.read_csv(csv_file_path)
        
        if df.empty:
            print("Erreur: Le fichier CSV est vide")
            return False
            
        # Insert data into MongoDB
        result = insert_data_to_mongodb(client, database_name, collection_name, df)
        
        if result:
            print(f"Données importées avec succès depuis {csv_file_path}")
            return True
        return False
        
    except FileNotFoundError:
        print(f"Erreur: Le fichier {csv_file_path} n'existe pas")
        return False
    except pd.errors.EmptyDataError:
        print("Erreur: Le fichier CSV est vide")
        return False
    except Exception as e:
        print(f"Erreur lors de l'importation du CSV: {e}")
        return False

# Exemple d'utilisation
if __name__ == "__main__":
    try:
        # Connect to MongoDB
        client = connect_to_mongodb()
        
        if client:
            # Example 1: Insert simple data
            data = [{"name": "John", "age": 30}]
            insert_data_to_mongodb(client, "test_db", "test_collection", data)
            
            # Example 2: Import from CSV
            # Uncomment and modify the path to your CSV file
            # import_csv_to_mongodb(client, "test_db", "csv_data", "path/to/your/file.csv")
            
            # Get data
            results = get_data_from_mongodb(client, "test_db", "test_collection")
            if results:
                print("Données récupérées:", results)
            
            # Fermeture de la connexion
            close_mongodb_connection(client)
    except Exception as e:
        print(f"Erreur dans le programme principal: {e}")