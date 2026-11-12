from langchain_core.tools import tool

# Base de datos simulada
CATALOGO_SIMULADO = {
    "polera azul": {"M": True, "L": False},
    "zapatillas deportivas": {"38": True, "40": True, "42": False},
    "calcetines": {"unica": True}
}

@tool
def consultar_catalogo(producto: str, talla: str) -> str:
    """
    Busca si un producto específico está en stock en una talla específica.
    Usa esta herramienta cuando el usuario pregunte por disponibilidad.
    """
    producto = producto.lower()
    
    # Búsqueda difusa simple
    encontrado = None
    for item in CATALOGO_SIMULADO:
        if item in producto or producto in item:
            encontrado = item
            break
            
    if encontrado:
        stock = CATALOGO_SIMULADO[encontrado].get(talla.upper())
        if stock:
            return f"Sí, tenemos stock de {encontrado} en talla {talla}."
        elif stock is False:
            return f"Lo siento, {encontrado} en talla {talla} está agotado actualmente."
        else:
            return f"Tenemos {encontrado}, pero no manejamos la talla {talla}. Pregúntale al cliente si desea otra."
            
    return f"No encontré el producto '{producto}' en nuestro catálogo."

@tool
def consultar_promociones() -> str:
    """
    Devuelve las promociones vigentes de la tienda.
    Úsalo cuando el usuario pregunte por descuentos o precios rebajados.
    """
    return "Actualmente tenemos un 20% de descuento en la segunda unidad de zapatillas y envío gratis por compras sobre $50.000."

# Lista exportable de herramientas para inyectar en el LLM
tools = [consultar_catalogo, consultar_promociones]
