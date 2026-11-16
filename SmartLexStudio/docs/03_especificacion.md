# 03 · Especificación de FlowLang 2.0

Autor: architect-fable. Este documento es el **contrato del lenguaje**. Todo lo que aquí se define como dato vive en `config/reglas.py`; los algoritmos que lo interpretan viven en `core/`.
FlowLang 2.0 **sustituye** a FlowLang 1.0 (sintaxis de llaves, `inicio … fin`): no hay modo de compatibilidad. Las diferencias están resumidas en §14.
Todas las tablas de transición y todos los resultados con posiciones de este documento fueron comprobados con un prototipo desechable (no forma parte del proyecto) antes de escribirlos, incluida la equivalencia regex ↔ AFD sobre 2 000 719 cadenas.

---

## 1. Qué es FlowLang

FlowLang es un lenguaje educativo para **describir automatizaciones de un invernadero** (riego, ventilación, alarmas). Desde la versión 2.0 se escribe como **pseudocódigo en español al estilo de PSeInt**: bloques que se abren y se cierran con palabras (`Si … FinSi`), asignación con `<-`, operadores lógicos con palabras (`Y`, `O`, `NO`). Conserva lo propio de la automatización: el tipo `Dispositivo`, las acciones `Activar`, `Desactivar` y `Esperar`, y los **literales con unidad** (`10s`, `30C`, `40%`).

```flow
// Riego automatico
Algoritmo riego
    Definir temperatura, humedad Como Real;
    Definir bomba Como Dispositivo;
    Leer temperatura, humedad;
    Si temperatura >= 30C Y humedad < 40% Entonces
        Activar bomba;
        Esperar 10s;
        Escribir "Regando\n";
    SiNo
        Desactivar bomba;
    FinSi
FinAlgoritmo
```

Características generales:

- **No distingue mayúsculas de minúsculas en las palabras**: `Si`, `si` y `SI` son la misma palabra reservada; `Bomba` y `bomba` son el mismo identificador (como en PSeInt). **Sí** las distingue dentro de las cadenas y en los símbolos de unidad (`30C` es una temperatura, `30c` no; §3.3).
- **Alfabeto de los lexemas**: ASCII. Las letras acentuadas y la `ñ` solo se admiten **dentro de cadenas y comentarios**. Por eso las palabras se escriben sin tilde: `Segun`, `Logico`.
- **Formato libre**: espacios, tabuladores y saltos de línea separan lexemas y no tienen otro significado. El `;` al final de una instrucción es un delimitador más (el analizador léxico no exige ponerlo).
- Archivo fuente: texto UTF-8 con extensión `.flow` (también se acepta `.txt`).

### 1.1 Alcance: qué se analiza y qué no

| Nivel | Pregunta que responde | ¿Lo hace SmartLex Studio? |
|---|---|---|
| **Léxico** | ¿Cada lexema pertenece a alguna categoría de token? | **Sí, completo** (objeto del proyecto). Diagnósticos `LEX-…` |
| **Sintáctico** | ¿Los tokens están en un orden permitido por la gramática? | **Solo las comprobaciones estructurales de §8.2**: marco `Algoritmo … FinAlgoritmo`, paréntesis balanceados y **bloques bien cerrados y anidados**. Están declaradas explícitamente como *estructurales*, no léxicas. Diagnósticos `SIN-…`. No hay parser. |
| **Semántico** | ¿El programa tiene sentido (tipos, variables declaradas, redeclaraciones)? | **No.** Único uso de contexto: anotar en la tabla de símbolos el tipo con que se declara un identificador (§9). No se reporta ningún error semántico. |

Ejemplos de lo que **no** es error para esta herramienta: `Definir x Como Entero; x <- "hola";` (semántico), `x <- <- 3;` o `Si x Entonces` sin condición completa (sintáctico), `Si a Hacer … FinSi` (falta `Entonces`: sintáctico), usar una variable no declarada (semántico), `a == b` (son dos `=` seguidos: sintáctico).

---

## 2. Categorías de token

`TipoToken` (enumeración en `core/modelos.py`), **15 miembros** (12 de la versión 1.0 más `DURACION`, `TEMPERATURA` y `PORCENTAJE`):

| # | Categoría | Ejemplos | ¿Va a la tabla de símbolos? |
|---|---|---|---|
| 1 | `PALABRA_RESERVADA` | `Algoritmo` `Si` `FinSi` `Escribir` | Sí |
| 2 | `IDENTIFICADOR` | `temperatura` `_x1` | Sí |
| 3 | `ENTERO` | `0` `28` `007` | Sí |
| 4 | `DECIMAL` | `45.5` `0.0` | Sí |
| 5 | `CADENA` | `"Regando\n"` | Sí |
| 6 | `DURACION` | `500ms` `10s` `1.5m` `2h` | Sí |
| 7 | `TEMPERATURA` | `30C` `22.5C` | Sí |
| 8 | `PORCENTAJE` | `40%` `0.5%` | Sí |
| 9 | `OPERADOR_ARITMETICO` | `+ - * / ^` `MOD` | No (configurable) |
| 10 | `OPERADOR_RELACIONAL` | `= <> < <= > >=` | No (configurable) |
| 11 | `OPERADOR_LOGICO` | `Y` `O` `NO` | No (configurable) |
| 12 | `ASIGNACION` | `<-` | No (configurable) |
| 13 | `DELIMITADOR` | `( ) , ; :` | No (configurable) |
| 14 | `COMENTARIO` | `// …` `/* … */` | No |
| 15 | `ERROR` | `3.4.5` `10x` `@` `"sin cerrar` | No |

Valores para mostrar (`TipoToken.X.value`) de los tres miembros nuevos: `"Duración"`, `"Temperatura"`, `"Porcentaje"`. En el `enum` se declaran después de `CADENA`.

- Los **espacios en blanco** (` `, `\t`, `\r`, `\n`) se descartan: no producen token.
- `COMENTARIO` sí produce token (para resaltarlo y explicarlo) pero es **no significativo**: el validador y la tabla de símbolos lo ignoran.
- `ERROR` es el token que acompaña a todo diagnóstico léxico: contiene el lexema inválido completo, para poder marcarlo en el editor.
- Token **significativo** = cualquier token que no sea `COMENTARIO` ni `ERROR`.

---

## 3. Definición formal de cada categoría

Notación: `L = [A-Za-z]` (52 letras ASCII), `D = [0-9]`. Las expresiones regulares usan la sintaxis del módulo `re` de Python y describen el **lexema completo**.

**Normalización.** `normalizar(w)` = `w` con sus letras en minúscula. Dos palabras son «la misma» si sus formas normalizadas son iguales. Es la única función que conoce la regla de mayúsculas (`core/modelos.py`); el lexer, el validador y la tabla de símbolos la usan.

### 3.1 Palabras reservadas (36)

Cada palabra tiene una **forma canónica** (la que se muestra en la documentación, en el panel *Lenguaje* y en los mensajes) y se reconoce escrita con cualquier combinación de mayúsculas.

