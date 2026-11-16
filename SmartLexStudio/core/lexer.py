"""Analizador lexico: coincidencia mas larga entre los AFD y la tabla de simbolos fijos."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from config import reglas
from core.afd import AFD
from core.errores import ManejadorErrores
from core.modelos import Token, TipoToken

# Los AFD se construyen una sola vez; el orden de AUTOMATAS es la prioridad.
_AUTOMATAS = tuple(AFD(definicion) for definicion in reglas.AUTOMATAS)
_SIMBOLOS = {**reglas.OPERADORES, **reglas.DELIMITADORES}
_NOMBRE_SIMBOLOS = "Tabla de operadores y delimitadores"
_LONGITUD_MAXIMA_SIMBOLO = max(len(simbolo) for simbolo in _SIMBOLOS)


@dataclass(frozen=True)
class Coincidencia:
    """Resultado de reconocer un lexema en una posicion del texto."""

    longitud: int
    tipo: TipoToken
    codigo_error: str | None
    reconocedor: str
    recorrido: tuple[str, ...]


def _mejor_simbolo(texto: str, posicion: int) -> Coincidencia | None:
    """Busca un operador o delimitador probando primero el largo mayor."""
    for largo in range(_LONGITUD_MAXIMA_SIMBOLO, 0, -1):
        simbolo = texto[posicion:posicion + largo]
        if len(simbolo) == largo and simbolo in _SIMBOLOS:
            return Coincidencia(largo, _SIMBOLOS[simbolo], None, _NOMBRE_SIMBOLOS, ())
    return None


def _candidatos(texto: str, posicion: int) -> Iterator[Coincidencia]:
    """Un candidato por cada reconocedor que consuma al menos un caracter."""
    for afd in _AUTOMATAS:
        resultado = afd.reconocer(texto, posicion)
        if resultado.longitud > 0:
            tipo = resultado.tipo if resultado.tipo is not None else TipoToken.ERROR
            yield Coincidencia(resultado.longitud, tipo, resultado.codigo_error,
                               afd.nombre, resultado.recorrido)
    simbolo = _mejor_simbolo(texto, posicion)
    if simbolo is not None:
        yield simbolo


def reconocer_lexema(texto: str, posicion: int = 0) -> Coincidencia:
    """Coincidencia mas larga en `posicion` (que no debe ser un espacio)."""
    ganador = None
    for candidato in _candidatos(texto, posicion):
        if ganador is None or candidato.longitud > ganador.longitud:  # empate: gana el primero
            ganador = candidato
    if ganador is None:
        return Coincidencia(1, TipoToken.ERROR, "LEX-001", "Ninguno", ())
    if ganador.tipo == TipoToken.IDENTIFICADOR:
        lexema = texto[posicion:posicion + ganador.longitud]
        if ganador.longitud > reglas.LONGITUD_MAXIMA_IDENTIFICADOR:
            return Coincidencia(ganador.longitud, TipoToken.ERROR, "LEX-005",
                                ganador.reconocedor, ganador.recorrido)
        if lexema in reglas.PALABRAS_RESERVADAS:
            return Coincidencia(ganador.longitud, TipoToken.PALABRA_RESERVADA, None,
                                ganador.reconocedor, ganador.recorrido)
    return ganador


class Lexer:
    """Recorre la fuente produciendo tokens; los errores se reportan sin detener el analisis."""

    def __init__(self, fuente: str, manejador: ManejadorErrores | None = None) -> None:
        self._fuente = fuente
        self.manejador: ManejadorErrores = manejador if manejador is not None else ManejadorErrores()

    def tokens(self) -> Iterator[Token]:
        """Generador perezoso de un solo uso: un token por lexema (incluye COMENTARIO y ERROR)."""
        fuente = self._fuente
        posicion, linea, columna = 0, 1, 1
        while posicion < len(fuente):
            caracter = fuente[posicion]
            if caracter in reglas.ESPACIOS:
                posicion += 1
                linea, columna = (linea + 1, 1) if caracter == "\n" else (linea, columna + 1)
                continue
            coincidencia = reconocer_lexema(fuente, posicion)
            lexema = fuente[posicion:posicion + coincidencia.longitud]
            if coincidencia.codigo_error is None:
                yield Token(coincidencia.tipo, lexema, linea, columna)
            else:
                self._reportar(coincidencia.codigo_error, lexema, linea, columna)
                yield Token(TipoToken.ERROR, lexema, linea, columna)
            posicion += coincidencia.longitud
            saltos = lexema.count("\n")
            if saltos:
                linea += saltos
                columna = len(lexema) - lexema.rfind("\n")
            else:
                columna += len(lexema)

    def analizar(self) -> list[Token]:
        """Todos los tokens de la fuente."""
        return list(self.tokens())

    def _reportar(self, codigo: str, lexema: str, linea: int, columna: int) -> None:
        """Registra el diagnostico de un lexema erroneo (uno por escape en LEX-006)."""
        if codigo == "LEX-006":
            self._reportar_escapes_invalidos(lexema, linea, columna)
        elif codigo == "LEX-001":
            sugerencia = reglas.SUGERENCIAS_CARACTER.get(lexema)
            self.manejador.reportar(codigo, linea, columna, lexema, sugerencia)
        else:
            self.manejador.reportar(codigo, linea, columna, lexema)

    def _reportar_escapes_invalidos(self, lexema: str, linea: int, columna: int) -> None:
        """Un LEX-006 por cada `\\x` invalido dentro de la cadena, en la posicion de su barra."""
        i = 1  # salta la comilla de apertura
        while i < len(lexema) - 1:
            if lexema[i] == "\\":
                if lexema[i + 1] not in reglas.ESCAPES_VALIDOS:
                    self.manejador.reportar("LEX-006", linea, columna + i, lexema[i:i + 2])
                i += 2
            else:
                i += 1
