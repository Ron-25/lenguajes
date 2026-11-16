"""Ventana principal: coordina las vistas y consume la sesion de analisis con `after`."""
from __future__ import annotations

import math
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from application.analisis_service import SesionAnalisis, explicar_token, tokenizar
from application.archivos import ErrorArchivo, cargar_fuente, guardar_fuente
from config import reglas
from core.modelos import Diagnostico, Token
from ui.componentes import BarraEstado, BarraHerramientas, PanelConsola, PanelLateral
from ui.editor import EditorCodigo
from ui.estilos import TEMA, aplicar_tema
from ui.paneles import PanelResultados

RETARDO_ANIMACION_MS = 20
DURACION_MAXIMA_ANIMACION_MS = 3000
TITULO_SOLICITUD = "Seleccione el archivo con las cadenas de entrada"
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

SIN_FUENTE, LISTO, ANALIZANDO, TERMINADO = "SIN_FUENTE", "LISTO", "ANALIZANDO", "TERMINADO"
_BOTONES_POR_ESTADO = {
    SIN_FUENTE: ("abrir", "analizar", "ayuda"),
    LISTO: ("abrir", "guardar", "analizar", "paso", "limpiar", "ayuda"),
    ANALIZANDO: ("abrir", "analizar", "paso", "detener", "limpiar", "ayuda"),
    TERMINADO: ("abrir", "guardar", "analizar", "paso", "limpiar", "ayuda"),
}
_AYUDA = (
    "SmartLex Studio — analizador léxico de FlowLang 1.0\n\n"
    "Ctrl+O  Abrir archivo (.flow / .txt)\nCtrl+S  Guardar\n"
    "F5  Analizar (evaluación progresiva)\nF10  Paso a paso (Modo educativo)\n"
    "Esc  Detener\nF1  Esta ayuda\n\n"
    "Clic en un token: ver cómo se reconoció.\nDoble clic en un error: ir a su posición.\n"
    "Al terminar se ofrece ver la tabla de símbolos.")


