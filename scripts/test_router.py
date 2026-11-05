import json
import os
import sys

# Ajustar PYTHONPATH para poder importar desde src cuando se corre desde la raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.router.graph import graph

def run_tests():
    # Leer JSON
    with open("tests/casos_router.json", "r", encoding="utf-8") as f:
        casos = json.load(f)
        
    aciertos = 0
    total = len(casos)
    fallados = []

    print(f"{'Mensaje':<55} | {'Esperado':<10} | {'Obtenido':<10} | {'Status':<6} | {'Motivo'}")
    print("-" * 130)

    for i, caso in enumerate(casos):
        mensaje = caso["mensaje"]
        esperado = caso["esperado"]
        
        initial_state = {
            "mensaje": mensaje,
            "messages": [("user", mensaje)]
        }
        # Thread único para cada caso, para que no interfiera la memoria de LangGraph
        config = {"configurable": {"thread_id": f"script_thread_{i}"}}
        
        try:
            result = graph.invoke(initial_state, config=config)
            obtenido = result.get("ruta")
            motivo = result.get("motivo")
        except Exception as e:
            obtenido = "error"
            motivo = str(e)
            
        is_correct = (obtenido == esperado)
        status = "✔" if is_correct else "✘"
        
        if is_correct:
            aciertos += 1
        else:
            fallados.append({
                "mensaje": mensaje,
                "esperado": esperado,
                "obtenido": obtenido,
                "motivo": motivo
            })
            
        print(f"{mensaje[:53]:<55} | {esperado:<10} | {obtenido:<10} | {status:<6} | {motivo}")

    porcentaje = (aciertos / total) * 100
    print("-" * 130)
    print(f"\nResultados: {aciertos}/{total} aciertos ({porcentaje:.1f}%)")
    
    if fallados:
        print("\nLista de casos fallados:")
        for f in fallados:
            print(f"- Mensaje: '{f['mensaje']}' | Esperado: {f['esperado']} | Obtenido: {f['obtenido']}")

if __name__ == "__main__":
    run_tests()
