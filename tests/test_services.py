"""Tests de la capa de servicios (reglas de negocio sobre SQL)."""

import os
from datetime import date

import pytest

from book_manager.entities.entities import Editorial, Genero, Libro
from book_manager.services import services as svc
from book_manager.services.services import (
    ServicioCotizacionDolar,
    ServicioGenero,
    ServicioLibro,
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


def test_obtener_cotizaciones_registra(conexion, monkeypatch):
    """Descarga de la API y registra una cotización por tipo."""
    servicio = ServicioCotizacionDolar(conexion=conexion)
    monkeypatch.setattr(
        svc,
        "_descargar_cotizaciones",
        lambda: [
            {
                "casa": "blue",
                "venta": 1240.0,
                "fechaActualizacion": "2026-01-01T00:00:00-03:00",
            },
            {
                "casa": "oficial",
                "venta": 1115.0,
                "fechaActualizacion": "2026-01-01T00:00:00-03:00",
            },
        ],
    )

    registradas = servicio.obtener_cotizaciones()

    assert len(registradas) == 2
    assert servicio.cotizacion_del_dia("Blue", date(2026, 1, 1)) is not None
    assert servicio.cotizacion_del_dia("Oficial", date(2026, 1, 1)) is not None


def test_fecha_de_usa_hora_argentina():
    """Un instante de las 22 h de Argentina (01 h UTC) cuenta como ese día."""
    item = {"fechaActualizacion": "2026-10-14T01:00:00.000Z"}
    assert svc._fecha_de(item) == date(2026, 10, 13)


def test_obtener_cotizaciones_ignora_casas_sin_venta(conexion, monkeypatch):
    servicio = ServicioCotizacionDolar(conexion=conexion)
    monkeypatch.setattr(
        svc,
        "_descargar_cotizaciones",
        lambda: [
            {
                "casa": "blue",
                "venta": None,
                "fechaActualizacion": "2026-01-01T12:00:00Z",
            },
            {
                "casa": "desconocida",
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
