import json
import os
import sys
import pytest

# Aseguramos que pytest encuentre la carpeta 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import src.router.graph as router_graph

@pytest.mark.anyio
async def test_router_accuracy():
    """
    Test que evalúa todos los casos del router en conjunto.
    Se exige que al menos 13 de los 15 casos sean correctos
    dado que el LLM no es 100% determinista incluso con temperature=0.
    """
    await router_graph.setup_db()
    
    try:
        with open("tests/casos_router.json", "r", encoding="utf-8") as f:
            casos = json.load(f)
            
        aciertos = 0
        total = len(casos)
        
        for i, caso in enumerate(casos):
            mensaje = caso["mensaje"]
            esperado = caso["esperado"]
            
            initial_state = {
                "mensaje": mensaje,
                "messages": [("user", mensaje)]
            }
            config = {"configurable": {"thread_id": f"pytest_thread_{i}"}}
            
            result = await router_graph.graph.ainvoke(initial_state, config=config)
            obtenido = result.get("ruta")
            
            if obtenido == esperado:
                aciertos += 1
                
        assert aciertos >= 13, f"Se esperaban al menos 13 aciertos de {total}, pero se obtuvieron {aciertos}."
    finally:
        await router_graph.close_db()
