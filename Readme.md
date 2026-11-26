
# 🎯 Jouons au Trivial Pursuit

## 📌 Présentation du projet

**Jouons au Trivial Pursuit** est un projet de Data Engineering et d'analyse des performances d'un modèle d'intelligence artificielle appliqué à un jeu de culture générale.

Le projet consiste à soumettre des questions issues du Trivial Pursuit à un modèle d'IA, puis à exploiter les réponses générées afin d'évaluer sa capacité à répondre correctement et rapidement selon différentes catégories de connaissances.

Les résultats sont centralisés dans un Data Warehouse afin de permettre leur analyse et leur visualisation à travers un tableau de bord interactif.

## 🎯 Objectifs du projet

- Automatiser l'envoi de questions de culture générale à un modèle d'intelligence artificielle.
- Collecter et conserver les réponses générées par le modèle.
- Évaluer la précision des réponses produites.
- Mesurer le temps nécessaire à la génération des réponses.
- Analyser les performances du modèle selon les catégories de questions.
- Centraliser et structurer les données dans un Data Warehouse.
- Concevoir un tableau de bord interactif pour faciliter l'exploitation des résultats.

## ⚙️ Fonctionnement général

Le projet repose sur un processus de traitement et d'analyse des données :

1. **Collecte des questions :** exploitation d'un jeu de données contenant des questions de culture générale.
2. **Interrogation du modèle IA :** transmission automatique des questions au modèle Gemma afin de générer des réponses.
3. **Enregistrement des résultats :** conservation des questions, des réponses générées et des informations relatives au traitement.
4. **Transformation des données :** nettoyage, structuration et préparation des données avec dbt.
5. **Centralisation :** stockage des données transformées dans un Data Warehouse DuckDB.
6. **Analyse et visualisation :** exploitation des données pour produire des indicateurs de performance et des visualisations interactives.

## 🛠️ Technologies utilisées

| Technologie | Rôle |
|---|---|
| Python | Automatisation et traitement des données |
| Gemma 3 4B | Modèle d'intelligence artificielle |
| LM Studio | Exécution locale du modèle et exposition de son API |
| SQL | Interrogation et analyse des données |
| dbt | Transformation et modélisation des données |
| DuckDB | Gestion du Data Warehouse |
| Streamlit | Développement du tableau de bord |
| Plotly | Création des visualisations |
| Git / GitHub | Gestion de versions |
| Linux Debian | Environnement de développement |

## 📊 Indicateurs et analyses

Le tableau de bord a pour objectif de présenter une vision synthétique et détaillée des performances du modèle IA.

Les principaux indicateurs suivis sont :

- **Nombre de questions traitées :** volume total de questions soumises au modèle.
- **Précision des réponses :** proportion de réponses correctes parmi les réponses évaluées.
- **Temps moyen de réponse :** durée moyenne de génération d'une réponse.
- **Performance par catégorie :** précision et temps moyen de réponse pour chaque catégorie de questions.
- **Analyse des résultats :** identification des catégories dans lesquelles le modèle obtient les meilleures et les moins bonnes performances.

## 🚀 Installation et exécution

### Prérequis

- Python 3
- Git
- LM Studio
- dbt
- DuckDB
- Streamlit
- Plotly

### Installation

Cloner le dépôt :

```bash
git clone https://github.com/ghitaoukili19/trivial-pursuit.git
cd trivial-pursuit
```

Créer un environnement virtuel :

```bash
python3 -m venv .venv
```

Activer l'environnement :

```bash
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

### Exécution

Lancer les transformations du Data Warehouse :

```bash
dbt run
```

Lancer le tableau de bord :

```bash
streamlit run dashboard/app.py
```

## 📈 Résultat attendu

Le projet vise à mettre en place une solution d'analyse permettant d'évaluer les capacités d'un modèle d'intelligence artificielle sur des questions de culture générale.

L'exploitation des données dans un Data Warehouse et leur restitution sous forme d'indicateurs permettent de comparer les performances du modèle selon plusieurs dimensions, notamment la précision et la rapidité de réponse par catégorie.

---

**Domaine :** Data Engineering – Intelligence Artificielle – Business Intelligence  
**Modèle IA :** Gemma 3 4B  
**Environnement :** Linux Debian
