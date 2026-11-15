# SmartLex Studio

Analizador léxico educativo para **FlowLang 1.0**, un lenguaje pequeño para describir automatizaciones (riego, luces, alarmas). Reconoce los lexemas con autómatas finitos deterministas definidos por tablas de transición, informa los errores léxicos y estructurales, y guarda los símbolos en una tabla hash propia.

Estado: **Fase A (núcleo) completa**: `config/`, `core/`, `application/` y sus pruebas. La interfaz gráfica (Fase B) aún no está construida.

## Requisitos

- Python 3.10 o superior, solo biblioteca estándar (sin dependencias externas).
- tkinter solo será necesario para la interfaz gráfica (Fase B); el núcleo no lo usa.

## Estructura

| Carpeta | Contenido |
|---|---|
| `config/reglas.py` | Todas las reglas de FlowLang como datos (palabras reservadas, operadores, tablas de los AFD) |
| `core/` | Dominio: modelos, motor de AFD, errores, lexer, validador estructural, tabla de símbolos |
| `application/` | Casos de uso: archivos y servicio de análisis (evaluación progresiva) |
| `ejemplos/` | Programas `.flow` de ejemplo (correcto, incorrecto, casos límite) |
| `tests/` | Pruebas con `unittest` |
| `docs/`, `agents/` | Especificación, arquitectura, tareas y decisiones |

## Ejecutar las pruebas

Desde esta carpeta:

```
python3 -m unittest discover -s tests -t . -v
```

En este equipo, usar `/opt/homebrew/bin/python3.14` (el `python3` por defecto no incluye tkinter).

## Uso rápido del núcleo

```python
from application.analisis_service import analizar_texto

resultado = analizar_texto("inicio numero x = 10; fin")
print(resultado.es_valida, len(resultado.tokens), len(resultado.tabla))
```
