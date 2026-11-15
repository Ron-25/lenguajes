# Revisiones — SmartLex Studio

Aquí se registran las auditorías de cada fase (reviewer-opus), las discrepancias que el desarrollador encuentre en el contrato y las aprobaciones del arquitecto. Se añade al final; no se borra historial.

## Índice de revisiones

| # | Fecha | Fase / Tarea | Revisor | Modelo | Veredicto | Hallazgos abiertos |
|---|---|---|---|---|---|---|
| 1 | 2026-11-15 | Fase A (A1–A10) | reviewer-opus | claude-opus-5-5 | Aprobado con observaciones | 6 escalados (E-1…E-6) |

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
