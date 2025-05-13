import os
import random
import sys
import time
import pandas as pd
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv
from sqlalchemy import text, exc
import logging
from typing import List, Tuple, Set
from contextlib import contextmanager


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv(override=True)
sys.path.append(os.getenv("DBCONNECT_PARENT"))
from dbconnect.connection import SQLServerConnector

@contextmanager
def get_db_connection():
    """Context manager pour la connexion à la base de données."""
    conn = SQLServerConnector()
    engine = conn.get_sqlalchemy_engine()
    try:
        yield engine
    finally:
        engine.dispose()

def get_existing_entries(engine) -> Set[Tuple[int, str]]:
    """Récupère les entrées existantes de la table patients_cities."""
    try:
        with engine.connect() as connection:
            existing_entries = pd.read_sql("""
                SELECT id_patient, Ville 
                FROM patients_cities
            """, connection)
            return set(zip(existing_entries['id_patient'], existing_entries['Ville']))
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des entrées existantes: {e}")
        raise

def check_for_duplicates(engine) -> pd.DataFrame:
    """Vérifie la présence de doublons dans la table patients_cities."""
    try:
        with engine.connect() as connection:
            return pd.read_sql("""
                SELECT id_patient, Ville, COUNT(*) as count
                FROM patients_cities
                GROUP BY id_patient, Ville
                HAVING COUNT(*) > 1
            """, connection)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des doublons: {e}")
        raise

def insert_batch(connection, batch: List[Tuple[int, str]], insert_query: text) -> None:
    """Insère un lot de données avec gestion des erreurs."""
    try:
        connection.execute(insert_query, [
            {"id_patient": id_patient, "Ville": ville}
            for id_patient, ville in batch
        ])
    except exc.IntegrityError as e:
        logger.error(f"Erreur d'intégrité lors de l'insertion du lot: {e}")
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'insertion du lot: {e}")
        raise

def main():
    try:
        with get_db_connection() as engine:
            # Étape 1 : Récupérer les villes et leurs populations
            with engine.connect() as connection:
                villes_df = pd.read_sql("SELECT Ville, Population FROM Villes", connection)

            # Analyse des données des villes
            logger.info("\nStatistiques des populations par ville:")
            logger.info(villes_df['Population'].describe())

            # Étape 2 : Tirage pondéré de 100 000 villes
            villes_choisies = random.choices(
                villes_df["Ville"].tolist(),
                weights=villes_df["Population"].tolist(),
                k=100_000
            )

            # Créer un DataFrame pour les villes choisies
            villes_choisies_df = pd.DataFrame({
                'id_patient': range(1, len(villes_choisies) + 1),
                'Ville': villes_choisies
            })

            # Analyse de la distribution
            distribution = villes_choisies_df['Ville'].value_counts()
            logger.info("\nDistribution des patients par ville:")
            logger.info(f"Nombre total de villes utilisées: {len(distribution)}")
            logger.info(f"Villes avec le plus de patients:")
            logger.info(distribution.head())

            # Étape 3 : Vérifier les entrées existantes
            logger.info("\nVérification des entrées existantes...")
            existing_pairs = get_existing_entries(engine)
            
            if existing_pairs:
                logger.info(f"Nombre d'entrées existantes: {len(existing_pairs)}")
                # Filtrer les nouvelles associations pour éviter les doublons
                new_associations = [
                    (id_patient, ville) 
                    for id_patient, ville in zip(villes_choisies_df['id_patient'], villes_choisies_df['Ville'])
                    if (id_patient, ville) not in existing_pairs
                ]
                logger.info(f"Nombre de nouvelles associations à insérer: {len(new_associations)}")
            else:
                logger.info("Aucune entrée existante trouvée.")
                new_associations = list(zip(villes_choisies_df['id_patient'], villes_choisies_df['Ville']))

            # Étape 4 : Insertion en batch avec barre de progression
            if new_associations:
                insert_query = text("""
                    INSERT INTO patients_cities (id_patient, Ville) 
                    VALUES (:id_patient, :Ville)
                """)
                batch_size = 10_000
                start_time = time.time()

                with engine.begin() as connection:
                    for i in tqdm(range(0, len(new_associations), batch_size), desc="Insertion des données"):
                        batch = new_associations[i:i+batch_size]
                        insert_batch(connection, batch, insert_query)

                elapsed = time.time() - start_time
                logger.info(f"\nInsertion terminée en {elapsed:.2f} secondes.")
            else:
                logger.info("\nAucune nouvelle association à insérer.")

            # Vérification finale
            with engine.connect() as connection:
                verification_df = pd.read_sql("""
                    SELECT 
                        COUNT(*) as total_patients, 
                        COUNT(DISTINCT Ville) as total_villes,
                        COUNT(DISTINCT id_patient) as patients_uniques,
                        COUNT(*) - COUNT(DISTINCT id_patient) as doublons_potentiels
                    FROM patients_cities
                """, connection)
                logger.info("\nVérification finale:")
                logger.info(verification_df)
                
                # Vérification des doublons
                duplicates_df = check_for_duplicates(engine)
                
                if not duplicates_df.empty:
                    logger.warning("\n⚠️ ATTENTION: Des doublons ont été détectés:")
                    logger.warning(duplicates_df)
                else:
                    logger.info("\n✅ Aucun doublon détecté dans la table patients_cities.")

    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du script: {e}")
        raise

if __name__ == "__main__":
    main()
