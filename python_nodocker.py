#1. Pour ceux qui n'utilisent pas Docker (MongoDB installé localement) :
# - Télécharger et installer MongoDB Community Server depuis : https://www.mongodb.com/try/download/community
# - Démarrer le service MongoDB :
#   - Windows : Le service démarre automatiquement
#   - Linux : sudo systemctl start mongod
#   - Mac : brew services start mongodb-community
# - URI de connexion sans authentification : mongodb://localhost:27017/
# - Pour activer l'authentification :
#   1. Créer un utilisateur admin : 
#      mongosh
#      use admin
#      db.createUser({user: "admin", password: "password", roles: ["root"]})
#   2. Modifier le fichier mongod.conf pour activer l'authentification
#   3. URI avec authentification : mongodb://admin:password@localhost:27017/
 
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

def connect_to_mongodb(max_retries=3, retry_delay=2, use_auth=True):
    """
    Connect to MongoDB with retry mechanism and detailed error handling
    """
    # Vérification du port
    if not check_mongodb_port():
        print("Erreur: Le port 27017 n'est pas accessible. Vérifiez que MongoDB est en cours d'exécution.")
        print("Pour démarrer MongoDB :")
        print("- Windows : Le service démarre automatiquement")
        print("- Linux : sudo systemctl start mongod")
        print("- Mac : brew services start mongodb-community")
        return None

    for attempt in range(max_retries):
        try:
            print(f"Tentative de connexion {attempt + 1}/{max_retries}...")
            
            # Connexion à MongoDB avec ou sans authentification
            if use_auth:
                client = MongoClient(
                    'mongodb://admin:password@localhost:27017/',
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000
                )
            else:
                client = MongoClient(
                    'mongodb://localhost:27017/',
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000
                )
            
            # Vérification de la connexion
            client.admin.command('ping')
            print("Connexion à MongoDB réussie!")
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
                print("1. MongoDB est installé et en cours d'exécution")
                print("2. Le service MongoDB est démarré")
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
            print("Vérifiez que les identifiants sont corrects et que l'authentification est correctement configurée")
            print("Pour désactiver l'authentification, utilisez use_auth=False")
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

# Exemple d'utilisation
if __name__ == "__main__":
    try:
        # Connect to MongoDB (sans authentification)
        client = connect_to_mongodb(use_auth=False)
        
        if client:
            # Insert data
            data = [{"name": "John", "age": 30}]
            insert_data_to_mongodb(client, "test_db", "test_collection", data)
            
            # Get data
            results = get_data_from_mongodb(client, "test_db", "test_collection")
            if results:
                print("Données récupérées:", results)
            
            # Fermeture de la connexion
            close_mongodb_connection(client)
    except Exception as e:
        print(f"Erreur dans le programme principal: {e}")