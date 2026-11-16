"""Editor de codigo: pestana unica, margen, resaltado por tokens, marcas de error y widget de inspeccion."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable

from core.modelos import Diagnostico, TipoDiagnostico, TipoToken, Token
from ui import iconos
from ui.estilos import COLORES_TOKEN, TEMA, TIPOS_EN_CURSIVA, fuente_codigo, fuente_interfaz

RETARDO_CAMBIO_MS = 300


def _normalizar(texto: str) -> str:
    """Convierte \\r\\n y \\r en \\n (D-34): las columnas del lexer deben coincidir con las de Tk."""
    return texto.replace("\r\n", "\n").replace("\r", "\n")


class EditorCodigo(ttk.Frame):
    """Text con margen de numeros; avisa de cambios (con debounce) y del movimiento del cursor."""

    def __init__(self, padre, al_cambiar: Callable[[], None] | None = None,
                 al_mover_cursor: Callable[[int, int], None] | None = None,
                 al_cerrar: Callable[[], None] | None = None) -> None:
        super().__init__(padre)
        self._al_cambiar = al_cambiar
        self._al_cerrar = al_cerrar
        self._marcas: list[tuple[int, int]] = []
        self._al_mover_cursor = al_mover_cursor
        self._id_cambio: str | None = None
        self._silencio = False
        self._id_ver: str | None = None
        self._lineas_marcadas: set[int] = set()
        fuente = fuente_codigo(13)

        self._construir_pestana()
        self.margen = tk.Text(self, width=6, padx=6, pady=8, takefocus=0, cursor="arrow", wrap="none",
                              font=fuente, background=TEMA["fondo"], foreground=TEMA["numero_linea"],
                              borderwidth=0, highlightthickness=0, state="disabled")
        self.margen.tag_configure("marca", foreground=TEMA["error"])
        self.margen.tag_configure("derecha", justify="right")
        self.texto = tk.Text(self, wrap="none", undo=True, padx=8, pady=8, font=fuente,
                             background=TEMA["fondo"], foreground=TEMA["texto_codigo"],
                             insertbackground=TEMA["blanco"], selectbackground=TEMA["seleccion"],
                             inactiveselectbackground=TEMA["seleccion"], borderwidth=0,
                             highlightthickness=0, tabs=("4c",))
        self._barra_v = ttk.Scrollbar(self, orient="vertical", command=self._desplazar_ambos)
        self._barra_h = ttk.Scrollbar(self, orient="horizontal", command=self.texto.xview)
        self.texto.configure(yscrollcommand=self._al_desplazar, xscrollcommand=self._barra_h.set)
        self.margen.grid(row=1, column=0, sticky="ns")
        tk.Frame(self, width=1, background=TEMA["borde"]).grid(row=1, column=1, sticky="ns")
        self.texto.grid(row=1, column=2, sticky="nsew")
        self._barra_v.grid(row=1, column=3, sticky="ns")
        self._barra_h.grid(row=2, column=2, sticky="ew")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self._construir_inspeccion()
        self._configurar_etiquetas()
        self.texto.bind("<<Modified>>", self._al_modificar)
        for evento in ("<KeyRelease>", "<ButtonRelease-1>"):
            self.texto.bind(evento, self._cursor_movido, add="+")
        self.margen.bind("<MouseWheel>", lambda e: self.texto.event_generate("<MouseWheel>", delta=e.delta))
        self._refrescar_margen()

    # --- configuracion -------------------------------------------------
    def _construir_pestana(self) -> None:
        """Fila de 36 px con la pestana unica (icono, nombre, x) subrayada en azul (D-46)."""
        fila = tk.Frame(self, background=TEMA["fondo"], height=36)
        fila.grid(row=0, column=0, columnspan=4, sticky="ew")
        fila.pack_propagate(False)
        tk.Frame(fila, height=1, background=TEMA["borde"]).pack(side="bottom", fill="x")
        pestana = tk.Frame(fila, background=TEMA["fondo"])
        pestana.pack(side="left", padx=(8, 0), fill="y")
        tk.Frame(pestana, height=3, background=TEMA["acento"]).pack(side="bottom", fill="x")
        self._icono_archivo = iconos.imagen("archivo", self)  # Tk pierde la imagen si no se guarda
        tk.Label(pestana, image=self._icono_archivo, background=TEMA["fondo"]).pack(side="left", padx=(8, 4))
        self._nombre = tk.Label(pestana, background=TEMA["fondo"], foreground=TEMA["texto"], font=fuente_interfaz(13))
        self._nombre.pack(side="left")
        cerrar = tk.Label(pestana, text="×", background=TEMA["fondo"], foreground=TEMA["texto_secundario"],
                          font=fuente_interfaz(14), cursor="hand2")
        cerrar.pack(side="left", padx=(6, 8))
        cerrar.bind("<Button-1>", lambda _e: self._al_cerrar() if self._al_cerrar else None)
        self.establecer_nombre(None)

    def establecer_nombre(self, nombre: str | None) -> None:
        """Nombre del archivo en la pestana (`sin título` si no hay)."""
        self._nombre.configure(text=nombre or "sin título")

    def _construir_inspeccion(self) -> None:
        """Widget `✗ N ⌃ ⌄` / `✓`, colocado con place sobre el texto (oculto hasta que hay analisis)."""
        self._inspeccion = tk.Frame(self, background=TEMA["fondo"])
        self._lbl_estado = tk.Label(self._inspeccion, background=TEMA["fondo"], font=fuente_interfaz(13))
        self._lbl_estado.pack(side="left", padx=(0, 6))
        self._flechas = []
        for simbolo, direccion in (("⌃", -1), ("⌄", 1)):
            flecha = tk.Label(self._inspeccion, text=simbolo, background=TEMA["fondo"], cursor="hand2",
                              foreground=TEMA["texto_secundario"], font=fuente_interfaz(14))
            flecha.bind("<Button-1>", lambda _e, d=direccion: self.ir_a_error(d))
            self._flechas.append(flecha)

    def _mostrar_inspeccion(self, texto: str, color: str, con_flechas: bool) -> None:
        self._lbl_estado.configure(text=texto, foreground=color)
        for flecha in self._flechas:
            flecha.pack_forget()
            if con_flechas:
                flecha.pack(side="left", padx=2)
        self._inspeccion.place(in_=self.texto, relx=1.0, x=-6, y=4, anchor="ne")
        self._inspeccion.lift()

    def indicar_sin_errores(self) -> None:
        """Muestra `✓` en verde: el analisis termino sin errores."""
        self._mostrar_inspeccion("✓", TEMA["exito"], False)

    def ir_a_error(self, direccion: int) -> None:
        """Salta a la marca siguiente (+1) o anterior (-1) respecto al cursor, dando la vuelta al final."""
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
        self.texto.tag_configure("linea_actual", background=TEMA["linea_actual"])
        base = fuente_codigo(13)
        for tipo, color in COLORES_TOKEN.items():
            fuente = base + ("italic",) if tipo in TIPOS_EN_CURSIVA else base
            self.texto.tag_configure(self._etiqueta(tipo), foreground=color, font=fuente)
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
        """Vacia el editor."""
        self.establecer_texto("")

    def descartar_cambio_pendiente(self) -> None:
        """Anula el aviso de cambio aun no emitido (el texto actual ya se va a usar; AUD-16)."""
        if self._id_cambio is not None:
            self.after_cancel(self._id_cambio)
            self._id_cambio = None

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
            self._marcas.append((d.linea, d.columna))
            if d.lexema:
                inicio = f"{d.linea}.{d.columna - 1}"
                self.texto.tag_add("marca_error", inicio, f"{inicio}+{len(d.lexema)}c")
            if d.tipo == TipoDiagnostico.LEXICO:
                self._lineas_marcadas.add(d.linea)
        self._refrescar_margen()
        if self._marcas:
            self._mostrar_inspeccion(f"✗ {len(self._marcas)}", TEMA["error"], True)

    def limpiar_marcas(self) -> None:
        """Quita subrayados, marcas del margen y token actual."""
        self.texto.tag_remove("marca_error", "1.0", "end")
        self.texto.tag_remove("actual", "1.0", "end")
        self._lineas_marcadas.clear()
        self._marcas.clear()
        self._inspeccion.place_forget()
        self._refrescar_margen()

    def resaltar_token_actual(self, token: Token | None) -> None:
        """Resalta el token indicado y lo hace visible; None quita el resaltado y vuelve
        la vista al cursor (AUD-19)."""
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
        """Hace visible el token resaltado una vez por ciclo de eventos (AUD-17)."""
        self._id_ver = None
        rango = self.texto.tag_ranges("actual")
        if rango:
            self.texto.see(rango[0])

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
