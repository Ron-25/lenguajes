"""Motor de autómatas finitos deterministas: no sabe nada de FlowLang, solo lee la tabla que recibe."""
from __future__ import annotations

from dataclasses import dataclass

from config import reglas
from core.modelos import TipoToken


def clase_caracter(caracter: str) -> str:
    """Clase del carácter (LETRA, DIGITO o SALTO); los demás son su propia clase."""
    if caracter in reglas.LETRAS:
        return reglas.LETRA
    if caracter in reglas.DIGITOS:
        return reglas.DIGITO
    if caracter == "\n":
        return reglas.SALTO
    return caracter


@dataclass(frozen=True)
class ResultadoAFD:
    """Prefijo más largo que terminó en estado final (longitud 0 si ninguno), con el recorrido de estados."""

    longitud: int
    tipo: TipoToken | None
    codigo_error: str | None
    recorrido: tuple[str, ...]


class AFD:
    """Autómata descrito por una tabla: estado inicial, transiciones y estados finales."""

    def __init__(self, definicion: dict) -> None:
        self.nombre: str = definicion["nombre"]
        self.inicial: str = definicion["inicial"]
        self.transiciones: dict[str, dict[str, str]] = definicion["transiciones"]
        self.aceptacion: dict[str, TipoToken] = definicion["aceptacion"]
        self.errores: dict[str, str] = definicion["errores"]

    def siguiente_estado(self, estado: str, caracter: str) -> str | None:
        """Función de transición.

        Se prueba primero el carácter exacto, después su clase y al final OTRO. Ese orden
        permite que q1 de los números distinga `s` de las demás letras. OTRO no consume
        saltos de línea, para que las cadenas y los comentarios de línea terminen en ellos.
        """
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
        """Corre el autómata desde `inicio` y devuelve el prefijo más largo que terminó en estado final.

        No se detiene en el primer estado final: sigue mientras haya transición y se queda con
        el último. Así `10ms` termina en q7 y no en q8 (`10m`). Los estados de error también
        cuentan como finales, para consumir el lexema mal formado completo.
        """
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
        """True si la cadena completa termina en un estado de aceptación (los de error no cuentan)."""
        resultado = self.reconocer(cadena, 0)
        return (
            len(cadena) > 0
            and resultado.longitud == len(cadena)
            and resultado.tipo is not None
        )
