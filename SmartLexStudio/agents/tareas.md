# Tareas — SmartLex Studio

Documentos de referencia obligatorios antes de implementar: `docs/03_especificacion.md` (el lenguaje) y `docs/02_arquitectura.md` (el diseño). Si este archivo y aquellos se contradicen, **gana la especificación** y se registra la discrepancia en `agents/revisiones.md`.

## Registro de ejecución

| Tarea | Agente | Modelo | Estado | Resultado |
|---|---|---|---|---|
| Pasos 1–5: requisitos, investigación, especificación, arquitectura, tareas | architect-fable | claude-fable-5-2 | completado | `docs/matriz_requisitos.md`, `docs/01_investigacion.md`, `docs/02_arquitectura.md`, `docs/03_especificacion.md`, `agents/tareas.md`, `agents/decisiones.md`, `agents/revisiones.md`, `ejemplos/*.flow` (3 archivos validados con prototipo) |
| Fase A (A1–A10) | developer-sonnet | — | pendiente | — |
| Auditoría Fase A | reviewer-opus | — | pendiente | — |
| Fase B (B1–B8) | developer-sonnet | — | pendiente | — |
| Auditoría Fase B y final | reviewer-opus | — | pendiente | — |

## Reglas generales para el desarrollador

1. Solo biblioteca estándar. Compatible con Python ≥ 3.10. Primera línea de código de cada módulo: `from __future__ import annotations`.
2. `core/` y `application/` **no importan tkinter**. `config/reglas.py` contiene **solo datos**.
3. Nombres públicos **exactamente** como en este contrato (clases, funciones, parámetros, constantes). Lo privado (prefijo `_`) es libre.
4. Sin tildes ni `ñ` en identificadores de código. Docstring de una o dos líneas en cada clase y función pública. Comentarios solo donde expliquen un porqué.
5. Nada de código no pedido (YAGNI). Si algo del contrato parece incorrecto, **no improvisar**: anotarlo en `agents/revisiones.md` y aplicar la opción más simple coherente con la especificación.
6. Ejecutar las pruebas desde `SmartLexStudio/`: `/opt/homebrew/bin/python3.14 -m unittest discover -s tests -t . -v`.
7. Los archivos de `ejemplos/` ya existen y **no se modifican** (las posiciones esperadas dependen de ellos byte a byte).
8. Una tarea está terminada cuando sus criterios se cumplen **y** toda la batería anterior sigue pasando.

---

# FASE A — Núcleo (config + core + application + pruebas)

## Contrato de interfaces públicas

### `core/modelos.py` — no importa nada del proyecto

```python
class TipoToken(Enum):
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
    LEXICO = "Léxico"
    ESTRUCTURAL = "Estructural"
    ARCHIVO = "Archivo"

@dataclass(frozen=True)
class Token:
    tipo: TipoToken
    lexema: str
    linea: int        # desde 1
    columna: int      # desde 1
    @property
    def longitud(self) -> int: ...            # len(lexema)
    @property
    def es_significativo(self) -> bool: ...   # tipo no es COMENTARIO ni ERROR

@dataclass(frozen=True)
class Diagnostico:
    codigo: str               # "LEX-002"
    tipo: TipoDiagnostico
    titulo: str
    mensaje: str              # plantilla ya rellenada
    sugerencia: str
    linea: int                # 0 en diagnósticos de archivo
    columna: int              # 0 en diagnósticos de archivo
    lexema: str = ""

@dataclass
class EntradaSimbolo:
    lexema: str
    categoria: TipoToken
    valor_hash: int
    tipo_dato: str | None = None
    valor: object = None
    linea_declaracion: int | None = None
    apariciones: list[tuple[int, int]] = field(default_factory=list)   # (linea, columna)
```

### `config/reglas.py` — solo constantes; importa únicamente `TipoToken`

| Constante | Tipo | Valor |
|---|---|---|
| `NOMBRE_LENGUAJE` / `VERSION_LENGUAJE` | `str` | `"FlowLang"` / `"1.0"` |
| `EXTENSIONES_PERMITIDAS` | `tuple[str, ...]` | `(".flow", ".txt")` |
| `CODIFICACION` | `str` | `"utf-8"` |
| `TAMANO_MAXIMO_BYTES` | `int` | `1_000_000` |
| `LETRAS` | `str` | `string.ascii_letters` (52) |
| `DIGITOS` | `str` | `"0123456789"` |
| `ESPACIOS` | `str` | `" \t\r\n"` |
| `LETRA`, `DIGITO`, `SALTO`, `OTRO` | `str` | `"letra"`, `"digito"`, `"salto"`, `"otro"` (nombres de clase de carácter) |
| `PALABRAS_RESERVADAS` | `dict[str, str]` | las 17 palabras → descripción de una línea (especificación §3.1) |
| `TIPOS_DE_DATO` | `tuple[str, ...]` | `("numero", "decimal", "texto", "booleano", "dispositivo")` |
| `VALORES_BOOLEANOS` | `dict[str, bool]` | `{"verdadero": True, "falso": False}` |
| `TIPO_DATO_LITERAL` | `dict[TipoToken, str]` | `ENTERO→"numero"`, `DECIMAL→"decimal"`, `CADENA→"texto"` |
| `PALABRA_INICIO` / `PALABRA_FIN` | `str` | `"inicio"` / `"fin"` |
| `OPERADORES` | `dict[str, TipoToken]` | los 15 operadores (especificación §3.6) |
| `DELIMITADORES` | `dict[str, TipoToken]` | `( ) { } , ;` → `DELIMITADOR` |
| `PARES_AGRUPACION` | `dict[str, str]` | `{"(": ")", "{": "}"}` |
| `ESCAPES_VALIDOS` | `dict[str, str]` | `{"n": "\n", "t": "\t", '"': '"', "\\": "\\"}` |
| `LONGITUD_MAXIMA_IDENTIFICADOR` | `int` | `32` |
| `AFD_COMENTARIO`, `AFD_CADENA`, `AFD_NUMERO`, `AFD_IDENTIFICADOR` | `dict` | ver abajo |
| `AUTOMATAS` | `tuple[dict, ...]` | `(AFD_COMENTARIO, AFD_CADENA, AFD_NUMERO, AFD_IDENTIFICADOR)` — orden = prioridad |
| `INFO_CATEGORIAS` | `dict[TipoToken, dict]` | por **cada** miembro de `TipoToken`: `{"descripcion": str, "regex": str \| None, "ejemplos": tuple[str, ...]}`. Regex exactas de la especificación §3; `None` para `ERROR`. `ENTERO` y `DECIMAL` llevan cada uno su regex |
| `SUGERENCIAS_CARACTER` | `dict[str, str]` | las 8 de la especificación §10.1 |
| `CATEGORIAS_EN_TABLA` | `frozenset[TipoToken]` | `{PALABRA_RESERVADA, IDENTIFICADOR, ENTERO, DECIMAL, CADENA}` |
| `CAPACIDAD_INICIAL_TABLA` | `int` | `17` |
| `FACTOR_CARGA_MAXIMO` | `float` | `0.75` |
| `BASE_HASH` / `MODULO_HASH` | `int` | `31` / `2 ** 32` |

