
import ast
import json
import random
import re
import time
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import requests


# ==========================================
# CONFIGURATION
# ==========================================

API_URL = "http://172.22.96.1:1234/v1/chat/completions"
MODEL_NAME = "google/gemma-3-4b"

SILVER_DIR = Path("silver")
BRONZE_DIR = Path("bronze")

OUTPUT_FILE = BRONZE_DIR / "questions_avec_reponses_ia.json"

INITIAL_RETRY_DELAY = 5
MAX_RETRY_DELAY = 60


# ==========================================
# NORMALISATION
# ==========================================

def normalize(text):
    text = str(text).lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ==========================================
# LECTURE DES REPONSES INCORRECTES
# ==========================================

def parse_incorrect_answers(value):

    if value is None:
        return []

    if isinstance(value, np.ndarray):
        value = value.tolist()

    if isinstance(value, (list, tuple)):
        return [
            str(item).strip()
            for item in value
            if item is not None and str(item).strip()
        ]

    try:
        if pd.isna(value):
            return []
    except (TypeError, ValueError):
        pass

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return []

        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(value)

                if isinstance(parsed, (list, tuple)):
                    return [
                        str(item).strip()
                        for item in parsed
                        if item is not None and str(item).strip()
                    ]

            except (ValueError, SyntaxError, TypeError):
                continue

        return [value]

    return []


# ==========================================
# EXTRACTION DE LA REPONSE
# ==========================================

def extract_choice(ai_answer, choices):

    normalized_answer = normalize(ai_answer)
    matches = []

    for choice in choices:
        normalized_choice = normalize(choice)

        if not normalized_choice:
            continue

        pattern = (
            r"(?<!\w)"
            + re.escape(normalized_choice)
            + r"(?!\w)"
        )

        if re.search(pattern, normalized_answer):
            matches.append(choice)

    matches = list(dict.fromkeys(matches))

    return matches[0] if len(matches) == 1 else None


# ==========================================
# CONVERSION DES VALEURS JSON
# ==========================================

def clean_value(value):

    if isinstance(value, np.ndarray):
        return [clean_value(v) for v in value.tolist()]

    if isinstance(value, (list, tuple)):
        return [clean_value(v) for v in value]

    if isinstance(value, dict):
        return {
            str(k): clean_value(v)
            for k, v in value.items()
        }

    if isinstance(value, np.generic):
        value = value.item()

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return value


# ==========================================
# CHARGEMENT DES QUESTIONS SILVER
# ==========================================

def load_silver_data():

    if not SILVER_DIR.exists():
        raise FileNotFoundError(
            f"Dossier {SILVER_DIR} introuvable."
        )

    parquet_files = sorted(
        SILVER_DIR.glob("questions_batch_*.parquet")
    )

    if not parquet_files:
        raise FileNotFoundError(
            "Aucun fichier questions_batch_*.parquet trouvé."
        )

    dataframes = []

    for file in parquet_files:
        print("Chargement :", file.name)

        batch_df = pd.read_parquet(file)

        if not batch_df.empty:
            dataframes.append(batch_df)

    if not dataframes:
        raise ValueError("Aucune question disponible dans Silver.")

    df = pd.concat(
        dataframes,
        ignore_index=True,
        sort=False
    )

    required_columns = [
        "question",
        "correct_answer",
        "incorrect_answers"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Colonnes obligatoires manquantes : {missing}"
        )

    df = df.dropna(
        subset=["question", "correct_answer"]
    ).copy()

    print("\nQuestions chargées :", len(df))

    return df


# ==========================================
# CHARGEMENT DES REPONSES BRONZE
# ==========================================

def load_bronze_data():

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    if not OUTPUT_FILE.exists():
        print("Aucun historique Bronze. Nouveau traitement.")
        return []

    with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
        results = json.load(file)

    if not isinstance(results, list):
        raise ValueError(
            "Le fichier Bronze doit contenir une liste JSON."
        )

    print(
        "Historique Bronze chargé :",
        len(results),
        "enregistrements"
    )

    return results


# ==========================================
# SAUVEGARDE IMMEDIATE ET SECURISEE
# ==========================================

