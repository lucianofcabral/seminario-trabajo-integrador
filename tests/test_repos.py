"""Tests de regresión para la capa de repositorios CSV."""

from datetime import date

import pytest

from book_manager.entities.entities import Genero, Libro
from book_manager.repositories.repositories import (
    RepoCotizacionDolarCSV,
    RepoEditorialCSV,
    RepoGeneroCSV,
    RepoLibroCSV,
    RepoMonedaCSV,
    RepoPrecioCSV,
    RepoStockCSV,
    RepoTipoCotizacionCSV,
)

REPOS = [
    RepoMonedaCSV,
    RepoGeneroCSV,
    RepoEditorialCSV,
    RepoLibroCSV,
    RepoStockCSV,
    RepoPrecioCSV,
    RepoTipoCotizacionCSV,
    RepoCotizacionDolarCSV,
]

LIBRO = {
    "isbn": "9780306406157",
    "titulo": "El eco del silencio",
    "autor": "Marina Solís",
    "editorial_id": 1,
    "genero_id": 1,
}


@pytest.mark.parametrize("repo_cls", REPOS)
def test_repo_instancia(repo_cls, repo_factory, tmp_path):
    """Todos los repositorios deben poder instanciarse (bug #1)."""
    repo = repo_factory(repo_cls, tmp_path)
    assert repo is not None


def test_leer_por_libro_con_int(repo_factory, tmp_path):
    """Lookup por FK debe matchear con int, no solo con string (bug #4)."""
    repo = repo_factory(
        RepoStockCSV,
        tmp_path,
        "stock.csv",
        [{"id": 1, "libro_id": 7, "existencia": 100}],
    )
    stock = repo.leer_por_libro(7)
    assert stock is not None
    assert stock.existencia == 100


def test_leer_por_libro_y_moneda_con_int(repo_factory, tmp_path):
    """Lookup compuesto por FK numéricas (bug #4)."""
    repo = repo_factory(
        RepoPrecioCSV,
        tmp_path,
        "precio.csv",
        [{"id": 1, "libro_id": 3, "moneda_id": 145, "valor": 68.45}],
    )
    precio = repo.leer_por_libro_y_moneda(3, 145)
    assert precio is not None
    assert precio.valor == 68.45


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


def test_crear_asigna_id_y_persiste(repo_factory, tmp_path):
    repo = repo_factory(RepoLibroCSV, tmp_path, "libro.csv")

    creado = repo.crear(Libro(**LIBRO))

    assert creado.id == 1
    assert repo.leer_por_id(1) == creado


def test_crear_duplicado_lanza_value_error(repo_factory, tmp_path):
    """Un ISBN repetido se rechaza, como indica la interfaz de la cátedra."""
    repo = repo_factory(RepoLibroCSV, tmp_path, "libro.csv")
    repo.crear(Libro(**LIBRO))

    with pytest.raises(ValueError):
        repo.crear(Libro(**{**LIBRO, "titulo": "Otro título"}))
    assert len(repo.leer_todos()) == 1


def test_actualizar_no_permite_repetir_clave(repo_factory, tmp_path):
    repo = repo_factory(RepoGeneroCSV, tmp_path, "genero.csv")
    repo.crear(Genero(genero="Ficción"))
    terror = repo.crear(Genero(genero="Terror"))

    with pytest.raises(ValueError):
        repo.actualizar(terror.model_copy(update={"genero": "Ficción"}))


def test_actualizar_inexistente_lanza_value_error(repo_factory, tmp_path):
    repo = repo_factory(RepoGeneroCSV, tmp_path, "genero.csv")
    with pytest.raises(ValueError):
        repo.actualizar(Genero(id=99, genero="Terror"))


def test_eliminar(repo_factory, tmp_path):
    repo = repo_factory(RepoGeneroCSV, tmp_path, "genero.csv")
    genero = repo.crear(Genero(genero="Ficción"))

    assert repo.eliminar(genero.id) is True
    assert repo.eliminar(genero.id) is False
    assert repo.leer_todos() == []


def test_leer_por_tipo_y_fecha(repo_factory, tmp_path):
    """Busca por tipo de cotización + fecha (bug #7)."""
    repo = repo_factory(
        RepoCotizacionDolarCSV,
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
    cotizacion = repo.leer_por_tipo_y_fecha(2, date(2026, 1, 1))
    assert cotizacion is not None
    assert cotizacion.valor_pesos == 1534.54


def test_leer_historico_por_tipo_ordenado(repo_factory, tmp_path):
    repo = repo_factory(
        RepoCotizacionDolarCSV,
        tmp_path,
        "cotizacion.csv",
        [
            {"id": 1, "tipo_cotizacion_id": 1, "fecha": "2026-01-03", "valor_pesos": 3},
            {"id": 2, "tipo_cotizacion_id": 2, "fecha": "2026-01-02", "valor_pesos": 2},
            {"id": 3, "tipo_cotizacion_id": 1, "fecha": "2026-01-01", "valor_pesos": 1},
        ],
    )
    historico = repo.leer_historico_por_tipo(1)
    assert [c.id for c in historico] == [3, 1]
