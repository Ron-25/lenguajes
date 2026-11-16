# Revisiones — SmartLex Studio

Aquí se registran las auditorías de cada fase (reviewer-opus), las discrepancias que el desarrollador encuentre en el contrato y las aprobaciones del arquitecto. Se añade al final; no se borra historial.

## Índice de revisiones

| # | Fecha | Fase / Tarea | Revisor | Modelo | Veredicto | Hallazgos abiertos |
|---|---|---|---|---|---|---|
| 1 | 2026-11-15 | Fase A (A1–A10) | reviewer-opus | claude-opus-5-5 | Aprobado con observaciones | 6 escalados (E-1…E-6) |
| 2 | 2026-11-15 | Aprobación formal de la Fase A | architect-fable | claude-fable-5-2 | **Aprobada; Fase B autorizada** | Ninguno bloqueante. E-1…E-6 resueltos en D-30…D-35; D-26…D-28 ratificadas en D-29; pendientes de implementar en B0 (E-2, E-4), B2/B6 (E-5), B4 (E-1) y B8 (E-6). E-3 queda como limitación documentada |
| 3 | 2026-11-15 | Fase B (B0–B7) y proyecto completo (paso 9) | reviewer-opus | claude-opus-5-5 | Aprobado con observaciones | 2 escalados menores (E-7, E-8); B8 pendiente |
| 4 | 2026-11-15 | Revisión de cierre (B9, B10, manual, README; base `555ea7b`) | reviewer-opus | claude-opus-5-5 | **Aprobado** | Ninguno. AUD-28 corregido; E-7 resuelto por B9, E-8 por B10 |

---

## Plantilla de revisión (copiar y completar)

### Revisión N — Fase X / Tarea(s) …

- **Fecha:**
- **Revisor / modelo:**
- **Alcance revisado:** (archivos y commit o estado)
- **Comando de pruebas y resultado:** (`python -m unittest discover -s tests -t . -v` → n pruebas, n fallos)
- **Veredicto:** Aprobado / Aprobado con observaciones / Rechazado

#### Verificación del contrato

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Nombres públicos idénticos a `agents/tareas.md` | | |
| `core/` y `application/` sin tkinter | | |
| `config/reglas.py` sin funciones ni clases | | |
| Sin `re` en producción | | |
| Valores de la especificación §12 reproducidos | | |
| Pruebas requeridas presentes | | |

#### Hallazgos

| ID | Severidad (Bloqueante / Mayor / Menor / Sugerencia) | Archivo:línea | Descripción | Acción propuesta | Estado |
|---|---|---|---|---|---|
| | | | | | |

#### Requisitos del PDF afectados
(Actualizar también `docs/matriz_requisitos.md`.)

---

## Plantilla de discrepancia del contrato (desarrollador)

| Fecha | Tarea | Qué dice el contrato | Qué problema hay | Qué se implementó | Resuelto por el arquitecto |
|---|---|---|---|---|---|
| | | | | | |

## Discrepancias y notas del desarrollador (Fase A)

| Fecha | Tarea | Qué dice el contrato | Qué problema hay | Qué se implementó | Resuelto por el arquitecto |
|---|---|---|---|---|---|
| 2026-11-15 | A10 | «Ningún archivo de `core/` o `application/` supera ~200 líneas» | `application/analisis_service.py` tiene 228 líneas (`core/simbolos.py` 193) | Se mantiene sin dividir (ver D-26) | Pendiente |
| 2026-11-15 | A10 | Regla general 6 usa `-t .`; el encargo del orquestador omite `-t .` | Ninguno: ambas formas de `unittest discover` funcionan y dan 87 pruebas | Sin cambios | — |

---

### Revisión 1 — Fase A / Tareas A1–A10

- **Fecha:** 2026-11-15
- **Revisor / modelo:** reviewer-opus / claude-opus-5-5
- **Alcance revisado:** `config/reglas.py`, `core/*.py`, `application/*.py`, `tests/*.py` en el commit `dc160e8` + correcciones sin commit
- **Comando de pruebas y resultado:** `/opt/homebrew/bin/python3.14 -m unittest discover -s tests -v` → `Ran 93 tests in 3.010s` / `OK` (87 originales + 6 de `tests/test_auditoria_fase_a.py`)
- **Veredicto:** Aprobado con observaciones. Detalle completo en `docs/06_auditoria.md`.

