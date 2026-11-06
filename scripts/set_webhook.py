import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
SECRET = os.getenv("TELEGRAM_SECRET")
PUBLIC_URL = os.getenv("PUBLIC_URL")

def main():
    if not TOKEN or not SECRET or not PUBLIC_URL:
        print("Error: Faltan variables en el archivo .env (TELEGRAM_TOKEN, TELEGRAM_SECRET o PUBLIC_URL)")
        return

    # Limpiamos la url pública asegurándonos de que no termine en '/'
    base_url = PUBLIC_URL.rstrip('/')
    webhook_url = f"{base_url}/telegram"
    
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    payload = {
        "url": webhook_url,
        "secret_token": SECRET
    }

    print(f"Configurando webhook a: {webhook_url}...")
    
    try:
        response = httpx.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error al conectar con la API de Telegram: {e}")

if __name__ == "__main__":
    main()
