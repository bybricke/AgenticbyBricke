import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.router.graph import setup_db, close_db, memory, memory_type

async def run():
    await setup_db()
    
    print(f"Tipo de memoria: {memory_type}")
    
    if memory_type == "postgres":
        checkpoints = []
        async for c in memory.alist(None):
            checkpoints.append(c)
        print(f"Found {len(checkpoints)} checkpoints")
        if checkpoints:
            print(checkpoints[0])
    await close_db()

if __name__ == "__main__":
    asyncio.run(run())
