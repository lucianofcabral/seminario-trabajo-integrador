"""Entidades del dominio: validación con Pydantic, sin id de persistencia.

La identidad de cada entidad es su clave natural (ISBN, código, nombre, proveedor,
tipo), no un id de base de datos. Las relaciones se modelan como referencias a
objetos: un `Libro` guarda su `Editorial` y su `Genero` completos.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class EntidadBase(BaseModel):
    """Base de todas las entidades del sistema.

    Encapsula el estado: los datos se validan al crear el objeto y también cada
    vez que se asigna un atributo, por lo que una entidad nunca queda inválida.
    """

    model_config = ConfigDict(validate_assignment=True, str_strip_whitespace=True)


class Genero(EntidadBase):
    """Categoría literaria a la que pertenece un libro."""

    genero: str = Field(..., min_length=3, description="Categoría del género")


class Editorial(EntidadBase):
    """Proveedor o distribuidora que provee los libros a la librería."""

    proveedor: str = Field(
        ..., min_length=3, description="Nombre único de la editorial"
    )
    pais: str = Field(..., min_length=3, description="País de la editorial")
    provincia: str = Field(..., min_length=3, description="Provincia de la editorial")
    localidad: str = Field(..., min_length=3, description="Localidad de la editorial")
    domicilio: str = Field(..., min_length=3, description="Domicilio de la editorial")
    telefono: str = Field(..., min_length=3, description="Teléfono de la editorial")
    email: EmailStr = Field(..., description="Email de la editorial")
    responsable: str = Field(
        ..., min_length=3, description="Responsable de la editorial"
    )


class Moneda(EntidadBase):
    """Moneda en la que se puede expresar un precio (ARS, USD, etc.)."""

    codigo: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Código internacional de la moneda de 3 dígitos.",
    )
    nombre: str = Field(..., min_length=3, description="Nombre de la moneda")

    @field_validator("codigo")
    @classmethod
    def a_mayusculas(cls, v: str) -> str:
        """Normaliza el código a mayúsculas y sin espacios."""
        return v.upper().replace(" ", "")


class TipoCotizacion(EntidadBase):
    """Tipo de cotización del dólar (Oficial, Blue, MEP, etc.)."""

    tipo: str = Field(
        ..., min_length=1, description="Tipo de cotización, p. ej. 'Blue', 'MEP'"
    )


class Libro(EntidadBase):
    """Título del catálogo de la librería; referencia su editorial y su género."""

    isbn: str = Field(..., min_length=10, max_length=17, description="ISBN del libro")
    titulo: str = Field(..., min_length=3, description="Título del libro")
    autor: str = Field(..., min_length=3, description="Autor del libro")
    editorial: Editorial = Field(..., description="Editorial del libro")
    genero: Genero = Field(..., description="Género del libro")


class Stock(EntidadBase):
    """Cantidad disponible de un libro."""

    libro: Libro = Field(..., description="Libro del stock")
    existencia: int = Field(0, ge=0, description="Cantidad de libros en stock actual")


class Precio(EntidadBase):
    """Valor de un libro expresado en una moneda determinada."""

    libro: Libro = Field(..., description="Libro del precio")
    moneda: Moneda = Field(..., description="Moneda del precio")
    valor: float = Field(
        ..., ge=0, description="Valor del libro expresado en la moneda"
    )


class CotizacionDolar(EntidadBase):
    """Registro histórico del valor del dólar para un tipo y una fecha."""

    tipo_cotizacion: TipoCotizacion = Field(..., description="Tipo de cotización")
    fecha: date = Field(..., description="Fecha de la cotización")
    valor_pesos: float = Field(..., gt=0, description="Valor del dólar en pesos")
