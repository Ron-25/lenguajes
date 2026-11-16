"""Iconos dibujados en codigo (D-44): trazos para `tk.Canvas` y rectangulos para `tk.PhotoImage`.

Solo datos y dos funciones. Los colores los decide quien llama (salen de `ui.estilos.TEMA`);
aqui solo hay nombres de claves de TEMA para los iconos de los arboles.
"""
from __future__ import annotations

import tkinter as tk

from ui.estilos import TEMA

# nombre -> primitivas en una rejilla de 16x16: (figura, relleno, x1, y1, x2, y2, ...)
# figuras: "linea" (polilinea), "rect", "ovalo", "poligono"
TRAZOS: dict[str, list[tuple]] = {
    "analizar": [("poligono", True, 4, 2, 13, 8, 4, 14)],
    "paso": [("poligono", False, 3, 2, 11, 8, 3, 14), ("linea", False, 13, 2, 13, 14)],
    "detener": [("rect", True, 3, 3, 13, 13)],
    "abrir": [("poligono", False, 2, 3, 6, 3, 8, 5, 13, 5, 13, 13, 2, 13)],
    "guardar": [("rect", False, 2, 2, 14, 14), ("rect", False, 5, 2, 11, 6), ("rect", False, 4, 9, 12, 14)],
    "limpiar": [("linea", False, 3, 4, 13, 4), ("rect", False, 4, 5, 12, 14), ("linea", False, 6, 2, 10, 2),
                ("linea", False, 7, 7, 7, 12), ("linea", False, 9, 7, 9, 12)],
    "ayuda": [("ovalo", False, 2, 2, 14, 14), ("linea", False, 6, 6, 6, 5, 7, 4, 9, 4, 10, 5, 10, 7, 8, 8, 8, 9),
              ("rect", True, 7, 11, 9, 12)],
    "proyecto": [("poligono", False, 2, 3, 6, 3, 8, 5, 14, 5, 14, 13, 2, 13)],
    "lenguaje": [("linea", False, 6, 2, 5, 3, 5, 7, 3, 8, 5, 9, 5, 13, 6, 14),
                 ("linea", False, 10, 2, 11, 3, 11, 7, 13, 8, 11, 9, 11, 13, 10, 14)],
    "consola": [("rect", False, 1, 3, 15, 13), ("linea", False, 4, 6, 7, 8, 4, 10), ("linea", False, 8, 11, 12, 11)],
    "problemas": [("ovalo", False, 2, 2, 14, 14), ("linea", False, 8, 5, 8, 9), ("rect", True, 7, 11, 9, 12)],
    "tokens": [("linea", False, 3, 4, 13, 4), ("linea", False, 3, 8, 13, 8), ("linea", False, 3, 12, 13, 12)],
    "simbolos": [("rect", False, 2, 3, 14, 13), ("linea", False, 2, 8, 14, 8), ("linea", False, 6, 3, 6, 13),
                 ("linea", False, 10, 3, 10, 13)],
    "estadisticas": [("rect", True, 3, 9, 5, 14), ("rect", True, 7, 5, 9, 14), ("rect", True, 11, 2, 13, 14)],
    "educativo": [("ovalo", False, 1, 5, 6, 10), ("ovalo", False, 10, 5, 15, 10), ("linea", False, 6, 8, 10, 8),
                  ("linea", False, 8, 6, 10, 8, 8, 10)],
    "ocultar": [("linea", False, 3, 8, 13, 8)],
}

# nombre -> [(clave de TEMA, x1, y1, x2, y2)] (x2, y2 no incluidos)
RECTANGULOS: dict[str, list[tuple]] = {
    "carpeta": [("texto_secundario", 2, 3, 7, 5), ("texto_secundario", 2, 5, 14, 13)],
    "archivo": [("info", 3, 1, 13, 15), ("panel", 5, 5, 11, 6), ("panel", 5, 8, 11, 9), ("panel", 5, 11, 9, 12)],
}


def dibujar(lienzo: tk.Canvas, nombre: str, x: int, y: int, color: str) -> list[int]:
    """Dibuja el icono `nombre` con su esquina superior izquierda en (x, y); devuelve los ids creados."""
    ids = []
    for figura, relleno, *puntos in TRAZOS[nombre]:
        coords = [c + (x if i % 2 == 0 else y) for i, c in enumerate(puntos)]
        opciones = {"fill": color if relleno else "", "outline": color}
        if figura == "linea":
            ids.append(lienzo.create_line(*coords, fill=color, width=1.5, capstyle="round", joinstyle="round"))
        elif figura == "rect":
            ids.append(lienzo.create_rectangle(*coords, width=1.5, **opciones))
        elif figura == "ovalo":
            ids.append(lienzo.create_oval(*coords, width=1.5, **opciones))
        else:
            ids.append(lienzo.create_polygon(*coords, width=1.5, joinstyle="round", **opciones))
    return ids


def imagen(nombre: str, master: tk.Misc | None = None) -> tk.PhotoImage:
    """`PhotoImage` de 16x16 pintada con rectangulos; quien la pide debe guardar la referencia
    y pasar su widget como `master` (con varias raices de Tk la imagen debe vivir en la suya)."""
    foto = tk.PhotoImage(master=master, width=16, height=16)
    for clave, x1, y1, x2, y2 in RECTANGULOS[nombre]:
        foto.put(TEMA[clave], to=(x1, y1, x2, y2))
    return foto
