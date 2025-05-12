import os
import sys
import yaml
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any
import docker
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

class MigrationExecutor:
    def __init__(self, config_path: str = "migration.yml"):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.docker_client = docker.from_env()
        self.engine = None
        self.logger = logging.getLogger(__name__)

    def _load_config(self, config_path: str) -> Dict:
        """Charge la configuration depuis le fichier YAML."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            sys.exit(1)

    def _setup_logging(self):
        """Configure le système de logging."""
        log_config = self.config['logging']
        for log_file in log_config['files']:
            os.makedirs(os.path.dirname(log_file['path']), exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format=log_config['format'],
            handlers=[
                logging.FileHandler(log_config['files'][0]['path']),
                logging.StreamHandler()
            ]
        )

    def _check_environment(self):
        """Vérifie que tous les outils requis sont installés."""
        self.logger.info("Vérification de l'environnement...")
        required_tools = self.config['environment']['required_tools']
        
        for tool in required_tools:
            try:
                if tool['name'] == 'Docker Desktop':
                    self.docker_client.ping()
                elif tool['name'] == 'WSL':
                    subprocess.run(['wsl', '--status'], check=True, capture_output=True)
                # Ajouter d'autres vérifications selon les besoins
                self.logger.info(f"✅ {tool['name']} est installé")
            except Exception as e:
                self.logger.error(f"❌ {tool['name']} n'est pas installé ou n'est pas accessible: {e}")
                raise

    def _setup_database(self):
        """Configure et démarre la base de données SQL Server dans Docker."""
        self.logger.info("Configuration de la base de données...")
        db_config = self.config['database']
        
        try:
            # Vérifier si le conteneur existe déjà
            containers = self.docker_client.containers.list(
                filters={'name': 'sql_server_container'}
            )
            
            if not containers:
                # Créer et démarrer le conteneur
                self.docker_client.containers.run(
                    db_config['docker']['image'],
                    environment=db_config['docker']['environment'],
                    ports={'1433/tcp': db_config['docker']['port']},
                    name='sql_server_container',
                    detach=True
                )
                self.logger.info("✅ Conteneur SQL Server démarré")
            else:
                self.logger.info("ℹ️ Conteneur SQL Server déjà en cours d'exécution")
            
            # Attendre que SQL Server soit prêt
            time.sleep(30)  # Attendre que SQL Server démarre
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la configuration de la base de données: {e}")
            raise

    def _create_database_connection(self):
        """Crée la connexion à la base de données."""
        try:
            load_dotenv(override=True)
            connection_string = (
                f"mssql+pyodbc://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
                f"{os.getenv('DB_SERVER')}/{os.getenv('DB_NAME')}"
                "?driver=ODBC+Driver+18+for+SQL+Server"
                "&Encrypt=no&TrustServerCertificate=yes"
                "&MultipleActiveResultSets=true"
            )
            self.engine = create_engine(connection_string)
            self.logger.info("✅ Connexion à la base de données établie")
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la connexion à la base de données: {e}")
            raise

    def _execute_sql_scripts(self):
        """Exécute les scripts SQL dans l'ordre spécifié."""
        self.logger.info("Exécution des scripts SQL...")
        scripts = self.config['migration_steps'][1]['scripts']  # Étape de configuration de la base de données
        
        for script_name in scripts:
            try:
                script_path = Path('etl/sources_sql_scripts') / script_name
                with open(script_path, 'r', encoding='utf-8') as file:
                    script_content = file.read()
                
                with self.engine.begin() as conn:
                    conn.execute(text(script_content))
                self.logger.info(f"✅ Script {script_name} exécuté avec succès")
            except Exception as e:
                self.logger.error(f"❌ Erreur lors de l'exécution du script {script_name}: {e}")
                raise

    def _execute_python_scripts(self):
        """Exécute les scripts Python d'importation de données."""
        self.logger.info("Exécution des scripts Python...")
        scripts = self.config['migration_steps'][2]['scripts']  # Étape d'importation des données
        
        for script_name in scripts:
            try:
                script_path = Path('etl') / script_name
                subprocess.run([sys.executable, str(script_path)], check=True)
                self.logger.info(f"✅ Script {script_name} exécuté avec succès")
            except Exception as e:
                self.logger.error(f"❌ Erreur lors de l'exécution du script {script_name}: {e}")
                raise

    def _validate_data(self):
        """Valide l'intégrité des données importées."""
        self.logger.info("Validation des données...")
        tables = self.config['backup']['tables']
        
        for table in tables:
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    self.logger.info(f"✅ Table {table}: {count} enregistrements")
            except Exception as e:
                self.logger.error(f"❌ Erreur lors de la validation de la table {table}: {e}")
                raise

    def _create_backup(self):
        """Crée une sauvegarde de la base de données."""
        if not self.config['backup']['enabled']:
            return
            
        self.logger.info("Création de la sauvegarde...")
        backup_dir = Path(self.config['backup']['location'])
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.bak"
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"""
                    BACKUP DATABASE [{os.getenv('DB_NAME')}]
                    TO DISK = '{backup_file}'
                    WITH FORMAT, INIT, NAME = 'Full Database Backup'
                """))
            self.logger.info(f"✅ Sauvegarde créée: {backup_file}")
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la création de la sauvegarde: {e}")
            raise

    def execute_migration(self):
        """Exécute la migration complète."""
        try:
            start_time = time.time()
            self.logger.info("Début de la migration...")
            
            # Exécution des étapes dans l'ordre
            self._check_environment()
            self._setup_database()
            self._create_database_connection()
            self._execute_sql_scripts()
            self._execute_python_scripts()
            self._validate_data()
            self._create_backup()
            
            execution_time = time.time() - start_time
            self.logger.info(f"✅ Migration terminée avec succès en {execution_time:.2f} secondes")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la migration: {e}")
            raise
        finally:
            # Nettoyage
            if self.engine:
                self.engine.dispose()

def main():
    try:
        executor = MigrationExecutor()
        executor.execute_migration()
    except Exception as e:
        print(f"Erreur lors de la migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 