| Grupo | Forma canónica | Descripción (texto de `PALABRAS_RESERVADAS`) |
|---|---|---|
| Programa | `Algoritmo` | Marca el comienzo del programa; va seguida de su nombre. |
| | `FinAlgoritmo` | Marca el final del programa. |
| Declaración | `Definir` | Declara una o varias variables separadas por comas. |
| | `Como` | Separa los nombres declarados de su tipo de dato. |
| Tipos de dato | `Entero` | Tipo de dato: número entero. |
| | `Real` | Tipo de dato: número con parte decimal. |
| | `Cadena` | Tipo de dato: texto entre comillas. |
| | `Logico` | Tipo de dato: Verdadero o Falso. |
| | `Dispositivo` | Tipo de dato: un aparato que se puede activar o desactivar. |
| Valores lógicos | `Verdadero` | Valor lógico verdadero. |
| | `Falso` | Valor lógico falso. |
| Condicional | `Si` | Abre una condición; se cierra con FinSi. |
| | `Entonces` | Separa la condición del Si de sus instrucciones. |
| | `SiNo` | Alternativa de un Si; solo puede ir dentro de un Si. |
| | `FinSi` | Cierra el bloque Si. |
| Ciclo Mientras | `Mientras` | Abre un ciclo que se repite mientras se cumpla la condición; se cierra con FinMientras. |
| | `Hacer` | Separa el encabezado de un ciclo o de un Segun de sus instrucciones. |
| | `FinMientras` | Cierra el bloque Mientras. |
| Ciclo Para | `Para` | Abre un ciclo con contador; se cierra con FinPara. |
| | `Hasta` | Límite de un Para; seguida de Que, cierra un Repetir. |
| | `Con` | Primera palabra de «Con Paso». |
| | `Paso` | Incremento del contador de un Para. |
| | `FinPara` | Cierra el bloque Para. |
| Ciclo Repetir | `Repetir` | Abre un ciclo que se ejecuta al menos una vez; se cierra con Hasta Que. |
| | `Que` | Segunda palabra de «Hasta Que». |
| Selección | `Segun` | Abre una selección entre varios casos; se cierra con FinSegun. |
| | `Caso` | Introduce un valor de un Segun. |
| | `De` | Primera palabra de «De Otro Modo». |
| | `Otro` | Segunda palabra de «De Otro Modo». |
| | `Modo` | Tercera palabra de «De Otro Modo». |
| | `FinSegun` | Cierra el bloque Segun. |
| Entrada y salida | `Escribir` | Muestra uno o varios valores al usuario. |
| | `Leer` | Lee el valor de un sensor o de una entrada. |
| Acciones | `Activar` | Enciende un dispositivo. |
| | `Desactivar` | Apaga un dispositivo. |
| | `Esperar` | Detiene el programa durante un tiempo. |

- Definición: conjunto finito de cadenas `R`, cerrado por cambio de mayúsculas. Regex: `(?i:algoritmo|finalgoritmo|…|esperar)` (se **deriva** del diccionario).
- **Reconocimiento**: no tienen AFD propio. Se reconoce un identificador con su AFD y luego se consulta `normalizar(lexema)` en `FORMA_CANONICA`; si está, el tipo pasa a `PALABRA_RESERVADA`. Así `si2`, `sinope`, `nota` y `modo_riego` son identificadores (coincidencia más larga) y agregar una palabra es añadir una entrada al diccionario.
- El token conserva el **lexema tal como se escribió** (`FINSI`); la forma canónica (`FinSi`) se obtiene con `FORMA_CANONICA[normalizar(lexema)]`.
- **Palabras compuestas** («Hasta Que», «Con Paso», «De Otro Modo»): son **tokens separados**, uno por palabra. No hay tokens que contengan espacios. La secuencia `Hasta` + `Que` la interpreta el validador (§8.2), no el lexer.
- Consecuencia asumida: `modo`, `otro`, `de`, `paso`, `con`, `que`, `como`, `caso`, `hasta`, `hacer`, `real`, `cadena`… no pueden usarse como nombres de variable (use `modo_riego`). `y`, `o`, `no` y `mod` tampoco: son operadores (§3.6).
- `Notificar` y `Funcion`/`FinFuncion` **no** son reservadas a propósito: son las modificaciones de ejemplo para la sustentación.

### 3.2 Identificadores

- Definición: `ID = { w ∈ (L ∪ D ∪ {_})⁺ : el primer símbolo de w ∈ L ∪ {_} y normalizar(w) ∉ normalizar(R ∪ OP) }`, con `|w| ≤ 32` (`OP` = operadores con letras de §3.6).
- Regex: `[A-Za-z_][A-Za-z0-9_]*`
- **No distinguen mayúsculas**: `si2`, `Si2` y `SI2` son el mismo identificador. Motivo: es la regla de PSeInt y evita que un lenguaje con `Si` = `si` tenga a la vez `Bomba` ≠ `bomba`. El token conserva el lexema original; la igualdad se decide en la tabla de símbolos por la clave normalizada (§9).
- AFD (`AFD_IDENTIFICADOR`), estado inicial `q0`, aceptación `{q1}` (**sin cambios** respecto de 1.0; la clase `letra` ya incluía mayúsculas y minúsculas):

| Estado | letra | dígito | `_` | otro |
|---|---|---|---|---|
| → q0 | q1 | — | q1 | — |
| * q1 `IDENTIFICADOR` | q1 | q1 | q1 | — |

(`—` = no hay transición: el autómata se detiene.)

- Longitud máxima: `LONGITUD_MAXIMA_IDENTIFICADOR = 32`. Un identificador más largo se reconoce completo y se reporta `LEX-005`. *Nota honesta:* el límite de longitud es una propiedad regular, pero codificarlo exigiría 32 estados; se comprueba con `len()` después del AFD. La comprobación de longitud va **antes** que la consulta de palabras reservadas.

### 3.3 Números y medidas (literales con unidad)

Un solo autómata reconoce cinco categorías. `N = D⁺ ( . D⁺ )?` es «un número» (entero o decimal).

| Categoría | Definición | Regex | Tipo de dato | Valor que se guarda |
|---|---|---|---|---|
| `ENTERO` | `D⁺` | `[0-9]+` | `Entero` | `int` (`007` vale 7) |
| `DECIMAL` | `D⁺ . D⁺` | `[0-9]+\.[0-9]+` | `Real` | `float` |
| `DURACION` | `N (ms ∣ s ∣ m ∣ h)` | `[0-9]+(?:\.[0-9]+)?(?:ms\|s\|m\|h)` | `Duracion` | milisegundos |
| `TEMPERATURA` | `N C` | `[0-9]+(?:\.[0-9]+)?C` | `Temperatura` | grados Celsius |
| `PORCENTAJE` | `N %` | `[0-9]+(?:\.[0-9]+)?%` | `Porcentaje` | el número (40 para `40%`) |

- Unidades (`UNIDADES_DURACION_MS`): `ms` = 1, `s` = 1 000, `m` (minuto) = 60 000, `h` = 3 600 000 milisegundos. `C` = grados Celsius. `%` = porcentaje.
- La unidad va **pegada** al número: `10s` es un token; `10 s` son dos (`ENTERO` e `IDENTIFICADOR`); `40 %` es `ENTERO` y un `%` suelto (`LEX-001`).
- **Las unidades sí distinguen mayúsculas** (son símbolos, no palabras, igual que en el Sistema Internacional `ms` ≠ `Ms`): `30C` es temperatura; `30c`, `10S` y `5H` son `LEX-008`.
- No hay signo en el literal: `-5C` son dos tokens (`-` y `5C`). No hay notación científica.
- `Duracion`, `Temperatura` y `Porcentaje` son **etiquetas de tipo de dato** para la tabla de símbolos, **no** palabras reservadas: `temperatura` sigue siendo un identificador válido.

**AFD mínimo** del lenguaje de los cinco tokens válidos (lo que se pide en teoría), 8 estados:

| Estado | dígito | `.` | `m` | `s` | `h` | `C` | `%` |
|---|---|---|---|---|---|---|---|
| → q0 | q1 | — | — | — | — | — | — |
| * q1 `ENTERO` | q1 | q2 | q7 | q8 | q8 | q9 | q10 |
| q2 | q3 | — | — | — | — | — | — |
| * q3 `DECIMAL` | q3 | — | q7 | q8 | q8 | q9 | q10 |
| * q7 `DURACION` (leyó `m`) | — | — | — | q8 | — | — | — |
| * q8 `DURACION` | — | — | — | — | — | — | — |
| * q9 `TEMPERATURA` | — | — | — | — | — | — | — |
| * q10 `PORCENTAJE` | — | — | — | — | — | — | — |

q8, q9 y q10 no se pueden fusionar aunque tengan las mismas transiciones: cada uno etiqueta una categoría distinta.

