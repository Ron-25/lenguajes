# lenguajes

Proyecto N.º 1 de Lenguajes Formales, Autómatas y Compiladores (UTP).

**SmartLex Studio** es un analizador léxico para **FlowLang**, un lenguaje pequeño para automatizar un invernadero. Tiene tabla de símbolos con hash propio, manejador de errores e interfaz gráfica en tkinter.

Todo el proyecto está en [`SmartLexStudio/`](SmartLexStudio/). Empieza por su [README](SmartLexStudio/README.md).

```
cd SmartLexStudio
python3 main.py                                   # interfaz gráfica
python3 main.py --consola ejemplos/correcto.flow  # modo texto
python3 -m unittest discover -s tests -t .        # pruebas
```

Para estudiar la sustentación:

- [Documentación del código por partes](SmartLexStudio/docs/Documentacion_por_partes.pdf): qué le toca explicar a cada integrante.
- [Guía de presentación y estudio](SmartLexStudio/docs/Guia_Presentacion_SmartLex.pdf).
