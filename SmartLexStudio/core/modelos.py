"""Modelos de datos del dominio: tokens, diagnosticos y entradas de la tabla de simbolos."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TipoToken(Enum):
    """Categorias de token de FlowLang; el valor es el nombre para mostrar."""

    PALABRA_RESERVADA = "Palabra reservada"
    IDENTIFICADOR = "Identificador"
    ENTERO = "Entero"
    DECIMAL = "Decimal"
    CADENA = "Cadena"
    OPERADOR_ARITMETICO = "Operador aritmético"
    OPERADOR_RELACIONAL = "Operador relacional"
    OPERADOR_LOGICO = "Operador lógico"
    ASIGNACION = "Asignación"
    DELIMITADOR = "Delimitador"
    COMENTARIO = "Comentario"
    ERROR = "Error"


class TipoDiagnostico(Enum):
    """Origen de un diagnostico."""

    LEXICO = "Léxico"
    ESTRUCTURAL = "Estructural"
    ARCHIVO = "Archivo"


@dataclass(frozen=True)
class Token:
    """Un lexema reconocido con su categoria y su posicion (desde 1)."""

    tipo: TipoToken
    lexema: str
    linea: int
    columna: int

    @property
    def longitud(self) -> int:
        """Cantidad de caracteres del lexema."""
        return len(self.lexema)

    @property
    def es_significativo(self) -> bool:
        """False para comentarios y errores, que el validador ignora."""
        return self.tipo not in (TipoToken.COMENTARIO, TipoToken.ERROR)


@dataclass(frozen=True)
class Diagnostico:
    """Un error o aviso con codigo, mensaje, sugerencia y posicion (0 en los de archivo)."""

    codigo: str
    tipo: TipoDiagnostico
    titulo: str
    mensaje: str
    sugerencia: str
    linea: int
    columna: int
    lexema: str = ""


@dataclass
class EntradaSimbolo:
    """Una fila de la tabla de simbolos; acumula las apariciones del lexema."""

    lexema: str
    categoria: TipoToken
    valor_hash: int
    tipo_dato: str | None = None
    valor: object = None
    linea_declaracion: int | None = None
    apariciones: list[tuple[int, int]] = field(default_factory=list)
