"""Lógica de negocio sobre los repositorios SQL.

Los servicios validan que las referencias existan, impiden borrar registros en
uso y resuelven las relaciones. Trabajan con las claves naturales de cada entidad.
"""

import csv
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests

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
    RepoPrecioWebSQL,
    RepoStockSQL,
    RepoTipoCotizacionSQL,
)
from book_manager.services.auditoria import auditar
from book_manager.utils import cargar_entorno, fecha_argentina

cargar_entorno()

_CASA_A_TIPO: dict[str, str] = {
    "oficial": "Oficial",
    "blue": "Blue",
    "bolsa": "MEP",
    "contadoconliqui": "CCL",
    "mayorista": "Mayorista",
    "cripto": "Cripto",
    "tarjeta": "Tarjeta",
    "solidario": "Solidario",
    "blend": "Blend",
    "turista": "Turista",
}


def _descargar_cotizaciones() -> list[dict[str, Any]]:
    """Descarga las cotizaciones del dólar desde la API configurada en `.env`."""
    url = os.environ.get("API_URL", "https://dolarapi.com/v1/dolares")
    respuesta = requests.get(url, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


def _fecha_de(item: dict[str, Any]) -> date:
    """Fecha (en Argentina) de la cotización según `fechaActualizacion`.

    La API informa el instante en UTC; después de las 21 h de Argentina ese
    instante ya cae en el día siguiente en UTC.
    """
    return fecha_argentina(datetime.fromisoformat(item["fechaActualizacion"]))


class ServicioBase[T: EntidadBase]:
    """Operaciones CRUD con las reglas de negocio de cada entidad."""

    def __init__(self, repo: IRepositorio[T]) -> None:
        self._repo = repo

    def leer_todos(self) -> list[T]:
        return self._repo.leer_todos()

    @auditar
    def crear(self, entidad: T) -> T:
        self._validar(entidad)
        return self._repo.crear(entidad)

    @auditar
    def actualizar(self, clave: object, entidad: T) -> T:
        self._validar(entidad)
        return self._repo.actualizar(clave, entidad)

    @auditar
    def eliminar(self, clave: object) -> bool:
        self._antes_de_eliminar(clave)
        return self._repo.eliminar(clave)

    def _validar(self, entidad: T) -> None:
        """Reglas de negocio antes de guardar. Por defecto, ninguna."""

    def _antes_de_eliminar(self, clave: object) -> None:
        """Verifica o prepara la eliminación. Por defecto, no hace nada."""


class ServicioLibro(ServicioBase[Libro]):
    """Libros: exige editorial y género existentes.

    Al borrar un libro, su stock y sus precios se borran por cascada en la misma
    transacción (ver `models.Libro`).
    """

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
        return self.actualizar(
            isbn, stock.model_copy(update={"existencia": existencia})
        )

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

    def leer_por_libro(self, isbn: str) -> list[Precio]:
        """Devuelve los precios de un libro, uno por moneda."""
        return self._repo.leer_por_libro(isbn)

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
        """Devuelve la cotización más reciente de un tipo, o None si no tiene."""
        return self._repo.leer_ultima_por_tipo(tipo)

    def ultimas(self) -> list[CotizacionDolar]:
        """Devuelve la cotización más reciente de cada tipo."""
        return self._repo.leer_ultimas()

    def _validar(self, cotizacion: CotizacionDolar) -> None:
        if self._repo_tipo.leer_por_tipo(cotizacion.tipo_cotizacion.tipo) is None:
            raise ValueError(
                f"No existe el tipo de cotización {cotizacion.tipo_cotizacion.tipo!r}."
            )

    @auditar("obtener_cotizaciones")
    def obtener_cotizaciones(self) -> list[CotizacionDolar]:
        """Busca, descarga y registra las cotizaciones del dólar en la base.

        Crea los tipos de cotización que falten y registra una cotización por
        tipo. Es idempotente: no duplica un tipo para una misma fecha.

        Returns:
            Las cotizaciones registradas en esta ejecución.
        """
        registradas: list[CotizacionDolar] = []
        for item in _descargar_cotizaciones():
            tipo_nombre = _CASA_A_TIPO.get(item.get("casa", ""))
            if tipo_nombre is None or not item.get("compra") or not item.get("venta"):
                continue
            tipo = self._repo_tipo.leer_por_tipo(tipo_nombre)
            if tipo is None:
                tipo = self._repo_tipo.crear(TipoCotizacion(tipo=tipo_nombre))
            fecha = _fecha_de(item)
            if self._repo.leer_por_tipo_y_fecha(tipo_nombre, fecha) is not None:
                continue
            cotizacion = CotizacionDolar(
                tipo_cotizacion=tipo,
                fecha=fecha,
                valor_compra=float(item["compra"]),
                valor_venta=float(item["venta"]),
            )
            registradas.append(self.crear(cotizacion))
        return registradas


@dataclass(frozen=True)
class PrecioBimonetario:
    """Precio de un libro en dólares y en pesos para un tipo de cotización."""

    isbn: str
    titulo: str
    usd: float
    ars: float


def _usd_y_ars(precio: Precio, tasa: float) -> tuple[float, float] | None:
    """Convierte un precio a (USD, ARS) con la tasa en pesos por dólar.

    Devuelve None si el precio está en otra moneda: no hay cotización para ella.
    """
    if precio.moneda.codigo == "USD":
        return precio.valor, precio.valor * tasa
    if precio.moneda.codigo == "ARS":
        return precio.valor / tasa, precio.valor
    return None


def _precio_base_por_libro(precios: list[Precio]) -> dict[str, Precio]:
    """Elige un precio por libro para convertir: el de USD y, si no hay, el de ARS."""
    prioridad = {"USD": 0, "ARS": 1}
    elegidos: dict[str, Precio] = {}
    for precio in precios:
        if precio.moneda.codigo not in prioridad:
            continue
        actual = elegidos.get(precio.libro.isbn)
        if (
            actual is None
            or prioridad[precio.moneda.codigo] < prioridad[actual.moneda.codigo]
        ):
            elegidos[precio.libro.isbn] = precio
    return elegidos


class ServicioListaPrecios:
    """Reportes de precios en pesos y en dólares según el tipo de cotización.

    Los precios del catálogo se cargan en USD (o en ARS). Cada tipo de dólar
    (Oficial, Blue, MEP, ...) da un precio en pesos distinto; se usa la última
    cotización registrada de cada tipo. Lee todo con una consulta por tabla.
    """

    def __init__(
        self,
        repo_precio: IRepositorioPrecio | None = None,
        repo_cotizacion: IRepositorioCotizacionDolar | None = None,
        conexion: ConexionDB | None = None,
    ) -> None:
        if repo_precio is None or repo_cotizacion is None:
            conexion = conexion or ConexionDB()
        self._repo_precio = repo_precio or RepoPrecioSQL(conexion)
        self._repo_cotizacion = repo_cotizacion or RepoCotizacionDolarSQL(conexion)

    def cotizaciones_vigentes(self) -> list[CotizacionDolar]:
        """Última cotización de cada tipo, ordenada por nombre del tipo."""
        return sorted(
            self._repo_cotizacion.leer_ultimas(), key=lambda c: c.tipo_cotizacion.tipo
        )

    def lista_bimonetaria(
        self, tipo: str
    ) -> tuple[CotizacionDolar, list[PrecioBimonetario]]:
        """Precio de cada libro en USD y en pesos al último dólar `tipo`.

        Raises:
            ValueError: Si el tipo no tiene cotizaciones registradas.
        """
        cotizacion = self._repo_cotizacion.leer_ultima_por_tipo(tipo)
        if cotizacion is None:
            raise ValueError(f"No hay cotizaciones del dólar {tipo!r}.")
        return cotizacion, self._convertir(cotizacion.valor_venta)

    def exportar_csv(self, ruta: Path) -> list[CotizacionDolar]:
        """Exporta cada precio en su moneda y en pesos para cada tipo de dólar.

        Columnas: isbn, titulo, moneda, valor y una `ARS <tipo>` por cada tipo
        con cotización registrada.

        Returns:
            Las cotizaciones usadas, una por columna de pesos.
        """
        cotizaciones = self.cotizaciones_vigentes()
        base = _precio_base_por_libro(self._repo_precio.leer_todos())

        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(
                ["isbn", "titulo", "moneda", "valor"]
                + [f"ARS {c.tipo_cotizacion.tipo}" for c in cotizaciones]
            )
            for precio in base.values():
                pesos = [_usd_y_ars(precio, c.valor_venta)[1] for c in cotizaciones]
                escritor.writerow(
                    [precio.libro.isbn, precio.libro.titulo, precio.moneda.codigo]
                    + [round(valor, 2) for valor in (precio.valor, *pesos)]
                )
        return cotizaciones

    def _convertir(self, tasa: float) -> list[PrecioBimonetario]:
        filas = []
        for precio in _precio_base_por_libro(self._repo_precio.leer_todos()).values():
            usd, ars = _usd_y_ars(precio, tasa)
            filas.append(
                PrecioBimonetario(
                    isbn=precio.libro.isbn,
                    titulo=precio.libro.titulo,
                    usd=round(usd, 2),
                    ars=round(ars, 2),
                )
            )
        return filas


# El precio web de Cúspide está en pesos: el interno se convierte con el dólar
# oficial (valor de venta), el mismo criterio que la lista bimonetaria.
TIPO_COTIZACION_COMPARACION = "Oficial"

COLUMNAS_ALERTAS = [
    "isbn",
    "titulo",
    "precio_interno",
    "precio_web",
    "diferencia",
    "fecha_extraccion",
]


@dataclass(frozen=True)
class ComparacionPrecio:
    """Precio interno y precio web de un libro, ambos en pesos, y su diferencia.

    `diferencia` conserva el signo: es positiva si el precio web es más caro
    que el interno y negativa si es más barato.
    """

    isbn: str
    titulo: str
    precio_interno: float
    precio_web: float
    diferencia: float
    fecha_extraccion: date


class ServicioComparacionPrecios:
    """Compara el precio interno con el precio web de Cúspide y alerta.

    El precio interno se guarda en USD (o en ARS) y se convierte a pesos con la
    última cotización del dólar oficial; el precio web ya viene en pesos. Solo
    se comparan los libros que tienen precio web, es decir, los que el scraper
    encontró en Cúspide. La diferencia es `precio_web - precio_interno` y una
    alerta se dispara cuando su valor absoluto supera el umbral en pesos que
    recibe cada ejecución.
    """

    def __init__(
        self,
        repo_precio: IRepositorioPrecio | None = None,
        repo_cotizacion: IRepositorioCotizacionDolar | None = None,
        repo_precio_web: RepoPrecioWebSQL | None = None,
        conexion: ConexionDB | None = None,
    ) -> None:
        if repo_precio is None or repo_cotizacion is None or repo_precio_web is None:
            conexion = conexion or ConexionDB()
        self._lista = ServicioListaPrecios(
            repo_precio=repo_precio, repo_cotizacion=repo_cotizacion, conexion=conexion
        )
        self._repo_precio_web = repo_precio_web or RepoPrecioWebSQL(conexion)

    def comparar(self) -> list[ComparacionPrecio]:
        """Compara en pesos el precio interno y el último precio web de cada libro.

        Returns:
            Una comparación por libro con precio web conocido, ordenada por ISBN.

        Raises:
            ValueError: Si no hay cotizaciones del dólar oficial registradas.
        """
        _, filas = self._lista.lista_bimonetaria(TIPO_COTIZACION_COMPARACION)
        web_por_libro = self._repo_precio_web.leer_ultimas_por_libro()
        comparaciones: list[ComparacionPrecio] = []
        for fila in filas:
            web = web_por_libro.get(fila.isbn)
            if web is None:
                continue
            precio_interno = round(fila.ars, 2)
            precio_web = round(web.precio, 2)
            comparaciones.append(
                ComparacionPrecio(
                    isbn=fila.isbn,
                    titulo=fila.titulo,
                    precio_interno=precio_interno,
                    precio_web=precio_web,
                    diferencia=round(precio_web - precio_interno, 2),
                    fecha_extraccion=web.fecha_extraccion,
                )
            )
        return comparaciones

    def alertas(self, umbral: float) -> list[ComparacionPrecio]:
        """Comparaciones cuya diferencia absoluta supera `umbral` (en pesos).

        Raises:
            ValueError: Si el umbral es negativo.
        """
        if umbral < 0:
            raise ValueError("El umbral de diferencia no puede ser negativo.")
        return [
            comparacion
            for comparacion in self.comparar()
            if abs(comparacion.diferencia) > umbral
        ]

    def exportar_alertas_csv(
        self, umbral: float, ruta: Path
    ) -> list[ComparacionPrecio]:
        """Escribe en `ruta` el CSV de alertas (cabecera y una fila por alerta).

        Escribe siempre el archivo, aunque no haya alertas: así cada ejecución
        del scraper deja un archivo descargable para analizar los precios.

        Returns:
            Las alertas exportadas.
        """
        alertas = self.alertas(umbral)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(COLUMNAS_ALERTAS)
            for alerta in alertas:
                escritor.writerow(
                    [
                        alerta.isbn,
                        alerta.titulo,
                        alerta.precio_interno,
                        alerta.precio_web,
                        alerta.diferencia,
                        alerta.fecha_extraccion.isoformat(),
                    ]
                )
        return alertas
