"""Lógica de negocio sobre los repositorios.

Los servicios son la puerta de entrada que usa la interfaz: validan que las
referencias entre entidades existan, impiden borrar registros que otros usan y
resuelven las relaciones entre objetos. La persistencia queda en los repositorios.
"""

from datetime import date

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
from book_manager.repositories.repositories import (
    IRepositorio,
    IRepositorioCotizacionDolar,
    IRepositorioEditorial,
    IRepositorioGenero,
    IRepositorioLibro,
    IRepositorioMoneda,
    IRepositorioPrecio,
    IRepositorioStock,
    IRepositorioTipoCotizacion,
    RepoCotizacionDolarCSV,
    RepoEditorialCSV,
    RepoGeneroCSV,
    RepoLibroCSV,
    RepoMonedaCSV,
    RepoPrecioCSV,
    RepoStockCSV,
    RepoTipoCotizacionCSV,
)


def _exigir_existencia(repo: IRepositorio, entidad_id: int, descripcion: str) -> None:
    """Verifica que exista la entidad referenciada.

    Args:
        repo: Repositorio donde buscarla.
        entidad_id: ID referenciado.
        descripcion: La entidad con su artículo, para el mensaje de error,
            p. ej. "la editorial".

    Raises:
        ValueError: Si no existe una entidad con ese ID.
    """
    if repo.leer_por_id(entidad_id) is None:
        raise ValueError(f"No existe {descripcion} con id {entidad_id}.")


class ServicioBase[T: EntidadBase]:
    """Operaciones CRUD con las reglas de negocio de cada entidad.

    Las subclases redefinen `_validar` y `_antes_de_eliminar` para agregar sus
    reglas.
    """

    def __init__(self, repo: IRepositorio[T]) -> None:
        """Recibe el repositorio donde se guardan las entidades.

        Args:
            repo: Repositorio de la entidad.
        """
        self._repo = repo

    def leer_todos(self) -> list[T]:
        """Devuelve todas las entidades."""
        return self._repo.leer_todos()

    def leer_por_id(self, entidad_id: int) -> T | None:
        """Devuelve la entidad con ese ID, o None si no existe."""
        return self._repo.leer_por_id(entidad_id)

    def crear(self, entidad: T) -> T:
        """Valida y guarda una entidad nueva.

        Args:
            entidad: Entidad a crear.

        Returns:
            La entidad creada, con su ID.

        Raises:
            ValueError: Si no cumple las reglas de negocio o repite una clave.
        """
        self._validar(entidad)
        return self._repo.crear(entidad)

    def actualizar(self, entidad: T) -> T:
        """Valida y guarda los cambios de una entidad existente.

        Args:
            entidad: Entidad con un ID existente y los datos nuevos.

        Returns:
            La entidad actualizada.

        Raises:
            ValueError: Si no existe, no cumple las reglas o repite una clave.
        """
        self._validar(entidad)
        return self._repo.actualizar(entidad)

    def eliminar(self, entidad_id: int) -> bool:
        """Elimina una entidad si las reglas de negocio lo permiten.

        Args:
            entidad_id: ID de la entidad.

        Returns:
            True si se eliminó, False si no existía.

        Raises:
            ValueError: Si otras entidades dependen de ella.
        """
        if self._repo.leer_por_id(entidad_id) is None:
            return False
        self._antes_de_eliminar(entidad_id)
        return self._repo.eliminar(entidad_id)

    def _validar(self, entidad: T) -> None:
        """Verifica las reglas de negocio antes de guardar. Por defecto, ninguna."""

    def _antes_de_eliminar(self, entidad_id: int) -> None:
        """Verifica o prepara la eliminación. Por defecto, no hace nada."""


