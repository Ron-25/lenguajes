# 05 · Guía de sustentación — SmartLex Studio

Para los estudiantes que van a presentar y defender el proyecto. Todo nombre de archivo, función o constante que aparece aquí existe en el código (commit `3a8f372`, 115 pruebas en verde). Los 10 ejercicios de modificación se ensayaron uno por uno en copias temporales del proyecto; el resultado que se indica en cada uno es el que realmente se obtuvo.

**Comandos** (ejecutar siempre dentro de la carpeta `SmartLexStudio/`; donde dice `python` use el intérprete con tkinter, en este equipo `/opt/homebrew/bin/python3.14`):

```
python main.py                                        # interfaz gráfica
python main.py --consola ejemplos/correcto.flow       # modo texto, sin tkinter
python -m unittest discover -s tests -t .             # toda la batería (≈ 20 s)
python -m unittest tests.test_afd -v                  # un archivo de pruebas
```

**Antes de la sustentación:** `git status` debe estar limpio. Después de cada modificación en vivo, vuelva al estado original con `git checkout -- .` (deshace todos los cambios no confirmados).

---

## Parte 1 · Conceptos, explicados con este proyecto

### 1.1 Qué es SmartLex Studio
Una aplicación de escritorio en Python (solo biblioteca estándar) que recibe un archivo con un programa escrito en **FlowLang** y hace tres cosas, que son los tres temas del proyecto:

1. **Analizador léxico:** parte el texto en *tokens* y decide si la cadena de entrada es válida.
2. **Tabla de símbolos:** instala los tokens en una tabla **hash** propia.
3. **Manejador de errores:** detecta, clasifica y explica cada error, y lo muestra **mientras** avanza la evaluación.

### 1.2 Qué es FlowLang
Un lenguaje inventado para el proyecto que describe automatizaciones (riego, luces): 17 palabras reservadas, identificadores, enteros, decimales, cadenas con escapes, 15 operadores, 6 delimitadores y 2 tipos de comentario. Su definición completa está en `docs/03_especificacion.md` y, como **datos**, en `config/reglas.py`.

### 1.3 Lexema, token y categoría
- **Lexema:** el trozo de texto tal como está escrito: `temperatura`, `>=`, `45.5`.
- **Token:** el lexema ya clasificado, con su posición. En el código es la clase `Token` de `core/modelos.py`: `tipo`, `lexema`, `linea`, `columna`.
- **Categoría:** el `tipo`; uno de los 12 miembros de `TipoToken` (palabra reservada, identificador, entero, decimal, cadena, tres clases de operador, asignación, delimitador, comentario, error).

`numero x = 10;` produce 5 tokens: (Palabra reservada, `numero`, 1:1), (Identificador, `x`, 1:8), (Asignación, `=`, 1:10), (Entero, `10`, 1:12), (Delimitador, `;`, 1:14).

### 1.4 Qué hace el analizador léxico (y qué no)
Lee carácter por carácter, agrupa en lexemas y los clasifica. **No** comprueba el orden de los tokens (eso es sintaxis) ni su significado (semántica). `numero x = "hola";` es léxicamente válido.

La única comprobación que va más allá está aparte, en `core/validador.py`, y se declara **estructural**: el programa empieza con `inicio`, termina con `fin`, y los `( )` y `{ }` están balanceados.

**Cadena válida** = 0 errores léxicos (`LEX-…`) **y** 0 errores estructurales (`SIN-…`). La aplicación muestra los dos veredictos por separado y, además, qué líneas son léxicamente inválidas.

### 1.5 Autómatas y expresiones regulares que se usan
El lexer **no usa el módulo `re`**. Usa cuatro **AFD** escritos como tablas de transición en `config/reglas.py`, ejecutados por un motor genérico (`core/afd.py`, clase `AFD`):

| AFD | Constante | Expresión regular equivalente |
|---|---|---|
| Identificadores | `AFD_IDENTIFICADOR` | `[A-Za-z_][A-Za-z0-9_]*` |
| Números | `AFD_NUMERO` | entero `[0-9]+`, decimal `[0-9]+\.[0-9]+` |
| Cadenas | `AFD_CADENA` | `"(?:[^"\\\n]\|\\[nt"\\])*"` |
| Comentarios | `AFD_COMENTARIO` | `//[^\n]*\|/\*(?:[^*]\|\*+[^*/])*\*+/` |

Cómo leer una tabla (ejemplo real):

```python
AFD_IDENTIFICADOR = {
    "inicial": "q0",
    "transiciones": {
        "q0": {LETRA: "q1", "_": "q1"},                 # desde q0, con letra o _ se pasa a q1
        "q1": {LETRA: "q1", DIGITO: "q1", "_": "q1"},   # en q1 se queda con letra, dígito o _
    },
    "aceptacion": {"q1": TipoToken.IDENTIFICADOR},      # q1 es estado final
    "errores": {},
}
```

El motor (`AFD.reconocer`) repite `estado = siguiente_estado(estado, carácter)` y **recuerda el último estado final** por el que pasó: devuelve el prefijo más largo reconocido. `x1 = 5` → recorrido `q0 → q1 → q1`, se detiene en el espacio y devuelve longitud 2.

Tres ideas que hay que saber decir:

