# Tareas — SmartLex Studio

Documentos de referencia obligatorios antes de implementar: `docs/03_especificacion.md` (el lenguaje) y `docs/02_arquitectura.md` (el diseño). Si este archivo y aquellos se contradicen, **gana la especificación** y se registra la discrepancia en `agents/revisiones.md`.

## Registro de ejecución

| Tarea | Agente | Modelo | Estado | Resultado |
|---|---|---|---|---|
| Pasos 1–5: requisitos, investigación, especificación, arquitectura, tareas | architect-fable | claude-fable-5-2 | completado | `docs/matriz_requisitos.md`, `docs/01_investigacion.md`, `docs/02_arquitectura.md`, `docs/03_especificacion.md`, `agents/tareas.md`, `agents/decisiones.md`, `agents/revisiones.md`, `ejemplos/*.flow` (3 archivos validados con prototipo) |
| Fase A (A1–A10) | developer-sonnet | claude-sonnet-5-5 | completado | 87 pruebas en verde con python3.11/3.12/3.14/3.15; `grep` de A10 vacíos; reproduce los valores de la especificación §12. Decisiones D-26 a D-28 pendientes de revisión |
| Auditoría Fase A | reviewer-opus | claude-opus-5-5 | completado | APROBADO CON OBSERVACIONES: 14 hallazgos (0 críticos/altos, 4 medios, 10 bajos); 7 corregidos con prueba (`tests/test_auditoria_fase_a.py`), 6 escalados (E-1…E-6); 93 pruebas OK; D-26/D-27/D-28 aprobadas. Ver `docs/06_auditoria.md` |
| Aprobación Fase A y resolución de escalados E-1…E-6 | architect-fable | claude-fable-5-2 | completado | **Fase A APROBADA.** D-26/D-27/D-28 ratificadas (D-29); E-1…E-6 resueltos (D-30…D-35); tarea B0 añadida; B2, B4, B5, B6 y B8 ajustadas. **Fase B AUTORIZADA** |
| Fase B (B0–B7) | developer-sonnet | claude-sonnet-5-5 | completado (B8 pendiente, paso 11) | B0–B7 hechas; 109 pruebas OK con python3.14 (incl. 12 de humo de UI y 3 del modo consola); la app arrancó y analizó sin excepciones; capturas NO posibles (D-40); D-36…D-40 pendientes de revisión |
| Cierre Fase B (B9, B10, manual, README) | developer-sonnet | claude-sonnet-5-5 | completado | B9 (un solo error de archivo) y B10 (una línea por dato en `detalle`) con pruebas; `docs/04_manual_usuario.md` y `README.md` ampliados; 117 pruebas OK con python3.14; captura 4 pendiente (orquestador) |
| Auditoría Fase B y final (paso 9) | reviewer-opus | claude-opus-5-5 | completado | APROBADO CON OBSERVACIONES: 13 hallazgos (0 críticos, 1 alto, 1 medio, 5 bajos, 6 sugerencias); 7 corregidos con prueba (`tests/test_auditoria_fase_b.py`, las 6 fallan en `dc4e725`), 2 escalados (E-7, E-8); 115 pruebas OK; requisitos 1–6 del PDF cumplen; D-36…D-39 aprobadas, D-40 superada; capturas rehechas. Ver `docs/06_auditoria.md` |
| Revisión final (paso 10) y guía de sustentación (paso 11) | architect-fable | claude-fable-5-2 | completado | **APROBADO.** Código real conforme a la arquitectura; D-36…D-40 ratificadas (D-41); E-7 → tarea B9 (D-42); E-8 → tarea B10 (D-43); `docs/02_arquitectura.md` (§15 nuevo) y `docs/03_especificacion.md` sincronizados; `docs/05_guia_sustentacion.md` escrito con 10 ejercicios verificados en copias temporales. Pendiente de Sonnet: B9, B10, manual de usuario y README |
| Revisión de cierre (B9, B10, manual, README) | reviewer-opus | claude-opus-5-5 | completado | **APROBADO.** B9/B10 correctos; AUD-28 (`after` huérfanos al destruir la ventana) corregido con prueba; errata del manual (Detener) corregida; 3 corridas `Ran 118 tests` · `OK` sin trazas |
| Diseño del rediseño visual estilo PyCharm | architect-fable | claude-fable-5-2 | completado | `docs/02_arquitectura.md` §16 (zonas, paleta, tipografías, iconos, *tool windows*, riesgos); tareas B11–B16 (Fase C); decisiones D-44…D-53. **Fase C AUTORIZADA** |
| Fase C (B11–B16) | developer-sonnet | claude-sonnet-5-5 | completado (pendiente de revisión) | B11–B16 implementadas; 141 pruebas con python3.14 (Tk 9.0), la única falla es `test_conteos_de_flowlang_1_0` por un cambio local ajeno en `config/reglas.py`; capturas reales 1..6 y tabla de 10 puntos en `docs/06_auditoria.md`; decisiones D-54…D-59 pendientes de revisión; Tk 8.6 y M5 pendientes |
| B17 Nuevo archivo (Ctrl+N) | developer-sonnet | claude-sonnet-5-5 | completado (pendiente de revisión) | `crear_fuente`/`plantilla_nueva`, icono y menú, atajos, árbol Proyecto actualizado; 151 pruebas, única falla `test_conteos_de_flowlang_1_0` (cambio local ajeno); D-60 |
| Diseño del rediseño claro estilo académico (Fase D) | architect-fable | claude-fable-5-2 | completado | `docs/02_arquitectura.md` §17 (zonas, paleta, pausa por línea, qué se elimina y reutiliza, pruebas a adaptar); tareas C1–C8; decisiones D-61…D-72; incluye la corrección pendiente AUD-29/31/32 |
| Fase D (C1–C8) | developer-sonnet | claude-sonnet-5-5 | completado (pendiente de revisión) | C1–C8 implementadas; 174 pruebas con python3.14 (Tk 9.0), solo las 2 fallas de D-72, tres corridas iguales; 6 capturas reales en 3 iteraciones y tabla de comparación en `docs/06_auditoria.md`; AUD-29/31/32 cerrados con prueba; D-73 pendiente de revisión; Tk 8.6 y M5 no probados |
| Auditoría Fase D | reviewer-opus | claude-opus-5-5 | completado | AUD-33 (tabla de símbolos legible: `lín:col`, «Veces», `verdadero/falso`) y AUD-34 (tope de 10 s y repintado en archivos largos) corregidos con prueba; AUD-35/36 bajos al arquitecto; O-2 no es defecto; D-73 aprobable; 176 pruebas, 2 fallas esperadas, 0 trazas en 3 corridas |

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
| `TIPO_DATO_BOOLEANO` | `str` | `"booleano"` — tipo de dato de las palabras de `VALORES_BOOLEANOS` *(añadida tras la auditoría, D-30; tarea B0)* |
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

Responsable de todas: **developer-sonnet**. Estado: **A1–A10 completadas** (ver registro de ejecución).

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

El diseño visual y de interacción está en `docs/02_arquitectura.md` §8–§10. Aquí el contrato es menos estricto en firmas internas, pero los **nombres de clase, los métodos listados y los comportamientos** son obligatorios. Responsable: **developer-sonnet**. Estado: **B0–B7 completadas; B8 pendiente (paso 11)**.

