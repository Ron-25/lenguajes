"""Editor de codigo: numeracion de lineas, resaltado por tokens y marcas de error."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable

from core.modelos import Diagnostico, TipoDiagnostico, TipoToken, Token
from ui.estilos import COLORES_TOKEN, TEMA, fuente_codigo

RETARDO_CAMBIO_MS = 300


def _normalizar(texto: str) -> str:
    """Convierte \\r\\n y \\r en \\n (D-34): las columnas del lexer deben coincidir con las de Tk."""
    return texto.replace("\r\n", "\n").replace("\r", "\n")


class EditorCodigo(ttk.Frame):
    """Text con margen de numeros; avisa de cambios (con debounce) y del movimiento del cursor."""

    def __init__(self, padre, al_cambiar: Callable[[], None] | None = None,
                 al_mover_cursor: Callable[[int, int], None] | None = None) -> None:
        super().__init__(padre)
        self._al_cambiar = al_cambiar
        self._al_mover_cursor = al_mover_cursor
        self._id_cambio: str | None = None
        self._silencio = False
        self._lineas_marcadas: set[int] = set()
        fuente = fuente_codigo(13)

        self.margen = tk.Text(self, width=6, padx=6, pady=8, takefocus=0, cursor="arrow", wrap="none",
                              font=fuente, background=TEMA["panel"], foreground=TEMA["texto_tenue"],
                              borderwidth=0, highlightthickness=0, state="disabled")
        self.margen.tag_configure("marca", foreground=TEMA["error"])
        self.margen.tag_configure("derecha", justify="right")
        self.texto = tk.Text(self, wrap="none", undo=True, padx=8, pady=8, font=fuente,
                             background=TEMA["fondo"], foreground=TEMA["texto"],
                             insertbackground=TEMA["blanco"], selectbackground=TEMA["seleccion"],
                             inactiveselectbackground=TEMA["seleccion"], borderwidth=0,
                             highlightthickness=0, tabs=("4c",))
        self._barra_v = ttk.Scrollbar(self, orient="vertical", command=self._desplazar_ambos)
        self._barra_h = ttk.Scrollbar(self, orient="horizontal", command=self.texto.xview)
        self.texto.configure(yscrollcommand=self._al_desplazar, xscrollcommand=self._barra_h.set)
        self.margen.grid(row=0, column=0, sticky="ns")
        self.texto.grid(row=0, column=1, sticky="nsew")
        self._barra_v.grid(row=0, column=2, sticky="ns")
        self._barra_h.grid(row=1, column=1, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self._configurar_etiquetas()
        self.texto.bind("<<Modified>>", self._al_modificar)
        for evento in ("<KeyRelease>", "<ButtonRelease-1>"):
            self.texto.bind(evento, self._cursor_movido, add="+")
        self.margen.bind("<MouseWheel>", lambda e: self.texto.event_generate("<MouseWheel>", delta=e.delta))
        self._refrescar_margen()

    # --- configuracion -------------------------------------------------
    def _configurar_etiquetas(self) -> None:
        self.texto.tag_configure("linea_actual", background=TEMA["linea_actual"])
        for tipo, color in COLORES_TOKEN.items():
            self.texto.tag_configure(self._etiqueta(tipo), foreground=color)
        if self._admite_underlinefg():
            self.texto.tag_configure("marca_error", underline=True, underlinefg=TEMA["error"])
        else:
            self.texto.tag_configure("marca_error", underline=True)
        self.texto.tag_configure("actual", background=TEMA["seleccion"])
        self.texto.tag_lower("linea_actual")
        self.texto.tag_raise("sel")

    def _admite_underlinefg(self) -> bool:
        try:
            self.texto.tag_configure("_prueba", underlinefg=TEMA["error"])
            self.texto.tag_delete("_prueba")
            return True
        except tk.TclError:
            return False

    @staticmethod
    def _etiqueta(tipo: TipoToken) -> str:
        return f"tok_{tipo.name}"

    # --- texto -----------------------------------------------------------
    def obtener_texto(self) -> str:
        """Contenido sin el salto final de Tk y con saltos normalizados."""
        return _normalizar(self.texto.get("1.0", "end-1c"))

    def establecer_texto(self, texto: str) -> None:
        """Reemplaza todo el contenido (sin disparar al_cambiar)."""
        estado = str(self.texto.cget("state"))
        self._silencio = True
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", _normalizar(texto))
        self.texto.edit_reset()
        self.texto.edit_modified(False)
        self.texto.configure(state=estado)
        self._silencio = False
        self.limpiar_marcas()
        self._refrescar_margen()
        self._marcar_linea_actual()

    def limpiar(self) -> None:
        """Vacia el editor."""
        self.establecer_texto("")

    def solo_lectura(self, activo: bool) -> None:
        """Bloquea o libera la edicion."""
        self.texto.configure(state="disabled" if activo else "normal")

    # --- resaltado y marcas ----------------------------------------------
    def resaltar(self, tokens: Iterable[Token]) -> None:
        """Colorea cada token segun su categoria."""
        for tipo in TipoToken:
            self.texto.tag_remove(self._etiqueta(tipo), "1.0", "end")
        for token in tokens:
            inicio = f"{token.linea}.{token.columna - 1}"
            self.texto.tag_add(self._etiqueta(token.tipo), inicio, f"{inicio}+{token.longitud}c")

    def marcar_errores(self, diagnosticos: Iterable[Diagnostico]) -> None:
        """Subraya el lexema de cada diagnostico con posicion y marca la linea lexica con X."""
        for d in diagnosticos:
            if d.linea <= 0:
                continue
            if d.lexema:
                inicio = f"{d.linea}.{d.columna - 1}"
                self.texto.tag_add("marca_error", inicio, f"{inicio}+{len(d.lexema)}c")
            if d.tipo == TipoDiagnostico.LEXICO:
                self._lineas_marcadas.add(d.linea)
        self._refrescar_margen()

    def limpiar_marcas(self) -> None:
        """Quita subrayados, marcas del margen y token actual."""
        self.texto.tag_remove("marca_error", "1.0", "end")
        self.texto.tag_remove("actual", "1.0", "end")
        self._lineas_marcadas.clear()
        self._refrescar_margen()

    def resaltar_token_actual(self, token: Token | None) -> None:
        """Resalta el token indicado y lo hace visible; None quita el resaltado."""
        self.texto.tag_remove("actual", "1.0", "end")
        if token is None:
            return
        inicio = f"{token.linea}.{token.columna - 1}"
        self.texto.tag_add("actual", inicio, f"{inicio}+{token.longitud}c")
        self.texto.see(inicio)

    def ir_a(self, linea: int, columna: int) -> None:
        """Lleva el cursor a (linea, columna) desde 1 y da el foco al editor."""
        self.texto.mark_set("insert", f"{linea}.{columna - 1}")
        self.texto.see("insert")
        self.texto.focus_set()
        self._cursor_movido()

    def posicion_cursor(self) -> tuple[int, int]:
        """(linea, columna) del cursor, ambas desde 1."""
        linea, columna = self.texto.index("insert").split(".")
        return int(linea), int(columna) + 1

    # --- margen y eventos --------------------------------------------------
    def _refrescar_margen(self) -> None:
        total = int(self.texto.index("end-1c").split(".")[0])
        filas = [f"{'✗ ' if n in self._lineas_marcadas else '  '}{n}" for n in range(1, total + 1)]
        self.margen.configure(state="normal", width=max(5, len(str(total)) + 3))
        self.margen.delete("1.0", "end")
        self.margen.insert("1.0", "\n".join(filas), "derecha")
        for n in self._lineas_marcadas:
            if n <= total:
                self.margen.tag_add("marca", f"{n}.0", f"{n}.1")
        self.margen.configure(state="disabled")
        self.margen.yview_moveto(self.texto.yview()[0])

    def _desplazar_ambos(self, *argumentos) -> None:
        self.texto.yview(*argumentos)

    def _al_desplazar(self, primero: str, ultimo: str) -> None:
        self._barra_v.set(primero, ultimo)
        self.margen.yview_moveto(primero)

    def _al_modificar(self, _evento=None) -> None:
        if not self.texto.edit_modified():
            return
        self.texto.edit_modified(False)
        if self._silencio:
            return
        self._refrescar_margen()
        if self._id_cambio is not None:
            self.after_cancel(self._id_cambio)
        self._id_cambio = self.after(RETARDO_CAMBIO_MS, self._notificar_cambio)

    def _notificar_cambio(self) -> None:
        self._id_cambio = None
        if self._al_cambiar is not None:
            self._al_cambiar()

    def _marcar_linea_actual(self) -> None:
        self.texto.tag_remove("linea_actual", "1.0", "end")
        linea = self.texto.index("insert").split(".")[0]
        self.texto.tag_add("linea_actual", f"{linea}.0", f"{int(linea) + 1}.0")

    def _cursor_movido(self, _evento=None) -> None:
        self._marcar_linea_actual()
        if self._al_mover_cursor is not None:
            self._al_mover_cursor(*self.posicion_cursor())
