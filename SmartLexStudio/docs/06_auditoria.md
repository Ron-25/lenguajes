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

---

## Auditoría final (Fase B y proyecto completo)

- **Fecha:** 2026-11-15
- **Auditor / modelo:** reviewer-opus / claude-opus-5-5
- **Base de comparación:** commit `dc4e725` («Fase B (Sonnet): interfaz tkinter tipo IDE, main.py y prueba de humo»), 109 pruebas OK
- **Veredicto:** **APROBADO CON OBSERVACIONES** (0 críticos; 1 alto y 1 medio, corregidos con prueba; 5 bajos y 6 sugerencias)

### 1. Alcance

| Incluido | Excluido |
|---|---|
| Todo el proyecto: `config/`, `core/`, `application/`, `ui/`, `main.py`, `tests/` | `ejemplos/*.flow` (no se modificaron) |
| Contraste con `instrucciones .pdf` (6 requisitos), `docs/03_especificacion.md`, `docs/02_arquitectura.md`, `agents/tareas.md` (B0–B7 y criterios de la Fase B), `agents/decisiones.md` (D-36…D-40) | B8 (manual de usuario, guía de sustentación, README): pendiente del paso 11 |
| Evidencia visual: `docs/capturas/1..5_*.png` (recapturadas tras las correcciones con `docs/capturas/capturar.py`, ajustado para mostrar el Modo educativo y el detalle de un error) | — |

### 2. Metodología (todo ejecutado)

1. Batería completa con `/opt/homebrew/bin/python3.14` (Tk 9.0) tras cada corrección; además con python3.11 y 3.12 (sin `_tkinter`: las 17 pruebas de UI se omiten y el resto pasa).
2. Comandos de arquitectura: `grep -rn tkinter core application config` → vacío; `grep -rn "core.lexer\|core.validador\|core.simbolos\|core.afd" ui/` → vacío; `grep -rn "#[0-9a-fA-F]\{6\}" ui/ | grep -v estilos.py` → vacío; `grep -rn '"booleano"' core application` → vacío.
3. Script propio de robustez (`messagebox`/`filedialog` sustituidos con `mock.patch`, ningún diálogo modal real): 28 comprobaciones de secuencias Abrir→Analizar→Paso a paso→Detener→Limpiar→Analizar, analizar/paso sin archivo, archivo inexistente / vacío / Latin-1 / extensión `.py` / carpeta, guardar con ruta nueva, doble clic real (por `bbox` de la fila) en un error, estados de los botones, edición en `TERMINADO`, `\r\n`/`\r`, reanálisis y paso a paso desde `TERMINADO`.
4. Medición de rendimiento con 1 000, 3 000 y 5 000 líneas (≈ 50 000 tokens, 243 KB): tiempo total, duración de cada *tick* y desglose por operación.
5. Modo consola: entrada `n`, `s`, sin ruta (la pide), archivo inexistente y **entrada cerrada** (`</dev/null`).
6. Ensayo de extensibilidad en una copia: añadir `repetir` a `PALABRAS_RESERVADAS`.
7. Mediciones `winfo_*` de la barra de herramientas y capturas reales (2.ª toma, tras corregir).

### 3. Hallazgos