**AFD implementado** (`AFD_NUMERO`, nombre para mostrar **«AFD de números y medidas»**): el mínimo más cuatro **estados de error** (q4, q5, q6→q4, q11) y q2 marcado como error. Sirven para que un número mal escrito se consuma **como un solo lexema** y se informe con precisión, en vez de partirse en trozos que producirían errores en cascada. «otra letra» = cualquier letra sin columna propia en esa fila.

| Estado | dígito | `.` | `m` | `s` | `h` | `C` | `%` | otra letra | `_` | Resultado si el autómata termina aquí |
|---|---|---|---|---|---|---|---|---|---|---|
| → q0 | q1 | q6 | — | — | — | — | — | — | — | (no acepta) |
| * q1 | q1 | q2 | q7 | q8 | q8 | q9 | q10 | q11 | q5 | token `ENTERO` |
| ✗ q2 | q3 | q4 | q4 | q4 | q4 | q4 | — | q4 | q4 | error `LEX-003` (falta la parte decimal: `3.`) |
| * q3 | q3 | q4 | q7 | q8 | q8 | q9 | q10 | q11 | q4 | token `DECIMAL` |
| ✗ q4 | q4 | q4 | q4 | q4 | q4 | q4 | — | q4 | q4 | error `LEX-003` (número mal formado: `3.4.5`, `.5`, `10s.5`) |
| ✗ q5 | q5 | q5 | q5 | q5 | q5 | q5 | — | q5 | q5 | error `LEX-004` (identificador que empieza con dígito: `2pi_r`, `1_000`, `10s5`) |
| q6 | q4 | — | — | — | — | — | — | — | — | (no acepta: un `.` suelto es `LEX-001`) |
| * q7 | q5 | q4 | q11 | q8 | q11 | q11 | — | q11 | q5 | token `DURACION` (`5m`) |
| * q8 | q5 | q4 | q11 | q11 | q11 | q11 | — | q11 | q5 | token `DURACION` (`10s`, `500ms`, `2h`) |
| * q9 | q5 | q4 | q11 | q11 | q11 | q11 | — | q11 | q5 | token `TEMPERATURA` |
| * q10 | — | — | — | — | — | — | — | — | — | token `PORCENTAJE` |
| ✗ q11 | q5 | q4 | q11 | q11 | q11 | q11 | — | q11 | q5 | error `LEX-008` (unidad desconocida: `10x`, `30c`, `5min`, `2pi`) |

En `config/reglas.py` las filas q1 y q3 comparten sus siete columnas de unidad mediante un diccionario común (`TRANSICIONES_UNIDAD = {"m": "q7", "s": "q8", "h": "q8", "C": "q9", "%": "q10", LETRA: "q11"}`), de modo que añadir una unidad es una sola línea. En q2, q4, q5, q8, q9 y q11 las columnas `m`, `s`, `h`, `C` y «otra letra» son la misma entrada `LETRA` (en q7 solo `s` tiene columna propia).

**Regla sin ambigüedad entre `LEX-003`, `LEX-004` y `LEX-008`** (consecuencia directa de la tabla):

1. Un **punto fuera de lugar** (segundo punto, punto sin dígitos a un lado, punto después de letras) → `LEX-003`, *número mal formado*.
2. **Letras** después del número que **no forman una unidad** → `LEX-008`, *unidad desconocida* — mientras solo haya letras.
3. Si después de las letras (o justo después de un entero) aparece un **dígito o `_`**, el lexema tiene forma de nombre → `LEX-004`, *identificador inválido*.
4. q4 y q5 son **absorbentes**: el primer diagnóstico definitivo se mantiene hasta el final del lexema. q11 es provisional (puede pasar a q4 o q5).

| Lexema | Recorrido | Resultado |
|---|---|---|
| `28` | q0 q1 q1 | `ENTERO` |
| `45.5` | q0 q1 q1 q2 q3 | `DECIMAL` |
| `10s` | q0 q1 q1 q8 | `DURACION` |
| `500ms` | q0 q1 q1 q1 q7 q8 | `DURACION` |
| `5m` | q0 q1 q7 | `DURACION` |
| `1.5s` | q0 q1 q2 q3 q8 | `DURACION` |
| `30C` | q0 q1 q1 q9 | `TEMPERATURA` |
| `22.5C` | q0 q1 q1 q2 q3 q9 | `TEMPERATURA` |
| `40%` | q0 q1 q1 q10 | `PORCENTAJE` |
| `3.` | q0 q1 q2 | `LEX-003` |
| `3.4.5` | q0 q1 q2 q3 q4 q4 | `LEX-003` |
| `.5` | q0 q6 q4 | `LEX-003` |
| `10s.5` | q0 q1 q1 q8 q4 q4 | `LEX-003` |
| `1.5_` | q0 q1 q2 q3 q4 | `LEX-003` |
| `10x` | q0 q1 q1 q11 | `LEX-008` |
| `30c` | q0 q1 q1 q11 | `LEX-008` |
| `5min` | q0 q1 q7 q11 q11 | `LEX-008` |
| `5mss` | q0 q1 q7 q8 q11 | `LEX-008` |
| `2pi` | q0 q1 q11 q11 | `LEX-008` |
| `1.5abc` | q0 q1 q2 q3 q11 q11 q11 | `LEX-008` |
| `2pi_r` | q0 q1 q11 q11 q5 q5 | `LEX-004` |
| `1_000` | q0 q1 q5 q5 q5 q5 | `LEX-004` |
| `10s5` | q0 q1 q1 q8 q5 | `LEX-004` |
| `40%%` | q0 q1 q1 q10 (longitud 3) | `PORCENTAJE` `40%`; el segundo `%` es `LEX-001` |

Cambio respecto de 1.0: `12abc` y `2pi` eran `LEX-004` y `1.5abc` era `LEX-003`; ahora los tres son `LEX-008`, cuya sugerencia cubre las dos hipótesis (unidad mal escrita o nombre que empieza con dígito).

### 3.4 Cadenas

**Sin cambios** respecto de 1.0.

- Delimitadas por **comillas dobles**, **en una sola línea**. Dentro se admite cualquier carácter excepto `"`, `\` y salto de línea, o una secuencia de escape válida. Las mayúsculas se conservan (`"Hola"` ≠ `"hola"`).
- Escapes válidos (`ESCAPES_VALIDOS`): `\n` (salto), `\t` (tabulador), `\"` (comilla), `\\` (barra invertida).
- Las comillas simples **no** delimitan cadenas (PSeInt sí las admite): `'` es `LEX-001` con sugerencia. Motivo: un segundo delimitador duplicaría los estados del AFD sin enseñar nada nuevo, y «añadir el literal `'a'`» es un ejercicio de sustentación.
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

**Sin cambios** respecto de 1.0.

- De línea: desde `//` hasta el final de la línea (el salto no forma parte). Regex: `//[^\n]*` — es el comentario de PSeInt.
- De bloque: desde `/*` hasta el primer `*/`; puede ocupar varias líneas; no se anidan. Regex: `/\*(?:[^*]|\*+[^*/])*\*+/` — **extensión de FlowLang** (PSeInt no lo tiene); se conserva porque es el único token de varias líneas y su AFD (el estado «vio `*`») es el más ilustrativo.
- AFD (`AFD_COMENTARIO`):

| Estado | `/` | `*` | otro | salto | Resultado si termina aquí |
|---|---|---|---|---|---|
| → q0 | q1 | — | — | — | (no acepta) |
| q1 | q2 | q3 | — | — | (no acepta: un `/` solo es el operador de división) |
| * q2 (línea) | q2 | q2 | q2 | — | token `COMENTARIO` |
| ✗ q3 (bloque) | q3 | q4 | q3 | q3 | error `LEX-007` (bloque sin cerrar) |
| ✗ q4 (bloque, vio `*`) | q5 | q4 | q3 | q3 | error `LEX-007` |
| * q5 | — | — | — | — | token `COMENTARIO` |

### 3.6 Operadores y delimitadores

**Símbolos fijos** (diccionarios `OPERADORES`, 12 entradas, y `DELIMITADORES`, 5 entradas):

