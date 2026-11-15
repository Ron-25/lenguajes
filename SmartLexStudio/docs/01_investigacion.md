# 01 · Investigación — SmartLex Studio

Autor: architect-fable · Fecha de consulta de todos los enlaces: **2026-11-15**.
Método: cada enlace de este documento fue abierto en esa fecha (respuesta HTTP 200 y, donde se cita contenido, lectura de la página). No se copió código de terceros: solo se tomaron ideas de diseño. Lo que no pudo confirmarse leyendo la página se marca como **(no verificado)**.

---

## 1. Referencias consultadas

### 1.1 Interfaces de IDE (¿qué layout es el más profesional?)

| Referencia | Enlace | Qué se tomó |
|---|---|---|
| VS Code — User Interface | https://code.visualstudio.com/docs/getstarted/userinterface | Layout en 5 zonas: *Activity Bar*, *Primary Side Bar* (explorador), *Editor*, *Panel* inferior (salida, errores y advertencias, terminal) y *Status Bar*. El panel inferior es donde viven los errores. |
| VS Code — Syntax Highlight Guide | https://code.visualstudio.com/api/language-extensions/syntax-highlight-guide | El resaltado se hace por *tokens* con un *scope* (`keyword…`, `comment.line…`); el tema mapea scope → color. Separar «qué es el token» de «de qué color se pinta». |
| PyCharm — Tool windows | https://www.jetbrains.com/help/pycharm/tool-windows.html | Las ventanas de herramientas se acoplan abajo y a los lados del editor; desde un problema de la lista se salta a su posición en el editor. |
| Sublime Text — Syntax Definitions | https://www.sublimetext.com/docs/syntax.html | Las reglas son datos (contextos + regex + scope). Si varias reglas coinciden, gana la coincidencia más a la izquierda y, en empate, la definida primero. Existe el scope `invalid.illegal` para marcar texto erróneo. |
| Sublime Text — Scope Naming | https://www.sublimetext.com/docs/scope_naming.html | Familias de categorías estándar (keyword, string, comment, constant.numeric, invalid…) que usamos como guía de colores. |
| Monaco Editor (repositorio) | https://github.com/microsoft/monaco-editor | Editor de VS Code para navegador (licencia MIT). Confirma que es tecnología web: no aplica a un proyecto de escritorio sin Electron. |
| Monaco — Monarch | https://microsoft.github.io/monaco-editor/monarch.html | Tokenizador declarativo: el lenguaje se describe como datos (estados → reglas). *(El contenido de la página se genera con JavaScript; se verificó que existe, no se pudo leer su texto con la herramienta.)* |

### 1.2 Teoría y práctica de analizadores léxicos

