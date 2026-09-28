"""Tests de las entidades."""

import pytest
from pydantic import ValidationError

from book_manager.entities.entities import Moneda, Precio, Stock


def test_asignacion_invalida_se_rechaza():
    """Una entidad no puede quedar en un estado inválido al modificarla."""
    stock = Stock(libro_id=1, existencia=10)
    with pytest.raises(ValidationError):
        stock.existencia = -5
    assert stock.existencia == 10


def test_precio_negativo_se_rechaza():
    with pytest.raises(ValidationError):
        Precio(libro_id=1, moneda_id=1, valor=-1)


def test_codigo_de_moneda_se_normaliza():
    assert Moneda(codigo=" usd", nombre="dólar").codigo == "USD"
