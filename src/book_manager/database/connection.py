"""Conexión a la base de datos PostgreSQL con SQLAlchemy."""

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from book_manager.utils import cargar_entorno

cargar_entorno()

_VARIABLES_REQUERIDAS: tuple[str, ...] = (
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
)


class ErrorConexion(Exception):
    """La base de datos no está configurada o no se pudo conectar a ella."""


class ConexionDB:
    """Maneja la conexión a la base de datos usando SQLAlchemy.

    Construye la URL de conexión a partir de variables de entorno (secrets de
    Colab o archivo `.env.local`) y expone una fábrica de sesiones. Las
    credenciales nunca quedan escritas en el código.
    """

    def __init__(self, url: URL | str | None = None) -> None:
        """Crea el motor y la fábrica de sesiones.

        Args:
            url: URL de conexión. Si no se pasa, se construye desde las
                variables DB_USER, DB_PASSWORD, DB_HOST, DB_PORT y DB_NAME, y
                se valida que la base responda.

        Raises:
            ErrorConexion: Si falta una variable de entorno, si DB_PORT no es
                un número, o si la base no responde al conectar.
        """
        self.url = url or self._construir_url()
        self.engine: Engine = create_engine(self.url)
        self._session_factory = sessionmaker(bind=self.engine)
        if url is None:
            self.probar_conexion()

    @staticmethod
    def _construir_url() -> URL:
        """Construye la URL de conexión desde las variables de entorno.

        Raises:
            ErrorConexion: Si falta alguna variable o DB_PORT no es numérico.
        """
        faltantes = [v for v in _VARIABLES_REQUERIDAS if not os.environ.get(v)]
        if faltantes:
            raise ErrorConexion(
                "Falta configurar las variables de entorno: "
                + ", ".join(faltantes)
                + ". Definilas como secrets de Colab o en `.env.local`."
            )
        try:
            puerto = int(os.environ["DB_PORT"])
        except ValueError as error:
            raise ErrorConexion(
                "DB_PORT debe ser un número de puerto válido."
            ) from error
        return URL.create(
            drivername="postgresql+psycopg",
            username=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=puerto,
            database=os.environ["DB_NAME"],
            query={"sslmode": "require"},
        )

    def probar_conexion(self) -> None:
        """Abre y cierra una conexión para verificar que la base responda.

        Raises:
            ErrorConexion: Si no se puede conectar a la base.
        """
        try:
            with self.engine.connect():
                pass
        except SQLAlchemyError as error:
            raise ErrorConexion(
                "No se pudo conectar a la base de datos. Revisá las variables "
                "de conexión y que el servicio esté disponible."
            ) from error

    def crear_sesion(self) -> Session:
        """Devuelve una sesión nueva para operar sobre la base de datos."""
        return self._session_factory()

    @contextmanager
    def transaccion(self) -> Generator[Session, None, None]:
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
