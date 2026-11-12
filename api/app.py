import os
import logging
import httpx
import secrets
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Importar el grafo. Al estar a nivel de módulo, se compila una sola vez al arranque.
from src.router.graph import graph

load_dotenv()

# Configuración básica de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración Swagger (OpenAPI)
description = """
Esta API expone el agente enrutador (Router) para el chat de ecommerce.
Analiza el mensaje del usuario y lo clasifica en una de tres rutas:
- **preventa**: Intención de compra, consultas de stock, productos, tallas, etc.
- **postventa**: Seguimiento de pedidos, devoluciones, quejas o garantías.
- **generica**: Saludos o mensajes no relacionados al ecommerce.
"""

tags_metadata = [
    {"name": "salud", "description": "Endpoints para monitorear el estado de la API."},
    {"name": "chat", "description": "Endpoints para interactuar con el router del agente."},
]

app = FastAPI(
    title="Ecommerce Router API",
    version="1.0.0",
    description=description,
    openapi_tags=tags_metadata
)

# Modelos Pydantic de entrada y salida
class ChatRequest(BaseModel):
    user_id: str = Field(
        ..., 
        description="Identificador único del usuario o sesión de chat (usado para la memoria).",
        examples=["usuario_123"]
    )
    texto: str = Field(
        ..., 
        description="Mensaje del usuario.",
        examples=["¿Tienen la polera azul en talla M?"]
    )

class ChatResponse(BaseModel):
    ruta: str = Field(
        ..., 
        description="Ruta asignada por el router.",
        examples=["preventa"]
    )
    motivo: str = Field(
        ..., 
        description="Motivo explicado por el modelo.",
        examples=["Consulta de disponibilidad y stock de un producto antes de comprar."]
    )
    respuesta: str = Field(
        ..., 
        description="Respuesta provista por el nodo destino.",
        examples=["Soy el agente de preventa. Recibí: ¿Tienen la polera azul en talla M?. Pronto podré ayudarte con productos y compras."]
    )

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False, description="Clave de acceso para usar la API.")

def verify_api_key(api_key: str = Depends(api_key_header)):
    expected_api_key = os.getenv("API_KEY")
    if not expected_api_key:
        raise HTTPException(
            status_code=500,
            detail="API_KEY no configurada en el servidor."
        )
    if not api_key or not secrets.compare_digest(api_key, expected_api_key):
        raise HTTPException(
            status_code=401,
            detail="Falta la clave X-API-Key o es incorrecta."
        )
    return api_key

@app.get("/health", tags=["salud"])
def health_check():
    """
    Retorna el estado de salud del servidor y el modelo configurado.
    """
    modelo = os.getenv("MODELO", "gemini-3.5-flash-lite")
    return {"ok": True, "modelo": modelo}


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["chat"],
    responses={
        200: {"description": "Mensaje procesado y enrutado exitosamente."},
        401: {"description": "No autorizado. Falta X-API-Key o es inválida."},
        422: {"description": "Error de validación (body inválido o faltan campos)."},
        502: {"description": "Error interno al comunicarse con el modelo LLM (Bad Gateway)."}
    }
)
def chat_endpoint(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    """
    Recibe un mensaje, lo envía al agente (router) manteniendo la memoria por `user_id`,
    y devuelve la ruta decidida, el motivo y la respuesta final del agente.
    """
    try:
        initial_state = {
            "mensaje": request.texto,
            "messages": [("user", request.texto)]
        }
        config = {"configurable": {"thread_id": request.user_id}}
        
        # Invocamos el grafo compilado
        result = graph.invoke(initial_state, config=config)
        
        return ChatResponse(
            ruta=result.get("ruta", "desconocida"),
            motivo=result.get("motivo", "Sin motivo"),
            respuesta=result.get("respuesta", "Sin respuesta")
        )
    except Exception as e:
        logger.error(f"Error procesando /chat: {e}")
        # Ocultar detalles internos (stack trace / keys) lanzando un 502 genérico
        raise HTTPException(
            status_code=502,
            detail="Error temporal al comunicarse con el servicio de IA. Intente más tarde."
        )


async def enviar_mensaje_directo_telegram(chat_id: int, texto: str):
    """
    Envía un mensaje directamente a Telegram sin pasar por el agente.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    if token:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": texto
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Error enviando mensaje directo a Telegram: {e}")

async def procesar_mensaje_telegram(chat_id: int, texto: str):
    """
    Invoca el grafo y envía la respuesta a Telegram.
    Se ejecuta en background para no bloquear la respuesta a Telegram.
    """
    try:
        initial_state = {
            "mensaje": texto,
            "messages": [("user", texto)]
        }
        # El thread_id es el chat_id de Telegram para mantener la memoria por usuario
        config = {"configurable": {"thread_id": str(chat_id)}}
        
        result = await graph.ainvoke(initial_state, config=config)
        respuesta = result.get("respuesta", "Lo siento, tuve un problema procesando tu mensaje.")
        ruta = result.get("ruta", "desconocida")
        logger.info(f"Telegram Enrutado -> Chat: {chat_id} | Ruta: {ruta} | Mensaje: {texto[:20]}")

        # Enviar de vuelta a Telegram usando httpx
        token = os.getenv("TELEGRAM_TOKEN")
        if token:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": respuesta
            }
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload)
    except Exception as e:
        logger.error(f"Error procesando mensaje en background para Telegram: {e}")


@app.post("/telegram", include_in_schema=False)
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    """
    Webhook destinado a Telegram. Se omite de la documentación de Swagger.
    """
    # 1. Validar el secret token de Telegram
    secret = os.getenv("TELEGRAM_SECRET")
    if not secret or x_telegram_bot_api_secret_token != secret:
        raise HTTPException(status_code=403, detail="Forbidden: Token inválido.")

    try:
        # 2. Leer el update de Telegram
        data = await request.json()
        message = data.get("message", {})
        
        chat_id = message.get("chat", {}).get("id")
        texto = message.get("text")

        # 3. Detectar GIFs u otros tipos y procesar texto
        if chat_id:
            # Telegram suele enviar los GIFs como 'animation' o como un 'document' de tipo video/mp4
            is_gif = "animation" in message or (
                "document" in message and message["document"].get("mime_type") in ["image/gif", "video/mp4"]
            )
            
            if is_gif:
                mensaje_rechazo = "No entiendo los GIFs por ahora. Por favor, escríbeme o mándame un mensaje de voz."
                background_tasks.add_task(enviar_mensaje_directo_telegram, chat_id, mensaje_rechazo)
                logger.info(f"GIF rechazado para Chat: {chat_id}")
            elif texto:
                # Enviar el procesamiento a una tarea de fondo (Background Task)
                # Esto permite devolver un 200 OK inmediatamente a Telegram
                background_tasks.add_task(procesar_mensaje_telegram, chat_id, texto)
            
    except Exception as e:
        logger.error(f"Error parseando request de Telegram: {e}")
    
    # 4. Responder 200 OK rápido
    return {"ok": True}
