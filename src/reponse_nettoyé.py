 
import json
import re
import html
import unicodedata
 
import pandas as pd
 
from pathlib import Path
 
 
# ==================================================
# 1. CONFIGURATION
# ==================================================
 
# Le script est dans src, Bronze et Silver sont à la racine
BASE_DIR = Path(__file__).resolve().parent.parent
 
BRONZE_DIR = BASE_DIR / "bronze"
SILVER_DIR = BASE_DIR / "silver"
 
INPUT_FILE = BRONZE_DIR / "questions_avec_reponses_ia.json"
 
OUTPUT_CLEAN = SILVER_DIR / "questions_clean.parquet"
 
OUTPUT_ERRORS = SILVER_DIR / "questions_en_erreur.parquet"
 
 
# ==================================================
# 2. CREATION DU DOSSIER SILVER
# ==================================================
 
SILVER_DIR.mkdir(parents=True, exist_ok=True)
 
 
# ==================================================
# 3. NORMALISATION
# ==================================================
 
def normaliser(texte):
 
    if texte is None:
        return ""
 
    texte = html.unescape(str(texte)).lower().strip()
 
    texte = unicodedata.normalize("NFD", texte)
 
    texte = "".join(
        c for c in texte
        if unicodedata.category(c) != "Mn"
    )
 
    texte = re.sub(r"[^\w\s]", " ", texte)
 
    return " ".join(texte.split())
 
 
# ==================================================
# 4. NETTOYAGE DES TEXTES
# ==================================================
 
def nettoyer_texte(texte):
 
    if texte is None:
        return None
 
    texte = html.unescape(str(texte))
 
    texte = re.sub(r"<[^>]+>", "", texte)
 
    texte = re.sub(r"\s+", " ", texte)
 
    return texte.strip()
 
 
# ==================================================
# 5. LECTURE DU FICHIER BRONZE
# ==================================================
 
print("\n========== TRAITEMENT SILVER ==========")
 
if not INPUT_FILE.exists():
 
    raise FileNotFoundError(
        f"Fichier introuvable : {INPUT_FILE}"
    )
 
with open(INPUT_FILE, "r", encoding="utf-8") as f:
 
    donnees = json.load(f)
 
if not isinstance(donnees, list):
 
    raise ValueError("Le fichier Bronze doit contenir une liste JSON.")
 
print("Questions récupérées :", len(donnees))
 
 
# ==================================================
# 6. INITIALISATION
# ==================================================
 
questions_clean = []
 
questions_erreur = []
 
questions_vues = set()
 
doublons = 0
 
sans_reponse = 0
 
# ==================================================
# 7. NETTOYAGE ET VALIDATION
# ==================================================
 
for index, item in enumerate(donnees, start=1):
 
    print(f"Traitement {index}/{len(donnees)}")
 
    if not isinstance(item, dict):
 
        questions_erreur.append({
            "index": index,
            "question": None,
            "source_file": None,
            "silver_error": "Format de question invalide",
            "original_data": json.dumps(
                item,
                ensure_ascii=False,
                default=str
            )
        })
 
        continue
 
    question = nettoyer_texte(item.get("question"))
 
    bonne_reponse = nettoyer_texte(
        item.get("correct_answer")
    )
 
    ai_answer = nettoyer_texte(
        item.get("ai_answer")
    )
 
    # Vérifier les champs obligatoires
 
    if not question or not bonne_reponse:
 
        questions_erreur.append({
            "index": index,
            "question": question,
            "source_file": item.get("source_file"),
            "silver_error": "Question ou bonne réponse manquante",
            "original_data": json.dumps(
                item,
                ensure_ascii=False,
                default=str
            )
        })
 
        continue
 
    # Supprimer les doublons
 
    cle = normaliser(question)
 
    if cle in questions_vues:
 
        doublons += 1
 
        continue
 
    questions_vues.add(cle)
 
    # Vérifier la réponse IA
 
    if not ai_answer:
 
        sans_reponse += 1
 
        questions_erreur.append({
            "index": index,
            "question": question,
            "source_file": item.get("source_file"),
            "silver_error": "Aucune réponse générée par l'IA",
            "original_data": json.dumps(
                item,
                ensure_ascii=False,
                default=str
            )
        })
 
        continue
 
    # Normaliser les réponses pour comparaison
 
    ai_normalisee = normaliser(ai_answer)
 
    bonne_normalisee = normaliser(bonne_reponse)
 
    ai_correct = ai_normalisee == bonne_normalisee
 
    # Nettoyer les réponses proposées
 
    choix = item.get("incorrect_answers", [])
 
    if not isinstance(choix, list):
        choix = []
 
    choix = [
        nettoyer_texte(c)
        for c in choix
        if c is not None and nettoyer_texte(c)
    ]
 
    # Construire la donnée Silver
 
    resultat = {
 
        "question": question,
 
        "category": nettoyer_texte(
            item.get("category")
        ),
 
        "difficulty": nettoyer_texte(
            item.get("difficulty")
        ),
 
        "type": nettoyer_texte(
            item.get("type")
        ),
 
        "incorrect_answers": choix,
 
        "correct_answer": bonne_reponse,
 
        "ai_answer": ai_answer,
 
        "ai_correct": bool(ai_correct),
 
        "response_time": item.get("response_time"),
 
        "ai_model": item.get("ai_model"),
 
        "source_file": item.get("source_file")
 
    }
 
    questions_clean.append(resultat)
 
 
# ==================================================
# 8. CONVERSION EN DATAFRAME
# ==================================================
 
df_clean = pd.DataFrame(questions_clean)
 
df_erreurs = pd.DataFrame(
    questions_erreur,
    columns=[
        "index",
        "question",
        "source_file",
        "silver_error",
        "original_data"
    ]
)
 
 
# ==================================================
# 9. EXPORT PARQUET
# ==================================================
 
df_clean.to_parquet(
    OUTPUT_CLEAN,
    engine="pyarrow",
    index=False
)
 
df_erreurs.to_parquet(
    OUTPUT_ERRORS,
    engine="pyarrow",
    index=False
)
 
 
# ==================================================
# 10. BILAN FINAL
# ==================================================
 
total = len(donnees)
 
print("\n========================================")
 
print("             BILAN SILVER")
 
print("========================================")
 
print("Total Bronze :", total)
 
print("Questions propres :", len(df_clean))
 
print("Questions en erreur :", len(df_erreurs))
 
print("Questions sans réponse IA :", sans_reponse)
 
print("Doublons supprimés :", doublons)
 
 
if not df_clean.empty:
 
    correctes = int(df_clean["ai_correct"].sum())
 
    incorrectes = len(df_clean) - correctes
 
    accuracy = correctes / len(df_clean) * 100
 
    print("Réponses correctes :", correctes)
 
    print("Réponses incorrectes :", incorrectes)
 
    print("Accuracy :", round(accuracy, 2), "%")
 
 
print("\nFichiers Parquet générés :")
 
print("1.", OUTPUT_CLEAN)
 
print("2.", OUTPUT_ERRORS)
 
print("\nTraitement Silver terminé !")