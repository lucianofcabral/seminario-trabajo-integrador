"""Persistencia: interfaces de repositorio y su implementación sobre archivos CSV."""

import csv
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import date
from pathlib import Path
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
from book_manager.repositories.csv_config import csv_config
from book_manager.rutas import CSV_FOLDER_PATH

# --- interfaces ---


class IRepositorio[T: EntidadBase](ABC):
    """Interfaz para repositorios que manejan entidades con operaciones CRUD básicas."""

    @abstractmethod
    def crear(self, entidad: T) -> T:
        """Crea una nueva entidad en el repositorio y le asigna un ID.

        Args:
            entidad (T): La entidad a crear.

        Returns:
            T: La entidad creada, con su ID.

        Raises:
            ValueError: Si ya existe una entidad con los mismos campos únicos.
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
    def leer_todos(self) -> list[T]:
        """Lee todas las entidades del repositorio.

        Returns:
            list[T]: Una lista con todas las entidades.
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
            ValueError: Si no se encuentra la entidad o si el cambio repite los
                campos únicos de otra.
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


class IRepositorioLibro(IRepositorio[Libro]):
    """Interfaz CRUD para libros."""

    @abstractmethod
    def leer_por_isbn(self, isbn: str) -> Libro | None:
        """Lee un libro por su ISBN.

        Args:
            isbn (str): El ISBN del libro.

        Returns:
            Libro | None: El libro si se encuentra, None en caso contrario.
        """
        ...

    @abstractmethod
    def leer_por_editorial(self, editorial_id: int) -> list[Libro]:
        """Lee los libros de una editorial.

        Args:
            editorial_id (int): El ID de la editorial.

        Returns:
            list[Libro]: Los libros de esa editorial.
        """
        ...

    @abstractmethod
    def leer_por_genero(self, genero_id: int) -> list[Libro]:
        """Lee los libros de un género.

        Args:
            genero_id (int): El ID del género.

        Returns:
            list[Libro]: Los libros de ese género.
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
    def leer_por_parametros(self, kwargs: dict[str, Any]) -> list[Editorial]:
        """Busca editoriales cuyos campos coincidan con los valores dados.

        Args:
            kwargs (dict[str, Any]): Pares campo -> valor a comparar por igualdad.

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


class IRepositorioStock(IRepositorio[Stock]):
    """Interfaz CRUD para stock."""

    @abstractmethod
    def leer_por_libro(self, libro_id: int) -> Stock | None:
        """Lee un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock.

        Returns:
            Stock | None: El stock si se encuentra, None en caso contrario.
        """
        ...


class IRepositorioPrecio(IRepositorio[Precio]):
    """Interfaz CRUD para precios."""

    @abstractmethod
    def leer_por_libro(self, libro_id: int) -> list[Precio]:
        """Lee todos los precios de un libro, uno por moneda.

        Args:
            libro_id (int): El ID del libro.

        Returns:
            list[Precio]: Los precios del libro.
        """
        ...

    @abstractmethod
    def leer_por_moneda(self, moneda_id: int) -> list[Precio]:
        """Lee todos los precios expresados en una moneda.

        Args:
            moneda_id (int): El ID de la moneda.

        Returns:
            list[Precio]: Los precios en esa moneda.
        """
        ...

    @abstractmethod
    def leer_por_libro_y_moneda(self, libro_id: int, moneda_id: int) -> Precio | None:
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


class IRepositorioCotizacionDolar(IRepositorio[CotizacionDolar]):
    """Interfaz CRUD para cotizaciones del dólar."""

    @abstractmethod
    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: date
    ) -> CotizacionDolar | None:
        """Lee una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización (e.g., 'Oficial', 'Blue').
            fecha (date): La fecha de la cotización.

        Returns:
            CotizacionDolar | None: La cotización si se encuentra, None en caso
            contrario.
        """
        ...

    @abstractmethod
    def leer_historico_por_tipo(self, tipo_id: int) -> list[CotizacionDolar]:
        """Lee el histórico de cotizaciones para un tipo específico.

        Args:
            tipo_id (int): El ID del tipo de cotización.

        Returns:
            list[CotizacionDolar]: Las cotizaciones de ese tipo, ordenadas por fecha.
        """
        ...


# --- implementación sobre CSV ---


