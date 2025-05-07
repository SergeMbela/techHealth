# Projet d'Analyse de l'Efficacité d'un Nouveau Traitement contre la Grippe Saisonnière

## Description
Ce projet vise à analyser l'efficacité d'un nouveau traitement contre la grippe saisonnière en étudiant les données démographiques, cliniques et environnementales. L'objectif est de trouver des corrélations entre la réponse au traitement et divers facteurs comme l'âge, le sexe, les allergies, ainsi que les conditions climatiques et environnementales (température, pollution).

## Outils et Technologies Requises

- **VS Code** (pour le développement Python)
- **SQL Server Management Studio** (pour la gestion de la base de données SQL Server)
- **Power BI** (pour la visualisation des résultats)
- **Docker Desktop** (pour l'exécution de SQL Server sous conteneur Docker)
- **Anaconda** (pour la gestion de l'environnement Python)
- **WSL (Windows Subsystem for Linux)** avec **Ubuntu** (environnement pour l'exécution des scripts et du traitement des données)

### Compétences Requises :
- **Python** : pour le traitement des données et la création de modèles.
- **SQL** : pour interroger et manipuler les données dans SQL Server.
- **T-SQL** : pour effectuer des requêtes avancées dans SQL Server.

### Environnement Requis :
- **Docker Desktop** installé sous Windows pour exécuter SQL Server dans un conteneur Docker.
- **WSL (Ubuntu)** installé pour exécuter le code Python dans un environnement Linux sur Windows.
- **Anaconda** pour gérer les dépendances Python et garantir un environnement reproductible.

---

## Installation

### 1. **Préparer l'environnement Docker avec SQL Server**
- Installer [Docker Desktop](https://www.docker.com/products/docker-desktop) pour Windows.
- Télécharger l'image de SQL Server et la démarrer dans un conteneur Docker :
  ```bash
  docker pull mcr.microsoft.com/mssql/server:2019-latest
  docker run -e 'ACCEPT_EULA=Y' -e 'MSSQL_SA_PASSWORD=VotreMotDePasse' -p 1433:1433 --name sql_server_container -d mcr.microsoft.com/mssql/server:2019-latest

  2. Configurer WSL et Ubuntu
Suivez ce guide officiel pour installer WSL et Ubuntu.

Ouvrir Ubuntu via WSL et installer les dépendances nécessaires :
sudo apt update
sudo apt install python3-pip
sudo apt install python3-dev

3. Installer Anaconda
Si vous n'avez pas déjà Anaconda installé, vous pouvez l'installer via ce lien : Anaconda.

Pour vérifier l'installation d'Anaconda, exécutez :
conda --version

4. Créer et Activer l'Environnement Conda
Clonez ce dépôt et créez un environnement Anaconda à partir du fichier environment.yml fourni.

git clone https://github.com/votre-compte/projet-grippe.git
cd projet-grippe
conda env create -f environment.yml
conda activate grippe-env

git clone https://github.com/votre-compte/projet-grippe.git
cd projet-grippe
conda env create -f environment.yml
conda activate grippe-env

5. Configurer SQL Server Management Studio
Téléchargez et installez SQL Server Management Studio (SSMS) pour gérer la base de données.

6. Power BI
Télécharger et installer Power BI Desktop.

Connectez Power BI à SQL Server pour visualiser les résultats de l'analyse.

Démarrage du Projet
1. Base de données SQL Server
Créez une base de données et les tables nécessaires pour stocker les données des patients, des résultats cliniques et des données climatiques/pollution.

Vous pouvez trouver les scripts SQL dans le dossier /sql pour configurer les tables et insérer des données fictives.

2. Exécution du code Python
Assurez-vous que l'environnement Anaconda est activé.

Vous pouvez ensuite exécuter les scripts Python pour nettoyer et analyser les données.

python analyse.py

Contribution
Si vous souhaitez contribuer à ce projet, vous pouvez fork le dépôt, créer une branche, puis soumettre une pull request.

Étapes pour contribuer :
Fork ce dépôt.

Clonez votre fork sur votre machine locale.

Créez une nouvelle branche.

Apportez vos modifications et commit.

Soumettez une pull request avec une description détaillée des changements.

