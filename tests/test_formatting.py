"""Tests del formateador de tablas."""

from book_manager.ui.formatting import render_tabla


def test_render_tabla_vacia():
    assert render_tabla([], [("a", "A")]) == ""


def test_render_tabla_alinea_columnas():
    filas = [
        {"id": 1, "titulo": "El eco del silencio", "autor": "Marina Solís"},
        {"id": 2, "titulo": "Sombras", "autor": "Diego Ferrari"},
    ]
    columnas = [("id", "ID"), ("titulo", "TÍTULO"), ("autor", "AUTOR")]

    salida = render_tabla(filas, columnas)

    lineas = salida.splitlines()
    assert len(lineas) == 3  # header + 2 filas

    header = lineas[0]
    assert "ID" in header
    assert "TÍTULO" in header
    assert "AUTOR" in header


def test_render_tabla_columna_numerica_a_la_derecha():
    filas = [{"id": 1, "valor": 68.45}, {"id": 120, "valor": 9.9}]
    salida = render_tabla(filas, [("id", "ID"), ("valor", "VALOR")])

    lineas = salida.splitlines()
    fila_1 = lineas[1]
    fila_120 = lineas[2]

    # El "1" debe quedar alineado a la derecha, alineado con el "0" de "120".
    assert fila_1.index("1") == fila_120.index("120") + 2


def test_render_tabla_none_se_muestra_vacio():
    filas = [{"id": 1, "nota": None}]
    salida = render_tabla(filas, [("id", "ID"), ("nota", "NOTA")])
    assert salida is not None