- **Coincidencia más larga (maximal munch).** En cada posición se ejecutan los 4 AFD y se consulta la tabla de operadores (primero 2 caracteres, luego 1); gana el candidato **más largo** (`reconocer_lexema` en `core/lexer.py`). Por eso `>=` es un token y no `>` seguido de `=`, y `// nota` es un comentario y no una división.
- **Palabras reservadas.** Se reconocen como identificadores y después se consulta `PALABRAS_RESERVADAS`. Por eso `si2` es un identificador y agregar una palabra es una línea.
- **Estados finales de error.** Los AFD de número, cadena y comentario tienen estados finales que no producen un token sino un **código de error** (clave `"errores"`). Así `3.4.5` se consume entero y da un solo error, en vez de partirse en trozos.

**Lo que es honesto afirmar:** los AFD equivalen a sus regex *según las pruebas* (`tests/test_afd.py` compara todas las cadenas de hasta 5 símbolos de un alfabeto de prueba); no es una demostración formal. Los operadores se resuelven con un diccionario, no con una tabla de estados. Los AFD de número y cadena **no son mínimos** (tienen estados de error añadidos; la especificación muestra también el mínimo). El balance de paréntesis usa una **pila** porque ese lenguaje no es regular.

### 1.6 Tabla de símbolos y hashing
Guarda una entrada por lexema distinto (reservadas, identificadores y literales) con lo que otras fases del compilador necesitarían: categoría, tipo de dato, valor, línea de declaración, todas las apariciones, valor hash y cubeta. Está en `core/simbolos.py` y **no usa `dict`**: es una lista de listas.

**Función hash** (`hash_polinomial`): empieza en 0 y por cada carácter hace `valor = (valor · 31 + código del carácter) mod 2³²`. La cubeta es `valor mod capacidad`.

Cálculo real para `fin` (códigos: f = 102, i = 105, n = 110):

```
valor = 0
f:  0 · 31 + 102        = 102
i:  102 · 31 + 105      = 3267
n:  3267 · 31 + 110     = 101387        ← hash_polinomial("fin")
cubeta con capacidad 17:  101387 mod 17 = 16
cubeta con capacidad 79:  101387 mod 79 = 30
```

Comprobación: `python -c "from core.simbolos import hash_polinomial as h; print(h('fin'), h('fin') % 17, h('fin') % 79)"` imprime `101387 16 30`. En la captura `docs/capturas/2_tabla_simbolos.png` se ve `fin` con hash 101387 en la cubeta 30.

**Colisión:** dos lexemas distintos caen en la misma cubeta. Con capacidad 17, `si` (hash 3670) y `temperatura` (hash 321701232) dan ambos cubeta **15**.

**Encadenamiento separado:** cada cubeta es una lista; el lexema que colisiona se añade al final. Para buscar se calcula la cubeta y se recorre solo esa lista (`TablaSimbolos.buscar`).

**Factor de carga y redimensionado:** cuando `entradas / capacidad` supera 0,75 la tabla crece al primer primo ≥ 2 × capacidad (17 → 37 → 79) y reubica todas las entradas (`_redimensionar`).

**Dos medidas de colisiones** (en `correcto.flow`: 36 entradas, capacidad final 79):
- *Colisiones al insertar* = **14**: cuántas veces un lexema nuevo llegó a una cubeta ocupada en ese momento.
- *En la tabla actual* = **7** = entradas − cubetas ocupadas (36 − 29). Son menos porque cada redimensionado reparte de nuevo y deshace colisiones.

**Duplicados:** un lexema repetido no crea otra entrada; se añade su posición a `apariciones`.

### 1.7 Cómo se detectan y manejan los errores
- **Detección léxica:** el AFD termina en un estado final de error (o ningún reconocedor acepta el carácter → `LEX-001`). El lexer llama a `ManejadorErrores.reportar(codigo, linea, columna, lexema)`.
- **Recuperación (modo pánico):** se descarta el lexema inválido, se emite un token de tipo `ERROR` y **el análisis continúa**. Por eso `incorrecto.flow` reporta sus 15 errores en una sola pasada.
- **Catálogo:** `CATALOGO` en `core/errores.py` tiene los 19 diagnósticos, cada uno con tipo, título, mensaje y sugerencia. Es el único lugar donde están los textos.
- **Tres familias:** `LEX-001…007` (léxicos), `SIN-001…006` (estructurales), `ARC-001…006` (archivo: no existe, extensión, vacío, codificación, lectura, tamaño).
- **Durante la evaluación:** `SesionAnalisis.siguiente_paso()` entrega un `Paso` por token con los errores de ese paso; la ventana lo pinta al instante (Manejador de errores, consola, subrayado y ✗ en el margen).
- **Al final:** se ofrece «¿Desea ver la tabla de símbolos?» y queda el botón «Ver tabla de símbolos».

### 1.8 Arquitectura por capas (Clean Architecture ligera)

```
main.py → ui/ → application/ → core/ → config/reglas.py → core/modelos.py
          tkinter   casos de uso    dominio     datos del lenguaje
```

- Las dependencias van en un solo sentido. `core/` y `application/` **no importan tkinter**: se comprueba con `grep -rn tkinter core application config` (no devuelve nada) y con la prueba `test_dominio_sin_tkinter`.
- `ui/` no usa el lexer directamente: pide todo a `application/analisis_service.py`.
- Consecuencia práctica: el mismo núcleo sirve a la ventana y al modo consola (`python main.py --consola …`).

### 1.9 SOLID con ejemplos de este código

