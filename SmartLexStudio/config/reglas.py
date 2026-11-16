"""Reglas de FlowLang 1.0 como datos: sin funciones, para que cambiar el lenguaje no toque `core/`."""
from __future__ import annotations

import string

from core.modelos import TipoToken

# Lenguaje y archivos
NOMBRE_LENGUAJE = "FlowLang"
VERSION_LENGUAJE = "1.0"
EXTENSIONES_PERMITIDAS = (".flow", ".txt")
CODIFICACION = "utf-8"
TAMANO_MAXIMO_BYTES = 1_000_000

# Alfabeto y clases de carácter
LETRAS = string.ascii_letters
DIGITOS = "0123456789"
ESPACIOS = " \t\r\n"
LETRA, DIGITO, SALTO, OTRO = "letra", "digito", "salto", "otro"

# Palabras reservadas
PALABRAS_RESERVADAS = {
    "inicio": "Marca el comienzo del programa.",
    "fin": "Marca el final del programa.",
    "numero": "Tipo de dato: número entero.",
    "decimal": "Tipo de dato: número con parte decimal.",
    "texto": "Tipo de dato: cadena de caracteres.",
    "booleano": "Tipo de dato: verdadero o falso.",
    "dispositivo": "Tipo de dato: un dispositivo que se puede activar o desactivar.",
    "verdadero": "Valor lógico verdadero.",
    "falso": "Valor lógico falso.",
    "si": "Inicia una condición.",
    "sino": "Alternativa de una condición.",
    "mientras": "Repite un bloque mientras se cumpla una condición.",
    "mostrar": "Muestra un valor al usuario.",
    "leer": "Lee el valor de un sensor o entrada.",
    "activar": "Enciende un dispositivo.",
    "desactivar": "Apaga un dispositivo.",
    "esperar": "Detiene el programa durante un tiempo, por ejemplo 10s.",
}
TIPOS_DE_DATO = ("numero", "decimal", "texto", "booleano", "dispositivo")
VALORES_BOOLEANOS = {"verdadero": True, "falso": False}
TIPO_DATO_BOOLEANO = "booleano"
TIPO_DATO_LITERAL = {
    TipoToken.ENTERO: "numero",
    TipoToken.DECIMAL: "decimal",
    TipoToken.DURACION: "duracion",
    TipoToken.CADENA: "texto",
}
UNIDADES_TIEMPO = {"ms": 1, "s": 1_000, "m": 60_000, "h": 3_600_000}
PALABRA_INICIO = "inicio"
PALABRA_FIN = "fin"

# Operadores y delimitadores
OPERADORES = {
    "+": TipoToken.OPERADOR_ARITMETICO,
    "-": TipoToken.OPERADOR_ARITMETICO,
    "*": TipoToken.OPERADOR_ARITMETICO,
    "/": TipoToken.OPERADOR_ARITMETICO,
    "%": TipoToken.OPERADOR_ARITMETICO,
    "==": TipoToken.OPERADOR_RELACIONAL,
    "!=": TipoToken.OPERADOR_RELACIONAL,
    "<": TipoToken.OPERADOR_RELACIONAL,
    "<=": TipoToken.OPERADOR_RELACIONAL,
    ">": TipoToken.OPERADOR_RELACIONAL,
    ">=": TipoToken.OPERADOR_RELACIONAL,
    "&&": TipoToken.OPERADOR_LOGICO,
    "||": TipoToken.OPERADOR_LOGICO,
    "!": TipoToken.OPERADOR_LOGICO,
    "=": TipoToken.ASIGNACION,
}
DELIMITADORES = {
    "(": TipoToken.DELIMITADOR,
    ")": TipoToken.DELIMITADOR,
    "{": TipoToken.DELIMITADOR,
    "}": TipoToken.DELIMITADOR,
    ",": TipoToken.DELIMITADOR,
    ";": TipoToken.DELIMITADOR,
}
PARES_AGRUPACION = {"(": ")", "{": "}"}
ESCAPES_VALIDOS = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
LONGITUD_MAXIMA_IDENTIFICADOR = 32

