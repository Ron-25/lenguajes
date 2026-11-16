"""Genera el documento de estudio por partes de SmartLex Studio (estilo del PDF de entregables)."""
import re
import sys

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

SALIDA = sys.argv[1]

BASE = ParagraphStyle("base", fontName="Helvetica", fontSize=10.5, leading=14.5, alignment=TA_LEFT)
TITULO_DOC = ParagraphStyle("td", parent=BASE, fontSize=11.5, leading=15)
PARTE = ParagraphStyle("parte", parent=BASE, fontSize=11.5, leading=15, spaceBefore=4)
SUB = ParagraphStyle("sub", parent=BASE, spaceBefore=7, spaceAfter=2)
TEXTO = ParagraphStyle("texto", parent=BASE, spaceBefore=6, spaceAfter=4)
VINETA = ParagraphStyle("vineta", parent=BASE)


def fmt(texto: str) -> str:
    """Escapa XML y convierte `codigo` en Courier."""
    texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', texto)


def p(texto, estilo=TEXTO):
    return Paragraph(fmt(texto), estilo)


def sub(texto):
    return Paragraph(fmt(texto), SUB)


def vinetas(items):
    return ListFlowable(
        [ListItem(Paragraph(fmt(t), VINETA), leftIndent=34, value="•") for t in items],
        bulletType="bullet", start="•", bulletFontName="Helvetica", bulletFontSize=8,
        leftIndent=34, bulletOffsetY=-1, spaceBefore=1, spaceAfter=2)


def parte(numero, titulo, responsable, puntos):
    return [Paragraph(fmt(f"Parte {numero}: {titulo}"), PARTE),
            Paragraph(fmt(f"Responsable: {responsable}"), BASE),
            Paragraph(fmt(f"Requisitos del PDF: {puntos}"), BASE)]


h = []

# ------------------------------------------------------------------ Portada breve
h += [Paragraph("DOCUMENTACIÓN DEL CÓDIGO POR PARTES", TITULO_DOC),
      Paragraph("SmartLex Studio · Analizador léxico de FlowLang 1.0 (con literales de duración)", BASE),
      Paragraph("Lenguajes Formales, Autómatas y Compiladores · Proyecto N.º 1 · UTP", BASE),
      p("Este documento reparte el código entre los cuatro expositores. Cada parte dice qué archivos "
        "le tocan a cada persona, qué hace cada función con su nombre real, qué debe saber explicar y "
        "qué preguntas le pueden hacer. Todas las rutas son relativas a la carpeta `SmartLexStudio/`."),
      p("Cómo ejecutar: `python3 main.py` abre la ventana; `python3 main.py --consola ejemplos/correcto.flow` "
        "muestra el resultado en texto; `python3 -m unittest discover -s tests -t .` corre las pruebas.")]

h += [sub("Mapa del código (de afuera hacia adentro):"),
      vinetas(["`main.py` y `ui/`: la ventana. No sabe analizar; solo pide pasos y los dibuja.",
               "`application/`: lee el archivo y coordina el análisis paso a paso.",
               "`core/`: la lógica: autómatas, lexer, tabla hash, errores y validador. No importa tkinter.",
               "`config/reglas.py`: las reglas de FlowLang como datos (palabras, operadores, tablas de los autómatas).",
               "Regla de oro: las dependencias van solo hacia adentro. `core/` no conoce la ventana."])]

# ------------------------------------------------------------------ Parte 1
h += [Spacer(1, 8)] + parte(1, "Introducción, FlowLang y arquitectura", "Persona A",
                             "1 (definir el lenguaje, 20 pts) y 6 (solicitar el archivo)")
h += [p("Presenta el proyecto, el lenguaje y cómo está organizado el código. También cierra la charla "
        "con la modificación en vivo (agregar una palabra reservada).")]