#### Verificación del contrato

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Nombres públicos idénticos a `agents/tareas.md` | Cumple | Revisión de firmas |
| `core/` y `application/` sin tkinter | Cumple | `grep` vacío; `test_dominio_sin_tkinter` |
| `config/reglas.py` sin funciones ni clases | Cumple | `grep` vacío |
| Sin `re` en producción | Cumple | `grep` vacío |
| Valores de la especificación §12 reproducidos | Cumple | `test_integracion`, `test_lexer` |
| Pruebas requeridas presentes | Cumple (alfabeto de A3 corregido, AUD-04) | `tests/` |

#### Hallazgos

| ID | Severidad (Bloqueante / Mayor / Menor / Sugerencia) | Archivo:línea | Descripción | Acción propuesta | Estado |
|---|---|---|---|---|---|
| AUD-01 | Mayor (Media) | `application/analisis_service.py` `siguiente_paso` | Copia de toda la lista de diagnósticos en cada paso: coste cuadrático (80 000 errores: 9,16 s) | Manejador por paso que se vacía | Corregido; `test_aud01_…` |
| AUD-02 | Mayor (Media) | `application/archivos.py` `guardar_fuente` | `UnicodeEncodeError` sin `ARC-005` y archivo existente truncado | Codificar antes de abrir | Corregido; `test_aud02_…` |
| AUD-03 | Mayor (Media) | `config/reglas.py` `INFO_CATEGORIAS` | Regex de reservadas duplicada a mano; queda obsoleta al agregar `repetir`; sin prueba de coherencia regex ↔ diccionarios | Derivar con `"\|".join(...)` + prueba | Corregido; `test_aud03_…` |
| AUD-04 | Menor (Baja) | `tests/test_afd.py` `ALFABETO` | Falta la letra `n` del contrato A3; mutación del escape `\n` no detectada por la prueba | Añadir `n`, `t` | Corregido |
| AUD-05 | Menor (Baja) | `application/archivos.py` `cargar_fuente` | `ARC-003` con `str.strip()` Unicode en vez de `reglas.ESPACIOS` | `strip(reglas.ESPACIOS)` | Corregido; `test_aud05_…` |
| AUD-06 | Menor (Baja) | `application/analisis_service.py` `explicar_token` | Sugerencia genérica de `LEX-001` en el modo educativo (la real es específica) | Reutilizar el diagnóstico del lexer | Corregido; `test_aud06_…` |
| AUD-07 | Menor (Baja) | `application/analisis_service.py` `_texto_instalacion` | «colisión, cubeta N, redimensionada» mezcla cubeta vieja y nueva | Reformular el texto | Corregido; `test_aud07_…` |
| AUD-08 | Mayor (Media) | `core/simbolos.py`; espec. §12.1 | Colisiones históricas 14 vs 7 visibles en la tabla final | Mostrar ambas | Escalado (E-1) |
| AUD-09 | Menor (Baja) | `core/simbolos.py` `registrar_token` | Literal `"booleano"` en `core` | Constante en `reglas` (cambia contrato) | Escalado (E-2) |
| AUD-10 | Menor (Baja) | `core/errores.py` | Textos con datos de `reglas` (32, `.flow`/`.txt`, escapes, 1 MB) | Aceptar y documentar | Escalado (E-3) |
| AUD-11 | Sugerencia (Baja) | `tests/test_afd.py` `test_conteos` | Se pone en rojo con las modificaciones en vivo | Decidir política | Escalado (E-4) |
| AUD-12 | Sugerencia (Baja) | `core/lexer.py` | Reusar `tokens()` duplica diagnósticos (contrato: un solo uso) | Ninguna | Observación |
| AUD-13 | Menor (Baja) | `application/analisis_service.py` | `\r` no se normaliza fuera de `cargar_fuente` | Normalizar en el editor (Fase B) | Escalado (E-5) |
| AUD-14 | Sugerencia (Baja) | `application/archivos.py` | `cargar_fuente("")` → `ARC-005` con nombre vacío | Ninguna | Observación |

