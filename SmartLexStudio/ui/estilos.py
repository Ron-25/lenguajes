"""Tema claro: colores, fuentes y estilos ttk. Es el único archivo de la interfaz con colores escritos."""
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from core.modelos import TipoToken

TEMA = {
    "fondo": "#F4F6F9",
    "panel": "#FFFFFF",
    "barra": "#E8ECF2",
    "borde": "#C5CDD8",
    "texto": "#1B2430",
    "texto_codigo": "#1F2937",
    "texto_secundario": "#4B5563",
    "texto_tenue": "#8791A0",
    "numero_linea": "#8791A0",
    "blanco": "#FFFFFF",
    "acento": "#1D5FD1",
    "acento_claro": "#3B7DE9",
    "seleccion": "#CFE0FB",
    "seleccion_fila": "#DCE8FB",
    "linea_actual": "#F1F5FB",
    "deslizador": "#B5BFCC",
    "error": "#C62828",
    "error_fondo": "#FDECEC",
    "error_lexema": "#F8C8C8",
    "exito": "#1E8E3E",
    "advertencia": "#B26A00",
    "info": "#1D5FD1",
    "colision": "#FFF4CC",
    "cabecera": "#14213D",
    "cabecera_tenue": "#A9B6CC",
}

COLORES_TOKEN = {
    TipoToken.PALABRA_RESERVADA: "#0B3FA8",
    TipoToken.IDENTIFICADOR: "#1F2937",
    TipoToken.ENTERO: "#1565C0",
    TipoToken.DECIMAL: "#1565C0",
    TipoToken.DURACION: "#00796B",
    TipoToken.CADENA: "#A14A00",
    TipoToken.OPERADOR_ARITMETICO: "#37474F",
    TipoToken.OPERADOR_RELACIONAL: "#37474F",
    TipoToken.OPERADOR_LOGICO: "#37474F",
    TipoToken.ASIGNACION: "#37474F",
    TipoToken.DELIMITADOR: "#5F6B7A",
    TipoToken.COMENTARIO: "#7A8594",
    TipoToken.ERROR: "#C62828",
}

# Cursiva y negrita no son colores; el editor las aplica a estas categorías.
TIPOS_EN_CURSIVA = (TipoToken.COMENTARIO,)
TIPOS_EN_NEGRITA = (TipoToken.PALABRA_RESERVADA,)

_FUENTES_CODIGO = ("JetBrains Mono", "Menlo", "Consolas", "DejaVu Sans Mono", "Courier New")
_FUENTES_INTERFAZ = ("Inter", "SF Pro Text", "Segoe UI", "Helvetica Neue", "DejaVu Sans", "Arial")


def _puntos(tamano: int) -> int:
    """Tamaño de diseño en píxeles a puntos de Tk: igual en macOS, por 0,75 en el resto."""
    return tamano if sys.platform == "darwin" else round(tamano * 0.75)


def _primera_disponible(candidatas: tuple[str, ...], por_defecto: str) -> str:
    """Primera familia de `candidatas` instalada; `por_defecto` si Tk aún no tiene ventana raíz."""
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
    negrita = (base[0], _puntos(13), "bold")
    estilo.configure(".", background=TEMA["fondo"], foreground=TEMA["texto"], font=base,
                     bordercolor=TEMA["borde"], lightcolor=TEMA["borde"], darkcolor=TEMA["borde"],
                     troughcolor=TEMA["panel"], focuscolor=TEMA["acento"])
    estilo.configure("TFrame", background=TEMA["fondo"])
    estilo.configure("Panel.TFrame", background=TEMA["panel"])
    estilo.configure("Estado.TFrame", background=TEMA["barra"])
    estilo.configure("TLabel", background=TEMA["fondo"], foreground=TEMA["texto"])
    estilo.configure("Panel.TLabel", background=TEMA["panel"])
    estilo.configure("Titulo.TLabel", background=TEMA["fondo"], foreground=TEMA["texto"], font=negrita)
    estilo.configure("TituloError.TLabel", background=TEMA["fondo"], foreground=TEMA["error"], font=negrita)
    estilo.configure("PanelError.TLabel", background=TEMA["panel"], foreground=TEMA["error"], font=negrita)
    estilo.configure("Tenue.TLabel", background=TEMA["panel"], foreground=TEMA["texto_secundario"], font=chica)
    estilo.configure("Estado.TLabel", background=TEMA["barra"], foreground=TEMA["texto_secundario"], font=chica)
    estilo.configure("Veredicto.TLabel", background=TEMA["barra"], foreground=TEMA["texto_secundario"],
                     font=(base[0], _puntos(12), "bold"))
    estilo.configure("TSeparator", background=TEMA["borde"])