### B0 — Ajustes posteriores a la auditoría de la Fase A (hacer primero)
- **Archivos:** `config/reglas.py`, `core/simbolos.py`, `tests/test_afd.py`, `tests/test_simbolos.py`.
- **B0.1 (E-2, D-30):** añadir `TIPO_DATO_BOOLEANO = "booleano"` a `reglas.py` y usarla en `registrar_token` en lugar del literal. Prueba nueva en `TestReglas`: `TIPO_DATO_BOOLEANO in TIPOS_DE_DATO`. Criterio: `grep -n '"booleano"' core/ application/ -r` vacío.
- **B0.2 (E-4, D-32):** renombrar `test_conteos` a `test_conteos_de_flowlang_1_0` y dar a cada `assertEqual` el mensaje `"FlowLang 1.0 define N …; si modificó el lenguaje a propósito, actualice este número"`. No relajar a `>=`.
- **B0.3 (AUD-12):** el docstring de `Lexer.tokens()` debe decir que es de un solo uso.
- **Criterios:** las 93 pruebas siguen en verde (94 con la nueva); ninguna firma pública cambia; los valores de la especificación §12 no cambian.
- No se toca `core/errores.py` (E-3 queda como limitación documentada, D-31) ni `EstadisticasTabla` (E-1 se resuelve en la UI, D-33).

### B1 — Tema (`ui/estilos.py`)
- `TEMA: dict[str, str]` con al menos: `fondo` `#1e1e1e`, `panel` `#252526`, `barra` `#333333`, `borde` `#3c3c3c`, `texto` `#d4d4d4`, `texto_tenue` `#858585`, `acento` `#007acc`, `seleccion` `#264f78`, `error` `#f44747`, `exito` `#4ec9b0`, `advertencia` `#cca700`, `linea_actual` `#2a2d2e`, `colision` `#3a2f1b`.
- `COLORES_TOKEN: dict[TipoToken, str]` con una entrada por cada `TipoToken` (reservada `#569cd6`, identificador `#9cdcfe`, entero y decimal `#b5cea8`, cadena `#ce9178`, comentario `#6a9955`, operadores `#d4d4d4`, asignación `#d4d4d4`, delimitador `#ffd700`, error `#f44747`).
- `fuente_codigo(tamano: int = 13) -> tuple[str, int]`: primera familia disponible de `Menlo`, `Consolas`, `DejaVu Sans Mono`, `Courier New`.
- `aplicar_tema(raiz) -> None`: `ttk.Style` sobre el tema `clam`; estilos para `TFrame`, `TLabel`, `TButton`, `Treeview` (+ `Treeview.Heading`), `TNotebook` (+ `.Tab`), `TPanedwindow`, barras de desplazamiento.
- **Criterio:** ningún color en hexadecimal aparece fuera de `ui/estilos.py` (`grep -rn "#[0-9a-fA-F]\{6\}" ui/ | grep -v estilos.py` vacío).

### B2 — Editor (`ui/editor.py`)
- `class EditorCodigo(ttk.Frame)`: `__init__(self, padre, al_cambiar=None, al_mover_cursor=None)`.
- Métodos: `obtener_texto() -> str` (sin el salto final que añade Tk y **con `\r\n` y `\r` convertidos a `\n`**, E-5), `establecer_texto(texto)` (aplica la misma normalización antes de insertar), `limpiar()`, `resaltar(tokens)`, `marcar_errores(diagnosticos)`, `limpiar_marcas()`, `resaltar_token_actual(token | None)`, `ir_a(linea, columna)`, `solo_lectura(activo: bool)`, `posicion_cursor() -> tuple[int, int]` (línea y columna desde 1).
- Margen de números sincronizado con el desplazamiento; `✗` en las líneas con diagnóstico léxico; línea del cursor resaltada; subrayado rojo en el rango de cada token `ERROR`; *debounce* de 300 ms para `al_cambiar`.
- El texto que se analiza y el que se resalta salen **siempre** de `obtener_texto()`: así las columnas del lexer coinciden con los índices de Tk aunque se pegue texto con `\r`.
- **Criterios:** tras `establecer_texto(t)`, `obtener_texto() == t` (para `t` sin `\r`); tras `establecer_texto("a\r\nb\rc")`, `obtener_texto() == "a\nb\nc"`; un token en (línea 2, columna 7) de longitud 5 se etiqueta en `2.6`–`2.11`; un comentario de bloque multilínea se colorea completo.

### B3 — Componentes (`ui/componentes.py`)
- `BarraHerramientas(padre, acciones: dict[str, Callable])` con botones `abrir`, `guardar`, `analizar`, `paso`, `detener`, `limpiar`, `ayuda`; método `habilitar(nombres: Iterable[str])` (deshabilita el resto).
- `PanelLateral(padre, al_elegir_ejemplo: Callable[[Path], None])`: lista de `listar_ejemplos()`; árbol «FlowLang» construido **desde `config.reglas`** (reservadas con descripción, operadores por categoría, delimitadores, escapes, límites). Añadir una palabra a `PALABRAS_RESERVADAS` debe reflejarse sin tocar este archivo.
- `PanelConsola(padre)`: `escribir(texto, nivel="normal")` con niveles `normal`, `error`, `exito`, `info`; `limpiar()`; desplazamiento automático al final.
- `BarraEstado(padre, al_ver_tabla: Callable)`: `establecer_estado(texto)`, `establecer_contadores(tokens, errores)`, `establecer_posicion(linea, columna)`, `habilitar_ver_tabla(activo)`.

### B4 — Paneles de resultados (`ui/paneles.py`)
- `PanelResultados(padre, al_seleccionar_token: Callable[[Token], None], al_seleccionar_error: Callable[[Diagnostico], None])` con `ttk.Notebook` de 5 pestañas.
- Constantes de columnas a nivel de módulo: `COLUMNAS_TOKENS`, `COLUMNAS_SIMBOLOS`, `COLUMNAS_ERRORES` (listas de `(identificador, título, ancho)`).
- Métodos: `agregar_token(numero, token)`, `agregar_error(diagnostico)`, `mostrar_tabla_simbolos(tabla)`, `mostrar_estadisticas(resultado)`, `mostrar_explicacion(explicacion)`, `limpiar()`, `habilitar_tabla_simbolos(activo)`, `seleccionar_pestana(nombre)` con nombres `"tokens"`, `"simbolos"`, `"errores"`, `"estadisticas"`, `"educativo"`.
- Tabla de símbolos: filas en orden de cubeta; fondo `TEMA["colision"]` en las entradas de cubetas con más de un elemento; línea de resumen con capacidad, entradas, factor de carga, **«Colisiones al insertar»** (`colisiones`), **«En la tabla actual»** (`cantidad - cubetas_ocupadas`, calculado aquí; E-1), cadena más larga y redimensionados; `valor` y lexemas largos recortados a 40 caracteres.
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
  9. **Navegación**: doble clic en una fila de Errores → `editor.ir_a(linea, columna)` y foco en el editor (los diagnósticos de archivo, con línea 0, no navegan). Clic en una fila de Tokens → selecciona el lexema en el editor y muestra `explicar_token(token, tabla)` en Modo educativo (sin cambiar de pestaña).
  10. En un paso de fase estructural (`paso.token is None`) no se llama a `explicar_token`; se muestra el diagnóstico en consola y Errores, y `ir_a` su posición.
  11. `sesion.resultado.tabla` solo se entrega a `mostrar_tabla_simbolos` al terminar; durante la evaluación la UI no lee la tabla salvo para `explicar_token`.
  12. No añadir lógica a `application/analisis_service.py` (ya está en 239 líneas, D-26); si la Fase B necesitara algo nuevo del servicio, registrarlo antes en `revisiones.md`.
  8. Tamaño inicial 1280×800, mínimo 1000×650; título `SmartLex Studio — <archivo>`.
