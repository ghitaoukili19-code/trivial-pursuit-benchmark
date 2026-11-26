
# AGENTS.md — Trivial Pursuit Benchmark

## 1. Contexte du projet

Trivial Pursuit Benchmark est un projet de data engineering consacré à l'évaluation des performances des modèles d'intelligence artificielle sur des questions de culture générale.

À partir des données publiques d'Open Trivia Database (OpenTDB), le projet consiste à soumettre des questions à différents modèles d'IA, puis à comparer leurs réponses aux réponses correctes de référence.

L'objectif est de transformer les données collectées en informations exploitables pour analyser et comparer les capacités des modèles.

## 2. Objectifs

- Collecter les questions de culture générale depuis OpenTDB.
- Constituer un dataset structuré et exploitable.
- Nettoyer et normaliser les données.
- Enrichir les questions avec les réponses générées par les modèles d'IA.
- Évaluer la justesse des réponses et mesurer les temps de génération.
- Comparer les performances des modèles et l'influence des prompts.
- Produire des indicateurs et des analyses de benchmark.
- Présenter les résultats dans un dashboard interactif.

## 3. Organisation du projet

| Dossier / Fichier | Rôle |
|---|---|
| `bronze/` | Stockage des questions brutes collectées depuis OpenTDB. |
| `silver/` | Données nettoyées, normalisées et enrichies avec les réponses des modèles. |
| `gold/` | Données consolidées et indicateurs destinés aux analyses du benchmark. |
| `src/` | Scripts Python liés à la collecte, au traitement et à l'enrichissement des données. |
| `logs/` | Traces des traitements et des exécutions. |
| `.venv/` | Environnement virtuel Python. |
| `.env` | Variables de configuration du projet. |
| `README.md` | Documentation, méthodologie et instructions d'utilisation. |
| `AGENTS.md` | Présentation du contexte et des objectifs du projet. |

## 4. Données et enrichissement

La source principale est Open Trivia Database, qui fournit des questions caractérisées par :

- Une catégorie (histoire, sciences, géographie, divertissement, etc.).
- Un énoncé.
- Une réponse correcte.
- Plusieurs réponses incorrectes.
- Un niveau de difficulté.

Chaque question est ensuite enrichie avec les résultats des modèles d'IA :

- `ai_answer` : réponse générée par le modèle.
- `ai_correct` : correspondance entre la réponse générée et la réponse attendue.
- `response_time` : durée de génération de la réponse.

Le modèle utilisé et la formulation du prompt constituent également des informations utiles pour interpréter les résultats.

## 5. Axes d'évaluation

| Axe | Objectif |
|---|---|
| Performance globale | Mesurer le taux de bonnes réponses. |
| Performance par catégorie | Identifier les domaines maîtrisés par chaque modèle. |
| Performance par difficulté | Évaluer les capacités selon le niveau des questions. |
| Temps de réponse | Comparer la rapidité des modèles. |
| Comparaison des modèles | Identifier les différences de performance. |
| Comparaison des prompts | Mesurer l'influence de leur formulation sur les réponses. |

D'autres analyses peuvent être ajoutées en fonction des résultats disponibles.

## 6. Résultat attendu

Le projet doit aboutir à un rapport de benchmark permettant de comprendre et de comparer les performances des modèles d'IA.

Les résultats seront présentés dans une application Streamlit interactive permettant de :

- Consulter les principaux indicateurs.
- Comparer les modèles évalués.
- Explorer les performances par catégorie et difficulté.
- Analyser les temps de réponse.
- Identifier les forces et les limites des modèles.

## 7. Livrables

- Un dataset de questions de culture générale collectées et enrichies.
- Un projet de data engineering organisé selon les couches Bronze, Silver et Gold.
- Des données analytiques et des indicateurs de benchmark.
- Un dashboard interactif Streamlit.
- Un dépôt GitHub documenté avec un README expliquant la méthodologie et le setup.
- Une présentation orale de 10 minutes suivie d'une session de questions/réponses.

---

**Vision globale :** exploiter des données de culture générale pour mesurer, analyser et comparer la capacité de différents modèles d'intelligence artificielle à produire des réponses correctes, rapides et fiables.
