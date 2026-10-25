"""Pipeline que persiste en la base los datos extraídos de Cúspide.

Cada item es una observación nueva de la tabla `precio_web`: no se actualiza el
registro anterior, así queda el histórico de precios web por libro.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from scrapy import Spider

from book_manager.database.connection import ConexionDB
from book_manager.models import models as m
from book_manager.repositories.sql_repository import RepoPrecioWebSQL
from book_manager.utils import fecha_argentina

# Ancho de la columna `precio_web.descripcion` en la base.
LARGO_MAXIMO_DESCRIPCION = 5000


class PrecioWebPipeline:
    """Guarda cada libro scrapeado como un registro de `precio_web`."""

    def __init__(self, conexion: ConexionDB | None = None) -> None:
        """Inicializa el pipeline.

        Args:
            conexion: Conexión ya armada (los tests la inyectan). Si no se pasa,
                se construye desde las variables de entorno al abrir el spider.
        """
        self.conexion = conexion
        self.repo: RepoPrecioWebSQL | None = None

    def open_spider(self, spider: Spider) -> None:
        """Abre la conexión a la base y arma el repositorio."""
        if self.conexion is None:
            self.conexion = ConexionDB()
        self.repo = RepoPrecioWebSQL(self.conexion)
        spider.logger.info("Pipeline de precios web listo")

    def process_item(self, item: Any, spider: Spider) -> Any:
        """Persiste el item como un registro nuevo y lo devuelve."""
        if self.repo is None:
            raise RuntimeError(
                "El pipeline se usó sin abrir: falta llamar a open_spider()."
            )
        registro = m.PrecioWeb(
            libro_id=item["libro_id"],
            titulo=item["titulo"],
            autor=item.get("autor") or None,
            precio=item["precio"],
            url_imagen=item.get("url_imagen") or "",
            formas_pago=item.get("formas_pago") or "",
            descripcion=(item.get("descripcion") or "")[:LARGO_MAXIMO_DESCRIPCION],
            url=item.get("url") or "",
            fecha_extraccion=fecha_argentina(datetime.now()),
        )
        self.repo.crear(registro)
        return item

    def close_spider(self, spider: Spider) -> None:
        """Libera las conexiones del pool del motor."""
        if self.conexion is not None:
            self.conexion.engine.dispose()