- **Criterio de arquitectura:** `ui/` no importa `core.lexer`, `core.validador`, `core.simbolos` ni `core.afd` (`grep -rn "core.lexer\|core.validador\|core.simbolos\|core.afd" ui/` vacío).

### B6 — Punto de entrada y prueba de humo (`main.py`, `tests/test_ui_humo.py`)
- `main.py`: si `import tkinter` falla, imprime un mensaje claro (cómo instalar Tk o usar `--consola`) y termina con código 1; si no, `VentanaPrincipal().mainloop()`.
- `tests/test_ui_humo.py`: `@unittest.skipUnless` hay tkinter y se puede crear `tk.Tk()`. Con `messagebox` y `filedialog` sustituidos (`unittest.mock.patch`):
  - crear `VentanaPrincipal(solicitar_archivo=False)`, `abrir_archivo("ejemplos/incorrecto.flow")`, `analizar()`, bombear `update()` hasta `estado == "TERMINADO"` (máximo 10 s);
  - comprobar: 57 filas en Tokens, 15 en Errores, `askyesno` llamado **una** vez con un texto que contiene «tabla de símbolos», pestaña de símbolos habilitada, 18 filas tras `ver_tabla_simbolos()`;
  - **progresividad**: tras `abrir_archivo` + un único `paso_a_paso()`, hay 1 fila en Tokens, `estado == "ANALIZANDO"` y la pestaña de símbolos sigue deshabilitada;
  - `abrir_archivo("no_existe.flow")` llama a `showerror` y no lanza excepción;
  - **requisito 6**: con `VentanaPrincipal(solicitar_archivo=True)` y `askopenfilename` simulado devolviendo `ejemplos/correcto.flow`, tras bombear `update()` el editor contiene el archivo y `askopenfilename` se llamó una vez; devolviendo `""` el estado es `"SIN_FUENTE"`;
  - **errores durante la evaluación**: sobre `incorrecto.flow`, avanzar con `paso_a_paso()` hasta el primer token `ERROR`: en ese momento hay 1 fila en Errores, el editor tiene la marca de error en `2.11`–`2.14` y la sesión no ha terminado;
  - **navegación**: invocar el callback de selección de error con el diagnóstico de 6:24 deja `posicion_cursor() == (6, 24)`;
  - **modo educativo**: tras `paso_a_paso()` el panel educativo no está vacío;
  - **colisiones (E-1)**: tras analizar `correcto.flow`, el resumen de la tabla contiene `14` y `7`;
  - **`\r` (E-5)**: `establecer_texto("x\r\ny")` + `analizar()` completo → el token `y` está en 2:1;
  - **fuera del BMP (E-5)**: solo si `tk.TkVersion >= 9` (si no, `skipTest`): con el texto `inicio "😀" x fin`, el rango etiquetado del token `x` (línea 1, columna 12) es `1.11`–`1.12`;
  - `destroy()` al final de cada prueba.

### B7 — Modo consola (recomendada, prioridad baja)
- `python main.py --consola [ruta]`: si falta la ruta la pide con `input("Archivo de entrada: ")`; imprime tokens, diagnósticos (código, posición, mensaje, sugerencia), veredicto, y pregunta `¿Desea ver la tabla de símbolos? (s/n)`. Máximo ~60 líneas, dentro de `main.py`. Sin tkinter.
- **Prueba:** en `tests/test_integracion.py`, subproceso con `--consola ejemplos/correcto.flow` y entrada `n` → código de salida 0 y la salida contiene `VÁLIDA`.

### B9 — Un solo error de archivo visible (E-7, D-42)
- **Archivos:** `ui/paneles.py`, `ui/interfaz.py`, `tests/test_ui_humo.py`.
- Añadir `PanelResultados.quitar_errores_de_archivo() -> None`: elimina de la tabla de Errores las filas cuyo tipo es `TipoDiagnostico.ARCHIVO` (y borra el detalle si mostraba una de ellas).
- `VentanaPrincipal._mostrar_error_archivo` la llama **antes** de `agregar_error`. No se tocan los contadores de la barra de estado (cuentan los errores del análisis).
- **Prueba:** dos `abrir_archivo("no_existe.flow")` seguidos → 1 fila en Errores; tras analizar `incorrecto.flow` (15 filas) y dos aperturas fallidas → 16 filas, las 15 del análisis intactas.

### B10 — Una línea por dato en el detalle del Modo educativo (E-8, D-43)
- **Archivos:** `application/analisis_service.py` (solo el texto de `explicar_token`), `tests/test_integracion.py`.
- La primera línea de `detalle` (`Lexema: …   Categoría: …   Posición: …`) se parte en tres líneas: `Lexema: …`, `Categoría: …`, `Posición: línea L, columna C`. Todas las líneas de `detalle` quedan con la forma `Campo: valor`. No se añaden campos a `ExplicacionToken` ni cambia ninguna firma; `ui/paneles.py` no se toca.
- **Prueba:** para el token `45.5` en 6:23, `detalle.split("\n")[:3] == ["Lexema: 45.5", "Categoría: Decimal", "Posición: línea 6, columna 23"]`; las pruebas existentes de `detalle` siguen en verde.
- Tras B9 y B10: rehacer la captura `docs/capturas/4_modo_educativo.png` con `docs/capturas/capturar.py`.

### B8 — Cierre: ensayo de modificaciones y documentación
- Ensayar **en una copia** las modificaciones de la arquitectura §11 «agregar `repetir`», «agregar operador `**`», «permitir `ñ` en identificadores» y «aceptar `5.` como decimal»; anotar en `docs/05_guia_sustentacion.md` los pasos exactos (incluido «actualizar `test_conteos_de_flowlang_1_0`» cuando corresponda) y el resultado (cada una debe requerir tocar solo los lugares indicados).
- **Nombres definitivos (D-35, los que pide el encargo):** `docs/04_manual_usuario.md` (uso con capturas o descripciones), `docs/05_guia_sustentacion.md` (cómo explicar cada módulo, preguntas probables y respuestas, tabla de modificaciones, las dos medidas de colisiones, la limitación D-31 y la prueba de conteos D-32). `docs/06_auditoria.md` ya existe y lo mantiene el auditor: la evidencia de pruebas (salida de la batería, cobertura por requisito) va **ahí**, en una sección «Auditoría Fase B y final»; no se crea `05_pruebas.md`.
- Verificación manual adicional **M4** (registrar en `06_auditoria.md`): pegar en el editor un texto con emoji dentro de una cadena y comprobar que el resaltado de los tokens posteriores no se desplaza; si el laboratorio usa Tcl/Tk 8.6 y se desplaza, queda documentado como limitación visual (los tokens y posiciones del análisis son correctos en cualquier caso).
- Ampliar `README.md`; completar `docs/matriz_requisitos.md` con evidencia; registrar verificaciones manuales M1–M3.

---

> **Estado de B8 tras la revisión final:** `docs/05_guia_sustentacion.md` ya está escrito por el arquitecto, con los 10 ejercicios ensayados en copias. A developer-sonnet le quedan `docs/04_manual_usuario.md`, ampliar `README.md`, y B9–B10.

## Criterios de aprobación por fase (arquitecto)

