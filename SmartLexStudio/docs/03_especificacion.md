# 03 · Especificación de FlowLang 1.0

Autor: architect-fable. Este documento es el **contrato del lenguaje**. Todo lo que aquí se define como dato vive en `config/reglas.py`; los algoritmos que lo interpretan viven en `core/`.
Todas las tablas de transición y todos los ejemplos con posiciones de este documento fueron comprobados con un prototipo desechable (no forma parte del proyecto) antes de escribirlos.

---

## 1. Qué es FlowLang

FlowLang es un lenguaje educativo para **describir automatizaciones** (riego, luces, alarmas): se declaran variables y dispositivos, se leen sensores, y se activan o desactivan dispositivos según condiciones.

```flow
// Riego automatico
inicio
    numero temperatura = 28;
    decimal humedad = 45.5;
    dispositivo bomba;
    si (temperatura >= 30 && humedad < 50.0) {
        activar bomba;
        esperar 10;
        mostrar "Regando\n";
    } sino {
        desactivar bomba;
    }
fin
```

Características generales:

- **Sensible a mayúsculas**: `inicio` es palabra reservada; `Inicio` es un identificador.
- **Alfabeto de los lexemas**: ASCII. Las letras acentuadas y la `ñ` solo se admiten **dentro de cadenas y comentarios**.
- **Formato libre**: espacios, tabuladores y saltos de línea separan lexemas y no tienen otro significado.
- Archivo fuente: texto UTF-8 con extensión `.flow` (también se acepta `.txt`).

### 1.1 Alcance: qué se analiza y qué no

| Nivel | Pregunta que responde | ¿Lo hace SmartLex Studio? |
|---|---|---|
| **Léxico** | ¿Cada lexema pertenece a alguna categoría de token? | **Sí, completo** (objeto del proyecto). Diagnósticos `LEX-…` |
| **Sintáctico** | ¿Los tokens están en un orden permitido por la gramática? | **Solo tres comprobaciones estructurales ligeras** (§8.2), declaradas explícitamente como *estructurales*, no léxicas. Diagnósticos `SIN-…`. No hay parser. |
| **Semántico** | ¿El programa tiene sentido (tipos, variables declaradas, redeclaraciones)? | **No.** Único uso de contexto: anotar en la tabla de símbolos el tipo con que se declara un identificador (§9). No se reporta ningún error semántico. |

Ejemplos de lo que **no** es error para esta herramienta: `numero x = "hola";` (semántico), `x = = 3;` (sintáctico), usar una variable no declarada (semántico).

---

## 2. Categorías de token

`TipoToken` (enumeración en `core/modelos.py`):

| # | Categoría | Ejemplos | ¿Va a la tabla de símbolos? |
|---|---|---|---|
| 1 | `PALABRA_RESERVADA` | `inicio` `si` `mostrar` | Sí |
| 2 | `IDENTIFICADOR` | `temperatura` `_x1` | Sí |
| 3 | `ENTERO` | `0` `28` `007` | Sí |
| 4 | `DECIMAL` | `45.5` `0.0` | Sí |
| 5 | `CADENA` | `"Regando\n"` | Sí |
| 6 | `OPERADOR_ARITMETICO` | `+ - * / %` | No (configurable) |
| 7 | `OPERADOR_RELACIONAL` | `== != < <= > >=` | No (configurable) |
| 8 | `OPERADOR_LOGICO` | `&& \|\| !` | No (configurable) |
| 9 | `ASIGNACION` | `=` | No (configurable) |
| 10 | `DELIMITADOR` | `( ) { } , ;` | No (configurable) |
| 11 | `COMENTARIO` | `// …` `/* … */` | No |
| 12 | `ERROR` | `3.4.5` `@` `"sin cerrar` | No |

- Los **espacios en blanco** (` `, `\t`, `\r`, `\n`) se descartan: no producen token.
- `COMENTARIO` sí produce token (para resaltarlo y explicarlo) pero es **no significativo**: el validador y la tabla de símbolos lo ignoran.
- `ERROR` es el token que acompaña a todo diagnóstico léxico: contiene el lexema inválido completo, para poder marcarlo en el editor.
- Token **significativo** = cualquier token que no sea `COMENTARIO` ni `ERROR`.