| ID | Severidad | Archivo | Problema | Impacto | Prueba que lo reproduce | Estado |
|---|---|---|---|---|---|---|
| AUD-15 (O-1) | Sugerencia | `ui/interfaz.py` `_al_seleccionar_token` | Al elegir un token, el panel no cambia a «Modo educativo» | Ninguno: **B5.9 exige «sin cambiar de pestaña»**. En la captura original el driver hacía `selection_set` estando en Estadísticas; la explicación sí se escribía en la pestaña oculta | Driver ajustado: tras seleccionar se ve la explicación (captura 4) | No es defecto (comportamiento contratado) |
| AUD-16 | Media | `ui/editor.py`, `ui/interfaz.py` | El aviso de cambio con *debounce* (300 ms) pendiente al pulsar Analizar se emitía después y, si el análisis ya había terminado (textos cortos), pasaba a `LISTO` con «los resultados están desactualizados» | Resultado correcto marcado como obsoleto; el aviso ocurría con el diálogo «¿ver tabla?» abierto | `test_auditoria_fase_b.test_aud16_…` (falla en `dc4e725`) | Corregido: `EditorCodigo.descartar_cambio_pendiente()` (también en `establecer_texto`), llamado al iniciar la sesión |
| AUD-17 | **Alta** | `ui/paneles.py` `agregar_token`, `ui/componentes.py` `escribir`, `ui/editor.py` `resaltar_token_actual` | `Treeview.see`, `Text.see` se llamaban **una vez por token**; `Treeview.see` es lineal en el número de filas → coste cuadrático | 5 000 líneas: **79 s** de análisis y *ticks* que crecían hasta ~1 s (UI congelada); 3 000 líneas: 20 s (8 s solo en `see`) | `test_aud17_un_solo_desplazamiento_por_tick` (cuenta llamadas a `see`; falla en `dc4e725`) | Corregido: un único desplazamiento por ciclo de eventos (`after_idle`). Ahora 1 000 líneas 3,4 s (*tick* máx. 0,02 s); 5 000 líneas **5,7 s** (*tick* máx. 0,098 s) |
| AUD-18 (O-4) | Baja | `ui/estilos.py` | El tema `clam` impone a `TButton` un ancho mínimo de 11 caracteres: «Abrir» medía 125 px como «Analizar» y, al ser planos, parecían separados de forma desigual | Barra visualmente desequilibrada | `test_aud18_…`; `winfo_width`: antes todos 125 px, ahora 58/80/104/131/94/75/68 | Corregido (`width=0` en el estilo) |
| AUD-19 (O-5) | Baja | `ui/editor.py` `establecer_texto` | Tras cargar, la marca `insert` quedaba **al final** del texto (la barra de estado decía «Lín 1, Col 1», falso) y al terminar la vista quedaba en el último token | Editor desplazado al final tras analizar; primera tecla se escribía al final | `test_aud19_…` | Corregido: cursor a `1.0` al cargar; `resaltar_token_actual(None)` devuelve la vista al cursor (al inicio, o al último error estructural al que se navegó) |
| AUD-20 (O-3) | Baja | `ui/paneles.py` | Cabecera «Cubeta» truncada (60 px); «Mensaje»/«Sugerencia» de Errores ilegibles en un panel de ~480 px | El usuario no ve el mensaje completo del manejador de errores (req. 4) sin desplazar en horizontal | `test_aud20_…` | Corregido: columna a 72 px y **detalle completo** (código, título, mensaje, sugerencia) bajo la tabla al seleccionar un error (captura 5) |
| AUD-21 | Baja | `main.py` `_modo_consola` | `input()` sin manejo de `EOFError`/`KeyboardInterrupt`: con la entrada cerrada o Ctrl+D se imprimía una traza | Modo consola poco robusto (p. ej. `python main.py --consola x.flow < /dev/null`) | `test_aud21_…` (subproceso con `stdin=DEVNULL`) | Corregido: `_preguntar()` trata EOF/Ctrl+C como respuesta vacía |
| AUD-22 | Sugerencia | `ui/interfaz.py` | Importación sin uso de `TEMA` | Código muerto | Inspección | Corregido |
| AUD-23 (O-2) | Sugerencia | `ui/componentes.py` `PanelConsola` | La primera línea visible de la consola aparece cortada | Cosmético: `Text.see("end")` alinea la última línea abajo y el alto del panel no es múltiplo de la línea; no se pierde contenido | Captura 1/5 | No se corrige (comportamiento estándar del `Text` de Tk con desplazamiento por píxeles; cualquier alternativa corta la última línea, que es la importante) |
| AUD-24 | Baja | `ui/interfaz.py` `_mostrar_error_archivo` | Los errores `ARC-*` de aperturas fallidas se **acumulan** en Errores y se mezclan con los de un análisis ya terminado; el contador de la barra no los incluye (15 vs 16 filas) | Confusión menor | Script de robustez: tras 5 aperturas fallidas, 5 filas | Escalado (E-7): B5.2 manda añadirlo a Errores; propuesta: limpiar filas `ARC-*` previas o reiniciar resultados al fallar la apertura |
| AUD-25 | Sugerencia | `ui/paneles.py` `mostrar_explicacion` | Formatea `ExplicacionToken.detalle` partiendo el texto por `": "`; la 1.ª línea («Lexema … Categoría … Posición …») queda en un único campo (captura 4) | Acoplamiento al formato textual del servicio; cosmético | Captura 4 | Observación (E-8): si se permite, `ExplicacionToken` podría exponer los campos; hoy D-29 congela el servicio |
| AUD-26 | Sugerencia | `ui/interfaz.py` `_al_editar` | Cada pausa al escribir re-tokeniza todo el texto: 0,5 s con 5 000 líneas | Ligera pausa al editar archivos grandes (los ejemplos tienen < 40 líneas) | Medición | Limitación documentada |
| AUD-27 | Sugerencia | `ui/interfaz.py`, `ui/paneles.py`, `main.py` | El texto de veredicto («válido/inválido», «VÁLIDA/INVÁLIDA») se arma en tres sitios | Duplicación menor | Inspección | Observación |

