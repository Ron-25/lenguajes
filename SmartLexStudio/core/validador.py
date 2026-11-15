"""Comprobaciones estructurales ligeras (inicio/fin y balance con pila), reglas E1-E4."""
from __future__ import annotations

from typing import Iterable

from config import reglas
from core.errores import crear_diagnostico
from core.modelos import Diagnostico, Token, TipoToken


def _es_palabra(token: Token, palabra: str) -> bool:
    return token.tipo == TipoToken.PALABRA_RESERVADA and token.lexema == palabra


def _diagnosticar(codigo: str, token: Token) -> Diagnostico:
    return crear_diagnostico(codigo, token.linea, token.columna, token.lexema)


def _validar_balance(tokens: list[Token]) -> list[Diagnostico]:
    """E4: usa una pila porque el balance de parentesis no es un lenguaje regular."""
    cierres = set(reglas.PARES_AGRUPACION.values())
    pila: list[Token] = []
    diagnosticos: list[Diagnostico] = []
    for token in tokens:
        if token.tipo != TipoToken.DELIMITADOR:
            continue
        if token.lexema in reglas.PARES_AGRUPACION:
            pila.append(token)
        elif token.lexema in cierres:
            if not pila:
                diagnosticos.append(_diagnosticar("SIN-004", token))
            else:
                apertura = pila.pop()
                if reglas.PARES_AGRUPACION[apertura.lexema] != token.lexema:
                    diagnosticos.append(_diagnosticar("SIN-006", token))
    diagnosticos.extend(_diagnosticar("SIN-005", apertura) for apertura in pila)
    return diagnosticos


def validar_estructura(tokens: Iterable[Token]) -> list[Diagnostico]:
    """Reglas E1-E4 sobre los tokens significativos, ordenado por (linea, columna)."""
    significativos = [t for t in tokens if t.es_significativo]
    if not significativos:
        return [crear_diagnostico("SIN-001", 1, 1)]
    diagnosticos: list[Diagnostico] = []
    if not _es_palabra(significativos[0], reglas.PALABRA_INICIO):
        diagnosticos.append(_diagnosticar("SIN-002", significativos[0]))
    if not _es_palabra(significativos[-1], reglas.PALABRA_FIN):
        diagnosticos.append(_diagnosticar("SIN-003", significativos[-1]))
    diagnosticos.extend(_validar_balance(significativos))
    return sorted(diagnosticos, key=lambda d: (d.linea, d.columna))
