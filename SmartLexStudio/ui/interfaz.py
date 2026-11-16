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
from ui.componentes import (RAIZ_PROYECTO, BarraEstado, BarraHerramientas, FranjaHerramientas, PanelConsola,
                            PanelHerramientas, PanelLateral)
from ui.editor import EditorCodigo
from ui.estilos import aplicar_tema
from ui.paneles import PanelProblemas, PanelResultados

RETARDO_ANIMACION_MS = 20
DURACION_MAXIMA_ANIMACION_MS = 3000
TITULO_SOLICITUD = "Seleccione el archivo con las cadenas de entrada"

# herramienta -> zona de la ventana (arquitectura §16.7)
_HERRAMIENTAS = {
    "proyecto": "izquierda", "lenguaje": "izquierda",
    "consola": "inferior", "problemas": "inferior",
    "tokens": "derecha", "simbolos": "derecha", "estadisticas": "derecha", "educativo": "derecha",
}
# (nombre, descripcion, abajo) de cada franja
_ICONOS_IZQUIERDA = (("proyecto", "Proyecto", False), ("lenguaje", "Lenguaje FlowLang", False),
                     ("consola", "Consola de evaluación", True), ("problemas", "Problemas", True))
_ICONOS_DERECHA = (("tokens", "Tokens", False), ("simbolos", "Tabla de símbolos", False),
                   ("estadisticas", "Estadísticas", False), ("educativo", "Modo educativo", False))

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
    "Esc  Detener\nF1  Esta ayuda\nF2 / Shift+F2  Siguiente / anterior error\n\n"
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
        self._tamanos: dict[str, int] = {}
        aplicar_tema(self)
        self._configurar_ventana()
        self._construir()
        self._registrar_atajos()
        self._poner_titulo()
        self._actualizar_estado(SIN_FUENTE)
        if solicitar_archivo:
            self.after(100, self._solicitar_archivo_inicial)

    def destroy(self) -> None:
        """Cancela todos los `after` pendientes del interprete (tick, debounce del editor,
        desplazamientos diferidos) antes de destruir: si no, el bucle de eventos los ejecuta
        despues y Tcl informa «invalid command name … ("after" script)» (AUD-28)."""
        try:
            pendientes = self.tk.splitlist(self.tk.call("after", "info"))
        except tk.TclError:
            pendientes = ()
        for identificador in pendientes:
            # solo se cancela en Tcl: cada widget borra su propio comando al destruirse
            self.tk.call("after", "cancel", identificador)
        self._id_tick = None
        super().destroy()

    # --- construccion ----------------------------------------------------
    def _configurar_ventana(self) -> None:
        ancho = min(1280, self.winfo_screenwidth())
        alto = min(800, self.winfo_screenheight() - 60)
        self.geometry(f"{ancho}x{alto}")
        self.minsize(min(1000, ancho), min(650, alto))
        self.title("SmartLex Studio")

    def _construir(self) -> None:
        """Disposicion de la arquitectura §16.2: barras, franjas y tres zonas redimensionables."""
        self.barra = BarraHerramientas(self, {
            "abrir": self.abrir_archivo, "guardar": self.guardar_archivo, "analizar": self.analizar,
            "paso": self.paso_a_paso, "detener": self.detener, "limpiar": self.limpiar,
            "ayuda": self.mostrar_ayuda, "salir": self.destroy})
        self.barra_estado = BarraEstado(self, self.ver_tabla_simbolos)
        self.franja_izquierda = FranjaHerramientas(self, self.alternar_herramienta)
        self.franja_derecha = FranjaHerramientas(self, self.alternar_herramienta)
        self.barra.pack(side="top", fill="x")
        self.barra_estado.pack(side="bottom", fill="x")
        self.franja_izquierda.pack(side="left", fill="y")
        self.franja_derecha.pack(side="right", fill="y")
        for franja, iconos in ((self.franja_izquierda, _ICONOS_IZQUIERDA), (self.franja_derecha, _ICONOS_DERECHA)):
            for nombre, descripcion, abajo in iconos:
                franja.agregar(nombre, descripcion, abajo)
        self.franja_derecha.habilitar("simbolos", False)
        self.cuerpo = ttk.Panedwindow(self, orient="vertical")
        self.cuerpo.pack(fill="both", expand=True)
        self.superior = ttk.Panedwindow(self.cuerpo, orient="horizontal")
        self.panel_lateral = PanelLateral(self.superior, self.abrir_archivo)
        self.editor = EditorCodigo(self.superior, al_cambiar=self._al_editar,
                                   al_mover_cursor=self.barra_estado.establecer_posicion, al_cerrar=self.limpiar)
        self.panel_resultados = PanelResultados(self.superior, self._al_seleccionar_token)
        self.inferior = PanelHerramientas(self.cuerpo)
        self.consola = PanelConsola(self.inferior.cuerpo)
        self.problemas = PanelProblemas(self.inferior.cuerpo, self._al_seleccionar_error)
        self.inferior.agregar_vista("consola", "Consola de evaluación", self.consola)
        self.inferior.agregar_vista("problemas", "Problemas", self.problemas)
        self._paneles = {"izquierda": self.panel_lateral, "derecha": self.panel_resultados, "inferior": self.inferior}
        for zona, panel in self._paneles.items():
            panel.al_ocultar = lambda z=zona: self._ocultar_zona(z)
        self.superior.add(self.panel_lateral, weight=0)
        self.superior.add(self.editor, weight=3)
        self.superior.add(self.panel_resultados, weight=2)
        self.cuerpo.add(self.superior, weight=4)
        self.cuerpo.add(self.inferior, weight=1)
        self._colocar_divisores()
        self._refrescar_franjas()

    def _colocar_divisores(self) -> None:
        """Tamanos iniciales: izquierda 250 px, derecha 36 % del ancho, inferior 250 px."""
        self.update_idletasks()
        ancho, alto = self.superior.winfo_width(), self.cuerpo.winfo_height()
        self.superior.sashpos(0, 250)
        self.superior.sashpos(1, ancho - int(ancho * 0.36))
        self.cuerpo.sashpos(0, alto - 250)

    def _registrar_atajos(self) -> None:
        atajos = {"<Control-o>": self.abrir_archivo, "<Control-s>": self.guardar_archivo,
                  "<F5>": self.analizar, "<F10>": self.paso_a_paso, "<Escape>": self.detener,
                  "<F1>": self.mostrar_ayuda, "<F2>": lambda: self.editor.ir_a_error(1),
                  "<Shift-F2>": lambda: self.editor.ir_a_error(-1)}
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

    def _migas(self) -> list[str]:
        """Migas de pan del archivo: proyecto › carpeta › archivo (o `carpeta › archivo` si esta fuera)."""
        nombre = RAIZ_PROYECTO.name
        if self.ruta_actual is None:
            return [nombre]
        ruta = self.ruta_actual.resolve()
        try:
            return [nombre, *ruta.relative_to(RAIZ_PROYECTO.resolve()).parts]
        except ValueError:
            return [ruta.parent.name, ruta.name]

    def _poner_titulo(self) -> None:
        """Titulo de la ventana, migas de la barra de estado, pestana del editor y arbol de Proyecto."""
        nombre = f" — {self.ruta_actual.name}" if self.ruta_actual else ""
        self.title(f"SmartLex Studio{nombre}")
        self.barra_estado.establecer_ruta(self._migas())
        self.editor.establecer_nombre(self.ruta_actual.name if self.ruta_actual else None)
        self.panel_lateral.marcar_abierto(self.ruta_actual)

    def _cancelar_temporizador(self) -> None:
        if self._id_tick is not None:
            self.after_cancel(self._id_tick)
            self._id_tick = None

    def _reiniciar_resultados(self) -> None:
        self._cancelar_temporizador()
        self.sesion = None
        self._errores_vistos = 0
        self.panel_resultados.limpiar()
        self.problemas.limpiar()
        self._habilitar_simbolos(False)
        self.franja_izquierda.poner_contador("problemas", 0)
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
        self.problemas.quitar_errores_de_archivo()
        self.problemas.agregar_error(diagnostico)
        self.mostrar_herramienta("problemas")
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
        self.editor.descartar_cambio_pendiente()
        self._reiniciar_resultados()
        self.sesion = SesionAnalisis(fuente)
        estimado = len(fuente) // 4
        self._pasos_por_tick = max(1, math.ceil(estimado / (DURACION_MAXIMA_ANIMACION_MS / RETARDO_ANIMACION_MS)))
        self.editor.solo_lectura(True)
        self.consola.limpiar()
        if not self._zona_visible("inferior"):
            self.mostrar_herramienta("consola")
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
            self.problemas.agregar_error(diagnostico)
            self.editor.marcar_errores([diagnostico])
            if self._errores_vistos == 1 and not educativo:
                self.mostrar_herramienta("problemas")
            if paso.token is None:
                self.editor.ir_a(diagnostico.linea, diagnostico.columna)
        self.barra_estado.establecer_contadores(len(resultado.tokens), self._errores_vistos)
        self.franja_izquierda.poner_contador("problemas", self._errores_vistos)
        if educativo:
            self.mostrar_herramienta("educativo")
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
        self._habilitar_simbolos(True)
        if not resultado.manejador.hay_errores():
            self.editor.indicar_sin_errores()
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
        """Muestra la tabla de simbolos (solo disponible al terminar)."""
        if self.panel_resultados.tabla_simbolos_habilitada():
            self.mostrar_herramienta("simbolos")

    def _habilitar_simbolos(self, activo: bool) -> None:
        """Icono de la franja, enlace de la barra de estado y vista, todo a la vez."""
        self.panel_resultados.habilitar_tabla_simbolos(activo)
        self.franja_derecha.habilitar("simbolos", activo)
        self.barra_estado.habilitar_ver_tabla(activo)
        if not activo and self.panel_resultados.vista_actual == "simbolos":
            self.mostrar_herramienta("tokens")

    # --- tool windows ------------------------------------------------------
    def _zona_visible(self, zona: str) -> bool:
        panel = self._paneles[zona]
        return str(panel) in self._contenedor(zona).panes()

    def _contenedor(self, zona: str) -> ttk.Panedwindow:
        return self.cuerpo if zona == "inferior" else self.superior

    def _refrescar_franjas(self) -> None:
        """El icono de la vista visible de cada zona queda resaltado."""
        activas = {z: self._paneles[z].vista_actual for z in self._paneles if self._zona_visible(z)}
        self.franja_izquierda.marcar([activas.get("izquierda"), activas.get("inferior")])
        self.franja_derecha.marcar([activas.get("derecha")])

    def mostrar_herramienta(self, nombre: str) -> None:
        """Deja visible la zona de `nombre` con esa vista."""
        zona = _HERRAMIENTAS[nombre]
        self._paneles[zona].mostrar(nombre)
        if not self._zona_visible(zona):
            self._mostrar_zona(zona)
        self._refrescar_franjas()

    def alternar_herramienta(self, nombre: str) -> None:
        """Clic en un icono: si su vista ya se ve, oculta la zona; si no, la muestra."""
        zona = _HERRAMIENTAS[nombre]
        if self._zona_visible(zona) and self._paneles[zona].vista_actual == nombre:
            self._ocultar_zona(zona)
        else:
            self.mostrar_herramienta(nombre)

    def _ocultar_zona(self, zona: str) -> None:
        """Quita la zona del Panedwindow guardando su tamano (el editor nunca se oculta)."""
        if not self._zona_visible(zona):
            return
        panel = self._paneles[zona]
        self._tamanos[zona] = panel.winfo_height() if zona == "inferior" else panel.winfo_width()
        self._contenedor(zona).forget(panel)
        self._refrescar_franjas()

    def _mostrar_zona(self, zona: str) -> None:
        """Vuelve a poner la zona en su sitio y restaura su tamano cuando Tk la haya medido."""
        panel, contenedor = self._paneles[zona], self._contenedor(zona)
        if zona == "izquierda":
            contenedor.insert(0, panel, weight=0)
        else:
            contenedor.add(panel, weight=2 if zona == "derecha" else 1)
        self.after_idle(lambda: self._restaurar_tamano(zona))

    def _restaurar_tamano(self, zona: str) -> None:
        contenedor = self._contenedor(zona)
        tamano = self._tamanos.get(zona, 250)
        try:
            if zona == "izquierda":
                contenedor.sashpos(0, tamano)
            elif zona == "derecha":
                contenedor.sashpos(len(contenedor.panes()) - 2, contenedor.winfo_width() - tamano)
            else:
                contenedor.sashpos(0, contenedor.winfo_height() - tamano)
        except tk.TclError:
            pass  # la ventana aun no tiene medidas: Tk reparte por pesos

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
