"""Ejecución del scraper: arma el catálogo de títulos y lanza el crawl.

El catálogo se puede tomar de la base propia, del CSV de libros o de una lista
de títulos escrita a mano. En los tres casos el resultado es la misma lista de
entradas `{"titulo": str, "libro_id": int | None}` que consume el spider.

Si la ejecución recibe un umbral de diferencia de precios, al terminar el crawl
se exporta el CSV de alertas (ver `ServicioComparacionPrecios`).
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Literal

from scrapy.crawler import CrawlerProcess
from sqlalchemy import select

from book_manager.database.connection import ConexionDB
from book_manager.models import models as m
from book_manager.rutas import CSV_FOLDER_PATH, EXPORTS_FOLDER_PATH
from book_manager.scraper.settings import settings
from book_manager.scraper.spiders.cuspide_spider import CuspideSpider
from book_manager.services.services import (
    ComparacionPrecio,
    ServicioComparacionPrecios,
)

Origen = Literal["base", "csv", "manual"]
Catalogo = list[dict[str, Any]]

ARCHIVO_LIBROS = CSV_FOLDER_PATH / "libro.csv"
ARCHIVO_ALERTAS = EXPORTS_FOLDER_PATH / "alertas_precios.csv"


def obtener_catalogo(
    origen: Origen = "base", titulos: list[str] | None = None
) -> Catalogo:
    """Devuelve los libros a buscar en Cúspide.

    Args:
        origen: De dónde salen los títulos.
            `"base"` los lee de la tabla `libro`, `"csv"` del CSV de libros y
            `"manual"` de la lista `titulos`.
        titulos: Títulos a buscar cuando `origen` es `"manual"`.

    Returns:
        Una lista de `{"titulo": str, "libro_id": int | None}`. El `libro_id` es
        None si el título no está en la base.

    Raises:
        ValueError: Si el origen no es conocido o falta la lista de títulos.
    """
    if origen == "base":
        return _catalogo_desde_base()
    if origen == "csv":
        return _catalogo_desde_csv()
    if origen == "manual":
        if not titulos:
            raise ValueError("origen='manual' requiere al menos un título.")
        return _catalogo_desde_titulos(titulos)
    raise ValueError(f"Origen de catálogo desconocido: {origen!r}")


def _catalogo_desde_base() -> Catalogo:
    """Lee todos los libros de la base propia."""
    with ConexionDB().crear_sesion() as sesion:
        filas = sesion.execute(select(m.Libro.id, m.Libro.titulo).order_by(m.Libro.id))
        return [{"titulo": titulo, "libro_id": libro_id} for libro_id, titulo in filas]


def _catalogo_desde_csv() -> Catalogo:
    """Lee el catálogo del CSV de libros (columnas `id` y `titulo`)."""
    with open(ARCHIVO_LIBROS, newline="", encoding="utf-8") as archivo:
        return [
            {"titulo": fila["titulo"], "libro_id": int(fila["id"])}
            for fila in csv.DictReader(archivo)
        ]


def _catalogo_desde_titulos(titulos: list[str]) -> Catalogo:
    """Resuelve el id de cada título contra la base (None si no existe)."""
    with ConexionDB().crear_sesion() as sesion:
        filas = sesion.execute(select(m.Libro.id, m.Libro.titulo))
        ids_por_titulo = {titulo: libro_id for libro_id, titulo in filas}
    return [
        {"titulo": titulo, "libro_id": ids_por_titulo.get(titulo)} for titulo in titulos
    ]


def ejecutar_scraping(
    catalogo: Catalogo,
    umbral: float | None = None,
    ruta_alertas: Path | None = None,
    conexion: ConexionDB | None = None,
) -> list[ComparacionPrecio] | None:
    """Corre el spider de Cúspide sobre el catálogo y exporta las alertas.

    El umbral lo ingresa el usuario antes de cada ejecución (el menú lo pide en
    el Ejercicio 07). Terminado el crawl, el pipeline ya guardó los precios web,
    así que se comparan con el precio interno y se escribe el CSV de alertas.

    Args:
        catalogo: Libros a buscar, como los devuelve `obtener_catalogo`.
        umbral: Diferencia en pesos a partir de la cual alertar. Si es None no
            se compara ni se escribe el archivo.
        ruta_alertas: Destino del CSV. Por defecto `exports/alertas_precios.csv`.
        conexion: Base donde leer los precios. Por defecto, la del entorno.

    Returns:
        Las alertas exportadas, o None si la ejecución no pidió comparación.
    """
    proceso = CrawlerProcess(settings)
    proceso.crawl(CuspideSpider, catalogo=catalogo)
    proceso.start()
    if umbral is None:
        return None
    return ServicioComparacionPrecios(conexion=conexion).exportar_alertas_csv(
        umbral, ruta_alertas or ARCHIVO_ALERTAS
    )