# Autómatas finitos deterministas: una tabla de transiciones cada uno
AFD_IDENTIFICADOR = {
    "nombre": "AFD de identificadores",
    "inicial": "q0",
    "transiciones": {
        "q0": {LETRA: "q1", "_": "q1"},
        "q1": {LETRA: "q1", DIGITO: "q1", "_": "q1"},
    },
    "aceptacion": {"q1": TipoToken.IDENTIFICADOR},
    "errores": {},
}

AFD_NUMERO = {
    "nombre": "AFD de números",
    "inicial": "q0",
    "transiciones": {
        "q0": {DIGITO: "q1", ".": "q6"},
        "q1": {DIGITO: "q1", ".": "q2", "s": "q7", "h": "q7", "m": "q8", LETRA: "q5", "_": "q5"},
        "q2": {DIGITO: "q3", ".": "q4", LETRA: "q4", "_": "q4"},
        "q3": {DIGITO: "q3", ".": "q4", LETRA: "q4", "_": "q4"},
        "q4": {DIGITO: "q4", ".": "q4", LETRA: "q4", "_": "q4"},
        "q5": {DIGITO: "q5", ".": "q5", LETRA: "q5", "_": "q5"},
        "q6": {DIGITO: "q4"},
        "q7": {DIGITO: "q5", ".": "q5", LETRA: "q5", "_": "q5"},
        "q8": {"s": "q7", DIGITO: "q5", ".": "q5", LETRA: "q5", "_": "q5"},
    },
    "aceptacion": {"q1": TipoToken.ENTERO, "q3": TipoToken.DECIMAL,
                   "q7": TipoToken.DURACION, "q8": TipoToken.DURACION},
    "errores": {"q2": "LEX-003", "q4": "LEX-003", "q5": "LEX-004"},
}

AFD_CADENA = {
    "nombre": "AFD de cadenas",
    "inicial": "q0",
    "transiciones": {
        "q0": {'"': "q1"},
        "q1": {'"': "q3", "\\": "q2", OTRO: "q1"},
        "q2": {"n": "q1", "t": "q1", '"': "q1", "\\": "q1", OTRO: "q4"},
        "q4": {'"': "q5", "\\": "q6", OTRO: "q4"},
        "q6": {OTRO: "q4"},
    },
    "aceptacion": {"q3": TipoToken.CADENA},
    "errores": {"q1": "LEX-002", "q2": "LEX-002", "q4": "LEX-002", "q6": "LEX-002", "q5": "LEX-006"},
}

AFD_COMENTARIO = {
    "nombre": "AFD de comentarios",
    "inicial": "q0",
    "transiciones": {
        "q0": {"/": "q1"},
        "q1": {"/": "q2", "*": "q3"},
        "q2": {OTRO: "q2"},
        "q3": {"*": "q4", OTRO: "q3", SALTO: "q3"},
        "q4": {"/": "q5", "*": "q4", OTRO: "q3", SALTO: "q3"},
    },
    "aceptacion": {"q2": TipoToken.COMENTARIO, "q5": TipoToken.COMENTARIO},
    "errores": {"q3": "LEX-007", "q4": "LEX-007"},
}

# El orden desempata cuando dos reconocedores consumen lo mismo.
AUTOMATAS = (AFD_COMENTARIO, AFD_CADENA, AFD_NUMERO, AFD_IDENTIFICADOR)