class VentanaPrincipal(tk.Tk):
    """Mini-IDE de SmartLex Studio. Los metodos publicos son los que usan atajos, botones y pruebas."""

    def __init__(self, solicitar_archivo: bool = True) -> None:
        super().__init__()
        self.estado = SIN_FUENTE
        self.sesion: SesionAnalisis | None = None
        self.ruta_actual: Path | None = None
        self._id_tick: str | None = None
        self._pasos_por_tick = 1
        self._errores_vistos = 0
        aplicar_tema(self)
        self._configurar_ventana()
        self._construir()
        self._registrar_atajos()
        self._actualizar_estado(SIN_FUENTE)
        if solicitar_archivo:
            self.after(100, self._solicitar_archivo_inicial)

    # --- construccion ----------------------------------------------------
    def _configurar_ventana(self) -> None:
        ancho = min(1280, self.winfo_screenwidth())
        alto = min(800, self.winfo_screenheight() - 60)
        self.geometry(f"{ancho}x{alto}")
        self.minsize(min(1000, ancho), min(650, alto))
        self._poner_titulo()

    def _construir(self) -> None:
        self.barra = BarraHerramientas(self, {
            "abrir": self.abrir_archivo, "guardar": self.guardar_archivo, "analizar": self.analizar,
            "paso": self.paso_a_paso, "detener": self.detener, "limpiar": self.limpiar,
            "ayuda": self.mostrar_ayuda})
        self.barra_estado = BarraEstado(self, self.ver_tabla_simbolos)
        self.barra.pack(side="top", fill="x")
        self.barra_estado.pack(side="bottom", fill="x")
        principal = ttk.Panedwindow(self, orient="horizontal")
        principal.pack(fill="both", expand=True)
        self.panel_lateral = PanelLateral(principal, self.abrir_archivo)
        centro = ttk.Panedwindow(principal, orient="vertical")
        arriba = ttk.Panedwindow(centro, orient="horizontal")
        self.editor = EditorCodigo(arriba, al_cambiar=self._al_editar,
                                   al_mover_cursor=self.barra_estado.establecer_posicion)
        self.panel_resultados = PanelResultados(arriba, self._al_seleccionar_token, self._al_seleccionar_error)
        self.consola = PanelConsola(centro)
        arriba.add(self.editor, weight=3)
        arriba.add(self.panel_resultados, weight=2)
        centro.add(arriba, weight=4)
        centro.add(self.consola, weight=1)
        principal.add(self.panel_lateral, weight=0)
        principal.add(centro, weight=1)
        self.update_idletasks()
        principal.sashpos(0, 250)
        self.update_idletasks()
        arriba.sashpos(0, int(arriba.winfo_width() * 0.52))

    def _registrar_atajos(self) -> None:
        atajos = {"<Control-o>": self.abrir_archivo, "<Control-s>": self.guardar_archivo,
                  "<F5>": self.analizar, "<F10>": self.paso_a_paso, "<Escape>": self.detener,
                  "<F1>": self.mostrar_ayuda}
        if sys.platform == "darwin":
            atajos.update({"<Command-o>": self.abrir_archivo, "<Command-s>": self.guardar_archivo})
        for secuencia, accion in atajos.items():
            self.bind_all(secuencia, lambda _e, f=accion: f())

    # --- estado ----------------------------------------------------------
    def _actualizar_estado(self, estado: str, mensaje: str | None = None) -> None:
        self.estado = estado
        self.barra.habilitar(_BOTONES_POR_ESTADO[estado])
        textos = {SIN_FUENTE: "Sin archivo", LISTO: "Listo para analizar",
                  ANALIZANDO: "Analizando…", TERMINADO: "Análisis terminado"}
        self.barra_estado.establecer_estado(mensaje or textos[estado])

    def _poner_titulo(self) -> None:
        nombre = f" — {self.ruta_actual.name}" if self.ruta_actual else ""
        self.title(f"SmartLex Studio{nombre}")

    def _cancelar_temporizador(self) -> None:
        if self._id_tick is not None:
            self.after_cancel(self._id_tick)
            self._id_tick = None

    def _reiniciar_resultados(self) -> None:
        self._cancelar_temporizador()
        self.sesion = None
        self._errores_vistos = 0
        self.panel_resultados.limpiar()
        self.barra_estado.habilitar_ver_tabla(False)
        self.barra_estado.establecer_contadores(0, 0)
        self.editor.limpiar_marcas()
        self.editor.solo_lectura(False)

    # --- archivos --------------------------------------------------------
    def _solicitar_archivo_inicial(self) -> None:
        if self.estado == SIN_FUENTE and not self.editor.obtener_texto().strip():
            self.abrir_archivo()

    def abrir_archivo(self, ruta=None) -> None:
        """Carga un archivo (pidiendolo si no se da la ruta) y lo muestra en el editor."""
        if ruta is None:
            ruta = filedialog.askopenfilename(
                title=TITULO_SOLICITUD, initialdir=str(RAIZ_PROYECTO / "ejemplos"),
                filetypes=[("FlowLang", " ".join("*" + e for e in reglas.EXTENSIONES_PERMITIDAS)),
                           ("Todos los archivos", "*.*")])
            if not ruta:
                return
        try:
            texto = cargar_fuente(ruta)
        except ErrorArchivo as error:
            self._mostrar_error_archivo(error.diagnostico)
            return
        self._reiniciar_resultados()
        self.editor.establecer_texto(texto)
        self.editor.resaltar(tokenizar(self.editor.obtener_texto()))
        self.ruta_actual = Path(ruta)
        self._poner_titulo()
        self.consola.escribir(f"Archivo cargado: {self.ruta_actual.name} ({len(texto)} caracteres)", "info")
        self._actualizar_estado(LISTO)

    def _mostrar_error_archivo(self, diagnostico: Diagnostico) -> None:
        self.consola.escribir(f"✗ {diagnostico.codigo} {diagnostico.mensaje} {diagnostico.sugerencia}", "error")
        self.panel_resultados.agregar_error(diagnostico)
        self.panel_resultados.seleccionar_pestana("errores")
        messagebox.showerror(diagnostico.titulo, f"{diagnostico.mensaje}\n\n{diagnostico.sugerencia}")

    def guardar_archivo(self) -> None:
        """Guarda el contenido del editor (pide la ruta si el archivo es nuevo)."""
        ruta = self.ruta_actual
        if ruta is None:
            elegida = filedialog.asksaveasfilename(
                title="Guardar programa FlowLang", defaultextension=reglas.EXTENSIONES_PERMITIDAS[0],
                initialdir=str(RAIZ_PROYECTO / "ejemplos"),
                filetypes=[("FlowLang", "*" + reglas.EXTENSIONES_PERMITIDAS[0])])
            if not elegida:
                return
            ruta = Path(elegida)
        try:
            guardar_fuente(ruta, self.editor.obtener_texto())
        except ErrorArchivo as error:
            self._mostrar_error_archivo(error.diagnostico)
            return
        self.ruta_actual = ruta
        self._poner_titulo()
        self.consola.escribir(f"Guardado: {ruta.name}", "info")

    # --- analisis --------------------------------------------------------
    def _sincronizar_con_texto(self) -> None:
        """Si se escribio texto sin abrir archivo, el editor ya es una fuente valida."""
        if self.estado == SIN_FUENTE and self.editor.obtener_texto().strip():
            self._actualizar_estado(LISTO)

    def _iniciar_sesion(self) -> None:
        fuente = self.editor.obtener_texto()
        self._reiniciar_resultados()
        self.sesion = SesionAnalisis(fuente)
        estimado = len(fuente) // 4
        self._pasos_por_tick = max(1, math.ceil(estimado / (DURACION_MAXIMA_ANIMACION_MS / RETARDO_ANIMACION_MS)))
        self.editor.solo_lectura(True)
        self.consola.limpiar()
        self.consola.escribir(f"Analizando {self.ruta_actual.name if self.ruta_actual else 'texto del editor'}…", "info")
        self._actualizar_estado(ANALIZANDO)

    def analizar(self) -> None:
        """Inicia (o continua) la evaluacion progresiva con un temporizador."""
        self._sincronizar_con_texto()
        if self.estado == SIN_FUENTE:
            self.abrir_archivo()
            return
        if self._id_tick is not None:
            return
        if self.estado != ANALIZANDO:
            self._iniciar_sesion()
        self._id_tick = self.after(RETARDO_ANIMACION_MS, self._tick)

    def _tick(self) -> None:
        self._id_tick = None
        for _ in range(self._pasos_por_tick):
            if not self._consumir_paso(educativo=False):
                return
        self._id_tick = self.after(RETARDO_ANIMACION_MS, self._tick)

    def paso_a_paso(self) -> None:
        """Consume exactamente un paso y lo explica en el Modo educativo."""
        self._sincronizar_con_texto()
        if self.estado == SIN_FUENTE:
            self.abrir_archivo()
            return
        self._cancelar_temporizador()
        if self.estado != ANALIZANDO:
            self._iniciar_sesion()
        self._consumir_paso(educativo=True)

    def detener(self) -> None:
        """Pausa la evaluacion; analizar o paso a paso la continuan."""
        if self._id_tick is not None:
            self._cancelar_temporizador()
            self._actualizar_estado(ANALIZANDO, "Evaluación detenida (F5 continúa, F10 avanza un paso)")

    def _consumir_paso(self, educativo: bool) -> bool:
        """Aplica un paso a las vistas; False cuando la sesion ya termino."""
        paso = self.sesion.siguiente_paso()
        if paso is None:
            self._finalizar()
            return False
        resultado = self.sesion.resultado
        if paso.token is not None:
            self.panel_resultados.agregar_token(paso.numero, paso.token)
            self.editor.resaltar_token_actual(paso.token)
        self.consola.escribir(paso.descripcion, "error" if paso.diagnosticos else "normal")
        for diagnostico in paso.diagnosticos:
            self._errores_vistos += 1
            self.panel_resultados.agregar_error(diagnostico)
            self.editor.marcar_errores([diagnostico])
            if self._errores_vistos == 1 and not educativo:
                self.panel_resultados.seleccionar_pestana("errores")
            if paso.token is None:
                self.editor.ir_a(diagnostico.linea, diagnostico.columna)
        self.barra_estado.establecer_contadores(len(resultado.tokens), self._errores_vistos)
        if educativo:
            self.panel_resultados.seleccionar_pestana("educativo")
            if paso.token is not None:
                self.panel_resultados.mostrar_explicacion(explicar_token(paso.token, resultado.tabla))
        return True

    def _finalizar(self) -> None:
        resultado = self.sesion.resultado
        self._cancelar_temporizador()
        self.editor.solo_lectura(False)
        self.editor.resaltar_token_actual(None)
        self.consola.escribir("— Fin del análisis —", "info")
        self._veredictos_en_consola(resultado)
        self.panel_resultados.mostrar_estadisticas(resultado)
        self.panel_resultados.mostrar_tabla_simbolos(resultado.tabla)
        self.panel_resultados.habilitar_tabla_simbolos(True)
        self.barra_estado.habilitar_ver_tabla(True)
        self._actualizar_estado(TERMINADO)
        valida = "VÁLIDA" if resultado.es_valida else "INVÁLIDA"
        if messagebox.askyesno("Análisis terminado", f"Análisis terminado: cadena {valida} "
                               f"({resultado.manejador.resumen()}).\n\n¿Desea ver la tabla de símbolos?"):
            self.ver_tabla_simbolos()

    def _veredictos_en_consola(self, resultado) -> None:
        def nivel(ok: bool) -> str:
            return "exito" if ok else "error"
        self.consola.escribir(f"Léxico: {'válido' if resultado.es_valida_lexicamente else 'inválido'}",
                              nivel(resultado.es_valida_lexicamente))
        self.consola.escribir(f"Estructura: {'válida' if resultado.es_valida_estructuralmente else 'inválida'}",
                              nivel(resultado.es_valida_estructuralmente))
        self.consola.escribir(f"Cadena de entrada: {'VÁLIDA' if resultado.es_valida else 'INVÁLIDA'} "
                              f"({resultado.manejador.resumen()})", nivel(resultado.es_valida))
        lineas = resultado.lineas_invalidas()
        if lineas:
            self.consola.escribir("Líneas léxicamente inválidas: " + ", ".join(map(str, lineas)), "error")

    def ver_tabla_simbolos(self) -> None:
        """Muestra la pestana de simbolos (solo disponible al terminar)."""
        if self.panel_resultados.tabla_simbolos_habilitada():
            self.panel_resultados.seleccionar_pestana("simbolos")

    def limpiar(self) -> None:
        """Deja la aplicacion sin archivo y sin resultados."""
        self._reiniciar_resultados()
        self.editor.limpiar()
        self.consola.limpiar()
        self.ruta_actual = None
        self._poner_titulo()
        self._actualizar_estado(SIN_FUENTE)

    def mostrar_ayuda(self) -> None:
        """Atajos y modo de uso."""
        messagebox.showinfo("Ayuda de SmartLex Studio", _AYUDA)

    # --- eventos de las vistas -------------------------------------------
    def _al_editar(self) -> None:
        """El usuario cambio el texto: re-resalta y deja obsoletos los resultados."""
        if self.estado == ANALIZANDO:
            return
        texto = self.editor.obtener_texto()
        self.editor.limpiar_marcas()
        self.editor.resaltar(tokenizar(texto))
        if self.estado == TERMINADO:
            self.sesion = None
            self._actualizar_estado(LISTO, "Texto modificado: los resultados están desactualizados")
        elif texto.strip():
            self._actualizar_estado(LISTO)
        else:
            self._actualizar_estado(SIN_FUENTE)

    def _al_seleccionar_token(self, token: Token) -> None:
        self.editor.resaltar_token_actual(token)
        tabla = self.sesion.resultado.tabla if self.sesion is not None else None
        self.panel_resultados.mostrar_explicacion(explicar_token(token, tabla))

    def _al_seleccionar_error(self, diagnostico: Diagnostico) -> None:
        if diagnostico.linea > 0:
            self.editor.ir_a(diagnostico.linea, diagnostico.columna)