Forma de cada definición de AFD (las cuatro tablas están validadas; copiarlas tal cual):

```python
AFD_IDENTIFICADOR = {
    "nombre": "AFD de identificadores",
    "inicial": "q0",
    "transiciones": {
        "q0": {LETRA: "q1", "_": "q1"},
        "q1": {LETRA: "q1", DIGITO: "q1", "_": "q1"},
    },
    "aceptacion": {"q1": TipoToken.IDENTIFICADOR},   # estado final → tipo de token
    "errores": {},                                   # estado final de error → código
}

AFD_NUMERO = {
    "nombre": "AFD de números",
    "inicial": "q0",
    "transiciones": {
        "q0": {DIGITO: "q1", ".": "q6"},
        "q1": {DIGITO: "q1", ".": "q2", LETRA: "q5", "_": "q5"},
        "q2": {DIGITO: "q3", ".": "q4", LETRA: "q4", "_": "q4"},
        "q3": {DIGITO: "q3", ".": "q4", LETRA: "q4", "_": "q4"},
        "q4": {DIGITO: "q4", ".": "q4", LETRA: "q4", "_": "q4"},
        "q5": {DIGITO: "q5", ".": "q5", LETRA: "q5", "_": "q5"},
        "q6": {DIGITO: "q4"},
    },
    "aceptacion": {"q1": TipoToken.ENTERO, "q3": TipoToken.DECIMAL},
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
```

Nota: las claves `"n"`, `"t"` de `q2` en `AFD_CADENA` deben coincidir con `ESCAPES_VALIDOS` (hay una prueba que lo exige).

### `core/afd.py`

```python
def clase_caracter(caracter: str) -> str:
    """LETRA, DIGITO o SALTO según reglas; si no, el propio carácter."""

@dataclass(frozen=True)
class ResultadoAFD:
    longitud: int                    # del prefijo más largo que terminó en estado final; 0 si ninguno
    tipo: TipoToken | None           # si el estado final es de token
    codigo_error: str | None         # si el estado final es de error
    recorrido: tuple[str, ...]       # estados visitados hasta ese prefijo (longitud + 1 elementos); (inicial,) si longitud 0

class AFD:
    def __init__(self, definicion: dict) -> None: ...
    nombre: str
    inicial: str
    transiciones: dict[str, dict[str, str]]
    aceptacion: dict[str, TipoToken]
    errores: dict[str, str]
    def siguiente_estado(self, estado: str, caracter: str) -> str | None: ...
    def reconocer(self, texto: str, inicio: int = 0) -> ResultadoAFD: ...
    def acepta(self, cadena: str) -> bool: ...
```

- `siguiente_estado`: orden de búsqueda en la fila del estado: carácter exacto → `clase_caracter` → `OTRO` solo si el carácter no es `"\n"`. Si el estado no tiene fila o nada aplica → `None`.
- `reconocer`: especificación §4 punto 4 y arquitectura §4.4. Nunca lanza excepción; con `inicio >= len(texto)` devuelve longitud 0.
- `acepta(cadena)`: `True` si `reconocer(cadena, 0)` consume **toda** la cadena, esta no es vacía y termina en estado final **de token**.

### `core/errores.py`

```python
CATALOGO: dict[str, dict]     # codigo → {"tipo": TipoDiagnostico, "titulo": str, "mensaje": str, "sugerencia": str}

def crear_diagnostico(codigo: str, linea: int = 0, columna: int = 0,
                      lexema: str = "", sugerencia: str | None = None) -> Diagnostico: ...

class ManejadorErrores:
    def __init__(self) -> None: ...
    def reportar(self, codigo: str, linea: int = 0, columna: int = 0,
                 lexema: str = "", sugerencia: str | None = None) -> Diagnostico: ...
    def agregar(self, diagnostico: Diagnostico) -> None: ...
    def extender(self, diagnosticos: Iterable[Diagnostico]) -> None: ...
    @property
    def diagnosticos(self) -> list[Diagnostico]: ...       # copia, en orden de reporte
    def ordenados(self) -> list[Diagnostico]: ...          # por (linea, columna, codigo)
    def por_tipo(self, tipo: TipoDiagnostico) -> list[Diagnostico]: ...
    def por_linea(self) -> dict[int, list[Diagnostico]]: ...
    def cantidad(self, tipo: TipoDiagnostico | None = None) -> int: ...
    def hay_errores(self, tipo: TipoDiagnostico | None = None) -> bool: ...
    def resumen(self) -> str: ...        # p. ej. "15 errores: 13 léxicos, 2 estructurales" / "Sin errores"
    def limpiar(self) -> None: ...
```

- `CATALOGO` contiene exactamente los 19 códigos de la especificación §10, con esos títulos, mensajes y sugerencias.
- `crear_diagnostico`: `mensaje = CATALOGO[codigo]["mensaje"].format(lexema=lexema)`; usa `sugerencia` si no es `None`, si no la del catálogo. Código desconocido → `KeyError`.

### `core/lexer.py`

```python
@dataclass(frozen=True)
class Coincidencia:
    longitud: int                    # >= 1 siempre
    tipo: TipoToken                  # TipoToken.ERROR si codigo_error no es None
    codigo_error: str | None
    reconocedor: str                 # nombre del AFD, "Tabla de operadores y delimitadores" o "Ninguno"
    recorrido: tuple[str, ...]       # () si no fue un AFD

def reconocer_lexema(texto: str, posicion: int = 0) -> Coincidencia:
    """Coincidencia más larga en `posicion` (que no debe ser un espacio)."""

class Lexer:
    def __init__(self, fuente: str, manejador: ManejadorErrores | None = None) -> None: ...
    manejador: ManejadorErrores      # el recibido o uno nuevo
    def tokens(self) -> Iterator[Token]: ...     # generador perezoso, de un solo uso
    def analizar(self) -> list[Token]: ...       # list(self.tokens())
```

