"""Tema oscuro estilo PyCharm (New UI): colores, fuentes y estilos ttk (unico lugar con colores)."""
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from core.modelos import TipoToken

TEMA = {
    "fondo": "#1E1F22",
    "panel": "#2B2D30",
    "barra": "#2B2D30",
    "borde": "#393B40",
    "texto": "#DFE1E5",
    "texto_codigo": "#BCBEC4",
    "texto_secundario": "#9DA0A8",
    "texto_tenue": "#6F737A",
    "numero_linea": "#4B5059",
    "blanco": "#FFFFFF",
    "acento": "#3574F0",
    "acento_claro": "#548AF7",
    "seleccion": "#214283",
    "seleccion_fila": "#2E436E",
    "activo": "#43454A",
    "deslizador": "#4D4E51",
    "linea_actual": "#26282E",
    "error": "#F75464",
    "exito": "#5FB865",
    "detener": "#DB5C5C",
    "advertencia": "#F2C55C",
    "info": "#56A8F5",
    "colision": "#3D3223",
    "ayuda_fondo": "#393B40",
}

COLORES_TOKEN = {
    TipoToken.PALABRA_RESERVADA: "#CF8E6D",
    TipoToken.IDENTIFICADOR: "#BCBEC4",
    TipoToken.ENTERO: "#2AACB8",
    TipoToken.DECIMAL: "#2AACB8",
    TipoToken.CADENA: "#6AAB73",
    TipoToken.OPERADOR_ARITMETICO: "#BCBEC4",
    TipoToken.OPERADOR_RELACIONAL: "#BCBEC4",
    TipoToken.OPERADOR_LOGICO: "#BCBEC4",
    TipoToken.ASIGNACION: "#BCBEC4",
    TipoToken.DELIMITADOR: "#BCBEC4",
    TipoToken.COMENTARIO: "#7A7E85",
    TipoToken.ERROR: "#F75464",
}

# La cursiva no es un color: el editor la aplica a estas categorias.
TIPOS_EN_CURSIVA = (TipoToken.COMENTARIO,)

_FUENTES_CODIGO = ("JetBrains Mono", "Menlo", "Consolas", "DejaVu Sans Mono", "Courier New")
_FUENTES_INTERFAZ = ("Inter", "SF Pro Text", "Segoe UI", "Helvetica Neue", "DejaVu Sans", "Arial")


def _puntos(tamano: int) -> int:
    """Tamano de diseno (pixeles de PyCharm) a puntos de Tk: igual en macOS, x0,75 en el resto (D-51)."""
    return tamano if sys.platform == "darwin" else round(tamano * 0.75)


def _primera_disponible(candidatas: tuple[str, ...], por_defecto: str) -> str:
    """Primera familia de `candidatas` instalada; si no hay raiz de Tk, `por_defecto`."""
    try:
        instaladas = set(tkfont.families())
    except (tk.TclError, RuntimeError):
        return por_defecto
    return next((f for f in candidatas if f in instaladas), por_defecto)


def fuente_codigo(tamano: int = 13) -> tuple[str, int]:
    """Fuente monoespaciada: la primera disponible de la lista, con respaldo generico."""
    return (_primera_disponible(_FUENTES_CODIGO, "Courier"), _puntos(tamano))


def fuente_interfaz(tamano: int = 13) -> tuple[str, int]:
    """Fuente proporcional para la interfaz."""
    return (_primera_disponible(_FUENTES_INTERFAZ, "Helvetica"), _puntos(tamano))


def _estilos_basicos(estilo: ttk.Style, base: tuple[str, int]) -> None:
    """Marcos, etiquetas y barra de estado."""
    chica = (base[0], _puntos(12))
    estilo.configure(".", background=TEMA["fondo"], foreground=TEMA["texto"], font=base,
                     bordercolor=TEMA["borde"], lightcolor=TEMA["borde"], darkcolor=TEMA["borde"],
                     troughcolor=TEMA["panel"], focuscolor=TEMA["acento"])
    estilo.configure("TFrame", background=TEMA["fondo"])
    estilo.configure("Panel.TFrame", background=TEMA["panel"])
    estilo.configure("Barra.TFrame", background=TEMA["barra"])
    estilo.configure("Estado.TFrame", background=TEMA["panel"])
    estilo.configure("TLabel", background=TEMA["fondo"], foreground=TEMA["texto"])
    estilo.configure("Panel.TLabel", background=TEMA["panel"])
    estilo.configure("Cabecera.TLabel", background=TEMA["panel"], foreground=TEMA["texto_secundario"],
                     font=(base[0], _puntos(12), "bold"))
    estilo.configure("Tenue.TLabel", background=TEMA["panel"], foreground=TEMA["texto_tenue"], font=chica)
    estilo.configure("Estado.TLabel", background=TEMA["panel"], foreground=TEMA["texto_secundario"], font=chica)
    estilo.configure("Ruta.TLabel", background=TEMA["panel"], foreground=TEMA["texto"], font=chica)
    estilo.configure("Enlace.TLabel", background=TEMA["panel"], foreground=TEMA["acento_claro"], font=chica)
    estilo.map("Enlace.TLabel", foreground=[("disabled", TEMA["texto_tenue"])])
    estilo.configure("TSeparator", background=TEMA["borde"])


def _estilos_tablas(estilo: ttk.Style, base: tuple[str, int]) -> None:
    """Treeview plano, filas altas, cabecera discreta, divisores."""
    estilo.configure("Treeview", background=TEMA["panel"], fieldbackground=TEMA["panel"],
                     foreground=TEMA["texto"], rowheight=28, borderwidth=0, relief="flat")
    estilo.map("Treeview", background=[("selected", TEMA["seleccion_fila"])],
               foreground=[("selected", TEMA["blanco"])])
    estilo.configure("Treeview.Heading", background=TEMA["panel"], foreground=TEMA["texto_secundario"],
                     relief="flat", borderwidth=0, padding=(8, 6), font=(base[0], _puntos(12)))
    estilo.map("Treeview.Heading", background=[("active", TEMA["panel"])])
    try:
        estilo.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    except tk.TclError:
        pass
    estilo.configure("TPanedwindow", background=TEMA["fondo"])
    estilo.configure("Sash", sashthickness=3, background=TEMA["fondo"])


def _estilos_barras(estilo: ttk.Style) -> None:
    """Barras de desplazamiento finas y sin flechas; si el tema no lo admite, queda el aspecto base."""
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
    """Configura ttk (tema clam) con la paleta oscura de PyCharm."""
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    raiz.configure(background=TEMA["fondo"])
    base = fuente_interfaz(13)
    _estilos_basicos(estilo, base)
    _estilos_tablas(estilo, base)
    _estilos_barras(estilo)
