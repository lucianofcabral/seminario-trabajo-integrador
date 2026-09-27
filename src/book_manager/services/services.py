import csv
from collections.abc import Iterator
from datetime import date
from pathlib import Path

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
        unique_fields: tuple[str] | None = None,
    ):
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
        """Crea una nueva entidad en el repositorio.
        Args:
            entidad: Entidad a crear.
        Returns:
            Entidad creada.
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
            Entidad encontrada.
        """
        for d in self._iterar():
            if int(d["id"]) == entidad_id:
                return self._modelo.model_validate(d)
        return None

    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente en el repositorio.
        Args:
            entidad: Entidad a actualizar.
        Returns:
            Entidad actualizada.
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
        """Iterador para uso interno."""
        with open(self._ruta, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            yield from reader

    def _leer_x_parametros_unico(self, **kwargs) -> T | None:
        """Lee una entidad por parámetros únicos.
        Args:
            kwargs: Diccionario de parámetros.
        Returns:
            Entidad que coincide con los parámetros, o None.
        """
        for entidad in self._leer_x_parametros(**kwargs):
            return entidad
        return None

    def _leer_x_parametros(self, **kwargs) -> list[T]:
        """Lee entidades por parámetros.
        Args:
            kwargs: Diccionario de parámetros.
        Returns:
            Lista de entidades que coinciden con los parámetros.
        """
        result: list[T] = []
        for d in self._iterar():
            entidad = self._modelo.model_validate(d)
            if all(getattr(entidad, campo) == valor for campo, valor in kwargs.items()):
                result.append(entidad)
        return result

    def _proximo_id(self) -> int:
        """Calcula el próximo ID disponible."""
        ids = [int(item["id"]) for item in self._iterar()]
        return max(ids) + 1 if ids else 1


class RepoMonedaCSV(RepoCSVBase[Moneda], IRepositorioMoneda):
    ruta: Path = CSV_FOLDER_PATH / "moneda.csv"
    tipo: type[Moneda] = Moneda
    unique_fields: tuple[str] = ("codigo",)

    def __init__(self):
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_codigo(self, codigo: str) -> Moneda | None:
        """Lee una moneda por código.
        Args:
            codigo: Código de la moneda.
        Returns:
            Moneda que coincide con el código.
        """
        codigo = codigo.upper().replace(" ", "")
        return self._leer_x_parametros_unico(codigo=codigo)


class RepoGeneroCSV(RepoCSVBase[Genero], IRepositorioGenero):
    ruta: Path = CSV_FOLDER_PATH / "genero.csv"
    tipo: type[Genero] = Genero
    unique_fields: tuple[str] = ("genero",)

    def __init__(self):
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_cadena(self, cadena: str) -> list[Genero]:
        """Lee géneros por cadena.
        Args:
            cadena: Cadena a buscar.
        Returns:
            Lista de géneros que coinciden con la cadena.
        """
        result = []
        for item in self._iterar():
            if cadena.lower() in item["genero"].lower():
                result.append(self._modelo.model_validate(item))
        return result


class RepoEditorialCSV(RepoCSVBase[Editorial], IRepositorioEditorial):
    """Interfaz CRUD para editoriales."""

    ruta: Path = CSV_FOLDER_PATH / "editorial.csv"
    tipo: type[Editorial] = Editorial
    unique_fields: tuple[str] = ("proveedor",)

    def __init__(self):
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_parametros(self, kwargs: dict) -> list[Editorial]:
        """Lee editoriales por parámetros.
        Args:
            kwargs: Diccionario de parámetros.
        Returns:
            Lista de editoriales que coinciden con los parámetros.

        *Levanta un KeyError si los parámetros son inválidos.*
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
            Editorial que coincide con el proveedor.
        """
        return self._leer_x_parametros_unico(proveedor=proveedor)


class RepoLibroCSV(RepoCSVBase[Libro], IRepositorioLibro):
    """Interfaz CRUD para libros."""

    ruta: Path = CSV_FOLDER_PATH / "libro.csv"
    tipo: type[Libro] = Libro
    unique_fields: tuple[str] = ("isbn",)

    def __init__(self):
        super().__init__(self.ruta, self.tipo, self.unique_fields)


class RepoStock(RepoCSVBase[Stock], IRepositorioStock):
    """Interfaz CRUD para stock."""

    ruta: Path = CSV_FOLDER_PATH / "stock.csv"
    tipo: type[Stock] = Stock
    unique_fields: tuple[str] = ("libro_id",)

    def __init__(self):
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_libro_id(self, libro_id: int) -> Stock | None:
        """Lee un stock por ID de libro."""
        return self._leer_x_parametros_unico(libro_id=libro_id)

    def modificar_stock(self, libro_id: int, existencia: int) -> None:
        """Modifica el stock de un libro."""
        stock = self.leer_por_libro_id(libro_id)
        if stock is None:
            raise ValueError(f"No se encontró stock para el libro {libro_id}")
        stock.existencia = existencia
        self.actualizar(stock)


class RepoPrecioCSV(RepoCSVBase[Precio], IRepositorioPrecio):
    """Interfaz CRUD para precios."""

    ruta: Path = CSV_FOLDER_PATH / "precio.csv"
    tipo: type[Precio] = Precio
    unique_fields: tuple[str] = ("libro_id", "moneda_id")

    def __init__(self):
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_libro_id(self, libro_id: int) -> list[Precio]:
        """Lee los precios de un libro por su ID."""
        return self._leer_x_parametros(libro_id=libro_id)

    def leer_por_libro_id_moneda_id(
        self, libro_id: int, moneda_id: int
    ) -> Precio | None:
        """Lee los precios de un libro por su ID y ID de moneda."""
        return self._leer_x_parametros_unico(libro_id=libro_id, moneda_id=moneda_id)

    def modificar_precio(self, libro_id: int, moneda_id: int, valor: float) -> Precio:
        precio = self.leer_por_libro_id_moneda_id(libro_id, moneda_id)
        if precio is None:
            raise ValueError(
                f"No se encontró precio para libro {libro_id} y moneda {moneda_id}"
            )
        precio.valor = valor
        return self.actualizar(precio)


class RepoTipoCotizacionCSV(RepoCSVBase[TipoCotizacion], IRepositorioTipoCotizacion):
    """Interfaz CRUD para tipos de cotización."""

    ruta: Path = CSV_FOLDER_PATH / "tipo_cotizacion.csv"
    tipo: type[TipoCotizacion] = TipoCotizacion
    unique_fields: tuple[str] = ("tipo",)

    def __init__(self):
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_por_tipo(self, tipo: str) -> TipoCotizacion | None:
        return self._leer_x_parametros_unico(tipo=tipo)


class RepoCotizacionCSV(RepoCSVBase[Cotizacion], IRepositorioCotizacion):
    """Implementación de CRUD para cotización en CSV."""

    ruta: Path = CSV_FOLDER_PATH / "cotizacion.csv"
    tipo: type[Cotizacion] = Cotizacion
    unique_fields: tuple[str] = ("tipo_cotizacion_id", "fecha")

    def __init__(self):
        super().__init__(self.ruta, self.tipo, self.unique_fields)

    def leer_cotizacion(
        self, tipo_cotizacion_id: int, fecha: date
    ) -> Cotizacion | None:
        """Lee una cotización por tipo de cotización y fecha."""
        return self._leer_x_parametros_unico(
            tipo_cotizacion_id=tipo_cotizacion_id, fecha=fecha
        )