def save_bronze_data(results):

    temp_file = OUTPUT_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=4
        )

    temp_file.replace(OUTPUT_FILE)


# ==========================================
# IDENTIFICATION DES QUESTIONS
# ==========================================

def get_question_key(row):

    return (
        normalize(row.get("category") or ""),
        normalize(row.get("question") or ""),
        normalize(row.get("correct_answer") or "")
    )


# ==========================================
# INTERROGER GEMMA AVEC RETRY
# ==========================================

def ask_model(question, choices):

    prompt = f"""Tu es un assistant de culture générale.

Question :
{question}

Propositions :
{chr(10).join('- ' + str(choice) for choice in choices)}

Consignes :
- Choisis exactement une proposition parmi la liste.
- N'invente aucune réponse.
- Ne donne aucune explication.
- Retourne uniquement le texte exact de la proposition choisie.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0,
        "max_tokens": 100,
        "tool_choice": "none"
    }

    retry_delay = INITIAL_RETRY_DELAY

    while True:

        start_time = time.perf_counter()

        try:

            response = requests.post(
                API_URL,
                json=payload,
                timeout=120
            )

            response.raise_for_status()

            data = response.json()

            ai_answer = data["choices"][0]["message"]["content"]

            if not isinstance(ai_answer, str) or not ai_answer.strip():
                raise ValueError("Gemma a retourné une réponse vide.")

            response_time = time.perf_counter() - start_time

            return ai_answer.strip(), response_time

        except requests.HTTPError as error:

            status_code = (
                error.response.status_code
                if error.response is not None
                else None
            )

            # Erreurs temporaires : on réessaie.
            if status_code == 429 or (
                status_code is not None and status_code >= 500
            ):
                print(
                    f"Erreur HTTP {status_code}. "
                    f"Nouvelle tentative dans {retry_delay}s..."
                )

            else:
                # Erreur permanente de configuration ou de requête.
                raise

        except (
            requests.Timeout,
            requests.ConnectionError,
            requests.RequestException,
            ValueError,
            KeyError,
            IndexError,
            TypeError
        ) as error:

            print("Gemma n'a pas répondu correctement :", error)
            print(f"Nouvelle tentative dans {retry_delay}s...")

        time.sleep(retry_delay)

        retry_delay = min(
            retry_delay * 2,
            MAX_RETRY_DELAY
        )


# ==========================================
# LANCEMENT DU BENCHMARK
# ==========================================

def main():

    print("\n========================================")
    print("BENCHMARK IA :", MODEL_NAME)
    print("========================================")

    # Vérification du serveur
    print("\nVérification de LM Studio...")

    models_url = API_URL.replace(
        "/chat/completions",
        "/models"
    )

    try:

        response = requests.get(
            models_url,
            timeout=10
        )

        response.raise_for_status()

        available_models = [
            model["id"]
            for model in response.json().get("data", [])
        ]

        if MODEL_NAME not in available_models:
            raise ValueError(
                f"Modèle {MODEL_NAME} introuvable. "
                f"Modèles disponibles : {available_models}"
            )

        print("Connexion LM Studio : OK")
        print("Modèle disponible :", MODEL_NAME)

    except (
        requests.RequestException,
        ValueError,
        KeyError
    ) as error:

        print("Erreur de connexion :", error)
        return

    # Chargement Silver
    print("\nChargement des questions Silver...")

    try:
        df = load_silver_data()
        results = load_bronze_data()

    except Exception as error:
        print("Erreur de chargement :", error)
        return

    # Questions déjà traitées avec succès
    processed_keys = {
        (
            normalize(item.get("category") or ""),
            normalize(item.get("question") or ""),
            normalize(item.get("correct_answer") or "")
        )
        for item in results
        if item.get("status") == "OK"
        and isinstance(item.get("ai_answer"), str)
        and item["ai_answer"].strip()
    }

    print(
        "\nQuestions déjà répondues par Gemma :",
        len(processed_keys)
    )

    # Toutes les questions Silver sont traitées.
    total = len(df)

    for index, row in df.iterrows():

        question = str(row["question"]).strip()
        correct_answer = str(row["correct_answer"]).strip()

        key = get_question_key(row)

        # Ne pas renvoyer une question déjà répondue.
        if key in processed_keys:
            continue

        print("\n----------------------------------------")
        print(f"Question {index + 1} / {total}")
        print("Question :", question)

        incorrect_answers = parse_incorrect_answers(
            row["incorrect_answers"]
        )

        choices = list(dict.fromkeys(
            [correct_answer]
            + [
                answer
                for answer in incorrect_answers
                if answer != correct_answer
            ]
        ))

        if len(choices) < 2:

            print("Question ignorée : propositions insuffisantes.")

            result = {
                "type": clean_value(row.get("type")),
                "difficulty": clean_value(row.get("difficulty")),
                "category": clean_value(row.get("category")),
                "question": question,
                "correct_answer": correct_answer,
                "incorrect_answers": clean_value(incorrect_answers),
                "ai_answer": None,
                "ai_answer_extracted": None,
                "ai_correct": None,
                "response_time": None,
                "model_name": MODEL_NAME,
                "status": "SKIPPED",
                "error": "Moins de deux propositions disponibles"
            }

            results.append(result)
            save_bronze_data(results)
            continue

        random.Random(str(index)).shuffle(choices)

        # Interrogation de Gemma.
        # Les erreurs temporaires sont réessayées automatiquement.
        try:

            ai_answer, response_time = ask_model(
                question,
                choices
            )

        except Exception as error:

            print("Erreur non récupérable :", error)

            result = {
                "type": clean_value(row.get("type")),
                "difficulty": clean_value(row.get("difficulty")),
                "category": clean_value(row.get("category")),
                "question": question,
                "correct_answer": correct_answer,
                "incorrect_answers": clean_value(incorrect_answers),
                "ai_answer": None,
                "ai_answer_extracted": None,
                "ai_correct": None,
                "response_time": None,
                "model_name": MODEL_NAME,
                "status": "ERROR",
                "error": str(error)
            }

            results.append(result)
            save_bronze_data(results)
            continue

        extracted_answer = extract_choice(
            ai_answer,
            choices
        )

        is_correct = (
            extracted_answer is not None
            and normalize(extracted_answer)
            == normalize(correct_answer)
        )

        result = {
            "type": clean_value(row.get("type")),
            "difficulty": clean_value(row.get("difficulty")),
            "category": clean_value(row.get("category")),
            "question": question,
            "correct_answer": correct_answer,
            "incorrect_answers": clean_value(incorrect_answers),
            "ai_answer": ai_answer,
            "ai_answer_extracted": extracted_answer,
            "ai_correct": is_correct,
            "response_time": round(response_time, 3),
            "model_name": MODEL_NAME,
            "status": "OK",
            "error": None
        }

        results.append(result)

        processed_keys.add(key)

        # Sauvegarde après CHAQUE réponse.
        save_bronze_data(results)

        print("Réponse Gemma :", ai_answer)
        print("Réponse extraite :", extracted_answer)
        print("Réponse officielle :", correct_answer)
        print("Correct :", is_correct)
        print("Temps :", round(response_time, 3), "secondes")

        print("Réponse enregistrée dans Bronze.")

    # ======================================
    # STATISTIQUES FINALES
    # ======================================

    results_df = pd.DataFrame(results)

    evaluated_df = results_df[
        results_df["status"] == "OK"
    ]

    print("\n========================================")
    print("BENCHMARK TERMINE")
    print("========================================")

    print("Questions Silver :", total)
    print("Enregistrements Bronze :", len(results))
    print("Réponses évaluables :", len(evaluated_df))

    if not evaluated_df.empty:

        success = int(evaluated_df["ai_correct"].sum())

        accuracy = (
            evaluated_df["ai_correct"].mean() * 100
        )

        average_time = evaluated_df["response_time"].mean()

        print("Bonnes réponses :", success)
        print("Taux de réussite :", round(accuracy, 2), "%")
        print("Temps moyen :", round(average_time, 3), "secondes")

    print("\nRésultats enregistrés dans :", OUTPUT_FILE)


if __name__ == "__main__":
    main()
