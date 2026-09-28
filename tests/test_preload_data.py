"""Tests de regresión para los generadores de CSVs de seed."""

import csv
from pathlib import Path

from book_manager.preload_data import preload_data
from book_manager.repositories import repositories as repos


def _leer_header(path: Path) -> list[str]:
    with open(path, newline="", encoding="utf-8") as f:
        return next(csv.reader(f))


def test_generar_csv_stock_usa_existencia(tmp_path, monkeypatch):
    """El CSV de stock debe usar `existencia` (campo del modelo), no `existencias` (bug #2)."""
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    preload_data.generar_csv_stock(renovar=True)

    header = _leer_header(tmp_path / "stock.csv")
    assert "existencia" in header
    assert "existencias" not in header


def test_generar_csv_cotizacion_usa_campos_del_modelo(tmp_path, monkeypatch):
    """El CSV de cotización debe usar los campos del modelo (bug #3)."""
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    preload_data.generar_csv_cotizacion(renovar=True)

    header = _leer_header(tmp_path / "cotizacion.csv")
    assert "tipo_cotizacion_id" in header
    assert "valor_pesos" in header
    assert "tipo" not in header
    assert "valor" not in header


def test_generar_csv_tipo_cotizacion_tiene_diez_registros(tmp_path, monkeypatch):
    """La consigna pide un mínimo de 10 registros por clase."""
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    preload_data.generar_csv_tipo_cotizacion(renovar=True)

    with open(tmp_path / "tipo_cotizacion.csv", newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) >= 10


def test_precarga_completa_es_consistente(tmp_path, monkeypatch):
    """Cada tabla tiene al menos 10 registros y todas las referencias existen."""
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    archivos = {
        repos.RepoLibroCSV: "libro.csv",
        repos.RepoGeneroCSV: "genero.csv",
        repos.RepoEditorialCSV: "editorial.csv",
        repos.RepoMonedaCSV: "moneda.csv",
        repos.RepoStockCSV: "stock.csv",
        repos.RepoPrecioCSV: "precio.csv",
        repos.RepoTipoCotizacionCSV: "tipo_cotizacion.csv",
        repos.RepoCotizacionDolarCSV: "cotizacion.csv",
    }
    for repo_cls, nombre in archivos.items():
        monkeypatch.setattr(repo_cls, "ruta", tmp_path / nombre)

    preload_data.precargar_datos(renovar=True)

    datos = {repo_cls: repo_cls().leer_todos() for repo_cls in archivos}
    assert all(len(filas) >= 10 for filas in datos.values())

    ids = {repo_cls: {e.id for e in filas} for repo_cls, filas in datos.items()}
    for libro in datos[repos.RepoLibroCSV]:
        assert libro.editorial_id in ids[repos.RepoEditorialCSV]
        assert libro.genero_id in ids[repos.RepoGeneroCSV]
    usd = repos.RepoMonedaCSV().leer_por_codigo("USD")
    for precio in datos[repos.RepoPrecioCSV]:
        assert precio.libro_id in ids[repos.RepoLibroCSV]
        assert precio.moneda_id == usd.id
    for stock in datos[repos.RepoStockCSV]:
        assert stock.libro_id in ids[repos.RepoLibroCSV]
    for cotizacion in datos[repos.RepoCotizacionDolarCSV]:
        assert cotizacion.tipo_cotizacion_id in ids[repos.RepoTipoCotizacionCSV]
