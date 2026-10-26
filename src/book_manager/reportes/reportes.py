"""Reporte Excel de precios (Sprint 3, Ejercicio 05).

Genera un reporte en Excel con el precio interno y el precio web de cada libro,
su diferencia y la fecha de extracción. Reutiliza `ServicioComparacionPrecios`
del Ejercicio 04, de modo que el reporte y las alertas se calculan con el mismo
criterio (precio interno en pesos a la cotización oficial de venta).

A diferencia de las alertas, el reporte incluye **todos** los libros con precio
web conocido, sin filtrar por umbral: es la vista completa para analizar precios.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from book_manager.database.connection import ConexionDB
from book_manager.rutas import EXPORTS_FOLDER_PATH
from book_manager.services.services import (
    ComparacionPrecio,
    ServicioComparacionPrecios,
)

COLUMNAS_REPORTE = [
    "Libro",
    "Precio interno",
    "Precio web",
    "Diferencia",
    "Fecha de extracción",
]

ARCHIVO_REPORTE = EXPORTS_FOLDER_PATH / "reporte_precios.xlsx"


class ServicioReporte:
    """Genera el reporte Excel de precios a partir de la comparación.

    Args:
        servicio_comparacion: Comparación ya armada (los tests la inyectan). Si
            no se pasa, se construye sobre la conexión de la base.
        conexion: Base de donde leer precios, cotizaciones y precios web. Solo
            se usa si no se inyecta una comparación.
    """

    def __init__(
        self,
        servicio_comparacion: ServicioComparacionPrecios | None = None,
        conexion: ConexionDB | None = None,
    ) -> None:
        self._servicio = servicio_comparacion or ServicioComparacionPrecios(
            conexion=conexion
        )

    def generar_reporte(self, ruta: Path = ARCHIVO_REPORTE) -> list[ComparacionPrecio]:
        """Escribe en `ruta` el reporte Excel y devuelve las comparaciones.

        El archivo se escribe siempre, aunque no haya libros con precio web: el
        reporte queda con la cabecera lista para descargar y analizar.

        Args:
            ruta: Destino del `.xlsx`. Por defecto `exports/reporte_precios.xlsx`.

        Returns:
            Las comparaciones volcadas al reporte, en el mismo orden.
        """
        comparaciones = self._servicio.comparar()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Precios"
        hoja.append(COLUMNAS_REPORTE)
        for comparacion in comparaciones:
            hoja.append(
                [
                    comparacion.titulo,
                    comparacion.precio_interno,
                    comparacion.precio_web,
                    comparacion.diferencia,
                    comparacion.fecha_extraccion.isoformat(),
                ]
            )
        libro.save(ruta)
        return comparaciones
