"""Tests de la consola (catálogo y resolución de referencias)."""

from book_manager.entities.entities import Editorial, Genero, Libro
from book_manager.ui import console
from book_manager.ui.console import _construir_tablas, _entidad_a_fila


def _armar_catalogo(conexion):
    tablas = _construir_tablas(conexion)
    console.CATALOGO.update({t.clave: t for t in tablas})
    return tablas


def test_construir_tablas(conexion):
    tablas = _armar_catalogo(conexion)
    assert len(tablas) == 8
    assert {t.clave for t in tablas} >= {"libro", "genero", "editorial", "moneda"}


def test_entidad_a_fila_resuelve_fk(conexion):
    tablas = _armar_catalogo(conexion)
    libro_tabla = next(t for t in tablas if t.clave == "libro")

    libro = Libro(
        isbn="9780306406157",
        titulo="El eco",
        autor="Marina",
        editorial=Editorial(
            proveedor="Alba",
            pais="Argentina",
            provincia="Buenos Aires",
            localidad="CABA",
            domicilio="Av 1",
            telefono="111",
            email="a@b.com",
            responsable="Juan",
        ),
        genero=Genero(genero="Ficción"),
    )

    fila = _entidad_a_fila(libro_tabla, libro)

    assert fila["isbn"] == "9780306406157"
    assert fila["editorial"] == "Alba"
    assert fila["genero"] == "Ficción"
