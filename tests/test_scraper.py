"""Tests del scraper de Cúspide.

No usan red: el HTML del sitio se embebe en cada test y se arma un
`HtmlResponse`, así el spider, el loader y el pipeline se ejercitan de punta a
punta sin depender de Cúspide.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import pytest
from scrapy import Request
from scrapy.http import HtmlResponse

from book_manager.database.connection import ConexionDB
from book_manager.models import models as m
from book_manager.repositories.sql_repository import RepoPrecioWebSQL
from book_manager.scraper import runner
from book_manager.scraper.items import CuspideItem
from book_manager.scraper.loaders import CuspideLoader, limpiar_precio
from book_manager.scraper.pipelines import PrecioWebPipeline
from book_manager.scraper.runner import obtener_catalogo
from book_manager.scraper.spiders.cuspide_spider import CuspideSpider
from book_manager.utils import fecha_argentina

URL_DETALLE = "https://cuspide.com/libro/el-eco-del-silencio/"
URL_BUSQUEDA = "https://cuspide.com/?s=El%20eco%20del%20silencio&post_type=product"

MONTO_PLANO = '<span class="woocommerce-Price-amount amount">$ 55.999,00</span>'
MONTO_ANIDADO = (
    '<span class="woocommerce-Price-amount amount"><bdi>'
    '<span class="woocommerce-Price-currencySymbol">$</span>&nbsp;55.999,00'
    "</bdi></span>"
)


def _respuesta(html: str, url: str = URL_DETALLE) -> HtmlResponse:
    """Arma una respuesta HTML con el cuerpo embebido en el test."""
    return HtmlResponse(url=url, body=html.encode("utf-8"), encoding="utf-8")


def _html_resultados(cantidad: int) -> str:
    """HTML de la página de búsqueda con `cantidad` tarjetas de producto."""
    tarjetas = "".join(
        '<div class="product-small"><div class="box-image">'
        f'<a href="https://cuspide.com/libro/resultado-{indice}/"></a>'
        "</div></div>"
        for indice in range(cantidad)
    )
    return f"<html><body>{tarjetas}</body></html>"


def _html_detalle(monto_html: str, *, con_imagen_principal: bool = True) -> str:
    """HTML de la página de detalle de un libro."""
    imagen = (
        '<img class="wp-post-image" src="https://cuspide.com/img/eco.jpg">'
        if con_imagen_principal
        else (
            '<div class="woocommerce-product-gallery__image">'
            '<a href="https://cuspide.com/img/eco-grande.jpg"></a></div>'
        )
    )
    return f"""<html><body>
<h1 class="product-title product_title entry-title">El eco del silencio</h1>
<div class="product-info">
  <a href="/?s=GARCIA%20MARQUEZ,%20GABRIEL&amp;post_type=product">
    GARCIA MARQUEZ, GABRIEL</a>
</div>
<div class="product-summary">
  <p class="price">{monto_html}</p>
</div>
<div class="product_meta"><span class="sku">9780306406157</span></div>
<div id="contentPaymentsPopUpArg">
  <ul>
    <li>Tarjeta de crédito</li>
    <li>Transferencia</li>
  </ul>
</div>
{imagen}
<div class="product-page-sections">
  <div class="panel entry-content">
    <div class="livriz-text-synopsis">Una sinopsis que resume la novela.</div>
  </div>
