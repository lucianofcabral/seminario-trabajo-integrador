"""Lógica de negocio sobre los repositorios SQL.

Los servicios validan que las referencias existan, impiden borrar registros en
uso y resuelven las relaciones. Trabajan con las claves naturales de cada entidad.
"""

from datetime import date

from book_manager.database.connection import ConexionDB
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
)
from book_manager.repositories.sql_repository import (
    RepoCotizacionDolarSQL,
    RepoEditorialSQL,
    RepoGeneroSQL,
    RepoLibroSQL,
    RepoMonedaSQL,
    RepoPrecioSQL,
    RepoStockSQL,
    RepoTipoCotizacionSQL,
)


class ServicioBase[T: EntidadBase]:
    """Operaciones CRUD con las reglas de negocio de cada entidad."""

    def __init__(self, repo: IRepositorio[T]) -> None:
        self._repo = repo

    def leer_todos(self) -> list[T]:
        return self._repo.leer_todos()

    def crear(self, entidad: T) -> T:
        self._validar(entidad)
        return self._repo.crear(entidad)

    def actualizar(self, clave: object, entidad: T) -> T:
        self._validar(entidad)
        return self._repo.actualizar(clave, entidad)

    def eliminar(self, clave: object) -> bool:
        self._antes_de_eliminar(clave)
        return self._repo.eliminar(clave)

    def _validar(self, entidad: T) -> None:
        """Reglas de negocio antes de guardar. Por defecto, ninguna."""

    def _antes_de_eliminar(self, clave: object) -> None:
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
        conexion: ConexionDB | None = None,
    ) -> None:
        conexion = conexion or ConexionDB()
        super().__init__(repo or RepoLibroSQL(conexion))
        self._repo_editorial = repo_editorial or RepoEditorialSQL(conexion)
        self._repo_genero = repo_genero or RepoGeneroSQL(conexion)
        self._repo_stock = repo_stock or RepoStockSQL(conexion)
        self._repo_precio = repo_precio or RepoPrecioSQL(conexion)

    def stock_de(self, isbn: str) -> Stock | None:
        return self._repo_stock.leer_por_libro(isbn)

    def precios_de(self, isbn: str) -> list[Precio]:
        return self._repo_precio.leer_por_libro(isbn)

    def _validar(self, libro: Libro) -> None:
        if self._repo_editorial.leer_por_proveedor(libro.editorial.proveedor) is None:
            raise ValueError(f"No existe la editorial {libro.editorial.proveedor!r}.")
        if self._repo_genero.leer_por_nombre(libro.genero.genero) is None:
            raise ValueError(f"No existe el género {libro.genero.genero!r}.")

    def _antes_de_eliminar(self, isbn: object) -> None:
        stock = self._repo_stock.leer_por_libro(str(isbn))
        if stock is not None:
            self._repo_stock.eliminar(str(isbn))
        for precio in self._repo_precio.leer_por_libro(str(isbn)):
            self._repo_precio.eliminar((str(isbn), precio.moneda.codigo))


class ServicioGenero(ServicioBase[Genero]):
    """Géneros: no se pueden borrar si tienen libros."""

    def __init__(
        self,
        repo: IRepositorioGenero | None = None,
        repo_libro: IRepositorioLibro | None = None,
        conexion: ConexionDB | None = None,
    ) -> None:
        conexion = conexion or ConexionDB()
        super().__init__(repo or RepoGeneroSQL(conexion))
        self._repo_libro = repo_libro or RepoLibroSQL(conexion)

    def libros_de(self, nombre: str) -> list[Libro]:
        return self._repo_libro.leer_por_genero(nombre)

    def _antes_de_eliminar(self, nombre: object) -> None:
        cantidad = len(self.libros_de(str(nombre)))
        if cantidad:
            raise ValueError(f"El género tiene {cantidad} libro(s) asociados.")


class ServicioEditorial(ServicioBase[Editorial]):
    """Editoriales: no se pueden borrar si tienen libros."""

    def __init__(
        self,
        repo: IRepositorioEditorial | None = None,
        repo_libro: IRepositorioLibro | None = None,
        conexion: ConexionDB | None = None,
    ) -> None:
        conexion = conexion or ConexionDB()
        super().__init__(repo or RepoEditorialSQL(conexion))
        self._repo_libro = repo_libro or RepoLibroSQL(conexion)

    def libros_de(self, proveedor: str) -> list[Libro]:
        return self._repo_libro.leer_por_editorial(proveedor)

    def _antes_de_eliminar(self, proveedor: object) -> None:
        cantidad = len(self.libros_de(str(proveedor)))
        if cantidad:
            raise ValueError(f"La editorial tiene {cantidad} libro(s) asociados.")


