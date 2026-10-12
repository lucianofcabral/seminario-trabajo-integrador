"""Conexión a la base de datos PostgreSQL con SQLAlchemy."""

import os
from collections.abc import Iterator
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()


class ConexionDB:
    """Maneja la conexión a la base de datos usando SQLAlchemy.

    Construye la URL de conexión a partir de variables de entorno (archivo
    `.env`) y expone una fábrica de sesiones. Las credenciales nunca quedan
    escritas en el código.
    """

    def __init__(self, url: URL | str | None = None) -> None:
        """Crea el motor y la fábrica de sesiones.

        Args:
            url: URL de conexión. Si no se pasa, se construye desde las
                variables DB_USER, DB_PASSWORD, DB_HOST, DB_PORT y DB_NAME.
        """
        self.url = url or self._construir_url()
        self.engine: Engine = create_engine(self.url)
        self._session_factory = sessionmaker(bind=self.engine)

    @staticmethod
    def _construir_url() -> URL:
        """Construye la URL de conexión desde las variables de entorno."""
        return URL.create(
            drivername="postgresql+psycopg",
            username=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            database=os.environ["DB_NAME"],
            query={"sslmode": "require"},
        )

    def crear_sesion(self) -> Session:
        """Devuelve una sesión nueva para operar sobre la base de datos."""
        return self._session_factory()

    @contextmanager
    def transaccion(self) -> Iterator[Session]:
        """Abre una transacción: commit al salir sin error, rollback ante fallo.

        Yields:
            La sesión activa para operar dentro del bloque `with`.

        Examples:
            with conexion.transaccion() as sesion:
                sesion.add(entidad)
        """
        sesion = self.crear_sesion()
        try:
            yield sesion
            sesion.commit()
        except Exception:
            sesion.rollback()
            raise
        finally:
            sesion.close()
