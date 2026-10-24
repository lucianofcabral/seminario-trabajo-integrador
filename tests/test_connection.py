"""Tests de la conexión a la base de datos (ConexionDB)."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from book_manager.database.connection import ConexionDB, ErrorConexion


def test_construir_url_desde_entorno(monkeypatch):
    """Construye la URL con SSL a partir de las variables de entorno."""
    monkeypatch.setenv("DB_USER", "postgres.proyecto")
    monkeypatch.setenv("DB_PASSWORD", "clave")
    monkeypatch.setenv("DB_HOST", "aws-0-us-east-1.pooler.supabase.com")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "postgres")

    url = ConexionDB._construir_url()

    assert url.drivername == "postgresql+psycopg"
    assert url.username == "postgres.proyecto"
    assert url.password == "clave"
    assert url.host == "aws-0-us-east-1.pooler.supabase.com"
    assert url.port == 5432
    assert url.database == "postgres"
    assert url.query["sslmode"] == "require"


def test_crear_sesion_con_url_explicita():
    """Crea una sesión operativa a partir de una URL explícita, sin Supabase."""
    conexion = ConexionDB("sqlite://")

    with conexion.crear_sesion() as sesion:
        assert isinstance(sesion, Session)
        assert sesion.execute(text("SELECT 1")).scalar() == 1


def test_transaccion_commitea_al_salir(tmp_path):
    """Confirma los cambios cuando el bloque termina sin error."""
    conexion = ConexionDB(f"sqlite:///{tmp_path / 't.db'}")

    with conexion.transaccion() as sesion:
        sesion.execute(
            text("CREATE TABLE prueba (id INTEGER PRIMARY KEY, nombre TEXT)")
        )
        sesion.execute(text("INSERT INTO prueba (nombre) VALUES ('a')"))

    with conexion.transaccion() as sesion:
        assert sesion.execute(text("SELECT COUNT(*) FROM prueba")).scalar() == 1


def test_transaccion_hace_rollback_ante_error(tmp_path):
    """Deshace los cambios cuando el bloque lanza una excepción."""
    conexion = ConexionDB(f"sqlite:///{tmp_path / 't.db'}")

    with conexion.transaccion() as sesion:
        sesion.execute(
            text("CREATE TABLE prueba (id INTEGER PRIMARY KEY, nombre TEXT)")
        )

    with pytest.raises(RuntimeError), conexion.transaccion() as sesion:
        sesion.execute(text("INSERT INTO prueba (nombre) VALUES ('a')"))
        raise RuntimeError("fallo")

    with conexion.transaccion() as sesion:
        assert sesion.execute(text("SELECT COUNT(*) FROM prueba")).scalar() == 0


def test_construir_url_sin_variable_da_mensaje_claro(monkeypatch):
    """Si falta una variable de entorno, lanza ErrorConexion nombrando la faltante."""
    for variable in ("DB_USER", "DB_HOST", "DB_PORT", "DB_NAME"):
        monkeypatch.setenv(variable, "x")
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(ErrorConexion, match="DB_PASSWORD"):
        ConexionDB._construir_url()


def test_construir_url_con_puerto_invalido_da_mensaje_claro(monkeypatch):
    """Si DB_PORT no es un número, lanza ErrorConexion en lugar de ValueError."""
    for variable, valor in (
        ("DB_USER", "u"),
        ("DB_PASSWORD", "p"),
        ("DB_HOST", "h"),
        ("DB_PORT", "no-es-un-puerto"),
        ("DB_NAME", "d"),
    ):
        monkeypatch.setenv(variable, valor)

    with pytest.raises(ErrorConexion, match="DB_PORT"):
        ConexionDB._construir_url()


def test_conexion_sin_variables_da_mensaje_claro(monkeypatch):
    """ConexionDB() sin variables de entorno no deja escapar un KeyError."""
    for variable in ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"):
        monkeypatch.delenv(variable, raising=False)

    with pytest.raises(ErrorConexion, match="Falta configurar"):
        ConexionDB()


def test_conexion_con_base_que_no_responde_da_mensaje_claro(monkeypatch):
    """Si la base no responde al conectar, lanza ErrorConexion, no un traceback."""
    for variable, valor in (
        ("DB_USER", "u"),
        ("DB_PASSWORD", "p"),
        ("DB_HOST", "h"),
        ("DB_PORT", "5432"),
        ("DB_NAME", "d"),
    ):
        monkeypatch.setenv(variable, valor)

    class _EngineQueFalla:
        def connect(self):
            raise OperationalError("SELECT 1", None, OSError("connection refused"))

    monkeypatch.setattr(
        "book_manager.database.connection.create_engine",
        lambda url: _EngineQueFalla(),
    )

    with pytest.raises(ErrorConexion, match="No se pudo conectar"):
        ConexionDB()