class RepoCSVBase[T: EntidadBase](IRepositorio[T]):
    """Implementación genérica de CRUD sobre un archivo CSV.

    Cada subclase indica la ruta del archivo, el modelo que guarda y qué campos
    no se pueden repetir entre registros.
    """

    ruta: Path
    tipo: type[T]
    unique_fields: tuple[str, ...] = ()

    def __init__(self) -> None:
        """Crea el archivo CSV con su cabecera si todavía no existe."""
        self._ruta = Path(self.ruta)
        self._modelo = self.tipo
        self._campos = list(self._modelo.model_fields)

        if not self._ruta.exists():
            self._ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(self._ruta, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, self._campos, **csv_config).writeheader()

    def crear(self, entidad: T) -> T:
        """Guarda una entidad nueva con el próximo ID disponible.

        Args:
            entidad: Entidad a crear; su ID se ignora.

        Returns:
            Una copia de la entidad con el ID asignado.

        Raises:
            ValueError: Si ya existe una entidad con los mismos campos únicos.
        """
        self._verificar_unicidad(entidad)
        nueva = entidad.model_copy(update={"id": self._proximo_id()})
        with open(self._ruta, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, self._campos, **csv_config).writerow(
                nueva.model_dump(mode="json")
            )
        return nueva

    def leer_por_id(self, entidad_id: int) -> T | None:
        """Lee una entidad por su ID.

        Args:
            entidad_id: ID de la entidad.

        Returns:
            La entidad encontrada, o None si no existe.
        """
        for fila in self._iterar():
            if int(fila["id"]) == entidad_id:
                return self._modelo.model_validate(fila)
        return None

    def leer_todos(self) -> list[T]:
        """Lee todas las entidades del archivo.

        Returns:
            Lista de entidades, en el orden del archivo.
        """
        return [self._modelo.model_validate(fila) for fila in self._iterar()]

    def actualizar(self, entidad: T) -> T:
        """Reemplaza los datos de una entidad existente.

        Args:
            entidad: Entidad con un ID existente y los datos nuevos.

        Returns:
            La entidad actualizada.

        Raises:
            ValueError: Si no existe una entidad con ese ID o si el cambio repite
                los campos únicos de otra.
        """
        entidades = self.leer_todos()
        if not any(e.id == entidad.id for e in entidades):
            raise ValueError(f"No se encontró el id {entidad.id}")
        self._verificar_unicidad(entidad)

        self._escribir_todos([entidad if e.id == entidad.id else e for e in entidades])
        return entidad

    def eliminar(self, entidad_id: int) -> bool:
        """Elimina una entidad por su ID.

        Args:
            entidad_id: ID de la entidad.

        Returns:
            True si se eliminó, False si no existía.
        """
        entidades = self.leer_todos()
        restantes = [e for e in entidades if e.id != entidad_id]
        if len(restantes) == len(entidades):
            return False
        self._escribir_todos(restantes)
        return True

    def _iterar(self) -> Iterator[dict[str, str]]:
        """Recorre las filas del CSV como diccionarios de texto."""
        with open(self._ruta, newline="", encoding="utf-8") as f:
            yield from csv.DictReader(f)

    def _escribir_todos(self, entidades: list[T]) -> None:
        """Reescribe el archivo completo con las entidades dadas."""
        with open(self._ruta, "w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, self._campos, **csv_config)
            escritor.writeheader()
            escritor.writerows(e.model_dump(mode="json") for e in entidades)

    def _verificar_unicidad(self, entidad: T) -> None:
        """Verifica que ninguna otra entidad tenga los mismos campos únicos.

        Raises:
            ValueError: Si otra entidad (con distinto ID) ya usa esos valores.
        """
        if not self.unique_fields:
            return
        valores = {campo: getattr(entidad, campo) for campo in self.unique_fields}
        for existente in self._leer_x_parametros(**valores):
            if existente.id != entidad.id:
                detalle = ", ".join(f"{c}={v}" for c, v in valores.items())
                raise ValueError(f"Ya existe un registro con {detalle}.")

    def _leer_x_parametros(self, **kwargs: Any) -> list[T]:
        """Lee las entidades cuyos campos coincidan con los dados.

        Args:
            kwargs: Pares campo -> valor a comparar por igualdad.

        Returns:
            Lista de entidades que coinciden.
        """
        return [
            entidad
            for entidad in self.leer_todos()
            if all(getattr(entidad, campo) == valor for campo, valor in kwargs.items())
        ]

    def _leer_x_parametros_unico(self, **kwargs: Any) -> T | None:
        """Lee la primera entidad cuyos campos coincidan con los dados, o None."""
        coincidencias = self._leer_x_parametros(**kwargs)
        return coincidencias[0] if coincidencias else None

    def _proximo_id(self) -> int:
        """Calcula el próximo ID disponible (el mayor existente + 1)."""
        ids = [int(fila["id"]) for fila in self._iterar()]
        return max(ids, default=0) + 1


class RepoLibroCSV(RepoCSVBase[Libro], IRepositorioLibro):
    """Implementación de CRUD para libros en CSV."""

    ruta = CSV_FOLDER_PATH / "libro.csv"
    tipo = Libro
    unique_fields = ("isbn",)

    def leer_por_isbn(self, isbn: str) -> Libro | None:
        """Lee un libro por su ISBN, o None si no existe."""
        return self._leer_x_parametros_unico(isbn=isbn)

    def leer_por_editorial(self, editorial_id: int) -> list[Libro]:
        """Lee los libros de una editorial."""
        return self._leer_x_parametros(editorial_id=editorial_id)

    def leer_por_genero(self, genero_id: int) -> list[Libro]:
        """Lee los libros de un género."""
        return self._leer_x_parametros(genero_id=genero_id)


class RepoGeneroCSV(RepoCSVBase[Genero], IRepositorioGenero):
    """Implementación de CRUD para géneros en CSV."""

    ruta = CSV_FOLDER_PATH / "genero.csv"
    tipo = Genero
    unique_fields = ("genero",)

    def leer_por_cadena(self, cadena: str) -> list[Genero]:
        """Lee los géneros que contienen la cadena, sin distinguir mayúsculas."""
        cadena = cadena.lower()
        return [g for g in self.leer_todos() if cadena in g.genero.lower()]


class RepoEditorialCSV(RepoCSVBase[Editorial], IRepositorioEditorial):
    """Implementación de CRUD para editoriales en CSV."""

    ruta = CSV_FOLDER_PATH / "editorial.csv"
    tipo = Editorial
    unique_fields = ("proveedor",)

    def leer_por_parametros(self, kwargs: dict[str, Any]) -> list[Editorial]:
        """Lee editoriales cuyos campos coincidan con los dados.

        Raises:
            KeyError: Si algún campo no existe en Editorial.
        """
        invalidos = [k for k in kwargs if k not in self._campos]
        if invalidos:
            raise KeyError(f"Campos inválidos: {', '.join(invalidos)}")
        return self._leer_x_parametros(**kwargs)

    def leer_por_proveedor(self, proveedor: str) -> Editorial | None:
        """Lee una editorial por su proveedor, o None si no existe."""
        return self._leer_x_parametros_unico(proveedor=proveedor)


class RepoMonedaCSV(RepoCSVBase[Moneda], IRepositorioMoneda):
    """Implementación de CRUD para monedas en CSV."""

    ruta = CSV_FOLDER_PATH / "moneda.csv"
    tipo = Moneda
    unique_fields = ("codigo",)

    def leer_por_codigo(self, codigo: str) -> Moneda | None:
        """Lee una moneda por código; se normaliza a mayúsculas y sin espacios."""
        return self._leer_x_parametros_unico(codigo=codigo.upper().replace(" ", ""))


class RepoStockCSV(RepoCSVBase[Stock], IRepositorioStock):
    """Implementación de CRUD para stock en CSV."""

    ruta = CSV_FOLDER_PATH / "stock.csv"
    tipo = Stock
    unique_fields = ("libro_id",)

    def leer_por_libro(self, libro_id: int) -> Stock | None:
        """Lee el stock de un libro, o None si no tiene."""
        return self._leer_x_parametros_unico(libro_id=libro_id)


class RepoPrecioCSV(RepoCSVBase[Precio], IRepositorioPrecio):
    """Implementación de CRUD para precios en CSV."""

    ruta = CSV_FOLDER_PATH / "precio.csv"
    tipo = Precio
    unique_fields = ("libro_id", "moneda_id")

    def leer_por_libro(self, libro_id: int) -> list[Precio]:
        """Lee los precios de un libro, uno por moneda."""
        return self._leer_x_parametros(libro_id=libro_id)

    def leer_por_moneda(self, moneda_id: int) -> list[Precio]:
        """Lee los precios expresados en una moneda."""
        return self._leer_x_parametros(moneda_id=moneda_id)

    def leer_por_libro_y_moneda(self, libro_id: int, moneda_id: int) -> Precio | None:
        """Lee el precio de un libro en una moneda, o None si no existe."""
        return self._leer_x_parametros_unico(libro_id=libro_id, moneda_id=moneda_id)


class RepoTipoCotizacionCSV(RepoCSVBase[TipoCotizacion], IRepositorioTipoCotizacion):
    """Implementación de CRUD para tipos de cotización en CSV."""

    ruta = CSV_FOLDER_PATH / "tipo_cotizacion.csv"
    tipo = TipoCotizacion
    unique_fields = ("tipo",)

    def leer_por_tipo(self, tipo: str) -> TipoCotizacion | None:
        """Lee un tipo de cotización por su nombre, o None si no existe."""
        return self._leer_x_parametros_unico(tipo=tipo)


class RepoCotizacionDolarCSV(RepoCSVBase[CotizacionDolar], IRepositorioCotizacionDolar):
    """Implementación de CRUD para cotizaciones del dólar en CSV."""

    ruta = CSV_FOLDER_PATH / "cotizacion.csv"
    tipo = CotizacionDolar
    unique_fields = ("tipo_cotizacion_id", "fecha")

    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: date
    ) -> CotizacionDolar | None:
        """Lee la cotización de un tipo en una fecha, o None si no existe."""
        return self._leer_x_parametros_unico(tipo_cotizacion_id=tipo_id, fecha=fecha)

    def leer_historico_por_tipo(self, tipo_id: int) -> list[CotizacionDolar]:
        """Lee las cotizaciones de un tipo, ordenadas por fecha."""
        historico = self._leer_x_parametros(tipo_cotizacion_id=tipo_id)
        return sorted(historico, key=lambda c: c.fecha)