Decisiones revisadas: D-26 aprobada, D-27 aprobada, D-28 aprobada (motivos en `docs/06_auditoria.md` §8).

#### Requisitos del PDF afectados
Requisito 4 (manejador de errores): AUD-02, AUD-05, AUD-06. Requisito 5 (interfaz durante la evaluación): AUD-01, AUD-07. Requisito 3 (tabla de símbolos): AUD-08. Ninguno queda incumplido.

---

### Revisión 3 — Fase B (B0–B7) y auditoría final del proyecto

- **Fecha:** 2026-11-15 · **Revisor:** reviewer-opus (claude-opus-5-5) · **Base:** `dc4e725` · **Detalle:** `docs/06_auditoria.md`, «Auditoría final»
- **Veredicto:** APROBADO CON OBSERVACIONES · Requisitos 1–6 del PDF: **cumplen** (evidencia en la auditoría §6 y en `docs/matriz_requisitos.md`)

#### Verificación del contrato

| Comprobación | Resultado | Evidencia |
|---|---|---|
| `ui/` no importa lexer/validador/simbolos/afd | OK | `grep` vacío |
| `core/`, `application/`, `config/` sin tkinter | OK | `grep` vacío |
| Colores solo en `ui/estilos.py` | OK | `grep` vacío |
| Nombres de B1–B7 | OK | Clases y métodos presentes; se añadió `EditorCodigo.descartar_cambio_pendiente()` |
| Prueba de humo B6 | OK | 12 pruebas en verde |
| Extensibilidad (`repetir`) | OK | Solo falla `test_conteos_de_flowlang_1_0` (D-32) |
| Batería | OK | `Ran 115 tests in 20.678s` · `OK` (python3.14); 3.11/3.12 `OK (skipped=17)` |

#### Hallazgos

| ID | Severidad | Archivo | Descripción | Acción | Estado |
|---|---|---|---|---|---|
| AUD-15 | Sugerencia | `ui/interfaz.py` | (O-1) seleccionar token no cambia a Modo educativo | Ninguna: B5.9 lo contrata así | No es defecto |
| AUD-16 | Mayor (Media) | `ui/editor.py`, `ui/interfaz.py` | Aviso de cambio pendiente invalidaba un análisis recién terminado | `descartar_cambio_pendiente()` | Corregido; `test_aud16_…` |
| AUD-17 | Mayor (Alta) | `ui/paneles.py`, `ui/componentes.py`, `ui/editor.py` | `see` por token, cuadrático: 79 s y *ticks* de ~1 s con 5 000 líneas | Un desplazamiento por ciclo (`after_idle`): 5,7 s, *tick* ≤ 0,1 s | Corregido; `test_aud17_…` |
| AUD-18 | Menor (Baja) | `ui/estilos.py` | (O-4) ancho mínimo de 11 caracteres de `clam` en los botones | `width=0` | Corregido; `test_aud18_…` |
| AUD-19 | Menor (Baja) | `ui/editor.py` | (O-5) cursor al final tras cargar; vista final en el último token | Cursor a 1.0; vista vuelve al cursor al terminar | Corregido; `test_aud19_…` |
| AUD-20 | Menor (Baja) | `ui/paneles.py` | (O-3) «Cubeta» y mensajes de error truncados | 72 px + detalle completo del error seleccionado | Corregido; `test_aud20_…` |
| AUD-21 | Menor (Baja) | `main.py` | EOF/Ctrl+C en `--consola` → traza | `_preguntar()` | Corregido; `test_aud21_…` |
| AUD-22 | Sugerencia | `ui/interfaz.py` | Import sin uso (`TEMA`) | Quitar | Corregido |
| AUD-23 | Sugerencia | `ui/componentes.py` | (O-2) primera línea de consola cortada | Ninguna (desplazamiento por píxeles de Tk) | Observación |
| AUD-24 | Menor (Baja) | `ui/interfaz.py` | Errores `ARC-*` de aperturas fallidas se acumulan en Errores | Limpiar filas `ARC-*` previas | Escalado (E-7) |
| AUD-25 | Sugerencia | `ui/paneles.py` | Modo educativo parsea `detalle` textual | Campos en `ExplicacionToken` si se relaja D-29 | Escalado (E-8) |
| AUD-26 | Sugerencia | `ui/interfaz.py` | Re-resaltado completo por edición (0,5 s / 5 000 líneas) | Ninguna | Limitación |
| AUD-27 | Sugerencia | `ui/`, `main.py` | Texto de veredicto armado en tres sitios | Ninguna | Observación |