h += [sub("config/reglas.py (solo datos, sin lógica):"),
      vinetas(["`PALABRAS_RESERVADAS`: las 17 palabras con su descripción (`inicio`, `fin`, `numero`, `decimal`, "
               "`texto`, `booleano`, `dispositivo`, `verdadero`, `falso`, `si`, `sino`, `mientras`, `mostrar`, "
               "`leer`, `activar`, `desactivar`, `esperar`).",
               "`OPERADORES` y `DELIMITADORES`: cada símbolo con su categoría (por ejemplo `>=` es operador relacional).",
               "`ESCAPES_VALIDOS` (`\\n`, `\\t`, `\\\"`, `\\\\`) y `LONGITUD_MAXIMA_IDENTIFICADOR = 32`.",
               "`UNIDADES_TIEMPO`: las unidades de las duraciones y su valor en milisegundos (`ms` = 1, `s` = 1000, `m` = 60000, `h` = 3600000).",
               "`EXTENSIONES_PERMITIDAS` (`.flow`, `.txt`) y `TAMANO_MAXIMO_BYTES` (1 MB).",
               "`CAPACIDAD_INICIAL_TABLA = 17`, `FACTOR_CARGA_MAXIMO = 0.75`, `BASE_HASH = 31`: parámetros de la tabla hash.",
               "`AFD_IDENTIFICADOR`, `AFD_NUMERO`, `AFD_CADENA`, `AFD_COMENTARIO` y `AUTOMATAS` (los explica la Persona B).",
               "`CATEGORIAS_EN_TABLA`: qué categorías se guardan en la tabla de símbolos (la explica la Persona C)."])]
h += [sub("core/modelos.py (los moldes de los datos):"),
      vinetas(["`TipoToken`: las 13 categorías (palabra reservada, identificador, entero, decimal, duración, cadena, operador "
               "aritmético, relacional y lógico, asignación, delimitador, comentario y error).",
               "`Token`: `tipo`, `lexema`, `linea`, `columna`. Es inmutable (`frozen=True`).",
               "`Diagnostico`: un error con `codigo`, `tipo`, `titulo`, `mensaje`, `sugerencia`, `linea` y `columna`.",
               "`EntradaSimbolo`: una fila de la tabla de símbolos (la usa la Persona C)."])]
h += [sub("main.py:"),
      vinetas(["`main()`: sin argumentos abre la ventana `VentanaPrincipal`; con `--consola archivo.flow` llama a "
               "`_modo_consola`, que imprime tokens, errores y veredicto, y pregunta si mostrar la tabla de símbolos.",
               "Si el equipo no tiene tkinter, muestra cómo instalarlo y sugiere el modo consola."])]
h += [sub("Arquitectura que debe explicar:"),
      vinetas(["Capas inspiradas en Clean Architecture: presentación (`ui/`), aplicación (`application/`), dominio "
               "(`core/`) y configuración (`config/`).",
               "El dominio no depende de la interfaz: lo comprueba la prueba `test_dominio_sin_tkinter`.",
               "Patrones: autómata dirigido por tabla, generador para el análisis paso a paso, Strategy mínimo "
               "(la función hash es un parámetro) y vista pasiva con coordinador en la interfaz.",
               "SOLID: cada archivo una responsabilidad; agregar una palabra no toca algoritmos (abierto/cerrado); "
               "el `Lexer` recibe su manejador de errores y la tabla su función hash (inversión de dependencias)."])]
h += [sub("Debe poder explicar y demostrar:"),
      vinetas(["Qué es SmartLex Studio y qué es FlowLang (lenguaje para automatizar un invernadero).",
               "Que el programa pide el archivo al iniciar (requisito 6).",
               "Modificación en vivo: agregar `\"repetir\"` a `PALABRAS_RESERVADAS`, reabrir y analizar `inicio repetir fin`. "
               "Falla a propósito una sola prueba, `test_conteos_de_flowlang_1_0`, que fija 17 palabras."])]
h += [sub("Preguntas probables:"),
      vinetas(["¿Qué arquitectura usaron? Capas; dependencias solo hacia adentro.",
               "¿Por qué las reglas están en un archivo aparte? Para cambiar el lenguaje sin tocar los algoritmos.",
               "¿Qué hace el análisis léxico y qué no? Agrupa caracteres en tokens; no revisa el orden (sintaxis) "
               "ni el significado (semántica)."])]

# ------------------------------------------------------------------ Parte 2
h += [PageBreak()] + parte(2, "Autómatas y analizador léxico (la parte más compleja)", "Persona B",
                            "2 (verificar la validez de la cadena, 20 pts)")
