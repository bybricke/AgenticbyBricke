import os
import logging
from fastapi import FastAPI, HTTPException, Request
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
        422: {"description": "Error de validación (body inválido o faltan campos)."},
        502: {"description": "Error interno al comunicarse con el modelo LLM (Bad Gateway)."}
    }
)
def chat_endpoint(request: ChatRequest):
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


@app.post("/telegram", include_in_schema=False)
async def telegram_webhook(request: Request):
    """
    Webhook destinado a Telegram. Se omite de la documentación de Swagger.
    """
    try:
        # Por ahora solo consumimos el body
        _ = await request.json()
    except Exception:
        pass
    
    return {"ok": True}
