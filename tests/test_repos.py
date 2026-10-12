"""Tests de los repositorios SQL (claves naturales y referencias a objetos)."""

import pytest

from book_manager.entities.entities import Genero
from book_manager.repositories.sql_repository import (
    RepoCotizacionDolarSQL,
    RepoGeneroSQL,
    RepoLibroSQL,
    RepoPrecioSQL,
    RepoStockSQL,
)


def test_genero_crear_y_duplicado(conexion):
    repo = RepoGeneroSQL(conexion)
    repo.crear(Genero(genero="Ficción"))

    assert repo.leer_por_nombre("Ficción") is not None
    with pytest.raises(ValueError):
        repo.crear(Genero(genero="Ficción"))


def test_genero_actualizar_renombra(conexion):
    repo = RepoGeneroSQL(conexion)
    repo.crear(Genero(genero="Ficción"))

    repo.actualizar("Ficción", Genero(genero="Ciencia Ficción"))

    assert repo.leer_por_nombre("Ficción") is None
    assert repo.leer_por_nombre("Ciencia Ficción") is not None


def test_eliminar_devuelve_false_si_no_existe(conexion):
    repo = RepoGeneroSQL(conexion)
    assert repo.eliminar("No existe") is False


def test_libro_resuelve_referencias(conexion_poblada):
    repo = RepoLibroSQL(conexion_poblada)
    libros = repo.leer_todos()

    assert len(libros) >= 10
    assert libros[0].editorial is not None
    assert libros[0].genero is not None
    assert repo.leer_por_isbn(libros[0].isbn) is not None


def test_stock_resuelve_libro(conexion_poblada):
    repo = RepoStockSQL(conexion_poblada)
    stocks = repo.leer_todos()

    assert len(stocks) >= 10
    assert stocks[0].libro.titulo


def test_precio_clave_compuesta(conexion_poblada):
    repo = RepoPrecioSQL(conexion_poblada)
    primero = repo.leer_todos()[0]

    assert (
        repo.leer_por_libro_y_moneda(primero.libro.isbn, primero.moneda.codigo)
        is not None
    )
    assert repo.leer_por_libro(primero.libro.isbn)


def test_cotizacion_historico_por_tipo(conexion_poblada):
    repo = RepoCotizacionDolarSQL(conexion_poblada)
    historico = repo.leer_historico_por_tipo("Blue")

    assert historico
    assert historico[0].tipo_cotizacion.tipo == "Blue"