h += [p("Explica cómo el programa reconoce cada token con autómatas finitos deterministas (AFD) escritos como "
        "tablas de transición, y cómo el lexer elige el lexema más largo. Es el centro teórico de la materia.")]
h += [sub("core/afd.py (motor genérico de autómatas, 83 líneas):"),
      vinetas(["`clase_caracter(caracter)`: agrupa caracteres en `LETRA`, `DIGITO` o `SALTO`; así la tabla no "
               "necesita una columna por cada letra.",
               "`ResultadoAFD`: lo que devuelve el autómata: `longitud` reconocida, `tipo` (si terminó en aceptación), "
               "`codigo_error` (si terminó en un estado de error) y `recorrido` (estados visitados).",
               "`AFD.siguiente_estado(estado, caracter)`: la función de transición δ. Busca el carácter exacto, luego "
               "su clase y luego el comodín `OTRO`; si no hay transición devuelve `None` y el autómata se detiene.",
               "`AFD.reconocer(texto, inicio)`: avanza carácter por carácter y recuerda el último estado final por el "
               "que pasó; así devuelve el prefijo más largo reconocido.",
               "`AFD.acepta(cadena)`: verdadero si la cadena completa termina en un estado de aceptación (lo usan las pruebas)."])]
h += [sub("Las tablas de los autómatas (en config/reglas.py):"),
      vinetas(["`AFD_IDENTIFICADOR`: q0 con letra o `_` pasa a q1; q1 acepta letras, dígitos y `_`. Regex `[A-Za-z_][A-Za-z0-9_]*`.",
               "`AFD_NUMERO`: q1 = entero, q3 = decimal, q7 y q8 = duración; estados de error q2 y q4 (LEX-003, número "
               "mal formado) y q5 (LEX-004, identificador que empieza con dígito).",
               "Duraciones: desde q1, con `s` o `h` pasa a q7 y con `m` a q8; desde q8, con `s` pasa a q7 (así `10ms` es "
               "un solo token). Cualquier otra letra va a q5: `10x`, `5min`, `10S` y `5mm` son LEX-004. Solo enteros: `1.5s` es LEX-003.",
               "`AFD_CADENA`: comillas dobles en una línea; q5 es LEX-006 (escape inválido) y los demás estados "
               "sin cerrar son LEX-002.",
               "`AFD_COMENTARIO`: `//` hasta fin de línea y `/* ... */`; sin cerrar es LEX-007.",
               "`AUTOMATAS = (comentario, cadena, número, identificador)`: el orden decide los empates de longitud."])]
h += [sub("core/lexer.py (analizador léxico, 126 líneas):"),
      vinetas(["`reconocer_lexema(texto, posicion)`: ejecuta los 4 AFD y busca en la tabla de operadores (primero 2 "
               "caracteres, luego 1); gana el más largo. Si ganó un identificador, revisa si pasa de 32 caracteres "
               "(LEX-005) o si está en `PALABRAS_RESERVADAS`. Si nadie reconoce el carácter: LEX-001.",
               "`_mejor_simbolo` y `_candidatos`: funciones de apoyo para operadores y para juntar candidatos.",
               "`Lexer.tokens()`: recorre el archivo saltando espacios, lleva la línea y la columna, entrega un token "
               "por lexema y, si hay error, lo reporta y sigue (modo pánico). Es un generador: entrega los tokens de a uno.",
               "`Lexer._reportar` y `_reportar_escapes_invalidos`: envían cada error al manejador con su posición exacta."])]
h += [sub("Recorrido que debe saber de memoria (45.5;):"),
      vinetas(["q0 lee 4 y pasa a q1 (entero); lee 5 y sigue en q1; lee el punto y pasa a q2 (error); lee 5 y pasa "
               "a q3 (decimal); con `;` no hay transición y se detiene. Resultado: `45.5`, decimal, longitud 4.",
               "`3.4.5` termina en q4: un solo error LEX-003. `12abc` termina en q5: LEX-004.",
               "`30s`: q0, q1, q1, q7 (duración). `500ms`: q0, q1, q1, q1, q8, q7; pasa por q8 (`500m` ya es duración) "
               "pero gana el último estado final, q7.",
               "`10 s` con espacio son dos tokens: entero `10` e identificador `s`."])]
