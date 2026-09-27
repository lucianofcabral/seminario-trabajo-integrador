from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator


class Genero(BaseModel):
    """Genero del libro."""

    id: int | None = None
    genero: str = Field(..., min_length=3, description="Categoría del género")
    libros: list[Libro] = Field(
        default_factory=list,
        description="Libros asociados al género",
        exclude=True,
    )


class Editorial(BaseModel):
    id: int | None = None
    proveedor: str = Field(
        ..., min_length=3, description="Nombre único de la editorial"
    )
    pais: str = Field(..., min_length=3, description="País de la editorial")
    provincia: str = Field(..., min_length=3, description="Provincia de la editorial")
    localidad: str = Field(..., min_length=3, description="Localidad de la editorial")
    domicilio: str = Field(..., min_length=3, description="Domicilio de la editorial")
    telefono: str | None = Field(
        ..., min_length=3, description="Teléfono de la editorial"
    )
    email: EmailStr = Field(..., description="Email de la editorial")
    responsable: str = Field(
        ..., min_length=3, description="Responsable de la editorial"
    )
    libros: list[Libro] = Field(
        default_factory=list,
        description="Libros asociados a la editorial",
        exclude=True,
    )


class Stock(BaseModel):
    id: int | None = None
    libro_id: int = Field(..., description="ID del libro")
    existencia: int = Field(0, ge=0, description="Cantidad de libros en stock actual")


class Libro(BaseModel):
    id: int | None = None
    isbn: str = Field(..., min_length=10, max_length=17, description="ISBN del libro")
    titulo: str = Field(..., min_length=3, description="Título del libro")
    autor: str = Field(..., min_length=3, description="Autor del libro")
    editorial_id: int
    genero_id: int


class Moneda(BaseModel):
    id: int | None = None
    codigo: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Código nternacional de la moneda de 3 dígitos.",
    )
    nombre: str = Field(..., min_length=3, description="Nombre de la moneda")

    @field_validator("codigo")
    @classmethod
    def a_mayusculas(cls, v: str) -> str:
        return v.upper().replace(" ", "")


class Precio(BaseModel):
    id: int | None = None
    libro_id: int
    moneda_id: int
    valor: float = Field(..., description="Valor del libro expresado en la moneda")


class TipoCotizacion(BaseModel):
    id: int | None = None
    tipo: str = Field(
        ...,
        min_length=1,
        description="Tipo de cotización del dolar, ejemplo: 'BLUE', 'MEP', etc.",
    )


class Cotizacion(BaseModel):
    id: int | None = None
    tipo_cotizacion_id: int
    fecha: date = Field(..., description="Fecha de la cotización")
    valor_pesos: float = Field(..., description="Valor del dolar en la fecha")
