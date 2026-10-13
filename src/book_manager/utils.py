"""Funciones auxiliares compartidas entre capas."""


def normalizar_codigo(codigo: str) -> str:
    """Normaliza un código de moneda: mayúsculas y sin espacios (`" usd "` -> `"USD"`)."""
    return codigo.upper().replace(" ", "")
