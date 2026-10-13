"""Funciones auxiliares compartidas entre capas."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from dotenv import find_dotenv, load_dotenv

ZONA_ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")


def cargar_entorno() -> None:
    """Carga las variables de entorno de `.env.local` y `.env`.

    `.env` está versionado y solo tiene configuración pública (`API_URL`).
    Los secretos (credenciales de la base) van en `.env.local`, que no se
    versiona. Ninguno pisa variables ya definidas, así los secrets de Colab o
    del sistema siempre tienen prioridad.
    """
    load_dotenv(find_dotenv(".env.local"))
    load_dotenv(find_dotenv(".env"))


def normalizar_codigo(codigo: str) -> str:
    """Normaliza un código de moneda: mayúsculas y sin espacios (`" usd "` -> `"USD"`)."""
    return codigo.upper().replace(" ", "")


def fecha_argentina(momento: datetime) -> date:
    """Fecha calendario en Argentina de un instante con zona horaria.

    A partir de las 21 h de Argentina, en UTC ya es el día siguiente.
    """
    return momento.astimezone(ZONA_ARGENTINA).date()
