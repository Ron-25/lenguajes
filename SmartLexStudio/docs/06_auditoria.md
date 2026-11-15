# 06 · Auditoría — SmartLex Studio

## Auditoría Fase A

- **Fecha:** 2026-11-15
- **Auditor / modelo:** reviewer-opus / claude-opus-5-5
- **Base de comparación:** commit `dc160e8` («Fase A (Sonnet): núcleo config/core/application con 87 pruebas»)
- **Veredicto:** **APROBADO CON OBSERVACIONES** (sin hallazgos críticos ni altos; 7 corregidos, 7 escalados u observaciones)

### 1. Alcance

| Incluido | Excluido |
|---|---|
| `config/reglas.py`, `core/*.py`, `application/*.py`, `tests/*.py` | `ui/` y `main.py` (Fase B, aún no existen) |
| Contraste con `instrucciones .pdf` (requisitos 1–6), `docs/03_especificacion.md`, `docs/02_arquitectura.md`, `agents/tareas.md` (A1–A10), `agents/decisiones.md` (D-26…D-28) | Los archivos de `ejemplos/` (no se modificaron) |

### 2. Metodología

Todo se ejecutó; nada se tomó del reporte del desarrollador.

1. **Batería existente**: `/opt/homebrew/bin/python3.14 -m unittest discover -s tests -v` → 87 pruebas OK en `dc160e8`. También con `python3.11` y `python3.12`.
2. **Sondas adversariales del lexer** (script desechable): `&&&`, `|||`, `===`, `!==`, `>==`, `a/*b*/c`, `a/ *b`, `/`, `//`, `/*`, `/* *`, `/*/`, `/**/`, `"`, `"\`, `"\q\""`, `.5.5`, `5..`, `..5`, `10si`, `1_`, `x.y`, `"a"b`, tabs, `\r`, `\r\n` dentro de cadena y comentario, `ñ`, emoji dentro y fuera de cadena, NBSP, NUL, fin de archivo en mitad de cadena, comentario y número. Todos los resultados coinciden con la especificación §3–§7 (maximal munch, prioridad, escapes, modo pánico, posiciones en puntos de código).
3. **Fuzzing con invariantes** (20 003 entradas: los 3 ejemplos + 20 000 cadenas aleatorias de hasta 60 piezas sobre `ab_19.;"\/*nqt`, espacios, saltos, operadores, `@ñ😀#`, `inicio`, `fin`, `//`, `/*`, `*/`, `\r\n`). Por cada entrada se comprobó: (a) los lexemas, en orden y separados solo por espacios, reconstruyen la fuente; (b) la (línea, columna) de cada token coincide con la calculada carácter a carácter; (c) ningún lexema vacío; (d) hay token `ERROR` si y solo si hay diagnóstico; (e) en `SesionAnalisis`, los diagnósticos de cada paso pertenecen a su token `ERROR` y su concatenación es igual a la del lexer; (f) tokens, diagnósticos y tamaño de tabla de la sesión paso a paso son iguales a los de `analizar_texto`. **0 fallos** antes y después de las correcciones.
4. **Equivalencia regex ↔ AFD independiente**: alfabeto de 13 símbolos (incluye `n` y `t`) hasta longitud 5, y otro con `Z 9 ñ \t \r` hasta longitud 4: **0 diferencias**. La prueba del proyecto **no es tautológica** (compara el AFD de `reglas.AFD_*` contra la regex de `INFO_CATEGORIAS`, que son datos independientes), pero su alfabeto omitía la letra `n` del contrato (AUD-04).
5. **Pruebas de mutación** puntuales en una copia (p. ej. `AFD_CADENA q2: "n" → q4`).
6. **Catálogo de errores** contrastado por script contra las tablas §10.1–§10.3 de la especificación: 19/19 códigos con título, mensaje y sugerencia idénticos.
7. **Archivos** con casos reales en disco: ruta con espacios y acentos (`carpeta ñandú/mi archivo é.flow`), sin permisos (`chmod 000`), directorio, enlace roto, `.flow` oculto, `x.Flow`, sin extensión, PNG, NUL, solo BOM, solo NBSP/`\f`/`\v`, ruta vacía, guardado con texto no codificable.
8. **Rendimiento** con entradas degeneradas (`"@" * n`).
9. **Extensibilidad** en copias temporales del proyecto (§6).
10. Comprobaciones A10: `grep` de `tkinter`, `def/class` en `reglas.py` y `import re` → vacíos; dependencias entre capas revisadas por `import`.

