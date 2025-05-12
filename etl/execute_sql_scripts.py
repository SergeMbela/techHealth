import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sql_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SQLScriptExecutor:
    def __init__(self):
        self.engine = self._create_engine()
        self.scripts_dir = Path(__file__).parent / 'sources_sql_scripts'
        
        # Ordre d'exécution des scripts
        self.script_order = [
            'create_villes.sql',
            'contrainte_unicite_ville.sql',
            'create_patients.sql',
            'create_temperature_daily.sql',
            'create_prises_sang.sql',
            'create_vaccinations_grippe.sql',
            'analyse.sql'
        ]

    def _create_engine(self):
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
            return create_engine(connection_string)
        except Exception as e:
            logger.error(f"Erreur lors de la création de la connexion à la base de données: {e}")
            raise

    def _read_sql_file(self, file_path: Path) -> str:
        """Lit le contenu d'un fichier SQL."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier {file_path}: {e}")
            raise

    def _execute_sql_script(self, script_content: str, script_name: str):
        """Exécute un script SQL."""
        try:
            with self.engine.begin() as conn:
                # Diviser le script en commandes individuelles
                commands = script_content.split(';')
                for command in commands:
                    command = command.strip()
                    if command:  # Ignorer les lignes vides
                        conn.execute(text(command))
            logger.info(f"✅ Script {script_name} exécuté avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'exécution du script {script_name}: {e}")
            raise

    def execute_all_scripts(self):
        """Exécute tous les scripts SQL dans l'ordre spécifié."""
        start_time = time.time()
        logger.info("Début de l'exécution des scripts SQL")
        
        try:
            for script_name in self.script_order:
                script_path = self.scripts_dir / script_name
                if not script_path.exists():
                    logger.error(f"❌ Script non trouvé: {script_name}")
                    continue
                
                logger.info(f"Exécution du script: {script_name}")
                script_content = self._read_sql_file(script_path)
                self._execute_sql_script(script_content, script_name)
                
            execution_time = time.time() - start_time
            logger.info(f"✅ Tous les scripts ont été exécutés avec succès en {execution_time:.2f} secondes")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'exécution des scripts: {e}")
            raise

def main():
    try:
        executor = SQLScriptExecutor()
        executor.execute_all_scripts()
    except Exception as e:
        logger.error(f"Erreur dans l'exécution du script: {e}")
        raise

if __name__ == "__main__":
    main() 