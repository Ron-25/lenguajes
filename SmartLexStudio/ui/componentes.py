"""Piezas de la ventana: barra de título, barra de actividad, explorador, referencia del lenguaje, consola y barra de estado."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Iterable

from application.archivos import listar_ejemplos
from config import reglas
from core.modelos import TipoToken
from ui.estilos import TEMA, fuente_codigo, fuente_interfaz

_MAX_LINEAS_CONSOLA = 5000
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
PAUSA_POR_DEFECTO_MS = 120  # del deslizador «Pausa por línea»; interfaz.py las importa de aquí
PAUSA_MAXIMA_MS = 500

# (clave, texto, estilo) de los botones de la barra de título
_GRUPO_ARCHIVO = (("nuevo", "Nuevo", "Menu.TButton"), ("abrir", "Abrir…", "Menu.TButton"))
_GRUPO_GUARDAR = (("guardar", "Guardar", "Menu.TButton"), ("limpiar", "Limpiar", "Menu.TButton"))
_GRUPO_EJECUCION = (("analizar", "Analizar", "Primario.TButton"), ("paso", "Paso a paso", "Secundario.TButton"),
                    ("detener", "Detener", "Secundario.TButton"))


class Cabecera(tk.Frame):
    """Barra de título al estilo de VS Code: menú de archivo a la izquierda, centro de comandos con el
    archivo abierto y, a la derecha, la ejecución (Analizar, Paso a paso, Detener), la pausa y la ayuda."""

    def __init__(self, padre, acciones: dict[str, Callable], al_elegir_ejemplo: Callable[[Path], None],
                 al_ver_tabla: Callable) -> None:
        super().__init__(padre, background=TEMA["cabecera"])
        self._al_elegir = al_elegir_ejemplo
        self.botones: dict[str, ttk.Button] = {}
        fila = tk.Frame(self, background=TEMA["cabecera"])
        fila.pack(fill="x", padx=(8, 8), pady=4)
        tk.Frame(self, height=1, background=TEMA["borde"]).pack(fill="x")
        self._grupo(fila, _GRUPO_ARCHIVO, acciones)
        self._menu_ejemplos(fila)
        self._grupo(fila, _GRUPO_GUARDAR, acciones)
        derecha = tk.Frame(fila, background=TEMA["cabecera"])
        derecha.pack(side="right")
        self.botones["ayuda"] = ttk.Button(derecha, text="Ayuda", style="Menu.TButton",
                                           command=acciones["ayuda"], width=0)
        self.botones["ayuda"].pack(side="right")
        self.boton_tabla = ttk.Button(derecha, text="Tabla de símbolos", style="Menu.TButton",
                                      command=al_ver_tabla, width=0)
        self.boton_tabla.pack(side="right", padx=(0, 2))
        self._separador(derecha)
        self._construir_pausa(derecha)
        self._separador(derecha)
        for clave, texto, estilo in reversed(_GRUPO_EJECUCION):
            boton = ttk.Button(derecha, text=texto, style=estilo, command=acciones[clave], width=0)
            boton.pack(side="right", padx=(4, 0))
            self.botones[clave] = boton
        self._izquierda_fin = self.botones["limpiar"]
        self._derecha = derecha
        self._centro_de_comandos(fila)
        self.habilitar_ver_tabla(False)

    def _grupo(self, fila, grupo, acciones) -> None:
        for clave, texto, estilo in grupo:
            boton = ttk.Button(fila, text=texto, style=estilo, command=acciones[clave], width=0)
            boton.pack(side="left", padx=(0, 1))
            self.botones[clave] = boton

    def _separador(self, fila) -> None:
        tk.Frame(fila, width=1, height=18, background=TEMA["borde_entrada"]).pack(side="right", padx=6)

    def _centro_de_comandos(self, fila) -> None:
        """Caja central como la barra de búsqueda de VS Code; muestra el archivo abierto."""
        self._caja = tk.Frame(fila, background=TEMA["entrada"], highlightthickness=1,
                              highlightbackground=TEMA["borde_entrada"], highlightcolor=TEMA["borde_entrada"])
        self._titulo = tk.Label(self._caja, background=TEMA["entrada"], foreground=TEMA["texto_secundario"],
                                font=fuente_interfaz(12), padx=28)
        self._titulo.pack()
        self.establecer_titulo(None)
        fila.bind("<Configure>", lambda _e: self.after_idle(self._colocar_centro))

    def _colocar_centro(self) -> None:
        """Centra la caja en el hueco libre entre los dos grupos de botones; si no cabe, la oculta.

        Va con `place` para que no sume al ancho mínimo de la barra.
        """
        inicio = self._izquierda_fin.winfo_x() + self._izquierda_fin.winfo_width() + 12
        fin = self._derecha.winfo_x() - 12
        ancho = min(self._caja.winfo_reqwidth(), 360)
        if fin - inicio < ancho:
            self._caja.place_forget()
            return
        centro = max(inicio + ancho // 2, min(fin - ancho // 2, self._caja.master.winfo_width() // 2))
        self._caja.place(x=centro, rely=0.5, anchor="center", width=ancho)

    def establecer_titulo(self, nombre: str | None) -> None:
        """Texto del centro de comandos: el archivo abierto o el nombre de la aplicación."""
        self._titulo.configure(text=f"{nombre} — SmartLex Studio" if nombre else "SmartLex Studio")
        self.after_idle(self._colocar_centro)

    def _menu_ejemplos(self, fila) -> None:
        """Menú «Ejemplos»: se rellena cada vez que se abre, así un archivo nuevo aparece sin reiniciar."""
        self.menu_ejemplos = tk.Menu(fila, tearoff=0, postcommand=self._llenar_ejemplos)
        boton = ttk.Menubutton(fila, text="Ejemplos", style="Cabecera.TMenubutton", menu=self.menu_ejemplos, width=0)
        boton.pack(side="left", padx=(0, 1))

    def _llenar_ejemplos(self) -> None:
        self.menu_ejemplos.delete(0, "end")
        for ruta in listar_ejemplos():
            self.menu_ejemplos.add_command(label=ruta.name, command=lambda r=ruta: self._al_elegir(r))

    def _construir_pausa(self, fila) -> None:
        """Deslizador «Pausa por línea» (se empaqueta de derecha a izquierda)."""
        self._etiqueta_pausa = tk.Label(fila, background=TEMA["cabecera"], foreground=TEMA["texto"],
                                        font=fuente_interfaz(12), width=5, anchor="w")
        self._etiqueta_pausa.pack(side="right", padx=(6, 0))
        self._escala = ttk.Scale(fila, from_=0, to=PAUSA_MAXIMA_MS, length=80, style="Cabecera.Horizontal.TScale",
                                 command=lambda _v: self._actualizar_etiqueta())
        self._escala.pack(side="right")
        tk.Label(fila, text="Pausa", background=TEMA["cabecera"], foreground=TEMA["cabecera_tenue"],
                 font=fuente_interfaz(12)).pack(side="right", padx=(0, 6))
        self.establecer_pausa(PAUSA_POR_DEFECTO_MS)

    def _actualizar_etiqueta(self) -> None:
        self._etiqueta_pausa.configure(text=f"{self.pausa_ms()} ms")

    def pausa_ms(self) -> int:
        """Valor del deslizador en múltiplos de 10 ms."""
        return int(round(float(self._escala.get()) / 10) * 10)

    def establecer_pausa(self, ms: int) -> None:
        """Fija el deslizador por código (lo usan las pruebas y las capturas)."""
        self._escala.set(ms)
        self._actualizar_etiqueta()

    def habilitar(self, nombres: Iterable[str]) -> None:
        """Activa solo los botones indicados."""
        activos = set(nombres)
        for nombre, boton in self.botones.items():
            boton.state(["!disabled"] if nombre in activos else ["disabled"])

    def habilitar_ver_tabla(self, activo: bool) -> None:
        """«Tabla de símbolos» solo está disponible al terminar el análisis."""
        self.boton_tabla.state(["!disabled"] if activo else ["disabled"])


# Dibujos de la barra de actividad: líneas y polígonos sobre una cuadrícula de 48 × 48 px.
_DIBUJOS = {
    "explorador": [("poly", (17, 15, 25, 15, 30, 20, 30, 35, 17, 35)), ("line", (25, 15, 25, 20, 30, 20)),
                   ("line", (13, 19, 13, 31))],
    "analizar": [("poly", (18, 14, 33, 24, 18, 34))],
    "lenguaje": [("poly", (15, 15, 33, 15, 33, 34, 15, 34)), ("line", (20, 15, 20, 34)),
                 ("line", (24, 21, 29, 21)), ("line", (24, 25, 29, 25))],
    "consola": [("poly", (13, 16, 35, 16, 35, 33, 13, 33)), ("line", (18, 21, 22, 24.5, 18, 28)),
                ("line", (24, 28, 30, 28))],
    "ayuda": [("oval", (14, 14, 34, 34)), ("text", (24, 24, "?"))],
}


class _ElementoActividad(tk.Canvas):
    """Un botón de la barra de actividad: dibujo gris, blanco al pasar o al estar activo, barra azul si activo."""

    def __init__(self, padre, dibujo: str, al_pulsar: Callable[[], None]) -> None:
        super().__init__(padre, width=48, height=48, background=TEMA["cabecera"], highlightthickness=0,
                         cursor="hand2")
        self._activo = False
        self._encima = False
        for figura, puntos in _DIBUJOS[dibujo]:
            if figura == "poly":
                self.create_polygon(*puntos, outline="", fill="", width=1.5, tags="trazo", joinstyle="round")
            elif figura == "line":
                self.create_line(*puntos, fill="", width=1.5, tags=("trazo", "linea"), capstyle="round")
            elif figura == "oval":
                self.create_oval(*puntos, outline="", width=1.5, tags="trazo")
            else:
                self.create_text(puntos[0], puntos[1], text=puntos[2], tags=("trazo", "letra"),
                                 font=fuente_interfaz(14) + ("bold",))
        self._barra = self.create_rectangle(0, 0, 2, 48, fill=TEMA["acento"], outline="", state="hidden")
        self.bind("<Enter>", lambda _e: self._pintar(encima=True))
        self.bind("<Leave>", lambda _e: self._pintar(encima=False))
        self.bind("<Button-1>", lambda _e: al_pulsar())
        self._pintar()

    def activar(self, activo: bool) -> None:
        """Marca el elemento como la vista abierta."""
        self._activo = activo
        self._pintar()

    def _pintar(self, encima: bool | None = None) -> None:
        if encima is not None:
            self._encima = encima
        color = TEMA["texto"] if (self._activo or self._encima) else TEMA["actividad_tenue"]
        for item in self.find_withtag("trazo"):
            tipo = self.type(item)
            if tipo == "line" or tipo == "text":
                self.itemconfigure(item, fill=color)
            else:
                self.itemconfigure(item, outline=color)
        self.itemconfigure(self._barra, state="normal" if self._activo else "hidden")


class BarraActividad(tk.Frame):
    """Columna de la izquierda de VS Code: explorador, ejecutar, lenguaje y consola; ayuda abajo."""

    def __init__(self, padre, acciones: dict[str, Callable[[], None]]) -> None:
        super().__init__(padre, background=TEMA["cabecera"], width=48)
        self.elementos: dict[str, _ElementoActividad] = {}
        for clave in ("explorador", "analizar", "lenguaje", "consola"):
            self.elementos[clave] = _ElementoActividad(self, clave, acciones[clave])
            self.elementos[clave].pack(side="top")
        self.elementos["ayuda"] = _ElementoActividad(self, "ayuda", acciones["ayuda"])
        self.elementos["ayuda"].pack(side="bottom", pady=(0, 6))

    def activar(self, clave: str, activo: bool) -> None:
        """Enciende o apaga la marca de vista abierta de `clave`."""
        self.elementos[clave].activar(activo)


class Explorador(tk.Frame):
    """Barra lateral «Explorador»: la carpeta de ejemplos; un clic abre el archivo."""

    def __init__(self, padre, al_abrir: Callable[[Path], None]) -> None:
        super().__init__(padre, background=TEMA["panel"], width=220)
        self._al_abrir = al_abrir
        self._rutas: dict[str, Path] = {}
        tk.Label(self, text="EXPLORADOR", background=TEMA["panel"], foreground=TEMA["texto_secundario"],
                 font=fuente_interfaz(11), anchor="w", padx=20, pady=10).pack(fill="x")
        self.arbol = ttk.Treeview(self, show="tree", selectmode="browse", style="Explorador.Treeview")
        self.arbol.pack(fill="both", expand=True, padx=(0, 0))
        self.arbol.tag_configure("carpeta", font=fuente_interfaz(11) + ("bold",))
        self.arbol.tag_configure("archivo", foreground=TEMA["texto"])
        self.arbol.tag_configure("abierto", foreground=TEMA["blanco"])
        self.arbol.bind("<ButtonRelease-1>", self._clic)
        self.arbol.bind("<Return>", lambda _e: self._abrir(self.arbol.focus()))
        self.refrescar(None)

    def refrescar(self, actual: Path | None) -> None:
        """Relee la carpeta de ejemplos y resalta el archivo abierto."""
        self.arbol.delete(*self.arbol.get_children())
        self._rutas.clear()
        carpeta = self.arbol.insert("", "end", text="EJEMPLOS", open=True, tags=("carpeta",))
        elegido = None
        rutas = listar_ejemplos()
        if actual is not None and all(r.resolve() != actual.resolve() for r in rutas):
            abierto = self.arbol.insert("", 0, text="ABIERTO", open=True, tags=("carpeta",))
            elegido = self.arbol.insert(abierto, "end", text=actual.name, tags=("archivo", "abierto"))
            self._rutas[elegido] = actual
        for ruta in rutas:
            es_actual = actual is not None and ruta.resolve() == actual.resolve()
            iid = self.arbol.insert(carpeta, "end", text=ruta.name,
                                    tags=("archivo", "abierto") if es_actual else ("archivo",))
            self._rutas[iid] = ruta
            if es_actual:
                elegido = iid
        if elegido is not None:
            self.arbol.selection_set(elegido)
            self.arbol.focus(elegido)
        else:
            self.arbol.selection_remove(*self.arbol.selection())

    def _clic(self, evento) -> None:
        self._abrir(self.arbol.identify_row(evento.y))

    def _abrir(self, iid: str) -> None:
        if iid in self._rutas:
            self._al_abrir(self._rutas[iid])


class VistaLenguaje(ttk.Frame):
    """Referencia de FlowLang armada desde `config.reglas`: palabras, números, operadores, delimitadores y límites."""

    def __init__(self, padre) -> None:
        super().__init__(padre, style="Panel.TFrame")
        self._descripciones: dict[str, str] = {}
        marco = ttk.Frame(self, style="Panel.TFrame")
        marco.pack(fill="both", expand=True)
        self.arbol = ttk.Treeview(marco, show="tree", selectmode="browse")
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=barra.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.arbol.bind("<<TreeviewSelect>>", self._mostrar_descripcion)
        self.detalle = ttk.Label(self, style="Tenue.TLabel", wraplength=1000, justify="left",
                                 padding=(14, 8), text="Seleccione un elemento para ver su descripción.")
        self.detalle.pack(fill="x")
        self._construir_arbol()

    def _nodo(self, padre: str, texto: str, descripcion: str = "", abierto: bool = False) -> str:
        iid = self.arbol.insert(padre, "end", text=texto, open=abierto)
        if descripcion:
            self._descripciones[iid] = descripcion
        return iid

    def _construir_arbol(self) -> None:
        raiz = self._nodo("", f"Palabras reservadas ({len(reglas.PALABRAS_RESERVADAS)})", abierto=True)
        for palabra, descripcion in reglas.PALABRAS_RESERVADAS.items():
            self._nodo(raiz, palabra, descripcion)
        numeros = self._nodo("", "Números")
        for tipo in (TipoToken.ENTERO, TipoToken.DECIMAL, TipoToken.DURACION):
            info = reglas.INFO_CATEGORIAS[tipo]
            grupo = self._nodo(numeros, tipo.value, info["descripcion"])
            for ejemplo in info["ejemplos"]:
                self._nodo(grupo, ejemplo, f"Ejemplo de {tipo.value.lower()}: {info['descripcion']}")
        simbolos = self._nodo("", "Operadores")
        for tipo in (TipoToken.OPERADOR_ARITMETICO, TipoToken.OPERADOR_RELACIONAL,
                     TipoToken.OPERADOR_LOGICO, TipoToken.ASIGNACION):
            grupo = self._nodo(simbolos, tipo.value, reglas.INFO_CATEGORIAS[tipo]["descripcion"])
            for simbolo, categoria in reglas.OPERADORES.items():
                if categoria == tipo:
                    self._nodo(grupo, simbolo, reglas.INFO_CATEGORIAS[tipo]["descripcion"])
        delimitadores = self._nodo("", "Delimitadores", reglas.INFO_CATEGORIAS[TipoToken.DELIMITADOR]["descripcion"])
        for simbolo in reglas.DELIMITADORES:
            self._nodo(delimitadores, simbolo, "Delimitador de FlowLang.")
        escapes = self._nodo("", "Escapes en cadenas", "Secuencias válidas dentro de una cadena.")
        for letra, real in reglas.ESCAPES_VALIDOS.items():
            self._nodo(escapes, "\\" + letra, f"Representa {real!r}.")
        limites = self._nodo("", "Límites")
        self._nodo(limites, f"Identificador: máx. {reglas.LONGITUD_MAXIMA_IDENTIFICADOR}",
                   "Un identificador más largo produce LEX-005.")
        self._nodo(limites, "Extensiones: " + " ".join(reglas.EXTENSIONES_PERMITIDAS),
                   "Extensiones de archivo aceptadas.")
        self._nodo(limites, f"Archivo: máx. {reglas.TAMANO_MAXIMO_BYTES // 1000} KB", "Tamaño máximo del archivo fuente.")

    def _mostrar_descripcion(self, _evento) -> None:
        seleccion = self.arbol.selection()
        if seleccion:
            self.detalle.configure(text=self._descripciones.get(seleccion[0], ""))


class PanelConsola(ttk.Frame):
    """Registro de la evaluación, con un color por nivel."""

    def __init__(self, padre) -> None:
        super().__init__(padre, style="Panel.TFrame")
        self._id_bajar: str | None = None
        self.texto = tk.Text(self, height=8, wrap="none", state="disabled", font=fuente_codigo(13),
                             background=TEMA["panel"], foreground=TEMA["texto_codigo"], borderwidth=0,
                             highlightthickness=0, padx=14, pady=6)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.texto.yview)
        self.texto.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.texto.pack(side="left", fill="both", expand=True)
        for nivel, color in (("normal", TEMA["texto_codigo"]), ("error", TEMA["error"]),
                             ("exito", TEMA["exito"]), ("info", TEMA["info"])):
            self.texto.tag_configure(nivel, foreground=color)

    def escribir(self, texto: str, nivel: str = "normal") -> None:
        """Agrega una línea y baja hasta el final."""
        self.texto.configure(state="normal")
        self.texto.insert("end", texto + "\n", nivel)
        exceso = int(self.texto.index("end-1c").split(".")[0]) - _MAX_LINEAS_CONSOLA
        if exceso > 0:
            self.texto.delete("1.0", f"{exceso + 1}.0")
        self.texto.configure(state="disabled")
        if self._id_bajar is None:
            self._id_bajar = self.after_idle(self._bajar_al_final)

    def _bajar_al_final(self) -> None:
        """Un solo desplazamiento por ciclo de eventos; bajar con cada línea haría lento un archivo largo."""
        self._id_bajar = None
        self.texto.see("end")

    def limpiar(self) -> None:
        """Vacía el registro."""
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.configure(state="disabled")


class BarraEstado(ttk.Frame):
    """Barra de estado de VS Code: gris en reposo y azul mientras se analiza (como al depurar).

    Izquierda: lenguaje y contadores. Derecha: estado, posición del cursor, codificación y veredicto.
    """

    def __init__(self, padre) -> None:
        super().__init__(padre, style="Estado.TFrame", height=24)
        self.pack_propagate(False)
        self._marca = ttk.Label(self, style="Marca.TLabel", text=f"  {reglas.NOMBRE_LENGUAJE}  ", padding=(4, 0))
        self.contadores = ttk.Label(self, style="Estado.TLabel")
        self._estado = ttk.Label(self, style="Estado.TLabel")
        self._posicion = ttk.Label(self, style="Estado.TLabel")
        self._formato = ttk.Label(self, style="Estado.TLabel", text="UTF-8    LF")
        self.veredicto = ttk.Label(self, style="Veredicto.TLabel")
        self._etiquetas = (self.contadores, self._estado, self._posicion, self._formato, self.veredicto)
        self._marca.pack(side="left", fill="y")
        self.contadores.pack(side="left", padx=(12, 0))
        self.veredicto.pack(side="right", padx=(14, 12))
        self._formato.pack(side="right", padx=(14, 0))
        self._posicion.pack(side="right", padx=(14, 0))
        self._estado.pack(side="right", padx=(14, 0))
        self._valido: bool | None = None
        self.establecer_estado("Listo")
        self.establecer_contadores(0, 0, 0, 0, 0)
        self.establecer_posicion(1, 1)
        self.establecer_veredicto(None)

    def depurando(self, activo: bool) -> None:
        """Pinta la barra de azul mientras el análisis está en curso."""
        self.configure(style="Depurando.TFrame" if activo else "Estado.TFrame")
        for etiqueta in self._etiquetas:
            etiqueta.configure(style="Depurando.TLabel" if activo else
                               ("Veredicto.TLabel" if etiqueta is self.veredicto else "Estado.TLabel"))
        self.establecer_veredicto(self._valido)

    def establecer_estado(self, texto: str) -> None:
        """Mensaje del estado de la aplicación."""
        self._estado.configure(text=texto)

    def establecer_contadores(self, validas: int, con_errores: int, tokens: int, simbolos: int, errores: int) -> None:
        """Los contadores del análisis en una sola etiqueta."""
        self.contadores.configure(text=(f"Líneas válidas: {validas}  ·  Líneas con errores: {con_errores}  ·  "
                                        f"Tokens: {tokens}  ·  Símbolos: {simbolos}  ·  Errores: {errores}"))

    def establecer_posicion(self, linea: int, columna: int) -> None:
        """Línea y columna del cursor."""
        self._posicion.configure(text=f"Lín {linea}, Col {columna}")

    def establecer_veredicto(self, valido: bool | None) -> None:
        """Veredicto del análisis; None lo borra."""
        self._valido = valido
        azul = str(self.cget("style")) == "Depurando.TFrame"
        if valido is None:
            self.veredicto.configure(text="")
        elif valido:
            self.veredicto.configure(text=f"✓ El archivo es válido para {reglas.NOMBRE_LENGUAJE}",
                                     foreground=TEMA["blanco"] if azul else TEMA["exito"])
        else:
            self.veredicto.configure(text=f"✗ El archivo NO es válido para {reglas.NOMBRE_LENGUAJE}",
                                     foreground=TEMA["blanco"] if azul else TEMA["error"])
