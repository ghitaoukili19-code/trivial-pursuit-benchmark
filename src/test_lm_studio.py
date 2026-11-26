
import requests
import time

# Configuration LM Studio
BASE_URL = "http://172.22.96.1:1234/v1"
MODEL_NAME = "google/gemma-3-4b"

print("=" * 45)
print("TEST CONNEXION PYTHON / LM STUDIO")
print("=" * 45)

# TEST 1 : Vérifier la connexion au serveur
try:
    response = requests.get(
        f"{BASE_URL}/models",
        timeout=10
    )
    response.raise_for_status()

    models = response.json()["data"]

    print("\n[OK] Connexion au serveur LM Studio")

    available_models = [m["id"] for m in models]

    print("Modèles disponibles :", available_models)

except Exception as e:
    print("\n[ERREUR] Connexion au serveur :", e)
    raise SystemExit


# TEST 2 : Vérifier la disponibilité de Gemma
if MODEL_NAME not in available_models:
    print("\n[ERREUR] Gemma introuvable")
    raise SystemExit

print("\n[OK] Gemma 3 4B disponible")


# TEST 3 : Envoyer une question au modèle
try:
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "Tu es un assistant de culture générale. Réponds directement en texte simple. N'utilise pas d'outils et ne génère pas de commandes."
            },
            {
                "role": "user",
                "content": "Quelle est la capitale de la France ? Réponds simplement par le nom de la ville."
            }
        ],
        "temperature": 0,
        "max_tokens": 100
    }

    start = time.time()

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    elapsed = time.time() - start

    data = response.json()

    answer = data["choices"][0]["message"]["content"]

    print("\n[OK] Question envoyée à Gemma")
    print("Question : Quelle est la capitale de la France ?")
    print("Réponse :", repr(answer))
    print("Temps :", round(elapsed, 3), "secondes")

except Exception as e:
    print("\n[ERREUR] Génération IA :", e)