class ServicioMoneda(ServicioBase[Moneda]):
    """Monedas: no se pueden borrar si hay precios expresados en ellas."""

    def __init__(
        self,
        repo: IRepositorioMoneda | None = None,
        repo_precio: IRepositorioPrecio | None = None,
        conexion: ConexionDB | None = None,
    ) -> None:
        conexion = conexion or ConexionDB()
        super().__init__(repo or RepoMonedaSQL(conexion))
        self._repo_precio = repo_precio or RepoPrecioSQL(conexion)

    def _antes_de_eliminar(self, codigo: object) -> None:
        cantidad = len(self._repo_precio.leer_por_moneda(str(codigo)))
        if cantidad:
            raise ValueError(f"La moneda tiene {cantidad} precio(s) asociados.")


class ServicioStock(ServicioBase[Stock]):
    """Stock: exige que el libro exista."""

    def __init__(
        self,
        repo: IRepositorioStock | None = None,
        repo_libro: IRepositorioLibro | None = None,
        conexion: ConexionDB | None = None,
    ) -> None:
        conexion = conexion or ConexionDB()
        super().__init__(repo or RepoStockSQL(conexion))
        self._repo_libro = repo_libro or RepoLibroSQL(conexion)

    def modificar_stock(self, isbn: str, existencia: int) -> Stock:
        stock = self._repo.leer_por_libro(isbn)
        if stock is None:
            raise ValueError(f"No se encontró stock para el libro {isbn}.")
        return self.actualizar(isbn, stock.model_copy(update={"existencia": existencia}))

    def _validar(self, stock: Stock) -> None:
        if self._repo_libro.leer_por_isbn(stock.libro.isbn) is None:
            raise ValueError(f"No existe el libro con ISBN {stock.libro.isbn!r}.")


class ServicioPrecio(ServicioBase[Precio]):
    """Precios: exigen que el libro y la moneda existan."""

    def __init__(
        self,
        repo: IRepositorioPrecio | None = None,
        repo_libro: IRepositorioLibro | None = None,
        repo_moneda: IRepositorioMoneda | None = None,
        conexion: ConexionDB | None = None,
    ) -> None:
        conexion = conexion or ConexionDB()
        super().__init__(repo or RepoPrecioSQL(conexion))
        self._repo_libro = repo_libro or RepoLibroSQL(conexion)
        self._repo_moneda = repo_moneda or RepoMonedaSQL(conexion)

    def modificar_precio(self, isbn: str, codigo: str, valor: float) -> Precio:
        precio = self._repo.leer_por_libro_y_moneda(isbn, codigo)
        if precio is None:
            raise ValueError(
                f"No se encontró precio para el libro {isbn} y la moneda {codigo}."
            )
        return self.actualizar(
            (isbn, codigo), precio.model_copy(update={"valor": valor})
        )

    def _validar(self, precio: Precio) -> None:
        if self._repo_libro.leer_por_isbn(precio.libro.isbn) is None:
            raise ValueError(f"No existe el libro con ISBN {precio.libro.isbn!r}.")
        if self._repo_moneda.leer_por_codigo(precio.moneda.codigo) is None:
            raise ValueError(f"No existe la moneda {precio.moneda.codigo!r}.")


class ServicioTipoCotizacion(ServicioBase[TipoCotizacion]):
    """Tipos de cotización: no se pueden borrar si tienen cotizaciones."""

    def __init__(
        self,
        repo: IRepositorioTipoCotizacion | None = None,
        repo_cotizacion: IRepositorioCotizacionDolar | None = None,
        conexion: ConexionDB | None = None,
    ) -> None:
        conexion = conexion or ConexionDB()
        super().__init__(repo or RepoTipoCotizacionSQL(conexion))
        self._repo_cotizacion = repo_cotizacion or RepoCotizacionDolarSQL(conexion)

    def _antes_de_eliminar(self, tipo: object) -> None:
        cantidad = len(self._repo_cotizacion.leer_historico_por_tipo(str(tipo)))
        if cantidad:
            raise ValueError(f"El tipo tiene {cantidad} cotización(es) registradas.")


class ServicioCotizacionDolar(ServicioBase[CotizacionDolar]):
    """Cotizaciones del dólar: exigen que el tipo de cotización exista."""

    def __init__(
        self,
        repo: IRepositorioCotizacionDolar | None = None,
        repo_tipo: IRepositorioTipoCotizacion | None = None,
        conexion: ConexionDB | None = None,
    ) -> None:
        conexion = conexion or ConexionDB()
        super().__init__(repo or RepoCotizacionDolarSQL(conexion))
        self._repo_tipo = repo_tipo or RepoTipoCotizacionSQL(conexion)

    def historico(self, tipo: str) -> list[CotizacionDolar]:
        return self._repo.leer_historico_por_tipo(tipo)

    def cotizacion_del_dia(self, tipo: str, fecha: date) -> CotizacionDolar | None:
        return self._repo.leer_por_tipo_y_fecha(tipo, fecha)

    def ultima(self, tipo: str) -> CotizacionDolar | None:
        historico = self.historico(tipo)
        return historico[-1] if historico else None

    def _validar(self, cotizacion: CotizacionDolar) -> None:
        if self._repo_tipo.leer_por_tipo(cotizacion.tipo_cotizacion.tipo) is None:
            raise ValueError(
                f"No existe el tipo de cotización {cotizacion.tipo_cotizacion.tipo!r}."
            )
