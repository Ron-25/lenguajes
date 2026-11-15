"""Lectura, escritura y validacion de archivos fuente (errores ARC-...)."""
from __future__ import annotations

from pathlib import Path

from config import reglas
from core.errores import crear_diagnostico
from core.modelos import Diagnostico


class ErrorArchivo(Exception):
    """Error de archivo que transporta su Diagnostico para mostrarlo con el formato comun."""

    def __init__(self, diagnostico: Diagnostico) -> None:
        super().__init__(diagnostico.mensaje)
        self.diagnostico = diagnostico


def _error(codigo: str, ruta: Path) -> ErrorArchivo:
    return ErrorArchivo(crear_diagnostico(codigo, lexema=ruta.name))


def cargar_fuente(ruta: str | Path) -> str:
    """Lee un archivo fuente validandolo; lanza ErrorArchivo (ARC-001 a ARC-006)."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise _error("ARC-001", ruta)
    if ruta.is_dir():
        raise _error("ARC-005", ruta)
    if ruta.suffix.lower() not in reglas.EXTENSIONES_PERMITIDAS:
        raise _error("ARC-002", ruta)
    try:
        if ruta.stat().st_size > reglas.TAMANO_MAXIMO_BYTES:
            raise _error("ARC-006", ruta)
        datos = ruta.read_bytes()
    except OSError:
        raise _error("ARC-005", ruta) from None
    try:
        texto = datos.decode("utf-8-sig")  # acepta (y quita) la marca BOM
    except UnicodeDecodeError:
        raise _error("ARC-004", ruta) from None
    if not texto.strip(reglas.ESPACIOS):  # "solo espacios" segun el lenguaje, no segun Unicode
        raise _error("ARC-003", ruta)
    return texto.replace("\r\n", "\n").replace("\r", "\n")


def guardar_fuente(ruta: str | Path, contenido: str) -> None:
    """Guarda el texto en UTF-8; OSError o texto no codificable se convierten en ARC-005."""
    ruta = Path(ruta)
    try:
        datos = contenido.encode(reglas.CODIFICACION)  # antes de abrir: si falla, no se trunca el archivo
        ruta.write_bytes(datos)
    except (OSError, UnicodeEncodeError):
        raise _error("ARC-005", ruta) from None


def listar_ejemplos(directorio: str | Path | None = None) -> list[Path]:
    """Archivos de ejemplo con extension permitida, ordenados por nombre."""
    if directorio is None:
        directorio = Path(__file__).resolve().parent.parent / "ejemplos"
    directorio = Path(directorio)
    if not directorio.is_dir():
        return []
    return sorted(
        (p for p in directorio.iterdir()
         if p.is_file() and p.suffix.lower() in reglas.EXTENSIONES_PERMITIDAS),
        key=lambda p: p.name,
    )
