"""Servicio de análisis: la sesión paso a paso, el resultado y la explicación de cada token."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from application.archivos import cargar_fuente
from config import reglas
from core.errores import CATALOGO, ManejadorErrores
from core.lexer import Lexer, reconocer_lexema
from core.modelos import Diagnostico, TipoDiagnostico, TipoToken, Token
from core.simbolos import ResultadoInstalacion, TablaSimbolos, registrar_token
from core.validador import validar_estructura

FASE_LEXICA = "Léxico"
FASE_ESTRUCTURAL = "Estructura"
_MAX_LEXEMA_VISIBLE = 40


@dataclass(frozen=True)
class Paso:
    """Un avance del análisis: un token (fase léxica) o un diagnóstico estructural."""

    numero: int
    fase: str
    token: Token | None
    diagnosticos: tuple[Diagnostico, ...]
    instalacion: ResultadoInstalacion | None
    descripcion: str


@dataclass
class ResultadoAnalisis:
    """Resultado de un análisis, parcial mientras la sesión no termina."""

    fuente: str
    tokens: list[Token]
    manejador: ManejadorErrores
    tabla: TablaSimbolos
    terminado: bool = False

    @property
    def diagnosticos(self) -> list[Diagnostico]:
        """Diagnósticos reportados hasta ahora."""
        return self.manejador.diagnosticos

    @property
    def es_valida_lexicamente(self) -> bool:
        """True si no hay diagnósticos léxicos."""
        return not self.manejador.hay_errores(TipoDiagnostico.LEXICO)

    @property
    def es_valida_estructuralmente(self) -> bool:
        """True si no hay diagnósticos estructurales."""
        return not self.manejador.hay_errores(TipoDiagnostico.ESTRUCTURAL)

    @property
    def es_valida(self) -> bool:
        """Cadena de entrada válida: análisis terminado y sin errores léxicos ni estructurales."""
        return self.terminado and self.es_valida_lexicamente and self.es_valida_estructuralmente

    def conteo_por_tipo(self) -> dict[TipoToken, int]:
        """Tokens por categoría, solo de las que aparecen."""
        conteo = {tipo: 0 for tipo in TipoToken}
        for token in self.tokens:
            conteo[token.tipo] += 1
        return {tipo: n for tipo, n in conteo.items() if n > 0}

    def lineas_invalidas(self) -> list[int]:
        """Líneas con al menos un diagnóstico léxico, ordenadas y sin repetir."""
        lineas = {d.linea for d in self.manejador.por_tipo(TipoDiagnostico.LEXICO)}
        return sorted(lineas)

    @property
    def cantidad_lineas(self) -> int:
        """0 si la fuente está vacía; si no, saltos de línea + 1."""
        return 0 if self.fuente == "" else self.fuente.count("\n") + 1

    @property
    def cantidad_caracteres(self) -> int:
        """Caracteres de la fuente."""
        return len(self.fuente)


@dataclass(frozen=True)
class ExplicacionToken:
    """Todo lo que la pestaña Autómatas muestra de un token."""

    token: Token
    categoria: str
    descripcion: str
    regex: str | None
    reconocedor: str
    recorrido: tuple[str, ...]
    detalle: str


def _visible(lexema: str) -> str:
    """Lexema en una sola línea (saltos como ⏎) y recortado a 40 caracteres."""
    texto = lexema.replace("\n", "⏎")
    return texto if len(texto) <= _MAX_LEXEMA_VISIBLE else texto[:_MAX_LEXEMA_VISIBLE] + "…"


def _texto_instalacion(instalacion: ResultadoInstalacion) -> str:
    if not instalacion.es_nueva:
        estado = "repetida"
    elif instalacion.hubo_colision:
        estado = "colisión"
    else:
        estado = "nueva"
    if instalacion.redimensiono:  # la colisión, si la hubo, fue antes de crecer; la cubeta que se muestra es la nueva
        return f"tabla: {estado}; tabla redimensionada, ahora en cubeta {instalacion.indice}"
    return f"tabla: {estado}, cubeta {instalacion.indice}"


class SesionAnalisis:
    """Análisis progresivo: cada llamada a siguiente_paso() avanza un token."""

    def __init__(self, fuente: str, capacidad_tabla: int = reglas.CAPACIDAD_INICIAL_TABLA) -> None:
        manejador = ManejadorErrores()
        # El lexer reporta en un manejador propio que se vacía en cada paso; así los
        # diagnósticos del paso salen sin copiar la lista completa.
        self._lexico = ManejadorErrores()
        self._tokens = Lexer(fuente, self._lexico).tokens()
        self._resultado = ResultadoAnalisis(fuente, [], manejador, TablaSimbolos(capacidad_tabla))
        self._anterior: Token | None = None      # último token significativo
        self._numero = 0
        self._lexico_agotado = False
        self._estructurales: list[Diagnostico] = []

    @property
    def terminada(self) -> bool:
        """True cuando ya no quedan pasos."""
        return self._resultado.terminado

    @property
    def resultado(self) -> ResultadoAnalisis:
        """Resultado parcial; siempre es el mismo objeto, que va creciendo."""
        return self._resultado

    def siguiente_paso(self) -> Paso | None:
        """Avanza un paso; None cuando el análisis ya terminó."""
        if self.terminada:
            return None
        manejador = self._resultado.manejador
        if not self._lexico_agotado:
            token = next(self._tokens, None)
            nuevos = self._lexico.diagnosticos
            self._lexico.limpiar()
            manejador.extender(nuevos)
            if token is not None:
                return self._paso_lexico(token, tuple(nuevos))
            self._lexico_agotado = True
            self._estructurales = validar_estructura(self._resultado.tokens)
            manejador.extender(self._estructurales)
        if self._estructurales:
            diagnostico = self._estructurales.pop(0)
            descripcion = (f"[{diagnostico.linea}:{diagnostico.columna}] Estructura: "
                           f"✗ {diagnostico.codigo} {diagnostico.titulo}")
            return self._nuevo_paso(FASE_ESTRUCTURAL, None, (diagnostico,), None, descripcion)
        self._resultado.terminado = True
        return None

    def pasos(self) -> Iterator[Paso]:
        """Los pasos que faltan, uno por uno."""
        return iter(self.siguiente_paso, None)

    def terminar(self) -> ResultadoAnalisis:
        """Consume los pasos que falten y devuelve el resultado completo."""
        for _ in self.pasos():
            pass
        return self._resultado

    def _paso_lexico(self, token: Token, diagnosticos: tuple[Diagnostico, ...]) -> Paso:
        self._resultado.tokens.append(token)
        instalacion = registrar_token(self._resultado.tabla, token, self._anterior)
        if token.es_significativo:
            self._anterior = token
        partes = [f"[{token.linea}:{token.columna}] {token.tipo.value} '{_visible(token.lexema)}'"]
        partes += [f"✗ {d.codigo}" for d in diagnosticos]
        if instalacion is not None:
            partes.append(_texto_instalacion(instalacion))
        return self._nuevo_paso(FASE_LEXICA, token, diagnosticos, instalacion, " · ".join(partes))

    def _nuevo_paso(self, fase: str, token: Token | None, diagnosticos: tuple[Diagnostico, ...],
                    instalacion: ResultadoInstalacion | None, descripcion: str) -> Paso:
        self._numero += 1
        return Paso(self._numero, fase, token, diagnosticos, instalacion, descripcion)


def analizar_texto(fuente: str) -> ResultadoAnalisis:
    """Analiza todo el texto de una vez."""
    return SesionAnalisis(fuente).terminar()


def analizar_archivo(ruta: str | Path) -> ResultadoAnalisis:
    """Lee el archivo (ErrorArchivo si no se puede) y lo analiza."""
    return analizar_texto(cargar_fuente(ruta))


def tokenizar(fuente: str) -> list[Token]:
    """Solo el lexer, sin tabla ni validador; basta para colorear el editor."""
    return Lexer(fuente).analizar()


def explicar_token(token: Token, tabla: TablaSimbolos | None = None) -> ExplicacionToken:
    """Reúne categoría, regex, recorrido del AFD y datos de la tabla de un token."""
    info = reglas.INFO_CATEGORIAS[token.tipo]
    coincidencia = reconocer_lexema(token.lexema, 0)
    descripcion = info["descripcion"]
    if token.tipo == TipoToken.PALABRA_RESERVADA:
        descripcion += " " + reglas.PALABRAS_RESERVADAS[token.lexema]
    lineas = [
        f"Lexema: {_visible(token.lexema)}",
        f"Categoría: {token.tipo.value}",
        f"Posición: línea {token.linea}, columna {token.columna}",
        f"Descripción: {descripcion}",
        f"Regla: {info['regex'] or '(ninguna)'}",
        f"Reconocedor: {coincidencia.reconocedor}",
    ]
    if coincidencia.recorrido:
        lineas.append("Recorrido: " + " → ".join(coincidencia.recorrido))
    if token.tipo == TipoToken.ERROR and coincidencia.codigo_error:
        datos = CATALOGO[coincidencia.codigo_error]
        # Se vuelve a reconocer el lexema para dar la misma sugerencia que recibió el diagnóstico
        # (la de LEX-001 para `&`, por ejemplo) sin copiar esa regla aquí.
        reanalisis = Lexer(token.lexema)
        reanalisis.analizar()
        sugerencia = next((d.sugerencia for d in reanalisis.manejador.diagnosticos), datos["sugerencia"])
        lineas.append(f"Error {coincidencia.codigo_error}: {datos['titulo']}")
        lineas.append(f"Sugerencia: {sugerencia}")
    entrada = tabla.buscar(token.lexema) if tabla is not None else None
    if tabla is not None and entrada is not None:
        lineas.append(
            f"Tabla de símbolos: hash {entrada.valor_hash} · cubeta {tabla.indice(token.lexema)} "
            f"(capacidad {tabla.capacidad}) · tipo {entrada.tipo_dato or '-'} · "
            f"apariciones {len(entrada.apariciones)}")
    return ExplicacionToken(token, token.tipo.value, descripcion, info["regex"],
                            coincidencia.reconocedor, coincidencia.recorrido, "\n".join(lineas))
