"""Tests de la migración de datos (CSV → .sql → base)."""

from sqlalchemy import func, select

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import migrar_datos, poblar_base_de_datos
from book_manager.models.models import CotizacionDolar, Libro
from book_manager.rutas import CSV_FOLDER_PATH


def test_migrar_datos_genera_sqls(tmp_path, escribir_csv):
    """Genera .sql con el entrecomillado correcto según el tipo de columna."""
    carpeta_csvs = tmp_path / "csv"
    carpeta_sqls = tmp_path / "sql"
    carpeta_csvs.mkdir()

    escribir_csv(carpeta_csvs / "genero.csv", [{"id": 1, "genero": "Ficción"}])
    escribir_csv(
        carpeta_csvs / "libro.csv",
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

    migrar_datos(str(carpeta_csvs), str(carpeta_sqls))

    sql_libro = (carpeta_sqls / "libro.sql").read_text(encoding="utf-8")
    sql_genero = (carpeta_sqls / "genero.sql").read_text(encoding="utf-8")

    assert (
        "INSERT INTO libro (id, isbn, titulo, autor, editorial_id, genero_id) "
        "VALUES (1, '9780306406157', 'El eco del silencio', 'Marina Solís', 1, 1);"
        in sql_libro
    )
    # el ISBN es texto aunque parezca numérico: va entrecomillado
    assert "'9780306406157'" in sql_libro
    assert "INSERT INTO genero (id, genero) VALUES (1, 'Ficción');" in sql_genero


def test_migrar_datos_puebla_base(tmp_path):
    """Migra los CSV reales del TP1 y puebla una base con sus relaciones."""
    carpeta_sqls = tmp_path / "sql"
    migrar_datos(str(CSV_FOLDER_PATH), str(carpeta_sqls))

    conexion = ConexionDB(f"sqlite:///{tmp_path / 'm.db'}")
    poblar_base_de_datos(conexion, str(carpeta_sqls))

    with conexion.crear_sesion() as sesion:
        total_libros = sesion.scalar(select(func.count()).select_from(Libro))
        total_cotizaciones = sesion.scalar(
            select(func.count()).select_from(CotizacionDolar)
        )
        libro = sesion.scalar(select(Libro))

        assert total_libros >= 10
        assert total_cotizaciones >= 10
        assert libro.editorial is not None
        assert libro.genero is not None
