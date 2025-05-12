import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import random
from datetime import date, timedelta
from sqlalchemy import create_engine, text
import logging
from typing import Dict, Tuple, List, Set, Optional
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import gc

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ParametreBiologique:
    id: int
    nom: str
    unite: str
    valeur_reference: str
    min_normal: float
    max_normal: float

class ResultatAnalyseGenerator:
    def __init__(self, batch_size: int = 1000, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.engine = self._create_engine()
        self.parametres = self._load_parametres()
        self.resultats_existants = self._load_resultats_existants()
        
    def _create_engine(self) -> create_engine:
        """Crée et retourne la connexion à la base de données."""
        try:
            load_dotenv(override=True)
            required_env_vars = ['DB_USERNAME', 'DB_PASSWORD', 'DB_SERVER', 'DB_NAME']
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            
            if missing_vars:
                raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
            
            connection_string = (
                f"mssql+pyodbc://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
                f"{os.getenv('DB_SERVER')}/{os.getenv('DB_NAME')}"
                "?driver=ODBC+Driver+18+for+SQL+Server"
                "&Encrypt=no&TrustServerCertificate=yes"
                "&MultipleActiveResultSets=true"
            )
            return create_engine(connection_string, fast_executemany=True, pool_size=5, max_overflow=10)
        except Exception as e:
            logger.error(f"Erreur lors de la création de la connexion à la base de données: {e}")
            raise

    def _load_parametres(self) -> Dict[int, ParametreBiologique]:
        """Charge les paramètres biologiques depuis la base de données."""
        try:
            df = pd.read_sql("SELECT id, nom, unite, valeur_reference FROM ParametreBiologique", self.engine)
            parametres = {}
            
            # Définir les plages de valeurs normales pour chaque paramètre
            ranges = {
                1: (4.0, 10.0),    # Globules blancs
                2: (40.0, 75.0),   # Neutrophiles
                3: (20.0, 45.0),   # Lymphocytes
                4: (0.0, 5.0),     # CRP
                5: (0.0, 20.0),    # VS
                6: (150000, 400000), # Plaquettes
                7: (2.5, 7.5),     # Urée
                8: (60.0, 110.0),  # Créatinine
                9: (10.0, 45.0),   # ALAT
                10: (10.0, 45.0)   # ASAT
            }
            
            for _, row in df.iterrows():
                min_val, max_val = ranges.get(row['id'], (0.0, 100.0))
                parametres[row['id']] = ParametreBiologique(
                    id=row['id'],
                    nom=row['nom'],
                    unite=row['unite'],
                    valeur_reference=row['valeur_reference'],
                    min_normal=min_val,
                    max_normal=max_val
                )
            
            return parametres
        except Exception as e:
            logger.error(f"Erreur lors du chargement des paramètres: {e}")
            raise

    def _load_resultats_existants(self) -> Set[Tuple[int, int]]:
        """Charge les résultats existants depuis la base de données."""
        try:
            df = pd.read_sql("SELECT analyse_id, parametre_id FROM ResultatAnalyse", self.engine)
            return set(zip(df['analyse_id'], df['parametre_id']))
        except Exception as e:
            logger.error(f"Erreur lors du chargement des résultats existants: {e}")
            raise

    def _is_period_hivernale(self, date_analyse: date) -> bool:
        """Détermine si une date est en période hivernale."""
        return date_analyse.month in [1, 2, 3, 11, 12]

    def _get_valeur_anormale(self, parametre_id: int, is_hiver: bool) -> Tuple[float, str]:
        """Génère une valeur anormale pour un paramètre donné."""
        param = self.parametres[parametre_id]
        
        if is_hiver:
            # En hiver, on génère des valeurs plus élevées
            if parametre_id in [1, 4, 5]:  # Globules blancs, CRP, VS
                valeur = random.uniform(param.max_normal * 1.2, param.max_normal * 2.0)
                return round(valeur, 1), "élevé"
            elif parametre_id in [3]:  # Lymphocytes
                valeur = random.uniform(param.min_normal * 0.5, param.min_normal * 0.9)
                return round(valeur, 1), "diminué"
        else:
            # Hors hiver, on génère des valeurs légèrement anormales
            if random.random() < 0.3:  # 30% de chance d'avoir une valeur anormale
                if random.random() < 0.5:
                    valeur = random.uniform(param.max_normal * 1.1, param.max_normal * 1.5)
                    return round(valeur, 1), "légèrement élevé"
                else:
                    valeur = random.uniform(param.min_normal * 0.7, param.min_normal * 0.9)
                    return round(valeur, 1), "légèrement diminué"
        
        # Valeur normale
        valeur = random.uniform(param.min_normal, param.max_normal)
        return round(valeur, 1), "normal"

    def _generer_valeurs_analyses(self, commentaires: str, date_analyse: date) -> Tuple[Dict[int, float], Dict[int, str]]:
        """Génère des valeurs et interprétations pour les analyses."""
        is_hiver = self._is_period_hivernale(date_analyse)
        has_symptoms = "Symptômes grippaux" in commentaires
        
        valeurs = {}
        interpretations = {}
        
        for parametre_id in range(1, 11):
            if has_symptoms and is_hiver:
                valeur, interpretation = self._get_valeur_anormale(parametre_id, True)
            else:
                valeur, interpretation = self._get_valeur_anormale(parametre_id, False)
            
            valeurs[parametre_id] = valeur
            interpretations[parametre_id] = interpretation
        
        return valeurs, interpretations

    def _process_batch(self, batch: List[Dict]) -> None:
        """Traite un lot de résultats pour l'insertion."""
        try:
            insert_sql = text("""
                INSERT INTO ResultatAnalyse (analyse_id, parametre_id, valeur, interpretation)
                VALUES (:analyse_id, :parametre_id, :valeur, :interpretation)
            """)
            
            with self.engine.begin() as conn:
                conn.execute(insert_sql, batch)
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion du lot: {e}")
            raise

    def _chunked(self, items: List[Dict]) -> List[List[Dict]]:
        """Divise une liste en lots de taille batch_size."""
        return [items[i:i + self.batch_size] for i in range(0, len(items), self.batch_size)]

    def generate_and_insert_resultats(self):
        """Génère et insère les résultats d'analyses."""
        try:
            start_time = time.time()
            
            # Charger les analyses
            logger.info("Chargement des analyses...")
            df_analyses = pd.read_sql("""
                SELECT a.id as analyse_id, a.date_analyse, a.commentaires 
                FROM Analyse a 
                WHERE a.type_analyse = 'Analyse grippe saisonnière'
            """, self.engine)
            
            # Générer les résultats
            logger.info("Génération des résultats...")
            resultats = []
            for _, row in df_analyses.iterrows():
                valeurs, interpretations = self._generer_valeurs_analyses(
                    row['commentaires'], 
                    row['date_analyse']
                )
                
                for parametre_id in range(1, 11):
                    if (row['analyse_id'], parametre_id) not in self.resultats_existants:
                        resultats.append({
                            "analyse_id": row['analyse_id'],
                            "parametre_id": parametre_id,
                            "valeur": valeurs[parametre_id],
                            "interpretation": interpretations[parametre_id]
                        })
            
            # Nettoyage de la mémoire
            del df_analyses
            gc.collect()
            
            # Insertion des résultats
            if resultats:
                logger.info(f"Insertion de {len(resultats)} résultats...")
                
                # Traitement parallèle des lots
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    batches = list(self._chunked(resultats))
                    executor.map(self._process_batch, batches)
                
                execution_time = time.time() - start_time
                logger.info(f"✅ {len(resultats)} résultats insérés en {execution_time:.2f} secondes")
            else:
                logger.info("ℹ️ Aucun nouveau résultat à insérer")
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération/insertion des résultats: {e}")
            raise
        finally:
            # Nettoyage final
            gc.collect()

def main():
    try:
        generator = ResultatAnalyseGenerator()
        generator.generate_and_insert_resultats()
    except Exception as e:
        logger.error(f"Erreur dans l'exécution du script: {e}")
        raise

if __name__ == "__main__":
    main()