No hay colores ni reglas léxicas duplicadas en `ui/` (los colores solo en `ui/estilos.py`; el árbol del panel lateral y la tabla de transiciones del Modo educativo se leen de `config.reglas`). La UI solo importa `application/`, `config/` y los modelos de `core/modelos.py`. Funciones largas: `aplicar_tema` (49 líneas, lista de estilos) y `mostrar_estadisticas` (45, dibujo secuencial con funciones internas): aceptables. Ninguna prueba es vacía: cada una de las 12 de humo afirma conteos, estados o índices concretos.

### 4. Correcciones aplicadas

Archivos tocados (71 líneas añadidas, 8 quitadas): `ui/editor.py`, `ui/paneles.py`, `ui/componentes.py`, `ui/estilos.py`, `ui/interfaz.py`, `main.py`. No se tocó `core/`, `application/`, `config/` ni ninguna firma pública del contrato (solo se **añadió** `EditorCodigo.descartar_cambio_pendiente()` y la etiqueta `PanelResultados.detalle_error`).
Pruebas nuevas: `tests/test_auditoria_fase_b.py` (6). Se comprobó que **las 6 fallan** sobre el código de `dc4e725` (exportado con `git archive`: 5 FAIL + 1 ERROR) y pasan tras las correcciones.

### 5. Regresión

| Momento | Resultado |
|---|---|
| Inicio (`dc4e725`) | `Ran 109 tests in 11.532s` · `OK` |
| Tras AUD-16…AUD-22 (python3.14, Tk 9.0), ejecución final | `Ran 115 tests in 20.678s` · `OK` |
| python3.11 / python3.12 (sin Tk) | `OK (skipped=17)` |
| Copia con `repetir` añadido | 114/115: solo falla `test_conteos_de_flowlang_1_0` con su mensaje (D-32). Lexer, resaltado (`tok_PALABRA_RESERVADA`), panel lateral («Palabras reservadas (18)») y Modo educativo la reconocen sin tocar otro archivo → **criterio de la Fase B cumplido** |

Correcciones de la Fase A vigentes: `tests/test_auditoria_fase_a.py` en verde; valores de la especificación §12 reproducidos (`test_integracion`); B0 aplicado (`TIPO_DATO_BOOLEANO`, `test_conteos_de_flowlang_1_0`, docstring de un solo uso).