h += [sub("Pruebas de su parte:"),
      vinetas(["`tests/test_afd.py`: compara cada AFD con su expresión regular en todas las cadenas de hasta 5 símbolos.",
               "`tests/test_lexer.py`: posiciones exactas, coincidencia más larga (`>=` frente a `>`), errores consecutivos."])]
h += [sub("Preguntas probables:"),
      vinetas(["¿Por qué es determinista? Para cada estado y símbolo hay como máximo una transición.",
               "¿Usaron expresiones regulares? No para reconocer; son la especificación, y una prueba compara cada AFD "
               "con su regex (prueba exhaustiva acotada, no demostración formal).",
               "¿Son AFD mínimos? No: tienen estados de error añadidos a propósito.",
               "¿Qué diferencia hay entre `10s`, `10 s` y `10seg`? Duración; entero más identificador; y LEX-004, porque "
               "`seg` no es una unidad.",
               "¿Los operadores tienen autómata? No, se buscan en un diccionario probando primero 2 caracteres.",
               "¿Por qué los paréntesis no se validan con un AFD? Ese lenguaje no es regular; hace falta una pila.",
               "La 5-tupla: Q son los estados, Σ las clases de caracteres, δ es `siguiente_estado`, q0 es `\"inicial\"` "
               "y F son los estados de `\"aceptacion\"`."])]

# ------------------------------------------------------------------ Parte 3
h += [PageBreak()] + parte(3, "Tabla de símbolos y hash", "Persona C",
                            "3 (instalar los tokens en la tabla de símbolos por función hash, 25 pts)")
h += [p("Explica cómo se guardan los tokens en una tabla hash propia (no se usa el `dict` de Python), cómo se "
        "calcula la cubeta, qué es una colisión y cómo crece la tabla.")]
h += [sub("core/simbolos.py (193 líneas):"),
      vinetas(["`hash_polinomial(lexema)`: por cada carácter `valor = (valor * 31 + ord(caracter)) % 2**32`. "
               "Ejemplo: `fin` da 102, luego 3267, luego 101387.",
               "`siguiente_primo(n)`: el menor primo mayor o igual que n (para el crecimiento 17, 37, 79).",
               "`TablaSimbolos`: una lista de listas (`_cubetas`). La función hash se recibe por parámetro.",
               "`indice(lexema)`: la cubeta, `hash mod capacidad`. `fin` con 79 cubetas va a la 30.",
               "`buscar(lexema)`: va a la cubeta y compara solo con lo que hay ahí.",
               "`instalar(token)`: si el lexema ya existe, suma una aparición; si es nuevo y la cubeta tenía algo, "
               "cuenta una colisión y lo agrega al final (encadenamiento). Si el factor de carga pasa de 0,75, crece.",
               "`_redimensionar()`: nueva capacidad = primo mayor o igual al doble; reubica todas las entradas con su hash guardado.",
               "`estadisticas()`: capacidad, cantidad, factor de carga, colisiones, cubetas ocupadas, cadena más larga y redimensionados.",
               "`registrar_token(tabla, token, anterior)`: decide si el token va a la tabla (`CATEGORIAS_EN_TABLA`), "
               "anota el valor de los literales y el tipo de dato; si antes venía `numero x`, guarda tipo y línea de declaración.",
               "`valor_literal` e `_interpretar_escapes`: convierten `\"10\"` en 10, `30s` en 30000 milisegundos y los escapes de las cadenas."])]
h += [sub("Qué guarda cada fila (EntradaSimbolo en core/modelos.py):"),
      vinetas(["`lexema`, `categoria`, `valor_hash`, `tipo_dato`, `valor`, `linea_declaracion` y `apariciones`.",
               "La cubeta no se guarda: se calcula, y por eso cambia cuando la tabla crece.",
               "Entran palabras reservadas, identificadores, enteros, decimales, duraciones y cadenas; no entran operadores, "
               "delimitadores, comentarios ni errores."])]
