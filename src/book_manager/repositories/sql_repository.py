"""Implementación de repositorios sobre SQLAlchemy.

Cada repositorio mapea entre la entidad de dominio (sin id, con referencias a
objetos) y el modelo ORM (con id y foreign keys). Las claves naturales localizan
los registros: ISBN, código de moneda, proveedor, nombre de género, etc.

Los listados se devuelven siempre ordenados por id: la consola selecciona
registros por número de fila y ese número tiene que ser estable entre lecturas.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import InstrumentedAttribute, Session, selectinload

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
from book_manager.models import models as m
from book_manager.repositories.repositories import (
    IRepositorioCotizacionDolar,
    IRepositorioEditorial,
    IRepositorioGenero,
    IRepositorioLibro,
    IRepositorioMoneda,
    IRepositorioPrecio,
    IRepositorioStock,
    IRepositorioTipoCotizacion,
)
from book_manager.utils import normalizar_codigo

# --- conversión modelo ORM -> entidad ---


def _editorial_entidad(modelo: m.Editorial) -> Editorial:
    return Editorial(
        proveedor=modelo.proveedor,
        pais=modelo.pais,
        provincia=modelo.provincia,
        localidad=modelo.localidad,
        domicilio=modelo.domicilio,
        telefono=modelo.telefono,
        email=modelo.email,
        responsable=modelo.responsable,
    )


def _genero_entidad(modelo: m.Genero) -> Genero:
    return Genero(genero=modelo.genero)


def _moneda_entidad(modelo: m.Moneda) -> Moneda:
    return Moneda(codigo=modelo.codigo, nombre=modelo.nombre)


def _tipo_entidad(modelo: m.TipoCotizacion) -> TipoCotizacion:
    return TipoCotizacion(tipo=modelo.tipo)


def _libro_entidad(modelo: m.Libro) -> Libro:
    return Libro(
        isbn=modelo.isbn,
        titulo=modelo.titulo,
        autor=modelo.autor,
        editorial=_editorial_entidad(modelo.editorial),
        genero=_genero_entidad(modelo.genero),
    )


def _stock_entidad(modelo: m.Stock) -> Stock:
    return Stock(libro=_libro_entidad(modelo.libro), existencia=modelo.existencia)


def _precio_entidad(modelo: m.Precio) -> Precio:
    return Precio(
        libro=_libro_entidad(modelo.libro),
        moneda=_moneda_entidad(modelo.moneda),
        valor=modelo.valor,
    )


def _cotizacion_entidad(modelo: m.CotizacionDolar) -> CotizacionDolar:
    return CotizacionDolar(
        tipo_cotizacion=_tipo_entidad(modelo.tipo_cotizacion),
        fecha=modelo.fecha,
        valor_compra=modelo.valor_compra,
        valor_venta=modelo.valor_venta,
    )


# --- resolución de foreign keys por clave natural ---


def _id_por_clave(
    sesion: Session, columna: InstrumentedAttribute, valor: Any, descripcion: str
) -> int:
    """Devuelve el id del registro cuya `columna` vale `valor`.

    Args:
        sesion: Sesión activa.
        columna: Columna de clave natural, p. ej. `m.Libro.isbn`.
        valor: Valor buscado.
        descripcion: Cómo nombrar al registro en el error, p. ej. "la editorial".

    Raises:
        ValueError: Si no existe un registro con ese valor.
    """
    id_registro = sesion.scalar(select(columna.class_.id).where(columna == valor))
    if id_registro is None:
        raise ValueError(f"No existe {descripcion} {valor!r}.")
    return id_registro


def _id_editorial(sesion: Session, proveedor: str) -> int:
    return _id_por_clave(sesion, m.Editorial.proveedor, proveedor, "la editorial")


def _id_genero(sesion: Session, nombre: str) -> int:
    return _id_por_clave(sesion, m.Genero.genero, nombre, "el género")


def _id_moneda(sesion: Session, codigo: str) -> int:
    return _id_por_clave(
        sesion, m.Moneda.codigo, normalizar_codigo(codigo), "la moneda"
    )


def _id_tipo(sesion: Session, tipo: str) -> int:
    return _id_por_clave(sesion, m.TipoCotizacion.tipo, tipo, "el tipo de cotización")


def _id_libro(sesion: Session, isbn: str) -> int:
    return _id_por_clave(sesion, m.Libro.isbn, isbn, "el libro con ISBN")


# --- base genérica ---


class RepoSqlBase[T: EntidadBase, M: m.Base](ABC):
    """Base común: CRUD transaccional delegando el mapeo a las subclases."""

    modelo: type[M]

    def __init__(self, conexion: ConexionDB) -> None:
        self._conexion = conexion

    @abstractmethod
    def _a_entidad(self, modelo: M) -> T:
        """Convierte el modelo ORM en la entidad de dominio."""

    @abstractmethod
    def _a_modelo(self, entidad: T, sesion: Session) -> M:
        """Convierte la entidad en un modelo ORM nuevo, resolviendo sus FKs."""

    @abstractmethod
    def _buscar(self, sesion: Session, clave: Any) -> M | None:
        """Busca el modelo por su clave natural, o None si no existe."""

    @abstractmethod
    def _aplicar(self, modelo: M, entidad: T, sesion: Session) -> None:
        """Copia los datos de la entidad sobre un modelo existente."""

    def _select(self) -> Select[tuple[M]]:
        """Consulta base de los listados, ordenada por id."""
        return select(self.modelo).order_by(self.modelo.id)

    def _listar(self, stmt: Select[tuple[M]]) -> list[T]:
        """Ejecuta una consulta y convierte cada fila en entidad."""
        with self._conexion.crear_sesion() as sesion:
            return [self._a_entidad(modelo) for modelo in sesion.scalars(stmt)]

    def _leer_uno(self, clave: Any) -> T | None:
        """Lee una entidad por su clave natural, o None si no existe."""
        with self._conexion.crear_sesion() as sesion:
            modelo = self._buscar(sesion, clave)
            return self._a_entidad(modelo) if modelo is not None else None

    def crear(self, entidad: T) -> T:
        try:
            with self._conexion.transaccion() as sesion:
                sesion.add(self._a_modelo(entidad, sesion))
        except IntegrityError as error:
            raise ValueError(
                "Ya existe un registro con la misma clave natural."
            ) from error
        return entidad

    def leer_todos(self) -> list[T]:
        return self._listar(self._select())

    def actualizar(self, clave: Any, entidad: T) -> T:
        try:
            with self._conexion.transaccion() as sesion:
                modelo = self._buscar(sesion, clave)
                if modelo is None:
                    raise ValueError(f"No se encontró el registro con clave {clave!r}.")
                self._aplicar(modelo, entidad, sesion)
        except IntegrityError as error:
            raise ValueError(
                "Ya existe un registro con la misma clave natural."
            ) from error
        return entidad

    def eliminar(self, clave: Any) -> bool:
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, clave)
            if modelo is None:
                return False
            sesion.delete(modelo)
        return True


# --- repositorios concretos ---


class RepoGeneroSQL(RepoSqlBase[Genero, m.Genero], IRepositorioGenero):
    """CRUD de géneros sobre SQL. Clave natural: nombre del género."""

    modelo = m.Genero

    def _a_entidad(self, modelo: m.Genero) -> Genero:
        return _genero_entidad(modelo)

    def _a_modelo(self, entidad: Genero, sesion: Session) -> m.Genero:
        return m.Genero(genero=entidad.genero)

    def _buscar(self, sesion: Session, clave: str) -> m.Genero | None:
        return sesion.scalar(select(m.Genero).where(m.Genero.genero == clave))

    def _aplicar(self, modelo: m.Genero, entidad: Genero, sesion: Session) -> None:
        modelo.genero = entidad.genero

    def leer_por_nombre(self, nombre: str) -> Genero | None:
        return self._leer_uno(nombre)

    def leer_por_cadena(self, cadena: str) -> list[Genero]:
        return self._listar(self._select().where(m.Genero.genero.ilike(f"%{cadena}%")))


class RepoEditorialSQL(RepoSqlBase[Editorial, m.Editorial], IRepositorioEditorial):
    """CRUD de editoriales sobre SQL. Clave natural: proveedor."""

    modelo = m.Editorial

    def _a_entidad(self, modelo: m.Editorial) -> Editorial:
        return _editorial_entidad(modelo)

    def _a_modelo(self, entidad: Editorial, sesion: Session) -> m.Editorial:
        return m.Editorial(**entidad.model_dump())

    def _buscar(self, sesion: Session, clave: str) -> m.Editorial | None:
        return sesion.scalar(select(m.Editorial).where(m.Editorial.proveedor == clave))

    def _aplicar(
        self, modelo: m.Editorial, entidad: Editorial, sesion: Session
    ) -> None:
        for campo, valor in entidad.model_dump().items():
            setattr(modelo, campo, valor)

    def leer_por_proveedor(self, proveedor: str) -> Editorial | None:
        return self._leer_uno(proveedor)


class RepoMonedaSQL(RepoSqlBase[Moneda, m.Moneda], IRepositorioMoneda):
    """CRUD de monedas sobre SQL. Clave natural: código ISO 4217."""

    modelo = m.Moneda

    def _a_entidad(self, modelo: m.Moneda) -> Moneda:
        return _moneda_entidad(modelo)

    def _a_modelo(self, entidad: Moneda, sesion: Session) -> m.Moneda:
        return m.Moneda(codigo=entidad.codigo, nombre=entidad.nombre)

    def _buscar(self, sesion: Session, clave: str) -> m.Moneda | None:
        return sesion.scalar(
            select(m.Moneda).where(m.Moneda.codigo == normalizar_codigo(clave))
        )

    def _aplicar(self, modelo: m.Moneda, entidad: Moneda, sesion: Session) -> None:
        modelo.codigo = entidad.codigo
        modelo.nombre = entidad.nombre

    def leer_por_codigo(self, codigo: str) -> Moneda | None:
        return self._leer_uno(codigo)


class RepoTipoCotizacionSQL(
    RepoSqlBase[TipoCotizacion, m.TipoCotizacion], IRepositorioTipoCotizacion
):
    """CRUD de tipos de cotización sobre SQL. Clave natural: nombre del tipo."""

    modelo = m.TipoCotizacion

    def _a_entidad(self, modelo: m.TipoCotizacion) -> TipoCotizacion:
        return _tipo_entidad(modelo)

    def _a_modelo(self, entidad: TipoCotizacion, sesion: Session) -> m.TipoCotizacion:
        return m.TipoCotizacion(tipo=entidad.tipo)

    def _buscar(self, sesion: Session, clave: str) -> m.TipoCotizacion | None:
        return sesion.scalar(
            select(m.TipoCotizacion).where(m.TipoCotizacion.tipo == clave)
        )

    def _aplicar(
        self, modelo: m.TipoCotizacion, entidad: TipoCotizacion, sesion: Session
    ) -> None:
        modelo.tipo = entidad.tipo

    def leer_por_tipo(self, tipo: str) -> TipoCotizacion | None:
        return self._leer_uno(tipo)


class RepoLibroSQL(RepoSqlBase[Libro, m.Libro], IRepositorioLibro):
    """CRUD de libros sobre SQL. Clave natural: ISBN.

    Al eliminar un libro, el ORM borra en cascada su stock y sus precios dentro
    de la misma transacción (ver `models.Libro`).
    """

    modelo = m.Libro

    def _a_entidad(self, modelo: m.Libro) -> Libro:
        return _libro_entidad(modelo)

    def _a_modelo(self, entidad: Libro, sesion: Session) -> m.Libro:
        return m.Libro(
            isbn=entidad.isbn,
            titulo=entidad.titulo,
            autor=entidad.autor,
            editorial_id=_id_editorial(sesion, entidad.editorial.proveedor),
            genero_id=_id_genero(sesion, entidad.genero.genero),
        )

    def _select(self) -> Select[tuple[m.Libro]]:
        return (
            super()
            ._select()
            .options(selectinload(m.Libro.editorial), selectinload(m.Libro.genero))
        )

    def _buscar(self, sesion: Session, clave: str) -> m.Libro | None:
        return sesion.scalar(select(m.Libro).where(m.Libro.isbn == clave))

    def _aplicar(self, modelo: m.Libro, entidad: Libro, sesion: Session) -> None:
        modelo.isbn = entidad.isbn
        modelo.titulo = entidad.titulo
        modelo.autor = entidad.autor
        modelo.editorial_id = _id_editorial(sesion, entidad.editorial.proveedor)
        modelo.genero_id = _id_genero(sesion, entidad.genero.genero)

    def leer_por_isbn(self, isbn: str) -> Libro | None:
        return self._leer_uno(isbn)

    def leer_por_editorial(self, proveedor: str) -> list[Libro]:
        return self._listar(
            self._select().join(m.Editorial).where(m.Editorial.proveedor == proveedor)
        )

    def leer_por_genero(self, genero: str) -> list[Libro]:
        return self._listar(
            self._select().join(m.Genero).where(m.Genero.genero == genero)
        )


class RepoStockSQL(RepoSqlBase[Stock, m.Stock], IRepositorioStock):
    """CRUD de stock sobre SQL. Clave natural: ISBN del libro."""

    modelo = m.Stock

    def _a_entidad(self, modelo: m.Stock) -> Stock:
        return _stock_entidad(modelo)

    def _a_modelo(self, entidad: Stock, sesion: Session) -> m.Stock:
        return m.Stock(
            libro_id=_id_libro(sesion, entidad.libro.isbn),
            existencia=entidad.existencia,
        )

    def _select(self) -> Select[tuple[m.Stock]]:
        libro = selectinload(m.Stock.libro)
        return (
            super()
            ._select()
            .options(
                libro.selectinload(m.Libro.editorial),
                libro.selectinload(m.Libro.genero),
            )
        )

    def _buscar(self, sesion: Session, clave: str) -> m.Stock | None:
        return sesion.scalar(select(m.Stock).join(m.Libro).where(m.Libro.isbn == clave))

    def _aplicar(self, modelo: m.Stock, entidad: Stock, sesion: Session) -> None:
        modelo.libro_id = _id_libro(sesion, entidad.libro.isbn)
        modelo.existencia = entidad.existencia

    def leer_por_libro(self, isbn: str) -> Stock | None:
        return self._leer_uno(isbn)


class RepoPrecioSQL(RepoSqlBase[Precio, m.Precio], IRepositorioPrecio):
    """CRUD de precios sobre SQL. Clave natural: (ISBN, código de moneda)."""

    modelo = m.Precio

    def _a_entidad(self, modelo: m.Precio) -> Precio:
        return _precio_entidad(modelo)

    def _a_modelo(self, entidad: Precio, sesion: Session) -> m.Precio:
        return m.Precio(
            libro_id=_id_libro(sesion, entidad.libro.isbn),
            moneda_id=_id_moneda(sesion, entidad.moneda.codigo),
            valor=entidad.valor,
        )

    def _select(self) -> Select[tuple[m.Precio]]:
        libro = selectinload(m.Precio.libro)
        return (
            super()
            ._select()
            .options(
                libro.selectinload(m.Libro.editorial),
                libro.selectinload(m.Libro.genero),
                selectinload(m.Precio.moneda),
            )
        )

    def _buscar(self, sesion: Session, clave: tuple[str, str]) -> m.Precio | None:
        isbn, codigo = clave
        return sesion.scalar(
            select(m.Precio)
            .join(m.Libro)
            .join(m.Moneda)
            .where(m.Libro.isbn == isbn, m.Moneda.codigo == normalizar_codigo(codigo))
        )

    def _aplicar(self, modelo: m.Precio, entidad: Precio, sesion: Session) -> None:
        modelo.libro_id = _id_libro(sesion, entidad.libro.isbn)
        modelo.moneda_id = _id_moneda(sesion, entidad.moneda.codigo)
        modelo.valor = entidad.valor

    def leer_por_libro(self, isbn: str) -> list[Precio]:
        return self._listar(self._select().join(m.Libro).where(m.Libro.isbn == isbn))

    def leer_por_moneda(self, codigo: str) -> list[Precio]:
        return self._listar(
            self._select()
            .join(m.Moneda)
            .where(m.Moneda.codigo == normalizar_codigo(codigo))
        )

    def leer_por_libro_y_moneda(self, isbn: str, codigo: str) -> Precio | None:
        return self._leer_uno((isbn, codigo))


class RepoCotizacionDolarSQL(
    RepoSqlBase[CotizacionDolar, m.CotizacionDolar], IRepositorioCotizacionDolar
):
    """CRUD de cotizaciones sobre SQL. Clave natural: (tipo, fecha)."""

    modelo = m.CotizacionDolar

    def _a_entidad(self, modelo: m.CotizacionDolar) -> CotizacionDolar:
        return _cotizacion_entidad(modelo)

    def _a_modelo(self, entidad: CotizacionDolar, sesion: Session) -> m.CotizacionDolar:
        return m.CotizacionDolar(
            tipo_cotizacion_id=_id_tipo(sesion, entidad.tipo_cotizacion.tipo),
            fecha=entidad.fecha,
            valor_compra=entidad.valor_compra,
            valor_venta=entidad.valor_venta,
        )

    def _select(self) -> Select[tuple[m.CotizacionDolar]]:
        return (
            super()._select().options(selectinload(m.CotizacionDolar.tipo_cotizacion))
        )

    def _buscar(
        self, sesion: Session, clave: tuple[str, date]
    ) -> m.CotizacionDolar | None:
        tipo, fecha = clave
        return sesion.scalar(
            select(m.CotizacionDolar)
            .join(m.TipoCotizacion)
            .where(m.TipoCotizacion.tipo == tipo, m.CotizacionDolar.fecha == fecha)
        )

    def _aplicar(
        self, modelo: m.CotizacionDolar, entidad: CotizacionDolar, sesion: Session
    ) -> None:
        modelo.tipo_cotizacion_id = _id_tipo(sesion, entidad.tipo_cotizacion.tipo)
        modelo.fecha = entidad.fecha
        modelo.valor_compra = entidad.valor_compra
        modelo.valor_venta = entidad.valor_venta

    def _del_tipo(self, tipo: str) -> Select[tuple[m.CotizacionDolar]]:
        """Cotizaciones de un tipo, sin orden (cada consulta pone el suyo)."""
        return (
            self._select()
            .order_by(None)
            .join(m.TipoCotizacion)
            .where(m.TipoCotizacion.tipo == tipo)
        )

    def leer_por_tipo_y_fecha(self, tipo: str, fecha: date) -> CotizacionDolar | None:
        return self._leer_uno((tipo, fecha))

    def leer_historico_por_tipo(self, tipo: str) -> list[CotizacionDolar]:
        return self._listar(self._del_tipo(tipo).order_by(m.CotizacionDolar.fecha))

    def leer_ultima_por_tipo(self, tipo: str) -> CotizacionDolar | None:
        ultima = self._listar(
            self._del_tipo(tipo).order_by(m.CotizacionDolar.fecha.desc()).limit(1)
        )
        return ultima[0] if ultima else None

    def leer_ultimas(self) -> list[CotizacionDolar]:
        ultima_fecha = (
            select(
                m.CotizacionDolar.tipo_cotizacion_id,
                func.max(m.CotizacionDolar.fecha).label("fecha"),
            )
            .group_by(m.CotizacionDolar.tipo_cotizacion_id)
            .subquery()
        )
        return self._listar(
            self._select().join(
                ultima_fecha,
                (
                    m.CotizacionDolar.tipo_cotizacion_id
                    == ultima_fecha.c.tipo_cotizacion_id
                )
                & (m.CotizacionDolar.fecha == ultima_fecha.c.fecha),
            )
        )


class RepoPrecioWebSQL:
    """Persistencia de los datos de Cúspide obtenidos por el scraper.

    A diferencia de los repositorios CRUD, `PrecioWeb` es un registro de
    observación generado automáticamente: solo se crea y se lee, no se edita
    ni se borra por el usuario. Trabaja con el modelo ORM directamente.
    """

    def __init__(self, conexion: ConexionDB) -> None:
        self._conexion = conexion

    def crear(self, registro: m.PrecioWeb) -> m.PrecioWeb:
        """Guarda un registro de precio web y lo devuelve con su id."""
        with self._conexion.transaccion() as sesion:
            sesion.add(registro)
            sesion.flush()  # asigna el id antes de salir de la transacción
            sesion.expunge(registro)  # evita el refresh posterior sobre un objeto detached
        return registro

    def leer_todos(self) -> list[m.PrecioWeb]:
        """Devuelve todos los registros, ordenados por id."""
        with self._conexion.crear_sesion() as sesion:
            return list(sesion.scalars(select(m.PrecioWeb).order_by(m.PrecioWeb.id)))

    def leer_por_libro(self, isbn: str) -> list[m.PrecioWeb]:
        """Devuelve el histórico de precios web de un libro, por ISBN."""
        with self._conexion.crear_sesion() as sesion:
            return list(
                sesion.scalars(
                    select(m.PrecioWeb)
                    .join(m.Libro)
                    .where(m.Libro.isbn == isbn)
                    .order_by(m.PrecioWeb.fecha_extraccion, m.PrecioWeb.id)
                )
            )

    def leer_ultima_por_libro(self, isbn: str) -> m.PrecioWeb | None:
        """Devuelve el último registro de precio web de un libro, o None."""
        with self._conexion.crear_sesion() as sesion:
            return sesion.scalar(
                select(m.PrecioWeb)
                .join(m.Libro)
                .where(m.Libro.isbn == isbn)
                .order_by(m.PrecioWeb.fecha_extraccion.desc(), m.PrecioWeb.id.desc())
                .limit(1)
            )