**Fase A aprobada si:** toda la batería pasa; contrato respetado nombre a nombre; los tres comandos `grep` de A10 no devuelven nada; los valores numéricos de la especificación §12 se reproducen.

**Fase B aprobada si:** prueba de humo en verde; verificaciones manuales M1–M3 registradas; `ui/` cumple la regla de dependencias; agregar `repetir` a `PALABRAS_RESERVADAS` cambia lexer, resaltado, panel lateral y modo educativo sin tocar ningún otro archivo.

> **Estado final (paso 11):** B9 y B10 completadas; B8 manual de usuario y README completados; la guía de sustentación (05) es del arquitecto.

---

# FASE C — Rediseño visual estilo PyCharm (solo `ui/`)

**Leer antes de empezar:** `docs/02_arquitectura.md` **§16** completo (es la especificación; estas tareas solo la reparten) y las decisiones D-44…D-53. Referencia visual del usuario: `/private/tmp/claude-501/-Volumes-Ojito-proyecto-de-lenguajes/001cc0b7-bd4c-4a80-909f-4edbc49746a8/images/2.png` (PyCharm New UI oscuro; si ya no existe, vale la lista de comprobación de §16.10). No se copia esa imagen al repositorio.

Reglas de la fase (además de las generales):

1. **Solo se modifican** `ui/`, `tests/test_ui_humo.py`, `tests/test_auditoria_fase_b.py`, `tests/test_ui_rediseno.py` (nuevo), `docs/capturas/` y los documentos de B16. Si parece necesario tocar `core/`, `application/`, `config/` o `main.py`: **no hacerlo**, anotarlo en `agents/revisiones.md`.
2. Colores: ningún literal `#rrggbb` fuera de `ui/estilos.py`. Comprobación: `grep -nE "#[0-9a-fA-F]{6}" ui/*.py | grep -v "^ui/estilos.py"` no devuelve nada.
3. Los métodos públicos de `VentanaPrincipal`, los cuatro estados, `_BOTONES_POR_ESTADO`, el temporizador y `_consumir_paso` conservan su comportamiento. No se reescribe lo que funciona: se cambia de sitio y de aspecto.
4. Al terminar **cada** tarea: batería completa en verde con `/opt/homebrew/bin/python3.14 -m unittest discover -s tests -t . -v` y la aplicación arranca (`python3.14 main.py`) sin trazas. Un *commit* por tarea.
5. Las pruebas existentes pueden cambiar **solo** de nombres de atributos (tabla de B16); ninguna aserción se elimina ni se relaja, salvo AUD-18, que se reformula como indica B16.
6. Si algo de §16 no se puede hacer en Tk tal como está escrito, aplicar la variante más simple que conserve el aspecto, y registrarla en `agents/decisiones.md` (D-54 en adelante) como «pendiente de revisión del arquitecto».

### B11 — Paleta, tipografías y estilos `ttk` (`ui/estilos.py`) — **estado: hecha (Fase C, developer-sonnet)**
- `TEMA` con las 24 claves y valores exactos de §16.3 (las 16 actuales cambian de valor; 8 nuevas). `COLORES_TOKEN` con los valores de §16.3. Nueva constante `TIPOS_EN_CURSIVA = (TipoToken.COMENTARIO,)`.
- Listas de fuentes de §16.4 y función privada `_puntos(tamano)`; `fuente_codigo` y `fuente_interfaz` conservan nombre y firma y la aplican.
- `aplicar_tema`: `Treeview` (fondo `panel`, `rowheight` 28, sin borde, selección `seleccion_fila` con texto `blanco`); `Treeview.Heading` plana, fondo `panel`, texto `texto_secundario`, sin negrita; barras de desplazamiento finas, sin flechas, pulgar `deslizador` (con `try/except tk.TclError` y el aspecto actual como respaldo); divisores de `Panedwindow` en `fondo`; estilos de la barra de estado sobre `panel` con texto `texto_secundario`; `Enlace.TLabel` (`acento_claro`; deshabilitado `texto_tenue`); `Cabecera.TLabel` (título de *tool window*). Se eliminan `Accion.TButton`, `Estado.TButton` y los estilos `TNotebook` cuando dejen de usarse (B13–B14).
- En esta tarea la ventana sigue con la disposición antigua, ya con los colores nuevos.
- **Aceptación:** `set(TEMA) ⊇` las 24 claves; todos los valores de `TEMA` y `COLORES_TOKEN` cumplen `^#[0-9A-Fa-f]{6}$`; `set(COLORES_TOKEN) == set(TipoToken)` (prueba nueva en `tests/test_ui_rediseno.py`, no necesita Tk); batería en verde; regla 2 de la fase.

### B12 — Iconos y piezas base (`ui/iconos.py` nuevo, `ui/componentes.py`) — **estado: hecha (Fase C, developer-sonnet)**
- `ui/iconos.py` según §16.5: `TRAZOS` (los 16 iconos de la tabla), `RECTANGULOS` (`carpeta`, `archivo`), `dibujar(lienzo, nombre, x, y, color)`, `imagen(nombre)`. Solo importa `tkinter` y `ui.estilos`. Dibujos simples: horizontales, verticales y las diagonales imprescindibles.
- En `ui/componentes.py`: `BotonIcono`, `Globo`, `PanelHerramientas`, `FranjaHerramientas` con la interfaz de §16.6. `BotonIcono` deshabilitado no llama a `command` ni cambia al pasar el ratón; con `relleno` deshabilitado se dibuja sin relleno y en `texto_tenue`.
- **Aceptación** (pruebas nuevas, con Tk): cada nombre de `TRAZOS` se dibuja en un `Canvas` sin excepción y crea al menos un elemento; `imagen("carpeta")` mide 16×16; un `BotonIcono` deshabilitado no ejecuta su `command` al simular el clic y uno habilitado sí; `PanelHerramientas.mostrar(nombre)` cambia `vista_actual` y el título de la cabecera; `FranjaHerramientas.poner_contador("x", 3)` no lanza. Cada clase nueva ≤ ~45 líneas.

### B13 — Barra superior y barra de estado (`ui/componentes.py`, `ui/interfaz.py`) — **estado: hecha (Fase C, developer-sonnet)**
- `BarraHerramientas` rehecha según §16.2 (zona A) y §16.6: tabla `_ACCIONES`; logo; *widget* «SmartLex Studio ▾» con su menú (Abrir, Guardar, Limpiar, Ayuda, Salir, cada uno con su atajo a la derecha); *widget* «FlowLang · Análisis léxico ▾» (texto armado con `reglas.NOMBRE_LENGUAJE`) con su menú (Analizar, Paso a paso, Detener); botones `analizar` (relleno `exito`), `paso` (icono `exito`), `detener` (relleno `detener`); a la derecha `abrir`, `guardar`, `limpiar`, `ayuda` en `texto_secundario`. Cada botón con su `Globo` «Texto (atajo)». Los menús copian el estado habilitado de los botones al abrirse.
- `botones` conserva las siete claves y `habilitar(nombres)` su firma. `VentanaPrincipal` solo añade la acción «Salir» (`self.destroy`).
- `BarraEstado` según zona H: `establecer_ruta(partes: list[str])` (migas unidas con ` › `, la última en `texto`), estado, contadores, posición `Lín:Col`, `LF`, `UTF-8`, lenguaje y versión, y «Ver tabla de símbolos» como enlace (`habilitar_ver_tabla` conserva la firma). Fondo `panel`.
- `VentanaPrincipal` calcula las migas en un único método privado (ruta relativa a `RAIZ_PROYECTO` precedida de su nombre; si el archivo está fuera, `carpeta › archivo`; sin archivo, solo el nombre del proyecto) y lo llama donde hoy llama a `_poner_titulo`.
- **Aceptación:** tras `abrir_archivo("ejemplos/correcto.flow")` la barra de estado contiene `SmartLexStudio › ejemplos › correcto.flow` y `1:1`; tras `limpiar()` solo `SmartLexStudio`; en cada estado, el conjunto de botones habilitados coincide con `_BOTONES_POR_ESTADO` (prueba nueva que recorre los cuatro estados); el menú de ejecución tiene «Detener» deshabilitado en `LISTO`; `F5`, `F10`, `Esc`, `F1`, `Ctrl+O`, `Ctrl+S` siguen funcionando.

