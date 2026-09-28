"""Fixtures y helpers compartidos para los tests."""

import csv
from pathlib import Path

import pytest

from book_manager.repositories import repositories as repos

ARCHIVOS_CSV = {
    repos.RepoLibroCSV: "libro.csv",
    repos.RepoGeneroCSV: "genero.csv",
    repos.RepoEditorialCSV: "editorial.csv",
    repos.RepoMonedaCSV: "moneda.csv",
    repos.RepoStockCSV: "stock.csv",
    repos.RepoPrecioCSV: "precio.csv",
    repos.RepoTipoCotizacionCSV: "tipo_cotizacion.csv",
    repos.RepoCotizacionDolarCSV: "cotizacion.csv",
}


@pytest.fixture(autouse=True)
def csv_temporales(monkeypatch, tmp_path):
    """Redirige todos los repositorios a CSV temporales.

    Así ningún test lee ni modifica los datos reales de `migrations/csv`.
    """
    for repo_cls, nombre in ARCHIVOS_CSV.items():
        monkeypatch.setattr(repo_cls, "ruta", tmp_path / nombre)


@pytest.fixture
def repos_csv() -> list[type]:
    """Las clases de todos los repositorios CSV."""
    return list(ARCHIVOS_CSV)


def _escribir_csv(path: Path, filas: list[dict]) -> Path:
    """Escribe un CSV simple con el header derivado de la primera fila."""
    if not filas:
        path.write_text("", encoding="utf-8")
        return path
    campos = list(filas[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)
    return path


@pytest.fixture
def escribir_csv():
    return _escribir_csv


@pytest.fixture
def repo_factory(monkeypatch, escribir_csv):
    """Instancia un repo concreto con su `ruta` redirigida a un CSV temporal."""

    def _factory(repo_cls, tmp_path, nombre="test.csv", filas=None):
        path = tmp_path / nombre
        if filas is not None:
            escribir_csv(path, filas)
        monkeypatch.setattr(repo_cls, "ruta", path, raising=False)
        return repo_cls()

    return _factory
