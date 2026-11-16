"""Tabla de símbolos: tabla hash hecha a mano, con una lista por cubeta para las colisiones."""
from __future__ import annotations

import string
from dataclasses import dataclass
from typing import Callable

from config import reglas
from core.modelos import EntradaSimbolo, Token, TipoToken


def hash_polinomial(lexema: str) -> int:
    """Hash polinomial de base 31 (Horner) módulo 2^32: h = h * 31 + código del carácter."""
    valor = 0
    for caracter in lexema:
        valor = (valor * reglas.BASE_HASH + ord(caracter)) % reglas.MODULO_HASH
    return valor


def siguiente_primo(n: int) -> int:
    """Primer primo mayor o igual que n; la capacidad prima reparte mejor las cubetas."""
    candidato = max(n, 2)
    while any(candidato % d == 0 for d in range(2, int(candidato ** 0.5) + 1)):
        candidato += 1
    return candidato


@dataclass(frozen=True)
class ResultadoInstalacion:
    """Lo que pasó al instalar un token: su entrada, si era nueva, si colisionó y si hubo redimensionado."""

    entrada: EntradaSimbolo
    es_nueva: bool
    hubo_colision: bool
    indice: int
    redimensiono: bool


@dataclass(frozen=True)
class EstadisticasTabla:
    """Estado de la tabla en un momento dado."""

    capacidad: int
    cantidad: int
    factor_carga: float
    colisiones: int
    cubetas_ocupadas: int
    cadena_mas_larga: int
    redimensionados: int


class TablaSimbolos:
    """Tabla hash de lexemas; la función hash se recibe por el constructor para poder cambiarla."""

    def __init__(self, capacidad: int = reglas.CAPACIDAD_INICIAL_TABLA,
                 funcion_hash: Callable[[str], int] = hash_polinomial,
                 factor_carga_maximo: float = reglas.FACTOR_CARGA_MAXIMO) -> None:
        if capacidad < 1:
            raise ValueError("La capacidad debe ser al menos 1")
        self._capacidad = capacidad
        self._funcion_hash = funcion_hash
        self._factor_maximo = factor_carga_maximo
        self._cubetas: list[list[EntradaSimbolo]] = [[] for _ in range(capacidad)]
        self._cantidad = 0
        self._colisiones = 0
        self._redimensionados = 0

    @property
    def capacidad(self) -> int:
        """Cubetas que tiene ahora."""
        return self._capacidad

    @property
    def colisiones(self) -> int:
        """Colisiones acumuladas al insertar; redimensionar no las reinicia."""
        return self._colisiones

    def __len__(self) -> int:
        return self._cantidad

    def __contains__(self, lexema: str) -> bool:
        return self.buscar(lexema) is not None

    def indice(self, lexema: str) -> int:
        """Cubeta del lexema con la capacidad actual."""
        return self._funcion_hash(lexema) % self._capacidad

    def buscar(self, lexema: str) -> EntradaSimbolo | None:
        """Busca el lexema recorriendo solo su cubeta."""
        for entrada in self._cubetas[self.indice(lexema)]:
            if entrada.lexema == lexema:
                return entrada
        return None

    def instalar(self, token: Token) -> ResultadoInstalacion:
        """Agrega el lexema, o suma una aparición si ya estaba."""
        posicion = (token.linea, token.columna)
        existente = self.buscar(token.lexema)
        if existente is not None:
            existente.apariciones.append(posicion)
            return ResultadoInstalacion(existente, False, False, self.indice(token.lexema), False)
        cubeta = self._cubetas[self.indice(token.lexema)]
        hubo_colision = len(cubeta) > 0  # hay colisión si la cubeta ya tenía algo antes de insertar
        if hubo_colision:
            self._colisiones += 1
        entrada = EntradaSimbolo(token.lexema, token.tipo, self._funcion_hash(token.lexema),
                                 apariciones=[posicion])
        cubeta.append(entrada)
        self._cantidad += 1
        redimensiono = self._cantidad / self._capacidad > self._factor_maximo
        if redimensiono:
            self._redimensionar()
        return ResultadoInstalacion(entrada, True, hubo_colision,
                                    self.indice(token.lexema), redimensiono)

    def _redimensionar(self) -> None:
        """Duplica la capacidad (al primo siguiente) y recoloca las entradas con el hash que ya guardan."""
        antiguas = self._cubetas
        self._capacidad = siguiente_primo(2 * self._capacidad)
        self._cubetas = [[] for _ in range(self._capacidad)]
        for cubeta in antiguas:
            for entrada in cubeta:
                self._cubetas[entrada.valor_hash % self._capacidad].append(entrada)
        self._redimensionados += 1

    def cubetas(self) -> list[list[EntradaSimbolo]]:
        """Copia de las cubetas para mostrarlas sin tocar la tabla."""
        return [list(cubeta) for cubeta in self._cubetas]

    def entradas(self) -> list[EntradaSimbolo]:
        """Todas las entradas, por cubeta y en orden de inserción dentro de cada una."""
        return [entrada for cubeta in self._cubetas for entrada in cubeta]

    def estadisticas(self) -> EstadisticasTabla:
        """Cifras de la tabla para el resumen."""
        largos = [len(cubeta) for cubeta in self._cubetas]
        return EstadisticasTabla(
            capacidad=self._capacidad,
            cantidad=self._cantidad,
            factor_carga=self._cantidad / self._capacidad,
            colisiones=self._colisiones,
            cubetas_ocupadas=sum(1 for n in largos if n > 0),
            cadena_mas_larga=max(largos),
            redimensionados=self._redimensionados,
        )


