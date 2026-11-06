import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

def main():
    if not TOKEN:
        print("Error: Falta la variable TELEGRAM_TOKEN en el archivo .env")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
    
    print("Consultando estado del Webhook...\n")
    
    try:
        response = httpx.get(url)
        print(f"Status Code: {response.status_code}")
        
        data = response.json()
        if data.get("ok"):
            info = data.get("result", {})
            print("\n--- Información del Webhook ---")
            print(f"URL configurada: {info.get('url', 'Ninguna')}")
            print(f"Tiene certificado custom: {info.get('has_custom_certificate')}")
            print(f"Actualizaciones pendientes: {info.get('pending_update_count')}")
            
            error_date = info.get("last_error_date")
            error_msg = info.get("last_error_message")
            if error_date:
                print(f"Último error: {error_msg} (Timestamp: {error_date})")
            else:
                print("Último error: Ninguno.")
        else:
            print(f"Error de Telegram: {data}")
            
    except Exception as e:
        print(f"Error al conectar con la API de Telegram: {e}")

if __name__ == "__main__":
    main()
