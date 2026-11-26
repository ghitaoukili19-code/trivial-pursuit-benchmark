
import requests
import json
import time
from pathlib import Path

# ==========================================
# 1. CONFIGURATION
# ==========================================

API_URL = "https://opentdb.com/api.php"
TOKEN_URL = "https://opentdb.com/api_token.php"

BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_DIR = BASE_DIR / "bronze"

BRONZE_DIR.mkdir(parents=True, exist_ok=True)

BATCH_SIZE = 50
MAX_RETRIES = 8
MIN_DELAY = 6

last_request_time = 0

session = requests.Session()


# ==========================================
# 2. GESTION DES REQUETES API
# ==========================================

def get_json(url, params):

    global last_request_time

    for attempt in range(MAX_RETRIES):

        elapsed = time.monotonic() - last_request_time
        wait = max(0, MIN_DELAY - elapsed)

        if wait > 0:
            time.sleep(wait)

        print("Envoi de la requête...")

        last_request_time = time.monotonic()

        try:
            response = session.get(
                url,
                params=params,
                timeout=30
            )

            # Erreur HTTP 429
            if response.status_code == 429:

                retry_after = response.headers.get("Retry-After")

                try:
                    wait = float(retry_after)
                except (TypeError, ValueError):
                    wait = min(10 * (2 ** attempt), 120)

                print(f"Erreur 429 : attente de {wait}s...")
                time.sleep(wait)
                continue

            response.raise_for_status()

            data = response.json()

            # Erreur de limitation OpenTDB
            if data.get("response_code") == 5:

                wait = min(10 * (2 ** attempt), 120)

                print(f"Limite API : attente de {wait}s...")
                time.sleep(wait)
                continue

            return data

        except requests.exceptions.RequestException as error:

            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"Erreur réseau : {error}")

            wait = min(5 * (2 ** attempt), 120)

            print(f"Erreur réseau : attente de {wait}s...")
            time.sleep(wait)

    raise RuntimeError("Nombre maximal de tentatives atteint")


# ==========================================
# 3. GESTION DU SESSION TOKEN
# ==========================================

def create_token():

    print("Demande du Session Token...")

    data = get_json(
        TOKEN_URL,
        {"command": "request"}
    )

    if data.get("response_code") != 0:
        raise RuntimeError("Impossible de créer le token")

    print("Session Token obtenu !")

    return data["token"]


# ==========================================
# 4. SAUVEGARDE BRONZE
# ==========================================

def save_batch(questions, batch_number):

    output_file = BRONZE_DIR / f"questions_batch_{batch_number:03d}.json"

    temp_file = output_file.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:

        json.dump(
            questions,
            file,
            ensure_ascii=False,
            indent=4
        )

    # Remplacement atomique du fichier temporaire
    temp_file.replace(output_file)

    print(f"Lot sauvegardé : {output_file.name}")


# ==========================================
# 5. REPRISE DES LOTS EXISTANTS
# ==========================================

def get_next_batch_number():

    existing_files = list(
        BRONZE_DIR.glob("questions_batch_*.json")
    )

    if not existing_files:
        return 1

    numbers = []

    for file in existing_files:
        try:
            number = int(file.stem.split("_")[-1])
            numbers.append(number)
        except ValueError:
            continue

    return max(numbers, default=0) + 1


def load_existing_questions():

    questions = []

    for file in sorted(BRONZE_DIR.glob("questions_batch_*.json")):

        with open(file, "r", encoding="utf-8") as f:
            batch = json.load(f)

        questions.extend(batch)

    return questions


# ==========================================
# 6. EXTRACTION DES QUESTIONS
# ==========================================

print("\n========== EXTRACTION OPENTDB ==========\n")

batch_number = get_next_batch_number()

existing_questions = load_existing_questions()

seen = {
    (
        q["category"],
        q["question"],
        q["correct_answer"]
    )
    for q in existing_questions
}

print(f"Questions déjà enregistrées : {len(seen)}")
print(f"Prochain lot : {batch_number}")

token = create_token()

while True:

    params = {
        "amount": BATCH_SIZE,
        "token": token
    }

    data = get_json(API_URL, params)

    code = data.get("response_code")

    # Token épuisé
    if code == 4:

        print("Token épuisé : création d'un nouveau token.")

        token = create_token()
        continue

    # Aucune question disponible
    if code == 1:

        print("Aucune question supplémentaire disponible.")
        break

    # Token invalide
    if code == 3:

        print("Token invalide : renouvellement.")

        token = create_token()
        continue

    if code != 0:

        raise RuntimeError(f"Erreur OpenTDB : code {code}")

    questions = data["results"]

    new_questions = []

    for q in questions:

        key = (
            q["category"],
            q["question"],
            q["correct_answer"]
        )

        if key not in seen:

            seen.add(key)
            new_questions.append(q)

    if not new_questions:

        print("Aucune nouvelle question dans ce lot.")
        break

    # Sauvegarder chaque lot immédiatement
    save_batch(new_questions, batch_number)

    print(f"Questions reçues : {len(questions)}")
    print(f"Nouvelles questions : {len(new_questions)}")
    print(f"Total collecté : {len(seen)}")

    batch_number += 1


# ==========================================
# 7. BILAN FINAL
# ==========================================

print("\n========== BILAN FINAL ==========")

print("Total des questions :", len(seen))

print(
    "Nombre de fichiers Bronze :",
    len(list(BRONZE_DIR.glob("questions_batch_*.json")))
)

print("Dossier Bronze :", BRONZE_DIR)

print("Extraction terminée !")
