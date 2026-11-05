# Telegram Agents Ecommerce API

Este es un proyecto de enrutamiento basado en **LangGraph** y **FastAPI**, diseñado para procesar mensajes de usuarios de un ecommerce (vía Telegram o interfaces web). Utiliza IA (Google Gemini) para clasificar las intenciones en tres categorías: preventa, postventa o consultas generales.

## Requisitos Previos

- Python 3.12 (ver archivo `.python-version`)
- Una clave de API de Google (Gemini)
- (Opcional) Token de un bot de Telegram proporcionado por BotFather.

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
   ```bash
   cp .env.example .env
   ```

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
- Para ver la arquitectura del grafo en formato Mermaid (`--diagrama`):
  ```bash
  python main.py router --diagrama
  ```

## Levantar la API Localmente

Para iniciar la API en FastAPI con recarga automática para desarrollo:

```bash
uvicorn api.app:app --reload --port 8000
```

- **Swagger (Documentación interactiva):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** `curl http://localhost:8000/health`
- **Simular un Chat:**
  ```bash
  curl -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"user_id": "cliente_1", "texto": "¿tienen la polera azul en talla M?"}'
  ```

## Pruebas

El proyecto cuenta con suites de test para asegurar la precisión del enrutador.
Para correr las pruebas parametrizadas utilizando `pytest`:

```bash
pytest tests/
```

Para ver la tabla visual de aciertos, corre el script de prueba:
```bash
python scripts/test_router.py
```

## Despliegue en Heroku

El proyecto ya contiene un archivo `Procfile` y la versión de python especificada (`.python-version`).

1. Crea tu aplicación en Heroku y configura las variables de entorno en "Settings > Config Vars" (las mismas del archivo `.env`).
2. Sube los cambios al repositorio y conéctalo con Heroku, o empuja tu rama principal con:
   ```bash
   git push heroku main
   ```

## Conectar a Telegram

Una vez desplegada tu aplicación (y teniendo tu URL pública, p.ej. `https://tu-app.herokuapp.com`):

1. En Heroku, asegúrate de que estén configurados:
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_SECRET`
2. Registra el Webhook en Telegram disparando el siguiente `curl` desde tu terminal (reemplazando `TU_TOKEN` y `TU_URL`):
   ```bash
   curl -F "url=https://TU_URL/telegram" \
        -F "secret_token=cambiame" \
        https://api.telegram.org/botTU_TOKEN/setWebhook
   ```
   *(Nota: Telegram enviará todos los mensajes del bot mediante POST al endpoint `/telegram` de la API)*
