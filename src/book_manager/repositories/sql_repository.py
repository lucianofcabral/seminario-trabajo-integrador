"""Implementación de repositorios sobre SQLAlchemy.

Cada repositorio mapea entre la entidad de dominio (sin id, con referencias a
objetos) y el modelo ORM (con id y foreign keys). Las claves naturales localizan
los registros: ISBN, código de moneda, proveedor, nombre de género, etc.
"""

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from book_manager.database.connection import ConexionDB
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
        valor_pesos=modelo.valor_pesos,
    )


# --- resolución de foreign keys por clave natural ---


def _id_editorial(sesion: Session, proveedor: str) -> int:
    modelo = sesion.scalar(select(m.Editorial).where(m.Editorial.proveedor == proveedor))
    if modelo is None:
        raise ValueError(f"No existe la editorial {proveedor!r}.")
    return modelo.id


def _id_genero(sesion: Session, nombre: str) -> int:
    modelo = sesion.scalar(select(m.Genero).where(m.Genero.genero == nombre))
    if modelo is None:
        raise ValueError(f"No existe el género {nombre!r}.")
    return modelo.id


def _id_moneda(sesion: Session, codigo: str) -> int:
    codigo = codigo.upper().replace(" ", "")
    modelo = sesion.scalar(select(m.Moneda).where(m.Moneda.codigo == codigo))
    if modelo is None:
        raise ValueError(f"No existe la moneda {codigo!r}.")
    return modelo.id


def _id_tipo(sesion: Session, tipo: str) -> int:
    modelo = sesion.scalar(select(m.TipoCotizacion).where(m.TipoCotizacion.tipo == tipo))
    if modelo is None:
        raise ValueError(f"No existe el tipo de cotización {tipo!r}.")
    return modelo.id


def _id_libro(sesion: Session, isbn: str) -> int:
    modelo = sesion.scalar(select(m.Libro).where(m.Libro.isbn == isbn))
    if modelo is None:
        raise ValueError(f"No existe el libro con ISBN {isbn!r}.")
    return modelo.id


# --- base genérica ---


class RepoSqlBase[T, M]:
    """Base común: CRUD transaccional delegando el mapeo a las subclases."""

    def __init__(self, conexion: ConexionDB) -> None:
        self._conexion = conexion

    # hooks que cada repositorio concreto implementa
    def _a_entidad(self, modelo: M) -> T:  # pragma: no cover - abstracto
        raise NotImplementedError

    def _a_modelo(self, entidad: T, sesion: Session) -> M:  # pragma: no cover
        raise NotImplementedError

    def _select(self):  # pragma: no cover - abstracto
        raise NotImplementedError

    def _buscar(self, sesion: Session, clave: Any):  # pragma: no cover - abstracto
        raise NotImplementedError

    def _aplicar(self, modelo: M, entidad: T, sesion: Session) -> None:  # pragma: no cover
        raise NotImplementedError

    def crear(self, entidad: T) -> T:
        try:
            with self._conexion.transaccion() as sesion:
                sesion.add(self._a_modelo(entidad, sesion))
        except IntegrityError as error:
            raise ValueError("Ya existe un registro con la misma clave natural.") from error
        return entidad

    def leer_todos(self) -> list[T]:
        with self._conexion.crear_sesion() as sesion:
            modelos = sesion.scalars(self._select()).all()
            return [self._a_entidad(modelo) for modelo in modelos]

    def actualizar(self, clave: Any, entidad: T) -> T:
        try:
            with self._conexion.transaccion() as sesion:
                modelo = self._buscar(sesion, clave)
                if modelo is None:
                    raise ValueError(f"No se encontró el registro con clave {clave!r}.")
                self._aplicar(modelo, entidad, sesion)
        except IntegrityError as error:
            raise ValueError("Ya existe un registro con la misma clave natural.") from error
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

    def _a_entidad(self, modelo: m.Genero) -> Genero:
        return _genero_entidad(modelo)

    def _a_modelo(self, entidad: Genero, sesion: Session) -> m.Genero:
        return m.Genero(genero=entidad.genero)

    def _select(self):
        return select(m.Genero)

    def _buscar(self, sesion: Session, clave: str):
        return sesion.scalar(select(m.Genero).where(m.Genero.genero == clave))

    def _aplicar(self, modelo: m.Genero, entidad: Genero, sesion: Session) -> None:
        modelo.genero = entidad.genero

    def leer_por_nombre(self, nombre: str) -> Genero | None:
        with self._conexion.crear_sesion() as sesion:
            modelo = self._buscar(sesion, nombre)
            return self._a_entidad(modelo) if modelo else None

    def leer_por_cadena(self, cadena: str) -> list[Genero]:
        with self._conexion.crear_sesion() as sesion:
            stmt = select(m.Genero).where(m.Genero.genero.ilike(f"%{cadena}%"))
            return [self._a_entidad(modelo) for modelo in sesion.scalars(stmt).all()]


