"""Fixtures compartidos para los tests."""

import csv
from pathlib import Path

import pytest

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import poblar_base_de_datos
from book_manager.models.models import Base
from book_manager.rutas import SQL_FOLDER_PATH


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
def conexion(tmp_path):
    """Conexión a SQLite con las tablas creadas y sin datos."""
    conexion = ConexionDB(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(conexion.engine)
    return conexion


@pytest.fixture
def conexion_poblada(tmp_path):
    """Conexión a SQLite con los datos de ejemplo del TP1 cargados."""
    conexion = ConexionDB(f"sqlite:///{tmp_path / 'test.db'}")
    poblar_base_de_datos(conexion, str(SQL_FOLDER_PATH))
    return conexion
