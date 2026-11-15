# Revisiones — SmartLex Studio

Aquí se registran las auditorías de cada fase (reviewer-opus), las discrepancias que el desarrollador encuentre en el contrato y las aprobaciones del arquitecto. Se añade al final; no se borra historial.

## Índice de revisiones

| # | Fecha | Fase / Tarea | Revisor | Modelo | Veredicto | Hallazgos abiertos |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

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
