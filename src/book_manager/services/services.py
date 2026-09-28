import csv
from collections.abc import Iterator
from datetime import date
from pathlib import Path

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
from book_manager.repositories.repositories import (
    IRepositorio,
    IRepositorioCotizacion,
    IRepositorioEditorial,
    IRepositorioGenero,
    IRepositorioLibro,
    IRepositorioMoneda,
    IRepositorioPrecio,
    IRepositorioStock,
    IRepositorioTipoCotizacion,
)
from book_manager.rutas import CSV_FOLDER_PATH
from book_manager.services.csv_config import csv_config


class RepoCSVBase[T: BaseModel](IRepositorio[T]):
    """Implementación genérica de CRUD sobre CSV para entidades Pydantic.

    Asume que T tiene un campo `id`.
    """

    def __init__(
        self,
        filepath: Path | str,
        modelo: type[T],
        unique_fields: tuple[str, ...] | None = None,
    ) -> None:
        """Prepara el repositorio y crea el CSV con su cabecera si no existe.

        Args:
            filepath: Ruta del archivo CSV.
            modelo: Clase Pydantic de las entidades que guarda.
            unique_fields: Campos que, combinados, no se pueden repetir.
        """
        self._ruta = Path(filepath)
        self._modelo = modelo
        self._campos = [
            nombre for nombre, info in self._modelo.model_fields.items() if not info.exclude
        ]
        self._unique_fields = unique_fields

        if not self._ruta.exists():
            self._ruta.parent.mkdir(parents=True, exist_ok=True)

            with open(self._ruta, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, self._campos, **csv_config)
                writer.writeheader()

    def leer_todos(self) -> list[T]:
        """Lee todas las entidades del repositorio.

        Returns:
            Lista de entidades.
        """
        with open(self._ruta, newline="", encoding="utf-8") as f:
            return [self._modelo.model_validate(fila) for fila in csv.DictReader(f)]

    def crear(self, entidad: T) -> T | None:
        """Crea una nueva entidad en el repositorio y le asigna un id.

        Args:
            entidad: Entidad a crear.

        Returns:
            La entidad creada. Si ya existe una con los mismos campos únicos,
            no se guarda nada y se devuelve la existente.
        """
        if self._unique_fields:
            for d in self._iterar():
                existente = self._modelo.model_validate(d)
                if all(
                    getattr(existente, field) == getattr(entidad, field)
                    for field in self._unique_fields
                ):
                    return existente

        entidad.id = self._proximo_id()
        with open(self._ruta, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, self._campos)
            writer.writerow(entidad.model_dump(mode="json"))

        return self.leer_por_id(entidad.id)

    def leer_por_id(self, entidad_id: int) -> T | None:
        """Lee una entidad del repositorio por su ID.

        Args:
            entidad_id: ID de la entidad.

        Returns:
            La entidad encontrada, o None si no existe.
        """
        for d in self._iterar():
            if int(d["id"]) == entidad_id:
                return self._modelo.model_validate(d)
        return None

    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente en el repositorio.

        Args:
            entidad: Entidad a actualizar, con un id existente.

        Returns:
            La entidad actualizada.

        Raises:
            ValueError: Si no existe una entidad con ese id.
        """
        filas = []
        encontrado = False

        with open(self._ruta, newline="", encoding="utf-8") as f:
            lector = csv.DictReader(f)
            for fila in lector:
                if fila["id"] == str(entidad.id):
                    fila.update(entidad.model_dump(mode="json"))
                    encontrado = True
                filas.append(fila)

        if not encontrado:
            raise ValueError(f"No se encontró el id {entidad.id}")

        with open(self._ruta, "w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, self._campos)
            escritor.writeheader()
            escritor.writerows(filas)

        return self.leer_por_id(entidad.id)

    def eliminar(self, entidad_id: int) -> bool:
        """Elimina una entidad del repositorio por su ID.

        Args:
            entidad_id: ID de la entidad.

        Returns:
            True si se eliminó, False si no existía.
        """
        if self.leer_por_id(entidad_id) is None:
            return False

        with open(self._ruta, newline="", encoding="utf-8") as f:
            lector = csv.DictReader(f)
            filas = [fila for fila in lector if fila["id"] != str(entidad_id)]

        with open(self._ruta, "w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, self._campos)
            escritor.writeheader()
            escritor.writerows(filas)

        return True

    def _iterar(self) -> Iterator[dict]:
        """Recorre las filas del CSV como diccionarios de texto."""
        with open(self._ruta, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            yield from reader

    def _leer_x_parametros_unico(self, **kwargs) -> T | None:
        """Lee la primera entidad cuyos campos coincidan con los dados.

        Args:
            kwargs: Pares campo -> valor a comparar por igualdad.

        Returns:
            La entidad que coincide, o None.
        """
        for entidad in self._leer_x_parametros(**kwargs):
            return entidad
        return None

    def _leer_x_parametros(self, **kwargs) -> list[T]:
        """Lee las entidades cuyos campos coincidan con los dados.

        Args:
            kwargs: Pares campo -> valor a comparar por igualdad.

        Returns:
            Lista de entidades que coinciden.
        """
        result: list[T] = []
        for d in self._iterar():
            entidad = self._modelo.model_validate(d)
            if all(getattr(entidad, campo) == valor for campo, valor in kwargs.items()):
                result.append(entidad)
        return result

    def _proximo_id(self) -> int:
        """Calcula el próximo ID disponible (el mayor existente + 1)."""
        ids = [int(item["id"]) for item in self._iterar()]
        return max(ids) + 1 if ids else 1


class RepoMonedaCSV(RepoCSVBase[Moneda], IRepositorioMoneda):
    """Implementación de CRUD para monedas en CSV."""

    ruta: Path = CSV_FOLDER_PATH / "moneda.csv"
    tipo: type[Moneda] = Moneda
    unique_fields: tuple[str, ...] = ("codigo",)

    def __init__(self) -> None:
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_codigo(self, codigo: str) -> Moneda | None:
        """Lee una moneda por código.

        Args:
            codigo: Código de la moneda; se normaliza a mayúsculas.

        Returns:
            La moneda que coincide con el código, o None.
        """
        codigo = codigo.upper().replace(" ", "")
        return self._leer_x_parametros_unico(codigo=codigo)


class RepoGeneroCSV(RepoCSVBase[Genero], IRepositorioGenero):
    """Implementación de CRUD para géneros en CSV."""

    ruta: Path = CSV_FOLDER_PATH / "genero.csv"
    tipo: type[Genero] = Genero
    unique_fields: tuple[str, ...] = ("genero",)

    def __init__(self) -> None:
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_cadena(self, cadena: str) -> list[Genero]:
        """Lee géneros por cadena.

        Args:
            cadena: Cadena a buscar, sin distinguir mayúsculas.

        Returns:
            Lista de géneros que contienen la cadena.
        """
        result = []
        for item in self._iterar():
            if cadena.lower() in item["genero"].lower():
                result.append(self._modelo.model_validate(item))
        return result


class RepoEditorialCSV(RepoCSVBase[Editorial], IRepositorioEditorial):
    """Implementación de CRUD para editoriales en CSV."""

    ruta: Path = CSV_FOLDER_PATH / "editorial.csv"
    tipo: type[Editorial] = Editorial
    unique_fields: tuple[str, ...] = ("proveedor",)

    def __init__(self) -> None:
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_parametros(self, kwargs: dict) -> list[Editorial]:
        """Lee editoriales por parámetros.

        Args:
            kwargs: Pares campo -> valor a comparar por igualdad.

        Returns:
            Lista de editoriales que coinciden con los parámetros.

        Raises:
            KeyError: Si algún campo no existe en Editorial.
        """
        x_keys = [k for k in kwargs if k not in self._campos]
        if len(x_keys):
            raise KeyError(f"Campos inválidos: {', '.join(x_keys)}")

        return self._leer_x_parametros(**kwargs)

    def leer_por_proveedor(self, proveedor: str) -> Editorial | None:
        """Lee una editorial por proveedor.

        Args:
            proveedor: Nombre del proveedor.

        Returns:
            La editorial que coincide con el proveedor, o None.
        """
        return self._leer_x_parametros_unico(proveedor=proveedor)


class RepoLibroCSV(RepoCSVBase[Libro], IRepositorioLibro):
    """Implementación de CRUD para libros en CSV."""

    ruta: Path = CSV_FOLDER_PATH / "libro.csv"
    tipo: type[Libro] = Libro
    unique_fields: tuple[str, ...] = ("isbn",)

    def __init__(self) -> None:
        super().__init__(self.ruta, self.tipo, self.unique_fields)


class RepoStock(RepoCSVBase[Stock], IRepositorioStock):
    """Implementación de CRUD para stock en CSV."""

    ruta: Path = CSV_FOLDER_PATH / "stock.csv"
    tipo: type[Stock] = Stock
    unique_fields: tuple[str, ...] = ("libro_id",)

    def __init__(self) -> None:
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_libro_id(self, libro_id: int) -> Stock | None:
        """Lee el stock de un libro.

        Args:
            libro_id: ID del libro.

        Returns:
            El stock del libro, o None.
        """
        return self._leer_x_parametros_unico(libro_id=libro_id)

    def modificar_stock(self, libro_id: int, existencia: int) -> None:
        """Reemplaza la existencia de un libro.

        Args:
            libro_id: ID del libro.
            existencia: Nueva cantidad disponible.

        Raises:
            ValueError: Si el libro no tiene registro de stock.
        """
        stock = self.leer_por_libro_id(libro_id)
        if stock is None:
            raise ValueError(f"No se encontró stock para el libro {libro_id}")
        stock.existencia = existencia
        self.actualizar(stock)


class RepoPrecioCSV(RepoCSVBase[Precio], IRepositorioPrecio):
    """Implementación de CRUD para precios en CSV."""

    ruta: Path = CSV_FOLDER_PATH / "precio.csv"
    tipo: type[Precio] = Precio
    unique_fields: tuple[str, ...] = ("libro_id", "moneda_id")

    def __init__(self) -> None:
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_libro_id(self, libro_id: int) -> list[Precio]:
        """Lee los precios de un libro, uno por moneda.

        Args:
            libro_id: ID del libro.

        Returns:
            Lista de precios del libro.
        """
        return self._leer_x_parametros(libro_id=libro_id)

    def leer_por_libro_id_moneda_id(
        self, libro_id: int, moneda_id: int
    ) -> Precio | None:
        """Lee el precio de un libro en una moneda.

        Args:
            libro_id: ID del libro.
            moneda_id: ID de la moneda.

        Returns:
            El precio, o None si no existe.
        """
        return self._leer_x_parametros_unico(libro_id=libro_id, moneda_id=moneda_id)

    def modificar_precio(self, libro_id: int, moneda_id: int, valor: float) -> Precio:
        """Reemplaza el valor del precio de un libro en una moneda.

        Args:
            libro_id: ID del libro.
            moneda_id: ID de la moneda.
            valor: Nuevo valor.

        Returns:
            El precio actualizado.

        Raises:
            ValueError: Si no existe precio para ese libro y moneda.
        """
        precio = self.leer_por_libro_id_moneda_id(libro_id, moneda_id)
        if precio is None:
            raise ValueError(
                f"No se encontró precio para libro {libro_id} y moneda {moneda_id}"
            )
        precio.valor = valor
        return self.actualizar(precio)


class RepoTipoCotizacionCSV(RepoCSVBase[TipoCotizacion], IRepositorioTipoCotizacion):
    """Implementación de CRUD para tipos de cotización en CSV."""

    ruta: Path = CSV_FOLDER_PATH / "tipo_cotizacion.csv"
    tipo: type[TipoCotizacion] = TipoCotizacion
    unique_fields: tuple[str, ...] = ("tipo",)

    def __init__(self) -> None:
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_tipo(self, tipo: str) -> TipoCotizacion | None:
        """Lee un tipo de cotización por su nombre.

        Args:
            tipo: Nombre exacto del tipo, p. ej. "Blue".

        Returns:
            El tipo de cotización, o None.
        """
        return self._leer_x_parametros_unico(tipo=tipo)


class RepoCotizacionCSV(RepoCSVBase[CotizacionDolar], IRepositorioCotizacion):
    """Implementación de CRUD para cotización en CSV."""

    ruta: Path = CSV_FOLDER_PATH / "cotizacion.csv"
    tipo: type[CotizacionDolar] = CotizacionDolar
    unique_fields: tuple[str, ...] = ("tipo_cotizacion_id", "fecha")

    def __init__(self) -> None:
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_cotizacion(
        self, tipo_cotizacion_id: int, fecha: date
    ) -> CotizacionDolar | None:
        """Lee la cotización de un tipo en una fecha.

        Args:
            tipo_cotizacion_id: ID del tipo de cotización.
            fecha: Fecha de la cotización.

        Returns:
            La cotización, o None si no existe.
        """
        return self._leer_x_parametros_unico(
            tipo_cotizacion_id=tipo_cotizacion_id, fecha=fecha
        )