### 3. Verificación del contrato

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Nombres públicos idénticos a `agents/tareas.md` | Cumple | Revisión de firmas en los 8 módulos |
| `core/` y `application/` sin tkinter; `core` solo biblioteca estándar | Cumple | `grep -rn tkinter core application config` vacío; `test_dominio_sin_tkinter` |
| `config/reglas.py` solo datos, importa solo `string` y `TipoToken` | Cumple | `grep -n "^def \|^class "` vacío |
| Sin `re` en producción | Cumple | `grep` vacío |
| Dependencias `ui → application → core → config → modelos` | Cumple | `afd`, `lexer`, `validador`, `simbolos` → `reglas`; `errores` → `modelos`; sin ciclos |
| Motor AFD ejecuta las tablas | Cumple | `AFD.reconocer` es el bucle `estado = δ(estado, c)` sobre `reglas.AFD_*`; el lexer construye los AFD desde `reglas.AUTOMATAS` y no tiene casos especiales salvo símbolos fijos, reservadas y `len() > 32` (lo que la arquitectura §4.3 declara) |
| Tabla hash propia | Cumple | Solo listas; `buscar` recorre la cubeta; `_redimensionar` reubica **todas** las entradas con su `valor_hash`; no usa `dict`, `set` ni `hash()` |
| Valores de la especificación §12 | Cumple | 111/57/118 tokens; 36 entradas, capacidad 79, 14 colisiones, 2 redimensionados; los 15 diagnósticos de `incorrecto.flow` con posición exacta |
| Pruebas requeridas A3–A9 | Cumple con una desviación | Todas presentes; el alfabeto de la prueba de equivalencia no tenía la letra `n` (AUD-04, corregido) |

### 4. Hallazgos