---

## 3. Definición formal de cada categoría

Notación: `L = [A-Za-z]` (52 letras ASCII), `D = [0-9]`. Las expresiones regulares usan la sintaxis del módulo `re` de Python y describen el **lexema completo**.

### 3.1 Palabras reservadas (17)

| Grupo | Palabras |
|---|---|
| Estructura del programa | `inicio` `fin` |
| Tipos de dato | `numero` `decimal` `texto` `booleano` `dispositivo` |
| Valores lógicos | `verdadero` `falso` |
| Control de flujo | `si` `sino` `mientras` |
| Acciones | `mostrar` `leer` `activar` `desactivar` `esperar` |

- Definición: conjunto finito de cadenas `R`. Regex: `inicio|fin|numero|…|esperar`.
- **Reconocimiento**: no tienen AFD propio. Se reconoce un identificador con su AFD y luego se consulta el lexema en `PALABRAS_RESERVADAS`; si está, el tipo pasa a `PALABRA_RESERVADA`. Así `si2` y `sinope` son identificadores (coincidencia más larga) y agregar una palabra es añadir una entrada al diccionario.
- `repetir` **no** es reservada a propósito: es la modificación de ejemplo para la sustentación.

### 3.2 Identificadores

- Definición: `ID = { w ∈ (L ∪ D ∪ {_})⁺ : el primer símbolo de w ∈ L ∪ {_} } − R`, con `|w| ≤ 32`.
- Regex: `[A-Za-z_][A-Za-z0-9_]*`
- AFD (`AFD_IDENTIFICADOR`), estado inicial `q0`, aceptación `{q1}`:

| Estado | letra | dígito | `_` | otro |
|---|---|---|---|---|
| → q0 | q1 | — | q1 | — |
| * q1 `IDENTIFICADOR` | q1 | q1 | q1 | — |

(`—` = no hay transición: el autómata se detiene.)

- Longitud máxima: `LONGITUD_MAXIMA_IDENTIFICADOR = 32`. Un identificador más largo se reconoce completo y se reporta `LEX-005`. *Nota honesta:* el límite de longitud es una propiedad regular, pero codificarlo exigiría 32 estados; se comprueba con `len()` después del AFD.

### 3.3 Números: enteros y decimales

- `ENTERO = D⁺` — regex `[0-9]+` (se permiten ceros a la izquierda: `007` vale 7).
- `DECIMAL = D⁺ . D⁺` — regex `[0-9]+\.[0-9]+` (parte entera y parte decimal obligatorias).
- No hay signo en el literal: `-5` son dos tokens (`-` y `5`). No hay notación científica.

**AFD mínimo** del lenguaje `ENTERO ∪ DECIMAL` (lo que se pide en teoría):

| Estado | dígito | `.` |
|---|---|---|
| → q0 | q1 | — |
| * q1 `ENTERO` | q1 | q2 |
| q2 | q3 | — |
| * q3 `DECIMAL` | q3 | — |

**AFD implementado** (`AFD_NUMERO`): el mínimo más tres **estados de error** (q4, q5, q6) y q2 marcado como error. Sirven para que un número mal escrito se consuma **como un solo lexema** y se informe con precisión, en vez de partirse en trozos que producirían errores en cascada.

| Estado | dígito | `.` | letra | `_` | Resultado si el autómata termina aquí |
|---|---|---|---|---|---|
| → q0 | q1 | q6 | — | — | (no acepta) |
| * q1 | q1 | q2 | q5 | q5 | token `ENTERO` |
| ✗ q2 | q3 | q4 | q4 | q4 | error `LEX-003` (falta la parte decimal: `3.`) |
| * q3 | q3 | q4 | q4 | q4 | token `DECIMAL` |
| ✗ q4 | q4 | q4 | q4 | q4 | error `LEX-003` (número mal formado: `3.4.5`, `1.5abc`, `.5`) |
| ✗ q5 | q5 | q5 | q5 | q5 | error `LEX-004` (identificador que empieza con dígito: `12abc`, `2pi`, `1_000`) |
| q6 | q4 | — | — | — | (no acepta: un `.` suelto es `LEX-001`) |