Decisiones revisadas: D-36 aprobada, D-37 aprobada, D-38 aprobada, D-39 aprobada, D-40 superada (ya hay capturas reales en `docs/capturas/`).

---

### Revisión 4 — Revisión de cierre

- **Base:** `555ea7b` · **Detalle:** `docs/06_auditoria.md`, «Revisión de cierre» · **Veredicto:** APROBADO

| ID | Severidad | Archivo | Descripción | Acción | Estado |
|---|---|---|---|---|---|
| AUD-28 | Menor (Baja) | `ui/interfaz.py` | `after` pendientes (tick, desplazamientos diferidos, *debounce*) sobrevivían a `destroy()` → `invalid command name … ("after" script)` intermitente en la batería | `destroy()` cancela todos los `after info` en Tcl | Corregido; `test_aud28_destruir_con_after_pendientes` |
| — | Errata | `docs/04_manual_usuario.md` §4, §8 | «Detener libera el editor» (falso) | Texto corregido | Corregido |

B9 (D-42) y B10 (D-43) revisados: correctos, con pruebas significativas. Batería: 3 corridas `Ran 118 tests` · `OK`, 0 trazas.


### Auditoría Fase D (reviewer-opus)

| ID | Severidad | Archivo | Problema | Corrección | Estado |
|---|---|---|---|---|---|
| AUD-33 | Media | `ui/paneles.py` | Tabla de símbolos con `repr` crudo (apariciones `[(6, 12)…]`, `True/False`, cadenas sin comillas) | `formatear_apariciones` (`6:12, 9:9`), `formatear_valor`, columna «Veces» | Corregido; `test_aud33_tabla_de_simbolos_legible` |
| AUD-34 | Media | `ui/interfaz.py` | Tope de 10 s incumplido (5 000 líneas a 120 ms: 39,6 s); en 0 ms sin repintado 1,9 s | Ritmo `líneas × pausa` + agrupación con presupuesto de 30 ms (`_atrasado`, `PRESUPUESTO_TICK_S`) → 9,0 s / 2,1 s con repintado | Corregido; `test_aud34_archivo_largo_respeta_el_tope_y_repinta` |
| AUD-35 | Baja | `ui/estilos.py` | `TEMA["advertencia"]` sin uso | Ninguna (paleta fijada por §17.3) | Abierto, arquitecto |
| AUD-36 | Baja | `ui/interfaz.py` (divisores) | Solo ~4 filas visibles de la Tabla de símbolos en 1440×880 | Escalado (proporciones §17.2) | Escalado a architect-fable |

O-2 (pausa en 0 ms) no es defecto: el valor por defecto real es 120 ms; el driver de capturas lo pone en 0. D-73: aprobable; sugerir deslizador de 120 px. Batería: 3 corridas `Ran 176 tests`, 2 fallas esperadas (archivos del usuario), 0 trazas.

### Fase E, T4: líneas del grep (d) que se dejan

- `ui/paneles.py:15`, `("linea", "Lín", 50)` en `COLUMNAS_TOKENS`: `"linea"` es el identificador de la columna de Tk, no un comentario.

Un hallazgo de T1: `valor_literal` quitaba la unidad con `rstrip("smh")`, que fallaba al añadir una unidad con otra letra (ejercicio 11, `d`). Ahora corta en el primer carácter que no es dígito; el resultado para `ms`, `s`, `m` y `h` es el mismo.
