"""Puertos (interfaces) de repositorio.

Los repositorios identifican las entidades por su clave natural, no por un id de
base de datos. `actualizar` y `eliminar` reciben esa clave para localizar el
registro; `crear` valida la unicidad de la clave en la implementación.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    EntidadBase,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)


class IRepositorio[T: EntidadBase](ABC):
    """Contrato CRUD genérico. La clave natural varía según la entidad."""

    @abstractmethod
    def crear(self, entidad: T) -> T:
        """Crea una entidad. Lanza ValueError si repite su clave natural."""
        ...

    @abstractmethod
    def leer_todos(self) -> list[T]:
        """Devuelve todas las entidades."""
        ...

    @abstractmethod
    def actualizar(self, clave: Any, entidad: T) -> T:
        """Reemplaza el registro identificado por `clave` con los datos nuevos."""
        ...

    @abstractmethod
    def eliminar(self, clave: Any) -> bool:
        """Elimina el registro identificado por `clave`. True si existía."""
        ...


class IRepositorioLibro(IRepositorio[Libro]):
    """Contrato para libros. Clave natural: ISBN."""

    @abstractmethod
    def leer_por_isbn(self, isbn: str) -> Libro | None:
        """Lee un libro por su ISBN, o None si no existe."""
        ...

    @abstractmethod
    def leer_por_editorial(self, proveedor: str) -> list[Libro]:
        """Lee los libros de una editorial (por proveedor)."""
        ...

    @abstractmethod
    def leer_por_genero(self, genero: str) -> list[Libro]:
        """Lee los libros de un género (por nombre)."""
        ...


class IRepositorioGenero(IRepositorio[Genero]):
    """Contrato para géneros. Clave natural: nombre del género."""

    @abstractmethod
    def leer_por_nombre(self, nombre: str) -> Genero | None:
        """Lee un género por su nombre exacto, o None si no existe."""
        ...

    @abstractmethod
    def leer_por_cadena(self, cadena: str) -> list[Genero]:
        """Busca géneros cuyo nombre contenga la cadena (sin distinguir mayúsculas)."""
        ...


class IRepositorioEditorial(IRepositorio[Editorial]):
    """Contrato para editoriales. Clave natural: proveedor."""

    @abstractmethod
    def leer_por_proveedor(self, proveedor: str) -> Editorial | None:
        """Lee una editorial por su proveedor, o None si no existe."""
        ...


class IRepositorioMoneda(IRepositorio[Moneda]):
    """Contrato para monedas. Clave natural: código ISO 4217."""

    @abstractmethod
    def leer_por_codigo(self, codigo: str) -> Moneda | None:
        """Lee una moneda por su código, o None si no existe."""
        ...


class IRepositorioStock(IRepositorio[Stock]):
    """Contrato para stock. Clave natural: ISBN del libro."""

    @abstractmethod
    def leer_por_libro(self, isbn: str) -> Stock | None:
        """Lee el stock de un libro por su ISBN, o None si no tiene."""
        ...


class IRepositorioPrecio(IRepositorio[Precio]):
    """Contrato para precios. Clave natural: (ISBN del libro, código de moneda)."""

    @abstractmethod
    def leer_por_libro(self, isbn: str) -> list[Precio]:
        """Lee todos los precios de un libro, uno por moneda."""
        ...

    @abstractmethod
    def leer_por_moneda(self, codigo: str) -> list[Precio]:
        """Lee todos los precios expresados en una moneda."""
        ...

    @abstractmethod
    def leer_por_libro_y_moneda(self, isbn: str, codigo: str) -> Precio | None:
        """Lee el precio de un libro en una moneda, o None si no existe."""
        ...


class IRepositorioTipoCotizacion(IRepositorio[TipoCotizacion]):
    """Contrato para tipos de cotización. Clave natural: nombre del tipo."""

    @abstractmethod
    def leer_por_tipo(self, tipo: str) -> TipoCotizacion | None:
        """Lee un tipo de cotización por su nombre, o None si no existe."""
        ...


class IRepositorioCotizacionDolar(IRepositorio[CotizacionDolar]):
    """Contrato para cotizaciones. Clave natural: (tipo, fecha)."""

    @abstractmethod
    def leer_por_tipo_y_fecha(
        self, tipo: str, fecha: date
    ) -> CotizacionDolar | None:
        """Lee la cotización de un tipo en una fecha, o None si no existe."""
        ...

    @abstractmethod
    def leer_historico_por_tipo(self, tipo: str) -> list[CotizacionDolar]:
        """Lee el histórico de cotizaciones de un tipo, ordenado por fecha."""
        ...