**Regla sin ambigüedad entre `LEX-003` y `LEX-004`** (consecuencia directa de la tabla): *decide el primer carácter que no es dígito.* Si es `.` el lexema es un **número mal formado** (`LEX-003`); si es letra o `_` es un **identificador inválido** (`LEX-004`).

| Lexema | Recorrido | Resultado |
|---|---|---|
| `28` | q0 q1 q1 | `ENTERO` |
| `45.5` | q0 q1 q1 q2 q3 | `DECIMAL` |
| `3.` | q0 q1 q2 | `LEX-003` |
| `3.4.5` | q0 q1 q2 q3 q4 q4 | `LEX-003` |
| `.5` | q0 q6 q4 | `LEX-003` |
| `12abc` | q0 q1 q1 q5 q5 q5 | `LEX-004` |
| `1.5abc` | q0 q1 q2 q3 q4 q4 q4 | `LEX-003` |

### 3.4 Cadenas

- Delimitadas por comillas dobles, **en una sola línea**. Dentro se admite cualquier carácter excepto `"`, `\` y salto de línea, o una secuencia de escape válida.
- Escapes válidos (`ESCAPES_VALIDOS`): `\n` (salto), `\t` (tabulador), `\"` (comilla), `\\` (barra invertida).
- Regex: `"(?:[^"\\\n]|\\[nt"\\])*"`
- AFD (`AFD_CADENA`). Columna «otro» = cualquier carácter **que no sea salto de línea** y no tenga columna propia:

| Estado | `"` | `\` | `n` `t` | otro | salto / fin de archivo | Resultado si termina aquí |
|---|---|---|---|---|---|---|
| → q0 | q1 | — | — | — | — | (no acepta) |
| ✗ q1 (cuerpo) | q3 | q2 | q1 | q1 | — | error `LEX-002` (sin cerrar) |
| ✗ q2 (tras `\`) | q1 | q1 | q1 | q4 | — | error `LEX-002` |
| * q3 | — | — | — | — | — | token `CADENA` |
| ✗ q4 (cuerpo con escape inválido) | q5 | q6 | q4 | q4 | — | error `LEX-002` |
| ✗ q5 | — | — | — | — | — | error `LEX-006` (cerrada, con escape inválido) |
| ✗ q6 (tras `\`, ya con error) | q4 | q4 | q4 | q4 | — | error `LEX-002` |

El AFD mínimo de las cadenas **válidas** es {q0, q1, q2, q3}; q4–q6 existen para seguir leyendo hasta la comilla de cierre después de un escape inválido.

| Lexema | Resultado |
|---|---|
| `""` | `CADENA` (vacía) |
| `"a\"b\\"` | `CADENA` |
| `"Hola` ⏎ | `LEX-002`, lexema `"Hola` |
| `"C:\qatos"` | `LEX-006` en la posición de `\q` |
| `"a\qb` ⏎ | `LEX-002` (solo se informa que no cierra) |

### 3.5 Comentarios

- De línea: desde `//` hasta el final de la línea (el salto no forma parte). Regex: `//[^\n]*`
- De bloque: desde `/*` hasta el primer `*/`; puede ocupar varias líneas; no se anidan. Regex: `/\*(?:[^*]|\*+[^*/])*\*+/`
- AFD (`AFD_COMENTARIO`):

| Estado | `/` | `*` | otro | salto | Resultado si termina aquí |
|---|---|---|---|---|---|
| → q0 | q1 | — | — | — | (no acepta) |
| q1 | q2 | q3 | — | — | (no acepta: un `/` solo es el operador de división) |
| * q2 (línea) | q2 | q2 | q2 | — | token `COMENTARIO` |
| ✗ q3 (bloque) | q3 | q4 | q3 | q3 | error `LEX-007` (bloque sin cerrar) |
| ✗ q4 (bloque, vio `*`) | q5 | q4 | q3 | q3 | error `LEX-007` |
| * q5 | — | — | — | — | token `COMENTARIO` |

### 3.6 Operadores y delimitadores (símbolos fijos)

