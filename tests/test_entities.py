"""Tests de las entidades del dominio (sin id, referencias a objetos)."""

import pytest
from pydantic import ValidationError

from book_manager.entities.entities import (
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
)


def _editorial() -> Editorial:
    return Editorial(
        proveedor="Editorial Alba",
        pais="Argentina",
        provincia="Buenos Aires",
        localidad="CABA",
        domicilio="Av. Siempre Viva 123",
        telefono="1145678901",
        email="contacto@editorialalba.com",
        responsable="Juan Pérez",
    )


def test_libro_referencia_objetos_y_sin_id():
    editorial = _editorial()
    genero = Genero(genero="Ficción")
    libro = Libro(
        isbn="9780306406157",
        titulo="El eco del silencio",
        autor="Marina Solís",
        editorial=editorial,
        genero=genero,
    )

    assert libro.editorial.proveedor == "Editorial Alba"
    assert libro.genero.genero == "Ficción"
    assert not hasattr(libro, "id")


def test_stock_y_precio_referencian_objetos():
    libro = Libro(
        isbn="9780306406157",
        titulo="El eco del silencio",
        autor="Marina Solís",
        editorial=_editorial(),
        genero=Genero(genero="Ficción"),
    )
    stock = Stock(libro=libro, existencia=10)
    precio = Precio(libro=libro, moneda=Moneda(codigo="usd", nombre="dólar"), valor=5.0)

    assert stock.libro.isbn == libro.isbn
    assert precio.moneda.codigo == "USD"  # el código se normaliza a mayúsculas


def test_validacion_al_asignar():
    genero = Genero(genero="Ficción")
    with pytest.raises(ValidationError):
        genero.genero = "a"  # min_length=3