</div>
</body></html>"""


def _recolectar(iterador: Any) -> list[Any]:
    """Consume un iterador asíncrono desde un test sincrónico."""

    async def _recolectar_async() -> list[Any]:
        return [elemento async for elemento in iterador]

    return asyncio.run(_recolectar_async())


def _crear_libro_de_prueba(conexion: ConexionDB) -> int:
    """Inserta el género, la editorial y el libro mínimos para el pipeline."""
    with conexion.transaccion() as sesion:
        genero = m.Genero(genero="Novela")
        editorial = m.Editorial(
            proveedor="Planeta",
            pais="Argentina",
            provincia="Ciudad de Buenos Aires",
            localidad="CABA",
            domicilio="Av. Corrientes 1234",
            telefono="11-5555-5555",
            email="ventas@planeta.com.ar",
            responsable="Ana Pérez",
        )
        sesion.add_all([genero, editorial])
        sesion.flush()
        libro = m.Libro(
            isbn="9780306406157",
            titulo="El eco del silencio",
            autor="Marina Solís",
            editorial_id=editorial.id,
            genero_id=genero.id,
        )
        sesion.add(libro)
        sesion.flush()
        return libro.id


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("$ 55.999,00", 55999.0),
        ("55.999,00", 55999.0),
        ("$ 1.234,50", 1234.5),
        ("&nbsp;9.999,99", 9999.99),
        ("", None),
        ("   ", None),
        ("$", None),
    ],
)
def test_limpiar_precio(entrada: str, esperado: float | None) -> None:
    assert limpiar_precio(entrada) == esperado


def test_loader_aplica_procesadores_de_entrada_y_salida() -> None:
    loader = CuspideLoader(item=CuspideItem())
    loader.add_value("titulo", "  El eco del silencio  ")
    loader.add_value("precio", "$ 55.999,00")
    loader.add_value("formas_pago", ["Tarjeta de crédito", " Transferencia "])

    item = loader.load_item()

    assert item["titulo"] == "El eco del silencio"
    assert item["precio"] == 55999.0
    assert isinstance(item["precio"], float)
    assert item["formas_pago"] == "Tarjeta de crédito, Transferencia"


def test_start_requests_arma_la_busqueda_por_titulo() -> None:
    spider = CuspideSpider(
        catalogo=[
            {"titulo": "El eco del silencio", "libro_id": 1},
            {"titulo": "Cien años de soledad", "libro_id": 2},
        ]
    )

    peticiones = list(spider.start_requests())

    assert [peticion.url for peticion in peticiones] == [
        URL_BUSQUEDA,
        "https://cuspide.com/?s=Cien%20a%C3%B1os%20de%20soledad&post_type=product",
    ]
    assert [peticion.cb_kwargs["libro_id"] for peticion in peticiones] == [1, 2]
    assert all(peticion.callback == spider.parse for peticion in peticiones)


def test_start_entrega_las_peticiones_iniciales() -> None:
    """Scrapy 2.13+ consume `start()`; el spider tiene que alimentarlo."""
    spider = CuspideSpider(catalogo=[{"titulo": "El eco del silencio", "libro_id": 1}])

    peticiones = _recolectar(spider.start())

    assert len(peticiones) == 1
    assert isinstance(peticiones[0], Request)
    assert peticiones[0].url == URL_BUSQUEDA


def test_parse_toma_como_maximo_diez_resultados() -> None:
    spider = CuspideSpider(catalogo=[{"titulo": "El eco del silencio", "libro_id": 1}])

    respuesta = _respuesta(_html_resultados(12), URL_BUSQUEDA)

    peticiones = list(spider.parse(respuesta, libro_id=1))

    assert len(peticiones) == 10
    assert all(isinstance(peticion, Request) for peticion in peticiones)
    assert peticiones[0].url == "https://cuspide.com/libro/resultado-0/"
    assert all(peticion.cb_kwargs["libro_id"] == 1 for peticion in peticiones)
    assert all(peticion.callback == spider.parse_producto for peticion in peticiones)


def test_parse_sin_resultados_no_genera_peticiones() -> None:
    spider = CuspideSpider(catalogo=[{"titulo": "El eco del silencio", "libro_id": 1}])

    respuesta = _respuesta(_html_resultados(0), URL_BUSQUEDA)

    assert list(spider.parse(respuesta, libro_id=1)) == []


@pytest.mark.parametrize("monto_html", [MONTO_PLANO, MONTO_ANIDADO])
def test_parse_producto_extrae_todos_los_campos(monto_html: str) -> None:
    spider = CuspideSpider(catalogo=[])
    respuesta = _respuesta(_html_detalle(monto_html))

    items = list(spider.parse_producto(respuesta, libro_id=7))

    assert len(items) == 1
    item = items[0]
    assert item["titulo"] == "El eco del silencio"
    assert item["autor"] == "GARCIA MARQUEZ, GABRIEL"
    assert item["precio"] == 55999.0
    assert isinstance(item["precio"], float)
    assert item["url_imagen"] == "https://cuspide.com/img/eco.jpg"
    assert item["formas_pago"] == "Tarjeta de crédito, Transferencia"
    assert item["descripcion"] == "Una sinopsis que resume la novela."
    assert item["isbn"] == "9780306406157"
    assert item["url"] == respuesta.url
    assert item["libro_id"] == 7


def test_parse_producto_usa_la_galeria_si_falta_la_imagen_principal() -> None:
    spider = CuspideSpider(catalogo=[])
    respuesta = _respuesta(_html_detalle(MONTO_PLANO, con_imagen_principal=False))

    items = list(spider.parse_producto(respuesta, libro_id=7))

    assert items[0]["url_imagen"] == "https://cuspide.com/img/eco-grande.jpg"


def test_parse_producto_sin_libro_id_no_genera_item() -> None:
    """Un título que no está en el catálogo no se puede persistir."""
    spider = CuspideSpider(catalogo=[])
    respuesta = _respuesta(_html_detalle(MONTO_PLANO))

    assert list(spider.parse_producto(respuesta, libro_id=None)) == []


def test_pipeline_persiste_el_precio_web(conexion: ConexionDB) -> None:
    libro_id = _crear_libro_de_prueba(conexion)
    spider = CuspideSpider(catalogo=[])
    pipeline = PrecioWebPipeline(conexion=conexion)
    pipeline.open_spider(spider)
    item = CuspideItem(
        libro_id=libro_id,
        titulo="El eco del silencio",
        autor="Marina Solís",
        precio=55999.0,
        url_imagen="https://cuspide.com/img/eco.jpg",
        formas_pago="Tarjeta de crédito, Transferencia",
        descripcion="Una sinopsis que resume la novela.",
        url=URL_DETALLE,
    )

    resultado = pipeline.process_item(item, spider)
    pipeline.close_spider(spider)

    assert resultado is item
    registros = RepoPrecioWebSQL(conexion).leer_todos()
    assert len(registros) == 1
    assert registros[0].libro_id == libro_id
    assert registros[0].titulo == "El eco del silencio"
    assert registros[0].precio == 55999.0
    assert registros[0].url == URL_DETALLE
    assert registros[0].fecha_extraccion == fecha_argentina(datetime.now())


def test_pipeline_trunca_la_descripcion_al_largo_de_la_columna(
    conexion: ConexionDB,
) -> None:
    """En PostgreSQL la columna es String(5000): no se puede desbordar."""
    libro_id = _crear_libro_de_prueba(conexion)
    spider = CuspideSpider(catalogo=[])
    pipeline = PrecioWebPipeline(conexion=conexion)
    pipeline.open_spider(spider)
    item = CuspideItem(
        libro_id=libro_id,
        titulo="El eco del silencio",
        precio=55999.0,
        url_imagen="https://cuspide.com/img/eco.jpg",
        formas_pago="Transferencia",
        descripcion="x" * 6000,
        url=URL_DETALLE,
    )

    pipeline.process_item(item, spider)
    pipeline.close_spider(spider)

    registros = RepoPrecioWebSQL(conexion).leer_todos()
    assert len(registros[0].descripcion) == 5000


def test_obtener_catalogo_desde_csv() -> None:
    catalogo = obtener_catalogo("csv")

    assert catalogo
    assert set(catalogo[0]) == {"titulo", "libro_id"}
    assert isinstance(catalogo[0]["libro_id"], int)
    assert catalogo[0]["titulo"]


def test_obtener_catalogo_manual_resuelve_el_id_por_titulo(
    conexion: ConexionDB,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    libro_id = _crear_libro_de_prueba(conexion)
    monkeypatch.setattr(runner, "ConexionDB", lambda: conexion)

    titulos = ["El eco del silencio", "Un título que no está"]

    catalogo = obtener_catalogo("manual", titulos)

    assert catalogo == [
        {"titulo": "El eco del silencio", "libro_id": libro_id},
        {"titulo": "Un título que no está", "libro_id": None},
    ]


def test_obtener_catalogo_rechaza_un_origen_desconocido() -> None:
    with pytest.raises(ValueError):
        obtener_catalogo("otro")
