import os
import requests
import time
from django.conf import settings

# Cargar settings de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "comercia.settings")
import django
django.setup()

# Tomar tokens de settings.py
BEARER_TOKEN = settings.X_BEARER_TOKEN
USER_ID = getattr(settings, "X_USER_ID", None)
USERNAME = getattr(settings, "X_USERNAME", None)
MAX_RESULTS = getattr(settings, "X_MAX_RESULTS", 5)


def get_user_id_from_username(username):
    """Si solo tienes username, obtener el user_id real desde la API."""
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        data = resp.json()
        return data["data"]["id"]
    else:
        print("❌ Error al obtener user_id:", resp.status_code, resp.text)
        return None


def check_rate_limit(user_id):
    """Consulta tweets y muestra headers de rate limit."""
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {"max_results": MAX_RESULTS}
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    resp = requests.get(url, headers=headers)

    print("\n=== Estado de la API X ===")
    print("Código HTTP:", resp.status_code)

    # Mostrar headers de rate limit
    print("x-rate-limit-limit:", resp.headers.get("x-rate-limit-limit"))
    print("x-rate-limit-remaining:", resp.headers.get("x-rate-limit-remaining"))
    print("x-rate-limit-reset:", resp.headers.get("x-rate-limit-reset"))

    if resp.status_code == 200:
        data = resp.json()
        tweets = data.get("data", [])
        print(f"✅ Se recibieron {len(tweets)} tweets")
        for t in tweets:
            print("-", t["id"], ":", t["text"][:60], "...")
    elif resp.status_code == 429:
        reset_time = int(resp.headers.get("x-rate-limit-reset", time.time() + 60))
        wait_for = max(reset_time - time.time(), 0)
        print(f"⚠️ Rate limit alcanzado. Debes esperar {wait_for:.0f} segundos.")
    else:
        print("❌ Error:", resp.text)


if __name__ == "__main__":
    if USERNAME and not USER_ID:
        USER_ID = get_user_id_from_username(USERNAME)

    if not USER_ID:
        print("⚠️ No se definió USER_ID ni USERNAME en settings.py")
    else:
        check_rate_limit(USER_ID)