| Categoría | Lexemas |
|---|---|
| `OPERADOR_ARITMETICO` | `+` `-` `*` `/` `%` |
| `OPERADOR_RELACIONAL` | `==` `!=` `<` `<=` `>` `>=` |
| `OPERADOR_LOGICO` | `&&` `\|\|` `!` |
| `ASIGNACION` | `=` |
| `DELIMITADOR` | `(` `)` `{` `}` `,` `;` |

- Definición: conjunto finito de cadenas de longitud 1 o 2. Regex: `==|!=|<=|>=|&&|\|\||[-+*/%<>=!(){},;]`
- Reconocimiento: consulta en los diccionarios `OPERADORES` y `DELIMITADORES` probando **primero los 2 caracteres siguientes y luego 1** (coincidencia más larga). Es un autómata trivial de profundidad 2; no se escribe su tabla porque el diccionario *es* la tabla.
- `&` y `|` sueltos **no** son tokens: producen `LEX-001` con la sugerencia «¿Quiso escribir `&&`?».

### 3.7 Espacios en blanco

` ` (espacio), `\t`, `\r`, `\n`. Regex `[ \t\r\n]+`. Se descartan. Cada uno avanza una columna, salvo `\n`, que incrementa la línea y devuelve la columna a 1.

---

## 4. Convención de las tablas de transición

Válida para los cuatro AFD (motor en `core/afd.py`):

1. El **alfabeto de entrada** se agrupa en clases: `LETRA` (`A-Z a-z`), `DIGITO` (`0-9`), `SALTO` (`\n`); cualquier otro carácter se representa a sí mismo.
2. Para decidir la transición desde un estado con el carácter `c` se busca, **en este orden**: (a) una columna con el carácter exacto `c`; (b) la columna de su clase; (c) la columna `OTRO`, **solo si `c` no es salto de línea** (igual que el `.` de las regex). Si nada aplica, no hay transición y el autómata se detiene.
3. Cada estado es de uno de tres tipos: **no final**, **final de token** (`*`, produce un `TipoToken`) o **final de error** (`✗`, produce un código de diagnóstico). Formalmente es un AFD cuyos estados finales están etiquetados con lo que se reconoció, la misma idea que usan los generadores tipo *lex*.
4. **Resultado del AFD** = el prefijo **más largo** que termina en un estado final (de token o de error). Si nunca pasó por un estado final, no reconoce nada (longitud 0).

---

## 5. Algoritmo de reconocimiento: coincidencia más larga y prioridad

En cada posición `p` del texto (después de saltar espacios):

1. Se ejecutan los cuatro AFD desde `p`, en el orden de `AUTOMATAS`: **comentario, cadena, número, identificador**.
2. Se consulta la tabla de símbolos fijos (2 caracteres, luego 1).
3. **Gana el candidato de mayor longitud** (*maximal munch*). En caso de empate gana el primero en el orden anterior (**prioridad**).
4. Si ningún candidato reconoce nada: el carácter en `p` es desconocido → `LEX-001`, se consume **un** carácter.
5. Postproceso del ganador: identificador ∈ `PALABRAS_RESERVADAS` → `PALABRA_RESERVADA`; identificador con más de 32 caracteres → `LEX-005`.

*Nota honesta sobre la prioridad:* en FlowLang 1.0 los candidatos empiezan por caracteres distintos, salvo `/`, que se resuelve por longitud; por tanto hoy **nunca hay empates**. La regla de prioridad existe para que el comportamiento siga definido cuando se agregue un patrón nuevo.

| Entrada | Tokens | Por qué |
|---|---|---|
| `a>=b` | `a` · `>=` · `b` | `>=` (2) gana a `>` (1) |
| `a>b` | `a` · `>` · `b` | no existe `>b` |
| `a= =b` | `a` · `=` · `=` · `b` | el espacio separa: dos asignaciones |
| `<=<==` | `<=` · `<=` · `=` | siempre el más largo desde la posición actual |
| `!x!=y` | `!` · `x` · `!=` · `y` | |
| `a/b` | `a` · `/` · `b` | el AFD de comentario no acepta `/b` |
| `a // c` | `a` · comentario | `// c` (4) gana a `/` (1) |
| `si2 sino` | identificador `si2` · reservada `sino` | el identificador se lee completo antes de consultar reservadas |