| Principio | Ejemplo concreto |
|---|---|
| **S** — responsabilidad única | `core/lexer.py` solo reconoce; `core/simbolos.py` solo es la tabla; `core/errores.py` solo errores; `ui/estilos.py` solo colores. Cambiar un color no toca el lexer |
| **O** — abierto/cerrado | Agregar `repetir` es **una línea de datos** en `PALABRAS_RESERVADAS`; no se modifica ningún algoritmo (ejercicio 1) |
| **L** — sustitución | Cualquier función `str → int` sirve como hash: `TablaSimbolos(funcion_hash=lambda s: 0)` sigue funcionando (así se fuerzan colisiones en `tests/test_simbolos.py`) |
| **I** — interfaces pequeñas | Los paneles reciben solo lo que pintan: `agregar_token(numero, token)`, `agregar_error(diagnostico)`; no conocen el servicio |
| **D** — inversión de dependencias | `Lexer(fuente, manejador)` recibe su manejador de errores y `TablaSimbolos` su función hash por parámetro; el dominio no depende de la interfaz |

No se usan fábricas, contenedores ni interfaces abstractas: a este tamaño solo añadirían código que explicar.

---

## Parte 2 · Diez ejercicios de modificación

Formato de cada ejercicio: qué se pide · dónde · cambio exacto · cómo comprobarlo · qué prueba cambia · explicación.

> **Sobre las pruebas que fallan.** Varias pruebas fijan la definición de FlowLang 1.0 (17 reservadas, 15 operadores…). Si se modifica el lenguaje, **deben** fallar: es la batería avisando de que la especificación cambió. La respuesta correcta ante el profesor es: «falla la prueba que fija ese número; lo actualizo y vuelve a verde».

### Ejercicio 1 — Agregar la palabra reservada `repetir`
- **Archivo:** `config/reglas.py`, diccionario `PALABRAS_RESERVADAS`.
- **Cambio:**

```python
# antes
    "mientras": "Repite un bloque mientras se cumpla una condición.",
# después
    "mientras": "Repite un bloque mientras se cumpla una condición.",
    "repetir": "Repite un bloque un número fijo de veces.",
```

- **Comprobar:** escribir `inicio repetir repetir2 fin` en el editor y analizar: `repetir` sale como Palabra reservada y `repetir2` como Identificador. El panel izquierdo muestra «Palabras reservadas (18)».
- **Pruebas:** 114 de 115. Falla solo `tests.test_afd.TestReglas.test_conteos_de_flowlang_1_0`. Arreglo en `tests/test_afd.py`: cambiar los dos `17` de la línea de `PALABRAS_RESERVADAS` por `18`.
- **Explicación:** el AFD no cambia; `repetir` ya era aceptada como identificador. Lo que cambia es la consulta posterior en `reconocer_lexema`. La regex del modo educativo se actualiza sola porque es `"|".join(PALABRAS_RESERVADAS)`.

### Ejercicio 2 — Agregar el operador `**` (potencia)
- **Archivo:** `config/reglas.py`, diccionario `OPERADORES` e `INFO_CATEGORIAS`.
- **Cambio:**

```python
# antes
    "%": TipoToken.OPERADOR_ARITMETICO,
# después
    "%": TipoToken.OPERADOR_ARITMETICO,
    "**": TipoToken.OPERADOR_ARITMETICO,
```
```python
# antes (en INFO_CATEGORIAS[TipoToken.OPERADOR_ARITMETICO])
        "regex": r"[-+*/%]",
# después
        "regex": r"\*\*|[-+*/%]",
```

- **Comprobar:** `inicio a ** b * c /** x */ fin` → `**` es un solo token aritmético, `*` otro, y `/** x */` sigue siendo comentario.
- **Pruebas:** falla solo `test_conteos_de_flowlang_1_0` (operadores 15 → 16). Si se olvida actualizar la regex, además falla `test_aud03_regex_informativas_coinciden_con_los_datos`: esa prueba vigila que la regex mostrada y el diccionario digan lo mismo.
- **Explicación:** coincidencia más larga. `_mejor_simbolo` prueba primero los símbolos más largos, así que `**` gana a `*`. Para un operador de un carácter que hoy es error (por ejemplo `^`), el cambio es idéntico: `"^": TipoToken.OPERADOR_ARITMETICO` y añadir `^` a la regex.

### Ejercicio 3 — Cambiar la regla de identificadores (permitir `ñ` y vocales con tilde)
- **Archivo:** `config/reglas.py`, constante `LETRAS` e `INFO_CATEGORIAS[TipoToken.IDENTIFICADOR]`.
- **Cambio:**

```python
# antes
LETRAS = string.ascii_letters
# después
LETRAS = string.ascii_letters + "ñÑáéíóúÁÉÍÓÚ"
```
```python
# antes
        "regex": "[A-Za-z_][A-Za-z0-9_]*",
# después
        "regex": "[A-Za-zñÑáéíóúÁÉÍÓÚ_][A-Za-z0-9ñÑáéíóúÁÉÍÓÚ_]*",
```

