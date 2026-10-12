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


def test_precio_en_convierte_entre_usd_y_ars():
    from book_manager.ui.console import _precio_en

    assert _precio_en("USD", 100.0, 1500.0, "ARS") == 150000.0
    assert _precio_en("ARS", 150000.0, 1500.0, "USD") == 100.0
    assert _precio_en("USD", 100.0, 1500.0, "USD") == 100.0
    assert _precio_en("USD", 100.0, 1500.0, "EUR") is None


def test_exportar_precios_csv(conexion_poblada, tmp_path):
    from book_manager.ui.console import _exportar_precios_csv

    ruta = tmp_path / "precios.csv"
    _exportar_precios_csv(conexion_poblada, str(ruta))

    contenido = ruta.read_text(encoding="utf-8")
    assert "isbn" in contenido
    assert "titulo" in contenido
    assert "USD" in contenido
