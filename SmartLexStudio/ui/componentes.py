"""Componentes de la ventana: cabecera, vista del lenguaje, consola y barra de estado (arquitectura §17.2)."""
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
PAUSA_POR_DEFECTO_MS = 120  # deslizador «Pausa por línea» (§17.7); la ventana las reexporta
PAUSA_MAXIMA_MS = 500

# (clave, texto, estilo) de los botones de la fila 2 de la cabecera, por grupos separados por una barra
_GRUPO_ARCHIVO = (("nuevo", "Nuevo archivo", "Secundario.TButton"), ("abrir", "Abrir archivo…", "Primario.TButton"))
_GRUPO_GUARDAR = (("guardar", "Guardar", "Secundario.TButton"), ("limpiar", "Limpiar", "Secundario.TButton"))
_GRUPO_EJECUCION = (("analizar", "Analizar", "Secundario.TButton"), ("paso", "Paso a paso", "Secundario.TButton"),
                    ("detener", "Detener", "Secundario.TButton"))


class Cabecera(tk.Frame):
    """Cabecera azul marino de dos filas: marca y ayuda arriba; acciones, ejemplos y pausa abajo."""

    def __init__(self, padre, acciones: dict[str, Callable], al_elegir_ejemplo: Callable[[Path], None],
                 al_ver_tabla: Callable) -> None:
        super().__init__(padre, background=TEMA["cabecera"])
        self._al_elegir = al_elegir_ejemplo
        self.botones: dict[str, ttk.Button] = {}
        fila1 = tk.Frame(self, background=TEMA["cabecera"])
        fila2 = tk.Frame(self, background=TEMA["cabecera"])
        fila1.pack(fill="x", padx=12, pady=(10, 4))
        fila2.pack(fill="x", padx=12, pady=(0, 10))
        tk.Label(fila1, text="SmartLex Studio", background=TEMA["cabecera"], foreground=TEMA["blanco"],
                 font=fuente_interfaz(17) + ("bold",)).pack(side="left")
        tk.Label(fila1, text=f"Analizador léxico de {reglas.NOMBRE_LENGUAJE} · Tabla de símbolos · Manejador de errores",
                 background=TEMA["cabecera"], foreground=TEMA["cabecera_tenue"],
                 font=fuente_interfaz(12)).pack(side="left", padx=(16, 0), pady=(4, 0))
        self.boton_tabla = ttk.Button(fila1, text="Ver tabla de símbolos", style="Secundario.TButton",
                                      command=al_ver_tabla, width=0)
        self.boton_tabla.pack(side="right")
        self.botones["ayuda"] = ttk.Button(fila1, text="Ayuda", style="Secundario.TButton",
                                           command=acciones["ayuda"], width=0)
        self.botones["ayuda"].pack(side="right", padx=(0, 8))
        self._grupo(fila2, _GRUPO_ARCHIVO, acciones)
        self._menu_ejemplos(fila2)
        self._grupo(fila2, _GRUPO_GUARDAR, acciones)
        self._separador(fila2)
        self._grupo(fila2, _GRUPO_EJECUCION, acciones)
        self._separador(fila2)
        self._construir_pausa(fila2)
        self.habilitar_ver_tabla(False)

    def _grupo(self, fila, grupo, acciones) -> None:
        for clave, texto, estilo in grupo:
            boton = ttk.Button(fila, text=texto, style=estilo, command=acciones[clave], width=0)
            boton.pack(side="left", padx=(0, 6))
            self.botones[clave] = boton

    def _separador(self, fila) -> None:
        tk.Frame(fila, width=1, height=24, background=TEMA["cabecera_tenue"]).pack(side="left", padx=(2, 6))

    def _menu_ejemplos(self, fila) -> None:
        """Menubutton «Ejemplos ▾»: el menu se rellena cada vez que se abre (un archivo nuevo aparece sin reiniciar)."""
        self.menu_ejemplos = tk.Menu(fila, tearoff=0, postcommand=self._llenar_ejemplos)
        boton = ttk.Menubutton(fila, text="Ejemplos", style="Cabecera.TMenubutton", menu=self.menu_ejemplos, width=0)
        boton.pack(side="left", padx=(0, 6))

    def _llenar_ejemplos(self) -> None:
        self.menu_ejemplos.delete(0, "end")
        for ruta in listar_ejemplos():
            self.menu_ejemplos.add_command(label=ruta.name, command=lambda r=ruta: self._al_elegir(r))

    def _construir_pausa(self, fila) -> None:
        tk.Label(fila, text="Pausa por línea:", background=TEMA["cabecera"], foreground=TEMA["cabecera_tenue"],
                 font=fuente_interfaz(12)).pack(side="left", padx=(0, 8))
        self._escala = ttk.Scale(fila, from_=0, to=PAUSA_MAXIMA_MS, length=80, style="Cabecera.Horizontal.TScale",
                                 command=lambda _v: self._actualizar_etiqueta())
        self._escala.pack(side="left")
        self._etiqueta_pausa = tk.Label(fila, background=TEMA["cabecera"], foreground=TEMA["blanco"],
                                        font=fuente_interfaz(12), width=6, anchor="w")
        self._etiqueta_pausa.pack(side="left", padx=(8, 0))
        self.establecer_pausa(PAUSA_POR_DEFECTO_MS)

    def _actualizar_etiqueta(self) -> None:
        self._etiqueta_pausa.configure(text=f"{self.pausa_ms()} ms")

    def pausa_ms(self) -> int:
        """Valor del deslizador redondeado a multiplos de 10."""
        return int(round(float(self._escala.get()) / 10) * 10)

    def establecer_pausa(self, ms: int) -> None:
        """Fija el deslizador (pruebas y capturas)."""
        self._escala.set(ms)
        self._actualizar_etiqueta()

    def habilitar(self, nombres: Iterable[str]) -> None:
        """Activa los botones indicados y desactiva el resto."""
        activos = set(nombres)
        for nombre, boton in self.botones.items():
            boton.state(["!disabled"] if nombre in activos else ["disabled"])

    def habilitar_ver_tabla(self, activo: bool) -> None:
        """«Ver tabla de símbolos» solo esta disponible al terminar el analisis."""
        self.boton_tabla.state(["!disabled"] if activo else ["disabled"])