class RepoEditorialSQL(RepoSqlBase[Editorial, m.Editorial], IRepositorioEditorial):
    """CRUD de editoriales sobre SQL. Clave natural: proveedor."""

    def _a_entidad(self, modelo: m.Editorial) -> Editorial:
        return _editorial_entidad(modelo)

    def _a_modelo(self, entidad: Editorial, sesion: Session) -> m.Editorial:
        return m.Editorial(
            proveedor=entidad.proveedor,
            pais=entidad.pais,
            provincia=entidad.provincia,
            localidad=entidad.localidad,
            domicilio=entidad.domicilio,
            telefono=entidad.telefono,
            email=entidad.email,
            responsable=entidad.responsable,
        )

    def _select(self):
        return select(m.Editorial)

    def _buscar(self, sesion: Session, clave: str):
        return sesion.scalar(select(m.Editorial).where(m.Editorial.proveedor == clave))

    def _aplicar(self, modelo: m.Editorial, entidad: Editorial, sesion: Session) -> None:
        modelo.proveedor = entidad.proveedor
        modelo.pais = entidad.pais
        modelo.provincia = entidad.provincia
        modelo.localidad = entidad.localidad
        modelo.domicilio = entidad.domicilio
        modelo.telefono = entidad.telefono
        modelo.email = entidad.email
        modelo.responsable = entidad.responsable

    def leer_por_proveedor(self, proveedor: str) -> Editorial | None:
        with self._conexion.crear_sesion() as sesion:
            modelo = self._buscar(sesion, proveedor)
            return self._a_entidad(modelo) if modelo else None


class RepoMonedaSQL(RepoSqlBase[Moneda, m.Moneda], IRepositorioMoneda):
    """CRUD de monedas sobre SQL. Clave natural: código ISO 4217."""

    def _a_entidad(self, modelo: m.Moneda) -> Moneda:
        return _moneda_entidad(modelo)

    def _a_modelo(self, entidad: Moneda, sesion: Session) -> m.Moneda:
        return m.Moneda(codigo=entidad.codigo, nombre=entidad.nombre)

    def _select(self):
        return select(m.Moneda)

    def _buscar(self, sesion: Session, clave: str):
        codigo = clave.upper().replace(" ", "")
        return sesion.scalar(select(m.Moneda).where(m.Moneda.codigo == codigo))

    def _aplicar(self, modelo: m.Moneda, entidad: Moneda, sesion: Session) -> None:
        modelo.codigo = entidad.codigo
        modelo.nombre = entidad.nombre

    def leer_por_codigo(self, codigo: str) -> Moneda | None:
        with self._conexion.crear_sesion() as sesion:
            modelo = self._buscar(sesion, codigo)
            return self._a_entidad(modelo) if modelo else None


