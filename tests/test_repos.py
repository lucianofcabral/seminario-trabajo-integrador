"""Tests de regresión para la capa de repositorios CSV."""

from datetime import date

import pytest

from book_manager.entities.entities import Libro
from book_manager.services.services import (
    RepoCotizacionCSV,
    RepoEditorialCSV,
    RepoGeneroCSV,
    RepoLibroCSV,
    RepoMonedaCSV,
    RepoPrecioCSV,
    RepoStock,
    RepoTipoCotizacionCSV,
)

REPOS = [
    RepoMonedaCSV,
    RepoGeneroCSV,
    RepoEditorialCSV,
    RepoLibroCSV,
    RepoStock,
    RepoPrecioCSV,
    RepoTipoCotizacionCSV,
    RepoCotizacionCSV,
]


@pytest.mark.parametrize("repo_cls", REPOS)
def test_repo_instancia(repo_cls, repo_factory, tmp_path):
    """Todos los repositorios deben poder instanciarse (bug #1)."""
    repo = repo_factory(repo_cls, tmp_path)
    assert repo is not None


def test_leer_por_libro_id_con_int(repo_factory, tmp_path):
    """Lookup por FK debe matchear con int, no solo con string (bug #4)."""
    repo = repo_factory(
        RepoStock,
        tmp_path,
        "stock.csv",
        [{"id": 1, "libro_id": 7, "existencia": 100}],
    )
    stock = repo.leer_por_libro_id(7)
    assert stock is not None
    assert stock.existencia == 100


def test_leer_por_libro_id_moneda_id_con_int(repo_factory, tmp_path):
    """Lookup compuesto por FK numéricas (bug #4)."""
    repo = repo_factory(
        RepoPrecioCSV,
        tmp_path,
        "precio.csv",
        [{"id": 1, "libro_id": 3, "moneda_id": 145, "valor": 68.45}],
    )
    precio = repo.leer_por_libro_id_moneda_id(3, 145)
    assert precio is not None
    assert precio.valor == 68.45


def test_modificar_stock(repo_factory, tmp_path):
    """modificar_stock debe actualizar el registro existente (bug #5)."""
    repo = repo_factory(
        RepoStock,
        tmp_path,
        "stock.csv",
        [{"id": 1, "libro_id": 7, "existencia": 100}],
    )
    repo.modificar_stock(7, 55)
    stock = repo.leer_por_libro_id(7)
    assert stock.existencia == 55


def test_modificar_precio(repo_factory, tmp_path):
    """modificar_precio debe actualizar el registro existente (bug #5)."""
    repo = repo_factory(
        RepoPrecioCSV,
        tmp_path,
        "precio.csv",
        [{"id": 1, "libro_id": 3, "moneda_id": 145, "valor": 68.45}],
    )
    repo.modificar_precio(3, 145, 99.99)
    precio = repo.leer_por_libro_id_moneda_id(3, 145)
    assert precio.valor == 99.99


def test_leer_por_cadena_busca_subcadena(repo_factory, tmp_path):
    """Buscar una subcadena debe encontrar géneros que la contengan (bug #6)."""
    repo = repo_factory(
        RepoGeneroCSV,
        tmp_path,
        "genero.csv",
        [{"id": 1, "genero": "Ficción"}, {"id": 2, "genero": "Ciencia ficción"}],
    )
    resultados = repo.leer_por_cadena("ciencia")
    assert [g.genero for g in resultados] == ["Ciencia ficción"]


def test_crear_libro_unico_por_isbn(repo_factory, tmp_path):
    """Crear un libro y rechazar duplicado por ISBN devolviendo el existente."""
    repo = repo_factory(RepoLibroCSV, tmp_path, "libro.csv")

    libro = Libro(
        isbn="9780306406157",
        titulo="El eco del silencio",
        autor="Marina Solís",
        editorial_id=1,
        genero_id=1,
    )
    creado = repo.crear(libro)
    assert creado is not None
    assert creado.id == 1

    duplicado = repo.crear(
        Libro(
            isbn="9780306406157",
            titulo="Otro título",
            autor="Otro Autor",
            editorial_id=2,
            genero_id=2,
        )
    )
    assert duplicado.id == 1
    assert duplicado.titulo == "El eco del silencio"


def test_leer_cotizacion_por_tipo_y_fecha(repo_factory, tmp_path):
    """leer_cotizacion debe buscar por tipo_cotizacion_id + fecha (bug #7)."""
    repo = repo_factory(
        RepoCotizacionCSV,
        tmp_path,
        "cotizacion.csv",
        [
            {
                "id": 1,
                "tipo_cotizacion_id": 2,
                "fecha": "2026-01-01",
                "valor_pesos": 1534.54,
            }
        ],
    )
    cotizacion = repo.leer_cotizacion(2, date(2026, 1, 1))
    assert cotizacion is not None
    assert cotizacion.valor_pesos == 1534.54