### B14 — *Tool windows*: franjas, paneles y disposición (`ui/componentes.py`, `ui/paneles.py`, `ui/interfaz.py`) — **estado: hecha (Fase C, developer-sonnet)**
- `PanelLateral(PanelHerramientas)` con dos vistas: `proyecto` (árbol `SmartLexStudio › ejemplos › *.flow` desde `listar_ejemplos()`, iconos de `iconos.imagen`, nodos abiertos; doble clic en un archivo llama a `al_elegir_ejemplo`; `marcar_abierto(ruta | None)` selecciona el archivo abierto y, si está fuera de `ejemplos/`, lo añade bajo la raíz) y `lenguaje` (el árbol y la descripción actuales, **sin cambiar** `_construir_arbol`).
- `PanelResultados(PanelHerramientas)` con cuatro vistas (`tokens`, `simbolos`, `estadisticas`, `educativo`) en lugar del `ttk.Notebook`; `habilitar_tabla_simbolos` / `tabla_simbolos_habilitada` pasan a ser un indicador booleano. Se elimina `seleccionar_pestana`.
- Clase nueva `PanelProblemas(ttk.Frame)` en `ui/paneles.py`: recibe **movido, no reescrito**, lo de errores (`arbol_errores`, `detalle_error`, `_errores`, `agregar_error`, `quitar_errores_de_archivo`, doble clic → *callback*, `limpiar`). Con el ancho completo, las columnas Mensaje y Sugerencia se reparten el espacio sobrante.
- `PanelConsola` sin su etiqueta de título. Zona inferior: un `PanelHerramientas` con `consola` y `problemas`.
- `VentanaPrincipal._construir` con la disposición de §16.2; atributos `self.problemas`, `self.franja_izquierda`, `self.franja_derecha`; tabla `_HERRAMIENTAS` y métodos `mostrar_herramienta(nombre)` y `alternar_herramienta(nombre)` de §16.7 (ocultar y mostrar zonas guardando su tamaño). Las cuatro llamadas actuales a `seleccionar_pestana` pasan a `mostrar_herramienta`; `agregar_error`, `quitar_errores_de_archivo` y el *callback* de selección de error pasan a `self.problemas`; `_reiniciar_resultados` limpia también `self.problemas`; el icono `simbolos` se habilita y deshabilita junto con `habilitar_tabla_simbolos`; el icono `problemas` recibe el contador en `_consumir_paso` y en `_reiniciar_resultados`.
- Actualizar en la misma tarea los nombres en `tests/test_ui_humo.py` y `tests/test_auditoria_fase_b.py` (tabla de B16) para que la batería siga en verde.
- **Aceptación** (pruebas nuevas): `alternar_herramienta("proyecto")` dos veces oculta y vuelve a mostrar la zona izquierda con ancho ≥ 150 px; lo mismo con una herramienta de cada zona; `alternar_herramienta("lenguaje")` con Proyecto visible cambia de vista sin ocultar; durante un análisis de `incorrecto.flow` detenido a la mitad, `problemas` es la vista visible de la zona inferior, tiene ≥ 1 fila y el contador del icono es > 0 (**requisito 5, errores durante la evaluación**); antes de terminar, el icono `simbolos` está deshabilitado y `ver_tabla_simbolos()` no cambia la vista; al terminar se habilita y `ver_tabla_simbolos()` deja `simbolos` como vista actual (**requisito 5, alternativa final**); `paso_a_paso()` deja `educativo` visible; el árbol de Proyecto tiene una fila por cada archivo de `listar_ejemplos()` y la del archivo abierto está seleccionada; `PanelLateral` conserva las referencias de sus imágenes.

### B15 — Editor: pestaña, margen e inspección (`ui/editor.py`, `ui/interfaz.py`) — **estado: hecha (Fase C, developer-sonnet)**
- Según §16.8: fila de pestaña única (`establecer_nombre`, *callback* `al_cerrar` conectado a `VentanaPrincipal.limpiar`); margen con `numero_linea` sobre `fondo` y línea divisoria; etiquetas de token con `COLORES_TOKEN` y cursiva para `TIPOS_EN_CURSIVA`; texto del editor en `texto_codigo`; *widget* de inspección con `ir_a_error(direccion)` e `indicar_sin_errores()`; atajos `F2` / `Shift+F2` registrados en `VentanaPrincipal` y añadidos al texto de ayuda.
- `VentanaPrincipal._finalizar` llama a `indicar_sin_errores()` si no hubo diagnósticos; el nombre de la pestaña se actualiza donde las migas.
- No se tocan `establecer_texto`, `obtener_texto`, `_al_modificar`, `_notificar_cambio`, `descartar_cambio_pendiente`, `resaltar_token_actual` ni el desplazamiento diferido.
- **Aceptación** (pruebas nuevas): tras analizar `incorrecto.flow`, el *widget* muestra `✗` y la cantidad de marcas con posición; con el cursor en 1:1, `ir_a_error(+1)` lo lleva a `2:12` (primer error), otra vez a `2:18`, y `ir_a_error(-1)` desde 1:1 lo lleva al último error (da la vuelta); tras analizar `correcto.flow` muestra `✓`; tras `limpiar()` o editar el texto, está oculto; la etiqueta del tipo `COMENTARIO` usa una fuente en cursiva; la pestaña muestra `correcto.flow` y, tras `limpiar()`, `sin título`. `test_aud16`, `test_aud17`, `test_aud19` y `test_editor_tags_y_normalizacion` pasan sin tocarlos.

### B16 — Pruebas, capturas y documentación — **estado: hecha (Fase C, developer-sonnet)**
- **Renombres permitidos en las pruebas existentes** (nada más):

| Antes | Después |
|---|---|
| `v.panel_resultados.arbol_errores` | `v.problemas.arbol_errores` |
| `pr._errores`, `pr.detalle_error` (errores) | `v.problemas._errores`, `v.problemas.detalle_error` |
| `pr.limpiar()` en `test_aud20` | `v.problemas.limpiar()` |

