"""Motor generico de automatas finitos deterministas dirigido por tabla de transiciones."""
from __future__ import annotations

from dataclasses import dataclass

from config import reglas
from core.modelos import TipoToken


def clase_caracter(caracter: str) -> str:
    """Devuelve LETRA, DIGITO o SALTO segun las reglas; si no, el propio caracter."""
    if caracter in reglas.LETRAS:
        return reglas.LETRA
    if caracter in reglas.DIGITOS:
        return reglas.DIGITO
    if caracter == "\n":
        return reglas.SALTO
    return caracter


@dataclass(frozen=True)
class ResultadoAFD:
    """Prefijo mas largo que termino en estado final (longitud 0 si ninguno)."""

    longitud: int
    tipo: TipoToken | None
    codigo_error: str | None
    recorrido: tuple[str, ...]


class AFD:
    """Automata descrito por una tabla: estado inicial, transiciones y estados finales."""

    def __init__(self, definicion: dict) -> None:
        self.nombre: str = definicion["nombre"]
        self.inicial: str = definicion["inicial"]
        self.transiciones: dict[str, dict[str, str]] = definicion["transiciones"]
        self.aceptacion: dict[str, TipoToken] = definicion["aceptacion"]
        self.errores: dict[str, str] = definicion["errores"]

    def siguiente_estado(self, estado: str, caracter: str) -> str | None:
        """Funcion de transicion: caracter exacto, luego su clase, luego OTRO (salvo salto)."""
        fila = self.transiciones.get(estado)
        if fila is None:
            return None
        if caracter in fila:
            return fila[caracter]
        clase = clase_caracter(caracter)
        if clase in fila:
            return fila[clase]
        if caracter != "\n" and reglas.OTRO in fila:
            return fila[reglas.OTRO]
        return None

    def reconocer(self, texto: str, inicio: int = 0) -> ResultadoAFD:
        """Ejecuta el automata desde `inicio` y devuelve el prefijo mas largo en estado final."""
        estado = self.inicial
        visitados = [estado]
        mejor = ResultadoAFD(0, None, None, (estado,))
        posicion = inicio
        while posicion < len(texto):
            estado = self.siguiente_estado(estado, texto[posicion])
            if estado is None:
                break
            posicion += 1
            visitados.append(estado)
            if estado in self.aceptacion or estado in self.errores:
                mejor = ResultadoAFD(
                    posicion - inicio,
                    self.aceptacion.get(estado),
                    self.errores.get(estado),
                    tuple(visitados),
                )
        return mejor

    def acepta(self, cadena: str) -> bool:
        """True si la cadena completa (no vacia) termina en un estado final de token."""
        resultado = self.reconocer(cadena, 0)
        return (
            len(cadena) > 0
            and resultado.longitud == len(cadena)
            and resultado.tipo is not None
        )
