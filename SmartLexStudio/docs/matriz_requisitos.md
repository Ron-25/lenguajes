# Matriz de requisitos — SmartLex Studio

Fuente de verdad: `instrucciones .pdf` (Proyecto N°1, Lenguajes Formales, Autómatas y Compiladores — UTP).
Tema: *Analizador léxico, tabla de símbolos y manejador de errores*. Objetivo: proyecto en Python empleando conceptos de teoría de autómatas.

Estado inicial de todas las filas: **Pendiente**. El auditor completa `Estado` y la evidencia (salida de pruebas, captura) al cerrar cada fase.
Las columnas *Implementación*, *Archivo* y *Prueba* indican lo **planificado** en `docs/02_arquitectura.md` y `agents/tareas.md`.

## Requisitos funcionales del PDF

| Requisito | Implementación | Archivo | Prueba | Estado |
|---|---|---|---|---|
| **R1** (Etapa 1, 20 pts) Definir un lenguaje de tema libre y complejidad media | Lenguaje **FlowLang** (automatizaciones): 17 palabras reservadas, identificadores, enteros, decimales, cadenas con escapes, 15 operadores, 6 delimitadores, 2 tipos de comentario. Definición formal, regex y AFD por categoría | `docs/03_especificacion.md`, `config/reglas.py`, `ejemplos/*.flow` | `tests/test_afd.py` (equivalencia regex ↔ AFD), `tests/test_lexer.py` | Pendiente |
| **R2** (Etapa 2, 20 pts) Verificar la validez de una cadena de entrada según las reglas del lenguaje | Lexer dirigido por AFD (tablas de transición, coincidencia más larga) + validador estructural ligero (inicio/fin, balance). Veredicto `es_valida` global y por línea | `core/afd.py`, `core/lexer.py`, `core/validador.py`, `application/analisis_service.py` | `tests/test_lexer.py`, `tests/test_validador.py`, `tests/test_integracion.py` | Pendiente |
| **R3** (25 pts) Instalar en la tabla de símbolos, **por función hash**, los tokens con los elementos necesarios para otros elementos del compilador | Tabla hash propia (hash polinomial base 31, encadenamiento separado, redimensionado, conteo de colisiones). Cada entrada: lexema, categoría, tipo de dato, valor, línea de declaración, apariciones, valor hash, cubeta | `core/simbolos.py`, `core/modelos.py` (`EntradaSimbolo`) | `tests/test_simbolos.py`, `tests/test_integracion.py` | Pendiente |
| **R4** (25 pts) Manejador de errores que administre los errores de la evaluación e informe al usuario | `ManejadorErrores` + catálogo de diagnósticos con código, tipo, mensaje y sugerencia (LEX-001…007, SIN-001…006, ARC-001…006); recuperación en modo pánico (el análisis nunca se detiene en el primer error) | `core/errores.py`, `core/lexer.py`, `core/validador.py`, `application/archivos.py` | `tests/test_errores.py`, `tests/test_lexer.py`, `tests/test_archivos.py` | Pendiente |
| **R5a** (10 pts) El manejador de errores tiene una interfaz de usuario que se despliega **durante la evaluación** | Evaluación progresiva: `SesionAnalisis.siguiente_paso()` entrega un `Paso` por token; la UI lo reproduce animado o paso a paso y muestra cada error en el instante en que se detecta (pestaña Errores, consola, marca en el editor) | `application/analisis_service.py`, `ui/interfaz.py`, `ui/paneles.py`, `ui/editor.py` | `tests/test_integracion.py` (pasos), `tests/test_ui_humo.py`, verificación manual M1 | Pendiente |
| **R5b** (10 pts) **Al final**, alternativa de desplegar el contenido de la tabla de símbolos | Al terminar: diálogo «¿Desea ver la tabla de símbolos?» + botón permanente «Ver tabla de símbolos»; la pestaña se habilita al finalizar | `ui/interfaz.py`, `ui/paneles.py` | `tests/test_ui_humo.py`, verificación manual M2 | Pendiente |
| **R6** Las cadenas de entrada están en un archivo que el programa debe **solicitar** para iniciar el proceso | Al arrancar se abre el selector de archivo; «Analizar» sin contenido vuelve a solicitarlo. Validación de existencia, extensión, vacío, codificación, tamaño | `application/archivos.py`, `ui/interfaz.py`, `main.py` | `tests/test_archivos.py`, verificación manual M3 | Pendiente |

## Requisitos derivados (del objetivo del curso y de la sustentación)

| Requisito | Implementación | Archivo | Prueba | Estado |
|---|---|---|---|---|
| **D1** Emplear conceptos de teoría de autómatas de forma demostrable | Motor AFD genérico por tabla de transiciones; 4 AFD definidos como datos; el recorrido de estados de cada token se muestra en el Modo educativo | `core/afd.py`, `config/reglas.py` | `tests/test_afd.py` | Pendiente |
| **D2** Posiciones exactas (línea y columna desde 1) en tokens y errores | Contadores en el lexer; multilínea en comentarios de bloque | `core/lexer.py` | `tests/test_lexer.py` (posiciones exactas) | Pendiente |
| **D3** Ejecutable en el laboratorio sin instalar nada | Solo biblioteca estándar (tkinter/ttk, unittest); Python ≥ 3.10 | `main.py`, `requirements.txt` (vacío de dependencias) | Ejecución de `python -m unittest` y arranque de `main.py` | Pendiente |
| **D4** Código explicable y modificable en vivo | Reglas del lenguaje centralizadas como datos; puntos de extensión documentados | `config/reglas.py`, `docs/02_arquitectura.md` §11 | Ensayo de modificaciones (tarea B8) | Pendiente |
| **D5** Dominio independiente de la interfaz | `core/` y `application/` no importan `tkinter` | todo `core/`, `application/` | `tests/test_integracion.py::test_dominio_sin_tkinter` | Pendiente |

## Verificaciones manuales (se registran con captura en la auditoría final)

| ID | Verificación |
|---|---|
| M1 | Abrir `ejemplos/incorrecto.flow`, pulsar **Analizar**: los errores aparecen uno a uno mientras avanza el resaltado del token actual. |
| M2 | Al terminar el análisis aparece la oferta de ver la tabla de símbolos; aceptar muestra la pestaña con cubetas y colisiones. |
| M3 | Al iniciar el programa se solicita el archivo; cancelar deja el editor vacío y utilizable. |
