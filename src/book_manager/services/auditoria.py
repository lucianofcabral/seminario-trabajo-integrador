"""Auditoría del sistema (Sprint 3, Ejercicio 06).

El decorador `@auditar` registra en la tabla `auditoria` cada operación que
modifica el sistema (y las acciones del sistema) con su acción, fecha y un
resumen de los detalles. La auditoría usa un repositorio a nivel de módulo que
se configura una vez con `configurar_auditoria(conexion)`; si no se configura,
el decorador es un no-op (no rompe usos standalone ni tests sin auditoría).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any

from book_manager.database.connection import ConexionDB
from book_manager.models import models as m
from book_manager.repositories.sql_repository import RepoAuditoriaSQL
from book_manager.utils import fecha_argentina

# Repositorio activo de auditoría. None = auditoría desactivada (no-op).
_repo: RepoAuditoriaSQL | None = None


def configurar_auditoria(conexion: ConexionDB | None = None) -> RepoAuditoriaSQL:
    """Activa la auditoría sobre `conexion` y devuelve el repositorio.

    Se llama una vez al arrancar la aplicación (y en los tests, con la base de
    prueba). Sin esta llamada, las operaciones auditadas no escriben nada.
    """
    global _repo
    _repo = RepoAuditoriaSQL(conexion or ConexionDB())
    return _repo


def auditar(accion: str | Callable | None = None) -> Callable:
    """Decora una operación para registrar su ejecución en la auditoría.

    Se puede usar de dos formas: `@auditar` (deriva la acción del método y la
    clase del servicio, p. ej. `crear Libro`) o `@auditar("ejecutar_scraping")`
    para fijar la acción explícita (funciones sueltas y acciones del sistema).

    La entrada se registra solo si la operación termina sin error y solo si la
    auditoría está configurada; si no, no hace nada.
    """
    if callable(accion):
        return _decorar(accion, None)
    return lambda func: _decorar(func, accion)


def _decorar(func: Callable, accion: str | None) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        resultado = func(*args, **kwargs)
        _registrar(accion or _accion_por_defecto(func, args), args, kwargs)
        return resultado

    return wrapper


def _accion_por_defecto(func: Callable, args: tuple) -> str:
    """`crear Libro`, `actualizar Precio`, etc., a partir de la clase de `self`."""
    if not args:
        return func.__name__
    entidad = args[0].__class__.__name__.removeprefix("Servicio")
    return f"{func.__name__} {entidad}".strip()


def _registrar(accion: str, args: tuple, kwargs: dict) -> None:
    if _repo is None:
        return
    _repo.crear(
        m.Auditoria(
            accion=accion,
            fecha=fecha_argentina(datetime.now()),
            detalles=_detalles(args, kwargs),
        )
    )


def _detalles(args: tuple, kwargs: dict) -> str:
    """Resumen legible de los argumentos de la operación (sin `self`)."""
    partes = [_breve(arg) for arg in args[1:]]
    partes += [f"{clave}={_breve(valor)}" for clave, valor in kwargs.items()]
    return ", ".join(partes) or "—"


def _breve(valor: Any) -> str:
    """Representación corta de un valor para la columna `detalles`."""
    if valor is None:
        return "—"
    if isinstance(valor, str):
        return valor
    for clave in ("isbn", "codigo", "tipo", "proveedor", "genero", "titulo"):
        if hasattr(valor, clave):
            return f"{clave}={getattr(valor, clave)!r}"
    if isinstance(valor, (list, tuple)):
        return f"{len(valor)} elementos"
    if isinstance(valor, dict):
        return f"{len(valor)} claves"
    return str(valor)


class ServicioAuditoria:
    """Lee el historial de auditoría (lo consume el menú del Ejercicio 07)."""

    def __init__(
        self,
        repo: RepoAuditoriaSQL | None = None,
        conexion: ConexionDB | None = None,
    ) -> None:
        if repo is None:
            conexion = conexion or ConexionDB()
            repo = RepoAuditoriaSQL(conexion)
        self._repo = repo

    def leer_todos(self) -> list[m.Auditoria]:
        """Devuelve el historial completo, del más reciente al más antiguo."""
        return self._repo.leer_todos()