def _estilos_cabecera(estilo: ttk.Style, base: tuple[str, int]) -> None:
    """Botones, menú y deslizador de la cabecera azul marino, con opciones que el tema clam admite."""
    boton = (base[0], _puntos(11))
    for nombre, fondo, texto, encima in (("Primario", TEMA["acento"], TEMA["blanco"], TEMA["acento_claro"]),
                                         ("Secundario", TEMA["panel"], TEMA["texto"], TEMA["barra"])):
        estilo.configure(f"{nombre}.TButton", background=fondo, foreground=texto, font=boton, width=0,
                         padding=(7, 4), borderwidth=1, relief="flat", bordercolor=TEMA["blanco"],
                         lightcolor=fondo, darkcolor=fondo, focuscolor=fondo)
        estilo.map(f"{nombre}.TButton", background=[("disabled", TEMA["barra"]), ("active", encima)],
                   foreground=[("disabled", TEMA["texto_tenue"])],
                   bordercolor=[("disabled", TEMA["borde"])])
    estilo.configure("Cabecera.TMenubutton", background=TEMA["panel"], foreground=TEMA["texto"], font=boton,
                     width=0, padding=(7, 4), borderwidth=1, relief="flat", bordercolor=TEMA["blanco"],
                     arrowcolor=TEMA["texto"])
    estilo.map("Cabecera.TMenubutton", background=[("active", TEMA["barra"])])
    estilo.configure("Cabecera.Horizontal.TScale", background=TEMA["cabecera"], troughcolor=TEMA["deslizador"],
                     bordercolor=TEMA["cabecera"], lightcolor=TEMA["blanco"], darkcolor=TEMA["blanco"])


def _estilos_tablas(estilo: ttk.Style, base: tuple[str, int]) -> None:
    """Treeview claro con filas de 24 px y cabecera con borde; pestañas, combobox y divisores."""
    estilo.configure("Treeview", background=TEMA["panel"], fieldbackground=TEMA["panel"],
                     foreground=TEMA["texto"], rowheight=24, borderwidth=0, relief="flat")
    estilo.map("Treeview", background=[("selected", TEMA["seleccion_fila"])],
               foreground=[("selected", TEMA["texto"])])
    estilo.configure("Treeview.Heading", background=TEMA["barra"], foreground=TEMA["texto_secundario"],
                     relief="solid", borderwidth=1, bordercolor=TEMA["borde"], padding=(7, 4),
                     font=(base[0], _puntos(12), "bold"))
    estilo.map("Treeview.Heading", background=[("active", TEMA["barra"])])
    estilo.configure("TNotebook", background=TEMA["fondo"], borderwidth=0, tabmargins=(0, 0, 0, 0))
    estilo.configure("TNotebook.Tab", background=TEMA["barra"], foreground=TEMA["texto_secundario"],
                     padding=(16, 6), borderwidth=1, font=(base[0], _puntos(12)))
    estilo.map("TNotebook.Tab", background=[("selected", TEMA["panel"])],
               foreground=[("selected", TEMA["acento"]), ("disabled", TEMA["texto_tenue"])])
    estilo.configure("TCombobox", fieldbackground=TEMA["panel"], background=TEMA["barra"],
                     foreground=TEMA["texto"], arrowcolor=TEMA["texto_secundario"], padding=4)
    estilo.map("TCombobox", fieldbackground=[("readonly", TEMA["panel"])],
               foreground=[("readonly", TEMA["texto"])], selectbackground=[("readonly", TEMA["panel"])],
               selectforeground=[("readonly", TEMA["texto"])])
    estilo.configure("TPanedwindow", background=TEMA["fondo"])
    estilo.configure("Sash", sashthickness=6, background=TEMA["fondo"], gripcount=0)


def _estilos_barras(estilo: ttk.Style) -> None:
    """Barras de desplazamiento finas y sin flechas; si el tema no lo admite se queda el aspecto base."""
    for orientacion, lado in (("Vertical", "ns"), ("Horizontal", "ew")):
        nombre = f"{orientacion}.TScrollbar"
        estilo.configure(nombre, background=TEMA["deslizador"], troughcolor=TEMA["panel"],
                         bordercolor=TEMA["panel"], lightcolor=TEMA["deslizador"],
                         darkcolor=TEMA["deslizador"], relief="flat", width=10, arrowsize=10)
        estilo.map(nombre, background=[("active", TEMA["texto_tenue"])])
        try:
            estilo.layout(nombre, [(f"{orientacion}.Scrollbar.trough", {"sticky": lado, "children": [
                (f"{orientacion}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
        except tk.TclError:
            pass


def aplicar_tema(raiz: tk.Misc) -> None:
    """Aplica la paleta clara sobre el tema clam de ttk."""
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    raiz.configure(background=TEMA["fondo"])
    base = fuente_interfaz(13)
    _estilos_basicos(estilo, base)
    _estilos_cabecera(estilo, base)
    _estilos_tablas(estilo, base)
    _estilos_barras(estilo)
