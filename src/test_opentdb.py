import requests

# URL de l'API OpenTDB
url = "https://opentdb.com/api.php?amount=50"

# Envoyer une requête à l'API
response = requests.get(url, timeout=20)

# Vérifier le statut HTTP
response.raise_for_status()

# Récupérer les données JSON
data = response.json()

# Récupérer les questions
questions = data["results"]

# Afficher les résultats
print("Statut HTTP :", response.status_code)
print("Code API :", data["response_code"])
print("Nombre de questions :", len(questions))

# Afficher la première question
print("\nPremière question :")
print(questions[0])
