"""Panel derecho con cinco pestanas: Tokens, Tabla de simbolos, Errores, Estadisticas y Modo educativo."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from application.analisis_service import ExplicacionToken, ResultadoAnalisis
from config import reglas
from core.modelos import Diagnostico, Token, TipoDiagnostico
from ui.estilos import COLORES_TOKEN, TEMA, fuente_codigo, fuente_interfaz

# (identificador, titulo, ancho)
COLUMNAS_TOKENS = [("n", "#", 56), ("linea", "Lín", 50), ("col", "Col", 50),
                   ("categoria", "Categoría", 150), ("lexema", "Lexema", 220)]
COLUMNAS_SIMBOLOS = [("cubeta", "Cubeta", 72), ("hash", "Hash", 100), ("lexema", "Lexema", 150),
                     ("categoria", "Categoría", 130), ("tipo", "Tipo", 90), ("valor", "Valor", 110),
                     ("decl", "Decl.", 50), ("apariciones", "Apariciones", 220)]
COLUMNAS_ERRORES = [("codigo", "Código", 80), ("tipo", "Tipo", 90), ("pos", "Lín:Col", 70),
                    ("mensaje", "Mensaje", 320), ("sugerencia", "Sugerencia", 320)]

_PESTANAS = (("tokens", "Tokens"), ("simbolos", "Tabla de símbolos"), ("errores", "Errores"),
             ("estadisticas", "Estadísticas"), ("educativo", "Modo educativo"))
_MAX_TEXTO = 40
_AYUDA_ERRORES = "Clic en un error: ver el detalle completo.  Doble clic: ir a su posición en el editor."


def recortar(texto: object, maximo: int = _MAX_TEXTO) -> str:
    """Texto en una linea (saltos como ⏎) y recortado a `maximo` caracteres."""
    limpio = str(texto).replace("\n", "⏎").replace("\t", "→")
    return limpio if len(limpio) <= maximo else limpio[:maximo] + "…"


def _tabla(padre, columnas) -> ttk.Treeview:
    """Treeview con barras de desplazamiento dentro de `padre`."""
    marco = ttk.Frame(padre)
    marco.pack(fill="both", expand=True)
    arbol = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings", selectmode="browse")
    for identificador, titulo, ancho in columnas:
        arbol.heading(identificador, text=titulo, anchor="w")
        arbol.column(identificador, width=ancho, minwidth=40, anchor="w", stretch=False)
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
    texto = tk.Text(padre, wrap="word", state="disabled", font=fuente, background=TEMA["fondo"],
                    foreground=TEMA["texto"], borderwidth=0, highlightthickness=0, padx=16, pady=12,
                    spacing1=2, spacing3=2)
    texto.pack(fill="both", expand=True)
    return texto


class PanelResultados(ttk.Frame):
    """Vista pasiva: muestra lo que le entrega la ventana y avisa de las selecciones del usuario."""

    def __init__(self, padre, al_seleccionar_token: Callable[[Token], None],
                 al_seleccionar_error: Callable[[Diagnostico], None]) -> None:
        super().__init__(padre)
        self._al_token = al_seleccionar_token
        self._al_error = al_seleccionar_error
        self._tokens: dict[str, Token] = {}
        self._ultimo_token: str | None = None
        self._id_ver_token: str | None = None
        self._errores: dict[str, Diagnostico] = {}
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self._marcos = {}
        for clave, titulo in _PESTANAS:
            marco = ttk.Frame(self.notebook)
            self.notebook.add(marco, text=titulo)
            self._marcos[clave] = marco
        self._construir_tokens(self._marcos["tokens"])
        self._construir_simbolos(self._marcos["simbolos"])
        self._construir_errores(self._marcos["errores"])
        self.lienzo = tk.Canvas(self._marcos["estadisticas"], background=TEMA["fondo"], highlightthickness=0)
        self.lienzo.pack(fill="both", expand=True)
        self.educativo = _texto_solo_lectura(self._marcos["educativo"], fuente_codigo(12))
        self._configurar_etiquetas_educativo()
        self.limpiar()

    # --- construccion ----------------------------------------------------
    def _construir_tokens(self, marco) -> None:
        self.arbol_tokens = _tabla(marco, COLUMNAS_TOKENS)
        for tipo, color in COLORES_TOKEN.items():
            self.arbol_tokens.tag_configure(tipo.name, foreground=color)
        self.arbol_tokens.bind("<<TreeviewSelect>>", self._seleccion_token)

    def _construir_simbolos(self, marco) -> None:
        self.etiqueta_resumen = ttk.Label(marco, padding=(12, 8), wraplength=520, justify="left")
        self.etiqueta_resumen.pack(fill="x")
        self.arbol_simbolos = _tabla(marco, COLUMNAS_SIMBOLOS)
        self.arbol_simbolos.tag_configure("colision", background=TEMA["colision"])

    def _construir_errores(self, marco) -> None:
        self.detalle_error = ttk.Label(marco, padding=(12, 8), wraplength=520, justify="left")
        self.detalle_error.pack(side="bottom", fill="x")
        self.arbol_errores = _tabla(marco, COLUMNAS_ERRORES)
        self.arbol_errores.tag_configure("error", foreground=TEMA["error"])
        self.arbol_errores.bind("<Double-1>", self._doble_clic_error)
        self.arbol_errores.bind("<<TreeviewSelect>>", self._mostrar_detalle_error)

    def _configurar_etiquetas_educativo(self) -> None:
        t = self.educativo
        t.tag_configure("titulo", foreground=TEMA["blanco"], font=(fuente_interfaz()[0], 14, "bold"), spacing3=8)
        t.tag_configure("campo", foreground=TEMA["texto_tenue"])
        t.tag_configure("valor", foreground=TEMA["texto"])
        t.tag_configure("codigo", foreground=TEMA["exito"])
        t.tag_configure("error", foreground=TEMA["error"])
        t.tag_configure("vacio", foreground=TEMA["texto_tenue"])

    # --- eventos ---------------------------------------------------------
    def _seleccion_token(self, _evento) -> None:
        seleccion = self.arbol_tokens.selection()
        if seleccion and seleccion[0] in self._tokens:
            self._al_token(self._tokens[seleccion[0]])

    def _mostrar_detalle_error(self, _evento=None) -> None:
        """Texto completo del error elegido: las columnas se recortan en paneles estrechos (AUD-20)."""
        seleccion = self.arbol_errores.selection()
        d = self._errores.get(seleccion[0]) if seleccion else None
        texto = f"{d.codigo} · {d.titulo}\n{d.mensaje}\n{d.sugerencia}" if d else _AYUDA_ERRORES
        self.detalle_error.configure(text=texto)

    def _doble_clic_error(self, evento) -> None:
        fila = self.arbol_errores.identify_row(evento.y)
        if fila in self._errores:
            self._al_error(self._errores[fila])

    # --- API publica -------------------------------------------------------
    def agregar_token(self, numero: int, token: Token) -> None:
        """Agrega una fila a la pestana Tokens (coloreada por categoria)."""
        iid = self.arbol_tokens.insert("", "end", tags=(token.tipo.name,), values=(
            numero, token.linea, token.columna, token.tipo.value, recortar(token.lexema)))
        self._tokens[iid] = token
        self._ultimo_token = iid
        if self._id_ver_token is None:
            self._id_ver_token = self.after_idle(self._ver_ultimo_token)

    def _ver_ultimo_token(self) -> None:
        """Desplaza a la ultima fila una vez por ciclo de eventos (`see` es lineal en filas; AUD-17)."""
        self._id_ver_token = None
        if self._ultimo_token is not None and self.arbol_tokens.exists(self._ultimo_token):
            self.arbol_tokens.see(self._ultimo_token)

    def agregar_error(self, diagnostico: Diagnostico) -> None:
        """Agrega una fila a la pestana Errores."""
        posicion = f"{diagnostico.linea}:{diagnostico.columna}" if diagnostico.linea else "—"
        iid = self.arbol_errores.insert("", "end", tags=("error",), values=(
            diagnostico.codigo, diagnostico.tipo.value, posicion, diagnostico.mensaje, diagnostico.sugerencia))
        self._errores[iid] = diagnostico
        self.arbol_errores.see(iid)

    def mostrar_tabla_simbolos(self, tabla) -> None:
        """Llena la pestana de simbolos en orden de cubeta y resume sus estadisticas."""
        self.arbol_simbolos.delete(*self.arbol_simbolos.get_children())
        for indice, cubeta in enumerate(tabla.cubetas()):
            for entrada in cubeta:
                self.arbol_simbolos.insert("", "end", tags=(("colision",) if len(cubeta) > 1 else ()), values=(
                    indice, entrada.valor_hash, recortar(entrada.lexema), entrada.categoria.value,
                    entrada.tipo_dato or "", recortar(entrada.valor) if entrada.valor is not None else "",
                    entrada.linea_declaracion or "", recortar(entrada.apariciones)))
        e = tabla.estadisticas()
        visibles = e.cantidad - e.cubetas_ocupadas
        self.etiqueta_resumen.configure(text=(
            f"Capacidad {e.capacidad}  ·  Entradas {e.cantidad}  ·  Factor de carga {e.factor_carga:.2f}  ·  "
            f"Colisiones al insertar {e.colisiones}  ·  En la tabla actual {visibles}  ·  "
            f"Cadena más larga {e.cadena_mas_larga}  ·  Redimensionados {e.redimensionados}"))

    def mostrar_estadisticas(self, resultado: ResultadoAnalisis) -> None:
        """Veredictos, tokens por categoria con barras, lineas, caracteres y errores por tipo."""
        c, base = self.lienzo, fuente_interfaz(12)[0]
        c.delete("all")
        y = 20

        def titulo(texto: str) -> None:
            nonlocal y
            c.create_text(20, y, text=texto, anchor="w", fill=TEMA["texto_tenue"], font=(base, 10, "bold"))
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
        """Muestra en el Modo educativo todo lo que se sabe del token."""
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
            t.insert("end", "\nTabla de transiciones de " + automata["nombre"] + "\n", "campo")
            for estado, fila in automata["transiciones"].items():
                celdas = "   ".join(f"{k} → {v}" for k, v in fila.items())
                t.insert("end", f"  {estado}:  {celdas}\n", "valor")
            finales = ", ".join(list(automata["aceptacion"]) + list(automata["errores"]))
            t.insert("end", f"  Estados finales: {finales}\n", "campo")
        t.configure(state="disabled")

    def limpiar(self) -> None:
        """Vacia las cinco pestanas y deshabilita la tabla de simbolos."""
        for arbol in (self.arbol_tokens, self.arbol_simbolos, self.arbol_errores):
            arbol.delete(*arbol.get_children())
        self._tokens.clear()
        self._ultimo_token = None
        self._errores.clear()
        self.detalle_error.configure(text=_AYUDA_ERRORES)
        self.etiqueta_resumen.configure(text="")
        self.lienzo.delete("all")
        self.lienzo.create_text(20, 24, anchor="w", fill=TEMA["texto_tenue"], font=fuente_interfaz(12),
                                text="Las estadísticas aparecen al terminar el análisis.")
        self.educativo.configure(state="normal")
        self.educativo.delete("1.0", "end")
        self.educativo.insert("end", "Seleccione un token, o use «Paso a paso», para ver cómo se reconoció.", "vacio")
        self.educativo.configure(state="disabled")
        self.habilitar_tabla_simbolos(False)

    def habilitar_tabla_simbolos(self, activo: bool) -> None:
        """La pestana de simbolos solo se habilita al terminar el analisis."""
        self.notebook.tab(self._marcos["simbolos"], state="normal" if activo else "disabled")

    def tabla_simbolos_habilitada(self) -> bool:
        """True si la pestana de simbolos esta disponible."""
        return str(self.notebook.tab(self._marcos["simbolos"], "state")) == "normal"

    def seleccionar_pestana(self, nombre: str) -> None:
        """Muestra la pestana 'tokens', 'simbolos', 'errores', 'estadisticas' o 'educativo'."""
        self.notebook.select(self._marcos[nombre])