- **Comprobar:** `inicio numero año = 1; fin` → `año` es un Identificador y la cadena es válida (antes daba `LEX-001` en la `ñ`).
- **Pruebas:** fallan 3, todas porque fijaban la regla anterior: `test_conteos_de_flowlang_1_0` (letras 52 → 64), `tests.test_afd.TestMotorAFD.test_clase_caracter` (afirmaba que `ñ` no es letra) y `tests.test_lexer.TestLexer.test_caracteres_desconocidos` (afirmaba que `año` da error). Se actualizan o se cambia la `ñ` de esas pruebas por otro carácter no permitido, como `ç`.
- **Explicación:** el AFD no nombra letras concretas: usa la **clase** `LETRA`, y `clase_caracter` (en `core/afd.py`) decide qué es letra consultando `LETRAS`. Cambiar el alfabeto no cambia los estados ni las transiciones. Variante: permitir `$` al inicio es añadir `"$": "q1"` en la fila `"q0"` de `AFD_IDENTIFICADOR`.

### Ejercicio 4 — Cambiar el formato de los decimales (aceptar `.5`)
- **Archivo:** `config/reglas.py`, `AFD_NUMERO` e `INFO_CATEGORIAS[TipoToken.DECIMAL]`.
- **Cambio:**

```python
# antes
        "q6": {DIGITO: "q4"},
# después
        "q6": {DIGITO: "q3"},
```
```python
# antes
        "regex": r"[0-9]+\.[0-9]+",
# después
        "regex": r"[0-9]*\.[0-9]+",
```

- **Comprobar:** `inicio decimal x = .5; decimal z = 5.; fin` → `.5` es Decimal con valor 0.5; `5.` sigue siendo `LEX-003`; un `.` suelto sigue siendo `LEX-001`.
- **Pruebas:** fallan 2: `tests.test_afd.TestMotorAFD.test_recorridos_de_la_especificacion` (esperaba `.5` → `q0, q6, q4`, error) y `tests.test_lexer.TestLexer.test_numeros_mal_formados` (tenía `.5` y `x1.5` como errores). La prueba de **equivalencia regex ↔ AFD sigue en verde**, lo que confirma que tabla y regex cambiaron de forma coherente.
- **Explicación:** `q6` es el estado «vi un punto sin parte entera». Antes llevaba al estado de error `q4`; ahora lleva a `q3`, el estado final de `DECIMAL`. Se cambió **una transición**.
- **Variante más invasiva (aceptar `5.`):** mover `q2` de `"errores"` a `"aceptacion"` (`"q2": TipoToken.DECIMAL`) y la regex a `[0-9]+\.[0-9]*`. Funciona, pero rompe 9 pruebas porque `incorrecto.flow` contiene `5.` como error de ejemplo. Conviene explicarla sin ejecutarla.

### Ejercicio 5 — Agregar un diagnóstico nuevo (`LEX-008`: decimal sin parte entera)
- **Archivos:** `core/errores.py` (`CATALOGO`) y `config/reglas.py` (`AFD_NUMERO`).
- **Cambio 1 — el texto, en `CATALOGO`, antes de `"SIN-001"`:**

```python
    "LEX-008": {"tipo": _LEX, "titulo": "Decimal sin parte entera",
                "mensaje": "Al número '{lexema}' le falta la parte entera.",
                "sugerencia": "Escriba un 0 antes del punto, por ejemplo 0.5."},
```

- **Cambio 2 — quién lo emite, en `AFD_NUMERO`:**

```python
# antes
        "q6": {DIGITO: "q4"},
    },
    "aceptacion": {"q1": TipoToken.ENTERO, "q3": TipoToken.DECIMAL},
    "errores": {"q2": "LEX-003", "q4": "LEX-003", "q5": "LEX-004"},
# después
        "q6": {DIGITO: "q7"},
        "q7": {DIGITO: "q7", ".": "q4", LETRA: "q4", "_": "q4"},
    },
    "aceptacion": {"q1": TipoToken.ENTERO, "q3": TipoToken.DECIMAL},
    "errores": {"q2": "LEX-003", "q4": "LEX-003", "q5": "LEX-004", "q7": "LEX-008"},
```

- **Comprobar:** `inicio x = .5; y = .5.2; z = 3.; fin` → `.5` da `LEX-008` con la sugerencia nueva; `.5.2` y `3.` siguen dando `LEX-003`.
- **Pruebas:** fallan 3: `tests.test_errores.TestCatalogo.test_diecinueve_codigos_con_tipo_correcto` (19 → 20 códigos, 7 → 8 léxicos), `test_recorridos_de_la_especificacion` y `test_numeros_mal_formados` (esperaban `LEX-003` para `.5`).
- **Explicación:** un diagnóstico tiene dos partes: **qué dice** (catálogo, un solo lugar) y **cuándo ocurre** (un estado final de error en un AFD). El lexer no se toca: ya sabe reportar cualquier código que el AFD le devuelva. Para un diagnóstico estructural, la segunda parte sería una regla en `validar_estructura` (`core/validador.py`).

### Ejercicio 6 — Agregar una columna a la tabla de símbolos («Longitud»)
- **Archivos:** `core/modelos.py`, `core/simbolos.py`, `ui/paneles.py`.
- **Cambio 1 — el dato, en la clase `EntradaSimbolo`:**

```python
# antes
    apariciones: list[tuple[int, int]] = field(default_factory=list)
# después
    apariciones: list[tuple[int, int]] = field(default_factory=list)
    longitud: int = 0
```

- **Cambio 2 — llenarlo, en `registrar_token`:**

```python
# antes
        entrada.valor = valor_literal(token)
# después
        entrada.valor = valor_literal(token)
        entrada.longitud = len(token.lexema)
```

