# Architecture du projet -- Jouons au Trivial Pursuit
 
## Vue d'ensemble
 
``` mermaid
flowchart TD
    A[API Open Trivia Database<br/>OpenTDB] --> B[Collecte des questions]
    B --> C[Modèle d'IA]
    C --> D[BRONZE<br/>Fichiers JSON<br/>Questions + réponses IA]
    D --> E[SILVER<br/>Fichiers Parquet nettoyés]
    E --> F[questions_clean.parquet]
    E --> G[questions_en_erreur.parquet]
    E --> H[Autres fichiers Parquet]
    F --> Modèles dbt<br/>staging → intermediate → marts
    G --> I
    H --> I
    I --> J[]I[GOLD<br/>Entrepôts DuckDB]
    J --> K[DASHBOARD<br/>Application Streamlit]
```
 
## Organisation des dossiers
 
``` text
trivial-pursuit/
│
├── Source externe : API Open Trivia Database (OpenTDB)
│
├── bronze/                 # Questions brutes et réponses du modèle IA (JSON)
│
├── silver/                 # Données nettoyées au format Parquet
│   ├── questions_clean.parquet
│   ├── questions_en_erreur.parquet
│   └── autres fichiers .parquet
│
├── gold/                   # Entrepôts de données DuckDB
│   ├── benchmark_gemma_test.parquet
│   ├── warehouse.duckdb
│
├── src/                    # Scripts Python et modèles dbt
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── benchmark.py
│   ├──transformation_silver.py
│   ├── extraction_complete.py
│   ├── reponse_nettoyee.py
│   └──test_opentdb.py
    └──test_lm_studio.py
│
├── dashboard/              # Application de visualisation
│   └── app.py
│
├── documentation/          # Documentation du projet
├── logs/                   # Journaux d'exécution
├── target/                 # Fichiers générés par dbt
├── venv/                   # Environnement virtuel Python
├── .env                    # Variables d'environnement
└── .user.yml               # Configuration utilisateur dbt
```
 
## Rôle des couches de données
 
  -----------------------------------------------------------------------
  Couche                  Contenu                 Finalité
  ----------------------- ----------------------- -----------------------
  **Bronze**              Fichiers JSON :         Conserver les données
                          questions brutes et     collectées et générées
                          réponses IA            
 
  **Silver**              Fichiers Parquet        Préparer et fiabiliser
         st_api.py                 nettoyés, questions     les données
                          exploitables et        
                          questions en erreur    
 
  **Gold**                Entrepôts DuckDB et     Organiser les données
                          modèles dbt             pour leur exploitation
 
  **Dashboard**           Application Streamlit   Visualiser les données
                          (`app.py`) et           et les indicateurs
                          composants              
  -----------------------------------------------------------------------
 
## Parcours des données
 
1.  Les questions sont collectées et envoyées au modèle d'IA.
2.  Les questions et les réponses obtenues sont enregistrées dans
    **Bronze** au format JSON.
3.  Les données sont nettoyées et converties au format Parquet dans
    **Silver**.
4.  Les questions nettoyées et celles en erreur sont distinguées.
5.  Les données sont exploitées dans **Gold**, avec DuckDB et les
    modèles dbt.
6.  Le dashboard présente les données et les indicateurs disponibles.
 
> **En résumé :** le projet suit un parcours de données allant des
> questions brutes et des réponses du modèle IA jusqu'à leur
> préparation, leur structuration et leur visualisation.