| Categoría | Lexemas |
|---|---|
| `OPERADOR_ARITMETICO` | `+` `-` `*` `/` `^` (potencia) |
| `OPERADOR_RELACIONAL` | `=` (igual) `<>` (distinto) `<` `<=` `>` `>=` |
| `ASIGNACION` | `<-` |
| `DELIMITADOR` | `(` `)` `,` `;` `:` |

- Definición: conjunto finito de cadenas de longitud 1 o 2. Regex: `<-|<=|<>|>=|[-+*/^=<>(),;:]`
- Reconocimiento: consulta en los diccionarios probando **primero los 2 caracteres siguientes y luego 1** (coincidencia más larga). Es un autómata trivial de profundidad 2; no se escribe su tabla porque el diccionario *es* la tabla.
- `=` es **comparación**, no asignación (como en PSeInt). No existe `==`: `a == b` son dos `=` (no es un error léxico). No existen `!=`, `&&`, `||`, `!`.
- `%` **no** es operador: solo existe como sufijo de un porcentaje (`40%`). El resto de la división es `MOD`.
- `:` separa el valor de un `Caso` de sus instrucciones. `{` y `}` ya no pertenecen al lenguaje.

**Operadores escritos con letras** (diccionario `OPERADORES_PALABRA`, 4 entradas; no distinguen mayúsculas):

| Forma canónica | Categoría | Significado |
|---|---|---|
| `Y` | `OPERADOR_LOGICO` | conjunción |
| `O` | `OPERADOR_LOGICO` | disyunción |
| `NO` | `OPERADOR_LOGICO` | negación |
| `MOD` | `OPERADOR_ARITMETICO` | resto de la división entera |

- Regex por categoría: aritmético `[-+*/^]|(?i:mod)`; lógico `(?i:y|o|no)`.
- Reconocimiento: igual que las palabras reservadas. El AFD de identificadores lee la palabra completa y `FORMA_CANONICA[normalizar(lexema)]` la encuentra en `OPERADORES_PALABRA`, que da su categoría. Por eso `Yo`, `nota`, `oro` y `modulo` son identificadores, y `y`, `Y`, `mod`, `Mod` son operadores.
- Son categoría **operador**, no palabra reservada: no entran en la tabla de símbolos por defecto y se resaltan con el color de los operadores.

### 3.7 Espacios en blanco

` ` (espacio), `\t`, `\r`, `\n`. Regex `[ \t\r\n]+`. Se descartan. Cada uno avanza una columna, salvo `\n`, que incrementa la línea y devuelve la columna a 1.

---

## 4. Convención de las tablas de transición

Válida para los cuatro AFD (motor en `core/afd.py`, **sin cambios**):

1. El **alfabeto de entrada** se agrupa en clases: `LETRA` (`A-Z a-z`), `DIGITO` (`0-9`), `SALTO` (`\n`); cualquier otro carácter se representa a sí mismo.
2. Para decidir la transición desde un estado con el carácter `c` se busca, **en este orden**: (a) una columna con el carácter exacto `c`; (b) la columna de su clase; (c) la columna `OTRO`, **solo si `c` no es salto de línea** (igual que el `.` de las regex). Si nada aplica, no hay transición y el autómata se detiene. *Este orden es el que permite que en q1 la `s` vaya a q8 (columna exacta) y la `x` a q11 (clase `LETRA`).*
3. Cada estado es de uno de tres tipos: **no final**, **final de token** (`*`, produce un `TipoToken`) o **final de error** (`✗`, produce un código de diagnóstico). Formalmente es un AFD cuyos estados finales están etiquetados con lo que se reconoció, la misma idea que usan los generadores tipo *lex*.
4. **Resultado del AFD** = el prefijo **más largo** que termina en un estado final (de token o de error). Si nunca pasó por un estado final, no reconoce nada (longitud 0).

---

## 5. Algoritmo de reconocimiento: coincidencia más larga y prioridad

En cada posición `p` del texto (después de saltar espacios):

1. Se ejecutan los cuatro AFD desde `p`, en el orden de `AUTOMATAS`: **comentario, cadena, número y medidas, identificador**.
2. Se consulta la tabla de símbolos fijos (2 caracteres, luego 1).
3. **Gana el candidato de mayor longitud** (*maximal munch*). En caso de empate gana el primero en el orden anterior (**prioridad**).
4. Si ningún candidato reconoce nada: el carácter en `p` es desconocido → `LEX-001`, se consume **un** carácter.
5. Postproceso del ganador, solo si es un identificador y en este orden: (a) más de 32 caracteres → `LEX-005`; (b) `normalizar(lexema)` ∈ `FORMA_CANONICA` → `PALABRA_RESERVADA`, o la categoría de `OPERADORES_PALABRA` si la forma canónica está allí.

*Nota honesta sobre la prioridad:* los candidatos empiezan por caracteres distintos, salvo `/`, que se resuelve por longitud; por tanto hoy **nunca hay empates**. La regla de prioridad existe para que el comportamiento siga definido cuando se agregue un patrón nuevo.

| Entrada | Tokens | Por qué |
|---|---|---|
| `x<-5` | `x` · `<-` · `5` | `<-` (2) gana a `<` (1): es una **asignación** |
| `x < -5` | `x` · `<` · `-` · `5` | el espacio separa: «menor que menos cinco» |
| `a<=b` | `a` · `<=` · `b` | `<=` (2) gana a `<` (1) |
| `a<>b` | `a` · `<>` · `b` | `<>` (2) gana a `<` (1) |
| `<-<=<><` | `<-` · `<=` · `<>` · `<` | siempre el más largo desde la posición actual |
| `a<--1` | `a` · `<-` · `-` · `1` | |
| `a==b` | `a` · `=` · `=` · `b` | no existe `==` |
| `a:=1` | `a` · `:` · `=` · `1` | no existe `:=` |
| `a/b` | `a` · `/` · `b` | el AFD de comentario no acepta `/b` |
| `a // c` | `a` · comentario | `// c` (4) gana a `/` (1) |
| `t>=30C` | `t` · `>=` · `30C` | el AFD de números sigue hasta la unidad |
| `x<-40%MOD 3` | `x` · `<-` · `40%` · `MOD` · `3` | tras `%` el AFD de números se detiene |
| `SiNo sino SINO sinope si2` | reservada ×3 · identificador `sinope` · identificador `si2` | el identificador se lee completo antes de consultar reservadas |
| `y Yo NO nota mod modo` | lógico `y` · id. `Yo` · lógico `NO` · id. `nota` · aritmético `mod` · reservada `modo` | ídem con los operadores con letras |

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
| Unidad desconocida (`LEX-008`) | El número y todas las letras que lo siguen (`10x`, `5min`) | Primer carácter que no es letra, dígito, `_` ni `.` |