---

## 6. Posiciones

- **Línea y columna empiezan en 1.** La posición de un token es la de su **primer carácter**.
- La columna cuenta **caracteres** (puntos de código): un tabulador cuenta 1, una `ñ` cuenta 1.
- Solo `\n` cambia de línea. Los finales `\r\n` y `\r` se normalizan a `\n` al cargar el archivo.
- Un comentario de bloque de varias líneas actualiza la línea y la columna de los tokens siguientes: en `/* a⏎ b */ c`, el token `c` está en línea 2, columna 7.
- Relación con el editor Tk: índice de inicio = `"{linea}.{columna-1}"`; fin = inicio `+ len(lexema) chars`.

---

## 7. Errores léxicos y recuperación (modo pánico)

Principio: **el analizador nunca se detiene en el primer error.** Por cada error (a) registra un diagnóstico, (b) emite un token `ERROR` con el lexema inválido y (c) descarta ese lexema y continúa con el carácter siguiente.

| Situación | Qué se descarta (lexema del token `ERROR`) | Dónde se reanuda |
|---|---|---|
| Carácter desconocido (`LEX-001`) | Ese único carácter. Varios seguidos producen **un diagnóstico por carácter** | Carácter siguiente |
| Cadena sin cerrar (`LEX-002`) | Desde `"` hasta el final de la línea (sin el salto) | Línea siguiente |
| Número mal formado (`LEX-003`) | La secuencia completa de dígitos, letras, `_` y `.` | Primer carácter fuera de la secuencia |
| Identificador inválido (`LEX-004`) | Igual que el anterior | Igual |
| Identificador demasiado largo (`LEX-005`) | El identificador completo | Carácter siguiente |
| Escape inválido (`LEX-006`) | La cadena completa, hasta su comilla de cierre. **Un diagnóstico por cada escape inválido**, situado en su `\`, con lexema de 2 caracteres (`\q`) | Después de la comilla de cierre |
| Comentario de bloque sin cerrar (`LEX-007`) | Desde `/*` hasta el fin del archivo | Fin del análisis |

Una barra invertida al final de la línea (`"abc\`⏎) no es un escape: se informa solo `LEX-002`.

---

## 8. Cadena de entrada válida

**Definición.** La *cadena de entrada* es el contenido completo del archivo: un programa FlowLang. Es **válida** si y solo si cumple las dos condiciones:

1. **Validez léxica** (análisis léxico): tiene **cero diagnósticos `LEX-…`**, es decir, el texto se descompone por completo en tokens de las categorías 1–11.
2. **Buena formación estructural** (comprobación sintáctica ligera): tiene **cero diagnósticos `SIN-…`**.

La interfaz muestra los dos veredictos por separado («Léxico: válido / Estructura: válida») y el global.

### 8.1 Veredicto por línea
Como el enunciado habla de «cadenas de entrada» en plural, además del veredicto global se informa el **veredicto léxico de cada línea**: una línea es *léxicamente inválida* si en ella comienza al menos un diagnóstico `LEX-…`. Se muestra como marca en el margen del editor y como lista en la consola.

### 8.2 Comprobaciones estructurales (clasificadas como **sintácticas**, no léxicas)
Las realiza `core/validador.py` sobre los tokens **significativos**, siempre, haya o no errores léxicos:

| Regla | Diagnóstico |
|---|---|
| E1. El programa tiene al menos un token significativo | `SIN-001` |
| E2. El primer token significativo es la palabra reservada `inicio` | `SIN-002` |
| E3. El último token significativo es la palabra reservada `fin` | `SIN-003` |
| E4. Los pares `( )` y `{ }` están balanceados y bien anidados | `SIN-004`, `SIN-005`, `SIN-006` |

- Si falla E1 no se evalúan las demás.
- E4 usa una **pila** (apertura → se apila; cierre → debe coincidir con la cima). *Apunte teórico:* el balance de paréntesis **no es un lenguaje regular**, ningún AFD puede comprobarlo; necesita memoria tipo pila (autómata de pila). Por eso está en el validador y no en el lexer.
- Detalle de E4: cierre con la pila vacía → `SIN-004` en el cierre. Cierre que no corresponde a la cima → `SIN-006` en el cierre, y se desapila la cima. Al terminar, cada apertura que quede en la pila → `SIN-005` en esa apertura.
- Los diagnósticos estructurales se devuelven ordenados por (línea, columna).
- No se comprueba nada más (ni `;`, ni la forma de las instrucciones): eso sería un analizador sintáctico, fuera del alcance.

---

## 9. Qué se instala en la tabla de símbolos

Se instalan los tokens cuyas categorías están en `CATEGORIAS_EN_TABLA`: **palabras reservadas, identificadores, enteros, decimales y cadenas**. La clave es el **lexema** (para una cadena, incluye las comillas, de modo que `"x"` y `x` son entradas distintas). Un lexema repetido **no** crea otra entrada: se añade una aparición.

| Atributo | Contenido |
|---|---|
| `lexema` | Clave |
| `categoria` | `TipoToken` |
| `tipo_dato` | Identificador: tipo con el que se declara (ver regla abajo) o vacío. `ENTERO` → `numero`; `DECIMAL` → `decimal`; `CADENA` → `texto`; `verdadero`/`falso` → `booleano` (constante `TIPO_DATO_BOOLEANO`); resto vacío |
| `valor` | `ENTERO` → `int`; `DECIMAL` → `float`; `CADENA` → texto sin comillas y con los escapes interpretados; `verdadero`/`falso` → `True`/`False`; resto vacío |
| `linea_declaracion` | Línea de la declaración (solo identificadores declarados) |
| `apariciones` | Lista de (línea, columna) de cada uso, en orden |
| `valor_hash` | Resultado de la función hash sobre el lexema |
| cubeta | `valor_hash mod capacidad` (se calcula; cambia al redimensionar) |

**Regla de declaración** (única regla contextual): un `IDENTIFICADOR` cuyo token significativo anterior es una palabra reservada de `TIPOS_DE_DATO` (`numero`, `decimal`, `texto`, `booleano`, `dispositivo`) queda anotado con ese `tipo_dato` y esa `linea_declaracion`. Si el identificador ya tenía declaración, se conserva la primera (detectar la redeclaración sería análisis semántico).

Precisión (D-27): la declaración se anota la primera vez que el identificador aparece **declarado**, aunque ya se hubiera usado antes: en `x = 1; numero x;` la entrada `x` queda con tipo `numero` y la línea de la declaración.

Operadores y delimitadores no se instalan por defecto porque no tienen atributos que otra fase necesite; basta añadir sus categorías a `CATEGORIAS_EN_TABLA` para instalarlos.

---

## 10. Catálogo de diagnósticos

Todos tienen: **código**, **tipo**, **título**, **mensaje** (con `{lexema}` sustituido), **sugerencia**, **línea**, **columna** y **lexema**. Los de archivo no tienen posición (línea 0, columna 0).

### 10.1 Léxicos

| Código | Título | Mensaje | Sugerencia |
|---|---|---|---|
| `LEX-001` | Carácter no reconocido | El carácter '{lexema}' no pertenece al alfabeto de FlowLang. | Elimínelo o reemplácelo por un símbolo válido. *(Se sustituye por una sugerencia específica si el carácter está en `SUGERENCIAS_CARACTER`: `&`, `\|`, `'`, `.`, `#`, `[`, `]`, `:`.)* |
| `LEX-002` | Cadena sin cerrar | La cadena {lexema} no tiene comilla de cierre en la misma línea. | Agregue `"` al final de la cadena; las cadenas no pueden ocupar varias líneas. |
| `LEX-003` | Número mal formado | '{lexema}' no es un número válido. | Un decimal necesita dígitos a ambos lados de un único punto, por ejemplo 3.14 o 0.5. |
| `LEX-004` | Identificador inválido | '{lexema}' no es válido: un identificador no puede comenzar con un dígito. | Comience el nombre con una letra o `_`; si quería un número, quite las letras. |
| `LEX-005` | Identificador demasiado largo | El identificador '{lexema}' supera el máximo de 32 caracteres. | Use un nombre más corto. |
| `LEX-006` | Secuencia de escape inválida | La secuencia '{lexema}' no es un escape válido dentro de una cadena. | Escapes permitidos: `\n`, `\t`, `\"` y `\\`. |
| `LEX-007` | Comentario de bloque sin cerrar | El comentario que comienza con /* nunca se cierra. | Agregue `*/` al final del comentario. |

Sugerencias específicas de `LEX-001`: `&` → «¿Quiso escribir `&&`?»; `|` → «¿Quiso escribir `||`?»; `'` → «Las cadenas se escriben con comillas dobles: "texto".»; `.` → «El punto solo se usa dentro de un número decimal, como 3.14.»; `#` → «Los comentarios se escriben con `//` o `/* */`.»; `[` y `]` → «FlowLang no tiene corchetes; use paréntesis o llaves.»; `:` → «Las instrucciones terminan con `;`.»

