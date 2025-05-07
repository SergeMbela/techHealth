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
