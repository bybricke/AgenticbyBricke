import asyncio
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import AsyncMemorySaver

def node(state):
    return state

graph = StateGraph(dict)
graph.add_node("node", node)
graph.add_edge(START, "node")
memory = AsyncMemorySaver()
app = graph.compile(checkpointer=memory)

try:
    app.invoke({"test": "value"}, {"configurable": {"thread_id": "1"}})
except Exception as e:
    print(f"Error calling invoke: {type(e).__name__}: {e}")
