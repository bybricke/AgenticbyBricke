import os
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv

from .prompts import SYSTEM_PROMPT
from .tools import tools

load_dotenv()

# Estado del agente
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Modelo y enlace con herramientas
modelo_nombre = os.getenv("MODELO", "gemini-3.5-flash-lite")
llm = ChatGoogleGenerativeAI(model=modelo_nombre)
llm_with_tools = llm.bind_tools(tools)

# Nodos
def agente_nodo(state: AgentState):
    # Si es el primer mensaje, inyectamos el system prompt silenciosamente
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Construcción del sub-grafo de preventa
workflow = StateGraph(AgentState)

workflow.add_node("agente", agente_nodo)
workflow.add_node("herramientas", ToolNode(tools))

workflow.add_edge(START, "agente")

# Lógica condicional: ¿El modelo quiere usar una herramienta o devolver texto final?
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "herramientas"
    return END

workflow.add_conditional_edges(
    "agente",
    should_continue,
    {
        "herramientas": "herramientas",
        END: END
    }
)

# Después de usar la herramienta, siempre vuelve al agente para que interprete el resultado
workflow.add_edge("herramientas", "agente")

# Compilamos (sin memoria propia, porque la memoria la manejará el router)
graph = workflow.compile()
