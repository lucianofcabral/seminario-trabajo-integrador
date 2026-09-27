"""Formateo de tablas en texto plano, sin dependencias externas."""

from collections.abc import Iterable


def _a_str(valor) -> str:
    """Convierte un valor a texto apto para una celda."""
    if valor is None:
        return ""
    return str(valor)


def _es_numero(texto: str) -> bool:
    """Indica si una celda representa un número (para alinear a la derecha)."""
    t = texto.strip()
    if not t:
        return False
    try:
        float(t)
        return True
    except ValueError:
        return False


def render_tabla(
    filas: Iterable[dict],
    columnas: Iterable[tuple[str, str]],
) -> str:
    """Devuelve una tabla alineada en texto plano.

    Args:
        filas: iterable de dicts (clave -> valor).
        columnas: iterable de (clave, etiqueta) en el orden deseado.

    Returns:
        Texto de la tabla con cabecera, separador y filas alineadas.
        Devuelve cadena vacía si no hay filas.
    """
    filas = list(filas)
    columnas = list(columnas)

    if not filas or not columnas:
        return ""

    claves = [clave for clave, _ in columnas]
    etiquetas = [etiqueta for _, etiqueta in columnas]

    celdas = [[_a_str(fila.get(clave)) for clave in claves] for fila in filas]

    anchos = []
    for i, etiqueta in enumerate(etiquetas):
        ancho = len(etiqueta)
        for fila in celdas:
            ancho = max(ancho, len(fila[i]))
        anchos.append(ancho)

    # Una columna se alinea a la derecha solo si todas sus celdas son numéricas.
    alineacion_derecha = [
        all(_es_numero(fila[i]) for fila in celdas) for i in range(len(claves))
    ]

    def _formatear(celdas_fila: list[str], alinear_derecha: list[bool]) -> str:
        partes = []
        for i, celda in enumerate(celdas_fila):
            if alinear_derecha[i]:
                partes.append(celda.rjust(anchos[i]))
            else:
                partes.append(celda.ljust(anchos[i]))
        return "  " + "  ".join(partes).rstrip()

    lineas = [_formatear(etiquetas, [False] * len(claves))]
    lineas.extend(_formatear(fila, alineacion_derecha) for fila in celdas)

    return "\n".join(lineas)
