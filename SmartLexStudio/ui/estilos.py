"""Tema oscuro al estilo de VS Code (Dark Modern): colores, fuentes y estilos ttk.

Es el único archivo de la interfaz con colores escritos.
"""
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from core.modelos import TipoToken

TEMA = {
    "fondo": "#1F1F1F",            # editor
    "panel": "#181818",            # barra lateral, panel inferior, manejador de errores
    "barra": "#181818",            # barra de título, pestañas inactivas, barra de estado
    "borde": "#2B2B2B",
    "texto": "#CCCCCC",
    "texto_codigo": "#CCCCCC",
    "texto_secundario": "#9D9D9D",
    "texto_tenue": "#6E7681",
    "numero_linea": "#6E7681",
    "numero_linea_activo": "#CCCCCC",
    "blanco": "#FFFFFF",
    "acento": "#0078D4",
    "acento_claro": "#026EC1",
    "seleccion": "#264F78",
    "seleccion_fila": "#04395E",
    "linea_actual": "#282828",
    "encima": "#2A2D2E",           # fila o elemento bajo el ratón
    "deslizador": "#424242",
    "entrada": "#313131",
    "borde_entrada": "#3C3C3C",
    "boton_secundario": "#313131",
    "boton_secundario_encima": "#3C3C3C",
    "actividad_tenue": "#868686",
    "error": "#F85149",
    "error_fondo": "#332020",
    "error_lexema": "#5C2626",
    "exito": "#89D185",
    "advertencia": "#CCA700",
    "info": "#3794FF",
    "colision": "#3D3A1A",
    "cabecera": "#181818",
    "cabecera_tenue": "#9D9D9D",
}

# Colores de Dark+ / Dark Modern para cada categoría.
COLORES_TOKEN = {
    TipoToken.PALABRA_RESERVADA: "#569CD6",
    TipoToken.IDENTIFICADOR: "#9CDCFE",
    TipoToken.ENTERO: "#B5CEA8",
    TipoToken.DECIMAL: "#B5CEA8",
    TipoToken.DURACION: "#4EC9B0",
    TipoToken.CADENA: "#CE9178",
    TipoToken.OPERADOR_ARITMETICO: "#D4D4D4",
    TipoToken.OPERADOR_RELACIONAL: "#D4D4D4",
    TipoToken.OPERADOR_LOGICO: "#D4D4D4",
    TipoToken.ASIGNACION: "#D4D4D4",
    TipoToken.DELIMITADOR: "#FFD700",
    TipoToken.COMENTARIO: "#6A9955",
    TipoToken.ERROR: "#F44747",
}

# Cursiva y negrita no son colores; el editor las aplica a estas categorías.
TIPOS_EN_CURSIVA = (TipoToken.COMENTARIO,)
TIPOS_EN_NEGRITA = (TipoToken.PALABRA_RESERVADA,)

_FUENTES_CODIGO = ("Menlo", "Consolas", "JetBrains Mono", "DejaVu Sans Mono", "Courier New")
_FUENTES_INTERFAZ = ("SF Pro Text", "Segoe UI", "Inter", "Helvetica Neue", "DejaVu Sans", "Arial")


def _puntos(tamano: int) -> int:
    """Tamaño de diseño en píxeles a puntos de Tk: igual en macOS, por 0,75 en el resto."""
    return tamano if sys.platform == "darwin" else round(tamano * 0.75)


def _primera_disponible(candidatas: tuple[str, ...], por_defecto: str) -> str:
    """Primera familia de `candidatas` instalada; `por_defecto` si no hay ninguna o Tk aún no tiene ventana raíz."""
    try:
        instaladas = set(tkfont.families())
    except (tk.TclError, RuntimeError):
        return por_defecto
    return next((f for f in candidatas if f in instaladas), por_defecto)


def fuente_codigo(tamano: int = 13) -> tuple[str, int]:
    """Fuente monoespaciada: la primera disponible de la lista."""
    return (_primera_disponible(_FUENTES_CODIGO, "Courier"), _puntos(tamano))


def fuente_interfaz(tamano: int = 13) -> tuple[str, int]:
    """Fuente proporcional de la interfaz."""
    return (_primera_disponible(_FUENTES_INTERFAZ, "Helvetica"), _puntos(tamano))


