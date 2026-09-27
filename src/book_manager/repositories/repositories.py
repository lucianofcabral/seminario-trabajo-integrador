from abc import ABC, abstractmethod
from datetime import date

from pydantic import BaseModel

from book_manager.entities.entities import (
    Cotizacion,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)


class IRepositorio[T: BaseModel](ABC):
    """Interfaz para repositorios que manejan entidades con operaciones CRUD básicas."""

    @abstractmethod
    def crear(self, entidad: T) -> T | None:
        """Crea una nueva entidad en el repositorio.

        Args:
            entidad (T): La entidad a crear.

        Returns:
            T: La entidad creada.

        Raises:
            ValueError: Si ya existe una entidad con el mismo ID.
        """
        ...

    @abstractmethod
    def leer_por_id(self, entidad_id: int) -> T | None:
        """Lee una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a leer.

        Returns:
            Optional[T]: La entidad si se encuentra, None en caso contrario.
        """
        ...

    @abstractmethod
    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente en el repositorio.

        Args:
            entidad (T): La entidad a actualizar (debe tener un ID existente).

        Returns:
            T: La entidad actualizada.

        Raises:
            ValueError: Si no se encuentra la entidad para actualizar.
        """
        ...

    @abstractmethod
    def eliminar(self, entidad_id: int) -> bool:
        """Elimina una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a eliminar.

        Returns:
            bool: True si la entidad fue eliminada, False si no se encontró.
        """
        ...

    @abstractmethod
    def leer_todos(self) -> list[T]:
        """Lee todas las entidades del repositorio.

        Returns:
            list[T]: Una lista con todas las entidades.
        """
        ...


class IRepositorioMoneda(IRepositorio[Moneda]):
    """Interfaz CRUD para monedas."""

    @abstractmethod
    def leer_por_codigo(self, codigo: str) -> Moneda | None: ...


class IRepositorioGenero(IRepositorio[Genero]):
    """Interfaz CRUD para géneros de libros."""

    @abstractmethod
    def leer_por_cadena(self, cadena: str) -> list[Genero]: ...


class IRepositorioEditorial(IRepositorio[Editorial]):
    """Interfaz CRUD para editoriales."""

    @abstractmethod
    def leer_por_parametros(self, kwargs: dict) -> list[Editorial]: ...

    @abstractmethod
    def leer_por_proveedor(self, proveedor: str) -> Editorial | None: ...


class IRepositorioLibro(IRepositorio[Libro]):
    """Interfaz CRUD para libros."""


class IRepositorioStock(IRepositorio[Stock]):
    """Interfaz CRUD para stock."""

    @abstractmethod
    def leer_por_libro_id(self, libro_id: int) -> Stock | None: ...

    @abstractmethod
    def modificar_stock(self, libro_id: int, existencia: int) -> None: ...


class IRepositorioPrecio(IRepositorio[Precio]):
    """Interfaz CRUD para precios."""

    @abstractmethod
    def leer_por_libro_id(self, libro_id: int) -> list[Precio]: ...

    @abstractmethod
    def modificar_precio(
        self, libro_id: int, moneda_id: int, valor: float
    ) -> Precio: ...

    @abstractmethod
    def leer_por_libro_id_moneda_id(
        self, libro_id: int, moneda_id: int
    ) -> Precio | None: ...


class IRepositorioTipoCotizacion(IRepositorio[TipoCotizacion]):
    """Interfaz CRUD para tipos de cotización."""

    @abstractmethod
    def leer_por_tipo(self, tipo: str) -> TipoCotizacion | None: ...


class IRepositorioCotizacion(IRepositorio[Cotizacion]):
    """Interfaz CRUD para cotización."""

    @abstractmethod
    def leer_cotizacion(
        self, tipo_cotizacion_id: int, fecha: date
    ) -> Cotizacion | None: ...