- **Cambio 3 — mostrarlo, en `ui/paneles.py`:**

```python
# antes (COLUMNAS_SIMBOLOS)
                     ("decl", "Decl.", 50), ("apariciones", "Apariciones", 220)]
# después
                     ("decl", "Decl.", 50), ("apariciones", "Apariciones", 220),
                     ("longitud", "Long.", 60)]
```
```python
# antes (mostrar_tabla_simbolos)
                    entrada.linea_declaracion or "", recortar(entrada.apariciones)))
# después
                    entrada.linea_declaracion or "", recortar(entrada.apariciones), entrada.longitud))
```

- **Comprobar:** analizar `correcto.flow`, aceptar ver la tabla: aparece la columna «Long.» al final (`temperatura` → 11).
- **Pruebas:** 115 de 115, ninguna cambia.
- **Explicación:** el dato recorre las capas en orden: modelo → dominio → interfaz. El valor debe ir en la misma posición que su columna (por eso ambos se añaden al final). La clase `TablaSimbolos` no se toca: es una tabla hash genérica.

### Ejercicio 7 — Cambiar un color o el tema
- **Archivo:** `ui/estilos.py`, diccionarios `COLORES_TOKEN` y `TEMA`.
- **Cambio:**

```python
# antes
    TipoToken.PALABRA_RESERVADA: "#0B3FA8",
# después
    TipoToken.PALABRA_RESERVADA: "#7B1FA2",
```
```python
# antes
    "cabecera": "#14213D",
# después
    "cabecera": "#0B3D2E",
```

- **Comprobar:** abrir la aplicación: las palabras reservadas se ven en violeta (siguen en negrita, `TIPOS_EN_NEGRITA`) en el editor y las palabras del resumen de la tabla; la cabecera pasa de azul marino a verde oscuro.
- **Pruebas:** 115 de 115.
- **Explicación:** responsabilidad única. Ningún otro archivo de `ui/` contiene colores: se comprueba con `grep -rn "#[0-9a-fA-F]\{6\}" ui/ | grep -v estilos.py`, que no devuelve nada.

### Ejercicio 8 — Aceptar otra extensión de archivo (`.fl`)
- **Archivos:** `config/reglas.py` (`EXTENSIONES_PERMITIDAS`) y el texto de `ARC-002` en `core/errores.py`.
- **Cambio:**

```python
# antes
EXTENSIONES_PERMITIDAS = (".flow", ".txt")
# después
EXTENSIONES_PERMITIDAS = (".flow", ".txt", ".fl")
```
```python
# antes (CATALOGO["ARC-002"])
"sugerencia": "Use un archivo `.flow` o `.txt`."
# después
"sugerencia": "Use un archivo `.flow`, `.txt` o `.fl`."
```

- **Comprobar:** copiar `ejemplos/correcto.flow` como `prueba.fl` y abrirlo: se analiza y es válido; abrir `main.py` da `ARC-002` con el texto nuevo. El selector de archivos también ofrece `*.fl` (lee la misma constante).
- **Pruebas:** 115 de 115.
- **Explicación:** la regla está en un dato y la aplica `cargar_fuente` (`application/archivos.py`). El segundo cambio es una **limitación conocida y declarada**: el texto de ese mensaje repite el dato (decisión D-31); funciona sin él, pero el mensaje quedaría desactualizado. Si se **reemplazara** `.flow` en vez de añadir `.fl`, los tres ejemplos dejarían de abrirse y fallarían unas 10 pruebas.

### Ejercicio 9 — Agregar un patrón léxico nuevo (carácter entre comillas simples: `'a'`)
- **Archivos:** `core/modelos.py`, `config/reglas.py`, `ui/estilos.py`.
- **Cambio 1 — la categoría, en `TipoToken`:**

```python
# antes
    CADENA = "Cadena"
# después
    CADENA = "Cadena"
    CARACTER = "Carácter"
```

- **Cambio 2 — el autómata, en `config/reglas.py`, antes de `AUTOMATAS`:**

```python
AFD_CARACTER = {
    "nombre": "AFD de caracteres",
    "inicial": "q0",
    "transiciones": {
        "q0": {"'": "q1"},
        "q1": {OTRO: "q2"},
        "q2": {"'": "q3"},
    },
    "aceptacion": {"q3": TipoToken.CARACTER},
    "errores": {},
}
```
```python
# antes
AUTOMATAS = (AFD_COMENTARIO, AFD_CADENA, AFD_NUMERO, AFD_IDENTIFICADOR)
# después
AUTOMATAS = (AFD_COMENTARIO, AFD_CADENA, AFD_CARACTER, AFD_NUMERO, AFD_IDENTIFICADOR)
```

- **Cambio 3 — su información, en `INFO_CATEGORIAS`, antes de `TipoToken.OPERADOR_ARITMETICO`:**

```python
    TipoToken.CARACTER: {
        "descripcion": "Un solo carácter entre comillas simples.",
        "regex": "'[^\\n]'",
        "ejemplos": ("'a'", "'7'"),
    },
```

- **Cambio 4 — su color, en `COLORES_TOKEN` (`ui/estilos.py`):**

```python
# antes
    TipoToken.CADENA: "#A14A00",
# después
    TipoToken.CADENA: "#A14A00",
    TipoToken.CARACTER: "#8A5A00",
```