class RepoTipoCotizacionSQL(
    RepoSqlBase[TipoCotizacion, m.TipoCotizacion], IRepositorioTipoCotizacion
):
    """CRUD de tipos de cotización sobre SQL. Clave natural: nombre del tipo."""

    def _a_entidad(self, modelo: m.TipoCotizacion) -> TipoCotizacion:
        return _tipo_entidad(modelo)

    def _a_modelo(self, entidad: TipoCotizacion, sesion: Session) -> m.TipoCotizacion:
        return m.TipoCotizacion(tipo=entidad.tipo)

    def _select(self):
        return select(m.TipoCotizacion)

    def _buscar(self, sesion: Session, clave: str):
        return sesion.scalar(
            select(m.TipoCotizacion).where(m.TipoCotizacion.tipo == clave)
        )

    def _aplicar(
        self, modelo: m.TipoCotizacion, entidad: TipoCotizacion, sesion: Session
    ) -> None:
        modelo.tipo = entidad.tipo

    def leer_por_tipo(self, tipo: str) -> TipoCotizacion | None:
        with self._conexion.crear_sesion() as sesion:
            modelo = self._buscar(sesion, tipo)
            return self._a_entidad(modelo) if modelo else None


class RepoLibroSQL(RepoSqlBase[Libro, m.Libro], IRepositorioLibro):
    """CRUD de libros sobre SQL. Clave natural: ISBN."""

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

    def _select(self):
        return select(m.Libro).options(
            selectinload(m.Libro.editorial), selectinload(m.Libro.genero)
        )

    def _buscar(self, sesion: Session, clave: str):
        return sesion.scalar(select(m.Libro).where(m.Libro.isbn == clave))

    def _aplicar(self, modelo: m.Libro, entidad: Libro, sesion: Session) -> None:
        modelo.isbn = entidad.isbn
        modelo.titulo = entidad.titulo
        modelo.autor = entidad.autor
        modelo.editorial_id = _id_editorial(sesion, entidad.editorial.proveedor)
        modelo.genero_id = _id_genero(sesion, entidad.genero.genero)

    def leer_por_isbn(self, isbn: str) -> Libro | None:
        with self._conexion.crear_sesion() as sesion:
            modelo = self._buscar(sesion, isbn)
            return self._a_entidad(modelo) if modelo else None

    def leer_por_editorial(self, proveedor: str) -> list[Libro]:
        with self._conexion.crear_sesion() as sesion:
            stmt = self._select().join(m.Editorial).where(m.Editorial.proveedor == proveedor)
            return [self._a_entidad(modelo) for modelo in sesion.scalars(stmt).all()]

    def leer_por_genero(self, genero: str) -> list[Libro]:
        with self._conexion.crear_sesion() as sesion:
            stmt = self._select().join(m.Genero).where(m.Genero.genero == genero)
            return [self._a_entidad(modelo) for modelo in sesion.scalars(stmt).all()]


class RepoStockSQL(RepoSqlBase[Stock, m.Stock], IRepositorioStock):
    """CRUD de stock sobre SQL. Clave natural: ISBN del libro."""

    def _a_entidad(self, modelo: m.Stock) -> Stock:
        return _stock_entidad(modelo)

    def _a_modelo(self, entidad: Stock, sesion: Session) -> m.Stock:
        return m.Stock(
            libro_id=_id_libro(sesion, entidad.libro.isbn),
            existencia=entidad.existencia,
        )

    def _select(self):
        return select(m.Stock).options(
            selectinload(m.Stock.libro).selectinload(m.Libro.editorial),
            selectinload(m.Stock.libro).selectinload(m.Libro.genero),
        )

    def _buscar(self, sesion: Session, clave: str):
        return sesion.scalar(
            select(m.Stock).join(m.Libro).where(m.Libro.isbn == clave)
        )

    def _aplicar(self, modelo: m.Stock, entidad: Stock, sesion: Session) -> None:
        modelo.libro_id = _id_libro(sesion, entidad.libro.isbn)
        modelo.existencia = entidad.existencia

    def leer_por_libro(self, isbn: str) -> Stock | None:
        with self._conexion.crear_sesion() as sesion:
            modelo = sesion.scalar(
                self._select().join(m.Libro).where(m.Libro.isbn == isbn)
            )
            return self._a_entidad(modelo) if modelo else None


