"""Componentes de la ventana: iconos, barras, tool windows, consola y barra de estado (arquitectura §16.6)."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Iterable

from application.archivos import listar_ejemplos
from config import reglas
from core.modelos import TipoToken
from ui import iconos
from ui.estilos import TEMA, fuente_codigo, fuente_interfaz

_MAX_LINEAS_CONSOLA = 5000
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

# (nombre, texto, atajo, grupo del menu): de aqui salen botones, menus y globos de la barra
_ACCIONES = (
    ("analizar", "Analizar", "F5", "ejecucion"), ("paso", "Paso a paso", "F10", "ejecucion"),
    ("detener", "Detener", "Esc", "ejecucion"), ("abrir", "Abrir", "Ctrl+O", "archivo"),
    ("guardar", "Guardar", "Ctrl+S", "archivo"), ("limpiar", "Limpiar", "", "archivo"),
    ("ayuda", "Ayuda", "F1", "archivo"),
)


class BotonIcono(tk.Canvas):
    """Boton de 30x30 con un icono de `iconos.TRAZOS`; `relleno` es una clave de TEMA (Analizar, Detener)."""

    def __init__(self, padre, nombre: str, command: Callable | None = None, relleno: str | None = None,
                 color: str = "texto_secundario", tam: int = 30, fondo: str = "panel") -> None:
        super().__init__(padre, width=tam, height=tam, highlightthickness=0, borderwidth=0, cursor="hand2")
        self.nombre, self.command, self.relleno, self._color = nombre, command, relleno, color
        self._tam, self._fondo = tam, fondo
        self.habilitado, self._activo, self._encima, self._contador = True, False, False, 0
        self.bind("<Enter>", lambda _e: self._cambiar_encima(True))
        self.bind("<Leave>", lambda _e: self._cambiar_encima(False))
        self.bind("<Button-1>", lambda _e: self.invocar())
        self._dibujar()

    def invocar(self) -> None:
        """Ejecuta `command` si el boton esta habilitado."""
        if self.habilitado and self.command is not None:
            self.command()

    def habilitar(self, activo: bool) -> None:
        """Habilita o deshabilita el boton (deshabilitado: sin relleno, gris tenue, sin respuesta)."""
        self.habilitado = activo
        self._dibujar()

    def marcar_activo(self, activo: bool) -> None:
        """Fondo `activo` (la vista que se esta mostrando en una franja)."""
        self._activo = activo
        self._dibujar()

    def poner_contador(self, cantidad: int) -> None:
        """Numero rojo en la esquina (0 lo oculta)."""
        self._contador = cantidad
        self._dibujar()

    def _cambiar_encima(self, encima: bool) -> None:
        self._encima = encima and self.habilitado
        self._dibujar()

    def _dibujar(self) -> None:
        t = self._tam
        rellenar = self.relleno is not None and self.habilitado
        if self._activo:
            fondo = TEMA["activo"]
        else:
            fondo = TEMA["borde"] if self._encima and self.relleno is None else TEMA[self._fondo]
        self.configure(background=fondo)
        self.delete("all")
        if rellenar:
            self.create_rectangle(1, 1, t - 1, t - 1, fill=TEMA[self.relleno], outline=TEMA[self.relleno])
        color = TEMA["texto_tenue"] if not self.habilitado else TEMA["blanco"] if rellenar else TEMA[self._color]
        iconos.dibujar(self, self.nombre, (t - 16) // 2, (t - 16) // 2, color)
        if self._contador:
            self.create_oval(t - 15, 0, t, 15, fill=TEMA["error"], outline="")
            self.create_text(t - 7, 8, text=str(min(self._contador, 99)), fill=TEMA["blanco"],
                             font=fuente_interfaz(10))


class Globo:
    """Texto de ayuda al detenerse sobre un widget (Toplevel sin decoracion, como idlelib.tooltip)."""

    def __init__(self, widget, texto: str) -> None:
        self.widget, self.texto = widget, texto
        self._ventana: tk.Toplevel | None = None
        self._id: str | None = None
        widget.bind("<Enter>", self._programar, add="+")
        widget.bind("<Leave>", self._ocultar, add="+")
        widget.bind("<ButtonPress>", self._ocultar, add="+")

    def _programar(self, _evento=None) -> None:
        self._ocultar()
        self._id = self.widget.after(500, self._mostrar)

    def _mostrar(self) -> None:
        self._id = None
        try:
            ventana = tk.Toplevel(self.widget)
            ventana.wm_overrideredirect(True)
            ventana.configure(background=TEMA["borde"])
            tk.Label(ventana, text=self.texto, background=TEMA["ayuda_fondo"], foreground=TEMA["texto"],
                     font=fuente_interfaz(12), padx=8, pady=4).pack(padx=1, pady=1)
            ventana.geometry(f"+{self.widget.winfo_rootx()}+{self.widget.winfo_rooty() + self.widget.winfo_height() + 4}")
            self._ventana = ventana
        except tk.TclError:
            self._ventana = None  # sin globo: la accion sigue disponible en los menus

    def _ocultar(self, _evento=None) -> None:
        if self._id is not None:
            self.widget.after_cancel(self._id)
            self._id = None
        if self._ventana is not None:
            self._ventana.destroy()
            self._ventana = None


class PanelHerramientas(ttk.Frame):
    """Una tool window: cabecera (titulo de la vista + ocultar) y varias vistas apiladas, una visible."""

    def __init__(self, padre, al_ocultar: Callable[[], None] | None = None) -> None:
        super().__init__(padre, style="Panel.TFrame")
        self.al_ocultar = al_ocultar
        self.vista_actual: str | None = None
        self._vistas: dict[str, tuple[str, tk.Misc]] = {}
        cabecera = ttk.Frame(self, style="Panel.TFrame", height=32)
        cabecera.pack(fill="x")
        cabecera.pack_propagate(False)
        self._titulo = ttk.Label(cabecera, style="Cabecera.TLabel")
        self._titulo.pack(side="left", padx=(14, 0))
        BotonIcono(cabecera, "ocultar", self._ocultar, tam=24).pack(side="right", padx=6)
        self.cuerpo = ttk.Frame(self, style="Panel.TFrame")
        self.cuerpo.pack(fill="both", expand=True)

    def _ocultar(self) -> None:
        if self.al_ocultar is not None:
            self.al_ocultar()

    def agregar_vista(self, nombre: str, titulo: str, vista) -> None:
        """Registra una vista (hija de `cuerpo`); la primera queda visible."""
        self._vistas[nombre] = (titulo, vista)
        if self.vista_actual is None:
            self.mostrar(nombre)

    def mostrar(self, nombre: str) -> None:
        """Deja visible la vista `nombre` y pone su titulo en la cabecera."""
        for _titulo, vista in self._vistas.values():
            vista.pack_forget()
        titulo, vista = self._vistas[nombre]
        vista.pack(fill="both", expand=True)
        self._titulo.configure(text=titulo)
        self.vista_actual = nombre


class FranjaHerramientas(ttk.Frame):
    """Columna de 40 px con un `BotonIcono` por tool window; unos arriba y otros abajo."""

    def __init__(self, padre, al_pulsar: Callable[[str], None]) -> None:
        super().__init__(padre, style="Panel.TFrame", width=40)
        self._al_pulsar = al_pulsar
        self._botones: dict[str, BotonIcono] = {}
        self._arriba = ttk.Frame(self, style="Panel.TFrame")
        self._abajo = ttk.Frame(self, style="Panel.TFrame")
        self._arriba.pack(side="top", pady=(6, 0))
        self._abajo.pack(side="bottom", pady=(0, 6))

    def agregar(self, nombre: str, descripcion: str, abajo: bool = False) -> None:
        """Agrega el icono `nombre` (con su globo) arriba o abajo."""
        boton = BotonIcono(self._abajo if abajo else self._arriba, nombre, lambda n=nombre: self._al_pulsar(n))
        boton.pack(pady=2, padx=5)
        Globo(boton, descripcion)
        self._botones[nombre] = boton

    def marcar(self, nombres: Iterable[str]) -> None:
        """Resalta los iconos indicados y quita el resalte a los demas."""
        activos = set(nombres)
        for nombre, boton in self._botones.items():
            boton.marcar_activo(nombre in activos)

    def habilitar(self, nombre: str, activo: bool) -> None:
        """Habilita o deshabilita un icono."""
        self._botones[nombre].habilitar(activo)

    def poner_contador(self, nombre: str, cantidad: int) -> None:
        """Numero rojo sobre un icono."""
        self._botones[nombre].poner_contador(cantidad)


class _Desplegable(tk.Label):
    """Widget de la barra con una flecha ▾ que abre un menu (como «proyecto ▾» de PyCharm)."""

    def __init__(self, padre, texto: str, menu: tk.Menu) -> None:
        super().__init__(padre, text=texto + " ▾", background=TEMA["panel"], foreground=TEMA["texto"],
                         font=fuente_interfaz(13), padx=10, pady=4, cursor="hand2")
        self.menu = menu
        self.bind("<Button-1>", self._abrir)
        self.bind("<Enter>", lambda _e: self.configure(background=TEMA["borde"]))
        self.bind("<Leave>", lambda _e: self.configure(background=TEMA["panel"]))

    def _abrir(self, _evento) -> None:
        self.menu.tk_popup(self.winfo_rootx(), self.winfo_rooty() + self.winfo_height())
        self.menu.grab_release()


class BarraHerramientas(ttk.Frame):
    """Barra superior (zona A): logo, dos menus desplegables, Analizar/Paso a paso/Detener e iconos."""

    def __init__(self, padre, acciones: dict[str, Callable]) -> None:
        super().__init__(padre, style="Barra.TFrame", height=40)
        self.pack_propagate(False)
        self._acciones = acciones
        self.botones: dict[str, BotonIcono] = {}
        logo = tk.Canvas(self, width=26, height=26, highlightthickness=0, background=TEMA["panel"])
        logo.create_rectangle(0, 0, 25, 25, fill=TEMA["acento"], outline="")
        logo.create_text(13, 13, text="SL", fill=TEMA["blanco"], font=fuente_interfaz(11) + ("bold",))
        logo.pack(side="left", padx=(12, 4))
        self.menu_archivo = self._crear_menu("archivo")
        self.menu_ejecucion = self._crear_menu("ejecucion")
        _Desplegable(self, "SmartLex Studio", self.menu_archivo).pack(side="left")
        _Desplegable(self, f"{reglas.NOMBRE_LENGUAJE} · Análisis léxico", self.menu_ejecucion).pack(side="left", padx=(16, 8))
        for nombre, relleno, color in (("analizar", "exito", "exito"), ("paso", None, "exito"), ("detener", "detener", "detener")):
            self._boton(nombre, relleno, color).pack(side="left", padx=3)
        for nombre in ("ayuda", "limpiar", "guardar", "abrir"):
            self._boton(nombre, None, "texto_secundario").pack(side="right", padx=3)

    def _boton(self, nombre: str, relleno: str | None, color: str) -> BotonIcono:
        _n, texto, atajo, _g = next(a for a in _ACCIONES if a[0] == nombre)
        boton = BotonIcono(self, nombre, self._acciones[nombre], relleno=relleno, color=color)
        Globo(boton, f"{texto} ({atajo})" if atajo else texto)
        self.botones[nombre] = boton
        return boton

    def _crear_menu(self, grupo: str) -> tk.Menu:
        menu = tk.Menu(self, tearoff=0, postcommand=lambda: self.llenar_menu(menu, grupo))
        self.llenar_menu(menu, grupo)
        return menu

    def llenar_menu(self, menu: tk.Menu, grupo: str) -> None:
        """Reconstruye las entradas del menu copiando el estado habilitado de los botones."""
        menu.delete(0, "end")
        for nombre, texto, atajo, g in _ACCIONES:
            if g == grupo and nombre in self.botones:
                menu.add_command(label=texto, accelerator=atajo, command=self._acciones[nombre],
                                 state="normal" if self.botones[nombre].habilitado else "disabled")
        if grupo == "archivo" and "salir" in self._acciones:
            menu.add_separator()
            menu.add_command(label="Salir", command=self._acciones["salir"])

    def habilitar(self, nombres: Iterable[str]) -> None:
        """Activa los botones indicados y desactiva el resto."""
        activos = set(nombres)
        for nombre, boton in self.botones.items():
            boton.habilitar(nombre in activos)


class PanelLateral(PanelHerramientas):
    """Tool window izquierda: vista Proyecto (ejemplos) y vista Lenguaje (referencia de config.reglas)."""

    def __init__(self, padre, al_elegir_ejemplo: Callable[[Path], None]) -> None:
        super().__init__(padre)
        self._al_elegir = al_elegir_ejemplo
        self._rutas: dict[str, Path] = {}
        self._descripciones: dict[str, str] = {}
        self._extra: str | None = None
        self._imagenes = {n: iconos.imagen(n, self) for n in ("carpeta", "archivo")}  # Tk las pierde si no se guardan
        self._construir_proyecto()
        self._construir_lenguaje()
        self.agregar_vista("proyecto", "Proyecto", self.vista_proyecto)
        self.agregar_vista("lenguaje", f"Lenguaje {reglas.NOMBRE_LENGUAJE} {reglas.VERSION_LENGUAJE}", self.vista_lenguaje)

    def _construir_proyecto(self) -> None:
        self.vista_proyecto = ttk.Frame(self.cuerpo, style="Panel.TFrame")
        self.lista = ttk.Treeview(self.vista_proyecto, show="tree", selectmode="browse")
        self.lista.pack(fill="both", expand=True, padx=(6, 0))
        self.lista.bind("<Double-1>", self._doble_clic)
        raiz = self.lista.insert("", "end", text=" " + RAIZ_PROYECTO.name, image=self._imagenes["carpeta"], open=True)
        self._raiz = raiz
        carpeta = self.lista.insert(raiz, "end", text=" ejemplos", image=self._imagenes["carpeta"], open=True)
        for ruta in listar_ejemplos():
            iid = self.lista.insert(carpeta, "end", text=" " + ruta.name, image=self._imagenes["archivo"])
            self._rutas[iid] = ruta.resolve()

    def _construir_lenguaje(self) -> None:
        self.vista_lenguaje = ttk.Frame(self.cuerpo, style="Panel.TFrame")
        marco = ttk.Frame(self.vista_lenguaje, style="Panel.TFrame")
        marco.pack(fill="both", expand=True, padx=(6, 0))
        self.arbol = ttk.Treeview(marco, show="tree", selectmode="browse")
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=barra.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.arbol.bind("<<TreeviewSelect>>", self._mostrar_descripcion)
        self.detalle = ttk.Label(self.vista_lenguaje, style="Tenue.TLabel", wraplength=220, justify="left",
                                 padding=(14, 8), text="Seleccione un elemento para ver su descripción.")
        self.detalle.pack(fill="x")
        self._construir_arbol()

    def _doble_clic(self, evento) -> None:
        elegido = self.lista.identify_row(evento.y)
        if elegido in self._rutas:
            self._al_elegir(self._rutas[elegido])

    def marcar_abierto(self, ruta: Path | None) -> None:
        """Selecciona el archivo abierto; si esta fuera de `ejemplos/` lo agrega bajo la raiz."""
        if self._extra is not None:
            self.lista.delete(self._extra)
            self._rutas.pop(self._extra, None)
            self._extra = None
        if ruta is None:
            self.lista.selection_set(())
            return
        ruta = Path(ruta).resolve()
        iid = next((i for i, r in self._rutas.items() if r == ruta), None)
        if iid is None:
            iid = self._extra = self.lista.insert(self._raiz, "end", text=" " + ruta.name, image=self._imagenes["archivo"])
            self._rutas[iid] = ruta
        self.lista.selection_set(iid)
        self.lista.see(iid)

    def _nodo(self, padre: str, texto: str, descripcion: str = "", abierto: bool = False) -> str:
        iid = self.arbol.insert(padre, "end", text=texto, open=abierto)
        if descripcion:
            self._descripciones[iid] = descripcion
        return iid

    def _construir_arbol(self) -> None:
        raiz = self._nodo("", f"Palabras reservadas ({len(reglas.PALABRAS_RESERVADAS)})", abierto=True)
        for palabra, descripcion in reglas.PALABRAS_RESERVADAS.items():
            self._nodo(raiz, palabra, descripcion)
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
    """Registro de la evaluacion con colores por nivel."""

    def __init__(self, padre) -> None:
        super().__init__(padre, style="Panel.TFrame")
        self._id_bajar: str | None = None
        self.texto = tk.Text(self, height=8, wrap="none", state="disabled", font=fuente_codigo(13),
                             background=TEMA["fondo"], foreground=TEMA["texto_codigo"], borderwidth=0,
                             highlightthickness=0, padx=14, pady=6)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.texto.yview)
        self.texto.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.texto.pack(side="left", fill="both", expand=True)
        for nivel, color in (("normal", TEMA["texto_codigo"]), ("error", TEMA["error"]),
                             ("exito", TEMA["exito"]), ("info", TEMA["info"])):
            self.texto.tag_configure(nivel, foreground=color)

    def escribir(self, texto: str, nivel: str = "normal") -> None:
        """Agrega una linea y baja el desplazamiento al final."""
        self.texto.configure(state="normal")
        self.texto.insert("end", texto + "\n", nivel)
        exceso = int(self.texto.index("end-1c").split(".")[0]) - _MAX_LINEAS_CONSOLA
        if exceso > 0:
            self.texto.delete("1.0", f"{exceso + 1}.0")
        self.texto.configure(state="disabled")
        if self._id_bajar is None:
            self._id_bajar = self.after_idle(self._bajar_al_final)

    def _bajar_al_final(self) -> None:
        """Un solo desplazamiento por ciclo de eventos aunque se escriban cientos de lineas (AUD-17)."""
        self._id_bajar = None
        self.texto.see("end")

    def limpiar(self) -> None:
        """Borra todo el registro."""
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.configure(state="disabled")


class BarraEstado(ttk.Frame):
    """Barra gris inferior (zona H): migas, estado, contadores, Lin:Col, LF, UTF-8, lenguaje y enlace."""

    def __init__(self, padre, al_ver_tabla: Callable) -> None:
        super().__init__(padre, style="Estado.TFrame", height=26)
        self.pack_propagate(False)
        self._al_ver_tabla = al_ver_tabla
        self._tabla_habilitada = False
        self._previas = ttk.Label(self, style="Estado.TLabel")
        self._ultima = ttk.Label(self, style="Ruta.TLabel")
        self._estado = ttk.Label(self, style="Estado.TLabel")
        self._contadores = ttk.Label(self, style="Estado.TLabel")
        self._posicion = ttk.Label(self, style="Estado.TLabel")
        self._enlace = ttk.Label(self, text="Ver tabla de símbolos", style="Enlace.TLabel", cursor="hand2")
        self._enlace.bind("<Button-1>", lambda _e: self._al_ver_tabla() if self._tabla_habilitada else None)
        self._enlace.pack(side="right", padx=(16, 12))
        ttk.Label(self, text=f"LF    UTF-8    {reglas.NOMBRE_LENGUAJE} {reglas.VERSION_LENGUAJE}",
                  style="Estado.TLabel").pack(side="right")
        self._posicion.pack(side="right", padx=(0, 16))
        self._previas.pack(side="left", padx=(12, 0))
        self._ultima.pack(side="left")
        self._estado.pack(side="left", padx=(28, 0))
        self._contadores.pack(side="left", padx=(16, 0))
        self.establecer_ruta([RAIZ_PROYECTO.name])
        self.establecer_estado("Listo")
        self.establecer_contadores(0, 0)
        self.establecer_posicion(1, 1)
        self.habilitar_ver_tabla(False)

    def establecer_ruta(self, partes: list[str]) -> None:
        """Migas de pan `a › b › c`; la ultima parte va en el color de texto principal."""
        self._previas.configure(text=" › ".join(partes[:-1]) + " › " if len(partes) > 1 else "")
        self._ultima.configure(text=partes[-1])

    def texto_ruta(self) -> str:
        """Las migas tal como se ven."""
        return str(self._previas.cget("text")) + str(self._ultima.cget("text"))

    def establecer_estado(self, texto: str) -> None:
        """Texto principal de estado."""
        self._estado.configure(text=texto)

    def establecer_contadores(self, tokens: int, errores: int) -> None:
        """Cantidad de tokens y de errores encontrados hasta ahora."""
        self._contadores.configure(text=f"{tokens} tokens  ·  {errores} {'error' if errores == 1 else 'errores'}")

    def establecer_posicion(self, linea: int, columna: int) -> None:
        """Posicion del cursor en formato Lin:Col."""
        self._posicion.configure(text=f"{linea}:{columna}")

    def habilitar_ver_tabla(self, activo: bool) -> None:
        """Activa o desactiva el enlace de la tabla de simbolos."""
        self._tabla_habilitada = activo
        self._enlace.state(["!disabled"] if activo else ["disabled"])
