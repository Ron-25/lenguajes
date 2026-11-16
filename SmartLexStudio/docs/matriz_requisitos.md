# Matriz de requisitos — SmartLex Studio

Fuente de verdad: `instrucciones .pdf` (Proyecto N°1, Lenguajes Formales, Autómatas y Compiladores — UTP).
Tema: *Analizador léxico, tabla de símbolos y manejador de errores*. Objetivo: proyecto en Python empleando conceptos de teoría de autómatas.

Estado inicial de todas las filas: **Pendiente**. El auditor completa `Estado` y la evidencia (salida de pruebas, captura) al cerrar cada fase.
Las columnas *Implementación*, *Archivo* y *Prueba* se actualizaron con **evidencia ejecutada** en la auditoría final (2026-11-15, `docs/06_auditoria.md`, «Auditoría final»): 115 pruebas OK con python3.14 / Tk 9.0.

**Estado final (revisión de cierre, 2026-11-15, commit base `555ea7b` + AUD-28):** los 7 requisitos del PDF (R1–R6, con R5 en a/b) y D1–D5 **cumplen**; batería `Ran 118 tests` · `OK` en tres corridas (historial; tras la Fase D: 174 pruebas, solo las 2 fallas de D-72). R4 incluye además B9/D-42 (un solo error `ARC-*` visible; `tests/test_ui_humo.py::test_un_solo_error_de_archivo`); D1 incluye B10/D-43 (detalle de la pestaña Autómatas en formato `Campo: valor`; `tests/test_integracion.py::test_detalle_una_linea_por_dato`).

## Requisitos funcionales del PDF

| Requisito | Implementación | Archivo | Prueba | Estado |
|---|---|---|---|---|
| **R1** (Etapa 1, 20 pts) Definir un lenguaje de tema libre y complejidad media | FlowLang 1.0: 17 reservadas, identificadores, enteros, decimales, cadenas con escapes, 15 operadores, 6 delimitadores, 2 comentarios; 4 AFD como datos | `docs/03_especificacion.md`, `config/reglas.py`, `ejemplos/*.flow` | `tests/test_afd.py` (regex ↔ AFD, `test_conteos_de_flowlang_1_0`), `tests/test_lexer.py` — OK | **Cumple** |
| **R2** (Etapa 2, 20 pts) Verificar la validez de una cadena de entrada según las reglas del lenguaje | Lexer dirigido por AFD + validador estructural; veredicto léxico / estructura / global y líneas inválidas en consola, la pestaña Resumen y el modo consola | `core/lexer.py`, `core/validador.py`, `application/analisis_service.py`, `ui/interfaz.py` (`_veredictos_en_consola`) | `tests/test_integracion.py::test_correcto` (VÁLIDA), `::test_incorrecto` (INVÁLIDA), `tests/test_validador.py`; capturas 1, 3, 5 — OK | **Cumple** |
| **R3** (25 pts) Instalar en la tabla de símbolos, **por función hash**, los tokens con los elementos necesarios para otros elementos del compilador | Tabla hash propia (polinomial base 31, encadenamiento, redimensionado, colisiones); entrada con lexema, categoría, tipo, valor, declaración, apariciones, hash, cubeta; pestaña «Tabla de símbolos» con la fórmula del hash, en orden de cubeta, colisiones resaltadas y ambas medidas (14 / 7) | `core/simbolos.py`, `core/modelos.py`, `ui/paneles.py` (`mostrar_tabla_simbolos`) | `tests/test_simbolos.py`, `tests/test_ui_humo.py::test_colisiones_en_el_resumen`; captura 2 — OK | **Cumple** |
| **R4** (25 pts) Manejador de errores que administre los errores de la evaluación e informe al usuario | `ManejadorErrores` + catálogo LEX/SIN/ARC (código, mensaje, sugerencia), modo pánico; en la UI: `panel_errores` (Manejador de errores) con detalle completo (AUD-20), línea rosada, subrayado y ✗ en el editor, `showerror` para archivos | `core/errores.py`, `core/lexer.py`, `core/validador.py`, `application/archivos.py`, `ui/paneles.py`, `ui/editor.py` | `tests/test_errores.py`, `tests/test_archivos.py`, `tests/test_auditoria_fase_b.py::test_aud20_…`, `tests/test_ui_rediseno.py::test_detalle_con_lexema_posicion_y_sugerencia`; captura 5 — OK | **Cumple** |
| **R5a** (10 pts) El manejador de errores tiene una interfaz de usuario que se despliega **durante la evaluación** | `SesionAnalisis.siguiente_paso()` + `VentanaPrincipal._consumir_paso`: cada error aparece en `panel_errores` (siempre visible), consola, editor (subrayado, línea rosada y ✗) y barra de estado en el paso en que se detecta; la animación avanza por línea con la «Pausa por línea» (`_tick`, `_pausa_efectiva`) o paso a paso | `application/analisis_service.py`, `ui/interfaz.py`, `ui/paneles.py`, `ui/editor.py` | `tests/test_ui_humo.py::test_errores_durante_la_evaluacion`, `::test_progresividad`, `tests/test_ui_rediseno.py::test_requisito_5a_errores_durante_la_evaluacion`, `::test_pausa_por_linea_marca_la_linea_terminada`, `tests/test_integracion.py::test_progresividad` — OK | **Cumple** |
| **R5b** (10 pts) **Al final**, alternativa de desplegar el contenido de la tabla de símbolos | `_finalizar`: `askyesno(«…¿Desea ver la tabla de símbolos?»)` + pestaña «Tabla de símbolos» y botón «Ver tabla de símbolos» de la cabecera, habilitados solo al terminar; consola: `(s/n)` | `ui/interfaz.py`, `ui/paneles.py`, `ui/componentes.py` (`Cabecera`), `main.py` | `tests/test_ui_humo.py::test_flujo_completo_incorrecto` (1 llamada, 18 filas), `tests/test_ui_rediseno.py::test_requisito_5b_oferta_final_de_la_tabla`, `tests/test_integracion.py::test_consola_incorrecto_con_tabla_y_sin_ruta` — OK | **Cumple** |
| **R6** Las cadenas de entrada están en un archivo que el programa debe **solicitar** para iniciar el proceso | Al arrancar `askopenfilename` («Seleccione el archivo con las cadenas de entrada»); Analizar/Paso sin fuente lo vuelven a pedir (D-36); validación de existencia, extensión, vacío, codificación, tamaño; consola: `input("Archivo de entrada: ")` | `main.py`, `ui/interfaz.py` (`_solicitar_archivo_inicial`, `analizar`, `_confirmar_descartar`), `application/archivos.py` | `tests/test_ui_humo.py::test_requisito_6_solicita_archivo`, `tests/test_ui_rediseno.py::test_requisito_6_pide_archivo_con_el_diseno_nuevo`, `::test_requisito_6_cancelado`, `tests/test_archivos.py` — OK | **Cumple** |