class VistaLenguaje(ttk.Frame):
    """Referencia de FlowLang (config.reglas): arbol de palabras, operadores, delimitadores y limites."""

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
    """Barra inferior: contadores a la izquierda; estado, Lin/Col y veredicto a la derecha."""

    def __init__(self, padre) -> None:
        super().__init__(padre, style="Estado.TFrame", height=28)
        self.pack_propagate(False)
        self.contadores = ttk.Label(self, style="Estado.TLabel")
        self._estado = ttk.Label(self, style="Estado.TLabel")
        self._posicion = ttk.Label(self, style="Estado.TLabel")
        self.veredicto = ttk.Label(self, style="Veredicto.TLabel")
        self.contadores.pack(side="left", padx=(14, 0))
        self.veredicto.pack(side="right", padx=(16, 14))
        self._posicion.pack(side="right", padx=(16, 0))
        self._estado.pack(side="right", padx=(16, 0))
        self.establecer_estado("Listo")
        self.establecer_contadores(0, 0, 0, 0, 0)
        self.establecer_posicion(1, 1)
        self.establecer_veredicto(None)

    def establecer_estado(self, texto: str) -> None:
        """Mensaje de estado (§10.4)."""
        self._estado.configure(text=texto)

    def establecer_contadores(self, validas: int, con_errores: int, tokens: int, simbolos: int, errores: int) -> None:
        """Los cinco contadores en una sola etiqueta."""
        self.contadores.configure(text=(f"Líneas válidas: {validas}  ·  Líneas con errores: {con_errores}  ·  "
                                        f"Tokens: {tokens}  ·  Símbolos: {simbolos}  ·  Errores: {errores}"))

    def establecer_posicion(self, linea: int, columna: int) -> None:
        """Posicion del cursor."""
        self._posicion.configure(text=f"Lín {linea}, Col {columna}")

    def establecer_veredicto(self, valido: bool | None) -> None:
        """Veredicto final del analisis; `None` lo borra."""
        if valido is None:
            self.veredicto.configure(text="")
        elif valido:
            self.veredicto.configure(text=f"✓ El archivo es válido para {reglas.NOMBRE_LENGUAJE}", foreground=TEMA["exito"])
        else:
            self.veredicto.configure(text=f"✗ El archivo NO es válido para {reglas.NOMBRE_LENGUAJE}", foreground=TEMA["error"])