class ServicioLibro(ServicioBase[Libro]):
    """Libros: exige editorial y género existentes; al borrar, borra stock y precios."""

    def __init__(
        self,
        repo: IRepositorioLibro | None = None,
        repo_editorial: IRepositorioEditorial | None = None,
        repo_genero: IRepositorioGenero | None = None,
        repo_stock: IRepositorioStock | None = None,
        repo_precio: IRepositorioPrecio | None = None,
    ) -> None:
        """Recibe los repositorios; si no se pasan, usa los de CSV."""
        super().__init__(repo or RepoLibroCSV())
        self._repo_editorial = repo_editorial or RepoEditorialCSV()
        self._repo_genero = repo_genero or RepoGeneroCSV()
        self._repo_stock = repo_stock or RepoStockCSV()
        self._repo_precio = repo_precio or RepoPrecioCSV()

    def editorial_de(self, libro: Libro) -> Editorial | None:
        """Devuelve la editorial del libro."""
        return self._repo_editorial.leer_por_id(libro.editorial_id)

    def genero_de(self, libro: Libro) -> Genero | None:
        """Devuelve el género del libro."""
        return self._repo_genero.leer_por_id(libro.genero_id)

    def stock_de(self, libro_id: int) -> Stock | None:
        """Devuelve el stock del libro, o None si no tiene."""
        return self._repo_stock.leer_por_libro(libro_id)

    def precios_de(self, libro_id: int) -> list[Precio]:
        """Devuelve los precios del libro, uno por moneda."""
        return self._repo_precio.leer_por_libro(libro_id)

    def _validar(self, libro: Libro) -> None:
        """Exige que la editorial y el género existan."""
        _exigir_existencia(self._repo_editorial, libro.editorial_id, "la editorial")
        _exigir_existencia(self._repo_genero, libro.genero_id, "el género")

    def _antes_de_eliminar(self, libro_id: int) -> None:
        """Borra el stock y los precios del libro, que no tienen sentido sin él."""
        stock = self._repo_stock.leer_por_libro(libro_id)
        if stock is not None:
            self._repo_stock.eliminar(stock.id)
        for precio in self._repo_precio.leer_por_libro(libro_id):
            self._repo_precio.eliminar(precio.id)


class ServicioGenero(ServicioBase[Genero]):
    """Géneros: no se pueden borrar si tienen libros."""

    def __init__(
        self,
        repo: IRepositorioGenero | None = None,
        repo_libro: IRepositorioLibro | None = None,
    ) -> None:
        """Recibe los repositorios; si no se pasan, usa los de CSV."""
        super().__init__(repo or RepoGeneroCSV())
        self._repo_libro = repo_libro or RepoLibroCSV()

    def libros_de(self, genero_id: int) -> list[Libro]:
        """Devuelve los libros del género."""
        return self._repo_libro.leer_por_genero(genero_id)

    def _antes_de_eliminar(self, genero_id: int) -> None:
        """Impide borrar un género que tiene libros."""
        cantidad = len(self.libros_de(genero_id))
        if cantidad:
            raise ValueError(f"El género tiene {cantidad} libro(s) asociados.")


class ServicioEditorial(ServicioBase[Editorial]):
    """Editoriales: no se pueden borrar si tienen libros."""

    def __init__(
        self,
        repo: IRepositorioEditorial | None = None,
        repo_libro: IRepositorioLibro | None = None,
    ) -> None:
        """Recibe los repositorios; si no se pasan, usa los de CSV."""
        super().__init__(repo or RepoEditorialCSV())
        self._repo_libro = repo_libro or RepoLibroCSV()

    def libros_de(self, editorial_id: int) -> list[Libro]:
        """Devuelve los libros de la editorial."""
        return self._repo_libro.leer_por_editorial(editorial_id)

    def _antes_de_eliminar(self, editorial_id: int) -> None:
        """Impide borrar una editorial que tiene libros."""
        cantidad = len(self.libros_de(editorial_id))
        if cantidad:
            raise ValueError(f"La editorial tiene {cantidad} libro(s) asociados.")


class ServicioMoneda(ServicioBase[Moneda]):
    """Monedas: no se pueden borrar si hay precios expresados en ellas."""

    def __init__(
        self,
        repo: IRepositorioMoneda | None = None,
        repo_precio: IRepositorioPrecio | None = None,
    ) -> None:
        """Recibe los repositorios; si no se pasan, usa los de CSV."""
        super().__init__(repo or RepoMonedaCSV())
        self._repo_precio = repo_precio or RepoPrecioCSV()

    def _antes_de_eliminar(self, moneda_id: int) -> None:
        """Impide borrar una moneda que tiene precios."""
        cantidad = len(self._repo_precio.leer_por_moneda(moneda_id))
        if cantidad:
            raise ValueError(f"La moneda tiene {cantidad} precio(s) asociados.")


