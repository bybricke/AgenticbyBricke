import os
from typing import Annotated, Literal, TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from .prompts import ROUTER_PROMPT, PREVENTA_PROMPT, POSTVENTA_PROMPT, GENERICA_PROMPT

load_dotenv()

# Configuración del modelo (usará GOOGLE_API_KEY del entorno automáticamente)
modelo_nombre = os.getenv("MODELO", "gemini-3.5-flash-lite")
llm = ChatGoogleGenerativeAI(model=modelo_nombre)

class Decision(BaseModel):
    ruta: Literal["preventa", "postventa", "generica"] = Field(description="A qué agente va el mensaje.")
    motivo: str = Field(description="Una frase: por qué esa ruta.")

class AgentState(TypedDict):
    mensaje: str
    ruta: str
    motivo: str
    respuesta: str
    messages: Annotated[list, add_messages]

def router_node(state: AgentState):
    # Forzar salida estructurada según el modelo pydantic Decision
    router_llm = llm.with_structured_output(Decision)
    
    mensajes = [
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=state["mensaje"])
    ]
    
    decision = router_llm.invoke(mensajes)
    
    return {
        "ruta": decision.ruta,
        "motivo": decision.motivo
    }

def preventa_node(state: AgentState):
    from src.preventa.graph import graph as preventa_graph
    
    # Le pasamos toda la historia de mensajes al sub-agente
    resultado = preventa_graph.invoke({"messages": state["messages"]})
    
    # Extraemos el último mensaje generado por el sub-agente de preventa
    respuesta_final = resultado["messages"][-1].content
    return {"respuesta": respuesta_final}

def postventa_node(state: AgentState):
    respuesta = POSTVENTA_PROMPT.format(mensaje=state["mensaje"])
    return {"respuesta": respuesta}

def generica_node(state: AgentState):
    return {"respuesta": GENERICA_PROMPT}

# Construcción del grafo
workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("agente_preventa", preventa_node)
workflow.add_node("agente_postventa", postventa_node)
workflow.add_node("respuesta_generica", generica_node)

workflow.add_edge(START, "router")

def route_decision(state: AgentState):
    return state["ruta"]

workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "preventa": "agente_preventa",
        "postventa": "agente_postventa",
        "generica": "respuesta_generica"
    }
)

workflow.add_edge("agente_preventa", END)
workflow.add_edge("agente_postventa", END)
workflow.add_edge("respuesta_generica", END)

# Compilación con Checkpointer (MemorySaver)
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