| Referencia | Enlace | Qué se tomó |
|---|---|---|
| Python `re` — «Writing a Tokenizer» | https://docs.python.org/3/library/re.html | Técnica del patrón maestro con grupos nombrados y `lastgroup`; regla comodín `MISMATCH` para no perder caracteres. Advertencia textual: las alternativas con `|` se prueban de izquierda a derecha y «el operador `|` nunca es codicioso»: **`re` no garantiza la coincidencia más larga**, depende del orden. |
| Python — Regex HOWTO | https://docs.python.org/3/howto/regex.html | Sintaxis de las regex usadas en la especificación. |
| Python `tokenize` | https://docs.python.org/3/library/tokenize.html | Modelo de token de CPython: tipo, texto, inicio `(fila, columna)`. Filas desde 1 y columnas desde 0 → decidimos documentar explícitamente nuestra convención (ambas desde 1). |
| PLY (documentación) | https://www.dabeaz.com/ply/ply.html | (a) Palabras reservadas: una sola regla de identificador + consulta en un diccionario (evita que `for` coincida dentro de `forget`). (b) Errores: `t_error` informa y hace `skip(1)` — modo pánico a nivel de carácter. (c) Líneas y columnas se llevan a mano. (d) Los literales más largos se prueban antes (`==` antes que `=`). |
| PLY (repositorio) | https://github.com/dabeaz/ply | El README declara el proyecto **abandonado**; el repositorio está archivado (solo lectura) desde 2025-12-21. No se distribuye por pip: se copia la carpeta. |
| SLY (sucesor de PLY) | https://github.com/dabeaz/sly | Existe; mismo autor. No se evaluó en detalle. |
| ANTLR 4 (repositorio) | https://github.com/antlr/antlr4 | Licencia BSD-3-Clause. Requiere **Java 11+** para generar el analizador, más un runtime por lenguaje. |
| ANTLR 4 — Lexer rules | https://github.com/antlr/antlr4/blob/master/doc/lexer-rules.md | Comandos `-> skip` y `-> channel(HIDDEN)`: los espacios se descartan y los comentarios pueden conservarse fuera del flujo principal. De ahí nuestra idea de token «no significativo». |
| Crafting Interpreters — Scanning | https://craftinginterpreters.com/scanning.html | *Maximal munch* («gana la regla que consume más caracteres»); palabra reservada = identificador que está en un mapa; tras un error el escáner **sigue** para reportar todos los errores en una pasada. |
| Maximal munch | https://en.wikipedia.org/wiki/Maximal_munch | Definición del principio de coincidencia más larga. |
| Tabla hash | https://en.wikipedia.org/wiki/Hash_table | Encadenamiento separado, factor de carga, redimensionado. |
| Método de Horner | https://en.wikipedia.org/wiki/Horner%27s_method | Evaluación del hash polinomial carácter a carácter. |
| Funciones hash de cadenas (djb2, sdbm) | https://www.eecs.yorku.ca/~oz/hash.html | Alternativas clásicas consideradas. *(Verificado que la página existe; el contenido no se pudo leer con la herramienta por un problema de certificado del dominio antiguo.)* |

### 1.3 Tecnología de interfaz en Python

| Referencia | Enlace | Qué se tomó |
|---|---|---|
| `tkinter` | https://docs.python.org/3/library/tkinter.html | Interfaz estándar de Python a Tcl/Tk. Modelo de **bucle de eventos**: los manejadores deben terminar rápido; el trabajo largo se trocea con temporizadores (`after`). `python -m tkinter` comprueba la instalación. |
| `tkinter.ttk` | https://docs.python.org/3/library/tkinter.ttk.html | `Treeview` (tablas con columnas, etiquetas de color por fila con `tag_configure`), `Notebook` (pestañas, con estado `disabled`), `Panedwindow` (paneles redimensionables), `Style` (temas). |
| TkDocs — Text | https://tkdocs.com/tutorial/text.html | El widget `Text` colorea rangos con *tags*: base del resaltado y de las marcas de error. |
| TkDocs — Treeview | https://tkdocs.com/tutorial/tree.html | Uso de `Treeview` como tabla. |
| IDLE — `sidebar.py` (CPython) | https://github.com/python/cpython/blob/main/Lib/idlelib/sidebar.py | Cómo el propio IDLE implementa los números de línea: un `Text` de solo lectura al lado del editor, sincronizado con el desplazamiento vertical (`yscrollcommand`). Demuestra que la numeración se logra con Tk puro. |
| CustomTkinter | https://github.com/TomSchimansky/CustomTkinter | Licencia MIT. Requiere `pip install customtkinter`. Aspecto moderno, pero no sustituye a `ttk.Treeview` ni aporta editor de código **(esto último no verificado en su documentación en esta sesión)**. |
| CustomTkinter — documentación | https://customtkinter.tomschimansky.com/documentation/ | Existe; índice de widgets, ventanas y utilidades. |
| Chlorophyll | https://github.com/rdbende/chlorophyll | Licencia MIT. Widget `CodeView` (Text + resaltado + números). Depende de `pygments` y `TkLineNums` → dos dependencias pip más. |
| TkLineNums | https://github.com/Moosems/TkLineNums | Licencia MIT. Números de línea para `Text`. Repositorio archivado desde 2024-07-17. |
| CTkCodeBox | https://github.com/Akascape/CTkCodeBox | Editor para CustomTkinter (existe; no evaluado en detalle). |
| Pygments | https://github.com/pygments/pygments | Resaltador genérico (existe; descartado por ser dependencia externa). |