| ID | Severidad | Archivo | Problema | Impacto | Prueba que lo reproduce | Estado |
|---|---|---|---|---|---|---|
| AUD-01 | Media | `application/analisis_service.py` (`siguiente_paso`) | Cada paso hacía `manejador.diagnosticos[antes:]`, y `diagnosticos` devuelve **una copia de toda la lista**: coste cuadrático en el número de diagnósticos. Medido: 20 000 errores 0,63 s; 40 000 → 2,31 s; 80 000 → 9,16 s (el lexer solo: 0,46 s). Un archivo permitido de 1 MB lleno de errores tardaría del orden de 20 minutos | La UI (Analizar, F5) y `analizar_texto` se congelan con archivos grandes con muchos errores | `test_auditoria_fase_a.test_aud01_sesion_lineal_en_cantidad_de_diagnosticos` (fallaba: 4,95 s frente a un límite de 1,85 s) | **Corregido** |
| AUD-02 | Media | `application/archivos.py` (`guardar_fuente`) | Un texto no codificable en UTF-8 (sustitutos sueltos, que Tk 8.6 produce con emoji) lanzaba `UnicodeEncodeError` sin convertirlo en `ARC-005`, **después** de haber abierto el archivo en modo `"w"`: el archivo existente quedaba vacío | Excepción no controlada y **pérdida del archivo del usuario** | `test_aud02_guardar_texto_no_codificable_no_trunca` (fallaba con `UnicodeEncodeError`; el archivo quedaba `''`) | **Corregido** |
| AUD-03 | Media | `config/reglas.py` (`INFO_CATEGORIAS`) | Regla duplicada: la regex informativa de `PALABRA_RESERVADA` repetía a mano las 17 palabras. Al agregar `repetir`, el lexer la reconoce pero el modo educativo muestra una regex que no la contiene (contradice la arquitectura §11: «el modo educativo la toma sola»). Ninguna prueba detectaba la divergencia entre las regex de símbolos/reservadas y los diccionarios | Información teórica falsa en pantalla tras una modificación en vivo | `test_aud03_regex_informativas_coinciden_con_los_datos`: en una copia del código original con `repetir` o `**` agregados **falla**; con la corrección pasa con `repetir`, y con `**` obliga a actualizar la regex de aritméticos (una línea) | **Corregido** (regex de reservadas derivada con `"\|".join(PALABRAS_RESERVADAS)`, valor idéntico al de la especificación) |
| AUD-04 | Baja | `tests/test_afd.py` | El alfabeto de la prueba de equivalencia omitía la letra `n` exigida por el contrato (A3); la transición del escape válido `\n` nunca se ejercitaba | La mutación `AFD_CADENA q2: "n" → q4` pasaba la prueba de equivalencia (la detectaba otra prueba del lexer por casualidad) | Mutación en copia: prueba original **OK**, prueba corregida **FAIL** | **Corregido** (se añaden `n` y `t`; +~1,8 s) |
| AUD-05 | Baja | `application/archivos.py` (`cargar_fuente`) | `ARC-003` usaba `str.strip()`, que considera espacio a NBSP, `\f`, `\v`, etc.; la especificación §3.7 define los espacios como `reglas.ESPACIOS`. Un archivo con solo NBSP se rechazaba como «vacío» en lugar de analizarse (daría `LEX-001`) | Clasificación incorrecta (archivo vs léxico); segunda definición de «espacio» fuera de `config` | `test_aud05_espacios_unicode_no_son_archivo_vacio` (fallaba con `ARC-003`) | **Corregido** (`strip(reglas.ESPACIOS)`) |
| AUD-06 | Baja | `application/analisis_service.py` (`explicar_token`) | Para un token `ERROR` de `LEX-001` mostraba la sugerencia genérica del catálogo, mientras el diagnóstico real llevaba la específica (`&` → «¿Quiso escribir `&&`?») | Pestaña Errores y Modo educativo se contradicen | `test_aud06_explicacion_usa_la_sugerencia_especifica` (fallaba) | **Corregido** (reanaliza el lexema y reutiliza la sugerencia del lexer: la regla sigue en un solo lugar) |
| AUD-07 | Baja | `application/analisis_service.py` (`_texto_instalacion`) | Cuando una inserción colisiona **y** redimensiona, la consola decía «colisión, cubeta 32, tabla redimensionada»: la colisión ocurrió en la cubeta de capacidad 17 y la 32 es la nueva (capacidad 37) | Narración engañosa en la evaluación progresiva | `test_aud07_narracion_de_colision_con_redimensionado` (fallaba) | **Corregido** («colisión; tabla redimensionada, ahora en cubeta 32») |
| AUD-08 | Media | `core/simbolos.py` / espec. §12.1 | `colisiones` es histórico (14 en `correcto.flow`), pero en la tabla final solo se ven 7 (36 entradas − 29 cubetas ocupadas). Coherente con el contrato, pero el encabezado «Colisiones 14» junto a una tabla con 7 colisiones visibles invita a la pregunta «¿dónde están las otras 7?» | Riesgo en la sustentación; no es un defecto de código | Medición: `estadisticas()` → `colisiones=14, cantidad=36, cubetas_ocupadas=29` | **Escalado** (E-1) |
| AUD-09 | Baja | `core/simbolos.py` (`registrar_token`) | El literal `"booleano"` (regla del lenguaje: `verdadero`/`falso` → `booleano`) está en `core`, no en `config` | Renombrar el tipo exige tocar `core` | Inspección | **Escalado** (E-2): requiere una constante nueva en el contrato |
| AUD-10 | Baja | `core/errores.py` | Textos del catálogo con datos que también están en `reglas`: `32` (LEX-005), `.flow`/`.txt` (ARC-002), los escapes (LEX-006), «1 MB» (ARC-006) | Cambiar esos datos deja textos obsoletos (visto en el escenario de extensión c) | Escenario c de §6 | **Escalado** (E-3); la arquitectura §11 ya lo documenta |
| AUD-11 | Baja | `tests/test_afd.py` (`test_conteos`) | Fija 17 reservadas y 15 operadores: la modificación en vivo «agregar `repetir`» pone una prueba en rojo | En la sustentación la batería deja de estar verde tras una modificación correcta | Escenarios a y b de §6 | **Escalado** (E-4) |
| AUD-12 | Baja | `core/lexer.py` | Llamar dos veces a `tokens()`/`analizar()` sobre el mismo `Lexer` duplica los diagnósticos en el manejador. El contrato lo declara «de un solo uso», pero el docstring no lo dice | Uso indebido silencioso | Inspección | Observación (sin cambio; contrato) |
| AUD-13 | Baja | `application/analisis_service.py` | `analizar_texto`/`tokenizar` no normalizan `\r` (solo lo hace `cargar_fuente`, como dice la especificación §6). Con texto pegado que conserve `\r`, este cuenta como columna y entra en lexemas de cadena/comentario | Posible desalineación en la Fase B | Sonda `x\r\n"ab\r\ny` | **Escalado a Fase B** (E-5) |
| AUD-14 | Baja | `application/archivos.py` | `cargar_fuente("")` informa `ARC-005` con nombre `''` | Mensaje poco útil; solo por API | Sonda | Observación |