Robustez (script propio, 28 comprobaciones): todas OK tras las correcciones (antes: 2 fallos, AUD-16 y AUD-19). Rendimiento: abrir 5 000 líneas 0,55 s; tecla 0,01 s; análisis completo 5,7 s con el bucle de eventos atendido entre *ticks* (máx. 0,098 s).

### 6. Verificación requisito por requisito del PDF

| Req. | Evidencia | Estado |
|---|---|---|
| **1** Definir un lenguaje (20 pts) | FlowLang 1.0: `docs/03_especificacion.md`, `config/reglas.py` (17 reservadas, 4 AFD como datos); `tests/test_afd.py`, `tests/test_lexer.py` | **Cumple** |
| **2** Verificar validez de la cadena (20 pts) | `core/lexer.py` (AFD por tablas, coincidencia más larga), `core/validador.py`; `ResultadoAnalisis.es_valida`; `test_integracion.test_correcto` (VÁLIDA) / `test_incorrecto` (INVÁLIDA); consola y Estadísticas muestran léxico/estructura/global (capturas 1, 3, 5) | **Cumple** |
| **3** Tabla de símbolos por función hash (25 pts) | `core/simbolos.py` (hash polinomial propio, encadenamiento, redimensionado); entrada con lexema, categoría, tipo, valor, declaración, apariciones, hash, cubeta; `tests/test_simbolos.py`; UI en orden de cubeta con colisiones resaltadas (captura 2; `test_colisiones_en_el_resumen`: 14 y 7) | **Cumple** |
| **4** Manejador de errores que informe al usuario (25 pts) | `core/errores.py` (LEX/SIN/ARC con código, mensaje y sugerencia), modo pánico; `tests/test_errores.py`; en la UI: pestaña Errores con detalle completo (AUD-20), marcas en el editor y ✗ en el margen (captura 5), `messagebox.showerror` para errores de archivo | **Cumple** |
| **5a** Interfaz de errores **durante** la evaluación (10 pts) | `SesionAnalisis.siguiente_paso` + `VentanaPrincipal._consumir_paso`: cada diagnóstico se añade a Errores, consola y editor en el paso en que aparece; `test_ui_humo.test_errores_durante_la_evaluacion` (1 fila en Errores y marca en `2.11–2.14` con la sesión sin terminar), `test_progresividad`, `test_integracion.test_progresividad` | **Cumple** |
| **5b** Alternativa **al final** de desplegar la tabla de símbolos | `_finalizar`: `askyesno("Análisis terminado", "…¿Desea ver la tabla de símbolos?")` + botón permanente «Ver tabla de símbolos» + pestaña habilitada solo al terminar; `test_flujo_completo_incorrecto` (una llamada, 18 filas), `test_progresividad` (deshabilitada a mitad); modo consola: `(s/n)` (`test_consola_incorrecto_con_tabla_y_sin_ruta`) | **Cumple** |
| **6** Solicitar el archivo para iniciar | `main.py` → `VentanaPrincipal()` (`solicitar_archivo=True`) abre `askopenfilename` («Seleccione el archivo con las cadenas de entrada»); Analizar/Paso sin fuente vuelve a pedirlo (D-36); validación en `application/archivos.py`; `test_requisito_6_solicita_archivo`, `test_requisito_6_cancelado`, `tests/test_archivos.py`; consola: `input("Archivo de entrada: ")` | **Cumple** |

Verificaciones M1–M3: cubiertas por las pruebas automáticas citadas y por las capturas reales (5 = estado final de M1; 2 = M2 aceptado). M4 (emoji): `test_fuera_del_bmp` en verde con Tk 9.0; con Tcl/Tk 8.6 queda como limitación visual documentada (D-34). Se recomienda que una persona repita M1–M3 en el equipo de la sustentación.

### 7. Opinión sobre D-36…D-40