### 1.4 Proyectos públicos comparables

| Proyecto | Enlace | Observación |
|---|---|---|
| ADLexSyn | https://github.com/AhmedDiaa0212/ADLexSyn | Proyecto de curso en Python: lexer con regex, parser y **tres tablas de símbolos** (no ordenada, ordenada y hash) en archivos separados. Sin interfaz gráfica (línea de comandos). Sin licencia declarada → solo referencia conceptual. |
| Python-Lexer-Parser | https://github.com/GeorgeHany45/Python-Lexer-Parser | Front-end con tabla de símbolos e interfaz Qt. Su README lista como casos de error los identificadores que empiezan por dígito (`1words`) → caso que cubrimos con LEX-004. Sin licencia declarada. |
| c-analyzer | https://github.com/dpaulsoria/c-analyzer | Analizador con Tkinter + PLY (existe; no evaluado en detalle). |
| mini-compiler-python | https://github.com/ThaisBarrosAlvim/mini-compiler-python | Mini compilador educativo en Python (existe; no evaluado en detalle). |

Dos resultados de búsqueda (`mdawoud27/syntax_checker` y `being-amara-khan/simplelang-compiler`) devolvieron **404** y se descartaron.

### 1.5 Licencias (resumen)

| Componente | Licencia | ¿Lo usamos? |
|---|---|---|
| Python / tkinter / Tcl-Tk | PSF License / BSD-style — https://github.com/python/cpython/blob/main/LICENSE | **Sí** (única dependencia) |
| VS Code (código) | MIT — https://github.com/microsoft/vscode/blob/main/LICENSE.txt | No; solo inspiración visual (disposición y paleta oscura genérica, sin logotipos ni iconos de Microsoft) |
| Monaco Editor | MIT | No |
| CustomTkinter, Chlorophyll, TkLineNums | MIT | No |
| ANTLR 4 | BSD-3-Clause — https://github.com/antlr/antlr4/blob/master/LICENSE.txt | No |
| PLY | «Software libre, conserve el aviso de copyright» según su README (la página no nombra la licencia) | No |

Conclusión de licencias: SmartLex Studio **no incorpora código de terceros**; no hay obligaciones de atribución más allá de citar estas fuentes en la documentación. Todo el código es propio.

---

## 2. Conclusiones

### 2.1 Layout de interfaz
VS Code y PyCharm coinciden en el mismo patrón, que es el que un evaluador reconoce como «IDE profesional»: **barra superior de acciones · panel lateral izquierdo (explorador) · editor central con numeración · panel inferior (salida/errores) · barra de estado**, con paneles redimensionables. Añadimos un **panel derecho con pestañas** (Tokens, Tabla de símbolos, Errores, Estadísticas, Modo educativo) porque nuestras «vistas de resultado» son tablas anchas que no caben bien en el panel inferior. De PyCharm tomamos la navegación *error → posición en el editor* (doble clic).

### 2.2 Representación de tokens, errores y tabla de símbolos
- **Tokens**: tabla (`ttk.Treeview`) con `# · Línea · Columna · Categoría · Lexema`, fila coloreada con el mismo color que el resaltado del editor (idea de los *scopes*: una sola tabla categoría → color).
- **Errores**: tabla con `Código · Tipo · Línea:Col · Mensaje · Sugerencia`, subrayado rojo en el editor y marca en el margen de números. Código + mensaje + sugerencia es el formato de los diagnósticos de los compiladores modernos.
- **Tabla de símbolos**: tabla ordenada por **cubeta** (`Cubeta · Hash · Lexema · Categoría · Tipo · Valor · Declaración · Apariciones`) para que el encadenamiento y las colisiones se vean; resumen de capacidad, factor de carga y colisiones encima.
- **Evaluación progresiva**: todos los escáneres consultados procesan token a token; exponer ese avance como una secuencia de «pasos» permite animarlo con `after` sin hilos (recomendación de la documentación de tkinter).