class ServicioStock(ServicioBase[Stock]):
    """Stock: exige que el libro exista."""

    def __init__(
        self,
        repo: IRepositorioStock | None = None,
        repo_libro: IRepositorioLibro | None = None,
    ) -> None:
        """Recibe los repositorios; si no se pasan, usa los de CSV."""
        super().__init__(repo or RepoStockCSV())
        self._repo_libro = repo_libro or RepoLibroCSV()

    def modificar_stock(self, libro_id: int, existencia: int) -> Stock:
        """Reemplaza la existencia de un libro.

        Args:
            libro_id: ID del libro.
            existencia: Nueva cantidad disponible.

        Returns:
            El stock actualizado.

        Raises:
            ValueError: Si el libro no tiene registro de stock.
        """
        stock = self._repo.leer_por_libro(libro_id)
        if stock is None:
            raise ValueError(f"No se encontró stock para el libro {libro_id}.")
        return self.actualizar(stock.model_copy(update={"existencia": existencia}))

    def _validar(self, stock: Stock) -> None:
        """Exige que el libro exista."""
        _exigir_existencia(self._repo_libro, stock.libro_id, "el libro")


class ServicioPrecio(ServicioBase[Precio]):
    """Precios: exigen que el libro y la moneda existan."""

    def __init__(
        self,
        repo: IRepositorioPrecio | None = None,
        repo_libro: IRepositorioLibro | None = None,
        repo_moneda: IRepositorioMoneda | None = None,
    ) -> None:
        """Recibe los repositorios; si no se pasan, usa los de CSV."""
        super().__init__(repo or RepoPrecioCSV())
        self._repo_libro = repo_libro or RepoLibroCSV()
        self._repo_moneda = repo_moneda or RepoMonedaCSV()

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
        precio = self._repo.leer_por_libro_y_moneda(libro_id, moneda_id)
        if precio is None:
            raise ValueError(
                f"No se encontró precio para el libro {libro_id} y la moneda {moneda_id}."
            )
        return self.actualizar(precio.model_copy(update={"valor": valor}))

    def _validar(self, precio: Precio) -> None:
        """Exige que el libro y la moneda existan."""
        _exigir_existencia(self._repo_libro, precio.libro_id, "el libro")
        _exigir_existencia(self._repo_moneda, precio.moneda_id, "la moneda")


class ServicioTipoCotizacion(ServicioBase[TipoCotizacion]):
    """Tipos de cotización: no se pueden borrar si tienen cotizaciones."""

    def __init__(
        self,
        repo: IRepositorioTipoCotizacion | None = None,
        repo_cotizacion: IRepositorioCotizacionDolar | None = None,
    ) -> None:
        """Recibe los repositorios; si no se pasan, usa los de CSV."""
        super().__init__(repo or RepoTipoCotizacionCSV())
        self._repo_cotizacion = repo_cotizacion or RepoCotizacionDolarCSV()

    def _antes_de_eliminar(self, tipo_id: int) -> None:
        """Impide borrar un tipo que tiene cotizaciones registradas."""
        cantidad = len(self._repo_cotizacion.leer_historico_por_tipo(tipo_id))
        if cantidad:
            raise ValueError(f"El tipo tiene {cantidad} cotización(es) registradas.")


class ServicioCotizacionDolar(ServicioBase[CotizacionDolar]):
    """Cotizaciones del dólar: exigen que el tipo de cotización exista."""

    def __init__(
        self,
        repo: IRepositorioCotizacionDolar | None = None,
        repo_tipo: IRepositorioTipoCotizacion | None = None,
    ) -> None:
        """Recibe los repositorios; si no se pasan, usa los de CSV."""
        super().__init__(repo or RepoCotizacionDolarCSV())
        self._repo_tipo = repo_tipo or RepoTipoCotizacionCSV()

    def historico(self, tipo_id: int) -> list[CotizacionDolar]:
        """Devuelve las cotizaciones de un tipo, ordenadas por fecha."""
        return self._repo.leer_historico_por_tipo(tipo_id)

    def cotizacion_del_dia(self, tipo_id: int, fecha: date) -> CotizacionDolar | None:
        """Devuelve la cotización de un tipo en una fecha, o None si no hay."""
        return self._repo.leer_por_tipo_y_fecha(tipo_id, fecha)

    def ultima(self, tipo_id: int) -> CotizacionDolar | None:
        """Devuelve la cotización más reciente de un tipo, o None si no hay."""
        historico = self.historico(tipo_id)
        return historico[-1] if historico else None

    def _validar(self, cotizacion: CotizacionDolar) -> None:
        """Exige que el tipo de cotización exista."""
        _exigir_existencia(
            self._repo_tipo, cotizacion.tipo_cotizacion_id, "el tipo de cotización"
        )
