"""Spider de Cúspide: busca cada título del catálogo y extrae el detalle.

La búsqueda usa el endpoint público del sitio (`?s=<titulo>&post_type=product`),
no la sección `/tienda/`, porque es el que devuelve resultados de producto.
De cada búsqueda se toman los 10 primeros resultados: el scraper solo cubre los
libros que ya están en el catálogo propio.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any
from urllib.parse import quote

import scrapy
from scrapy.http import Response

from book_manager.scraper.items import CuspideItem
from book_manager.scraper.loaders import CuspideLoader

# Cantidad máxima de resultados de búsqueda que se visitan por título.
MAXIMO_RESULTADOS = 10

URL_BUSQUEDA = "https://cuspide.com/?s={titulo}&post_type=product"

SEL_TITULO = "h1.product-title.product_title.entry-title::text"
SEL_AUTOR = "div.product-info a[href*='?s=']::text"
SEL_PRECIO = ".product-summary .price .woocommerce-Price-amount::text"
# WooCommerce anida el monto dentro de `<bdi>`: el selector anterior solo toma
# el texto hijo directo, así que este es el fallback de descendientes.
SEL_PRECIO_ANIDADO = ".product-summary .price .woocommerce-Price-amount ::text"
SEL_IMAGEN = "img.wp-post-image::attr(src)"
SEL_IMAGEN_GALERIA = "div.woocommerce-product-gallery__image a::attr(href)"
SEL_FORMAS_PAGO = "#contentPaymentsPopUpArg ul li::text"
SEL_DESCRIPCION = (
    ".product-page-sections .panel.entry-content .livriz-text-synopsis::text"
)
SEL_ISBN = ".product_meta .sku::text"
SEL_RESULTADO = "div.product-small"
SEL_LINK_RESULTADO = ".box-image a::attr(href)"


class CuspideSpider(scrapy.Spider):
    """Busca los libros del catálogo en Cúspide y extrae su detalle.

    Attributes:
        catalogo: Entradas `{"titulo": str, "libro_id": int}` a buscar. El
            `libro_id` es el id del libro en la base propia y viaja por
            `cb_kwargs` hasta el item.
    """

    name = "cuspide"

    def __init__(
        self, catalogo: list[dict[str, Any]] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.catalogo: list[dict[str, Any]] = catalogo or []

    async def start(self) -> AsyncIterator[scrapy.Request]:
        """Entrega los requests iniciales con la API de scrapy 2.13+."""
        for peticion in self.start_requests():
            yield peticion

    def start_requests(self) -> Iterator[scrapy.Request]:
        """Un request de búsqueda por cada título del catálogo."""
        for entrada in self.catalogo:
            yield scrapy.Request(
                URL_BUSQUEDA.format(titulo=quote(entrada["titulo"])),
                callback=self.parse,
                cb_kwargs={"libro_id": entrada["libro_id"]},
            )

    def parse(
        self, response: Response, libro_id: int | None
    ) -> Iterator[scrapy.Request]:
        """Sigue los 10 primeros resultados de la búsqueda hasta su detalle."""
        resultados = response.css(SEL_RESULTADO)[:MAXIMO_RESULTADOS]
        if not resultados:
            self.logger.info(
                "Cúspide no devolvió resultados para libro_id=%s", libro_id
            )
        for resultado in resultados:
            link = resultado.css(SEL_LINK_RESULTADO).get()
            if not link:
                self.logger.warning(
                    "Resultado sin link de detalle para libro_id=%s", libro_id
                )
                continue
            yield response.follow(
                link,
                callback=self.parse_producto,
                cb_kwargs={"libro_id": libro_id},
            )

    def parse_producto(
        self, response: Response, libro_id: int | None
    ) -> Iterator[CuspideItem]:
        """Extrae del detalle el precio, la imagen, las formas de pago y más."""
        if libro_id is None:
            # Un título que no está en el catálogo no se puede persistir: la
            # tabla `precio_web` referencia a `libro.id`.
            self.logger.warning(
                "Se omite el detalle %s: el título no está en el catálogo",
                response.url,
            )
            return

        loader = CuspideLoader(item=CuspideItem(), response=response)
        loader.add_css("titulo", SEL_TITULO)
        loader.add_css("autor", SEL_AUTOR)
        loader.add_css("precio", SEL_PRECIO)
        if not loader.get_collected_values("precio"):
            loader.add_css("precio", SEL_PRECIO_ANIDADO)
        loader.add_css("url_imagen", SEL_IMAGEN)
        if not loader.get_collected_values("url_imagen"):
            loader.add_css("url_imagen", SEL_IMAGEN_GALERIA)
        loader.add_css("formas_pago", SEL_FORMAS_PAGO)
        loader.add_css("descripcion", SEL_DESCRIPCION)
        loader.add_css("isbn", SEL_ISBN)
        loader.add_value("url", response.url)
        loader.add_value("libro_id", libro_id)

        item = loader.load_item()
        if "precio" not in item:
            self.logger.warning(
                "No se encontró el precio en %s (libro_id=%s)", response.url, libro_id
            )
            return
        yield item