### 2.3 Organización del proyecto
Los proyectos de curso consultados separan lexer, tabla de símbolos y punto de entrada en archivos distintos, pero mezclan reglas del lenguaje con lógica. Monarch y Sublime muestran la alternativa superior: **el lenguaje como datos**. Decisión: `config/reglas.py` contiene solo datos (palabras, operadores, tablas de transición) y `core/` contiene los algoritmos genéricos.

### 2.4 Técnica de análisis léxico: AFD explícito, no `re`
La documentación de `re` advierte que la alternancia no es codiciosa (prioridad por orden, no por longitud) y el motor es de *backtracking*: afirmar «nuestro lexer es un autómata finito» usando `re` no sería demostrable. Como el objetivo del curso es **emplear teoría de autómatas**, el reconocimiento se hace con **AFD explícitos por tabla de transiciones** y coincidencia más larga real. Las expresiones regulares quedan como **especificación** y las pruebas verifican la equivalencia regex ↔ AFD. De PLY y Crafting Interpreters se adoptan tres prácticas: palabra reservada = identificador + consulta a un diccionario; recuperación en modo pánico sin detener el análisis; posiciones llevadas a mano.

### 2.5 Generadores (PLY / ANTLR): descartados
PLY está abandonado y archivado; ANTLR exige Java y un runtime. Ambos ocultarían justo lo que hay que explicar en la sustentación (el autómata) y añadirían instalación en el laboratorio.

### 2.6 tkinter + ttk frente a CustomTkinter
| Criterio | tkinter + ttk | CustomTkinter |
|---|---|---|
| Instalación en laboratorio | Ninguna (biblioteca estándar) | `pip install` (puede no haber red/permisos) |
| Tabla (`Treeview`), pestañas, paneles redimensionables | Incluidos en `ttk` | No incluye tabla equivalente: habría que mezclar con `ttk` (no verificado en esta sesión) |
| Editor con *tags* de color | `tk.Text` | Envoltorio sobre `tk.Text` (mismo mecanismo; no verificado en esta sesión) |
| Tema oscuro | Manual: `ttk.Style` con tema `clam` + colores propios | Incluido |
| Riesgo en la sustentación | Mínimo | Fallo de importación = programa que no abre |

**Decisión: tkinter + ttk, solo biblioteca estándar.** El aspecto moderno se consigue con un tema oscuro propio centralizado en `ui/estilos.py`. El costo (escribir ~80 líneas de estilos) es menor que el riesgo de una dependencia.

---

## 3. Decisiones derivadas

El registro completo (con alternativas y justificación) está en `agents/decisiones.md`. Las que salen directamente de esta investigación:

| ID en `decisiones.md` | Decisión |
|---|---|
| D-01 | UI con tkinter + ttk (biblioteca estándar), tema oscuro propio; sin CustomTkinter, Pygments ni Chlorophyll. |
| D-02 | Layout tipo VS Code: barra superior, panel izquierdo, editor, panel derecho con pestañas, consola inferior, barra de estado. |
| D-03 | Lexer dirigido por AFD explícitos (tablas de transición); sin `re`, PLY ni ANTLR. |
| D-04 | Las regex quedan como especificación, verificada contra los AFD en las pruebas. |
| D-07 | Palabras reservadas reconocidas como identificadores + consulta a diccionario. |
| D-12 | Comentarios y errores producen token (no significativo), como los canales ocultos de ANTLR. |
| D-13 | Recuperación en modo pánico; el análisis nunca se detiene en el primer error. |
| D-20 | Evaluación progresiva por pasos consumidos con `after` (sin hilos). |
