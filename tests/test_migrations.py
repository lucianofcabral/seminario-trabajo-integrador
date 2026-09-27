"""Tests de regresión para los generadores de CSVs de seed."""

import csv
from pathlib import Path

from book_manager.migrations import migrations


def _leer_header(path: Path) -> list[str]:
    with open(path, newline="", encoding="utf-8") as f:
        return next(csv.reader(f))


def test_generar_csv_stock_usa_existencia(tmp_path, monkeypatch):
    """El CSV de stock debe usar `existencia` (campo del modelo), no `existencias` (bug #2)."""
    monkeypatch.setattr(migrations, "CSV_FOLDER", tmp_path)
    migrations.generar_csv_stock(renovar=True)

    header = _leer_header(tmp_path / "stock.csv")
    assert "existencia" in header
    assert "existencias" not in header


def test_generar_csv_cotizacion_usa_campos_del_modelo(tmp_path, monkeypatch):
    """El CSV de cotización debe usar los campos del modelo (bug #3)."""
    monkeypatch.setattr(migrations, "CSV_FOLDER", tmp_path)
    migrations.generar_csv_cotizacion(renovar=True)

    header = _leer_header(tmp_path / "cotizacion.csv")
    assert "tipo_cotizacion_id" in header
    assert "valor_pesos" in header
    assert "tipo" not in header
    assert "valor" not in header