Una barra invertida al final de la línea (`"abc\`⏎) no es un escape: se informa solo `LEX-002`.

---

## 8. Cadena de entrada válida

**Definición.** La *cadena de entrada* es el contenido completo del archivo: un programa FlowLang. Es **válida** si y solo si cumple las dos condiciones:

1. **Validez léxica** (análisis léxico): tiene **cero diagnósticos `LEX-…`**, es decir, el texto se descompone por completo en tokens de las categorías 1–14.
2. **Buena formación estructural** (comprobación sintáctica ligera): tiene **cero diagnósticos `SIN-…`**.

La interfaz muestra los dos veredictos por separado («Léxico: válido / Estructura: válida») y el global.

### 8.1 Veredicto por línea
Como el enunciado habla de «cadenas de entrada» en plural, además del veredicto global se informa el **veredicto léxico de cada línea**: una línea es *léxicamente inválida* si en ella comienza al menos un diagnóstico `LEX-…`. Se muestra como marca en el margen del editor y como lista en la consola.

### 8.2 Comprobaciones estructurales (clasificadas como **sintácticas**, no léxicas)
Las realiza `core/validador.py` sobre los tokens **significativos**, siempre, haya o no errores léxicos. Las palabras se comparan por su **forma canónica** (no importa cómo se escribieron).

| Regla | Mecanismo | Diagnóstico |
|---|---|---|
| E1. El programa tiene al menos un token significativo | contar | `SIN-001` |
| E2. El primer token significativo es la palabra reservada `Algoritmo` | mirar el primero | `SIN-002` |
| E3. El último token significativo es la palabra reservada `FinAlgoritmo` | mirar el último | `SIN-003` |
| E4. Los paréntesis `( )` están balanceados | **pila** de paréntesis | `SIN-004`, `SIN-005`, `SIN-006` |
| E5. Cada bloque abierto se cierra con su palabra, y los bloques están bien anidados | **pila** de bloques | `SIN-007`, `SIN-008` |
| E6. Una palabra intermedia (`SiNo`) aparece directamente dentro de su bloque (`Si`) | cima de la pila de bloques | `SIN-009` |

- Si falla E1 no se evalúan las demás.
- Los diagnósticos estructurales se devuelven ordenados por (línea, columna).

**Datos de E5 y E6** (`config/reglas.py`):

```python
BLOQUES = {                      # apertura -> cierre (formas canónicas)
    "Si": "FinSi",
    "Mientras": "FinMientras",
    "Para": "FinPara",
    "Repetir": "Hasta Que",      # cierre de dos tokens
    "Segun": "FinSegun",
}
PALABRAS_INTERMEDIAS = {"SiNo": "Si"}   # palabra -> bloque en el que debe estar
```

**Por qué `Algoritmo`/`FinAlgoritmo` no están en la pila.** El marco del programa no se anida: basta mirar el primer y el último token (E2 y E3), algo que **no necesita memoria**. Los cinco bloques de `BLOQUES` sí se anidan unos dentro de otros sin límite de profundidad, y eso es lo que exige una pila. Ponerlos también en la pila produciría dos diagnósticos para el mismo defecto (falta `FinAlgoritmo`).

**Algoritmo de E5/E6** (una pasada de izquierda a derecha; cada elemento de la pila es la apertura con su posición):

```
para cada token significativo t, con palabra = forma canónica de t (o nada si no es reservada):
    si palabra es una apertura de BLOQUES:
        apilar t
    si no, si palabra es intermedia (SiNo):
        si la pila está vacía o su cima no es el bloque requerido (Si):   → SIN-009 en t
    si no, si en t empieza un cierre c (se prueba primero el de dos palabras, «Hasta Que»):
        A = la apertura que corresponde a c
        si no hay ningún A en la pila:                                    → SIN-008 en t  (la pila no cambia)
        si no:
            mientras la cima no sea un A:  desapilar x                    → SIN-007 en x  (quedó sin cerrar)
            desapilar el A   (cierre correcto)
al terminar: cada apertura x que quede en la pila                         → SIN-007 en x
```

- `Hasta` **solo** es cierre cuando el token significativo siguiente es `Que`. Un `Hasta` suelto es el límite de un `Para` (`Para i <- 1 Hasta 10`) y el validador lo ignora. Por eso `Repetir … Hasta x = 0` (sin `Que`) deja el `Repetir` abierto → `SIN-007`.
- `SIN-007` se sitúa en la **apertura** (como `SIN-005`); `SIN-008` y `SIN-009`, en la palabra que sobra.
- Recuperación sin cascada: un cierre que no tiene apertura en la pila **no desapila nada**; un cierre cuya apertura está más abajo da por no cerrados los bloques intermedios y continúa. En ningún caso se informa algo falso.
- **Dos pilas independientes** (paréntesis y bloques): así un paréntesis sin cerrar no arrastra errores de bloque, y al revés. Consecuencia aceptada: no se detecta el cruce `( Si … ) FinSi`.
- No se comprueba que cada `Si` tenga `Entonces`, que cada ciclo tenga `Hacer`, que un `Si` tenga un solo `SiNo`, ni que `Caso` esté dentro de un `Segun`: eso ya sería un analizador sintáctico. (Añadir `"Caso": "Segun"` a `PALABRAS_INTERMEDIAS` es un ejercicio de sustentación.)
- Detalle de E4 (sin cambios): cierre con la pila vacía → `SIN-004` en el cierre. Al terminar, cada apertura que quede en la pila → `SIN-005` en esa apertura. `SIN-006` (cierre que no corresponde a la cima) **no puede producirse en FlowLang 2.0 base** porque solo hay un par (`PARES_AGRUPACION = {"(": ")"}`); el código y su entrada del catálogo se conservan porque el validador es genérico y reaparece al añadir un segundo par (ejercicio «agregar `[` `]`»).

*Apunte teórico (la respuesta a «¿por qué no lo hace un AFD?»):* el lenguaje de los paréntesis balanceados —y el de los bloques `Si … FinSi` anidados, que es el mismo con otros símbolos— **no es regular**. Un AFD tiene un número fijo de estados y para saber cuántos bloques siguen abiertos haría falta un estado por cada profundidad posible, que no tiene límite (lema del bombeo sobre `Siⁿ FinSiⁿ`). Hace falta memoria tipo pila: es un lenguaje libre de contexto, reconocible por un **autómata de pila**. Por eso esta comprobación está en el validador y no en el lexer.

| Entrada (dentro de `Algoritmo p … FinAlgoritmo`) | Diagnósticos |
|---|---|
| `Si a Entonces` ⏎ `FinSi` | ninguno |
| `Si a Entonces` (sin cierre) | `SIN-007` en `Si`: «Falta `FinSi` para el `Si` de la línea 2.» |
| `FinMientras` | `SIN-008`: «`FinMientras` sin `Mientras`: no hay ningún `Mientras` abierto en este punto.» |
| `SiNo` | `SIN-009`: «`SiNo` fuera de un `Si`: …» |
| `Si a Entonces` ⏎ `Mientras b Hacer` ⏎ `SiNo` ⏎ `FinMientras` ⏎ `FinSi` | `SIN-009` en `SiNo` (la cima es `Mientras`) |
| `Si a Entonces` ⏎ `Mientras b Hacer` ⏎ `Para i <- 1 Hasta 3 Hacer` ⏎ `FinSi` | `SIN-007` en `Mientras` y `SIN-007` en `Para` |
| `Si a Entonces` ⏎ `FinMientras` ⏎ `FinSi` | `SIN-008` en `FinMientras` (el `Si` se cierra bien) |
| `Repetir` ⏎ `Hasta Que a` | ninguno |
| `Hasta Que a` | `SIN-008` en `Hasta`: «`Hasta Que` sin `Repetir`: …» |
| `Repetir` ⏎ `Hasta a` | `SIN-007` en `Repetir`: «Falta `Hasta Que` para el `Repetir` de la línea 2.» |
| `Para i <- 1 Hasta 3 Hacer` ⏎ `FinPara` | ninguno (ese `Hasta` no es un cierre) |
| `si a entonces` ⏎ `FINSI` | ninguno (no distingue mayúsculas) |

---

## 9. Qué se instala en la tabla de símbolos

Se instalan los tokens cuyas categorías están en `CATEGORIAS_EN_TABLA`: **palabras reservadas, identificadores, enteros, decimales, cadenas, duraciones, temperaturas y porcentajes**. Un símbolo repetido **no** crea otra entrada: se añade una aparición.

**Clave** (`clave_simbolo(lexema, tipo)` en `core/simbolos.py`):

| Categoría del token | Clave | Ejemplo |
|---|---|---|
| En `CATEGORIAS_INSENSIBLES` (palabra reservada, identificador, operador aritmético, operador lógico) | `normalizar(lexema)` | `Si2`, `SI2`, `si2` → `si2` |
| Cualquier otra (cadena, números, medidas…) | el lexema tal cual | `"Hola"` ≠ `"hola"`; `30C` |

- La **función hash se aplica a la clave**, no al lexema: por eso `Bomba` y `bomba` caen en la misma cubeta y son la misma entrada.
- El campo `lexema` de la entrada guarda **la primera forma en que se escribió**, que es lo que se muestra. Las demás formas solo suman apariciones.
- La clave de una cadena incluye las comillas, de modo que `"x"` y `x` son entradas distintas.
- Los operadores están en `CATEGORIAS_INSENSIBLES` solo para que, si se decide instalarlos (§11 de la arquitectura), `Y` e `y` sean una entrada.

| Atributo | Contenido |
|---|---|
| `lexema` | Primera forma escrita |
| `clave` | Clave de búsqueda (ver arriba) |
| `categoria` | `TipoToken` |
| `tipo_dato` | Identificador: tipo con el que se declara (reglas de abajo) o vacío. `ENTERO` → `Entero`; `DECIMAL` → `Real`; `CADENA` → `Cadena`; `DURACION` → `Duracion`; `TEMPERATURA` → `Temperatura`; `PORCENTAJE` → `Porcentaje`; `Verdadero`/`Falso` → `Logico` (constante `TIPO_DATO_BOOLEANO`); resto vacío |
| `valor` | `ENTERO` → `int`; `DECIMAL` → `float`; `CADENA` → texto sin comillas y con los escapes interpretados; `DURACION` → **milisegundos** (`10s` → 10000, `1.5m` → 90000.0); `TEMPERATURA` y `PORCENTAJE` → el número (`22.5C` → 22.5, `40%` → 40); `Verdadero`/`Falso` → `True`/`False`; resto vacío |
| `linea_declaracion` | Línea de la declaración (solo identificadores declarados) |
| `apariciones` | Lista de (línea, columna) de cada uso, en orden |
| `valor_hash` | Resultado de la función hash sobre la **clave** |
| cubeta | `valor_hash mod capacidad` (se calcula; cambia al redimensionar) |

El valor de una medida es `int` si el número se escribió sin punto y `float` (redondeado a 3 decimales) si se escribió con punto.

**Reglas de declaración** (las únicas reglas contextuales; las aplica `RegistradorSimbolos`, que recuerda en qué punto de una declaración está):

- **D1 — `Definir a, b, c Como Tipo`**: después de `Definir`, cada `IDENTIFICADOR` (separados por `,`) queda pendiente; al llegar `Como` seguido de una palabra de `TIPOS_DE_DATO`, todos los pendientes se anotan con `tipo_dato` = forma canónica del tipo (`Entero`, aunque se haya escrito `entero`) y `linea_declaracion` = la línea donde está **ese identificador**. Si entre `Definir` y el tipo aparece cualquier otro token significativo, la declaración se abandona sin anotar nada (no se reporta error: sería sintaxis).
- **D2 — `Para i <- …`**: el `IDENTIFICADOR` que sigue inmediatamente a `Para` queda declarado **implícitamente** con `tipo_dato = Entero` (`TIPO_DATO_CONTADOR`) y esa línea, como hace PSeInt con la variable de control.
- En ambos casos, **si el identificador ya tenía declaración se conserva la primera** (detectar la redeclaración sería análisis semántico).
- Precisión (D-27, sigue vigente): la declaración se anota la primera vez que el identificador aparece **declarado**, aunque ya se hubiera usado antes.
- Los tokens `COMENTARIO` y `ERROR` no interrumpen una declaración: en `Definir 2pi_r, radio Como Real`, `radio` queda declarado.
- `Leer x` y `x <- 1` **no** declaran.

Operadores y delimitadores no se instalan por defecto porque no tienen atributos que otra fase necesite; basta añadir sus categorías a `CATEGORIAS_EN_TABLA` para instalarlos.

---

## 10. Catálogo de diagnósticos

Todos tienen: **código**, **tipo**, **título**, **mensaje**, **sugerencia**, **línea**, **columna** y **lexema**. Los de archivo no tienen posición (línea 0, columna 0). En las plantillas, `{lexema}` es el lexema del token; `SIN-007`…`SIN-009` usan además `{apertura}`, `{cierre}`, `{palabra}` y `{linea_apertura}` (formas canónicas), que el validador entrega en el parámetro `datos` de `crear_diagnostico`. La plantilla de la **sugerencia** también se rellena con esos datos.

### 10.1 Léxicos

| Código | Título | Mensaje | Sugerencia |
|---|---|---|---|
| `LEX-001` | Carácter no reconocido | El carácter '{lexema}' no pertenece al alfabeto de FlowLang. | Elimínelo o reemplácelo por un símbolo válido. *(Se sustituye por una sugerencia específica si el carácter está en `SUGERENCIAS_CARACTER`.)* |
| `LEX-002` | Cadena sin cerrar | La cadena {lexema} no tiene comilla de cierre en la misma línea. | Agregue `"` al final de la cadena; las cadenas no pueden ocupar varias líneas. |
| `LEX-003` | Número mal formado | '{lexema}' no es un número válido. | Un decimal necesita dígitos a ambos lados de un único punto, por ejemplo 3.14 o 0.5. |
| `LEX-004` | Identificador inválido | '{lexema}' no es válido: un identificador no puede comenzar con un dígito. | Comience el nombre con una letra o `_`; si quería un número, quite las letras. |
| `LEX-005` | Identificador demasiado largo | El identificador '{lexema}' supera el máximo de 32 caracteres. | Use un nombre más corto. |
| `LEX-006` | Secuencia de escape inválida | La secuencia '{lexema}' no es un escape válido dentro de una cadena. | Escapes permitidos: `\n`, `\t`, `\"` y `\\`. |
| `LEX-007` | Comentario de bloque sin cerrar | El comentario que comienza con /* nunca se cierra. | Agregue `*/` al final del comentario. |
| `LEX-008` **(nuevo)** | Unidad desconocida | En '{lexema}' las letras que siguen al número no forman una unidad conocida. | Unidades válidas: ms, s, m, h (duración), C (temperatura) y % (porcentaje). Si es un nombre, no puede comenzar con un dígito. |

Sugerencias específicas de `LEX-001` (`SUGERENCIAS_CARACTER`, 11 entradas):

| Carácter | Sugerencia |
|---|---|
| `&` | El «y» lógico se escribe con la palabra `Y`. |
| `\|` | El «o» lógico se escribe con la palabra `O`. |
| `!` | La negación se escribe `NO` y «distinto de» se escribe `<>`. |
| `%` | `%` solo se usa pegado a un número, como 40%; el resto de la división se escribe `MOD`. |
| `'` | Las cadenas se escriben con comillas dobles: "texto". |
| `.` | El punto solo se usa dentro de un número decimal, como 3.14. |
| `#` | Los comentarios se escriben con `//` o `/* */`. |
| `{` y `}` | FlowLang no usa llaves: los bloques se cierran con palabras como `FinSi` o `FinMientras`. |
| `[` y `]` | FlowLang no tiene corchetes; use paréntesis. |

### 10.2 Estructurales (sintácticos ligeros)

| Código | Título | Mensaje | Sugerencia | Posición |
|---|---|---|---|---|
| `SIN-001` | Programa vacío | El programa no contiene ninguna instrucción. | Escriba un programa entre `Algoritmo` y `FinAlgoritmo`. | 1:1 |
| `SIN-002` | Falta `Algoritmo` | El programa debe comenzar con la palabra reservada `Algoritmo`; se encontró '{lexema}'. | Agregue `Algoritmo` y un nombre como primera línea. | Primer token significativo |
| `SIN-003` | Falta `FinAlgoritmo` | El programa debe terminar con la palabra reservada `FinAlgoritmo`; se encontró '{lexema}'. | Agregue `FinAlgoritmo` como última palabra. | Último token significativo |
| `SIN-004` | Cierre sin apertura | El símbolo '{lexema}' no tiene apertura correspondiente. | Elimine el símbolo o agregue su apertura. | El cierre |
| `SIN-005` | Apertura sin cierre | El símbolo '{lexema}' nunca se cierra. | Agregue el símbolo de cierre correspondiente. | La apertura |
| `SIN-006` | Cierre no correspondiente | El símbolo '{lexema}' no corresponde con la última apertura pendiente. | Revise el orden de los símbolos de agrupación. | El cierre (no alcanzable con un solo par; §8.2) |
| `SIN-007` **(nuevo)** | Bloque sin cerrar | Falta `{cierre}` para el `{apertura}` de la línea {linea_apertura}. | Agregue `{cierre}` donde termina el bloque. | La apertura |
| `SIN-008` **(nuevo)** | Cierre de bloque sin apertura | `{cierre}` sin `{apertura}`: no hay ningún `{apertura}` abierto en este punto. | Elimine `{cierre}` o agregue el `{apertura}` que le corresponde. | El cierre (su primera palabra) |
| `SIN-009` **(nuevo)** | Palabra fuera de su bloque | `{palabra}` fuera de un `{apertura}`: en este punto el bloque abierto más reciente no es un `{apertura}`. | `{palabra}` solo puede ir directamente dentro de un `{apertura}` abierto. | La palabra |

El `lexema` de `SIN-007`…`SIN-009` es el del token señalado **tal como se escribió** (para subrayarlo en el editor); el mensaje usa las formas canónicas.

### 10.3 De archivo

Sin cambios.

| Código | Título | Mensaje | Sugerencia |
|---|---|---|---|
| `ARC-001` | Archivo inexistente | No se encontró el archivo '{lexema}'. | Verifique la ruta y el nombre. |
| `ARC-002` | Extensión no soportada | El archivo '{lexema}' no tiene una extensión permitida. | Use un archivo `.flow` o `.txt`. |
| `ARC-003` | Archivo vacío | El archivo '{lexema}' no contiene texto. | Elija un archivo con un programa FlowLang. |
| `ARC-004` | Codificación inválida | El archivo '{lexema}' no está codificado en UTF-8. | Guárdelo como UTF-8 e inténtelo de nuevo. |
| `ARC-005` | Error de lectura o escritura | No se pudo leer o escribir '{lexema}'. | Revise los permisos y que no sea una carpeta. |
| `ARC-006` | Archivo demasiado grande | El archivo '{lexema}' supera el tamaño máximo de 1 MB. | Divida el archivo o use uno más pequeño. |

Orden de comprobación al cargar: `ARC-001` → `ARC-005` (si es carpeta) → `ARC-002` → `ARC-006` → lectura (`ARC-005`) → decodificación (`ARC-004`) → `ARC-003` (vacío o solo espacios).

Total del catálogo: **23 diagnósticos** (8 `LEX`, 9 `SIN`, 6 `ARC`).

---

## 11. Gramática informativa (no implementada)

Solo para dar contexto al lenguaje. **SmartLex Studio no la comprueba** (salvo §8.2). Las palabras entre comillas se aceptan con cualquier combinación de mayúsculas.

```ebnf
programa     = "Algoritmo" IDENTIFICADOR { instruccion } "FinAlgoritmo" ;
instruccion  = ( declaracion | asignacion | accion ) [ ";" ]
             | condicional | mientras | para | repetir | segun ;
declaracion  = "Definir" IDENTIFICADOR { "," IDENTIFICADOR } "Como" tipo ;
tipo         = "Entero" | "Real" | "Cadena" | "Logico" | "Dispositivo" ;
asignacion   = IDENTIFICADOR "<-" expresion ;
accion       = "Escribir" expresion { "," expresion }
             | "Leer" IDENTIFICADOR { "," IDENTIFICADOR }
             | ( "Activar" | "Desactivar" ) IDENTIFICADOR
             | "Esperar" expresion ;
condicional  = "Si" expresion "Entonces" { instruccion } [ "SiNo" { instruccion } ] "FinSi" ;
mientras     = "Mientras" expresion "Hacer" { instruccion } "FinMientras" ;
para         = "Para" IDENTIFICADOR "<-" expresion "Hasta" expresion [ "Con" "Paso" expresion ] "Hacer"
               { instruccion } "FinPara" ;
repetir      = "Repetir" { instruccion } "Hasta" "Que" expresion ;
segun        = "Segun" expresion "Hacer" { "Caso" expresion { "," expresion } ":" { instruccion } }
               [ "De" "Otro" "Modo" ":" { instruccion } ] "FinSegun" ;
expresion    = (* operandos: IDENTIFICADOR, literales, medidas, "Verdadero", "Falso", "(" expresion ")";
                  operadores: + - * / ^ MOD  = <> < <= > >=  Y O NO *) ;
```

En PSeInt las opciones de un `Segun` se escriben solo con el valor (`1:`); FlowLang antepone `Caso` para que se lea mejor. Al analizador léxico le da igual.

---

## 12. Archivos de ejemplo y resultados esperados

Los tres archivos de `ejemplos/` ya están creados en sintaxis 2.0 y son **parte del contrato**: no deben modificarse sin actualizar esta sección y las pruebas. (`ejemplos/practica.flow` es un archivo local del usuario, ajeno al contrato.)

### 12.1 `ejemplos/correcto.flow` — válido
- **189 tokens**; 0 diagnósticos; `es_valida = True`. 54 líneas.
- Por categoría: 63 reservadas, 35 identificadores, 14 enteros, 1 decimal, 6 cadenas, 5 duraciones, 2 temperaturas, 1 porcentaje, 6 aritméticos, 6 relacionales, 4 lógicos, 6 asignaciones, 37 delimitadores, 3 comentarios.
- Primer token significativo: `Algoritmo` en 2:1. Último: `FinAlgoritmo` en 54:1.
- Usa los cinco bloques (`Si` con `SiNo`, `Mientras`, `Para … Con Paso`, `Repetir … Hasta Que`, `Segun` con `Caso` y `De Otro Modo`) y un `Si` anidado en un `Mientras`.
- Tabla de símbolos (capacidad inicial 17): **66 entradas**, 3 redimensionados (17 → 37 al instalar `activo`, → 79 al instalar `Activar`, → 163 al instalar `De`), capacidad final 163, factor de carga 0,405, cadena más larga 3.
- Colisiones — son dos medidas distintas y se muestran las dos:
  - **Colisiones al insertar: 32.** Contador histórico: cuántas veces un símbolo nuevo llegó a una cubeta que ya estaba ocupada *en el momento de insertarlo*.
  - **Colisiones en la tabla final: 8.** Entradas que hoy comparten cubeta con otra anterior = entradas − cubetas ocupadas = 66 − 58.
- Declaraciones anotadas: `temperatura` y `humedad` → `Real`, línea 5; `ciclos` y `zona` → `Entero`, línea 6; `nombre` → `Cadena`, 7; `activo` → `Logico`, 8; `bomba` y `ventilador` → `Dispositivo`, 9; **`i` → `Entero`, línea 34** (regla D2, `Para i`). `riego_invernadero` (nombre del algoritmo) queda sin tipo.
- La línea 53 escribe `escribir` en minúsculas: es la misma entrada que `Escribir` (5 apariciones; lexema mostrado `Escribir`, el de la primera).
- Medidas: `30C` → 30, `40%` → 40, `10s` → 10000, `500ms` → 500, `1.5m` → 90000.0, `22.5C` → 22.5, `5m` → 300000, `1h` → 3600000.

### 12.2 `ejemplos/incorrecto.flow` — inválido
**82 tokens** (15 de tipo `ERROR`), **30 entradas** en la tabla (capacidad final 79, 2 redimensionados, 10 colisiones al insertar, 4 en la tabla final), **21 diagnósticos: 15 léxicos y 6 estructurales**. Por categoría: 19 reservadas, 15 identificadores, 8 enteros, 2 aritméticos, 3 relacionales, 7 asignaciones, 13 delimitadores, 15 errores.

| # | Código | Línea | Col | Lexema | Qué muestra |
|---|---|---|---|---|---|
| 1 | `LEX-004` | 2 | 13 | `2pi_r` | nombre que empieza con dígito |
| 2 | `LEX-003` | 3 | 14 | `3.14.15` | dos puntos |
| 3 | `LEX-003` | 3 | 24 | `5.` | falta la parte decimal |
| 4 | `LEX-008` | 4 | 13 | `10x` | unidad desconocida |
| 5 | `LEX-002` | 5 | 15 | `"Hola mundo;` | cadena sin cerrar |
| 6 | `LEX-006` | 6 | 16 | `\q` | escape inválido |
| 7 | `LEX-001` | 7 | 18 | `@` | carácter desconocido |
| 8 | `LEX-001` | 7 | 22 | `%` | `%` suelto (sugerencia: `MOD`) |
| 9 | `LEX-001` | 8 | 21 | `&` | sugerencia: `Y` |
| 10 | `LEX-005` | 9 | 5 | `identificador_demasiado_largo_para_flowlang` | 43 caracteres |
| 11 | `LEX-001` | 11 | 18 | `'` | comilla simple |
| 12 | `LEX-001` | 11 | 24 | `'` | comilla simple |
| 13 | `LEX-001` | 16 | 24 | `{` | llaves de FlowLang 1.0 |
| 14 | `LEX-001` | 16 | 26 | `}` | |
| 15 | `LEX-007` | 21 | 1 | desde `/* comentario sin cerrar` hasta el fin del archivo | bloque sin cerrar (se traga `FinAlgoritmo`) |
| 16 | `SIN-005` | 10 | 8 | `(` | paréntesis sin cerrar |
| 17 | `SIN-007` | 12 | 9 | `Mientras` | «Falta `FinMientras` para el `Mientras` de la línea 12.» (lo descubre el `FinSi` de la línea 14) |
| 18 | `SIN-009` | 15 | 5 | `SiNo` | `SiNo` después de `FinSi`: ya no hay `Si` abierto |
| 19 | `SIN-008` | 17 | 5 | `FinPara` | «`FinPara` sin `Para`: …» |
| 20 | `SIN-007` | 18 | 5 | `Repetir` | «Falta `Hasta Que` para el `Repetir` de la línea 18.» (la línea 20 dice `Hasta` sin `Que`) |
| 21 | `SIN-003` | 20 | 19 | `0` | el último token significativo no es `FinAlgoritmo` |

El orden de la tabla es el de reporte: primero los léxicos en orden de aparición y después los estructurales ordenados por posición. Líneas léxicamente inválidas: 2, 3, 4, 5, 6, 7, 8, 9, 11, 16, 21. Primer token significativo `Algoritmo` (1:1); `radio` queda declarado `Real` en la línea 2 aunque `2pi_r` sea un error.

### 12.3 `ejemplos/casos_limite.flow` — válido
**223 tokens**, 0 diagnósticos, **68 entradas** (capacidad final 163, 3 redimensionados, 31 colisiones al insertar, 12 en la tabla final). Por categoría: 54 reservadas, 47 identificadores, 17 enteros, 1 decimal, 3 cadenas, 6 duraciones, 2 temperaturas, 2 porcentajes, 10 aritméticos, 11 relacionales, 6 lógicos, 13 asignaciones, 41 delimitadores, 10 comentarios. Primer token significativo `ALGORITMO` (2:1); último `finalgoritmo` (30:1). Cubre:

- palabras reservadas en mayúsculas, minúsculas y mixtas (`ALGORITMO`, `definir`, `DEFINIR`, `VERDADERO`, `finalgoritmo`);
- identificador de exactamente 32 caracteres, `_` solo, y nombres que **contienen** una palabra reservada u operador sin serlo (`si2`, `Yo`, `nota`, `modo_riego`);
- identificadores sin distinguir mayúsculas: `si2`, `SI2` y `Si2` son **una** entrada con 12 apariciones, declarada `Entero` en la línea 6;
- cadena vacía, los cuatro escapes, `//` y `/* */` dentro de una cadena, `/**/`;
- operadores pegados sin espacios (línea 18: `b<-si2>=_ Y si2<=nota O NO b=Falso<>VERDADERO;` → 17 tokens) y la pareja `si2<-5` (asignación) / `si2 < -5` (comparación);
- las cuatro unidades de duración con entero y con decimal, temperatura y porcentaje pegados a operadores (`d>=22.5C`, `d<>0.5%`);
- bloques en una sola línea, `Repetir` anidado en `Repetir` con dos `Hasta Que`, un `Para` cuyo `Hasta` no es cierre, `Segun` con `Caso` y `De Otro Modo`;
- comentario final sin salto de línea.

---

## 13. Función hash (resumen; diseño completo en `02_arquitectura.md` §6)

`h(clave)`: se parte de 0 y por cada carácter `c` de la **clave** se hace `h = (h · 31 + código(c)) mod 2³²`. Cubeta = `h mod capacidad`. La función no cambia respecto de 1.0; lo nuevo es que recibe la clave normalizada (§9).

| Lexema escrito | Clave | `h` | Cubeta con capacidad 17 |
|---|---|---|---|
| `x` | `x` | 120 | 1 |
| `si`, `Si`, `SI` | `si` | 115·31 + 105 = 3670 | 15 |
| `10` | `10` | 49·31 + 48 = 1567 | 3 |
| `10s` | `10s` | 1567·31 + 115 = 48692 | 4 |
| `temperatura` | `temperatura` | 321701232 | 15 (colisiona con `si`) |
| `riego` | `riego` | 108509814 | 4 |
| `activo` | `activo` | 2872016656 | 4 (colisiona con `riego`) |
| `total` | `total` | 110549828 | 1 (colisiona con `x`) |
| `Algoritmo` | `algoritmo` | 225490188 | 12 |

---

## 14. Diferencias con FlowLang 1.0 y con PSeInt

### 14.1 Qué cambia respecto de FlowLang 1.0

| Aspecto | 1.0 | 2.0 |
|---|---|---|
| Marco | `inicio … fin` | `Algoritmo nombre … FinAlgoritmo` |
| Bloques | llaves `{ }` | palabra de cierre: `FinSi`, `FinMientras`, `FinPara`, `Hasta Que`, `FinSegun` |
| Declaración | `numero x = 1;` | `Definir x Como Entero;` y luego `x <- 1;` |
| Asignación / igualdad | `=` / `==` | `<-` / `=` |
| Distinto, lógicos | `!=`, `&&`, `\|\|`, `!` | `<>`, `Y`, `O`, `NO` |
| Resto, potencia | `%`, — | `MOD`, `^` |
| Mayúsculas | sensible | insensible en palabras e identificadores |
| Literales con unidad | no | `DURACION`, `TEMPERATURA`, `PORCENTAJE` |
| Estructuras nuevas | — | `Para`, `Repetir`, `Segun` |
| Salida | `mostrar` | `Escribir` |
| Palabras reservadas | 17 | 36 (+ 4 operadores con letras) |
| Diagnósticos | 19 | 23 (`LEX-008`, `SIN-007`, `SIN-008`, `SIN-009`) |
| Sin cambios | AFD de identificadores, cadenas y comentarios; motor de AFD; función hash; errores `ARC` |

### 14.2 Qué **no** se toma de PSeInt (decisiones KISS)

| PSeInt | FlowLang 2.0 | Motivo |
|---|---|---|
| Cadenas con `"` o `'` | solo `"` | §3.4 |
| Sin escapes en cadenas | `\n \t \" \\` | se conserva `LEX-006` y el AFD con estados de error |
| Solo comentario `//` | `//` y `/* */` | §3.5 |
| `Proceso`/`FinProceso`, `Funcion`, arreglos (`Dimension`, `[ ]`) | no existen | fuera del alcance; `Funcion … FinFuncion` es ejercicio de sustentación |
| Sinónimos (`:=`, `==`, `!=`, `&`, `\|`, `~`, `Numero`, `Texto`, `Caracter`, `Mostrar`, `Imprimir`) | una sola forma por concepto | menos reglas que explicar |
| Tildes opcionales (`Según`, `Lógico`) | sin tilde | alfabeto ASCII (§1) |
| Opciones de `Segun` sin palabra (`1:`) | `Caso 1:` | legibilidad |