- **Comprobar:** `inicio x = 'a'; y = 'ab'; fin` → `'a'` es un token Carácter con recorrido `q0 → q1 → q2 → q3`; `'ab'` no es aceptado (dos `LEX-001`, uno por cada comilla, como antes).
- **Pruebas:** fallan 3: `test_conteos_de_flowlang_1_0` (autómatas 4 → 5), `tests.test_lexer.TestModelos.test_doce_tipos` (12 → 13) y `test_caracteres_desconocidos` (afirmaba que `'a'` da dos errores).
- **Explicación:** el lexer ejecuta **todos** los AFD de `AUTOMATAS` y elige el más largo; añadir un patrón es añadir una tabla, no escribir código. Opcional: para instalarlo en la tabla de símbolos, añadir `TipoToken.CARACTER` a `CATEGORIAS_EN_TABLA`; para que no quede una sugerencia obsoleta, quitar la entrada `"'"` de `SUGERENCIAS_CARACTER`.

### Ejercicio 10 — Instalar también operadores y delimitadores en la tabla de símbolos
- **Archivo:** `config/reglas.py`, `CATEGORIAS_EN_TABLA`.
- **Cambio:**

```python
# antes
    TipoToken.CADENA,
})
# después
    TipoToken.CADENA,
    TipoToken.OPERADOR_ARITMETICO,
    TipoToken.OPERADOR_RELACIONAL,
    TipoToken.OPERADOR_LOGICO,
    TipoToken.ASIGNACION,
    TipoToken.DELIMITADOR,
})
```

- **Comprobar:** analizar `correcto.flow` y ver la tabla: pasa de 36 a **53 entradas** (capacidad 79, 23 colisiones al insertar, 15 en la tabla actual); `;` aparece con sus 15 apariciones.
- **Pruebas:** fallan 6, todas por números que cambian a propósito: `tests.test_simbolos.TestRegistrarToken.test_no_instalables`, `tests.test_integracion.TestEjemplos.test_correcto` y `test_incorrecto`, `tests.test_integracion.TestSesion.test_pasos_lexicos`, y en `tests.test_ui_humo.TestUIHumo`, `test_colisiones_en_el_resumen` y `test_flujo_completo_incorrecto`. Para la demostración: mostrar el resultado y volver atrás con `git checkout -- config/reglas.py`.
- **Explicación:** qué se instala es una **decisión de diseño expresada como dato**; `registrar_token` solo pregunta `token.tipo not in reglas.CATEGORIAS_EN_TABLA`. Ver la pregunta 13.

### Resumen de los ejercicios

| # | Modificación | Archivos | Pruebas que cambian |
|---|---|---|---|
| 1 | Reservada `repetir` | `config/reglas.py` | 1 (conteos) |
| 2 | Operador `**` | `config/reglas.py` | 1 (conteos) |
| 3 | `ñ` en identificadores | `config/reglas.py` | 3 |
| 4 | Decimal `.5` | `config/reglas.py` | 2 |
| 5 | Diagnóstico `LEX-008` | `core/errores.py`, `config/reglas.py` | 3 |
| 6 | Columna «Longitud» | `core/modelos.py`, `core/simbolos.py`, `ui/paneles.py` | 0 |
| 7 | Color / tema | `ui/estilos.py` | 0 |
| 8 | Extensión `.fl` | `config/reglas.py`, `core/errores.py` | 0 |
| 9 | Patrón `'a'` | `core/modelos.py`, `config/reglas.py`, `ui/estilos.py` | 3 |
| 10 | Operadores en la tabla | `config/reglas.py` | 6 |

---

## Parte 3 · Preguntas probables y respuestas

**Autómatas y expresiones regulares**

1. **¿Dónde está el autómata en el código?** Las tablas, en `config/reglas.py` (`AFD_IDENTIFICADOR`, `AFD_NUMERO`, `AFD_CADENA`, `AFD_COMENTARIO`). El motor que las ejecuta, en `core/afd.py` (`AFD.siguiente_estado` y `AFD.reconocer`). En pantalla, la pestaña Autómatas muestra el recorrido de estados de cualquier token y la tabla de transiciones usada.
2. **¿Por qué es determinista?** Para cada par (estado, carácter), `siguiente_estado` devuelve un solo estado o ninguno. El orden de búsqueda es fijo: carácter exacto, luego su clase (letra, dígito, salto), luego `OTRO`.
3. **¿Usan expresiones regulares?** Como **especificación**, no para analizar. El módulo `re` solo se usa en las pruebas, para comprobar que cada AFD acepta lo mismo que su regex. No lo usamos en el lexer porque `re` funciona por *backtracking* y su `|` elige la primera alternativa que coincide, no la más larga.
4. **¿El AFD es mínimo?** El de identificadores sí (2 estados). Los de número y cadena no: tienen estados de error añadidos a propósito para consumir entero un lexema mal escrito. El mínimo de números tiene 4 estados (q0–q3) y está en la especificación §3.3.
5. **¿Cómo distinguen `3.4.5` de `12abc`?** Decide el primer carácter que no es dígito: si es `.`, el AFD va hacia `q4` (`LEX-003`, número mal formado); si es letra o `_`, hacia `q5` (`LEX-004`, identificador que empieza con dígito).
6. **¿Por qué el balance de paréntesis no lo hace un AFD?** Porque no es un lenguaje regular: haría falta contar aperturas sin límite y un autómata finito no tiene memoria. Se usa una pila en `_validar_balance` (`core/validador.py`), que es la idea de un autómata de pila.

