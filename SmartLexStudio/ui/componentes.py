"""Componentes de la ventana: barra de herramientas, panel lateral, consola y barra de estado."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Iterable

from application.archivos import listar_ejemplos
from config import reglas
from core.modelos import TipoToken
from ui.estilos import TEMA, fuente_codigo

_MAX_LINEAS_CONSOLA = 5000

# nombre de accion -> (texto del boton, estilo)
_BOTONES = (
    ("abrir", "Abrir", "TButton"), ("guardar", "Guardar", "TButton"), None,
    ("analizar", "▶  Analizar", "Accion.TButton"), ("paso", "⏭  Paso a paso", "TButton"),
    ("detener", "■  Detener", "TButton"), None,
    ("limpiar", "Limpiar", "TButton"), ("ayuda", "Ayuda", "TButton"),
)


class BarraHerramientas(ttk.Frame):
    """Fila de botones; `acciones` asocia el nombre de cada boton con su funcion."""

    def __init__(self, padre, acciones: dict[str, Callable]) -> None:
        super().__init__(padre, style="Barra.TFrame", padding=(10, 8))
        self.botones: dict[str, ttk.Button] = {}
        for definicion in _BOTONES:
            if definicion is None:
                ttk.Separator(self, orient="vertical").pack(side="left", fill="y", padx=8)
                continue
            nombre, texto, estilo = definicion
            boton = ttk.Button(self, text=texto, style=estilo, command=acciones[nombre])
            boton.pack(side="left", padx=3)
            self.botones[nombre] = boton

    def habilitar(self, nombres: Iterable[str]) -> None:
        """Activa los botones indicados y desactiva el resto."""
        activos = set(nombres)
        for nombre, boton in self.botones.items():
            boton.state(["!disabled"] if nombre in activos else ["disabled"])


class PanelLateral(ttk.Frame):
    """Ejemplos disponibles y arbol de referencia de FlowLang construido desde config.reglas."""

    def __init__(self, padre, al_elegir_ejemplo: Callable[[Path], None]) -> None:
        super().__init__(padre, style="Panel.TFrame")
        self._al_elegir = al_elegir_ejemplo
        self._rutas: dict[str, Path] = {}
        self._descripciones: dict[str, str] = {}
        ttk.Label(self, text="EJEMPLOS", style="Titulo.TLabel", padding=(14, 12, 0, 4)).pack(anchor="w")
        self.lista = ttk.Treeview(self, show="tree", selectmode="browse", height=4)
        self.lista.pack(fill="x", padx=6)
        self.lista.bind("<Double-1>", self._doble_clic)
        for ruta in listar_ejemplos():
            iid = self.lista.insert("", "end", text="  " + ruta.name)
            self._rutas[iid] = ruta
        ttk.Label(self, text=f"{reglas.NOMBRE_LENGUAJE.upper()} {reglas.VERSION_LENGUAJE}",
                  style="Titulo.TLabel", padding=(14, 14, 0, 4)).pack(anchor="w")
        marco = ttk.Frame(self, style="Panel.TFrame")
        marco.pack(fill="both", expand=True, padx=(6, 0))
        self.arbol = ttk.Treeview(marco, show="tree", selectmode="browse")
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=barra.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.arbol.bind("<<TreeviewSelect>>", self._mostrar_descripcion)
        self.detalle = ttk.Label(self, style="Tenue.TLabel", wraplength=220, justify="left",
                                 padding=(14, 8), text="Seleccione un elemento para ver su descripción.")
        self.detalle.pack(fill="x")
        self._construir_arbol()

    def _doble_clic(self, _evento) -> None:
        elegido = self.lista.identify_row(_evento.y)
        if elegido in self._rutas:
            self._al_elegir(self._rutas[elegido])

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
        ttk.Label(self, text="CONSOLA DE EVALUACIÓN", style="Titulo.TLabel", padding=(14, 8, 0, 2)).pack(anchor="w")
        marco = ttk.Frame(self, style="Panel.TFrame")
        marco.pack(fill="both", expand=True)
        self.texto = tk.Text(marco, height=8, wrap="none", state="disabled", font=fuente_codigo(12),
                             background=TEMA["panel"], foreground=TEMA["texto"], borderwidth=0,
                             highlightthickness=0, padx=14, pady=4)
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.texto.yview)
        self.texto.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.texto.pack(side="left", fill="both", expand=True)
        for nivel, color in (("normal", TEMA["texto"]), ("error", TEMA["error"]),
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
        self.texto.see("end")

    def limpiar(self) -> None:
        """Borra todo el registro."""
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.configure(state="disabled")


class BarraEstado(ttk.Frame):
    """Franja inferior: estado, contadores, posicion del cursor y boton de la tabla."""

    def __init__(self, padre, al_ver_tabla: Callable) -> None:
        super().__init__(padre, style="Estado.TFrame", padding=(12, 4))
        self._estado = ttk.Label(self, style="Estado.TLabel")
        self._contadores = ttk.Label(self, style="Estado.TLabel")
        self._posicion = ttk.Label(self, style="Estado.TLabel")
        self._boton = ttk.Button(self, text="Ver tabla de símbolos", style="Estado.TButton", command=al_ver_tabla)
        self._boton.pack(side="right")
        ttk.Label(self, text=f"UTF-8  ·  {reglas.NOMBRE_LENGUAJE} {reglas.VERSION_LENGUAJE}",
                  style="Estado.TLabel").pack(side="right", padx=16)
        self._posicion.pack(side="right", padx=8)
        self._estado.pack(side="left")
        self._contadores.pack(side="left", padx=24)
        self.establecer_estado("Listo")
        self.establecer_contadores(0, 0)
        self.establecer_posicion(1, 1)
        self.habilitar_ver_tabla(False)

    def establecer_estado(self, texto: str) -> None:
        """Texto principal de estado."""
        self._estado.configure(text=texto)

    def establecer_contadores(self, tokens: int, errores: int) -> None:
        """Cantidad de tokens y de errores encontrados hasta ahora."""
        self._contadores.configure(text=f"{tokens} tokens  ·  {errores} {'error' if errores == 1 else 'errores'}")

    def establecer_posicion(self, linea: int, columna: int) -> None:
        """Posicion del cursor."""
        self._posicion.configure(text=f"Lín {linea}, Col {columna}")

    def habilitar_ver_tabla(self, activo: bool) -> None:
        """Activa o desactiva el boton de la tabla de simbolos."""
        self._boton.state(["!disabled"] if activo else ["disabled"])
