"""Fixtures y helpers compartidos para los tests."""

import csv
from pathlib import Path

import pytest


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