**Tokens y análisis léxico**

7. **¿Qué pasa con `>=`?** Se prueban primero 2 caracteres y luego 1 (`_mejor_simbolo`): `>=` es un token. Con `a= =b` salen dos asignaciones, porque el espacio separa.
8. **¿Cómo saben la línea y la columna?** El lexer lleva dos contadores desde 1; el salto de línea suma una línea y devuelve la columna a 1. Un comentario de bloque de varias líneas actualiza ambos (`Lexer.tokens`).
9. **¿Qué hacen con los espacios y los comentarios?** Los espacios se descartan. Los comentarios producen un token `COMENTARIO` (para colorearlos y explicarlos) que el validador y la tabla de símbolos ignoran.
10. **¿Cuál es la complejidad del lexer?** Lineal en la longitud del texto: en cada posición cada AFD se detiene en el primer carácter que no le corresponde, y el lexema ganador no se vuelve a leer. Hay una prueba con 5 000 líneas (40 000 tokens).

**Tabla hash**

11. **¿Por qué no usaron `dict`?** Porque el enunciado pide instalar «por función hash» y había que poder explicarla. `hash_polinomial` y `TablaSimbolos` están escritos a mano con listas.
12. **¿Complejidad de la tabla?** Buscar e insertar: en promedio constante (factor de carga ≤ 0,75); en el peor caso, lineal en el largo de la cubeta (todo en una cubeta: lo fuerza la prueba `test_colisiones_forzadas` con una función hash que siempre devuelve 0). Redimensionar es lineal, pero ocurre pocas veces (coste amortizado constante).
13. **(Duda abierta) ¿Por qué los operadores no están en la tabla de símbolos?** Decisión de diseño: la tabla guarda lo que tiene atributos útiles para otras fases (tipo, valor, declaración, apariciones): identificadores, literales y reservadas. Un `;` no tiene atributos; su categoría basta. **Si el profesor quiere todos los tokens:** ejercicio 10, un cambio en `CATEGORIAS_EN_TABLA`; la tabla pasa de 36 a 53 entradas en `correcto.flow`.
14. **¿Por qué aparecen 14 colisiones si en la tabla solo veo 7?** Son dos medidas: 14 ocurrieron al insertar (con capacidades 17 y 37); al redimensionar, las entradas se reparten de nuevo y hoy solo 7 comparten cubeta (36 entradas − 29 cubetas ocupadas).
15. **¿Por qué capacidad prima y base 31?** Un módulo primo reparte mejor los restos. La base 31 es la del hash polinomial clásico de cadenas y permite hacer la cuenta a mano. La capacidad inicial es pequeña (17) para que las colisiones se vean con programas cortos.
16. **¿Qué pasa con un identificador repetido?** No se duplica: `instalar` lo encuentra con `buscar` y añade la posición a `apariciones`.
17. **¿Cómo sabe la tabla el tipo de `temperatura`?** Única regla de contexto: un identificador que va justo después de una palabra de `TIPOS_DE_DATO` (`numero temperatura`) queda con ese tipo y esa línea de declaración (`registrar_token`). No es análisis semántico: no se reporta ningún error de tipos.

**Manejo de errores**

18. **¿Qué es el modo pánico?** Ante un error se descarta el lexema inválido y se sigue con el carácter siguiente; nunca se detiene en el primer error.
19. **¿Qué tiene cada error?** Código, tipo, título, mensaje, sugerencia, línea, columna y lexema (`Diagnostico` en `core/modelos.py`).
20. **¿Cómo cumple «la interfaz se despliega durante la evaluación»?** El lexer es un generador; `SesionAnalisis.siguiente_paso()` devuelve un `Paso` por token, con los errores de ese paso. La ventana consume pasos con un temporizador (`after`), agrupados por línea (la «Pausa por línea» del deslizador), y pinta cada error cuando aparece. Con «Paso a paso» (F10) se ve token por token.
21. **¿Y «al final, la alternativa de desplegar la tabla de símbolos»?** La pestaña «Tabla de símbolos» y el botón «Ver tabla de símbolos» de la cabecera están deshabilitados durante el análisis; al terminar aparece el diálogo «¿Desea ver la tabla de símbolos?» y quedan la pestaña y el botón.

**Validez de la cadena**

22. **¿Qué es una cadena válida para ustedes?** Cero errores léxicos y cero estructurales. Los estructurales (inicio/fin, balance) son comprobaciones sintácticas mínimas, declaradas como tales y separadas en `core/validador.py`.
23. **(Duda abierta) El enunciado dice «cadenas de entrada», en plural. ¿Analizan una por línea?** Tomamos el archivo como un programa, y **además** se informa el veredicto léxico de cada línea: ✗ en el margen del editor y «Líneas léxicamente inválidas: …» en la consola (`ResultadoAnalisis.lineas_invalidas`). **Si el profesor quiere cada línea como cadena independiente, sin `inicio`/`fin`:** en `validar_estructura` (`core/validador.py`) se quitan las cuatro líneas de las reglas `SIN-002` y `SIN-003` (los dos `if not _es_palabra(...)`). Ensayado: un archivo sin `inicio`/`fin` queda estructuralmente válido y se sigue informando qué líneas tienen error; cambian 6 pruebas que esperaban esos dos diagnósticos.

**Arquitectura y calidad**