- **AUD-18** (los botones no heredan el ancho mínimo del tema `clam`): la prueba pasa a comprobar que cada botón de `v.barra.botones` mide lo que su icono (`winfo_reqwidth() <= 40`) y que los siete tienen el mismo ancho; se conserva el nombre `test_aud18_botones_con_ancho_natural` y su *docstring* explica el cambio.
- `tests/test_ui_rediseno.py` reúne las pruebas nuevas de B11–B15, con el mismo patrón que `test_ui_humo.py` (detección de Tk en subproceso, D-38; `messagebox` y `filedialog` simulados). Total esperado: las 118 actuales más las nuevas, todas en verde con **python3.14 (Tk 9.0)** y con **python3.11 o 3.12 (Tk 8.6)** si están instalados; anotar ambas salidas `Ran N tests` · `OK` en `docs/06_auditoria.md` (sección nueva «Rediseño visual, Fase C»). `tests/test_auditoria_fase_b.py` completo en verde: AUD-16…AUD-21 y AUD-28 siguen vigentes.
- Comprobaciones por `grep`, vacías ambas: la de colores (regla 2) y `grep -rn "Notebook\|seleccionar_pestana" ui/ tests/ docs/capturas/capturar.py`.
- **Capturas reales**: actualizar `docs/capturas/capturar.py` (`mostrar_herramienta`, `v.problemas`) y regenerar, **con los mismos nombres de archivo**, `1_correcto_tokens`, `2_tabla_simbolos`, `3_estadisticas`, `4_modo_educativo`, `5_incorrecto_errores` (esta con Problemas abierto y un error seleccionado), más `6_paneles_ocultos` (zonas izquierda e inferior ocultas). Abrir cada captura y la referencia con la herramienta de lectura de imágenes y recorrer los **10 puntos de la lista de §16.10**; registrar en `docs/06_auditoria.md` una tabla punto → cumple / no cumple / diferencia aceptada (las de §16.1). Si un punto no se cumple, se corrige y se repite la captura; no se declara una verificación visual que no se hizo (D-40). Si `screencapture` no tiene permiso, decirlo y dejar la verificación como pendiente manual.
- **Verificaciones manuales** a registrar en `docs/06_auditoria.md`: M1–M3 repetidas con el diseño nuevo; **M5** (Windows o Linux del laboratorio: tamaño del texto, iconos legibles, menús, globos) queda como pendiente con sus pasos si no hay equipo.
- **Documentación**:
  - `docs/04_manual_usuario.md`: recorrido de la ventana nueva (barra superior y sus dos menús, franjas, mostrar y ocultar herramientas, Proyecto y Lenguaje, pestaña, inspección `✗ N ⌃ ⌄` con `F2` / `Shift+F2`, Problemas, barra de estado); sustituir toda mención a «pestaña Errores / Tokens…» por la herramienta correspondiente; capturas nuevas.
  - `docs/05_guia_sustentacion.md`, **Ejercicio 7** y el «Cambio 4» del ejercicio de nuevo tipo de token: los valores «antes» pasan a los de §16.3 (`TipoToken.PALABRA_RESERVADA: "#CF8E6D"`, `"fondo": "#1E1F22"`, `TipoToken.CADENA: "#6AAB73"`); repetir el ejercicio 7 en una copia y confirmar el resultado. Añadir una pregunta probable: «¿Cómo están hechos los iconos?» (respuesta: §16.5) y otra: «¿Dónde se ven los errores durante la evaluación?» (§16.7). Revisar cualquier otra mención a pestañas o a nombres de paneles.
  - `README.md`: descripción de la interfaz, captura principal y árbol de archivos (`ui/iconos.py`).
  - `docs/02_arquitectura.md`: quitar la nota de «pendiente de implementar» de §16, actualizar el diagrama de §10.1 y la tabla de §10.2 para que remitan a §16, y añadir a §15 las diferencias entre §16 y lo implementado (con su decisión).
  - `docs/matriz_requisitos.md`: evidencia de los requisitos 5 y 6 con los nombres nuevos.
  - `agents/tareas.md`: fila de la Fase C en el registro de ejecución.

## Criterio de aprobación de la Fase C (arquitecto)

**Aprobada si:** batería completa en verde en Tk 9.0 (y en Tk 8.6 si está disponible); los dos `grep` de B16 vacíos; `git diff --stat` respecto a `3a12ba2` no muestra cambios en `core/`, `application/`, `config/` ni `main.py`; las seis capturas existen y la tabla de los 10 puntos está registrada; las pruebas de los requisitos 5 y 6 no se han relajado; el manual, la guía (ejercicio 7 repetido) y el README describen la ventana nueva; ninguna clase nueva supera lo que un estudiante puede explicar en dos minutos.

---

# FASE D — Rediseño claro estilo académico (solo `ui/`)

**Leer antes de empezar:** `docs/02_arquitectura.md` **§17** completo (es la especificación; estas tareas solo la reparten) y las decisiones D-61…D-72. Referencia visual del usuario (otra aplicación, «DronLang»; se imita estilo y disposición, **no** nombres, códigos ni datos; no se copia al repositorio): `/private/tmp/claude-501/-Volumes-Ojito-proyecto-de-lenguajes/001cc0b7-bd4c-4a80-909f-4edbc49746a8/images/3.png`. Punto de partida: `d952707`.

Reglas de la fase (además de las generales):

1. **Solo se modifican** `ui/`, `tests/test_ui_humo.py`, `tests/test_auditoria_fase_b.py`, `tests/test_ui_rediseno.py`, `docs/capturas/` y los documentos de C8. `core/`, `application/`, `config/` y `main.py` no se tocan; si parece necesario, parar y anotarlo en `agents/revisiones.md`.
2. **`config/reglas.py` tiene un cambio local del usuario y `ejemplos/practica.flow` es un archivo suyo sin seguimiento: no se editan, no se restauran, no se borran y no entran en ningún *commit*.** `git add` siempre con rutas explícitas (nunca `-A` ni `.`). Por ellos fallan `test_conteos_de_flowlang_1_0` y `test_listar_ejemplos`: son las **dos únicas** fallas admitidas (D-72).
3. Colores: ningún literal `#rrggbb` fuera de `ui/estilos.py`. Comprobación vacía: `grep -nE "#[0-9a-fA-F]{6}" ui/*.py | grep -v "^ui/estilos.py"`.
4. No queda nada de PyCharm. Comprobación vacía: `grep -rnE "iconos|BotonIcono|Globo|FranjaHerramientas|PanelHerramientas|PanelLateral|PanelProblemas|alternar_herramienta|mostrar_herramienta|_migas|PyCharm|Darcula" ui/ tests/ docs/capturas/capturar.py`.
5. Se conservan sin cambio de comportamiento: los cuatro estados y `_BOTONES_POR_ESTADO`, `destroy()` (AUD-28), `_al_editar`, `descartar_cambio_pendiente` (AUD-16), los desplazamientos diferidos (AUD-17, AUD-19), `quitar_errores_de_archivo` (D-42), la solicitud inicial del archivo (requisito 6), el `askyesno` final (requisito 5b), `nuevo_archivo` (B17) y el modo consola.
6. C1 se entrega sola con la batería en su estado admitido. **C2–C5 forman un bloque** (la ventana no arranca a medias): la batería completa se exige al cerrar C6. Batería: `/opt/homebrew/bin/python3.14 -m unittest discover -s tests -t . -v`; arranque: `/opt/homebrew/bin/python3.14 main.py` sin trazas en la terminal.
7. Si algo de §17 no se puede hacer en Tk tal como está escrito, aplicar la variante más simple que conserve el aspecto y registrarla en `agents/decisiones.md` (D-73 en adelante) como «pendiente de revisión del arquitecto».

### C1 — Paleta clara y estilos `ttk` (`ui/estilos.py`) — **estado: hecha (Fase D, developer-sonnet)**