No se encontraron defectos en: maximal munch, prioridad reservada/identificador, escapes, recuperación en modo pánico y errores consecutivos, fin de archivo en mitad de cadena/comentario/número, posiciones (tabs, `\r\n` normalizado, última línea sin salto, `ñ` y emoji contados como un punto de código), validador estructural, función hash, encadenamiento, rehash completo, colisiones forzadas, clasificación LEX/SIN/ARC, orden de comprobación de archivos, BOM, permisos, rutas con espacios y acentos.

### 5. Correcciones aplicadas

Todas acotadas y coherentes con la arquitectura; ninguna cambia firmas públicas ni valores de la especificación §12. Diff respecto de `dc160e8`: 4 archivos de código/prueba modificados (+25 / −14 líneas) y 1 archivo de pruebas nuevo (`tests/test_auditoria_fase_a.py`, 6 pruebas).

| ID | Cambio | Prueba |
|---|---|---|
| AUD-01 | `SesionAnalisis` da al lexer un `ManejadorErrores` propio que se vacía en cada paso y vuelca sus diagnósticos al manejador del resultado (solo API pública del contrato). 80 000 errores: 9,16 s → 0,60 s; 300 000: 2,35 s | `test_aud01_…` |
| AUD-02 | `guardar_fuente` codifica **antes** de abrir y escribe bytes; `UnicodeEncodeError` → `ARC-005` | `test_aud02_…` |
| AUD-03 | `INFO_CATEGORIAS[PALABRA_RESERVADA]["regex"] = "\|".join(PALABRAS_RESERVADAS)` (sigue siendo un dato, sin funciones) + prueba de coherencia regex ↔ diccionarios para reservadas, operadores y delimitadores | `test_aud03_…` |
| AUD-04 | Alfabeto de la prueba de equivalencia + `n`, `t` | `TestEquivalenciaRegexAFD` |
| AUD-05 | `texto.strip(reglas.ESPACIOS)` | `test_aud05_…` |
| AUD-06 | `explicar_token` reanaliza el lexema `ERROR` y muestra la sugerencia del diagnóstico real | `test_aud06_…` |
| AUD-07 | Texto de la instalación con redimensionado | `test_aud07_…` |

### 6. Regresión

- Antes de corregir, las 6 pruebas nuevas: **5 fallaban** (AUD-01, 02, 05, 06, 07); AUD-03 es latente y se reprodujo en la copia extendida (§7).
- Batería completa tras las correcciones, `/opt/homebrew/bin/python3.14 -m unittest discover -s tests -v`, última línea real:

```
Ran 93 tests in 3.010s

OK
```

- También `OK` con `python3.11` y `python3.12` (`-t .`). Fuzzing (§2.3) repetido tras las correcciones: 20 003 casos, 0 fallos. `grep` de A10 vacíos.

### 7. Prueba de extensibilidad

En copias temporales del proyecto (nunca en el real). «Líneas» = líneas de código de producción tocadas.

