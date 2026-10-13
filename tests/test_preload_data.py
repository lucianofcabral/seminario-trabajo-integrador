"""Tests de regresión para los generadores de CSVs de seed."""

import csv
from datetime import date, timedelta
from pathlib import Path

from book_manager.preload_data import preload_data


def _leer_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _leer_header(path: Path) -> list[str]:
    with open(path, newline="", encoding="utf-8") as f:
        return next(csv.reader(f))


def test_generar_csv_stock_usa_existencia(tmp_path, monkeypatch):
    """El CSV de stock debe usar `existencia`, no `existencias`."""
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    preload_data.generar_csv_stock(renovar=True)

    header = _leer_header(tmp_path / "stock.csv")
    assert "existencia" in header
    assert "existencias" not in header


def test_generar_csv_cotizacion_usa_campos_del_modelo(tmp_path, monkeypatch):
    """El CSV de cotización debe usar `tipo_cotizacion_id` y `valor_pesos`."""
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    preload_data.generar_csv_cotizacion(renovar=True)

    header = _leer_header(tmp_path / "cotizacion.csv")
    assert "tipo_cotizacion_id" in header
    assert "valor_pesos" in header


def test_generar_csv_tipo_cotizacion_tiene_diez_registros(tmp_path, monkeypatch):
    """La consigna pide un mínimo de 10 registros por clase."""
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    preload_data.generar_csv_tipo_cotizacion(renovar=True)

    filas = _leer_csv(tmp_path / "tipo_cotizacion.csv")
    assert len(filas) >= 10


def test_precarga_completa_es_consistente(tmp_path, monkeypatch):
    """Cada tabla tiene al menos 10 registros y todas las referencias existen."""
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    preload_data.precargar_datos(renovar=True)

    def ids(nombre: str) -> set[str]:
        return {fila["id"] for fila in _leer_csv(tmp_path / f"{nombre}.csv")}

    editoriales = ids("editorial")
    generos = ids("genero")
    libros = ids("libro")
    monedas = ids("moneda")
    tipos = ids("tipo_cotizacion")

    for libro in _leer_csv(tmp_path / "libro.csv"):
        assert libro["editorial_id"] in editoriales
        assert libro["genero_id"] in generos
    for stock in _leer_csv(tmp_path / "stock.csv"):
        assert stock["libro_id"] in libros
    for precio in _leer_csv(tmp_path / "precio.csv"):
        assert precio["libro_id"] in libros
        assert precio["moneda_id"] in monedas
    for cotizacion in _leer_csv(tmp_path / "cotizacion.csv"):
        assert cotizacion["tipo_cotizacion_id"] in tipos


def test_cotizaciones_de_ejemplo_terminan_una_semana_antes(tmp_path, monkeypatch):
    """Las cotizaciones de ejemplo dejan libre la última semana para la API."""
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    preload_data.generar_csv_cotizacion(renovar=True)

    fechas = [c["fecha"] for c in _leer_csv(tmp_path / "cotizacion.csv")]
    ultima = date.today() - timedelta(days=preload_data.DIAS_SIN_DATOS_DE_EJEMPLO)
    assert max(fechas) == ultima.isoformat()
    assert len(fechas) == 365
    assert len(fechas) == len(set(fechas))
