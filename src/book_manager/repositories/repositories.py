from abc import ABC, abstractmethod
from datetime import date

from pydantic import BaseModel

from book_manager.entities.entities import (
    CotizacionDolar,
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
            T | None: La entidad creada. Si ya existe una entidad con los
            mismos campos únicos, devuelve la existente.
        """
        ...

    @abstractmethod
    def leer_por_id(self, entidad_id: int) -> T | None:
        """Lee una entidad del repositorio por su ID.

        Args:
            entidad_id (int): El ID de la entidad a leer.

        Returns:
            T | None: La entidad si se encuentra, None en caso contrario.
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
            entidad_id (int): El ID de la entidad a eliminar.

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
    def leer_por_codigo(self, codigo: str) -> Moneda | None:
        """Lee una moneda por su código ISO 4217.

        Args:
            codigo (str): Código de 3 letras, p. ej. "USD".

        Returns:
            Moneda | None: La moneda si se encuentra, None en caso contrario.
        """
        ...


class IRepositorioGenero(IRepositorio[Genero]):
    """Interfaz CRUD para géneros de libros."""

    @abstractmethod
    def leer_por_cadena(self, cadena: str) -> list[Genero]:
        """Busca géneros cuyo nombre contenga una cadena.

        Args:
            cadena (str): Texto a buscar, sin distinguir mayúsculas.

        Returns:
            list[Genero]: Los géneros que coinciden.
        """
        ...


class IRepositorioEditorial(IRepositorio[Editorial]):
    """Interfaz CRUD para editoriales."""

    @abstractmethod
    def leer_por_parametros(self, kwargs: dict) -> list[Editorial]:
        """Busca editoriales cuyos campos coincidan con los valores dados.

        Args:
            kwargs (dict): Pares campo -> valor a comparar por igualdad.

        Returns:
            list[Editorial]: Las editoriales que coinciden.

        Raises:
            KeyError: Si algún campo no existe en Editorial.
        """
        ...

    @abstractmethod
    def leer_por_proveedor(self, proveedor: str) -> Editorial | None:
        """Lee una editorial por el nombre de su proveedor.

        Args:
            proveedor (str): Nombre exacto del proveedor.

        Returns:
            Editorial | None: La editorial si se encuentra, None en caso contrario.
        """
        ...


class IRepositorioLibro(IRepositorio[Libro]):
    """Interfaz CRUD para libros."""


class IRepositorioStock(IRepositorio[Stock]):
    """Interfaz CRUD para stock."""

    @abstractmethod
    def leer_por_libro_id(self, libro_id: int) -> Stock | None:
        """Lee el registro de stock de un libro.

        Args:
            libro_id (int): El ID del libro.

        Returns:
            Stock | None: El stock si se encuentra, None en caso contrario.
        """
        ...

    @abstractmethod
    def modificar_stock(self, libro_id: int, existencia: int) -> None:
        """Reemplaza la existencia de un libro.

        Args:
            libro_id (int): El ID del libro.
            existencia (int): La nueva cantidad disponible.

        Raises:
            ValueError: Si el libro no tiene registro de stock.
        """
        ...


class IRepositorioPrecio(IRepositorio[Precio]):
    """Interfaz CRUD para precios."""

    @abstractmethod
    def leer_por_libro_id(self, libro_id: int) -> list[Precio]:
        """Lee todos los precios de un libro, uno por moneda.

        Args:
            libro_id (int): El ID del libro.

        Returns:
            list[Precio]: Los precios del libro.
        """
        ...

    @abstractmethod
    def modificar_precio(self, libro_id: int, moneda_id: int, valor: float) -> Precio:
        """Reemplaza el valor del precio de un libro en una moneda.

        Args:
            libro_id (int): El ID del libro.
            moneda_id (int): El ID de la moneda.
            valor (float): El nuevo valor.

        Returns:
            Precio: El precio actualizado.

        Raises:
            ValueError: Si no existe precio para ese libro y moneda.
        """
        ...

    @abstractmethod
    def leer_por_libro_id_moneda_id(
        self, libro_id: int, moneda_id: int
    ) -> Precio | None:
        """Lee el precio de un libro en una moneda.

        Args:
            libro_id (int): El ID del libro.
            moneda_id (int): El ID de la moneda.

        Returns:
            Precio | None: El precio si se encuentra, None en caso contrario.
        """
        ...


class IRepositorioTipoCotizacion(IRepositorio[TipoCotizacion]):
    """Interfaz CRUD para tipos de cotización."""

    @abstractmethod
    def leer_por_tipo(self, tipo: str) -> TipoCotizacion | None:
        """Lee un tipo de cotización por su nombre.

        Args:
            tipo (str): Nombre exacto del tipo, p. ej. "Blue".

        Returns:
            TipoCotizacion | None: El tipo si se encuentra, None en caso contrario.
        """
        ...


class IRepositorioCotizacion(IRepositorio[CotizacionDolar]):
    """Interfaz CRUD para cotización."""

    @abstractmethod
    def leer_cotizacion(
        self, tipo_cotizacion_id: int, fecha: date
    ) -> CotizacionDolar | None:
        """Lee la cotización de un tipo en una fecha.

        Args:
            tipo_cotizacion_id (int): El ID del tipo de cotización.
            fecha (date): La fecha de la cotización.

        Returns:
            CotizacionDolar | None: La cotización si se encuentra, None en caso contrario.
        """
        ...
