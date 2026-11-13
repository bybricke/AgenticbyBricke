import asyncio
import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import src.router.graph as router_graph

async def main():
    parser = argparse.ArgumentParser(description="Ver la memoria guardada en LangGraph.")
    parser.add_argument("thread_id", type=str, nargs="?", help="El ID del hilo a visualizar")
    args = parser.parse_args()

    await router_graph.setup_db()
    
    try:
        memory = router_graph.memory
        memory_type = router_graph.memory_type
        
        if memory_type == "ram":
            print("AVISO: Usando MemorySaver (RAM). Al ser un proceso nuevo, no habrá datos guardados de procesos anteriores.")
            if hasattr(memory, "storage"):
                # Mostrar hilos en memoria RAM (aunque estarán vacíos usualmente si es script nuevo)
                if not args.thread_id:
                    print("\n--- Hilos en RAM ---")
                    for k in memory.storage.keys():
                        print(f"- {k}")
                else:
                    state = await router_graph.graph.aget_state({"configurable": {"thread_id": args.thread_id}})
                    print(state.values)
            return

        # Si es Postgres, podemos listar o leer
        if not args.thread_id:
            # Listar hilos
            print("Listando hilos guardados en la base de datos...\n")
            hilos = {}
            # alist(None) itera por todos los checkpoints guardados.
            async for c in memory.alist(None):
                tid = c.get("config", {}).get("configurable", {}).get("thread_id")
                if tid:
                    if tid not in hilos:
                        hilos[tid] = {"count": 0, "last_date": None}
                    hilos[tid]["count"] += 1
                    
                    # c["metadata"] suele tener "step", c["ts"] tiene la fecha.
                    # langgraph checkpointers devuelven "ts" en c.get("metadata", {}).get("ts") o algo así, 
                    # dependiendo de la versión de PostgresSaver.
                    # Vamos a usar la información del tuple checkpoint
                    ts = c.get("metadata", {}).get("timestamp", c.get("ts"))
                    # Asumimos que los recuperamos y actualizamos
                    # De hecho alist() puede devolver los checkpoints con sus fechas
                    if ts and (not hilos[tid]["last_date"] or ts > hilos[tid]["last_date"]):
                        hilos[tid]["last_date"] = ts
            
            if not hilos:
                print("No se encontraron hilos guardados en la base de datos.")
            else:
                for tid, data in hilos.items():
                    print(f"Hilo: {tid}")
                    print(f"  Checkpoints: {data['count']}")
                    print(f"  Último modificado: {data['last_date']}\n")
                    
        else:
            # Imprimir los mensajes de esa conversación en orden
            print(f"Mensajes para el hilo: {args.thread_id}\n")
            config = {"configurable": {"thread_id": args.thread_id}}
            state = await router_graph.graph.aget_state(config)
            
            if not state or not state.values:
                print("No se encontró estado para este hilo o está vacío.")
                return
                
            messages = state.values.get("messages", [])
            for msg in messages:
                role = getattr(msg, "type", type(msg).__name__)
                content = getattr(msg, "content", msg)
                print(f"[{role.upper()}]: {content}\n")
    finally:
        await router_graph.close_db()

if __name__ == "__main__":
    asyncio.run(main())
