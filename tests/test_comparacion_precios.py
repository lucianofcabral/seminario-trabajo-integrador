"""Tests de la comparación de precios y las alertas CSV (Sprint 3, Ejercicio 04).

No usan red: la cotización del dólar y los precios web se cargan en la base de
prueba (SQLite) y el crawl del scraper se reemplaza por un proceso falso.
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from typing import Any, ClassVar

import pytest
from sqlalchemy import select

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
    CotizacionDolar,
    Moneda,
    Precio,
    TipoCotizacion,
)
from book_manager.models import models as m
from book_manager.repositories.sql_repository import RepoPrecioWebSQL
from book_manager.scraper import runner
from book_manager.services.services import (
    COLUMNAS_ALERTAS,
    ServicioComparacionPrecios,
    ServicioCotizacionDolar,
    ServicioLibro,
    ServicioPrecio,
)

HOY = date(2026, 1, 5)
TASA_OFICIAL = 1000.0


def _proxima_fecha(conexion: ConexionDB) -> date:
    """Fecha posterior a la última cotización oficial cargada en la base.

    Los datos de ejemplo traen un año de cotizaciones con fechas futuras, así
    que la cotización «vigente» del test se calcula a partir de la última.
    """
    ultima = ServicioCotizacionDolar(conexion=conexion).ultima("Oficial")
    return (ultima.fecha if ultima else HOY) + timedelta(days=1)


def _oficial(
    conexion: ConexionDB, valor_venta: float, fecha: date | None = None
) -> date:
    """Registra la cotización del dólar oficial y devuelve su fecha."""
    fecha = fecha or _proxima_fecha(conexion)
    ServicioCotizacionDolar(conexion=conexion).crear(
        CotizacionDolar(
            tipo_cotizacion=TipoCotizacion(tipo="Oficial"),
            fecha=fecha,
            valor_compra=valor_venta - 10.0,
            valor_venta=valor_venta,
        )
    )
    return fecha


def _libros_con_precio(
    conexion: ConexionDB, cantidad: int = 2
) -> list[tuple[str, float]]:
    """Devuelve (isbn, precio en USD) de los primeros libros del catálogo."""
    servicio_precio = ServicioPrecio(conexion=conexion)
    return [
        (libro.isbn, servicio_precio.leer_por_libro(libro.isbn)[0].valor)
        for libro in ServicioLibro(conexion=conexion).leer_todos()[:cantidad]
    ]


def _id_de(conexion: ConexionDB, isbn: str) -> int:
    with conexion.crear_sesion() as sesion:
        return sesion.scalar(select(m.Libro.id).where(m.Libro.isbn == isbn))


def _titulo_de(conexion: ConexionDB, isbn: str) -> str:
    """Título del catálogo interno del libro (el que va al CSV)."""
    libro = next(
        libro
        for libro in ServicioLibro(conexion=conexion).leer_todos()
        if libro.isbn == isbn
    )
    return libro.titulo


def _registrar_precio_web(
    conexion: ConexionDB,
    isbn: str,
    precio: float,
    fecha: date = HOY,
) -> m.PrecioWeb:
    """Inserta un precio web como el que deja el pipeline del scraper."""
    return RepoPrecioWebSQL(conexion).crear(
        m.PrecioWeb(
            libro_id=_id_de(conexion, isbn),
            titulo=f"El libro {isbn}",
            precio=precio,
            url_imagen="https://cuspide.com/img/eco.jpg",
            formas_pago="Transferencia",
            descripcion="Una sinopsis.",
            url=f"https://cuspide.com/libro/{isbn}/",
            fecha_extraccion=fecha,
        )
    )


def _servicio(conexion: ConexionDB) -> ServicioComparacionPrecios:
    return ServicioComparacionPrecios(conexion=conexion)


def _leer_csv(ruta: Any) -> list[dict[str, str]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


# --- T1: comparación (conversión USD→ARS + diferencia con signo) ---


def test_comparar_convierte_el_precio_interno_a_pesos_oficiales(
    conexion_poblada: ConexionDB,
) -> None:
    _oficial(conexion_poblada, TASA_OFICIAL)
    isbn, usd = _libros_con_precio(conexion_poblada, 1)[0]
    _registrar_precio_web(conexion_poblada, isbn, usd * TASA_OFICIAL + 500.0)

    comparaciones = _servicio(conexion_poblada).comparar()

    assert len(comparaciones) == 1
    comparacion = comparaciones[0]
    assert comparacion.isbn == isbn
    assert comparacion.precio_interno == round(usd * TASA_OFICIAL, 2)
    assert comparacion.precio_web == round(usd * TASA_OFICIAL + 500.0, 2)
    assert comparacion.diferencia == 500.0
    assert comparacion.fecha_extraccion == HOY


def test_comparar_con_dos_extracciones_el_mismo_dia_usa_la_ultima(
    conexion_poblada: ConexionDB,
) -> None:
    _oficial(conexion_poblada, TASA_OFICIAL)
    isbn, _ = _libros_con_precio(conexion_poblada, 1)[0]
    _registrar_precio_web(conexion_poblada, isbn, 100.0, HOY)
    _registrar_precio_web(conexion_poblada, isbn, 200.0, HOY)

    comparaciones = _servicio(conexion_poblada).comparar()

    assert len(comparaciones) == 1
    assert comparaciones[0].precio_web == 200.0


def test_comparar_usa_la_ultima_cotizacion_oficial(
    conexion_poblada: ConexionDB,
) -> None:
    _oficial(conexion_poblada, 1200.0)
    _oficial(conexion_poblada, 500.0)
    isbn, usd = _libros_con_precio(conexion_poblada, 1)[0]
    _registrar_precio_web(conexion_poblada, isbn, 1_000_000.0)

    comparacion = _servicio(conexion_poblada).comparar()[0]

    assert comparacion.precio_interno == round(usd * 500.0, 2)


def test_comparar_usa_el_ultimo_precio_web_de_cada_libro(
    conexion_poblada: ConexionDB,
) -> None:
    _oficial(conexion_poblada, TASA_OFICIAL)
    isbn, _ = _libros_con_precio(conexion_poblada, 1)[0]
    _registrar_precio_web(conexion_poblada, isbn, 1.0, HOY - timedelta(days=1))
    _registrar_precio_web(conexion_poblada, isbn, 2.0, HOY)

    comparaciones = _servicio(conexion_poblada).comparar()

    assert len(comparaciones) == 1
    assert comparaciones[0].precio_web == 2.0


def test_comparar_usa_el_precio_en_pesos_tal_cual(
    conexion_poblada: ConexionDB,
) -> None:
    """Un precio interno cargado en ARS no se convierte: se compara directo."""
    _oficial(conexion_poblada, TASA_OFICIAL)
    isbn, _ = _libros_con_precio(conexion_poblada, 1)[0]
    servicio_precio = ServicioPrecio(conexion=conexion_poblada)
    libro = next(
        libro
        for libro in ServicioLibro(conexion=conexion_poblada).leer_todos()
        if libro.isbn == isbn
    )
    servicio_precio.eliminar((isbn, "USD"))
    servicio_precio.crear(
        Precio(
            libro=libro,
            moneda=Moneda(codigo="ARS", nombre="peso argentino"),
            valor=50_000.0,
        )
    )
    _registrar_precio_web(conexion_poblada, isbn, 52_000.0)

    comparacion = _servicio(conexion_poblada).comparar()[0]

    assert comparacion.precio_interno == 50_000.0
    assert comparacion.diferencia == 2_000.0


def test_comparar_ignora_los_libros_sin_precio_web(
    conexion_poblada: ConexionDB,
) -> None:
    _oficial(conexion_poblada, TASA_OFICIAL)
    (isbn, _), _ = _libros_con_precio(conexion_poblada, 2)
    _registrar_precio_web(conexion_poblada, isbn, 10.0)

    comparaciones = _servicio(conexion_poblada).comparar()

    assert [c.isbn for c in comparaciones] == [isbn]


def test_comparar_sin_cotizacion_oficial_falla(conexion: ConexionDB) -> None:
    with pytest.raises(ValueError):
        _servicio(conexion).comparar()


# --- T2: umbral de alerta como parámetro ---


def test_alertas_incluye_solo_las_que_superan_el_umbral(
    conexion_poblada: ConexionDB,
) -> None:
    _oficial(conexion_poblada, TASA_OFICIAL)
    (isbn_grande, usd_grande), (isbn_chico, usd_chico) = _libros_con_precio(
        conexion_poblada, 2
    )
    _registrar_precio_web(
        conexion_poblada, isbn_grande, usd_grande * TASA_OFICIAL + 500
    )
    _registrar_precio_web(conexion_poblada, isbn_chico, usd_chico * TASA_OFICIAL + 100)

    alertas = _servicio(conexion_poblada).alertas(umbral=200.0)

    assert [a.isbn for a in alertas] == [isbn_grande]
    assert alertas[0].diferencia == 500.0


def test_alertas_usa_el_valor_absoluto_de_la_diferencia(
    conexion_poblada: ConexionDB,
) -> None:
    """Un precio web más barato que el interno también es una alerta."""
    _oficial(conexion_poblada, TASA_OFICIAL)
    isbn, usd = _libros_con_precio(conexion_poblada, 1)[0]
    _registrar_precio_web(conexion_poblada, isbn, usd * TASA_OFICIAL - 900)

    alertas = _servicio(conexion_poblada).alertas(umbral=500.0)

    assert [a.isbn for a in alertas] == [isbn]
    assert alertas[0].diferencia == -900.0


def test_alertas_no_incluye_la_diferencia_igual_al_umbral(
    conexion_poblada: ConexionDB,
) -> None:
    """La comparación es estricta: `abs(diferencia) > umbral`."""
    _oficial(conexion_poblada, TASA_OFICIAL)
    isbn, usd = _libros_con_precio(conexion_poblada, 1)[0]
    _registrar_precio_web(conexion_poblada, isbn, usd * TASA_OFICIAL + 500)

    assert _servicio(conexion_poblada).alertas(umbral=500.0) == []


def test_alertas_rechaza_un_umbral_negativo(conexion_poblada: ConexionDB) -> None:
    with pytest.raises(ValueError):
        _servicio(conexion_poblada).alertas(umbral=-1.0)


# --- T3: exportación del CSV de alertas ---


def test_exportar_alertas_escribe_cabecera_y_filas(
    conexion_poblada: ConexionDB,
    tmp_path: Any,
) -> None:
    _oficial(conexion_poblada, TASA_OFICIAL)
    isbn, usd = _libros_con_precio(conexion_poblada, 1)[0]
    _registrar_precio_web(conexion_poblada, isbn, usd * TASA_OFICIAL + 750)
    ruta = tmp_path / "alertas_precios.csv"

    alertas = _servicio(conexion_poblada).exportar_alertas_csv(umbral=100.0, ruta=ruta)

    assert len(alertas) == 1
    with ruta.open(encoding="utf-8", newline="") as archivo:
        cabecera = next(csv.reader(archivo))
    assert cabecera == COLUMNAS_ALERTAS
    assert COLUMNAS_ALERTAS == [
        "isbn",
        "titulo",
        "precio_interno",
        "precio_web",
        "diferencia",
        "fecha_extraccion",
    ]
    fila = _leer_csv(ruta)[0]
    assert fila["isbn"] == isbn
    assert fila["titulo"] == _titulo_de(conexion_poblada, isbn)
    assert float(fila["precio_interno"]) == round(usd * TASA_OFICIAL, 2)
    assert float(fila["precio_web"]) == round(usd * TASA_OFICIAL + 750, 2)
    assert float(fila["diferencia"]) == 750.0
    assert fila["fecha_extraccion"] == HOY.isoformat()


def test_exportar_alertas_sin_alertas_deja_solo_la_cabecera(
    conexion_poblada: ConexionDB,
    tmp_path: Any,
) -> None:
    _oficial(conexion_poblada, TASA_OFICIAL)
    isbn, usd = _libros_con_precio(conexion_poblada, 1)[0]
    _registrar_precio_web(conexion_poblada, isbn, usd * TASA_OFICIAL)
    ruta = tmp_path / "alertas_precios.csv"

    alertas = _servicio(conexion_poblada).exportar_alertas_csv(umbral=100.0, ruta=ruta)

    assert alertas == []
    assert ruta.read_text(encoding="utf-8").strip() == ",".join(COLUMNAS_ALERTAS)


def test_exportar_alertas_crea_la_carpeta_de_destino(
    conexion_poblada: ConexionDB,
    tmp_path: Any,
) -> None:
    _oficial(conexion_poblada, TASA_OFICIAL)
    ruta = tmp_path / "exports" / "alertas_precios.csv"

    _servicio(conexion_poblada).exportar_alertas_csv(umbral=0.0, ruta=ruta)

    assert ruta.exists()


# --- T4: integración con la ejecución del scraper ---


class _ProcesoFalso:
    """Reemplaza a `CrawlerProcess` para no salir a la red en los tests."""

    instancias: ClassVar[list[_ProcesoFalso]] = []

    def __init__(self, _settings: dict[str, Any]) -> None:
        self.crawls: list[dict[str, Any]] = []
        self.iniciado = False
        _ProcesoFalso.instancias.append(self)

    def crawl(self, spider: Any, **kwargs: Any) -> None:
        self.crawls.append({"spider": spider, **kwargs})

    def start(self) -> None:
        self.iniciado = True


@pytest.fixture
def crawl_falso(monkeypatch: pytest.MonkeyPatch) -> type[_ProcesoFalso]:
    _ProcesoFalso.instancias = []
    monkeypatch.setattr(runner, "CrawlerProcess", _ProcesoFalso)
    return _ProcesoFalso


def test_ejecutar_scraping_genera_el_csv_de_alertas(
    conexion_poblada: ConexionDB,
    crawl_falso: type[_ProcesoFalso],
    tmp_path: Any,
) -> None:
    _oficial(conexion_poblada, TASA_OFICIAL)
    isbn, usd = _libros_con_precio(conexion_poblada, 1)[0]
    _registrar_precio_web(conexion_poblada, isbn, usd * TASA_OFICIAL + 800)
    catalogo = [
        {"titulo": f"El libro {isbn}", "libro_id": _id_de(conexion_poblada, isbn)}
    ]
    ruta = tmp_path / "alertas_precios.csv"

    alertas = runner.ejecutar_scraping(
        catalogo, umbral=100.0, ruta_alertas=ruta, conexion=conexion_poblada
    )

    proceso = crawl_falso.instancias[0]
    assert proceso.iniciado is True
    assert proceso.crawls[0]["catalogo"] == catalogo
    assert alertas is not None
    assert [a.isbn for a in alertas] == [isbn]
    assert _leer_csv(ruta)[0]["isbn"] == isbn


def test_ejecutar_scraping_sin_alertas_igual_deja_el_csv(
    conexion_poblada: ConexionDB,
    crawl_falso: type[_ProcesoFalso],
    tmp_path: Any,
) -> None:
    """S2: cada ejecución con umbral deja el archivo de alertas descargable."""
    _oficial(conexion_poblada, TASA_OFICIAL)
    ruta = tmp_path / "alertas_precios.csv"

    alertas = runner.ejecutar_scraping(
        [], umbral=100.0, ruta_alertas=ruta, conexion=conexion_poblada
    )

    assert alertas == []
    assert _leer_csv(ruta) == []
    assert ruta.read_text(encoding="utf-8").strip() == ",".join(COLUMNAS_ALERTAS)


def test_ejecutar_scraping_sin_umbral_no_genera_alertas(
    conexion_poblada: ConexionDB,
    crawl_falso: type[_ProcesoFalso],
    tmp_path: Any,
) -> None:
    _oficial(conexion_poblada, TASA_OFICIAL)
    isbn, usd = _libros_con_precio(conexion_poblada, 1)[0]
    _registrar_precio_web(conexion_poblada, isbn, usd * TASA_OFICIAL + 800)
    ruta = tmp_path / "alertas_precios.csv"

    alertas = runner.ejecutar_scraping([], ruta_alertas=ruta, conexion=conexion_poblada)

    assert alertas is None
    assert not ruta.exists()
    assert crawl_falso.instancias[0].iniciado is True


def test_ejecutar_scraping_usa_el_archivo_de_alertas_por_defecto(
    conexion_poblada: ConexionDB,
    crawl_falso: type[_ProcesoFalso],
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sin ruta explícita, el CSV va a `exports/alertas_precios.csv`."""
    _oficial(conexion_poblada, TASA_OFICIAL)
    ruta = tmp_path / "exports" / "alertas_precios.csv"
    monkeypatch.setattr(runner, "ARCHIVO_ALERTAS", ruta)

    runner.ejecutar_scraping([], umbral=100.0, conexion=conexion_poblada)

    assert ruta.exists()
    assert ruta.name == "alertas_precios.csv"