## Requisitos derivados (del objetivo del curso y de la sustentación)

| Requisito | Implementación | Archivo | Prueba | Estado |
|---|---|---|---|---|
| **D1** Emplear conceptos de teoría de autómatas de forma demostrable | Motor AFD genérico; 4 AFD como datos; recorrido de estados y tabla de transiciones en la pestaña Autómatas (D-39) | `core/afd.py`, `config/reglas.py`, `ui/paneles.py` | `tests/test_afd.py`; captura 4 — OK | **Cumple** |
| **D2** Posiciones exactas (línea y columna desde 1) en tokens y errores | Contadores en el lexer; `\r` normalizado en el editor (D-34); doble clic en un error navega a su posición | `core/lexer.py`, `ui/editor.py` | `tests/test_lexer.py`, `tests/test_ui_humo.py::test_navegacion_a_un_error`, `::test_retorno_de_carro`, `::test_fuera_del_bmp` — OK | **Cumple** |
| **D3** Ejecutable en el laboratorio sin instalar nada | Solo biblioteca estándar; sin Tk, `main.py` explica cómo instalarlo o usar `--consola` | `main.py` | Batería OK en python3.11/3.12 (UI omitida) y 3.14 (completa) | **Cumple** |
| **D4** Código explicable y modificable en vivo | Reglas centralizadas como datos | `config/reglas.py`, `docs/02_arquitectura.md` §11 | Ensayo en copia: añadir `repetir` cambia lexer, resaltado, la pestaña Lenguaje y Autómatas; solo falla `test_conteos_de_flowlang_1_0` (D-32). Ensayo de modificaciones documentado en `docs/05_guia_sustentacion.md` (B8) | **Cumple** |
| **D5** Dominio independiente de la interfaz | `core/` y `application/` sin `tkinter`; `ui/` no importa lexer/validador/simbolos/afd | todo `core/`, `application/` | `tests/test_integracion.py::test_dominio_sin_tkinter`; `grep` vacíos (auditoría final §2) | **Cumple** |

## Verificaciones manuales (se registran con captura en la auditoría final)

Estado: M1–M3 cubiertas por pruebas automáticas y capturas reales `docs/capturas/1..6_*.png` (rediseño Fase C) (auditoría final §6); se recomienda repetirlas a mano en el equipo de la sustentación.

| ID | Verificación |
|---|---|
| M1 | Abrir `ejemplos/incorrecto.flow`, pulsar **Analizar**: los errores aparecen uno a uno mientras avanza el resaltado del token actual. |
| M2 | Al terminar el análisis aparece la oferta de ver la tabla de símbolos; aceptar muestra la herramienta Tabla de símbolos con cubetas y colisiones. |
| M3 | Al iniciar el programa se solicita el archivo; cancelar deja el editor vacío y utilizable. |