- `TEMA` con las 25 claves y valores de §17.3; `COLORES_TOKEN` con los valores de §17.3 para **todos** los `TipoToken`; `TIPOS_EN_NEGRITA = (TipoToken.PALABRA_RESERVADA,)`.
- `aplicar_tema`: estilos de §17.3 (Treeview claro con cabecera con borde, `TNotebook`, `Primario.TButton`, `Secundario.TButton`, `Cabecera.TMenubutton`, `Cabecera.Horizontal.TScale`, `Titulo.TLabel`, `TituloError.TLabel`, `Estado.*`, `Veredicto.TLabel`, `TCombobox`). Botones con `width=0`. Se mantienen `_puntos`, `fuente_codigo`, `fuente_interfaz`, `_estilos_barras`.
- **Aceptación:** `set(TEMA)` es exactamente el conjunto de §17.3 y cada valor cumple `^#[0-9A-F]{6}$`; `COLORES_TOKEN` cubre `set(TipoToken)`; `aplicar_tema(tk.Tk())` no lanza excepción; los textos del docstring y comentarios ya no dicen PyCharm.

### C2 — Cabecera, barra de estado y vista Lenguaje (`ui/componentes.py`; se borra `ui/iconos.py`) — **estado: hecha (Fase D, developer-sonnet)**

- `Cabecera(padre, acciones: dict[str, Callable], al_elegir_ejemplo: Callable[[Path], None], al_ver_tabla: Callable)` según §17.2: dos filas, `botones` (ocho claves), `habilitar(nombres)`, `habilitar_ver_tabla(activo)`, `pausa_ms()`, `establecer_pausa(ms)`, menú «Ejemplos ▾» rellenado en `postcommand` con `listar_ejemplos()`.
- `BarraEstado` con la API de §17.2 (`establecer_contadores` de cinco valores, `establecer_estado`, `establecer_posicion`, `establecer_veredicto`).
- `VistaLenguaje(padre)`: el árbol de referencia de FlowLang del antiguo `PanelLateral`, sin el árbol *Proyecto* ni imágenes.
- `PanelConsola` no cambia. Se eliminan `BotonIcono`, `Globo`, `PanelHerramientas`, `FranjaHerramientas`, `_Desplegable`, `BarraHerramientas`, `PanelLateral` y `ui/iconos.py`. `RAIZ_PROYECTO` se queda.
- **Aceptación** (pruebas de C6): con una ventana de 1100 px, `cabecera.winfo_reqwidth() <= 1100`; `pausa_ms()` vale 120 al arrancar y `establecer_pausa(0)` lo deja en 0 y la etiqueta en «0 ms»; el menú Ejemplos tiene una entrada por cada archivo de `listar_ejemplos()` y un archivo creado después aparece al volver a abrirlo; `establecer_veredicto(True/False/None)` produce los textos de §17.2 con «FlowLang» tomado de `reglas.NOMBRE_LENGUAJE`.

### C3 — Editor con columna ✓/✗ (`ui/editor.py`) — **estado: hecha (Fase D, developer-sonnet)**

- Todo §17.4: título «Archivo de entrada: …», margen `número + marca`, `marcar_lineas_evaluadas`, `linea_error`, fondo `error_lexema` en el lexema, ✗ para cualquier diagnóstico con posición, `conteo_lineas()`, negrita de reservadas, sin *widget* de inspección ni `al_cerrar`.
- No se tocan `establecer_texto`, `obtener_texto`, `_al_modificar`, `_notificar_cambio`, `descartar_cambio_pendiente`, `resaltar_token_actual`, `ir_a`, `ir_a_error`.
- **Aceptación** (pruebas de C6): tras `marcar_lineas_evaluadas([1, 2, 3])` y un diagnóstico en la línea 2, el margen contiene `1 ✓`, `2 ✗`, `3 ✓`, la línea 4 no tiene marca y `conteo_lineas() == (2, 1)`; `texto.tag_ranges("linea_error")` cubre `2.0`–`3.0`; `tag_ranges("marca_error")` sigue dando `2.11`–`2.14` para el primer error de `incorrecto.flow`; `limpiar_marcas()` deja el margen sin ✓ ni ✗ y `conteo_lineas() == (0, 0)`; un diagnóstico estructural (`SIN-`) con línea también pone ✗.

### C4 — Manejador de errores y pestañas (`ui/paneles.py`) — **estado: hecha (Fase D, developer-sonnet)**

- `PanelErrores` según §17.5 (título con el número de errores, cinco columnas, `detalle_titulo` + `detalle_error`).
- `PanelResultados` según §17.6: `cuaderno` con las seis vistas en orden, `mostrar(nombre)`, `vista_actual`, pestaña de símbolos deshabilitada hasta `habilitar_tabla_simbolos(True)`, línea de resumen con la fórmula real, pestaña Autómatas con `selector_automata` y `mostrar_automata(nombre)`, `VistaLenguaje` y `PanelConsola` como pestañas (`self.consola`).
- **Aceptación** (pruebas de C6): con `incorrecto.flow` terminado el título es «Manejador de errores (15 errores)» y con `correcto.flow` «Manejador de errores (sin errores)»; las columnas de `arbol_errores` son `("codigo", "linea", "col", "lexema", "error")` y la primera fila empieza por un código `LEX-`; los títulos de las pestañas son, en orden, Tokens, Tabla de símbolos, Resumen, Autómatas, Lenguaje, Consola; antes de terminar `cuaderno.tab(1, "state") == "disabled"` y después `"normal"`; con `correcto.flow` el resumen contiene `h = (h · 31 + código(c)) mod 2³²`, `cubeta = h mod capacidad`, `Colisiones al insertar: 14` y `En la tabla actual: 7`, y hay filas con la etiqueta `colision`; `selector_automata` ofrece los cuatro nombres de `reglas.AUTOMATAS`, y al elegir cada uno el texto contiene «Tabla de transiciones de» + ese nombre; al seleccionar un token identificador, el selector pasa al AFD que lo reconoció.

### C5 — Ventana, pausa por línea y cambios sin guardar (`ui/interfaz.py`) — **estado: hecha (Fase D, developer-sonnet)**