def valor_literal(token: Token) -> object:
    """Valor del literal (duraciones en milisegundos) o del booleano; None para el resto."""
    if token.tipo == TipoToken.ENTERO:
        return int(token.lexema)
    if token.tipo == TipoToken.DECIMAL:
        return float(token.lexema)
    if token.tipo == TipoToken.DURACION:
        # la unidad es lo que sigue a los dígitos; así una unidad nueva en `reglas` no exige tocar esto
        corte = len(token.lexema.rstrip(string.ascii_lowercase))
        return int(token.lexema[:corte]) * reglas.UNIDADES_TIEMPO[token.lexema[corte:]]
    if token.tipo == TipoToken.CADENA:
        return _interpretar_escapes(token.lexema[1:-1])
    if token.tipo == TipoToken.PALABRA_RESERVADA:
        return reglas.VALORES_BOOLEANOS.get(token.lexema)
    return None


def _interpretar_escapes(contenido: str) -> str:
    """Cambia cada escape válido por su carácter; una barra suelta se deja como está."""
    resultado = []
    i = 0
    while i < len(contenido):
        siguiente = contenido[i + 1:i + 2]
        if contenido[i] == "\\" and siguiente in reglas.ESCAPES_VALIDOS:
            resultado.append(reglas.ESCAPES_VALIDOS[siguiente])
            i += 2
        else:
            resultado.append(contenido[i])
            i += 1
    return "".join(resultado)


def registrar_token(tabla: TablaSimbolos, token: Token,
                    anterior: Token | None = None) -> ResultadoInstalacion | None:
    """Instala el token si su categoría va a la tabla y anota su tipo de dato y su declaración.

    Un identificador queda declarado en su primera aparición precedida por un tipo (`numero x`).
    """
    if token.tipo not in reglas.CATEGORIAS_EN_TABLA:
        return None
    resultado = tabla.instalar(token)
    entrada = resultado.entrada
    if resultado.es_nueva:
        entrada.valor = valor_literal(token)
        if token.lexema in reglas.VALORES_BOOLEANOS and token.tipo == TipoToken.PALABRA_RESERVADA:
            entrada.tipo_dato = reglas.TIPO_DATO_BOOLEANO
        else:
            entrada.tipo_dato = reglas.TIPO_DATO_LITERAL.get(token.tipo)
    if (token.tipo == TipoToken.IDENTIFICADOR and entrada.linea_declaracion is None
            and anterior is not None and anterior.tipo == TipoToken.PALABRA_RESERVADA
            and anterior.lexema in reglas.TIPOS_DE_DATO):
        entrada.tipo_dato = anterior.lexema
        entrada.linea_declaracion = token.linea
    return resultado