h += [sub("En la interfaz (ui/paneles.py):"),
      vinetas(["`PanelResultados.mostrar_tabla_simbolos(tabla)`: llena la pestaña con la línea de resumen (fórmula del "
               "hash, capacidad, factor de carga, colisiones) y la tabla; las filas en colisión salen en amarillo.",
               "`formatear_apariciones` y `formatear_valor`: muestran `6:12, 9:9` y los valores en forma legible."])]
h += [sub("Cifras de correcto.flow que debe conocer:"),
      vinetas(["36 entradas, capacidad final 79 (creció 17, 37, 79), 14 colisiones al insertar y 7 en la tabla actual.",
               "`si` (hash 3670) y `temperatura` (hash 321701232) caen en la cubeta 15 con 17 cubetas; al crecer se separan.",
               "`30s` es una duración: hash 50614, cubeta 54 con 79 cubetas, tipo `duracion`, valor 30000."])]
h += [sub("Pruebas de su parte:"),
      vinetas(["`tests/test_simbolos.py`: inserción, búsqueda, duplicados, colisiones forzadas con "
               "`TablaSimbolos(funcion_hash=lambda s: 0)` y redimensionado."])]
h += [sub("Preguntas probables:"),
      vinetas(["¿El hash es el token? No: el token es el lexema clasificado; el hash es el número que indica la cubeta.",
               "¿Por qué base 31? Hace que el orden de las letras importe (`roma` y `amor` dan distinto) y reparte bien.",
               "¿Complejidad? Buscar e insertar cuestan O(1) en promedio y O(n) en el peor caso.",
               "¿Por qué capacidades primas? El módulo de un primo reparte mejor los restos.",
               "¿Por qué no `dict`? Para que el hashing sea visible y se puedan mostrar cubetas y colisiones."])]

# ------------------------------------------------------------------ Parte 4
h += [PageBreak()] + parte(4, "Manejador de errores e interfaz", "Persona D",
                            "4 (manejador de errores, 25 pts) y 5 (interfaz durante la evaluación y tabla al final, 10 pts)")
h += [p("Explica cómo se detectan, clasifican y muestran los errores, cómo se lee el archivo, cómo funciona el "
        "análisis paso a paso y cómo la interfaz muestra los errores mientras avanza la evaluación.")]
h += [sub("core/errores.py:"),
      vinetas(["`CATALOGO`: los 19 errores, cada uno con tipo, título, mensaje y sugerencia. Es el único lugar con los textos.",
               "Familias: LEX-001 a LEX-007 (léxicos), SIN-001 a SIN-006 (estructurales), ARC-001 a ARC-006 (archivo).",
               "`crear_diagnostico(codigo, linea, columna, lexema)`: rellena la plantilla del catálogo.",
               "`ManejadorErrores`: `reportar`, `agregar`, `extender`, `ordenados`, `por_tipo`, `por_linea`, `cantidad`, "
               "`hay_errores` y `resumen` (por ejemplo «17 errores: 15 léxicos, 2 estructurales»)."])]
h += [sub("core/validador.py (comprobaciones estructurales, no léxicas):"),
      vinetas(["`validar_estructura(tokens)`: ignora comentarios y errores; el primer token debe ser `inicio` (si no, "
               "SIN-002) y el último `fin` (si no, SIN-003); sin tokens es SIN-001.",
               "`_validar_balance(tokens)`: una pila. Con `(` o `{` apila; con `)` o `}` desapila y compara. Cierre sin "
               "apertura es SIN-004, apertura sin cierre SIN-005 y cierre que no corresponde SIN-006."])]
h += [sub("application/archivos.py:"),
      vinetas(["`cargar_fuente(ruta)`: revisa existencia (ARC-001), extensión (ARC-002), tamaño (ARC-006), lectura "
               "(ARC-005), codificación UTF-8 (ARC-004) y vacío (ARC-003); normaliza los saltos de línea de Windows.",
               "`guardar_fuente`, `crear_fuente` y `plantilla_nueva` (archivo nuevo con `inicio` y `fin`), y `listar_ejemplos`."])]
