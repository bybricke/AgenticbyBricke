import argparse
import importlib
import sys

def main():
    parser = argparse.ArgumentParser(description="Ejecutar agentes de LangGraph.")
    parser.add_argument("agent", type=str, help="Nombre del agente a ejecutar")
    parser.add_argument("message", type=str, help="Mensaje a enviar al agente", nargs="?", default="")
    parser.add_argument("--saltos", action="store_true", help="Imprime los nodos por los que pasó el grafo")
    parser.add_argument("--diagrama", action="store_true", help="Imprime el Mermaid del grafo sin ejecutarlo")
    
    args = parser.parse_args()
    agent_name = args.agent
    message = args.message

    # Cargar el agente dinámicamente
    try:
        agent_module = importlib.import_module(f"src.{agent_name}.graph")
        graph = agent_module.graph
    except ImportError as e:
        print(f"Error al cargar el agente '{agent_name}': {e}")
        sys.exit(1)

    if args.diagrama:
        try:
            print(f"Diagrama Mermaid para {agent_name}:\n")
            print(graph.get_graph().draw_mermaid())
        except Exception as e:
            print(f"No se pudo generar el diagrama: {e}")
        return

    if not message:
        print("Se requiere un mensaje para ejecutar el agente.")
        return

    # Configuración de memoria de LangGraph
    config = {"configurable": {"thread_id": "cli_thread_1"}}
    
    # Estado inicial
    initial_state = {
        "mensaje": message,
        "messages": [("user", message)]
    }

    if args.saltos:
        print(f"\nEjecutando agente '{agent_name}' con saltos...\n")
        try:
            # Ejecutar con streaming para ver el paso a paso
            for event in graph.stream(initial_state, config=config, stream_mode="updates"):
                for node_name, node_state in event.items():
                    print(f"-> Nodo: {node_name}")
                    if "motivo" in node_state:
                        print(f"   Motivo: {node_state['motivo']}")
                    if "respuesta" in node_state:
                        print(f"   Respuesta: {node_state['respuesta']}")
            
            # Obtener e imprimir el estado final completo
            final_state = graph.get_state(config).values
            print("\n--- Estado Final ---")
            print(f"Ruta: {final_state.get('ruta')}")
            print(f"Motivo: {final_state.get('motivo')}")
            print(f"Respuesta: {final_state.get('respuesta')}")
            
        except Exception as e:
            print(f"\nError en la ejecución: {e}")
    else:
        try:
            result = graph.invoke(initial_state, config=config)
            print(f"\nRespuesta: {result.get('respuesta')}")
        except Exception as e:
            print(f"\nError en la ejecución: {e}")

if __name__ == "__main__":
    main()