24. **¿Qué pasa si cambian la interfaz por otra?** `core/` y `application/` no cambian; el modo consola es la prueba: usa el mismo servicio sin tkinter.
25. **¿Dónde se cambia el lenguaje?** En `config/reglas.py`, que solo contiene datos (ni funciones ni clases).
26. **¿Qué patrones usaron?** Autómata dirigido por tabla; generador para la evaluación progresiva; la función hash como parámetro (estrategia mínima); paneles pasivos coordinados por `VentanaPrincipal`. No usamos más porque no simplificaban nada.
27. **¿Cómo saben que funciona?** 141 pruebas con `unittest`: posiciones exactas, coincidencia más larga, colisiones forzadas, archivos inválidos, equivalencia regex ↔ AFD, y pruebas de la ventana. Dos auditorías independientes (`docs/06_auditoria.md`) incluyeron 20 000 entradas aleatorias sin fallos.
28. **¿Qué limitaciones tiene?** No hay análisis sintáctico completo ni semántico. Cuatro mensajes repiten un dato de `reglas.py` (hay que actualizar el texto si cambia el dato). El análisis animado de un archivo de 5 000 líneas tarda unos 6 segundos. Con Tcl/Tk 8.6, el coloreado posterior a un emoji puede desplazarse (el análisis es correcto).
29. **¿Cómo se cambia el aspecto de la ventana?** Todos los colores están en `ui/estilos.py` (`TEMA`, `COLORES_TOKEN`) y los estilos `ttk` en `aplicar_tema`; ningún otro archivo de `ui/` tiene un color (arquitectura §17.3).
30. **¿Dónde se ven los errores durante la evaluación?** En cinco sitios a la vez: línea roja en la Consola, fila nueva en el Manejador de errores (siempre visible, con el total en su título), subrayado y línea rosada con ✗ en el editor, y los contadores de la barra de estado (arquitectura §17.5).

---

## Parte 4 · Guion de demostración (6 minutos)

Preparación: `git status` limpio; terminal abierta en `SmartLexStudio/`; ventana maximizada. Las capturas de `docs/capturas/` muestran cómo debe verse cada momento y sirven de respaldo si algo falla.

| Tiempo | Qué hacer | Qué decir |
|---|---|---|
| 0:00–0:40 | `python main.py`. Se abre el selector de archivo; elegir `ejemplos/correcto.flow` | «El programa solicita el archivo con la cadena de entrada para iniciar (requisito 6). FlowLang es nuestro lenguaje para automatizaciones; la pestaña «Lenguaje» muestra sus reglas, leídas de `config/reglas.py`.» |
| 0:40–1:30 | Pulsar **Analizar** (F5). Ver la pestaña Tokens llenarse línea por línea, con la ✓ de cada línea evaluada (deslizador «Pausa por línea»). Responder **No** al diálogo final (captura `1_correcto_tokens.png`) | «La evaluación es progresiva: un token por paso, agrupados por línea. 111 tokens, léxico válido, estructura válida: cadena VÁLIDA. Al final se ofrece ver la tabla de símbolos.» |
| 1:30–2:30 | Botón **Ver tabla de símbolos** (captura `2_tabla_simbolos.png`). Señalar `fin`: hash 101387, cubeta 30; y las filas resaltadas | «Tabla hash propia. `fin`: 102·31+105 = 3267; 3267·31+110 = 101387; módulo 79 = 30. Las filas resaltadas comparten cubeta: colisiones resueltas por encadenamiento. Hubo 14 colisiones al insertar; tras dos redimensionados quedan 7.» |
| 2:30–3:20 | Pestaña Tokens, clic en `45.5`, luego pestaña **Autómatas** (captura `4_automatas.png`) | «Este decimal lo reconoció el AFD de números con el recorrido q0, q1, q1, q2, q3. Abajo está la tabla de transiciones: es la misma que usa el lexer.» |
| 3:20–4:40 | Menú **Ejemplos ▾** → `incorrecto.flow`. **Paso a paso** (F10) tres veces: el tercer token es `2pi`. Luego **Analizar** para terminar; responder **No**. Clic en un error y doble clic (captura `5_incorrecto_errores.png`) | «`2pi` empieza con dígito: el AFD termina en un estado de error y aparece LEX-004 en ese instante, con el análisis sin terminar (requisito 5). No se detiene: modo pánico. Al final, 15 errores con código, mensaje y sugerencia; doble clic lleva a la posición.» |
| 4:40–5:10 | Pestaña **Resumen** (captura `3_resumen.png`) y la barra de estado con el veredicto | «Veredictos separados: léxico y estructura. Los estructurales —falta `fin`, paréntesis sin cerrar— los detecta el validador con una pila, porque eso no es regular.» |
| 5:10–6:00 | Modificación en vivo (ejercicio 1): añadir `repetir` en `config/reglas.py`, reabrir la aplicación, escribir `inicio repetir fin` y analizar. Después `git checkout -- .` | «Una línea de datos y ningún algoritmo tocado: abierto/cerrado. La batería avisa con una sola prueba, la que fija que FlowLang 1.0 tiene 17 reservadas.» |

**Si no hay tkinter en el equipo:** `python main.py --consola ejemplos/incorrecto.flow` muestra tokens, errores, veredicto y pregunta si se quiere ver la tabla de símbolos.

**Si preguntan por las pruebas:** `python -m unittest discover -s tests -t .` (≈ 25 s) → `Ran 118 tests … OK`.
