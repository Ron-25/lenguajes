"""Catalogo unico de diagnosticos y manejador que los acumula y consulta."""
from __future__ import annotations

from typing import Iterable

from core.modelos import Diagnostico, TipoDiagnostico

_LEX = TipoDiagnostico.LEXICO
_SIN = TipoDiagnostico.ESTRUCTURAL
_ARC = TipoDiagnostico.ARCHIVO

CATALOGO: dict[str, dict] = {
    "LEX-001": {"tipo": _LEX, "titulo": "Carácter no reconocido",
                "mensaje": "El carácter '{lexema}' no pertenece al alfabeto de FlowLang.",
                "sugerencia": "Elimínelo o reemplácelo por un símbolo válido."},
    "LEX-002": {"tipo": _LEX, "titulo": "Cadena sin cerrar",
                "mensaje": "La cadena {lexema} no tiene comilla de cierre en la misma línea.",
                "sugerencia": 'Agregue `"` al final de la cadena; las cadenas no pueden ocupar varias líneas.'},
    "LEX-003": {"tipo": _LEX, "titulo": "Número mal formado",
                "mensaje": "'{lexema}' no es un número válido.",
                "sugerencia": "Un decimal necesita dígitos a ambos lados de un único punto, por ejemplo 3.14 o 0.5."},
    "LEX-004": {"tipo": _LEX, "titulo": "Identificador inválido",
                "mensaje": "'{lexema}' no es válido: un identificador no puede comenzar con un dígito.",
                "sugerencia": "Comience el nombre con una letra o `_`; si quería un número, quite las letras."},
    "LEX-005": {"tipo": _LEX, "titulo": "Identificador demasiado largo",
                "mensaje": "El identificador '{lexema}' supera el máximo de 32 caracteres.",
                "sugerencia": "Use un nombre más corto."},
    "LEX-006": {"tipo": _LEX, "titulo": "Secuencia de escape inválida",
                "mensaje": "La secuencia '{lexema}' no es un escape válido dentro de una cadena.",
                "sugerencia": 'Escapes permitidos: `\\n`, `\\t`, `\\"` y `\\\\`.'},
    "LEX-007": {"tipo": _LEX, "titulo": "Comentario de bloque sin cerrar",
                "mensaje": "El comentario que comienza con /* nunca se cierra.",
                "sugerencia": "Agregue `*/` al final del comentario."},
    "SIN-001": {"tipo": _SIN, "titulo": "Programa vacío",
                "mensaje": "El programa no contiene ninguna instrucción.",
                "sugerencia": "Escriba un programa entre `inicio` y `fin`."},
    "SIN-002": {"tipo": _SIN, "titulo": "Falta `inicio`",
                "mensaje": "El programa debe comenzar con la palabra reservada `inicio`; se encontró '{lexema}'.",
                "sugerencia": "Agregue `inicio` como primera palabra."},
    "SIN-003": {"tipo": _SIN, "titulo": "Falta `fin`",
                "mensaje": "El programa debe terminar con la palabra reservada `fin`; se encontró '{lexema}'.",
                "sugerencia": "Agregue `fin` como última palabra."},
    "SIN-004": {"tipo": _SIN, "titulo": "Cierre sin apertura",
                "mensaje": "El símbolo '{lexema}' no tiene apertura correspondiente.",
                "sugerencia": "Elimine el símbolo o agregue su apertura."},
    "SIN-005": {"tipo": _SIN, "titulo": "Apertura sin cierre",
                "mensaje": "El símbolo '{lexema}' nunca se cierra.",
                "sugerencia": "Agregue el símbolo de cierre correspondiente."},
    "SIN-006": {"tipo": _SIN, "titulo": "Cierre no correspondiente",
                "mensaje": "El símbolo '{lexema}' no corresponde con la última apertura pendiente.",
                "sugerencia": "Revise el orden de paréntesis y llaves."},
    "ARC-001": {"tipo": _ARC, "titulo": "Archivo inexistente",
                "mensaje": "No se encontró el archivo '{lexema}'.",
                "sugerencia": "Verifique la ruta y el nombre."},
    "ARC-002": {"tipo": _ARC, "titulo": "Extensión no soportada",
                "mensaje": "El archivo '{lexema}' no tiene una extensión permitida.",
                "sugerencia": "Use un archivo `.flow` o `.txt`."},
    "ARC-003": {"tipo": _ARC, "titulo": "Archivo vacío",
                "mensaje": "El archivo '{lexema}' no contiene texto.",
                "sugerencia": "Elija un archivo con un programa FlowLang."},
    "ARC-004": {"tipo": _ARC, "titulo": "Codificación inválida",
                "mensaje": "El archivo '{lexema}' no está codificado en UTF-8.",
                "sugerencia": "Guárdelo como UTF-8 e inténtelo de nuevo."},
    "ARC-005": {"tipo": _ARC, "titulo": "Error de lectura o escritura",
                "mensaje": "No se pudo leer o escribir '{lexema}'.",
                "sugerencia": "Revise los permisos y que no sea una carpeta."},
    "ARC-006": {"tipo": _ARC, "titulo": "Archivo demasiado grande",
                "mensaje": "El archivo '{lexema}' supera el tamaño máximo de 1 MB.",
                "sugerencia": "Divida el archivo o use uno más pequeño."},
}

