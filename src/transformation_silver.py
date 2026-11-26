
import json
import html
import re
from pathlib import Path

import pandas as pd

# Chemins des couches Bronze et Silver
BRONZE_DIR = Path("bronze")
SILVER_DIR = Path("silver")

# Création du dossier Silver
SILVER_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(value):
    """Décode les caractères HTML et nettoie les espaces."""

    if not isinstance(value, str):
        return ""

    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def clean_file(json_file):
    """Nettoie un JSON et crée son fichier Parquet correspondant."""

    print(f"\nTraitement de : {json_file.name}")

    # 1. Lecture du fichier JSON
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Gestion des deux structures JSON possibles
    if isinstance(data, list):
        questions = data

    elif isinstance(data, dict):
        questions = data.get("results", [])

    else:
        print("Structure JSON invalide. Fichier ignoré.")
        return

    if not isinstance(questions, list):
        print("Format des questions invalide. Fichier ignoré.")
        return

    # 2. Nettoyage et validation
    cleaned_questions = []
    seen = set()

    for q in questions:

        if not isinstance(q, dict):
            continue

        incorrect_answers = q.get("incorrect_answers", [])

        if not isinstance(incorrect_answers, list):
            continue

        incorrect_answers = [
            clean_text(answer)
            for answer in incorrect_answers
        ]

        incorrect_answers = [
            answer for answer in incorrect_answers if answer
        ]

        cleaned = {
            "type": clean_text(q.get("type")).lower(),
            "difficulty": clean_text(q.get("difficulty")).lower(),
            "category": clean_text(q.get("category")),
            "question": clean_text(q.get("question")),
            "correct_answer": clean_text(q.get("correct_answer")),
            "incorrect_answers": incorrect_answers
        }

        # Vérification des champs obligatoires
        if not all([
            cleaned["type"],
            cleaned["difficulty"],
            cleaned["category"],
            cleaned["question"],
            cleaned["correct_answer"]
        ]):
            continue

        # Vérification des trois mauvaises réponses
        if len(incorrect_answers) != 3:
            continue

        # 3. Suppression des doublons dans le fichier
        key = (
            cleaned["category"].casefold(),
            cleaned["question"].casefold(),
            cleaned["correct_answer"].casefold()
        )

        if key not in seen:
            seen.add(key)
            cleaned_questions.append(cleaned)

    # 4. Conversion en DataFrame
    columns = [
        "type",
        "difficulty",
        "category",
        "question",
        "correct_answer",
        "incorrect_answers"
    ]

    df = pd.DataFrame(cleaned_questions, columns=columns)

    # 5. Création du Parquet correspondant
    parquet_file = SILVER_DIR / f"{json_file.stem}.parquet"

    df.to_parquet(
        parquet_file,
        engine="pyarrow",
        index=False,
        compression="snappy"
    )

    # 6. Bilan du fichier
    print("Questions initiales :", len(questions))
    print("Questions conservées :", len(df))
    print("Questions rejetées :", len(questions) - len(df))
    print("Fichier créé :", parquet_file)


def main():

    # Récupération des fichiers JSON Bronze
    json_files = sorted(BRONZE_DIR.glob("questions_batch_*.json"))

    if not json_files:
        print("Aucun fichier JSON trouvé dans Bronze.")
        return

    print("Nombre de fichiers JSON :", len(json_files))

    # Transformation individuelle de chaque fichier
    for json_file in json_files:
        clean_file(json_file)

    print("\nTransformation Bronze vers Silver terminée !")


if __name__ == "__main__":
    main()