| Escenario | Código original (`dc160e8`) | Tras las correcciones |
|---|---|---|
| **(a)** agregar reservada `repetir` | 1 archivo / 1 línea (`PALABRAS_RESERVADAS`). Lexer, tabla y descripción la toman solos. **Defecto:** la regex del modo educativo no la incluye (AUD-03). Pruebas: 86/87 (falla `test_conteos`, que fija 17) | 1 archivo / 1 línea; la regex se actualiza sola. Pruebas: 92/93 (solo `test_conteos`, E-4) |
| **(b)** agregar operador `%` | **No aplicable:** `%` ya es operador aritmético en la especificación §3.6 y en `OPERADORES` (`a % b` → `%` aritmético). Se ensayó en su lugar `**` (el de la arquitectura §11) | — |
| **(b')** agregar operador `**` | 1 archivo / 1 línea; maximal munch correcto (`a ** b` → `**`; `/** c */` sigue siendo comentario). **Defecto:** regex de aritméticos obsoleta, sin prueba que avise. 86/87 (`test_conteos`) | 1 archivo / 2 líneas (`OPERADORES` + regex de aritméticos, exigida por la nueva prueba AUD-03). 92/93 (`test_conteos`) |
| **(c)** reemplazar extensión por `.fl` | 1 archivo / 1 línea en `reglas.py` + el texto de `ARC-002` en `core/errores.py` queda obsoleto (2.º archivo, AUD-10). 77/87: 5 fallos + 5 errores, todos esperables (los ejemplos y las pruebas de archivos usan `.flow`) | Igual |
| **(c')** agregar `.fl` conservando las demás | 1 archivo / 1 línea; `.fl` se carga; 87/87 OK. Texto de `ARC-002` obsoleto | Igual (93/93) |

Conclusión: el principio abierto/cerrado se cumple en el código (ningún algoritmo se tocó en ningún escenario). Las fricciones restantes son de textos (E-3) y de pruebas que fijan conteos (E-4).

### 8. Opinión sobre las decisiones del desarrollador (para el arquitecto)

| Decisión | Opinión | Motivo |
|---|---|---|
| **D-26** (`analisis_service.py` ~228 líneas, `simbolos.py` ~193; no dividir) | **Aprobada** | El archivo está organizado por secciones y se explica bien. Tras AUD-01/06/07 queda en 239 líneas. Si en la Fase B crece más, mover `ExplicacionToken` + `explicar_token` a `application/educativo.py` es un corte limpio (sin dependencias cruzadas) |
| **D-27** (anotar la declaración en cualquier aparición mientras `linea_declaracion` sea `None`) | **Aprobada** | Es la lectura correcta de la especificación §9 («se conserva la primera declaración»); con la alternativa, `x = 1; numero x;` perdería la declaración real. No altera ningún valor de §12. Comprobado con `numero x … texto x` (se conserva `numero`) |
| **D-28** (`resumen()` con singular/plural y solo tipos presentes) | **Aprobada** | Cumple literalmente los dos ejemplos del contrato y es mejor texto para la UI |

### 9. Escalados al arquitecto

| # | Tema | Propuesta |
|---|---|---|
| E-1 (AUD-08) | Colisiones históricas (14) frente a visibles (7) en `correcto.flow` | Mostrar ambas en la UI y en la especificación §12.1: «14 colisiones al insertar (7 visibles tras redimensionar = entradas − cubetas ocupadas)». No requiere cambiar `EstadisticasTabla` (se calcula) |
| E-2 (AUD-09) | `"booleano"` literal en `core/simbolos.py` | Añadir a `reglas` un dato como `TIPO_DATO_PALABRA = {"verdadero": "booleano", "falso": "booleano"}` y usarlo en `registrar_token`. Cambia el contrato (constante nueva) |
| E-3 (AUD-10) | Textos de `CATALOGO` con datos de `reglas` | O bien aceptarlo (ya está en la arquitectura §11 como «¿Algo más?»), o bien plantillas `{maximo}`, `{extensiones}` rellenadas por quien reporta. Esto último añade la dependencia `errores → reglas`; recomiendo aceptarlo y recordarlo en la guía de sustentación |
| E-4 (AUD-11) | `test_conteos` se pone en rojo con `repetir`/`**` | Decidir si la guía de sustentación dice «actualizar el conteo de la prueba» (recomendado: muestra que las pruebas vigilan la especificación) o si la prueba pasa a `>=` |
| E-5 (AUD-13, AUD-02) | Fase B | El editor debe normalizar `\r\n`/`\r` del texto pegado antes de `tokenizar`/`SesionAnalisis`. En PCs del laboratorio con Tcl 8.6 un emoji puede llegar como dos sustitutos (de ahí AUD-02); la correspondencia columna del lexer ↔ índice de Tk con caracteres fuera del BMP no está verificada y debe incluirse en las pruebas manuales M1–M3. Aquí hay Tcl 9.0 |
| E-6 | Nomenclatura | `docs/06_auditoria.md` (este) y `docs/06_guia_sustentacion.md` (previsto en B8) comparten el prefijo `06`; renumerar uno de los dos |

No se encontraron erratas en la especificación ni en la arquitectura que exigieran corrección; la única aclaración recomendada es la de E-1.

### 10. Veredicto

**APROBADO CON OBSERVACIONES.** El núcleo cumple el contrato y la especificación: el lexer es dirigido por tablas de AFD reales, la coincidencia más larga y la recuperación en modo pánico son correctas bajo fuzzing, la tabla hash es propia y rehashea por completo, y el manejador clasifica bien los tres tipos de error. Los tres hallazgos de severidad media (rendimiento cuadrático, pérdida de datos al guardar, regla duplicada) están corregidos con prueba. Quedan seis puntos para el arquitecto (E-1 a E-6), ninguno bloqueante para empezar la Fase B.
