"""Tests de la interfaz de consola (unidades sin ejecutar el loop de menú)."""

from book_manager.entities.entities import Genero, Libro
from book_manager.repositories.repositories import (
    RepoEditorialCSV,
    RepoGeneroCSV,
    RepoLibroCSV,
)
from book_manager.ui import console

EDITORIAL_VALIDA = {
    "id": 1,
    "proveedor": "Editorial Alba",
    "pais": "Argentina",
    "provincia": "Buenos Aires",
    "localidad": "CABA",
    "domicilio": "Av 123",
    "telefono": "1145678901",
    "email": "contacto@alba.com",
    "responsable": "Juan Pérez",
}


def test_entidad_a_fila_valores_directos():
    tabla = console.CATALOGO["genero"]
    fila = console._entidad_a_fila(tabla, Genero(id=1, genero="Ficción"))
    assert fila == {"id": 1, "genero": "Ficción"}


def test_resolver_fk(monkeypatch, tmp_path, escribir_csv):
    monkeypatch.setattr(RepoGeneroCSV, "ruta", tmp_path / "genero.csv")
    escribir_csv(tmp_path / "genero.csv", [{"id": 2, "genero": "Terror"}])

    assert console._resolver_fk("genero", 2) == "Terror"
    assert console._resolver_fk("genero", 99) == "99"


def test_entidad_a_fila_resuelve_referencias(monkeypatch, tmp_path, escribir_csv):
    monkeypatch.setattr(RepoGeneroCSV, "ruta", tmp_path / "genero.csv")
    monkeypatch.setattr(RepoEditorialCSV, "ruta", tmp_path / "editorial.csv")

    escribir_csv(tmp_path / "genero.csv", [{"id": 3, "genero": "Terror"}])
    escribir_csv(tmp_path / "editorial.csv", [EDITORIAL_VALIDA])

    libro = Libro(
        id=5,
        isbn="9780306406157",
        titulo="El eco del silencio",
        autor="Marina Solís",
        editorial_id=1,
        genero_id=3,
    )
    fila = console._entidad_a_fila(console.CATALOGO["libro"], libro)

    assert fila["editorial_id"] == "Editorial Alba"
    assert fila["genero_id"] == "Terror"


def test_ver_generos(monkeypatch, tmp_path, capsys, escribir_csv):
    monkeypatch.setattr(RepoGeneroCSV, "ruta", tmp_path / "genero.csv")
    escribir_csv(tmp_path / "genero.csv", [{"id": 1, "genero": "Ficción"}])

    console._ver(console.CATALOGO["genero"])

    salida = capsys.readouterr().out
    assert "Ficción" in salida
    assert "1 género" in salida


def test_crear_genero(monkeypatch, tmp_path):
    monkeypatch.setattr(RepoGeneroCSV, "ruta", tmp_path / "genero.csv")
    monkeypatch.setattr("builtins.input", lambda prompt="": "Ficción")

    console._crear(console.CATALOGO["genero"])

    todos = RepoGeneroCSV().leer_todos()
    assert len(todos) == 1
    assert todos[0].genero == "Ficción"


def test_editar_genero(monkeypatch, tmp_path, escribir_csv):
    monkeypatch.setattr(RepoGeneroCSV, "ruta", tmp_path / "genero.csv")
    escribir_csv(tmp_path / "genero.csv", [{"id": 1, "genero": "Ficción"}])

    respuestas = iter(["1", "1", "Romance"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(respuestas))

    console._editar(console.CATALOGO["genero"])

    todos = RepoGeneroCSV().leer_todos()
    assert todos[0].genero == "Romance"


def test_editar_solo_un_campo(monkeypatch, tmp_path, escribir_csv):
    """Elegir un solo atributo deja el resto intacto."""
    monkeypatch.setattr(RepoEditorialCSV, "ruta", tmp_path / "editorial.csv")
    escribir_csv(tmp_path / "editorial.csv", [EDITORIAL_VALIDA])

    # id=1, campo 8 (Responsable), nuevo valor
    respuestas = iter(["1", "8", "Nuevo Responsable"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(respuestas))

    console._editar(console.CATALOGO["editorial"])

    editorial = RepoEditorialCSV().leer_por_id(1)
    assert editorial.responsable == "Nuevo Responsable"
    assert editorial.proveedor == "Editorial Alba"


def test_eliminar_genero(monkeypatch, tmp_path, escribir_csv):
    monkeypatch.setattr(RepoGeneroCSV, "ruta", tmp_path / "genero.csv")
    escribir_csv(
        tmp_path / "genero.csv",
        [{"id": 1, "genero": "Ficción"}, {"id": 2, "genero": "Terror"}],
    )

    respuestas = iter(["1", "s"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(respuestas))

    console._eliminar(console.CATALOGO["genero"])

    todos = RepoGeneroCSV().leer_todos()
    assert len(todos) == 1
    assert todos[0].genero == "Terror"


def test_buscar_genero(monkeypatch, tmp_path, capsys, escribir_csv):
    monkeypatch.setattr(RepoGeneroCSV, "ruta", tmp_path / "genero.csv")
    escribir_csv(
        tmp_path / "genero.csv",
        [{"id": 1, "genero": "Ficción"}, {"id": 2, "genero": "Ciencia ficción"}],
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": "ficción")

    console._buscar(console.CATALOGO["genero"])

    salida = capsys.readouterr().out
    assert "Ciencia ficción" in salida
    assert "2 géneros" in salida


def test_eliminar_genero_en_uso_muestra_motivo(monkeypatch, tmp_path, capsys, escribir_csv):
    """La consola aplica las reglas del servicio y explica por qué no borra."""
    monkeypatch.setattr(RepoGeneroCSV, "ruta", tmp_path / "genero.csv")
    monkeypatch.setattr(RepoLibroCSV, "ruta", tmp_path / "libro.csv")
    escribir_csv(tmp_path / "genero.csv", [{"id": 1, "genero": "Ficción"}])
    escribir_csv(
        tmp_path / "libro.csv",
        [
            {
                "id": 1,
                "isbn": "9780306406157",
                "titulo": "El eco del silencio",
                "autor": "Marina Solís",
                "editorial_id": 1,
                "genero_id": 1,
            }
        ],
    )
    respuestas = iter(["1", "s"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(respuestas))

    console._eliminar(console.CATALOGO["genero"])

    assert "No se pudo borrar" in capsys.readouterr().out
    assert len(RepoGeneroCSV().leer_todos()) == 1