# Descripción, expresión regular y ejemplos de cada categoría (pestañas Autómatas y Lenguaje)
INFO_CATEGORIAS = {
    TipoToken.PALABRA_RESERVADA: {
        "descripcion": "Palabra con significado fijo en el lenguaje; no puede usarse como nombre.",
        # Se arma desde el diccionario: agregar una palabra reservada actualiza también su regex.
        "regex": "|".join(PALABRAS_RESERVADAS),
        "ejemplos": ("inicio", "si", "mostrar"),
    },
    TipoToken.IDENTIFICADOR: {
        "descripcion": "Nombre de una variable o dispositivo: letra o _ seguida de letras, dígitos o _ (máximo 32).",
        "regex": "[A-Za-z_][A-Za-z0-9_]*",
        "ejemplos": ("temperatura", "_x1", "Inicio"),
    },
    TipoToken.ENTERO: {
        "descripcion": "Número entero sin signo: una o más cifras.",
        "regex": "[0-9]+",
        "ejemplos": ("0", "28", "007"),
    },
    TipoToken.DECIMAL: {
        "descripcion": "Número con parte entera y parte decimal separadas por un punto.",
        "regex": r"[0-9]+\.[0-9]+",
        "ejemplos": ("45.5", "0.0", "3.14"),
    },
    TipoToken.DURACION: {
        "descripcion": "Tiempo: un entero pegado a su unidad (ms, s, m, h), como en `esperar 10s;`.",
        "regex": "[0-9]+(?:ms|s|m|h)",
        "ejemplos": ("10s", "500ms", "2h"),
    },
    TipoToken.CADENA: {
        "descripcion": "Texto entre comillas dobles en una sola línea; admite \\n, \\t, \\\" y \\\\.",
        "regex": r'"(?:[^"\\\n]|\\[nt"\\])*"',
        "ejemplos": ('"Regando\\n"', '""', '"a\\"b"'),
    },
    TipoToken.OPERADOR_ARITMETICO: {
        "descripcion": "Operación aritmética entre dos valores.",
        "regex": r"[-+*/%]",
        "ejemplos": ("+", "-", "%"),
    },
    TipoToken.OPERADOR_RELACIONAL: {
        "descripcion": "Comparación entre dos valores.",
        "regex": "==|!=|<=|>=|<|>",
        "ejemplos": ("==", "<=", ">"),
    },
    TipoToken.OPERADOR_LOGICO: {
        "descripcion": "Combina o niega condiciones.",
        "regex": r"&&|\|\||!",
        "ejemplos": ("&&", "||", "!"),
    },
    TipoToken.ASIGNACION: {
        "descripcion": "Asigna un valor a una variable.",
        "regex": "=",
        "ejemplos": ("=",),
    },
    TipoToken.DELIMITADOR: {
        "descripcion": "Símbolo que agrupa o separa elementos.",
        "regex": "[(){},;]",
        "ejemplos": ("(", "{", ";"),
    },
    TipoToken.COMENTARIO: {
        "descripcion": "Texto ignorado por el programa: de línea (//) o de bloque (/* */).",
        "regex": r"//[^\n]*|/\*(?:[^*]|\*+[^*/])*\*+/",
        "ejemplos": ("// nota", "/* varias lineas */"),
    },
    TipoToken.ERROR: {
        "descripcion": "Texto que no pertenece a ninguna categoría de FlowLang.",
        "regex": None,
        "ejemplos": ("@", "3.4.5", '"sin cerrar'),
    },
}

SUGERENCIAS_CARACTER = {
    "&": "¿Quiso escribir `&&`?",
    "|": "¿Quiso escribir `||`?",
    "'": 'Las cadenas se escriben con comillas dobles: "texto".',
    ".": "El punto solo se usa dentro de un número decimal, como 3.14.",
    "#": "Los comentarios se escriben con `//` o `/* */`.",
    "[": "FlowLang no tiene corchetes; use paréntesis o llaves.",
    "]": "FlowLang no tiene corchetes; use paréntesis o llaves.",
    ":": "Las instrucciones terminan con `;`.",
}

# Tabla de símbolos
CATEGORIAS_EN_TABLA = frozenset({
    TipoToken.PALABRA_RESERVADA,
    TipoToken.IDENTIFICADOR,
    TipoToken.ENTERO,
    TipoToken.DECIMAL,
    TipoToken.DURACION,
    TipoToken.CADENA,
})
CAPACIDAD_INICIAL_TABLA = 17
FACTOR_CARGA_MAXIMO = 0.75
BASE_HASH = 31
MODULO_HASH = 2 ** 32
