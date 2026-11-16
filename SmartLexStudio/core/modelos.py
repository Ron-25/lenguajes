"""Datos del dominio: categorías de token, tokens, diagnósticos y entradas de la tabla de símbolos."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TipoToken(Enum):
    """Categorías de token; el valor es el nombre que se muestra en pantalla."""

    PALABRA_RESERVADA = "Palabra reservada"
    IDENTIFICADOR = "Identificador"
    ENTERO = "Entero"
    DECIMAL = "Decimal"
    DURACION = "Duración"
    CADENA = "Cadena"
    OPERADOR_ARITMETICO = "Operador aritmético"
    OPERADOR_RELACIONAL = "Operador relacional"
    OPERADOR_LOGICO = "Operador lógico"
    ASIGNACION = "Asignación"
    DELIMITADOR = "Delimitador"
    COMENTARIO = "Comentario"
    ERROR = "Error"


class TipoDiagnostico(Enum):
    """De dónde viene un diagnóstico."""

    LEXICO = "Léxico"
    ESTRUCTURAL = "Estructural"
    ARCHIVO = "Archivo"


@dataclass(frozen=True)
class Token:
    """Un lexema con su categoría y su posición (línea y columna empiezan en 1)."""

    tipo: TipoToken
    lexema: str
    linea: int
    columna: int

    @property
    def longitud(self) -> int:
        """Caracteres del lexema."""
        return len(self.lexema)

    @property
    def es_significativo(self) -> bool:
        """Falso para comentarios y errores: el validador estructural no los mira."""
        return self.tipo not in (TipoToken.COMENTARIO, TipoToken.ERROR)


@dataclass(frozen=True)
class Diagnostico:
    """Un error con código, mensaje, sugerencia y posición (0 y 0 en los de archivo)."""

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
    """Una fila de la tabla de símbolos; acumula las apariciones del lexema."""

    lexema: str
    categoria: TipoToken
    valor_hash: int
    tipo_dato: str | None = None
    valor: object = None
    linea_declaracion: int | None = None
    apariciones: list[tuple[int, int]] = field(default_factory=list)