class RepoPrecioSQL(RepoSqlBase[Precio, m.Precio], IRepositorioPrecio):
    """CRUD de precios sobre SQL. Clave natural: (ISBN, código de moneda)."""

    def _a_entidad(self, modelo: m.Precio) -> Precio:
        return _precio_entidad(modelo)

    def _a_modelo(self, entidad: Precio, sesion: Session) -> m.Precio:
        return m.Precio(
            libro_id=_id_libro(sesion, entidad.libro.isbn),
            moneda_id=_id_moneda(sesion, entidad.moneda.codigo),
            valor=entidad.valor,
        )

    def _select(self):
        return select(m.Precio).options(
            selectinload(m.Precio.libro).selectinload(m.Libro.editorial),
            selectinload(m.Precio.libro).selectinload(m.Libro.genero),
            selectinload(m.Precio.moneda),
        )

    def _buscar(self, sesion: Session, clave: tuple[str, str]):
        isbn, codigo = clave
        codigo = codigo.upper().replace(" ", "")
        return sesion.scalar(
            select(m.Precio)
            .join(m.Libro)
            .join(m.Moneda)
            .where(m.Libro.isbn == isbn, m.Moneda.codigo == codigo)
        )

    def _aplicar(self, modelo: m.Precio, entidad: Precio, sesion: Session) -> None:
        modelo.libro_id = _id_libro(sesion, entidad.libro.isbn)
        modelo.moneda_id = _id_moneda(sesion, entidad.moneda.codigo)
        modelo.valor = entidad.valor

    def leer_por_libro(self, isbn: str) -> list[Precio]:
        with self._conexion.crear_sesion() as sesion:
            stmt = self._select().join(m.Libro).where(m.Libro.isbn == isbn)
            return [self._a_entidad(modelo) for modelo in sesion.scalars(stmt).all()]

    def leer_por_moneda(self, codigo: str) -> list[Precio]:
        codigo = codigo.upper().replace(" ", "")
        with self._conexion.crear_sesion() as sesion:
            stmt = self._select().join(m.Moneda).where(m.Moneda.codigo == codigo)
            return [self._a_entidad(modelo) for modelo in sesion.scalars(stmt).all()]

    def leer_por_libro_y_moneda(self, isbn: str, codigo: str) -> Precio | None:
        with self._conexion.crear_sesion() as sesion:
            modelo = self._buscar(sesion, (isbn, codigo))
            return self._a_entidad(modelo) if modelo else None


class RepoCotizacionDolarSQL(
    RepoSqlBase[CotizacionDolar, m.CotizacionDolar], IRepositorioCotizacionDolar
):
    """CRUD de cotizaciones sobre SQL. Clave natural: (tipo, fecha)."""

    def _a_entidad(self, modelo: m.CotizacionDolar) -> CotizacionDolar:
        return _cotizacion_entidad(modelo)

    def _a_modelo(self, entidad: CotizacionDolar, sesion: Session) -> m.CotizacionDolar:
        return m.CotizacionDolar(
            tipo_cotizacion_id=_id_tipo(sesion, entidad.tipo_cotizacion.tipo),
            fecha=entidad.fecha,
            valor_pesos=entidad.valor_pesos,
        )

    def _select(self):
        return select(m.CotizacionDolar).options(
            selectinload(m.CotizacionDolar.tipo_cotizacion)
        )

    def _buscar(self, sesion: Session, clave: tuple[str, date]):
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
        modelo.valor_pesos = entidad.valor_pesos

    def leer_por_tipo_y_fecha(self, tipo: str, fecha: date) -> CotizacionDolar | None:
        with self._conexion.crear_sesion() as sesion:
            modelo = self._buscar(sesion, (tipo, fecha))
            return self._a_entidad(modelo) if modelo else None

    def leer_historico_por_tipo(self, tipo: str) -> list[CotizacionDolar]:
        with self._conexion.crear_sesion() as sesion:
            stmt = (
                self._select()
                .join(m.TipoCotizacion)
                .where(m.TipoCotizacion.tipo == tipo)
                .order_by(m.CotizacionDolar.fecha)
            )
            return [self._a_entidad(modelo) for modelo in sesion.scalars(stmt).all()]