| Decisión | Opinión | Motivo |
|---|---|---|
| **D-36** (Analizar activo en `SIN_FUENTE`; Abrir y Limpiar activos en `ANALIZANDO`) | **Aprobada** | Es la única forma de que el botón cumpla B5.1/req. 6. Abrir/Limpiar durante el análisis cancelan el temporizador limpiamente (verificado en la secuencia de robustez) |
| **D-37** (`marcar_errores` acumula; subrayado del lexema del diagnóstico) | **Aprobada** | Necesario para la evaluación progresiva; `limpiar_marcas` se llama al reiniciar/editar, así que no quedan marcas viejas |
| **D-38** (detectar Tk en un subproceso) | **Aprobada** | Reproducido el riesgo con Tk 9.0.4; coste ~1 s. La función está duplicada en `test_auditoria_fase_b.py` a propósito (evitar importar otro módulo de prueba) |
| **D-39** (tabla de transiciones del AFD en el Modo educativo, leída de `reglas.AUTOMATAS`) | **Aprobada** | Cumple la arquitectura §9 sin tocar el servicio; ver AUD-25 sobre el formateo del detalle |
| **D-40** (sin capturas) | **Superada** | El orquestador y esta auditoría tomaron capturas reales (`docs/capturas/`). La decisión fue correcta en su momento (no declarar lo no verificado) |

### 8. Escalados al arquitecto

| # | Tema | Propuesta |
|---|---|---|
| E-7 (AUD-24) | Errores de archivo acumulados en Errores tras aperturas fallidas | Al fallar `abrir_archivo`, quitar las filas `ARC-*` anteriores (o reiniciar resultados si no hay sesión) y contar el error en la barra de estado |
| E-8 (AUD-25) | Modo educativo parsea texto | Si se relaja D-29, que `ExplicacionToken` exponga campos (posición, regla, recorrido) en vez de un `detalle` textual |

Ninguno es bloqueante.

### 9. Limitaciones conocidas

- Re-resaltado completo al editar (0,5 s con 5 000 líneas; AUD-26). El análisis animado de archivos grandes supera los 3 s previstos (5,7 s con 5 000 líneas) por el coste de dibujo de Tk, pero la UI sigue respondiendo.
- Primera línea de la consola cortada (AUD-23, cosmético).
- Con Tcl/Tk 8.6, el resaltado de tokens posteriores a un emoji puede desplazarse (D-34); los tokens y posiciones del análisis son correctos.
- `cargar_fuente("")` → `ARC-005` con nombre vacío (AUD-14, ya observado en la Fase A; visible en el modo consola si se pulsa Enter sin ruta).
- B8 (manual, guía de sustentación, README ampliado) pendiente.

### 10. Veredicto

**APROBADO CON OBSERVACIONES.** Los seis requisitos del PDF se cumplen con evidencia ejecutada. La arquitectura por capas se respeta (UI sin lógica léxica, núcleo sin tkinter, colores y reglas en un único lugar). El único hallazgo alto (coste cuadrático al animar entradas grandes, que congelaba la UI ~1 s por *tick*), el medio (aviso de cambio fuera de tiempo) y los bajos de comportamiento (cursor al final tras cargar, EOF en consola, columnas truncadas, botones) están corregidos con pruebas que fallan sobre `dc4e725`. Quedan dos escalados menores (E-7, E-8) y la tarea B8.

---

## Revisión de cierre

- **Fecha:** 2026-11-15 · **Auditor:** reviewer-opus / claude-opus-5-5 · **Base:** `555ea7b` (B9, B10, manual, README; 117 pruebas)
- **Veredicto de cierre:** **APROBADO** (sin hallazgos abiertos de severidad media o superior)

### 1. Diff de B9/B10 (`git diff 1af68fb 555ea7b -- ui application tests`)