h += [sub("application/analisis_service.py (coordina el análisis):"),
      vinetas(["`SesionAnalisis.siguiente_paso()`: pide un token al lexer, lo instala en la tabla y devuelve un `Paso` "
               "con los errores de ese momento. Al terminar los tokens corre el validador y entrega sus errores como pasos.",
               "`terminar()`: ejecuta todos los pasos que falten (botón Analizar).",
               "`ResultadoAnalisis`: `es_valida_lexicamente`, `es_valida_estructuralmente`, `es_valida`, `conteo_por_tipo` "
               "y `lineas_invalidas`.",
               "`explicar_token(token)`: arma la explicación de la pestaña Autómatas; `analizar_archivo(ruta)` lo hace todo de una vez."])]
h += [sub("ui/ (la ventana):"),
      vinetas(["`interfaz.py`, `VentanaPrincipal`: conecta los botones con `application/`. `analizar`, `paso_a_paso`, "
               "`detener`, `abrir_archivo`, `nuevo_archivo`, `guardar_archivo`, `limpiar`, `ver_tabla_simbolos`. "
               "Usa `after()` de tkinter para pedir pasos con la «Pausa por línea»; al final ofrece ver la tabla de símbolos.",
               "`editor.py`, `EditorCodigo`: números de línea, marcas de línea válida o con error, resaltado "
               "(`resaltar`), subrayado de errores (`marcar_errores`) e `ir_a` para saltar a un error.",
               "`paneles.py`, `PanelErrores`: el «Manejador de errores (N errores)» con el detalle del error elegido; "
               "`PanelResultados`: pestañas Tokens, Tabla de símbolos, Resumen, Autómatas, Lenguaje y Consola.",
               "`componentes.py`: `Cabecera` (botones y deslizador de pausa), `BarraEstado` (contadores y veredicto), "
               "`PanelConsola` y `VistaLenguaje`. `estilos.py`: el único lugar con colores y fuentes."])]
h += [sub("Debe poder demostrar:"),
      vinetas(["Abrir `incorrecto.flow`, pulsar Paso a paso tres veces: el tercer token es `2pi` y el error aparece en ese instante.",
               "Terminar con Analizar: 17 errores; doble clic en uno lleva a su línea. La línea 13 muestra los errores "
               "de duración: `5min` (LEX-004) y `1.5s` (LEX-003).",
               "Al terminar se ofrece ver la tabla de símbolos (requisito 5)."])]
h += [sub("Preguntas probables:"),
      vinetas(["¿Qué es el modo pánico? Se descarta el lexema inválido y el análisis continúa, para reportar todos los errores.",
               "¿Diferencia entre error léxico y estructural? El léxico es un lexema mal escrito; el estructural es "
               "el programa mal armado (falta `fin`, paréntesis sin cerrar).",
               "¿Por qué una pila? Un autómata finito no puede contar paréntesis abiertos.",
               "¿Cómo cumplen el requisito 5? Cada paso trae sus errores y la ventana los muestra en ese momento; "
               "al final se ofrece la tabla de símbolos."])]

# ------------------------------------------------------------------ Resumen
h += [Spacer(1, 14), Paragraph("RESUMEN", BASE), Spacer(1, 6)]
datos = [["N°", "Parte", "Responsable", "Archivos principales"],
         ["1", "Introducción, FlowLang y arquitectura", "Persona A", "config/reglas.py, core/modelos.py, main.py"],
         ["2", "Autómatas y analizador léxico", "Persona B", "core/afd.py, core/lexer.py, tablas AFD"],
         ["3", "Tabla de símbolos y hash", "Persona C", "core/simbolos.py, ui/paneles.py (tabla)"],
         ["4", "Manejador de errores e interfaz", "Persona D", "core/errores.py, core/validador.py, application/, ui/"]]
tabla = Table(datos, colWidths=[12 * mm, 62 * mm, 26 * mm, 70 * mm])
tabla.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "Helvetica", 9.5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
h += [tabla]

doc = SimpleDocTemplate(SALIDA, pagesize=A4, leftMargin=25 * mm, rightMargin=25 * mm,
                        topMargin=22 * mm, bottomMargin=22 * mm,
                        title="Documentación del código por partes - SmartLex Studio", author="SmartLex Studio")
doc.build(h)
print("ok")
