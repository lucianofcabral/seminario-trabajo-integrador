"""Punto de entrada: conecta a la base, puebla si hace falta y abre la consola."""

from sqlalchemy import func, select

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import migrar_datos, poblar_base_de_datos
from book_manager.models import models as m
from book_manager.models.models import Base
from book_manager.preload_data.preload_data import precargar_datos
from book_manager.rutas import CSV_FOLDER_PATH, SQL_FOLDER_PATH
from book_manager.ui.console import main as console_main


def _base_vacia(conexion: ConexionDB) -> bool:
    """Indica si la tabla de libros no tiene registros."""
    with conexion.crear_sesion() as sesion:
        return sesion.scalar(select(func.count()).select_from(m.Libro)) == 0


def main(import_default_data: bool = False) -> None:
    """Ejecuta el sistema sobre la base de datos.

    Args:
        import_default_data: Si es True, regenera los CSV de ejemplo, los `.sql`
            y recrea la base desde cero. Con False conserva los datos; solo
            puebla la base si está vacía.
    """
    conexion = ConexionDB()

    if import_default_data:
        Base.metadata.drop_all(conexion.engine)
        precargar_datos(renovar=True)
        migrar_datos(str(CSV_FOLDER_PATH), str(SQL_FOLDER_PATH))

    Base.metadata.create_all(conexion.engine)
    if _base_vacia(conexion):
        poblar_base_de_datos(conexion, str(SQL_FOLDER_PATH))

    console_main(conexion)


if __name__ == "__main__":
    main()
