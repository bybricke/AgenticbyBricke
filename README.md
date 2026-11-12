# Telegram Agents Ecommerce API

Este es un proyecto de enrutamiento basado en **LangGraph** y **FastAPI**, diseñado para procesar mensajes de usuarios de un ecommerce (vía Telegram o interfaces web). Utiliza IA (Google Gemini) para clasificar las intenciones en tres categorías: preventa, postventa o consultas generales.

## Requisitos Previos

- Python 3.12 (ver archivo `.python-version`)
- Una clave de API de Google (Gemini)
- Token de un bot de Telegram proporcionado por BotFather.

## Instalación

1. Clona el repositorio.
2. Crea e inicia un entorno virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configura tus variables de entorno:
   Copia el archivo `.env.example` como `.env` y rellena tus claves.

## Ejecución Local del Router (CLI)

Puedes probar el modelo router desde la consola directamente sin levantar la API:

- Con respuesta final simulada:
  ```bash
  python main.py router "¿tienen zapatillas talla 42?"
  ```
- Para ver por cuáles nodos pasó y los motivos (`--saltos`):
  ```bash
  python main.py router "mi pedido 4521 llegó roto" --saltos
  ```

## Clave de la API

El endpoint `/chat` está protegido. Para usarlo necesitas una clave secreta.

1. **Cómo generar una:** Puedes usar cualquier texto difícil de adivinar. Por ejemplo, en tu terminal ejecuta `openssl rand -hex 32` o genera una contraseña segura.
2. **En local:** Añádela en tu archivo `.env`:
   ```bash
   API_KEY="tu_clave_super_secreta"
   ```
3. **En Heroku / Fly.io:** Añádela como variable de entorno (Config Vars en el dashboard de Heroku, o mediante comando):
   ```bash
   heroku config:set API_KEY="tu_clave_super_secreta"
   # o en Fly.io:
   fly secrets set API_KEY="tu_clave_super_secreta"
   ```
Al hacer peticiones POST a `/chat`, envía esta clave en el header `X-API-Key`.

## Levantar la API Localmente

Para iniciar la API en FastAPI con recarga automática para desarrollo:

```bash
uvicorn api.app:app --reload --port 8000
```
- **Swagger (Documentación interactiva):** [http://localhost:8000/docs](http://localhost:8000/docs)

*(Opcional) Probar Telegram en local:*
Puedes usar `ngrok` para exponer tu puerto local al mundo de manera segura (no usa protección anti-bots como Cloudflare, que bloquea a Telegram) y usar esa URL como tu `PUBLIC_URL` para Telegram:
```bash
# Si tienes Mac con Homebrew:
brew install ngrok/ngrok/ngrok
ngrok http 8000

# Si no tienes Homebrew, descarga el zip desde ngrok.com y ejecuta:
./ngrok http 8000
```

## Pruebas
Para correr las pruebas de enrutamiento (`pytest` y test visual):
```bash
pytest tests/
python scripts/test_router.py
```

---

## Conectar la API a Telegram y Desplegar (Fly.io / Heroku)

Sigue estos pasos en orden para levantar tu bot conectándolo con Telegram:

1. **Configura los secretos en tu proveedor de nube (Fly.io o Heroku):**
   *(Ejemplo para Fly.io, si usas Heroku usa `heroku config:set`)*:
   ```bash
   fly secrets set TELEGRAM_TOKEN="tu_token_aqui" TELEGRAM_SECRET="cambiame" GOOGLE_API_KEY="tu_google_key"
   ```

2. **Sube tus cambios y despliega:**
   ```bash
   git add .
   git commit -m "Agregada integración con Telegram Webhook"
   git push origin main
   fly deploy  # O `git push heroku main` dependiendo de tu plataforma
   ```

3. **Registra el Webhook en Telegram:**
   Una vez desplegado y teniendo tu URL pública, configura el archivo `.env` localmente añadiendo tu `PUBLIC_URL` y ejecuta los scripts:
   ```bash
   # Registra la URL en Telegram
   python scripts/set_webhook.py
   
   # Confirma que se registró sin errores
   python scripts/webhook_info.py
   ```

4. **Prueba el Bot:**
   Abre Telegram, escríbele al bot los 6 mensajes de las pruebas (ej: "¿tienen la polera azul en talla M?") y revisa los logs de tu servidor para verificar las rutas:
   ```bash
   fly logs --tail  # o `heroku logs --tail`
   ```

5. **Troubleshooting (Qué revisar si el bot no responde):**
   - Asegúrate de que tu webhook está apuntando a `https://TU_URL/telegram` (la API de Telegram exige **https**).
   - Verifica en `scripts/webhook_info.py` que no haya errores de entrega (`last_error_message`).
   - Confirma que `TELEGRAM_SECRET` sea idéntico en tu `.env` de producción y en la invocación de webhook.
   - Valida que `TELEGRAM_TOKEN` sea el correcto (el que te dio BotFather).
