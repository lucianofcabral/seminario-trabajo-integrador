"""Tests de la capa de servicios (reglas de negocio sobre SQL)."""

import csv
import os
from datetime import date

import pytest

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    TipoCotizacion,
)
from book_manager.services import services as svc
from book_manager.services.services import (
    ServicioCotizacionDolar,
    ServicioGenero,
    ServicioLibro,
    ServicioListaPrecios,
)


def _editorial() -> Editorial:
    return Editorial(
        proveedor="Editorial Alba",
        pais="Argentina",
        provincia="Buenos Aires",
        localidad="CABA",
        domicilio="Av. Siempre Viva 123",
        telefono="1145678901",
        email="contacto@editorialalba.com",
        responsable="Juan Pérez",
    )


def test_crear_libro_exige_editorial_y_genero(conexion):
    servicio = ServicioLibro(conexion=conexion)
    libro = Libro(
        isbn="9780306406157",
        titulo="El eco del silencio",
        autor="Marina Solís",
        editorial=_editorial(),
        genero=Genero(genero="Ficción"),
    )

    with pytest.raises(ValueError):
        servicio.crear(libro)


def test_eliminar_genero_en_uso(conexion_poblada):
    servicio = ServicioGenero(conexion=conexion_poblada)
    genero = servicio.leer_todos()[0]

    with pytest.raises(ValueError):
        servicio.eliminar(genero.genero)


def test_eliminar_libro_borra_stock_y_precios(conexion_poblada):
    servicio = ServicioLibro(conexion=conexion_poblada)
    libro = servicio.leer_todos()[0]
    isbn = libro.isbn

    assert servicio.stock_de(isbn) is not None
    assert servicio.precios_de(isbn)

    assert servicio.eliminar(isbn) is True

    assert servicio.stock_de(isbn) is None
    assert servicio.precios_de(isbn) == []


def test_obtener_cotizaciones_registra_compra_y_venta(conexion, monkeypatch):
    """Descarga de la API y registra compra y venta de cada tipo."""
    servicio = ServicioCotizacionDolar(conexion=conexion)
    monkeypatch.setattr(
        svc,
        "_descargar_cotizaciones",
        lambda: [
            {
                "casa": "blue",
                "compra": 1200.0,
                "venta": 1240.0,
                "fechaActualizacion": "2026-01-01T00:00:00-03:00",
            },
            {
                "casa": "oficial",
                "compra": 1100.0,
                "venta": 1115.0,
                "fechaActualizacion": "2026-01-01T00:00:00-03:00",
            },
        ],
    )

    registradas = servicio.obtener_cotizaciones()

    assert len(registradas) == 2
    blue = servicio.cotizacion_del_dia("Blue", date(2026, 1, 1))
    oficial = servicio.cotizacion_del_dia("Oficial", date(2026, 1, 1))
    assert blue is not None
    assert oficial is not None
    assert (blue.valor_compra, blue.valor_venta) == (1200.0, 1240.0)
    assert (oficial.valor_compra, oficial.valor_venta) == (1100.0, 1115.0)


def test_fecha_de_usa_hora_argentina():
    """Un instante de las 22 h de Argentina (01 h UTC) cuenta como ese día."""
    item = {"fechaActualizacion": "2026-10-14T01:00:00.000Z"}
    assert svc._fecha_de(item) == date(2026, 10, 13)


def test_obtener_cotizaciones_ignora_casas_sin_compra_o_venta(conexion, monkeypatch):
    servicio = ServicioCotizacionDolar(conexion=conexion)
    monkeypatch.setattr(
        svc,
        "_descargar_cotizaciones",
        lambda: [
            {
                "casa": "blue",
                "compra": 100,
                "venta": None,
                "fechaActualizacion": "2026-01-01T12:00:00Z",
            },
            {
                "casa": "oficial",
                "compra": None,
                "venta": 10,
                "fechaActualizacion": "2026-01-01T12:00:00Z",
            },
            {
                "casa": "desconocida",
                "compra": 10,
                "venta": 10,
                "fechaActualizacion": "2026-01-01T12:00:00Z",
            },
        ],
    )

    assert servicio.obtener_cotizaciones() == []


def test_obtener_cotizaciones_es_idempotente(conexion, monkeypatch):
    servicio = ServicioCotizacionDolar(conexion=conexion)
    monkeypatch.setattr(
        svc,
        "_descargar_cotizaciones",
        lambda: [
            {
                "casa": "blue",
                "compra": 1515,
                "venta": 1540,
                "fechaActualizacion": "2026-10-12T20:56:00.000Z",
            }
        ],
    )

    assert len(servicio.obtener_cotizaciones()) == 1
    assert servicio.obtener_cotizaciones() == []


def test_api_url_se_carga_del_env_versionado():
    from book_manager.utils import cargar_entorno

    cargar_entorno()
    assert os.environ["API_URL"] == "https://dolarapi.com/v1/dolares"


def _con_cotizaciones(conexion_poblada) -> None:
    """Registra dos cotizaciones recientes para los tests de reportes."""
    servicio = ServicioCotizacionDolar(conexion=conexion_poblada)
    for tipo, valor in (("Oficial", 1500.0), ("Blue", 1600.0)):
        servicio.crear(
            CotizacionDolar(
                tipo_cotizacion=TipoCotizacion(tipo=tipo),
                fecha=date.today(),
                valor_compra=valor - 10.0,
                valor_venta=valor,
            )
        )


def test_lista_bimonetaria_usa_la_ultima_cotizacion(conexion_poblada):
    _con_cotizaciones(conexion_poblada)
    servicio = ServicioListaPrecios(conexion=conexion_poblada)

    cotizacion, filas = servicio.lista_bimonetaria("Blue")

    assert cotizacion.fecha == date.today()
    assert len(filas) == 30
    assert all(fila.ars == round(fila.usd * 1600.0, 2) for fila in filas)


def test_lista_bimonetaria_tipo_sin_cotizaciones(conexion):
    with pytest.raises(ValueError):
        ServicioListaPrecios(conexion=conexion).lista_bimonetaria("Blue")


def test_exportar_una_columna_por_tipo(conexion_poblada, tmp_path):
    _con_cotizaciones(conexion_poblada)
    servicio = ServicioListaPrecios(conexion=conexion_poblada)
    ruta = tmp_path / "precios.csv"

    usadas = servicio.exportar_csv(ruta)

    filas = list(csv.DictReader(ruta.open(encoding="utf-8")))
    tipos = [c.tipo_cotizacion.tipo for c in usadas]
    assert {"Blue", "Oficial"} <= set(tipos)
    assert len(filas) == 30
    primera = filas[0]
    assert float(primera["ARS Blue"]) == round(float(primera["valor"]) * 1600.0, 2)


def test_precio_en_pesos_se_convierte_a_dolares():
    libro = Libro(
        isbn="9780306406157",
        titulo="El eco del silencio",
        autor="Marina Solís",
        editorial=_editorial(),
        genero=Genero(genero="Ficción"),
    )
    precio = Precio(libro=libro, moneda=Moneda(codigo="ARS", nombre="peso"), valor=3000)
    otro = Precio(libro=libro, moneda=Moneda(codigo="EUR", nombre="euro"), valor=10)

    assert svc._usd_y_ars(precio, 1500) == (2, 3000)
    assert svc._usd_y_ars(otro, 1500) is None