- `reconocer_lexema` implementa la especificación §5 completa, incluidos el paso 4 (nada reconocido → longitud 1, `LEX-001`, reconocedor `"Ninguno"`) y el paso 5 (palabra reservada; más de 32 caracteres → `LEX-005`). Los objetos `AFD` se construyen **una sola vez** a nivel de módulo a partir de `reglas.AUTOMATAS`.
- `Lexer.tokens()`: salta `reglas.ESPACIOS` llevando línea y columna (especificación §6); por cada lexema llama a `reconocer_lexema`, y:
  - sin error → produce `Token(tipo, lexema, linea, columna)`;
  - con error → reporta en `manejador` y produce `Token(TipoToken.ERROR, lexema, linea, columna)`. Para `LEX-006` reporta **un diagnóstico por cada escape inválido** (posición de su `\`, lexema de 2 caracteres). Para `LEX-001` pasa `sugerencia=reglas.SUGERENCIAS_CARACTER.get(caracter)`. Para los demás, un diagnóstico en la posición de inicio con el lexema completo.
- El lexer no lanza excepciones con ninguna entrada (`""` produce cero tokens).

### `core/validador.py`

```python
def validar_estructura(tokens: Iterable[Token]) -> list[Diagnostico]:
    """Reglas E1–E4 de la especificación §8.2 sobre los tokens significativos. Ordenado por (linea, columna)."""
```

### `core/simbolos.py`

```python
def hash_polinomial(lexema: str) -> int: ...          # especificación §13
def siguiente_primo(n: int) -> int: ...               # menor primo >= n  (siguiente_primo(34) == 37)

@dataclass(frozen=True)
class ResultadoInstalacion:
    entrada: EntradaSimbolo
    es_nueva: bool
    hubo_colision: bool      # True solo si es_nueva y la cubeta ya tenía entradas
    indice: int              # cubeta de la entrada DESPUÉS de un posible redimensionado
    redimensiono: bool

@dataclass(frozen=True)
class EstadisticasTabla:
    capacidad: int
    cantidad: int
    factor_carga: float      # cantidad / capacidad
    colisiones: int          # histórico
    cubetas_ocupadas: int
    cadena_mas_larga: int
    redimensionados: int

class TablaSimbolos:
    def __init__(self, capacidad: int = reglas.CAPACIDAD_INICIAL_TABLA,
                 funcion_hash: Callable[[str], int] = hash_polinomial,
                 factor_carga_maximo: float = reglas.FACTOR_CARGA_MAXIMO) -> None: ...
    def instalar(self, token: Token) -> ResultadoInstalacion: ...
    def buscar(self, lexema: str) -> EntradaSimbolo | None: ...
    def indice(self, lexema: str) -> int: ...                    # funcion_hash(lexema) % capacidad
    def cubetas(self) -> list[list[EntradaSimbolo]]: ...         # copia superficial, longitud == capacidad
    def entradas(self) -> list[EntradaSimbolo]: ...              # por cubeta ascendente y orden de inserción
    def estadisticas(self) -> EstadisticasTabla: ...
    @property
    def capacidad(self) -> int: ...
    @property
    def colisiones(self) -> int: ...
    def __len__(self) -> int: ...                                # cantidad de entradas
    def __contains__(self, lexema: str) -> bool: ...

def valor_literal(token: Token) -> object: ...
def registrar_token(tabla: TablaSimbolos, token: Token,
                    anterior: Token | None = None) -> ResultadoInstalacion | None: ...
```

- `TablaSimbolos` no usa `dict`, `set` ni `hash()` para almacenar o localizar entradas: solo listas. Algoritmo exacto: arquitectura §6.2 (colisión contada **antes** de insertar; redimensionado comprobado **después** de insertar con `cantidad / capacidad > factor_carga_maximo`; nueva capacidad `siguiente_primo(2 * capacidad)`; reubicar no cuenta colisiones). `capacidad < 1` → `ValueError`.
- `instalar` en lexema existente: añade `(token.linea, token.columna)` a `apariciones`, devuelve `es_nueva=False`, `hubo_colision=False`. En lexema nuevo: crea `EntradaSimbolo(lexema, categoria=token.tipo, valor_hash=…, apariciones=[(linea, columna)])`.
- `valor_literal`: `ENTERO → int`, `DECIMAL → float`, `CADENA →` contenido sin comillas con `ESCAPES_VALIDOS` aplicados, reservada en `VALORES_BOOLEANOS → bool`, cualquier otro → `None`.
- `registrar_token`: devuelve `None` si `token.tipo` no está en `CATEGORIAS_EN_TABLA`. Si no, instala y, cuando la entrada es nueva, asigna `tipo_dato` (`TIPO_DATO_LITERAL`, o `"booleano"` para `verdadero`/`falso`) y `valor`. Regla de declaración de la especificación §9 usando `anterior` (el token **significativo** previo; lo mantiene quien llama).

### `application/archivos.py`

```python
class ErrorArchivo(Exception):
    def __init__(self, diagnostico: Diagnostico) -> None: ...
    diagnostico: Diagnostico             # str(error) == diagnostico.mensaje

def cargar_fuente(ruta: str | Path) -> str: ...          # lanza ErrorArchivo (ARC-001…006)
def guardar_fuente(ruta: str | Path, contenido: str) -> None: ...   # UTF-8; OSError → ErrorArchivo(ARC-005)
def listar_ejemplos(directorio: str | Path | None = None) -> list[Path]: ...
```

- `cargar_fuente`: orden de comprobación de la especificación §10.3. Extensión comparada en minúsculas. Decodifica con `utf-8-sig` (acepta BOM). Normaliza `\r\n` y `\r` a `\n`. El `lexema` del diagnóstico es el nombre del archivo (`Path(ruta).name`).
- `listar_ejemplos`: archivos con extensión permitida del directorio (por defecto `<raíz del proyecto>/ejemplos`), ordenados por nombre; lista vacía si el directorio no existe.

### `application/analisis_service.py`

```python
FASE_LEXICA = "Léxico"
FASE_ESTRUCTURAL = "Estructura"

@dataclass(frozen=True)
class Paso:
    numero: int                               # desde 1
    fase: str                                 # FASE_LEXICA | FASE_ESTRUCTURAL
    token: Token | None                       # None en FASE_ESTRUCTURAL
    diagnosticos: tuple[Diagnostico, ...]     # los detectados en este paso
    instalacion: ResultadoInstalacion | None
    descripcion: str                          # una línea para la consola

@dataclass
class ResultadoAnalisis:
    fuente: str
    tokens: list[Token]
    manejador: ManejadorErrores
    tabla: TablaSimbolos
    terminado: bool = False
    @property
    def diagnosticos(self) -> list[Diagnostico]: ...            # manejador.diagnosticos
    @property
    def es_valida_lexicamente(self) -> bool: ...                # sin diagnósticos LEXICO
    @property
    def es_valida_estructuralmente(self) -> bool: ...           # sin diagnósticos ESTRUCTURAL
    @property
    def es_valida(self) -> bool: ...                            # terminado y las dos anteriores
    def conteo_por_tipo(self) -> dict[TipoToken, int]: ...      # solo tipos con al menos 1 token
    def lineas_invalidas(self) -> list[int]: ...                # líneas con diagnóstico LEXICO, ordenadas, sin repetir
    @property
    def cantidad_lineas(self) -> int: ...                       # 0 si fuente == "", si no fuente.count("\n") + 1
    @property
    def cantidad_caracteres(self) -> int: ...

@dataclass(frozen=True)
class ExplicacionToken:
    token: Token
    categoria: str                    # token.tipo.value
    descripcion: str                  # de INFO_CATEGORIAS; para reservadas se añade la de PALABRAS_RESERVADAS
    regex: str | None
    reconocedor: str
    recorrido: tuple[str, ...]
    detalle: str                      # texto de varias líneas listo para mostrar

class SesionAnalisis:
    def __init__(self, fuente: str, capacidad_tabla: int = reglas.CAPACIDAD_INICIAL_TABLA) -> None: ...
    def siguiente_paso(self) -> Paso | None: ...        # None cuando ya no hay más
    def pasos(self) -> Iterator[Paso]: ...              # itera siguiente_paso() hasta None
    def terminar(self) -> ResultadoAnalisis: ...        # consume lo que falte y devuelve el resultado
    @property
    def terminada(self) -> bool: ...
    @property
    def resultado(self) -> ResultadoAnalisis: ...       # parcial mientras no termina (mismo objeto siempre)

def analizar_texto(fuente: str) -> ResultadoAnalisis: ...          # SesionAnalisis(fuente).terminar()
def analizar_archivo(ruta: str | Path) -> ResultadoAnalisis: ...   # cargar_fuente + analizar_texto; propaga ErrorArchivo
def tokenizar(fuente: str) -> list[Token]: ...                     # solo lexer; para el resaltado del editor
def explicar_token(token: Token, tabla: TablaSimbolos | None = None) -> ExplicacionToken: ...
```

- Secuencia de `siguiente_paso()`: arquitectura §8. Un `Paso` léxico por token (incluidos `COMENTARIO` y `ERROR`); `diagnosticos` = los que el manejador recibió durante ese token; `instalacion` = `registrar_token(...)`. Al agotarse el lexer se llama **una vez** a `validar_estructura`, se añaden sus diagnósticos al manejador y se emite un `Paso` estructural por cada uno. Después: `None`, `terminada == True`, `resultado.terminado == True`. Llamadas posteriores siguen devolviendo `None`.
- `descripcion` contiene siempre `"{linea}:{columna}"` y, en pasos léxicos, el nombre de la categoría y el lexema (recortado a 40 caracteres, saltos de línea mostrados como `⏎`); si hay diagnósticos, el código de cada uno; si hubo instalación, la cubeta y si fue nueva, repetida o colisión.
- `explicar_token`: datos según arquitectura §9. `recorrido` y `reconocedor` salen de `reconocer_lexema(token.lexema)`. Para tokens `ERROR`, `detalle` incluye código, título y sugerencia del catálogo. Si se pasa `tabla` y el lexema está, `detalle` incluye hash, cubeta, tipo de dato y número de apariciones.

---

## Tareas de la Fase A

Responsable de todas: **developer-sonnet**. Estado inicial: **Pendiente**.

### A1 — Esqueleto y modelos
- **Archivos:** `config/__init__.py`, `core/__init__.py`, `application/__init__.py`, `ui/__init__.py`, `tests/__init__.py` (vacíos), `core/modelos.py`, `.gitignore` (`__pycache__/`, `*.pyc`, `.DS_Store`), `requirements.txt` (solo un comentario: sin dependencias externas; Python ≥ 3.10 con tkinter).
- **Criterios:** `python -c "import core.modelos"` funciona; `Token` y `Diagnostico` son inmutables (asignar un campo lanza `FrozenInstanceError`); `TipoToken` tiene exactamente 12 miembros.
- **Pruebas:** incluidas en `tests/test_lexer.py::TestModelos` (inmutabilidad, `longitud`, `es_significativo`).

### A2 — Reglas del lenguaje
- **Archivos:** `config/reglas.py`.
- **Criterios:** todas las constantes del contrato con sus valores; 17 palabras reservadas; 15 operadores; 6 delimitadores; el archivo no define funciones ni clases y solo importa `string` y `TipoToken`; `INFO_CATEGORIAS` tiene una entrada por cada `TipoToken`; cada regex de `INFO_CATEGORIAS` compila con `re.compile`.
- **Pruebas:** `tests/test_afd.py::TestReglas` — conteos anteriores; toda clave de `TIPOS_DE_DATO`, `VALORES_BOOLEANOS`, `PALABRA_INICIO`, `PALABRA_FIN` está en `PALABRAS_RESERVADAS`; las claves de un carácter de `AFD_CADENA["transiciones"]["q2"]` distintas de `OTRO` son exactamente las de `ESCAPES_VALIDOS`; todo estado destino de cada AFD es un estado con fila o un estado final.

### A3 — Motor de autómatas
- **Archivos:** `core/afd.py`, `tests/test_afd.py`.
- **Criterios:** contrato de `AFD`; determinismo (`siguiente_estado` devuelve un único estado o `None`); `recorrido` correcto.
- **Pruebas requeridas:**
  - Recorridos exactos de la tabla de la especificación §3.3 (`28`, `45.5`, `3.`, `3.4.5`, `.5`, `12abc`, `1.5abc`) con su tipo o código.
  - `reconocer("abc def", 0)` con el AFD de identificadores → longitud 3; `reconocer("abc", 3)` → longitud 0.
  - `OTRO` no consume `"\n"`: AFD de comentarios sobre `"// a\nb"` → longitud 4.
  - **Equivalencia regex ↔ AFD**: para todas las cadenas de longitud 0 a 5 sobre el alfabeto `a 1 _ . " \ n / * espacio salto q`, y para cada pareja (AFD, regex, tipo) — identificador, entero, decimal, cadena, comentario —, `AFD.reconocer` consume toda la cadena terminando en ese tipo **si y solo si** `re.fullmatch(regex, cadena)`. Cero diferencias.

### A4 — Manejador de errores
- **Archivos:** `core/errores.py`, `tests/test_errores.py`.
- **Criterios:** 19 códigos (7 `LEX`, 6 `SIN`, 6 `ARC`) con el tipo correcto; ningún mensaje ni sugerencia vacío.
- **Pruebas requeridas:** `crear_diagnostico("LEX-001", 3, 7, "@")` → mensaje contiene `'@'`, línea 3, columna 7, tipo `LEXICO`; sugerencia personalizada sustituye a la del catálogo; código inexistente → `KeyError`; `ordenados()` ordena por posición aunque se reporten desordenados; `por_tipo`, `por_linea`, `cantidad`, `hay_errores`, `limpiar`; `resumen()` sin errores y con mezcla de tipos; `diagnosticos` devuelve copia (modificarla no altera el manejador).

### A5 — Analizador léxico
- **Archivos:** `core/lexer.py`, `tests/test_lexer.py`.
- **Criterios:** contrato de `reconocer_lexema` y `Lexer`; no usa `re`; no lanza excepciones.
- **Pruebas requeridas** (formato `(tipo, lexema, línea, columna)`; todos los valores están verificados):

| Caso | Entrada | Esperado |
|---|---|---|
| Cadena válida básica | `numero x = 10;` | `(PALABRA_RESERVADA,"numero",1,1)` `(IDENTIFICADOR,"x",1,8)` `(ASIGNACION,"=",1,10)` `(ENTERO,"10",1,12)` `(DELIMITADOR,";",1,14)`; 0 diagnósticos |
| Números | `7 8.25` | `(ENTERO,"7",1,1)` `(DECIMAL,"8.25",1,3)` |
| Maximal munch | `a>=b` | `a` · `(OPERADOR_RELACIONAL,">=",1,2)` · `(IDENTIFICADOR,"b",1,4)` |
| Maximal munch | `a>b` | `a` · `(OPERADOR_RELACIONAL,">",1,2)` · `(IDENTIFICADOR,"b",1,3)` |
| Maximal munch | `<=<==` | `("<=",1,1)` `("<=",1,3)` `(ASIGNACION,"=",1,5)` |
| Maximal munch | `!x!=y` | `(OPERADOR_LOGICO,"!",1,1)` `x` `(OPERADOR_RELACIONAL,"!=",1,3)` `y` |
| Separación por espacio | `a= =b` | dos `ASIGNACION` en columnas 2 y 4 |
| División vs comentario | `a/b` | `(OPERADOR_ARITMETICO,"/",1,2)` |
| Comentario de línea | `a // c⏎b` | `(COMENTARIO,"// c",1,3)` y `(IDENTIFICADOR,"b",2,1)` |
| Comentario de bloque multilínea | `/* a⏎ b */ c` | `(COMENTARIO,"/* a\n b */",1,1)` y `(IDENTIFICADOR,"c",2,7)` |
| Reservada vs identificador | `si2 sino` | `(IDENTIFICADOR,"si2",1,1)` `(PALABRA_RESERVADA,"sino",1,5)` |
| Mayúsculas | `Inicio` | `IDENTIFICADOR` |
| Cadena con escapes | `"ok\n\t\"\\"` (texto fuente con barras) | un `CADENA`, 0 diagnósticos |
| Cadenas vacías | `"" ""` | `CADENA` en columnas 1 y 4 |
| Cadena sin cerrar | `"hola` | `(ERROR,"\"hola",1,1)`; `LEX-002` en 1:1 |
| Cadena sin cerrar no arrastra la línea siguiente | `"a⏎b` | `LEX-002` y luego `(IDENTIFICADOR,"b",2,1)` |
| Barra final | `"a\` | solo `LEX-002` en 1:1 |
| Escape inválido | `"a\qb" x` | `(ERROR,"\"a\\qb\"",1,1)` `(IDENTIFICADOR,"x",1,8)`; `LEX-006` en 1:3 con lexema `\q` |
| Dos escapes inválidos | `"a\qb\zc"` | un token `ERROR`; `LEX-006` en 1:3 (`\q`) y 1:6 (`\z`) |
| Escape inválido y sin cerrar | `"a\qb` | solo `LEX-002` en 1:1 |
| Número mal formado | `x=3.;` | `(ERROR,"3.",1,3)` `(DELIMITADOR,";",1,5)`; `LEX-003` en 1:3 |
| Número mal formado | `3.4.5` / `3..5` / `.5` / `1.5abc` | un token `ERROR` con todo el lexema; `LEX-003` en 1:1 |
| Identificador inválido | `12abc` / `1_000` / `12abc.5` | un token `ERROR` con todo el lexema; `LEX-004` en 1:1 |
| Punto tras identificador | `x1.5` | `(IDENTIFICADOR,"x1",1,1)` `(ERROR,".5",1,3)`; `LEX-003` en 1:3 |
| Punto suelto | `x.` | `LEX-001` en 1:2 con la sugerencia específica del punto |
| Símbolos desconocidos consecutivos | `@#` | `LEX-001` en 1:1 y en 1:2 (uno por carácter) |
| `&` suelto | `a&&b&c` | `(OPERADOR_LOGICO,"&&",1,2)`; `LEX-001` en 1:5 con sugerencia que contiene `&&` |
| Letra no ASCII | `año` | `a` · `LEX-001` en 1:2 (`ñ`) · `o` |
| Comillas simples | `'a'` | `LEX-001` en 1:1 y 1:3 |
| Longitud límite | 32 × `x` | `IDENTIFICADOR`, 0 diagnósticos |
| Identificador largo | 33 × `x` | un token `ERROR`; `LEX-005` en 1:1 |
| Bloque sin cerrar | `/* sin cerrar⏎ x` | un token `ERROR` hasta el final; `LEX-007` en 1:1 |
| Errores consecutivos en una línea | `3. 12a @ "x` | 4 tokens `ERROR`; códigos en orden `LEX-003`, `LEX-004`, `LEX-001`, `LEX-002` en columnas 1, 4, 8, 10 |
| Entrada vacía / solo espacios | `""`, `"  \n\t "` | 0 tokens, 0 diagnósticos |
| Tabulador y CRLF | `\tx\r\ny` | `x` en 1:2; `y` en 2:1 |
| Tokens repetidos | `x x x` | 3 tokens iguales salvo columna (1, 3, 5) |
| Generador perezoso | `Lexer("a b").tokens()` | `next()` devuelve `a` sin haber analizado `b` (el manejador aún tiene 0 diagnósticos si `b` fuese un error: usar `"a @"`) |
| Entrada grande | línea `numero x1 = 10 + 2.5; // c⏎` × 5 000 | 40 000 tokens, 0 diagnósticos, último token en línea 5 000, menos de 5 s |
| Archivos de ejemplo | `ejemplos/correcto.flow`, `incorrecto.flow`, `casos_limite.flow` | conteos y tabla de diagnósticos léxicos de la especificación §12 (posiciones exactas de los 13 `LEX` de `incorrecto.flow`) |

### A6 — Validador estructural
- **Archivos:** `core/validador.py`, `tests/test_validador.py`.
- **Pruebas requeridas** (tokens obtenidos con `Lexer(...).analizar()`):

| Entrada | Esperado |
|---|---|
| `inicio fin` | `[]` |
| `inicio si (x) { y = (1); } fin` | `[]` |
| `""` y `// solo comentario` | solo `SIN-001` en 1:1 |
| `@` (solo un token de error) | solo `SIN-001` |
| `x = 1; fin` | `SIN-002` en 1:1 con lexema `x` |
| `inicio x = 1;` | `SIN-003` en 1:13 con lexema `;` |
| `fin` | solo `SIN-002` en 1:1 |
| `inicio ) fin` | `SIN-004` en 1:8 |
| `inicio ( fin` | `SIN-005` en 1:8 |
| `inicio ( } fin` | `SIN-006` en 1:10 y nada más |
| `inicio { ( fin` | `SIN-005` en 1:8 y en 1:10 (ordenados) |
| `inicio // (⏎ "(" fin` | `[]` (comentarios y cadenas no cuentan) |
| `ejemplos/incorrecto.flow` | exactamente `SIN-005` en 9:8 y `SIN-003` en 12:22, en ese orden |

### A7 — Tabla de símbolos
- **Archivos:** `core/simbolos.py`, `tests/test_simbolos.py`.
- **Criterios:** contrato; implementación con listas (sin `dict`/`set`/`hash()` para almacenar); valores hash exactos.
- **Pruebas requeridas:**
  - Hash: `hash_polinomial("")==0`, `("x")==120`, `("si")==3670`, `("10")==1567`, `("temperatura")==321701232`, `("riego")==108509814`, `("activo")==2872016656`.
  - `siguiente_primo`: 1→2, 17→17, 34→37, 74→79, 158→163.
  - Inserción y búsqueda: instalar `x` (1:1) → `es_nueva`, `len==1`, `"x" in tabla`, `buscar("x").apariciones==[(1,1)]`, `buscar("z") is None`.
  - **Duplicados / tokens repetidos**: instalar `x` tres veces → `len==1`, 3 apariciones en orden, segunda y tercera con `es_nueva=False` y `hubo_colision=False`.
  - **Colisión natural** (capacidad 17): `si` y `temperatura` → ambas en cubeta 15, `colisiones==1`, segunda instalación con `hubo_colision=True`, `len(cubetas()[15])==2`. Igual con `riego`/`activo` (cubeta 4) y `x`/`total` (cubeta 1).
  - **Colisiones forzadas**: `TablaSimbolos(capacidad=5, funcion_hash=lambda s: 0)` con 10 lexemas distintos → `len==10`, `colisiones==9`, todas en la cubeta 0, todas recuperables con `buscar`, `cadena_mas_larga==10`.
  - **Redimensionado**: capacidad 17; instalar 12 lexemas distintos → capacidad 17; el 13.º → capacidad 37, `redimensiono=True`, todos siguen encontrándose y `indice(lexema)` coincide con la cubeta donde está cada uno.
  - Sin redimensionado: `factor_carga_maximo=float("inf")` mantiene la capacidad.
  - `capacidad=0` → `ValueError`.
  - `estadisticas()` coherente: `cantidad==len(tabla)`, `factor_carga==cantidad/capacidad`, suma de longitudes de cubetas == cantidad.
  - `valor_literal`: `"007"`→`7`; `"45.5"`→`45.5`; `"\"a\\n\\\"b\""` (fuente `"a\n\"b"`) → `a`, salto, `"`, `b`; `verdadero`→`True`; identificador → `None`.
  - `registrar_token`: operador → `None` y la tabla no cambia; `numero x` → entrada `x` con `tipo_dato=="numero"` y `linea_declaracion` correcta; uso posterior de `x` no cambia la declaración; segunda declaración (`texto x`) conserva la primera; `x` sin declarar → `tipo_dato is None`; literales con su `tipo_dato` y `valor`; token `ERROR` y `COMENTARIO` → `None`.

### A8 — Archivos
- **Archivos:** `application/archivos.py`, `tests/test_archivos.py` (usar `tempfile.TemporaryDirectory`).
- **Pruebas requeridas:** ruta inexistente → `ARC-001`; directorio con nombre `x.flow` → `ARC-005`; `datos.pdf` → `ARC-002`; `.FLOW` en mayúsculas se acepta; archivo de 0 bytes → `ARC-003`; archivo solo con espacios y saltos → `ARC-003`; bytes `b"\xff\xfe\x00inicio"` → `ARC-004`; archivo mayor que `TAMANO_MAXIMO_BYTES` → `ARC-006`; archivo con BOM UTF-8 se lee sin el BOM; `\r\n` se normaliza a `\n`; `.txt` válido se acepta; `guardar_fuente` + `cargar_fuente` devuelve el mismo texto (incluida `ñ`); `guardar_fuente` en un directorio inexistente → `ARC-005`; `listar_ejemplos()` devuelve los 3 archivos de `ejemplos/` en orden alfabético; el diagnóstico de `ErrorArchivo` tiene tipo `ARCHIVO`, línea 0 y el nombre del archivo en el mensaje.

### A9 — Servicio de análisis y evaluación progresiva
- **Archivos:** `application/analisis_service.py`, `tests/test_integracion.py`.
- **Pruebas requeridas:**
  - `analizar_archivo("ejemplos/correcto.flow")`: `terminado`, `es_valida`, 111 tokens, 0 diagnósticos, `len(tabla)==36`, `tabla.capacidad==79`, `tabla.colisiones==14`, 2 redimensionados; `conteo_por_tipo()` igual a la especificación §12.1; `temperatura` con `tipo_dato=="numero"` y `linea_declaracion==5`; `bomba` con `tipo_dato=="dispositivo"`; `humedad` con `apariciones == [(6, 13), (13, 30), (23, 9), (23, 19)]`; `ciclos` con 5 apariciones; entrada `45.5` con `valor==45.5`.
  - `analizar_archivo("ejemplos/incorrecto.flow")`: no válida léxica ni estructuralmente; 57 tokens; 15 diagnósticos con códigos y posiciones de la especificación §12.2 (los 13 léxicos en orden de aparición y luego los 2 estructurales); `len(tabla)==18`; `tabla.capacidad==37`; `tabla.colisiones==7`; `lineas_invalidas()==[2,3,4,5,6,7,8,10,12,13]`.
  - `analizar_archivo("ejemplos/casos_limite.flow")`: válida, 118 tokens.
  - `analizar_texto("")`: 0 tokens, `SIN-001`, no válida, `cantidad_lineas==0`.
  - Léxicamente válida pero estructuralmente no: `x = 1;` → `es_valida_lexicamente`, no `es_valida_estructuralmente`, no `es_valida`.
  - **Pasos**: para `inicio x = @ fin` → 5 pasos léxicos numerados 1–5; el 4.º tiene `token.tipo==ERROR` y un diagnóstico `LEX-001`; los demás, `diagnosticos==()`; el paso de `x` tiene `instalacion.es_nueva`; el de `=` tiene `instalacion is None`; después `None`; `terminada`.
  - Pasos estructurales: `x = 1;` → tras los 4 pasos léxicos, 2 pasos con `fase==FASE_ESTRUCTURAL`, `token is None` y un diagnóstico cada uno (`SIN-002`, `SIN-003`).
  - **Progresividad**: tras el primer `siguiente_paso()` de una sesión sobre `incorrecto.flow`, `resultado.tokens` tiene 1 elemento, `resultado.terminado` es `False` y `es_valida` es `False`.
  - `terminar()` a mitad de sesión produce el mismo resultado (tokens, diagnósticos, tamaño de tabla) que `analizar_texto`.
  - `siguiente_paso()` después de terminar devuelve `None` sin error y no duplica diagnósticos.
  - `descripcion` de un paso con error contiene el código y `linea:columna`.
  - `tokenizar` devuelve los mismos tokens que el resultado completo.
  - `explicar_token`: para `45.5` → `reconocedor=="AFD de números"`, `recorrido==("q0","q1","q1","q2","q3")`, `regex` igual a la de `INFO_CATEGORIAS[DECIMAL]`; para `si` → `detalle` contiene la descripción de `PALABRAS_RESERVADAS["si"]`; para `>=` → `reconocedor=="Tabla de operadores y delimitadores"`, `recorrido==()`; para un token `ERROR` `3.` → `detalle` contiene `LEX-003`; con `tabla`, `detalle` contiene la cubeta.
  - `test_dominio_sin_tkinter`: en un subproceso (`sys.executable -c`) importar `application.analisis_service` y `application.archivos` y comprobar que `"tkinter" not in sys.modules`.
  - Independencia de sesiones: dos `analizar_texto` seguidos no comparten tabla ni manejador.

### A10 — Cierre de la Fase A
- **Archivos:** `README.md` (qué es, requisitos, cómo ejecutar pruebas; se ampliará en B8).
- **Criterios:** batería completa en verde con `/opt/homebrew/bin/python3.14` **y** con otro intérprete ≥ 3.10 si está disponible; `grep -rn "tkinter" core application config` no devuelve nada; `grep -n "^def \|^class " config/reglas.py` no devuelve nada; `grep -rn "^import re\|^from re" core application config` no devuelve nada; ningún archivo de `core/` o `application/` supera ~200 líneas (justificar en `revisiones.md` si alguno lo hace); registrar el resultado en la tabla de este archivo.

---

# FASE B — Interfaz, integración y `main.py`

El diseño visual y de interacción está en `docs/02_arquitectura.md` §8–§10. Aquí el contrato es menos estricto en firmas internas, pero los **nombres de clase, los métodos listados y los comportamientos** son obligatorios. Responsable: **developer-sonnet**. Estado inicial: **Pendiente**.

### B1 — Tema (`ui/estilos.py`)
- `TEMA: dict[str, str]` con al menos: `fondo` `#1e1e1e`, `panel` `#252526`, `barra` `#333333`, `borde` `#3c3c3c`, `texto` `#d4d4d4`, `texto_tenue` `#858585`, `acento` `#007acc`, `seleccion` `#264f78`, `error` `#f44747`, `exito` `#4ec9b0`, `advertencia` `#cca700`, `linea_actual` `#2a2d2e`, `colision` `#3a2f1b`.
- `COLORES_TOKEN: dict[TipoToken, str]` con una entrada por cada `TipoToken` (reservada `#569cd6`, identificador `#9cdcfe`, entero y decimal `#b5cea8`, cadena `#ce9178`, comentario `#6a9955`, operadores `#d4d4d4`, asignación `#d4d4d4`, delimitador `#ffd700`, error `#f44747`).
- `fuente_codigo(tamano: int = 13) -> tuple[str, int]`: primera familia disponible de `Menlo`, `Consolas`, `DejaVu Sans Mono`, `Courier New`.
- `aplicar_tema(raiz) -> None`: `ttk.Style` sobre el tema `clam`; estilos para `TFrame`, `TLabel`, `TButton`, `Treeview` (+ `Treeview.Heading`), `TNotebook` (+ `.Tab`), `TPanedwindow`, barras de desplazamiento.
- **Criterio:** ningún color en hexadecimal aparece fuera de `ui/estilos.py` (`grep -rn "#[0-9a-fA-F]\{6\}" ui/ | grep -v estilos.py` vacío).

### B2 — Editor (`ui/editor.py`)
- `class EditorCodigo(ttk.Frame)`: `__init__(self, padre, al_cambiar=None, al_mover_cursor=None)`.
- Métodos: `obtener_texto() -> str` (sin el salto final que añade Tk), `establecer_texto(texto)`, `limpiar()`, `resaltar(tokens)`, `marcar_errores(diagnosticos)`, `limpiar_marcas()`, `resaltar_token_actual(token | None)`, `ir_a(linea, columna)`, `solo_lectura(activo: bool)`, `posicion_cursor() -> tuple[int, int]` (línea y columna desde 1).
- Margen de números sincronizado con el desplazamiento; `✗` en las líneas con diagnóstico léxico; línea del cursor resaltada; subrayado rojo en el rango de cada token `ERROR`; *debounce* de 300 ms para `al_cambiar`.
- **Criterios:** tras `establecer_texto(t)`, `obtener_texto() == t`; un token en (línea 2, columna 7) de longitud 5 se etiqueta en `2.6`–`2.11`; un comentario de bloque multilínea se colorea completo.

### B3 — Componentes (`ui/componentes.py`)
- `BarraHerramientas(padre, acciones: dict[str, Callable])` con botones `abrir`, `guardar`, `analizar`, `paso`, `detener`, `limpiar`, `ayuda`; método `habilitar(nombres: Iterable[str])` (deshabilita el resto).
- `PanelLateral(padre, al_elegir_ejemplo: Callable[[Path], None])`: lista de `listar_ejemplos()`; árbol «FlowLang» construido **desde `config.reglas`** (reservadas con descripción, operadores por categoría, delimitadores, escapes, límites). Añadir una palabra a `PALABRAS_RESERVADAS` debe reflejarse sin tocar este archivo.
- `PanelConsola(padre)`: `escribir(texto, nivel="normal")` con niveles `normal`, `error`, `exito`, `info`; `limpiar()`; desplazamiento automático al final.
- `BarraEstado(padre, al_ver_tabla: Callable)`: `establecer_estado(texto)`, `establecer_contadores(tokens, errores)`, `establecer_posicion(linea, columna)`, `habilitar_ver_tabla(activo)`.

### B4 — Paneles de resultados (`ui/paneles.py`)
- `PanelResultados(padre, al_seleccionar_token: Callable[[Token], None], al_seleccionar_error: Callable[[Diagnostico], None])` con `ttk.Notebook` de 5 pestañas.
- Constantes de columnas a nivel de módulo: `COLUMNAS_TOKENS`, `COLUMNAS_SIMBOLOS`, `COLUMNAS_ERRORES` (listas de `(identificador, título, ancho)`).
- Métodos: `agregar_token(numero, token)`, `agregar_error(diagnostico)`, `mostrar_tabla_simbolos(tabla)`, `mostrar_estadisticas(resultado)`, `mostrar_explicacion(explicacion)`, `limpiar()`, `habilitar_tabla_simbolos(activo)`, `seleccionar_pestana(nombre)` con nombres `"tokens"`, `"simbolos"`, `"errores"`, `"estadisticas"`, `"educativo"`.
- Tabla de símbolos: filas en orden de cubeta; fondo `TEMA["colision"]` en las entradas de cubetas con más de un elemento; línea de resumen con los 6 datos de `EstadisticasTabla`; `valor` y lexemas largos recortados a 40 caracteres.
- Estadísticas: veredictos léxico / estructura / global, tokens por categoría con barra proporcional (`Canvas`), líneas, caracteres, errores por tipo.

### B5 — Ventana principal y flujo progresivo (`ui/interfaz.py`)
- `class VentanaPrincipal(tk.Tk)`: `__init__(self, solicitar_archivo: bool = True)`.
- Constantes: `RETARDO_ANIMACION_MS = 20`, `DURACION_MAXIMA_ANIMACION_MS = 3000`.
- Métodos públicos (usados por atajos, botones y la prueba de humo): `abrir_archivo(ruta=None)`, `guardar_archivo()`, `analizar()`, `paso_a_paso()`, `detener()`, `limpiar()`, `mostrar_ayuda()`, `ver_tabla_simbolos()`; atributos `sesion` (`SesionAnalisis | None`) y `estado` (`"SIN_FUENTE"`, `"LISTO"`, `"ANALIZANDO"`, `"TERMINADO"`).
- Comportamiento obligatorio:
  1. **Requisito 6**: con `solicitar_archivo=True`, tras mostrarse la ventana se abre `filedialog.askopenfilename` (título «Seleccione el archivo con las cadenas de entrada», filtros `.flow`/`.txt`). `analizar()` en `SIN_FUENTE` vuelve a solicitarlo.
  2. `abrir_archivo` usa `cargar_fuente`; ante `ErrorArchivo` muestra el diagnóstico en consola, pestaña Errores y `messagebox.showerror`, sin cambiar el contenido del editor.
  3. **Requisito 5a**: `analizar()` crea la sesión (o continúa la existente) y consume pasos con `after`; por cada paso: `agregar_token`, línea en consola, `resaltar_token_actual`, y por cada diagnóstico `agregar_error` + marca en el editor + contadores. El primer error selecciona la pestaña Errores. Pasos por *tick* = `max(1, ceil(estimado / (DURACION_MAXIMA_ANIMACION_MS / RETARDO_ANIMACION_MS)))` con `estimado = len(fuente) // 4`.
  4. `paso_a_paso()` consume exactamente un paso, selecciona la pestaña Modo educativo y muestra `explicar_token` del token actual.
  5. **Requisito 5b**: al devolver `None` la sesión: veredictos en consola (léxico, estructura, global, líneas inválidas), `mostrar_estadisticas`, `mostrar_tabla_simbolos`, `habilitar_tabla_simbolos(True)`, `habilitar_ver_tabla(True)` y `messagebox.askyesno("Análisis terminado", "… ¿Desea ver la tabla de símbolos?")`; «Sí» → `ver_tabla_simbolos()`.
  6. Durante `ANALIZANDO` el editor está en solo lectura; editar en `TERMINADO` vuelve a `LISTO` y avisa en la barra de estado.
  7. Atajos: Ctrl+O, Ctrl+S, F5, F10, Esc, F1 (en macOS también Cmd+O / Cmd+S).
  8. Tamaño inicial 1280×800, mínimo 1000×650; título `SmartLex Studio — <archivo>`.
- **Criterio de arquitectura:** `ui/` no importa `core.lexer`, `core.validador`, `core.simbolos` ni `core.afd` (`grep -rn "core.lexer\|core.validador\|core.simbolos\|core.afd" ui/` vacío).

### B6 — Punto de entrada y prueba de humo (`main.py`, `tests/test_ui_humo.py`)
- `main.py`: si `import tkinter` falla, imprime un mensaje claro (cómo instalar Tk o usar `--consola`) y termina con código 1; si no, `VentanaPrincipal().mainloop()`.
- `tests/test_ui_humo.py`: `@unittest.skipUnless` hay tkinter y se puede crear `tk.Tk()`. Con `messagebox` y `filedialog` sustituidos (`unittest.mock.patch`):
  - crear `VentanaPrincipal(solicitar_archivo=False)`, `abrir_archivo("ejemplos/incorrecto.flow")`, `analizar()`, bombear `update()` hasta `estado == "TERMINADO"` (máximo 10 s);
  - comprobar: 57 filas en Tokens, 15 en Errores, `askyesno` llamado **una** vez con un texto que contiene «tabla de símbolos», pestaña de símbolos habilitada, 18 filas tras `ver_tabla_simbolos()`;
  - **progresividad**: tras `abrir_archivo` + un único `paso_a_paso()`, hay 1 fila en Tokens, `estado == "ANALIZANDO"` y la pestaña de símbolos sigue deshabilitada;
  - `abrir_archivo("no_existe.flow")` llama a `showerror` y no lanza excepción;
  - `destroy()` al final de cada prueba.

### B7 — Modo consola (recomendada, prioridad baja)
- `python main.py --consola [ruta]`: si falta la ruta la pide con `input("Archivo de entrada: ")`; imprime tokens, diagnósticos (código, posición, mensaje, sugerencia), veredicto, y pregunta `¿Desea ver la tabla de símbolos? (s/n)`. Máximo ~60 líneas, dentro de `main.py`. Sin tkinter.
- **Prueba:** en `tests/test_integracion.py`, subproceso con `--consola ejemplos/correcto.flow` y entrada `n` → código de salida 0 y la salida contiene `VÁLIDA`.

### B8 — Cierre: ensayo de modificaciones y documentación
- Ensayar **en una copia** las modificaciones de la arquitectura §11 «agregar `repetir`», «agregar operador `**`», «permitir `ñ` en identificadores» y «aceptar `5.` como decimal»; anotar en `docs/06_guia_sustentacion.md` los pasos exactos y el resultado (cada una debe requerir tocar solo los lugares indicados).
- `docs/04_manual_usuario.md` (uso con capturas o descripciones), `docs/05_pruebas.md` (salida de la batería, cobertura por requisito), `docs/06_guia_sustentacion.md` (cómo explicar cada módulo, preguntas probables y respuestas, tabla de modificaciones).
- Ampliar `README.md`; completar `docs/matriz_requisitos.md` con evidencia; registrar verificaciones manuales M1–M3.

---

## Criterios de aprobación por fase (arquitecto)

**Fase A aprobada si:** toda la batería pasa; contrato respetado nombre a nombre; los tres comandos `grep` de A10 no devuelven nada; los valores numéricos de la especificación §12 se reproducen.

**Fase B aprobada si:** prueba de humo en verde; verificaciones manuales M1–M3 registradas; `ui/` cumple la regla de dependencias; agregar `repetir` a `PALABRAS_RESERVADAS` cambia lexer, resaltado, panel lateral y modo educativo sin tocar ningún otro archivo.
