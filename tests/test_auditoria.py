"""Tests del decorador de auditoría (Sprint 3, Ejercicio 06).

Sin red: se configura la auditoría sobre la base SQLite de prueba y se verifica
que las operaciones dejan una entrada con acción, fecha y detalles. También se
prueba que sin configurar el decorador es un no-op y que una operación que falla
no deja registro.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import Editorial, Genero, Libro
from book_manager.services import auditoria
from book_manager.services.auditoria import ServicioAuditoria
from book_manager.services.services import (
    ServicioGenero,
    ServicioLibro,
    ServicioStock,
)
from book_manager.utils import fecha_argentina


@pytest.fixture(autouse=True)
def _auditoria_limpia() -> Any:
    """Deja la auditoría sin configurar antes y después de cada test."""
    auditoria._repo = None
    yield
    auditoria._repo = None


@pytest.fixture
def auditoria_activa(conexion_poblada: ConexionDB) -> ConexionDB:
    """Configura la auditoría sobre la base poblada de prueba."""
    auditoria.configurar_auditoria(conexion_poblada)
    return conexion_poblada


def _historial(conexion: ConexionDB) -> list[Any]:
    return ServicioAuditoria(conexion=conexion).leer_todos()


def _crear_genero(conexion: ConexionDB, nombre: str = "Novela") -> Genero:
    return ServicioGenero(conexion=conexion).crear(Genero(genero=nombre))


# --- T1/T2: registro de acción, fecha y detalles ---


def test_crear_registra_accion_fecha_y_detalles(auditoria_activa: ConexionDB) -> None:
    _crear_genero(auditoria_activa)

    registros = _historial(auditoria_activa)
    assert len(registros) == 1
    registro = registros[0]
    assert registro.accion == "crear Genero"
    assert registro.fecha == fecha_argentina(datetime.now())
    assert registro.detalles == "genero='Novela'"


def test_eliminar_registra_la_accion(auditoria_activa: ConexionDB) -> None:
    ServicioGenero(conexion=auditoria_activa).crear(Genero(genero="Novela"))
    ServicioGenero(conexion=auditoria_activa).eliminar("Novela")

    registros = _historial(auditoria_activa)
    assert [r.accion for r in registros] == ["eliminar Genero", "crear Genero"]


def test_actualizar_registra_la_accion(auditoria_activa: ConexionDB) -> None:
    ServicioGenero(conexion=auditoria_activa).crear(Genero(genero="Novela"))
    ServicioGenero(conexion=auditoria_activa).actualizar(
        "Novela", Genero(genero="Novela")
    )

    registros = _historial(auditoria_activa)
    assert registros[0].accion == "actualizar Genero"


def test_modificar_stock_queda_auditado_como_actualizar(
    auditoria_activa: ConexionDB,
) -> None:
    """`modificar_stock` pasa por `actualizar`, así que se audita igual."""
    isbn = ServicioLibro(conexion=auditoria_activa).leer_todos()[0].isbn
    ServicioStock(conexion=auditoria_activa).modificar_stock(isbn, 5)

    registros = _historial(auditoria_activa)
    assert registros[0].accion == "actualizar Stock"
    assert isbn in registros[0].detalles


def test_obtener_una_operacion_que_falla_no_deja_registro(
    auditoria_activa: ConexionDB,
) -> None:
    """Un libro con editorial inexistente falla en `_validar` y no se audita."""
    libro = Libro(
        isbn="978-999-0001",
        titulo="Libro inválido",
        autor="Nadie",
        editorial=Editorial(
            proveedor="Editorial inexistente",
            pais="Argentina",
            provincia="Buenos Aires",
            localidad="La Plata",
            domicilio="Calle 1",
            telefono="111",
            email="a@b.com",
            responsable="Nadie",
        ),
        genero=Genero(genero="Novela"),
    )
    with pytest.raises(ValueError):
        ServicioLibro(conexion=auditoria_activa).crear(libro)

    assert _historial(auditoria_activa) == []


# --- T3: acciones del sistema ---


def test_generar_reporte_registra_accion(
    auditoria_activa: ConexionDB, tmp_path: Any
) -> None:
    class _ComparacionFalsa:
        def comparar(self) -> list:
            return []

    from book_manager.reportes.reportes import ServicioReporte

    ServicioReporte(servicio_comparacion=_ComparacionFalsa()).generar_reporte(
        tmp_path / "reporte.xlsx"
    )

    registros = _historial(auditoria_activa)
    assert registros[0].accion == "generar_reporte"


# --- no-op sin configurar ---


def test_sin_configurar_el_decorador_no_registra_ni_falla(
    conexion_poblada: ConexionDB,
) -> None:
    """Sin `configurar_auditoria`, las operaciones no escriben auditoría."""
    _crear_genero(conexion_poblada)

    assert _historial(conexion_poblada) == []