### 10.2 Estructurales (sintácticos ligeros)

| Código | Título | Mensaje | Sugerencia | Posición |
|---|---|---|---|---|
| `SIN-001` | Programa vacío | El programa no contiene ninguna instrucción. | Escriba un programa entre `inicio` y `fin`. | 1:1 |
| `SIN-002` | Falta `inicio` | El programa debe comenzar con la palabra reservada `inicio`; se encontró '{lexema}'. | Agregue `inicio` como primera palabra. | Primer token significativo |
| `SIN-003` | Falta `fin` | El programa debe terminar con la palabra reservada `fin`; se encontró '{lexema}'. | Agregue `fin` como última palabra. | Último token significativo |
| `SIN-004` | Cierre sin apertura | El símbolo '{lexema}' no tiene apertura correspondiente. | Elimine el símbolo o agregue su apertura. | El cierre |
| `SIN-005` | Apertura sin cierre | El símbolo '{lexema}' nunca se cierra. | Agregue el símbolo de cierre correspondiente. | La apertura |
| `SIN-006` | Cierre no correspondiente | El símbolo '{lexema}' no corresponde con la última apertura pendiente. | Revise el orden de paréntesis y llaves. | El cierre |

### 10.3 De archivo

| Código | Título | Mensaje | Sugerencia |
|---|---|---|---|
| `ARC-001` | Archivo inexistente | No se encontró el archivo '{lexema}'. | Verifique la ruta y el nombre. |
| `ARC-002` | Extensión no soportada | El archivo '{lexema}' no tiene una extensión permitida. | Use un archivo `.flow` o `.txt`. |
| `ARC-003` | Archivo vacío | El archivo '{lexema}' no contiene texto. | Elija un archivo con un programa FlowLang. |
| `ARC-004` | Codificación inválida | El archivo '{lexema}' no está codificado en UTF-8. | Guárdelo como UTF-8 e inténtelo de nuevo. |
| `ARC-005` | Error de lectura o escritura | No se pudo leer o escribir '{lexema}'. | Revise los permisos y que no sea una carpeta. |
| `ARC-006` | Archivo demasiado grande | El archivo '{lexema}' supera el tamaño máximo de 1 MB. | Divida el archivo o use uno más pequeño. |