| Cambio | Revisión |
|---|---|
| B9 / D-42: `PanelResultados.quitar_errores_de_archivo()` antes de `agregar_error` en `_mostrar_error_archivo` | Correcto: solo borra filas con `tipo == ARCHIVO`, refresca el detalle (AUD-20) y conserva los 15 errores de un análisis terminado. La prueba `test_un_solo_error_de_archivo` cubre los dos casos (sin análisis → 1 fila; tras analizar `incorrecto.flow` → 16 con un solo `ARC`). Resuelve E-7 / AUD-24 |
| B10 / D-43: `explicar_token` separa Lexema / Categoría / Posición en líneas | Correcto y mínimo (2 líneas en el servicio); `test_detalle_una_linea_por_dato` exige `Campo: valor` en todas las líneas. Resuelve el aspecto visible de E-8 / AUD-25 (captura 4) |
| AUD-16…AUD-22 | Siguen vigentes: `tests/test_auditoria_fase_b.py` en verde |

### 2. Hallazgo nuevo

| ID | Severidad | Archivo | Problema | Impacto | Prueba | Estado |
|---|---|---|---|---|---|---|
| AUD-28 | Baja | `ui/interfaz.py` (`VentanaPrincipal`) | Al destruir la ventana quedaban `after` pendientes en el intérprete: el *tick* del análisis (`_tick`), los desplazamientos diferidos de AUD-17 (`_bajar_al_final`, `_ver_ultimo_token`, `_ver_token_actual`), el *debounce* de 300 ms del editor y la solicitud inicial de 100 ms. tkinter borra los comandos Python al destruir los widgets, pero Tcl conserva los eventos; el bucle de eventos (compartido por hilo) los dispara en la siguiente ventana y Tcl imprime `invalid command name "…_tick" … ("after" script)` | Traza intermitente en stderr de la batería (dependía de si la prueba destruía la ventana con un análisis en curso); en uso real, solo al cerrar la ventana a mitad de un análisis | `tests/test_auditoria_fase_b.py::TestDestruccion::test_aud28_destruir_con_after_pendientes` (subproceso, porque Tcl escribe en el descriptor 2): falla en `555ea7b` con `_bajar_al_final` y `_tick` huérfanos; pasa tras la corrección | Corregido: `VentanaPrincipal.destroy()` cancela en Tcl (`after cancel`) todos los ids de `after info` antes de `super().destroy()`. Se cancela solo en Tcl (no con `after_cancel`) porque cada widget hijo borra su propio comando al destruirse; borrarlo antes provoca `TclError: can't delete Tcl command` |

### 3. Documentación verificada contra el código

`README.md` y `docs/04_manual_usuario.md`: atajos (Ctrl/Cmd+O, Ctrl/Cmd+S, F5, F10, Esc, F1), comandos (`--consola` con y sin ruta), 19 diagnósticos, 4 AFD, 17 reservadas, capacidad inicial 17 y factor 0,75, ejemplos de `LEX-003` (`3.`, `.5`, `3.4.5`), `SIN-006` con `( }`, comando de pruebas con `-t .` y estructura de carpetas: **coinciden**.
Errata corregida en el manual (§4 y §8): decía que *Detener* libera el editor; en realidad la pausa mantiene la sesión en `ANALIZANDO` y el editor sigue en solo lectura hasta terminar o *Limpiar*.

### 4. Regresión

| Corrida (`python3.14 -m unittest discover -s tests`, sin `-v`) | Resultado | Trazas `("after" script)` en stderr |
|---|---|---|
| 1 | `Ran 118 tests in 24.373s` · `OK` | 0 |
| 2 | `Ran 118 tests in 24.163s` · `OK` | 0 |
| 3 | `Ran 118 tests in 24.253s` · `OK` | 0 |

### 5. Veredicto de cierre

**APROBADO.** B9 y B10 son correctos y están probados; AUD-28 corregido con prueba que falla en `555ea7b`; documentación de usuario coherente con el código tras una errata. Limitaciones que siguen vigentes (sin cambios): AUD-23 (consola), AUD-26 (re-resaltado en archivos grandes), D-31, D-34.

