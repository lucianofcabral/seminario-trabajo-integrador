"""Items de scrapy: estructura de los datos extraídos de Cúspide."""

from __future__ import annotations

import scrapy


class CuspideItem(scrapy.Item):
    """Datos de un libro publicados en el sitio de Cúspide.

    Cada campo se completa desde el loader (`CuspideLoader`); los campos que no
    se encuentran en la página quedan afuera del item en lugar de viajar vacíos.
    """

    titulo = scrapy.Field()
    autor = scrapy.Field()
    precio = scrapy.Field()
    url_imagen = scrapy.Field()
    formas_pago = scrapy.Field()
    descripcion = scrapy.Field()
    url = scrapy.Field()
    isbn = scrapy.Field()
    libro_id = scrapy.Field()
