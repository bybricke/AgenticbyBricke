import asyncio
from src.router.graph import graph

async def main():
    result = await graph.ainvoke({"mensaje": "hola", "messages": [("user", "hola")]}, {"configurable": {"thread_id": "test_async"}})
    print("Async result:", result.get("ruta"))

if __name__ == "__main__":
    asyncio.run(main())