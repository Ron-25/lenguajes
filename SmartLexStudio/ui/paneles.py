"""Manejador de errores (a la derecha) y pestañas de resultados (abajo)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from application.analisis_service import ExplicacionToken, ResultadoAnalisis
from config import reglas
from core.modelos import Diagnostico, Token, TipoDiagnostico
from ui.componentes import PanelConsola, VistaLenguaje
from ui.estilos import COLORES_TOKEN, TEMA, fuente_codigo, fuente_interfaz

# (identificador, titulo, ancho)
COLUMNAS_TOKENS = [("n", "#", 56), ("linea", "Lín", 50), ("col", "Col", 50),
                   ("categoria", "Categoría", 150), ("lexema", "Lexema", 220)]
COLUMNAS_SIMBOLOS = [("cubeta", "Cubeta", 76), ("hash", "Hash", 116), ("lexema", "Lexema", 150),
                     ("categoria", "Categoría", 150), ("tipo", "Tipo", 90), ("valor", "Valor", 110),
                     ("decl", "Decl.", 50), ("veces", "Veces", 70), ("apariciones", "Apariciones (lín:col)", 240)]
COLUMNAS_ERRORES = [("codigo", "Código", 80), ("linea", "Línea", 58), ("col", "Col", 45),
                    ("lexema", "Lexema", 110), ("error", "Error", 200)]

_VISTAS = (("tokens", "Tokens"), ("simbolos", "Tabla de símbolos"), ("resumen", "Resumen"),
           ("automatas", "Autómatas"), ("lenguaje", "Lenguaje"), ("consola", "Consola"))
_MAX_TEXTO = 40
_AYUDA_ERRORES = "Clic en un error: ver el detalle completo.  Doble clic: ir a su posición en el editor."


def recortar(texto: object, maximo: int = _MAX_TEXTO) -> str:
    """Texto en una sola línea (saltos como ⏎), recortado a `maximo` caracteres."""
    limpio = str(texto).replace("\n", "⏎").replace("\t", "→")
    return limpio if len(limpio) <= maximo else limpio[:maximo] + "…"


def formatear_apariciones(apariciones) -> str:
    """Posiciones como `lín:col, lín:col`, en vez de la lista de Python."""
    return recortar(", ".join(f"{linea}:{columna}" for linea, columna in apariciones), 60)


def formatear_valor(valor: object) -> str:
    """Valor como se escribe en FlowLang: booleanos con su palabra, cadenas con comillas, nada para None."""
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return next((palabra for palabra, v in reglas.VALORES_BOOLEANOS.items() if v is valor), str(valor))
    if isinstance(valor, str):
        return recortar('"' + valor.replace("\\", "\\\\").replace('"', '\\"') + '"')
    return recortar(valor)


def _tabla(padre, columnas, estirar: tuple[str, ...] = ()) -> ttk.Treeview:
    """Treeview con barras de desplazamiento; las columnas de `estirar` se reparten el ancho que sobra."""
    marco = ttk.Frame(padre, style="Panel.TFrame")
    marco.pack(fill="both", expand=True)
    arbol = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings", selectmode="browse")
    for identificador, titulo, ancho in columnas:
        arbol.heading(identificador, text=titulo, anchor="w")
        arbol.column(identificador, width=ancho, minwidth=40, anchor="w", stretch=identificador in estirar)
    vertical = ttk.Scrollbar(marco, orient="vertical", command=arbol.yview)
    horizontal = ttk.Scrollbar(marco, orient="horizontal", command=arbol.xview)
    arbol.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    arbol.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    marco.rowconfigure(0, weight=1)
    marco.columnconfigure(0, weight=1)
    return arbol


def _texto_solo_lectura(padre, fuente) -> tk.Text:
    texto = tk.Text(padre, wrap="word", state="disabled", font=fuente, background=TEMA["panel"],
                    foreground=TEMA["texto_codigo"], borderwidth=0, highlightthickness=0, padx=16, pady=12,
                    spacing1=2, spacing3=2)
    texto.pack(fill="both", expand=True)
    return texto


def _escribir_tabla_transiciones(t: tk.Text, automata: dict) -> None:
    """Tabla de transiciones y estados finales de un AFD, para la explicación de un token y para el selector."""
    t.insert("end", "\nTabla de transiciones de " + automata["nombre"] + "\n", "campo")
    for estado, fila in automata["transiciones"].items():
        celdas = "   ".join(f"{k} → {v}" for k, v in fila.items())
        t.insert("end", f"  {estado}:  {celdas}\n", "valor")
    finales = ", ".join(list(automata["aceptacion"]) + list(automata["errores"]))
    t.insert("end", f"  Estados finales: {finales}\n", "campo")


def _modulo_hash() -> str:
    """El módulo del hash como se escribe en la fórmula (2³² si es 2 ** 32)."""
    return "2³²" if reglas.MODULO_HASH == 2 ** 32 else str(reglas.MODULO_HASH)


class PanelResultados(ttk.Frame):
    """Pestañas de resultados. No calcula nada: muestra lo que le da la ventana y avisa cuando se elige un token."""

    def __init__(self, padre, al_seleccionar_token: Callable[[Token], None]) -> None:
        super().__init__(padre)
        self._al_token = al_seleccionar_token
        self._tokens: dict[str, Token] = {}
        self._ultimo_token: str | None = None
        self._id_ver_token: str | None = None
        self.cuaderno = ttk.Notebook(self)
        self.cuaderno.pack(fill="both", expand=True)
        self._marcos = {clave: ttk.Frame(self.cuaderno, style="Panel.TFrame") for clave, _t in _VISTAS}
        self._construir_tokens(self._marcos["tokens"])
        self._construir_simbolos(self._marcos["simbolos"])
        self.lienzo = tk.Canvas(self._marcos["resumen"], background=TEMA["panel"], highlightthickness=0)
        self.lienzo.pack(fill="both", expand=True)
        self.lienzo.bind("<MouseWheel>", lambda e: self.lienzo.yview_scroll(-1 if e.delta > 0 else 1, "units"))
        self._construir_automatas(self._marcos["automatas"])
        VistaLenguaje(self._marcos["lenguaje"]).pack(fill="both", expand=True)
        self.consola = PanelConsola(self._marcos["consola"])
        self.consola.pack(fill="both", expand=True)
        for clave, titulo in _VISTAS:
            self.cuaderno.add(self._marcos[clave], text=titulo)
        self.limpiar()

    def _construir_tokens(self, marco) -> None:
        self.arbol_tokens = _tabla(marco, COLUMNAS_TOKENS)
        for tipo, color in COLORES_TOKEN.items():
            self.arbol_tokens.tag_configure(tipo.name, foreground=color)
        self.arbol_tokens.bind("<<TreeviewSelect>>", self._seleccion_token)

    def _construir_simbolos(self, marco) -> None:
        self.etiqueta_resumen = ttk.Label(marco, style="Panel.TLabel", padding=(12, 8), justify="left")
        self.etiqueta_resumen.pack(fill="x")
        self.etiqueta_resumen.bind("<Configure>", lambda e: self.etiqueta_resumen.configure(wraplength=e.width - 24))
        self.arbol_simbolos = _tabla(marco, COLUMNAS_SIMBOLOS)
        self.arbol_simbolos.tag_configure("colision", background=TEMA["colision"])

    def _construir_automatas(self, marco) -> None:
        fila = ttk.Frame(marco, style="Panel.TFrame")
        fila.pack(fill="x", padx=12, pady=(8, 0))
        ttk.Label(fila, text="Autómata:", style="Panel.TLabel").pack(side="left")
        self.selector_automata = ttk.Combobox(fila, state="readonly", width=28,
                                              values=[a["nombre"] for a in reglas.AUTOMATAS])
        self.selector_automata.pack(side="left", padx=8)
        self.selector_automata.bind("<<ComboboxSelected>>", lambda _e: self.mostrar_automata(self.selector_automata.get()))
        self.educativo = _texto_solo_lectura(marco, fuente_codigo(13))
        t = self.educativo
        t.tag_configure("titulo", foreground=TEMA["texto"], font=(fuente_interfaz()[0], 14, "bold"), spacing3=8)
        t.tag_configure("campo", foreground=TEMA["texto_secundario"])
        t.tag_configure("valor", foreground=TEMA["texto_codigo"])
        t.tag_configure("codigo", foreground=TEMA["exito"])
        t.tag_configure("error", foreground=TEMA["error"])
        t.tag_configure("vacio", foreground=TEMA["texto_tenue"])

    def _seleccion_token(self, _evento) -> None:
        seleccion = self.arbol_tokens.selection()
        if seleccion and seleccion[0] in self._tokens:
            self._al_token(self._tokens[seleccion[0]])

    @property
    def vista_actual(self) -> str:
        """Clave de la pestaña visible: tokens, simbolos, resumen, automatas, lenguaje o consola."""
        elegida = self.cuaderno.select()
        return next(clave for clave, marco in self._marcos.items() if str(marco) == str(elegida))

    def mostrar(self, nombre: str) -> None:
        """Muestra la pestaña `nombre`."""
        self.cuaderno.select(self._marcos[nombre])

    def agregar_token(self, numero: int, token: Token) -> None:
        """Agrega una fila a la pestaña Tokens, con el color de su categoría."""
        iid = self.arbol_tokens.insert("", "end", tags=(token.tipo.name,), values=(
            numero, token.linea, token.columna, token.tipo.value, recortar(token.lexema)))
        self._tokens[iid] = token
        self._ultimo_token = iid
        if self._id_ver_token is None:
            self._id_ver_token = self.after_idle(self._ver_ultimo_token)

    def _ver_ultimo_token(self) -> None:
        """Baja a la última fila una vez por ciclo de eventos; `see` cuesta más cuantas más filas hay."""
        self._id_ver_token = None
        if self._ultimo_token is not None and self.arbol_tokens.exists(self._ultimo_token):
            self.arbol_tokens.see(self._ultimo_token)

    def mostrar_tabla_simbolos(self, tabla) -> None:
        """Llena la tabla de símbolos por cubeta y escribe la fórmula del hash y las cifras de la tabla."""
        self.arbol_simbolos.delete(*self.arbol_simbolos.get_children())
        for indice, cubeta in enumerate(tabla.cubetas()):
            for entrada in cubeta:
                self.arbol_simbolos.insert("", "end", tags=(("colision",) if len(cubeta) > 1 else ()), values=(
                    indice, entrada.valor_hash, recortar(entrada.lexema), entrada.categoria.value,
                    entrada.tipo_dato or "", formatear_valor(entrada.valor),
                    entrada.linea_declaracion or "", len(entrada.apariciones),
                    formatear_apariciones(entrada.apariciones)))
        e = tabla.estadisticas()
        visibles = e.cantidad - e.cubetas_ocupadas
        self.etiqueta_resumen.configure(text=(
            f"Función hash: h = (h · {reglas.BASE_HASH} + código(c)) mod {_modulo_hash()}  ·  "
            f"cubeta = h mod capacidad  ·  Capacidad: {e.capacidad}  ·  Símbolos: {e.cantidad}  ·  "
            f"Factor de carga: {e.factor_carga:.2f}  ·  Redimensionados: {e.redimensionados}  ·  "
            f"Colisiones al insertar: {e.colisiones}  ·  En la tabla actual: {visibles} (filas resaltadas)"))

    def mostrar_estadisticas(self, resultado: ResultadoAnalisis) -> None:
        """Pestaña Resumen: veredictos, tokens por categoría con barras, líneas, caracteres y errores por tipo."""
        c, base = self.lienzo, fuente_interfaz(12)[0]
        c.delete("all")
        y = 20

        def titulo(texto: str) -> None:
            nonlocal y
            c.create_text(20, y, text=texto, anchor="w", fill=TEMA["texto_secundario"], font=(base, 11, "bold"))
            y += 26

        def linea(texto: str, color: str = TEMA["texto"], negrita: bool = False) -> None:
            nonlocal y
            c.create_text(20, y, text=texto, anchor="w", fill=color, font=(base, 12, "bold" if negrita else "normal"))
            y += 26

        def veredicto(nombre: str, valido: bool) -> None:
            linea(f"{nombre}:  {'válido' if valido else 'inválido'}", TEMA["exito"] if valido else TEMA["error"])

        titulo("VEREDICTO")
        veredicto("Léxico", resultado.es_valida_lexicamente)
        veredicto("Estructura", resultado.es_valida_estructuralmente)
        linea(f"Cadena de entrada:  {'VÁLIDA' if resultado.es_valida else 'INVÁLIDA'}",
              TEMA["exito"] if resultado.es_valida else TEMA["error"], negrita=True)
        y += 8
        titulo("TOKENS POR CATEGORÍA")
        conteo = resultado.conteo_por_tipo()
        mayor = max(conteo.values(), default=1)
        for tipo, cantidad in conteo.items():
            c.create_text(20, y, text=tipo.value, anchor="w", fill=TEMA["texto"], font=(base, 12))
            ancho = max(3, int(200 * cantidad / mayor))
            c.create_rectangle(190, y - 8, 190 + ancho, y + 8, fill=COLORES_TOKEN[tipo], outline="")
            c.create_text(200 + ancho, y, text=str(cantidad), anchor="w", fill=TEMA["texto"], font=(base, 12))
            y += 24
        y += 12
        titulo("RESUMEN")
        linea(f"Líneas: {resultado.cantidad_lineas}    Caracteres: {resultado.cantidad_caracteres}    "
              f"Tokens: {len(resultado.tokens)}")
        for tipo in TipoDiagnostico:
            cantidad = resultado.manejador.cantidad(tipo)
            if cantidad:
                linea(f"Errores {tipo.value.lower()}: {cantidad}", TEMA["error"])
        if not resultado.manejador.hay_errores():
            linea("Sin errores", TEMA["exito"])
        c.configure(scrollregion=(0, 0, 500, y + 20))

    def mostrar_explicacion(self, explicacion: ExplicacionToken) -> None:
        """Pestaña Autómatas: lo que se sabe del token, con el selector puesto en el AFD que lo reconoció."""
        t = self.educativo
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("end", f"{explicacion.categoria}   ", "titulo")
        t.insert("end", recortar(explicacion.token.lexema, 60) + "\n", ("titulo", "codigo"))
        for linea in explicacion.detalle.split("\n"):
            nombre, separador, resto = linea.partition(": ")
            etiqueta = "error" if nombre.startswith("Error") else "valor"
            if separador and len(nombre) < 24:
                t.insert("end", nombre + ":  ", "campo")
                t.insert("end", resto + "\n", etiqueta)
            else:
                t.insert("end", linea + "\n", etiqueta)
        automata = next((a for a in reglas.AUTOMATAS if a["nombre"] == explicacion.reconocedor), None)
        if automata is not None:
            self.selector_automata.set(automata["nombre"])
            _escribir_tabla_transiciones(t, automata)
        t.configure(state="disabled")

    def mostrar_automata(self, nombre: str) -> None:
        """Solo la tabla de transiciones y los estados finales del AFD `nombre`, sin token."""
        automata = next(a for a in reglas.AUTOMATAS if a["nombre"] == nombre)
        self.selector_automata.set(nombre)
        t = self.educativo
        t.configure(state="normal")
        t.delete("1.0", "end")
        _escribir_tabla_transiciones(t, automata)
        t.configure(state="disabled")

    def limpiar(self) -> None:
        """Vacía los resultados, deshabilita la tabla de símbolos y vuelve a la pestaña Tokens."""
        for arbol in (self.arbol_tokens, self.arbol_simbolos):
            arbol.delete(*arbol.get_children())
        self._tokens.clear()
        self._ultimo_token = None
        self.etiqueta_resumen.configure(text="")
        self.lienzo.delete("all")
        self.lienzo.create_text(20, 24, anchor="w", fill=TEMA["texto_tenue"], font=fuente_interfaz(13),
                                text="El resumen aparece al terminar el análisis.")
        self.mostrar_automata(reglas.AUTOMATAS[0]["nombre"])
        self.educativo.configure(state="normal")
        self.educativo.insert("1.0", "Seleccione un token, o use «Paso a paso», para ver cómo se reconoció.\n", "vacio")
        self.educativo.configure(state="disabled")
        self.habilitar_tabla_simbolos(False)
        self.mostrar("tokens")

    def habilitar_tabla_simbolos(self, activo: bool) -> None:
        """La tabla de símbolos solo está disponible al terminar el análisis."""
        self.cuaderno.tab(self._marcos["simbolos"], state="normal" if activo else "disabled")

    def tabla_simbolos_habilitada(self) -> bool:
        """True si la tabla de símbolos está disponible."""
        return str(self.cuaderno.tab(self._marcos["simbolos"], "state")) == "normal"


class PanelErrores(ttk.Frame):
    """Manejador de errores: título con el total, tabla y detalle del error elegido."""

    def __init__(self, padre, al_seleccionar_error: Callable[[Diagnostico], None]) -> None:
        super().__init__(padre)
        self._al_error = al_seleccionar_error
        self._errores: dict[str, Diagnostico] = {}
        self.titulo = ttk.Label(self)
        self.titulo.pack(side="top", anchor="w", pady=(0, 6))
        caja = ttk.Frame(self, style="Panel.TFrame", height=178, padding=(12, 8))
        caja.pack(side="bottom", fill="x", pady=(8, 0))
        caja.pack_propagate(False)
        self.detalle_titulo = ttk.Label(caja, style="PanelError.TLabel")
        self.detalle_titulo.pack(anchor="w")
        self.detalle_error = ttk.Label(caja, style="Panel.TLabel", justify="left")
        self.detalle_error.pack(anchor="w", pady=(4, 0))
        caja.bind("<Configure>", lambda e: self.detalle_error.configure(wraplength=e.width - 24))
        self.arbol_errores = _tabla(self, COLUMNAS_ERRORES, estirar=("error",))
        self.arbol_errores.tag_configure("error", foreground=TEMA["error"])
        self.arbol_errores.bind("<Double-1>", self._doble_clic_error)
        self.arbol_errores.bind("<<TreeviewSelect>>", self._mostrar_detalle_error)
        self.limpiar()

    def _actualizar_titulo(self) -> None:
        n = len(self._errores)
        if n:
            self.titulo.configure(text=f"Manejador de errores ({n} {'error' if n == 1 else 'errores'})",
                                  style="TituloError.TLabel")
        else:
            self.titulo.configure(text="Manejador de errores (sin errores)", style="Titulo.TLabel")

    def _mostrar_detalle_error(self, _evento=None) -> None:
        """Detalle completo del error elegido, porque las columnas de la tabla recortan el texto."""
        seleccion = self.arbol_errores.selection()
        d = self._errores.get(seleccion[0]) if seleccion else None
        if d is None:
            self.detalle_titulo.configure(text="")
            self.detalle_error.configure(text=_AYUDA_ERRORES)
            return
        posicion = f" — línea {d.linea}, columna {d.columna}" if d.linea > 0 else ""
        self.detalle_titulo.configure(text=f"{d.codigo} · {d.titulo}{posicion}")
        lexema = f"Lexema: {d.lexema!r}\n" if d.lexema else ""
        self.detalle_error.configure(text=f"{lexema}{d.mensaje}\nSugerencia: {d.sugerencia}")

    def _doble_clic_error(self, evento) -> None:
        fila = self.arbol_errores.identify_row(evento.y)
        if fila in self._errores:
            self._al_error(self._errores[fila])

    def agregar_error(self, diagnostico: Diagnostico) -> None:
        """Agrega una fila a la tabla de errores."""
        con_posicion = diagnostico.linea > 0
        iid = self.arbol_errores.insert("", "end", tags=("error",), values=(
            diagnostico.codigo, diagnostico.linea if con_posicion else "—",
            diagnostico.columna if con_posicion else "—", recortar(diagnostico.lexema), diagnostico.titulo))
        self._errores[iid] = diagnostico
        self.arbol_errores.see(iid)
        self._actualizar_titulo()

    def quitar_errores_de_archivo(self) -> None:
        """Quita las filas de errores de archivo (ARC-) para que se vea una sola a la vez."""
        for iid, diagnostico in list(self._errores.items()):
            if diagnostico.tipo == TipoDiagnostico.ARCHIVO:
                self.arbol_errores.delete(iid)
                del self._errores[iid]
        self._actualizar_titulo()
        self._mostrar_detalle_error()

    def limpiar(self) -> None:
        """Vacía la tabla y el detalle."""
        self.arbol_errores.delete(*self.arbol_errores.get_children())
        self._errores.clear()
        self._actualizar_titulo()
        self._mostrar_detalle_error()
