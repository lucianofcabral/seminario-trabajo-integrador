"""Tests de la conexión a la base de datos (ConexionDB)."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from book_manager.database.connection import ConexionDB


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