_NOMBRES_PLURALES = {
    TipoDiagnostico.LEXICO: ("léxico", "léxicos"),
    TipoDiagnostico.ESTRUCTURAL: ("estructural", "estructurales"),
    TipoDiagnostico.ARCHIVO: ("de archivo", "de archivo"),
}


def crear_diagnostico(codigo: str, linea: int = 0, columna: int = 0,
                      lexema: str = "", sugerencia: str | None = None) -> Diagnostico:
    """Construye un Diagnostico rellenando la plantilla del catalogo (KeyError si no existe)."""
    datos = CATALOGO[codigo]
    return Diagnostico(
        codigo=codigo,
        tipo=datos["tipo"],
        titulo=datos["titulo"],
        mensaje=datos["mensaje"].format(lexema=lexema),
        sugerencia=datos["sugerencia"] if sugerencia is None else sugerencia,
        linea=linea,
        columna=columna,
        lexema=lexema,
    )


class ManejadorErrores:
    """Acumula los diagnosticos de un analisis y responde consultas sobre ellos."""

    def __init__(self) -> None:
        self._diagnosticos: list[Diagnostico] = []

    def reportar(self, codigo: str, linea: int = 0, columna: int = 0,
                 lexema: str = "", sugerencia: str | None = None) -> Diagnostico:
        """Crea un diagnostico del catalogo, lo guarda y lo devuelve."""
        diagnostico = crear_diagnostico(codigo, linea, columna, lexema, sugerencia)
        self._diagnosticos.append(diagnostico)
        return diagnostico

    def agregar(self, diagnostico: Diagnostico) -> None:
        """Guarda un diagnostico ya construido."""
        self._diagnosticos.append(diagnostico)

    def extender(self, diagnosticos: Iterable[Diagnostico]) -> None:
        """Guarda varios diagnosticos ya construidos."""
        self._diagnosticos.extend(diagnosticos)

    @property
    def diagnosticos(self) -> list[Diagnostico]:
        """Copia de los diagnosticos en orden de reporte."""
        return list(self._diagnosticos)

    def ordenados(self) -> list[Diagnostico]:
        """Diagnosticos ordenados por (linea, columna, codigo)."""
        return sorted(self._diagnosticos, key=lambda d: (d.linea, d.columna, d.codigo))

    def por_tipo(self, tipo: TipoDiagnostico) -> list[Diagnostico]:
        """Diagnosticos de un tipo, en orden de reporte."""
        return [d for d in self._diagnosticos if d.tipo == tipo]

    def por_linea(self) -> dict[int, list[Diagnostico]]:
        """Agrupa los diagnosticos por linea."""
        grupos: dict[int, list[Diagnostico]] = {}
        for diagnostico in self._diagnosticos:
            grupos.setdefault(diagnostico.linea, []).append(diagnostico)
        return grupos

    def cantidad(self, tipo: TipoDiagnostico | None = None) -> int:
        """Cantidad total de diagnosticos, o de un tipo concreto."""
        if tipo is None:
            return len(self._diagnosticos)
        return len(self.por_tipo(tipo))

    def hay_errores(self, tipo: TipoDiagnostico | None = None) -> bool:
        """True si hay al menos un diagnostico (del tipo indicado, si se da)."""
        return self.cantidad(tipo) > 0

    def resumen(self) -> str:
        """Texto como '15 errores: 13 léxicos, 2 estructurales' o 'Sin errores'."""
        total = len(self._diagnosticos)
        if total == 0:
            return "Sin errores"
        partes = []
        for tipo, (singular, plural) in _NOMBRES_PLURALES.items():
            n = self.cantidad(tipo)
            if n:
                partes.append(f"{n} {singular if n == 1 else plural}")
        return f"{total} {'error' if total == 1 else 'errores'}: {', '.join(partes)}"

    def limpiar(self) -> None:
        """Elimina todos los diagnosticos."""
        self._diagnosticos.clear()