def _estilos_basicos(estilo: ttk.Style, base: tuple[str, int]) -> None:
    """Marcos, etiquetas, barra de estado y veredicto."""
    chica = (base[0], _puntos(12))
    seccion = (base[0], _puntos(11), "bold")
    estilo.configure(".", background=TEMA["fondo"], foreground=TEMA["texto"], font=base,
                     bordercolor=TEMA["borde"], lightcolor=TEMA["borde"], darkcolor=TEMA["borde"],
                     troughcolor=TEMA["panel"], focuscolor=TEMA["acento"], selectbackground=TEMA["seleccion"],
                     selectforeground=TEMA["blanco"], insertcolor=TEMA["texto"])
    estilo.configure("TFrame", background=TEMA["fondo"])
    estilo.configure("Panel.TFrame", background=TEMA["panel"])
    estilo.configure("Estado.TFrame", background=TEMA["barra"])
    estilo.configure("Depurando.TFrame", background=TEMA["acento"])
    estilo.configure("TLabel", background=TEMA["fondo"], foreground=TEMA["texto"])
    estilo.configure("Panel.TLabel", background=TEMA["panel"], foreground=TEMA["texto"])
    # títulos de sección como los de VS Code: pequeños, en negrita y apagados
    estilo.configure("Titulo.TLabel", background=TEMA["panel"], foreground=TEMA["texto_secundario"], font=seccion)
    estilo.configure("TituloError.TLabel", background=TEMA["panel"], foreground=TEMA["error"], font=seccion)
    estilo.configure("PanelError.TLabel", background=TEMA["panel"], foreground=TEMA["error"],
                     font=(base[0], _puntos(13), "bold"))
    estilo.configure("Tenue.TLabel", background=TEMA["panel"], foreground=TEMA["texto_secundario"], font=chica)
    estilo.configure("Estado.TLabel", background=TEMA["barra"], foreground=TEMA["texto"], font=chica)
    estilo.configure("Depurando.TLabel", background=TEMA["acento"], foreground=TEMA["blanco"], font=chica)
    estilo.configure("Marca.TLabel", background=TEMA["acento"], foreground=TEMA["blanco"], font=chica)
    estilo.configure("Veredicto.TLabel", background=TEMA["barra"], foreground=TEMA["texto"],
                     font=(base[0], _puntos(12), "bold"))
    estilo.configure("TSeparator", background=TEMA["borde"])


def _estilos_cabecera(estilo: ttk.Style, base: tuple[str, int]) -> None:
    """Botones de la barra de título: de menú (planos), primario azul y secundarios grises."""
    boton = (base[0], _puntos(12))
    for nombre, fondo, texto, encima in (
            ("Primario", TEMA["acento"], TEMA["blanco"], TEMA["acento_claro"]),
            ("Secundario", TEMA["boton_secundario"], TEMA["texto"], TEMA["boton_secundario_encima"]),
            ("Menu", TEMA["cabecera"], TEMA["texto"], TEMA["boton_secundario_encima"])):
        estilo.configure(f"{nombre}.TButton", background=fondo, foreground=texto, font=boton, width=0,
                         padding=(7, 2) if nombre != "Menu" else (5, 2), borderwidth=0, relief="flat",
                         bordercolor=fondo, lightcolor=fondo, darkcolor=fondo, focuscolor=fondo,
                         focusthickness=0)
        estilo.map(f"{nombre}.TButton",
                   background=[("disabled", fondo if nombre == "Menu" else TEMA["boton_secundario"]),
                               ("pressed", encima), ("active", encima)],
                   foreground=[("disabled", TEMA["texto_tenue"])],
                   bordercolor=[("active", encima)], lightcolor=[("active", encima)],
                   darkcolor=[("active", encima)])
    estilo.configure("Cabecera.TMenubutton", background=TEMA["cabecera"], foreground=TEMA["texto"], font=boton,
                     width=0, padding=(5, 2), borderwidth=0, relief="flat", bordercolor=TEMA["cabecera"],
                     lightcolor=TEMA["cabecera"], darkcolor=TEMA["cabecera"], arrowcolor=TEMA["texto_secundario"],
                     arrowsize=0)
    estilo.map("Cabecera.TMenubutton", background=[("active", TEMA["boton_secundario_encima"])])
    estilo.configure("Cabecera.Horizontal.TScale", background=TEMA["texto_secundario"],
                     troughcolor=TEMA["borde_entrada"], bordercolor=TEMA["cabecera"],
                     lightcolor=TEMA["texto_secundario"], darkcolor=TEMA["texto_secundario"], sliderthickness=12,
                     troughrelief="flat", sliderrelief="flat")
    estilo.map("Cabecera.Horizontal.TScale", background=[("active", TEMA["texto"])])


