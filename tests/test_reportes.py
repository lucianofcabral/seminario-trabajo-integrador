"""Tests del reporte Excel de precios (Sprint 3, Ejercicio 05).

El reporte reutiliza la comparación del Ejercicio 04 y la vuelca a un `.xlsx`
con openpyxl. Los tests unitarios inyectan una comparación falsa; el test de
integración arma los datos en SQLite para verificar que el servicio lee de la
base y escribe todos los libros con precio web (no solo las alertas).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from openpyxl import load_workbook
from sqlalchemy import select

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import CotizacionDolar, TipoCotizacion
from book_manager.models import models as m
from book_manager.reportes.reportes import COLUMNAS_REPORTE, ServicioReporte
from book_manager.repositories.sql_repository import RepoPrecioWebSQL
from book_manager.services.services import (
    ComparacionPrecio,
    ServicioCotizacionDolar,
    ServicioLibro,
    ServicioPrecio,
)

HOY = date(2026, 1, 5)
TASA_OFICIAL = 1000.0


class _ComparacionFalsa:
    """Reemplaza a `ServicioComparacionPrecios` en los tests unitarios."""

    def __init__(self, comparaciones: list[ComparacionPrecio]) -> None:
        self._comparaciones = comparaciones

    def comparar(self) -> list[ComparacionPrecio]:
        return self._comparaciones


def _comparacion(
    *,
    isbn: str = "978-987-1",
    titulo: str = "Cien años de soledad",
    precio_interno: float = 23_990.0,
    precio_web: float = 25_990.0,
    diferencia: float = 2_000.0,
    fecha: date = HOY,
) -> ComparacionPrecio:
    return ComparacionPrecio(
        isbn=isbn,
        titulo=titulo,
        precio_interno=precio_interno,
        precio_web=precio_web,
        diferencia=diferencia,
        fecha_extraccion=fecha,
    )


def _leer_filas(ruta: Any) -> list[tuple]:
    """Devuelve las filas del `.xlsx` como tuplas (sin la cabecera)."""
    libro = load_workbook(ruta)
    hoja = libro.active
    return list(hoja.iter_rows(values_only=True))


# --- T1: el reporte vuelca la comparación a Excel ---


def test_generar_reporte_escribe_cabecera_y_filas(tmp_path: Any) -> None:
    servicio = ServicioReporte(servicio_comparacion=_ComparacionFalsa([_comparacion()]))
    ruta = tmp_path / "reporte_precios.xlsx"

    resultado = servicio.generar_reporte(ruta)

    assert len(resultado) == 1
    filas = _leer_filas(ruta)
    assert filas[0] == tuple(COLUMNAS_REPORTE)
    assert COLUMNAS_REPORTE == [
        "Libro",
        "Precio interno",
        "Precio web",
        "Diferencia",
        "Fecha de extracción",
    ]
    assert filas[1] == (
        "Cien años de soledad",
        23_990.0,
        25_990.0,
        2_000.0,
        "2026-01-05",
    )


def test_generar_reporte_con_varios_libros_mantiene_el_orden(
    tmp_path: Any,
) -> None:
    comparaciones = [
        _comparacion(isbn="978-1", titulo="Libro A", diferencia=100.0),
        _comparacion(isbn="978-2", titulo="Libro B", diferencia=-50.0),
    ]
    servicio = ServicioReporte(servicio_comparacion=_ComparacionFalsa(comparaciones))
    ruta = tmp_path / "reporte_precios.xlsx"

    servicio.generar_reporte(ruta)

    filas = _leer_filas(ruta)
    assert [fila[0] for fila in filas[1:]] == ["Libro A", "Libro B"]
    assert filas[2][3] == -50.0  # la diferencia conserva el signo


def test_generar_reporte_sin_comparaciones_deja_solo_la_cabecera(
    tmp_path: Any,
) -> None:
    servicio = ServicioReporte(servicio_comparacion=_ComparacionFalsa([]))
    ruta = tmp_path / "reporte_precios.xlsx"

    resultado = servicio.generar_reporte(ruta)

    assert resultado == []
    filas = _leer_filas(ruta)
    assert len(filas) == 1
    assert filas[0] == tuple(COLUMNAS_REPORTE)


def test_generar_reporte_crea_la_carpeta_de_destino(tmp_path: Any) -> None:
    servicio = ServicioReporte(servicio_comparacion=_ComparacionFalsa([]))
    ruta = tmp_path / "reportes" / "reporte_precios.xlsx"

    servicio.generar_reporte(ruta)

    assert ruta.exists()


# --- T2: integración con la base ---


def _oficial(conexion: ConexionDB, valor_venta: float = TASA_OFICIAL) -> None:
    """Registra una cotización oficial posterior a las de ejemplo."""
    ultima = ServicioCotizacionDolar(conexion=conexion).ultima("Oficial")
    fecha = (ultima.fecha if ultima else HOY) + timedelta(days=1)
    ServicioCotizacionDolar(conexion=conexion).crear(
        CotizacionDolar(
            tipo_cotizacion=TipoCotizacion(tipo="Oficial"),
            fecha=fecha,
            valor_compra=valor_venta - 10.0,
            valor_venta=valor_venta,
        )
    )


def _registrar_precio_web(
    conexion: ConexionDB, isbn: str, precio: float, fecha: date = HOY
) -> None:
    with conexion.crear_sesion() as sesion:
        libro_id = sesion.scalar(select(m.Libro.id).where(m.Libro.isbn == isbn))
    RepoPrecioWebSQL(conexion).crear(
        m.PrecioWeb(
            libro_id=libro_id,
            titulo=f"El libro {isbn}",
            precio=precio,
            url_imagen="https://cuspide.com/img/eco.jpg",
            formas_pago="Transferencia",
            descripcion="Una sinopsis.",
            url=f"https://cuspide.com/libro/{isbn}/",
            fecha_extraccion=fecha,
        )
    )


def _libros_con_precio(conexion: ConexionDB, cantidad: int) -> list[tuple[str, float]]:
    servicio_precio = ServicioPrecio(conexion=conexion)
    return [
        (libro.isbn, servicio_precio.leer_por_libro(libro.isbn)[0].valor)
        for libro in ServicioLibro(conexion=conexion).leer_todos()[:cantidad]
    ]


def test_generar_reporte_incluye_todos_los_libros_con_precio_web(
    conexion_poblada: ConexionDB,
    tmp_path: Any,
) -> None:
    """El reporte vuelca todo el catálogo comparado, sin filtrar por umbral."""
    _oficial(conexion_poblada)
    (isbn_grande, usd_grande), (isbn_chico, usd_chico) = _libros_con_precio(
        conexion_poblada, 2
    )
    # Una diferencia grande y una chica: ambas deben aparecer en el reporte.
    _registrar_precio_web(
        conexion_poblada, isbn_grande, usd_grande * TASA_OFICIAL + 5000
    )
    _registrar_precio_web(conexion_poblada, isbn_chico, usd_chico * TASA_OFICIAL + 100)

    servicio = ServicioReporte(conexion=conexion_poblada)
    ruta = tmp_path / "reporte_precios.xlsx"

    resultado = servicio.generar_reporte(ruta)

    isbns = [comparacion.isbn for comparacion in resultado]
    assert set(isbns) == {isbn_grande, isbn_chico}
    filas = _leer_filas(ruta)
    assert len(filas) == 3  # cabecera + 2 libros