Orden de comprobación al cargar: `ARC-001` → `ARC-005` (si es carpeta) → `ARC-002` → `ARC-006` → lectura (`ARC-005`) → decodificación (`ARC-004`) → `ARC-003` (vacío o solo espacios).

---

## 11. Gramática informativa (no implementada)

Solo para dar contexto al lenguaje. **SmartLex Studio no la comprueba** (salvo §8.2).

```ebnf
programa     = "inicio" { instruccion } "fin" ;
instruccion  = declaracion | asignacion | condicional | ciclo | accion ;
declaracion  = tipo IDENTIFICADOR [ "=" expresion ] ";" ;
tipo         = "numero" | "decimal" | "texto" | "booleano" | "dispositivo" ;
asignacion   = IDENTIFICADOR "=" expresion ";" ;
condicional  = "si" "(" expresion ")" bloque [ "sino" bloque ] ;
ciclo        = "mientras" "(" expresion ")" bloque ;
bloque       = "{" { instruccion } "}" ;
accion       = ( "mostrar" | "esperar" ) expresion ";"
             | ( "leer" | "activar" | "desactivar" ) IDENTIFICADOR ";" ;
```

---

## 12. Archivos de ejemplo y resultados esperados

Los tres archivos de `ejemplos/` ya están creados y son **parte del contrato**: no deben modificarse sin actualizar esta sección y las pruebas.

