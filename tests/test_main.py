"""Tests del punto de entrada."""

from book_manager import main as modulo_main
from book_manager.preload_data import preload_data


def test_main_genera_los_csv_faltantes(monkeypatch, tmp_path):
    """Con import_default_data=False igual se crean los CSV que no existen."""
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    monkeypatch.setattr(modulo_main, "console_main", lambda: None)

    modulo_main.main(import_default_data=False)

    assert (tmp_path / "libro.csv").exists()
    assert (tmp_path / "cotizacion.csv").exists()


def test_main_sin_importar_conserva_los_datos(monkeypatch, tmp_path):
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    monkeypatch.setattr(modulo_main, "console_main", lambda: None)
    modulo_main.main(import_default_data=True)
    genero = tmp_path / "genero.csv"
    genero.write_text('"id","genero"\n1,"Solo este"\n', encoding="utf-8")

    modulo_main.main(import_default_data=False)

    assert "Solo este" in genero.read_text(encoding="utf-8")


def test_main_importando_regenera_los_datos(monkeypatch, tmp_path):
    monkeypatch.setattr(preload_data, "CSV_FOLDER", tmp_path)
    monkeypatch.setattr(modulo_main, "console_main", lambda: None)
    modulo_main.main(import_default_data=True)
    genero = tmp_path / "genero.csv"
    genero.write_text('"id","genero"\n1,"Solo este"\n', encoding="utf-8")

    modulo_main.main(import_default_data=True)

    assert "Solo este" not in genero.read_text(encoding="utf-8")
