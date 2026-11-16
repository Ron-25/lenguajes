"""Editor de código: título, margen con número de línea y ✓/✗, color por categoría y marcas de error."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable

from core.modelos import Diagnostico, TipoToken, Token
from ui.estilos import COLORES_TOKEN, TEMA, TIPOS_EN_CURSIVA, TIPOS_EN_NEGRITA, fuente_codigo

RETARDO_CAMBIO_MS = 300


def _normalizar(texto: str) -> str:
    """Convierte \\r\\n y \\r en \\n: Tk cuenta un solo carácter por salto y las columnas del lexer deben coincidir."""
    return texto.replace("\r\n", "\n").replace("\r", "\n")


class EditorCodigo(ttk.Frame):
    """Text con un margen `número marca` al lado; avisa de los cambios (con espera) y del movimiento del cursor."""

    def __init__(self, padre, al_cambiar: Callable[[], None] | None = None,
                 al_mover_cursor: Callable[[int, int], None] | None = None) -> None:
        super().__init__(padre)
        self._al_cambiar = al_cambiar
        self._marcas: list[tuple[int, int]] = []
        self._al_mover_cursor = al_mover_cursor
        self._id_cambio: str | None = None
        self._silencio = False
        self._id_ver: str | None = None
        self._lineas_evaluadas: set[int] = set()
        self._lineas_error: set[int] = set()
        fuente = fuente_codigo(13)

        self._titulo = ttk.Label(self, style="Titulo.TLabel")
        self._titulo.grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.establecer_nombre(None)
        marco = tk.Frame(self, background=TEMA["panel"], highlightthickness=1, highlightbackground=TEMA["borde"],
                         highlightcolor=TEMA["borde"])
        marco.grid(row=1, column=0, sticky="nsew")
        self.margen = tk.Text(marco, width=7, padx=6, pady=8, takefocus=0, cursor="arrow", wrap="none",
                              font=fuente, background=TEMA["panel"], foreground=TEMA["numero_linea"],
                              borderwidth=0, highlightthickness=0, state="disabled")
        self.margen.tag_configure("derecha", justify="right")
        self.margen.tag_configure("marca_error", foreground=TEMA["error"])
        self.margen.tag_configure("marca_ok", foreground=TEMA["exito"])
        self.texto = tk.Text(marco, wrap="none", undo=True, padx=8, pady=8, font=fuente,
                             background=TEMA["panel"], foreground=TEMA["texto_codigo"],
                             insertbackground=TEMA["texto"], selectbackground=TEMA["seleccion"],
                             inactiveselectbackground=TEMA["seleccion"], borderwidth=0,
                             highlightthickness=0, tabs=("4c",))
        self._barra_v = ttk.Scrollbar(marco, orient="vertical", command=self._desplazar_ambos)
        self._barra_h = ttk.Scrollbar(marco, orient="horizontal", command=self.texto.xview)
        self.texto.configure(yscrollcommand=self._al_desplazar, xscrollcommand=self._barra_h.set)
        self.margen.grid(row=0, column=0, sticky="ns")
        tk.Frame(marco, width=1, background=TEMA["borde"]).grid(row=0, column=1, sticky="ns")
        self.texto.grid(row=0, column=2, sticky="nsew")
        self._barra_v.grid(row=0, column=3, sticky="ns")
        self._barra_h.grid(row=1, column=2, sticky="ew")
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self._configurar_etiquetas()
        self.texto.bind("<<Modified>>", self._al_modificar)
        for evento in ("<KeyRelease>", "<ButtonRelease-1>"):
            self.texto.bind(evento, self._cursor_movido, add="+")
        self.margen.bind("<MouseWheel>", lambda e: self.texto.event_generate("<MouseWheel>", delta=e.delta))
        self._refrescar_margen()

    def establecer_nombre(self, nombre: str | None) -> None:
        """Título «Archivo de entrada: nombre», o «(sin archivo)»."""
        self._titulo.configure(text=f"Archivo de entrada: {nombre or '(sin archivo)'}")

    def ir_a_error(self, direccion: int) -> None:
        """Salta a la marca de error siguiente (+1) o anterior (-1), dando la vuelta al llegar al final."""
        marcas = sorted(set(self._marcas))
        if not marcas:
            return
        actual = self.posicion_cursor()
        if direccion > 0:
            destino = next((m for m in marcas if m > actual), marcas[0])
        else:
            destino = next((m for m in reversed(marcas) if m < actual), marcas[-1])
        self.ir_a(*destino)

    def _configurar_etiquetas(self) -> None:
        """Las etiquetas de Tk se pisan por orden de creación: línea actual, línea con error, categorías, lexema con error, token actual y selección."""
        self.texto.tag_configure("linea_actual", background=TEMA["linea_actual"])
        self.texto.tag_configure("linea_error", background=TEMA["error_fondo"])
        base = fuente_codigo(13)
        for tipo, color in COLORES_TOKEN.items():
            fuente = base + ("italic",) if tipo in TIPOS_EN_CURSIVA else base + ("bold",) if tipo in TIPOS_EN_NEGRITA else base
            self.texto.tag_configure(self._etiqueta(tipo), foreground=color, font=fuente)
        self.texto.tag_configure("marca_error", underline=True, background=TEMA["error_lexema"])
        if self._admite_underlinefg():
            self.texto.tag_configure("marca_error", underlinefg=TEMA["error"])
        self.texto.tag_configure("actual", background=TEMA["seleccion"])
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

    def obtener_texto(self) -> str:
        """Texto sin el salto final que Tk agrega siempre."""
        return _normalizar(self.texto.get("1.0", "end-1c"))

    def establecer_texto(self, texto: str) -> None:
        """Reemplaza el contenido sin avisar de un cambio."""
        estado = str(self.texto.cget("state"))
        self.descartar_cambio_pendiente()
        self._silencio = True
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", _normalizar(texto))
        self.texto.mark_set("insert", "1.0")
        self.texto.see("1.0")
        self.texto.edit_reset()
        self.texto.edit_modified(False)
        self.texto.configure(state=estado)
        self._silencio = False
        self.limpiar_marcas()
        self._refrescar_margen()
        self._marcar_linea_actual()

    def limpiar(self) -> None:
        """Vacía el editor."""
        self.establecer_texto("")

    def descartar_cambio_pendiente(self) -> None:
        """Cancela el aviso de cambio que aún no salió: el texto actual ya se va a analizar."""
        if self._id_cambio is not None:
            self.after_cancel(self._id_cambio)
            self._id_cambio = None

    def solo_lectura(self, activo: bool) -> None:
        """Bloquea o libera la edición."""
        self.texto.configure(state="disabled" if activo else "normal")

    def resaltar(self, tokens: Iterable[Token]) -> None:
        """Colorea cada token según su categoría."""
        for tipo in TipoToken:
            self.texto.tag_remove(self._etiqueta(tipo), "1.0", "end")
        for token in tokens:
            inicio = f"{token.linea}.{token.columna - 1}"
            self.texto.tag_add(self._etiqueta(token.tipo), inicio, f"{inicio}+{token.longitud}c")

    def marcar_errores(self, diagnosticos: Iterable[Diagnostico]) -> None:
        """Por cada diagnóstico con posición: lexema con fondo rojizo, línea rosada y ✗ en el margen."""
        for d in diagnosticos:
            if d.linea <= 0:
                continue
            self._marcas.append((d.linea, d.columna))
            if d.lexema:
                inicio = f"{d.linea}.{d.columna - 1}"
                self.texto.tag_add("marca_error", inicio, f"{inicio}+{len(d.lexema)}c")
            self.texto.tag_add("linea_error", f"{d.linea}.0", f"{d.linea + 1}.0")
            self._lineas_error.add(d.linea)
            self._pintar_marca(d.linea)

    def marcar_lineas_evaluadas(self, lineas: Iterable[int]) -> None:
        """Marca las líneas que el lexer ya recorrió: ✓, o ✗ si tienen error."""
        for n in lineas:
            self._lineas_evaluadas.add(n)
            self._pintar_marca(n)

    def conteo_lineas(self) -> tuple[int, int]:
        """(líneas válidas, líneas con errores) entre las ya evaluadas."""
        return len(self._lineas_evaluadas - self._lineas_error), len(self._lineas_error)

    def limpiar_marcas(self) -> None:
        """Quita lexemas marcados, líneas rosadas, marcas del margen y token actual."""
        for etiqueta in ("marca_error", "linea_error", "actual"):
            self.texto.tag_remove(etiqueta, "1.0", "end")
        self._lineas_evaluadas.clear()
        self._lineas_error.clear()
        self._marcas.clear()
        self._refrescar_margen()

    def resaltar_token_actual(self, token: Token | None) -> None:
        """Resalta el token indicado y lo hace visible; None quita el resaltado y devuelve la vista al cursor."""
        self.texto.tag_remove("actual", "1.0", "end")
        if token is None:
            if self._id_ver is not None:
                self.after_cancel(self._id_ver)
                self._id_ver = None
            self.texto.see("insert")
            return
        inicio = f"{token.linea}.{token.columna - 1}"
        self.texto.tag_add("actual", inicio, f"{inicio}+{token.longitud}c")
        if self._id_ver is None:
            self._id_ver = self.after_idle(self._ver_token_actual)

    def _ver_token_actual(self) -> None:
        """Muestra el token resaltado una vez por ciclo de eventos, no una por cada token del análisis."""
        self._id_ver = None
        rango = self.texto.tag_ranges("actual")
        if rango:
            self.texto.see(rango[0])

    def ir_a(self, linea: int, columna: int) -> None:
        """Lleva el cursor a (línea, columna), contadas desde 1, y da el foco al editor."""
        self.texto.mark_set("insert", f"{linea}.{columna - 1}")
        self.texto.see("insert")
        self.texto.focus_set()
        self._cursor_movido()

    def posicion_cursor(self) -> tuple[int, int]:
        """(línea, columna) del cursor, contadas desde 1."""
        linea, columna = self.texto.index("insert").split(".")
        return int(linea), int(columna) + 1

    def _fila_margen(self, n: int) -> tuple[str, str | None]:
        """Texto del margen de la línea `n` (`número marca`) y la etiqueta de su marca."""
        if n in self._lineas_error:
            return f"{n} ✗", "marca_error"
        if n in self._lineas_evaluadas and self.texto.get(f"{n}.0", f"{n}.end").strip():
            return f"{n} ✓", "marca_ok"
        return f"{n}  ", None

    def _refrescar_margen(self) -> None:
        """Rehace todo el margen; hace falta cuando cambia la cantidad de líneas."""
        total = int(self.texto.index("end-1c").split(".")[0])
        self.margen.configure(state="normal", width=max(6, len(str(total)) + 4))
        self.margen.delete("1.0", "end")
        for n in range(1, total + 1):
            self.margen.insert("end", ("\n" if n > 1 else "") + self._fila_margen(n)[0], "derecha")
        for n in self._lineas_evaluadas | self._lineas_error:
            self._etiquetar_marca(n)
        self.margen.configure(state="disabled")
        self.margen.yview_moveto(self.texto.yview()[0])

    def _etiquetar_marca(self, n: int) -> None:
        etiqueta = self._fila_margen(n)[1]
        if etiqueta and n <= int(self.margen.index("end-1c").split(".")[0]):
            self.margen.tag_add(etiqueta, f"{n}.end-1c", f"{n}.end")

    def _pintar_marca(self, n: int) -> None:
        """Cambia solo la fila `n` del margen; rehacerlo entero por cada línea evaluada sería lento."""
        if n > int(self.margen.index("end-1c").split(".")[0]):
            return
        texto, _etiqueta = self._fila_margen(n)
        self.margen.configure(state="normal")
        self.margen.delete(f"{n}.0", f"{n}.end")
        self.margen.insert(f"{n}.0", texto, "derecha")
        self._etiquetar_marca(n)
        self.margen.configure(state="disabled")

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