### 12.1 `ejemplos/correcto.flow` — válido
- 111 tokens; 0 diagnósticos; `es_valida = True`.
- Por categoría: 21 reservadas, 21 identificadores, 9 enteros, 3 decimales, 4 cadenas, 6 aritméticos, 5 relacionales, 4 lógicos, 7 asignaciones, 29 delimitadores, 2 comentarios.
- Primer token significativo: `inicio` en 2:1. Último: `fin` en 29:1.
- Tabla de símbolos (capacidad inicial 17): **36 entradas**, 2 redimensionados, capacidad final 79.
- Colisiones — son dos medidas distintas y se muestran las dos:
  - **Colisiones al insertar: 14.** Contador histórico: cuántas veces un lexema nuevo llegó a una cubeta que ya estaba ocupada *en el momento de insertarlo* (con la capacidad que la tabla tenía entonces: 17, luego 37, luego 79).
  - **Colisiones en la tabla final: 7.** Entradas que hoy comparten cubeta con otra anterior = entradas − cubetas ocupadas = 36 − 29. Es menor porque cada redimensionado reparte de nuevo las entradas y deshace colisiones antiguas.

### 12.2 `ejemplos/incorrecto.flow` — inválido
57 tokens (13 de tipo `ERROR`), 18 entradas en la tabla, 15 diagnósticos:

| # | Código | Línea | Col | Lexema |
|---|---|---|---|---|
| 1 | `LEX-004` | 2 | 12 | `2pi` |
| 2 | `LEX-003` | 2 | 18 | `3.14.15` |
| 3 | `LEX-003` | 3 | 21 | `5.` |
| 4 | `LEX-002` | 4 | 20 | `"Hola mundo;` |
| 5 | `LEX-006` | 5 | 21 | `\q` |
| 6 | `LEX-001` | 6 | 24 | `@` |
| 7 | `LEX-001` | 7 | 29 | `&` |
| 8 | `LEX-005` | 8 | 12 | `identificador_demasiado_largo_para_flowlang` |
| 9 | `LEX-001` | 10 | 17 | `'` |
| 10 | `LEX-001` | 10 | 23 | `'` |
| 11 | `LEX-001` | 12 | 19 | `$` |
| 12 | `LEX-001` | 12 | 21 | `#` |
| 13 | `LEX-007` | 13 | 1 | desde `/* comentario sin cerrar` hasta el fin del archivo |
| 14 | `SIN-005` | 9 | 8 | `(` |
| 15 | `SIN-003` | 12 | 22 | `;` |

Líneas léxicamente inválidas: 2, 3, 4, 5, 6, 7, 8, 10, 12, 13.

### 12.3 `ejemplos/casos_limite.flow` — válido
118 tokens, 0 diagnósticos. Cubre: identificador de exactamente 32 caracteres, `_` solo, `Inicio` como identificador, `si2`, cadena vacía, los cuatro escapes, `//` y `/* */` dentro de una cadena, `/**/`, operadores pegados sin espacios (línea 15: `b = si2 >= _ && si2 <= Inicio || ! b == falso != verdadero ;` → 17 tokens) y comentario final sin salto de línea.

---

## 13. Función hash (resumen; diseño completo en `02_arquitectura.md` §6)

`h(lexema)`: se parte de 0 y por cada carácter `c` se hace `h = (h · 31 + código(c)) mod 2³²`. Cubeta = `h mod capacidad`.

| Lexema | `h` | Cubeta con capacidad 17 |
|---|---|---|
| `x` | 120 | 1 |
| `si` | 115·31 + 105 = 3670 | 15 |
| `10` | 49·31 + 48 = 1567 | 3 |
| `temperatura` | 321701232 | 15 (colisiona con `si`) |
| `riego` | 108509814 | 4 |
| `activo` | 2872016656 | 4 (colisiona con `riego`) |
| `total` | 110549828 | 1 (colisiona con `x`) |