def _estilos_tablas(estilo: ttk.Style, base: tuple[str, int]) -> None:
    """Listas oscuras con filas de 22 px, pestañas del panel inferior, combobox y divisores finos."""
    estilo.configure("Treeview", background=TEMA["panel"], fieldbackground=TEMA["panel"],
                     foreground=TEMA["texto"], rowheight=22, borderwidth=0, relief="flat",
                     bordercolor=TEMA["panel"], lightcolor=TEMA["panel"], darkcolor=TEMA["panel"])
    estilo.map("Treeview", background=[("selected", TEMA["seleccion_fila"])],
               foreground=[("selected", TEMA["blanco"])])
    estilo.configure("Treeview.Heading", background=TEMA["panel"], foreground=TEMA["texto_secundario"],
                     relief="flat", borderwidth=0, bordercolor=TEMA["borde"], lightcolor=TEMA["panel"],
                     darkcolor=TEMA["borde"], padding=(8, 4), font=(base[0], _puntos(11), "bold"))
    estilo.map("Treeview.Heading", background=[("active", TEMA["encima"])])
    estilo.configure("Treeitem.indicator", foreground=TEMA["texto_secundario"])
    estilo.configure("Explorador.Treeview", rowheight=22, indent=12)
    # pestañas del panel inferior: sin caja; la elegida en blanco, el resto apagadas
    estilo.configure("TNotebook", background=TEMA["panel"], borderwidth=0, tabmargins=(8, 4, 0, 0),
                     bordercolor=TEMA["panel"], lightcolor=TEMA["panel"], darkcolor=TEMA["panel"])
    estilo.configure("TNotebook.Tab", background=TEMA["panel"], foreground=TEMA["texto_secundario"],
                     padding=(10, 5), borderwidth=0, bordercolor=TEMA["panel"], lightcolor=TEMA["panel"],
                     darkcolor=TEMA["panel"], focuscolor=TEMA["panel"], font=(base[0], _puntos(11)))
    estilo.map("TNotebook.Tab", background=[("selected", TEMA["panel"]), ("active", TEMA["panel"])],
               foreground=[("selected", TEMA["blanco"]), ("disabled", TEMA["borde_entrada"]),
                           ("active", TEMA["texto"])],
               bordercolor=[("selected", TEMA["panel"]), ("!selected", TEMA["panel"])],
               lightcolor=[("selected", TEMA["panel"]), ("!selected", TEMA["panel"])],
               darkcolor=[("selected", TEMA["panel"]), ("!selected", TEMA["panel"])],
               expand=[("selected", (0, 0, 0, 0))])
    estilo.configure("TCombobox", fieldbackground=TEMA["entrada"], background=TEMA["entrada"],
                     foreground=TEMA["texto"], arrowcolor=TEMA["texto_secundario"], padding=4,
                     bordercolor=TEMA["borde_entrada"], lightcolor=TEMA["entrada"], darkcolor=TEMA["entrada"])
    estilo.map("TCombobox", fieldbackground=[("readonly", TEMA["entrada"])],
               foreground=[("readonly", TEMA["texto"])], selectbackground=[("readonly", TEMA["entrada"])],
               selectforeground=[("readonly", TEMA["texto"])], bordercolor=[("focus", TEMA["acento"])])
    estilo.configure("TPanedwindow", background=TEMA["borde"])
    estilo.configure("Sash", sashthickness=1, background=TEMA["borde"], gripcount=0,
                     lightcolor=TEMA["borde"], darkcolor=TEMA["borde"], bordercolor=TEMA["borde"])


def _estilos_barras(estilo: ttk.Style) -> None:
    """Barras de desplazamiento finas y sin flechas; si el tema no lo admite se queda el aspecto base."""
    for orientacion, lado in (("Vertical", "ns"), ("Horizontal", "ew")):
        nombre = f"{orientacion}.TScrollbar"
        estilo.configure(nombre, background=TEMA["deslizador"], troughcolor=TEMA["fondo"],
                         bordercolor=TEMA["fondo"], lightcolor=TEMA["deslizador"],
                         darkcolor=TEMA["deslizador"], relief="flat", width=10, arrowsize=10)
        estilo.map(nombre, background=[("active", TEMA["actividad_tenue"])])
        try:
            estilo.layout(nombre, [(f"{orientacion}.Scrollbar.trough", {"sticky": lado, "children": [
                (f"{orientacion}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
        except tk.TclError:
            pass


def _opciones_tk(raiz: tk.Misc) -> None:
    """Colores de los widgets clásicos que ttk no cubre: lista del combobox y menús."""
    for patron, valor in (("*TCombobox*Listbox.background", TEMA["entrada"]),
                          ("*TCombobox*Listbox.foreground", TEMA["texto"]),
                          ("*TCombobox*Listbox.selectBackground", TEMA["seleccion_fila"]),
                          ("*TCombobox*Listbox.selectForeground", TEMA["blanco"]),
                          ("*Menu.background", TEMA["entrada"]), ("*Menu.foreground", TEMA["texto"]),
                          ("*Menu.activeBackground", TEMA["acento"]), ("*Menu.activeForeground", TEMA["blanco"])):
        raiz.option_add(patron, valor)


def aplicar_tema(raiz: tk.Misc) -> None:
    """Aplica la paleta oscura sobre el tema clam de ttk."""
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    raiz.configure(background=TEMA["fondo"])
    base = fuente_interfaz(13)
    _opciones_tk(raiz)
    _estilos_basicos(estilo, base)
    _estilos_cabecera(estilo, base)
    _estilos_tablas(estilo, base)
    _estilos_barras(estilo)