- Disposición de §17.2 (cabecera, `cuerpo`/`superior`, `panel_errores`, `panel_resultados`, barra de estado), `minsize` 1100×650, título de ventana como hoy.
- Evaluación progresiva de §17.7 (constantes, `_linea_en_curso`, `_tick`, `_pausa_efectiva`, `_consumir_paso`, `_finalizar` con veredicto en la barra de estado). `ver_tabla_simbolos()` → `panel_resultados.mostrar("simbolos")` si está habilitada.
- §17.8 completo: `_confirmar_descartar`, `salir()` + `WM_DELETE_WINDOW`, `<Control-o>` en el `Text` del editor, cursor de *Nuevo* calculado. El parche `…/scratchpad/opus_parcial.patch` sirve de referencia para estas tres piezas, **no se aplica con `git apply`** (está hecho sobre la ventana PyCharm).
- Se eliminan franjas, zonas ocultables, `_migas` y los menús; `_mostrar_error_archivo` deja de llamar a `mostrar_herramienta`.
- **Aceptación** (pruebas de C6, además de las existentes de los requisitos 5 y 6):
  - *Pausa por línea*: con `incorrecto.flow`, pausa 0 y avanzando con `paso_a_paso()` hasta el primer token de la línea 3, el margen muestra `1 ✓` y `2 ✗` y la línea 3 aún no tiene marca; con el temporizador simulado (`after` capturado), cada llamada a `_tick` deja `_linea_en_curso` exactamente una línea con tokens más adelante y programa el siguiente `after` con `_pausa_efectiva()`; `_pausa_efectiva()` vale 120 con un archivo de 10 líneas y 10 con uno de 1 000.
  - *Requisito 5a*: durante el análisis (sesión no terminada) `panel_errores.arbol_errores` ya tiene filas y el editor ya tiene `marca_error`.
  - *Requisito 5b*: al terminar se llama una vez a `askyesno` con «tabla de símbolos»; si devuelve `True`, `panel_resultados.vista_actual == "simbolos"`.
  - *Barra de estado*: al terminar `incorrecto.flow` el texto de contadores contiene `Tokens: 57`, `Símbolos: 18`, `Errores: 15` y los dos contadores de líneas coinciden con `editor.conteo_lineas()`; el veredicto es «✗ El archivo NO es válido para FlowLang» y con `correcto.flow` «✓ El archivo es válido para FlowLang»; al editar el texto o limpiar, el veredicto se borra.
  - *AUD-29*: con cambios sin guardar, *Abrir* con ruta, el menú Ejemplos, *Limpiar* y `salir()` llaman a `askyesnocancel`; con *Cancelar* (`None`) el texto y `ruta_actual` no cambian, `askopenfilename` **no** se llama y la ventana sigue existiendo; con *No* se descarta; con *Sí* se guarda antes (y si el guardado se cancela, no se continúa). Sin cambios, ninguno pregunta. La solicitud inicial (requisito 6) no pregunta.
  - *AUD-31*: `editor.texto.event_generate("<Control-o>")` con el foco en el editor no cambia `obtener_texto()` y llama a `askopenfilename` exactamente una vez.
  - *Paso a paso* selecciona la pestaña Autómatas; *Analizar* selecciona Tokens.

### C6 — Pruebas — **estado: hecha (Fase D, developer-sonnet)**

- Adaptar `tests/test_ui_humo.py` y `tests/test_auditoria_fase_b.py` con la tabla de §17.10 (solo renombres, `askyesnocancel.return_value = False`, pausa 0, textos del resumen y AUD-18/AUD-20 reformuladas). **Ninguna otra aserción cambia.**
- Reescribir `tests/test_ui_rediseno.py`: se eliminan las pruebas de piezas que ya no existen (lista en §17.10) y se añaden las de aceptación de C1–C5. Las pruebas de B17 se conservan adaptadas.
- **Aceptación:** batería completa con solo las dos fallas de D-72, en tres corridas seguidas (sin pruebas intermitentes); ninguna traza `invalid command name` en la salida; los dos `grep` de las reglas 3 y 4 vacíos; `git diff --stat d952707 -- SmartLexStudio/core SmartLexStudio/application SmartLexStudio/main.py` vacío y `git status --short` muestra `config/reglas.py` y `ejemplos/practica.flow` exactamente como al empezar.

### C7 — Capturas reales y comparación con la referencia (`docs/capturas/`) — **estado: hecha (Fase D, developer-sonnet)**

- Actualizar `docs/capturas/capturar.py` (API nueva; pausa 0 salvo en la captura «durante»; ventana 1440×880) y regenerar con la aplicación real (método de D-58): `1_correcto_tokens.png`, `2_tabla_simbolos.png`, `3_resumen.png`, `4_automatas.png`, `5_incorrecto_errores.png` (error seleccionado, detalle visible, pestaña Tabla de símbolos abajo: es la equivalente a la referencia) y `6_durante_evaluacion.png` (análisis detenido a mitad: líneas de arriba con ✓/✗, las de abajo sin marca, errores ya listados). Borrar `3_estadisticas.png`, `4_modo_educativo.png` y `6_paneles_ocultos.png`.
- **Aceptación:** abrir cada PNG con la herramienta de lectura de imágenes y comprobar que muestra la ventana de SmartLex Studio completa (no otra aplicación, no recortada, texto legible, ✓ y ✗ con glifo). Comparar `5_incorrecto_errores.png` con la referencia y dejar en `docs/06_auditoria.md` una tabla «elemento de la referencia → presente / diferencia aceptada (§17.1) / defecto» con estas filas como mínimo: cabecera azul marino con nombre y subtítulo; botón primario azul; deslizador con valor en ms; «Ver tabla de símbolos» a la derecha; título del archivo; números + ✓/✗; línea con error en rosado; lexema subrayado en rojo; resaltado sobrio (reservadas azul negrita, comentarios gris cursiva); título rojo del manejador con el número; tabla de cinco columnas; cuadro de detalle; pestañas; línea de resumen del hash; filas de colisión en amarillo; barra de estado con contadores; veredicto en rojo/verde. Ningún «defecto» puede quedar abierto.

### C8 — Documentación — **estado: hecha (Fase D, developer-sonnet)**

- `docs/04_manual_usuario.md`: recorrido de la ventana nueva (cabecera y cada botón con su atajo, menú Ejemplos, pausa por línea y su tope en archivos largos, columna ✓/✗, manejador de errores y detalle, seis pestañas, barra de estado y veredicto, confirmación de cambios sin guardar), con las capturas nuevas.
- `docs/05_guia_sustentacion.md`: **Ejercicio 7** (cambiar un color o el tema) y el «Cambio 4» del ejercicio de nuevo tipo de token con los valores «antes» de §17.3; donde diga «Modo educativo», «Problemas», «tool window» o «franja», usar «Autómatas», «Manejador de errores» y las pestañas; añadir a la demostración la pausa por línea como evidencia del requisito 5.
- `README.md`: descripción de la interfaz, captura principal (`5_incorrecto_errores.png`) y árbol de archivos (sin `ui/iconos.py`).
- `docs/matriz_requisitos.md`: evidencia de R3, R4, R5a, R5b y R6 con los nombres nuevos (`panel_errores`, pausa por línea, pestaña y botón «Ver tabla de símbolos», `_confirmar_descartar`) y número real de pruebas; M1–M3 redactadas con la ventana nueva.
- `docs/02_arquitectura.md`: quitar «pendiente de implementar» de §17; §10.1 y §10.2 remiten a §17; añadir a §15 las diferencias entre §17 y lo implementado.
- `docs/06_auditoria.md`: cerrar AUD-29…AUD-32 (AUD-30 «no aplica: las zonas ya no se ocultan»), la tabla de C7 y M1–M3 repetidas; M5 y Tk 8.6 siguen pendientes si no se pueden probar (no declarar lo que no se hizo).
- `agents/tareas.md`: fila de la Fase D en el registro de ejecución.
- **Aceptación:** `grep -rnE "PyCharm|tool window|franja|Modo educativo|iconos\.py|3_estadisticas|4_modo_educativo|6_paneles_ocultos" README.md docs/04_manual_usuario.md docs/05_guia_sustentacion.md docs/matriz_requisitos.md` vacío; todas las imágenes enlazadas existen; los valores de color citados en la guía coinciden con `ui/estilos.py`.

## Criterio de aprobación de la Fase D (arquitecto)

**Aprobada si:** batería con solo las dos fallas de D-72 en Tk 9.0; los `grep` de las reglas 3 y 4 y el de C8 vacíos; `core/`, `application/`, `main.py` sin cambios y `config/reglas.py` / `ejemplos/practica.flow` intactos y fuera de los *commits*; las seis capturas son reales y la tabla de comparación de C7 no tiene defectos abiertos; los requisitos 5a, 5b y 6, paso a paso, detener, nuevo archivo y el modo consola tienen prueba en verde; AUD-29, AUD-31 y AUD-32 cerrados con prueba.
