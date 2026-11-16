"""Tema oscuro de la interfaz: colores, fuentes y estilos ttk (unico lugar con colores)."""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from core.modelos import TipoToken

TEMA = {
    "fondo": "#1e1e1e",
    "panel": "#252526",
    "barra": "#333333",
    "borde": "#3c3c3c",
    "texto": "#d4d4d4",
    "blanco": "#ffffff",
    "texto_tenue": "#858585",
    "acento": "#007acc",
    "acento_claro": "#1a8ad4",
    "seleccion": "#264f78",
    "error": "#f44747",
    "exito": "#4ec9b0",
    "advertencia": "#cca700",
    "info": "#569cd6",
    "linea_actual": "#2a2d2e",
    "colision": "#3a2f1b",
}

COLORES_TOKEN = {
    TipoToken.PALABRA_RESERVADA: "#569cd6",
    TipoToken.IDENTIFICADOR: "#9cdcfe",
    TipoToken.ENTERO: "#b5cea8",
    TipoToken.DECIMAL: "#b5cea8",
    TipoToken.CADENA: "#ce9178",
    TipoToken.OPERADOR_ARITMETICO: "#d4d4d4",
    TipoToken.OPERADOR_RELACIONAL: "#d4d4d4",
    TipoToken.OPERADOR_LOGICO: "#d4d4d4",
    TipoToken.ASIGNACION: "#d4d4d4",
    TipoToken.DELIMITADOR: "#ffd700",
    TipoToken.COMENTARIO: "#6a9955",
    TipoToken.ERROR: "#f44747",
}

_FUENTES_CODIGO = ("Menlo", "Consolas", "DejaVu Sans Mono", "Courier New")
_FUENTES_INTERFAZ = ("SF Pro Text", "Segoe UI", "Helvetica Neue", "DejaVu Sans", "Arial")


def _primera_disponible(candidatas: tuple[str, ...], por_defecto: str) -> str:
    """Primera familia de `candidatas` instalada; si no hay raiz de Tk, `por_defecto`."""
    try:
        instaladas = set(tkfont.families())
    except (tk.TclError, RuntimeError):
        return por_defecto
    return next((f for f in candidatas if f in instaladas), por_defecto)


def fuente_codigo(tamano: int = 13) -> tuple[str, int]:
    """Fuente monoespaciada: la primera disponible de la lista, con respaldo generico."""
    return (_primera_disponible(_FUENTES_CODIGO, "Courier"), tamano)


def fuente_interfaz(tamano: int = 11) -> tuple[str, int]:
    """Fuente proporcional para la interfaz."""
    return (_primera_disponible(_FUENTES_INTERFAZ, "Helvetica"), tamano)


def aplicar_tema(raiz: tk.Misc) -> None:
    """Configura ttk (tema clam) con la paleta oscura."""
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    base = fuente_interfaz(11)
    negrita = (base[0], 11, "bold")
    raiz.configure(background=TEMA["fondo"])
    estilo.configure(".", background=TEMA["fondo"], foreground=TEMA["texto"], font=base,
                     bordercolor=TEMA["borde"], lightcolor=TEMA["borde"], darkcolor=TEMA["borde"],
                     troughcolor=TEMA["panel"], focuscolor=TEMA["acento"])
    estilo.configure("TFrame", background=TEMA["fondo"])
    estilo.configure("Panel.TFrame", background=TEMA["panel"])
    estilo.configure("Barra.TFrame", background=TEMA["barra"])
    estilo.configure("Estado.TFrame", background=TEMA["acento"])
    estilo.configure("TLabel", background=TEMA["fondo"], foreground=TEMA["texto"])
    estilo.configure("Panel.TLabel", background=TEMA["panel"])
    estilo.configure("Titulo.TLabel", background=TEMA["panel"], foreground=TEMA["texto_tenue"],
                     font=(base[0], 9, "bold"))
    estilo.configure("Tenue.TLabel", background=TEMA["panel"], foreground=TEMA["texto_tenue"])
    estilo.configure("Estado.TLabel", background=TEMA["acento"], foreground="#ffffff", font=(base[0], 10))
    estilo.configure("TButton", background=TEMA["barra"], foreground=TEMA["texto"], padding=(12, 6),
                     borderwidth=0, relief="flat")
    estilo.map("TButton", background=[("disabled", TEMA["barra"]), ("active", TEMA["borde"])],
               foreground=[("disabled", TEMA["texto_tenue"])])
    estilo.configure("Accion.TButton", background=TEMA["acento"], foreground="#ffffff", font=negrita)
    estilo.map("Accion.TButton", background=[("disabled", TEMA["borde"]), ("active", TEMA["acento_claro"])],
               foreground=[("disabled", TEMA["texto_tenue"])])
    estilo.configure("Estado.TButton", background=TEMA["acento_claro"], foreground="#ffffff",
                     padding=(10, 1), font=(base[0], 10))
    estilo.map("Estado.TButton", background=[("disabled", TEMA["acento"]), ("active", TEMA["seleccion"])],
               foreground=[("disabled", "#7fbce6")])
    estilo.configure("Treeview", background=TEMA["panel"], fieldbackground=TEMA["panel"],
                     foreground=TEMA["texto"], rowheight=24, borderwidth=0)
    estilo.map("Treeview", background=[("selected", TEMA["seleccion"])],
               foreground=[("selected", "#ffffff")])
    estilo.configure("Treeview.Heading", background=TEMA["barra"], foreground=TEMA["texto"],
                     relief="flat", padding=(6, 4), font=(base[0], 10, "bold"))
    estilo.map("Treeview.Heading", background=[("active", TEMA["borde"])])
    estilo.configure("TNotebook", background=TEMA["fondo"], borderwidth=0, tabmargins=(0, 0, 0, 0))
    estilo.configure("TNotebook.Tab", background=TEMA["panel"], foreground=TEMA["texto_tenue"],
                     padding=(14, 7), borderwidth=0)
    estilo.map("TNotebook.Tab", background=[("selected", TEMA["fondo"])],
               foreground=[("selected", "#ffffff"), ("disabled", TEMA["borde"])])
    estilo.configure("TPanedwindow", background=TEMA["borde"])
    estilo.configure("Sash", sashthickness=4, background=TEMA["borde"])
    for orientacion in ("Vertical", "Horizontal"):
        estilo.configure(f"{orientacion}.TScrollbar", background=TEMA["barra"], troughcolor=TEMA["panel"],
                         bordercolor=TEMA["panel"], arrowcolor=TEMA["texto_tenue"], relief="flat")
        estilo.map(f"{orientacion}.TScrollbar", background=[("active", TEMA["borde"])])
