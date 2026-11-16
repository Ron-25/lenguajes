"""Ventana principal: coordina las vistas y avanza la sesión de análisis con `after`."""
from __future__ import annotations

import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from application.analisis_service import SesionAnalisis, explicar_token, tokenizar
from application.archivos import ErrorArchivo, cargar_fuente, crear_fuente, guardar_fuente
from config import reglas
from core.modelos import Diagnostico, Token
from ui.componentes import PAUSA_MAXIMA_MS, PAUSA_POR_DEFECTO_MS, RAIZ_PROYECTO, BarraEstado, Cabecera
from ui.editor import EditorCodigo
from ui.estilos import aplicar_tema
from ui.paneles import PanelErrores, PanelResultados

DURACION_MAXIMA_ANIMACION_MS = 10000  # tope de la animación completa: en archivos largos se acorta la pausa por línea
PASOS_MAXIMOS_POR_TICK = 500          # una línea larguísima no debe bloquear la ventana
PRESUPUESTO_TICK_S = 0.03             # si el reloj va atrasado, el latido agrupa líneas hasta 30 ms y cede para repintar
TITULO_SOLICITUD = "Seleccione el archivo con las cadenas de entrada"

SIN_FUENTE, LISTO, ANALIZANDO, TERMINADO = "SIN_FUENTE", "LISTO", "ANALIZANDO", "TERMINADO"
_BOTONES_POR_ESTADO = {
    SIN_FUENTE: ("nuevo", "abrir", "analizar", "ayuda"),
    LISTO: ("nuevo", "abrir", "guardar", "analizar", "paso", "limpiar", "ayuda"),
    ANALIZANDO: ("nuevo", "abrir", "analizar", "paso", "detener", "limpiar", "ayuda"),
    TERMINADO: ("nuevo", "abrir", "guardar", "analizar", "paso", "limpiar", "ayuda"),
}
_AYUDA = (
    "SmartLex Studio — analizador léxico de FlowLang 1.0\n\n"
    "Ctrl+N  Nuevo archivo\nCtrl+O  Abrir archivo (.flow / .txt)\nCtrl+S  Guardar\n"
    "F5  Analizar (evaluación progresiva)\nF10  Paso a paso (pestaña Autómatas)\n"
    "Esc  Detener\nF1  Esta ayuda\nF2 / Shift+F2  Siguiente / anterior error\n\n"
    "Pausa por línea: el deslizador fija cuánto espera el análisis entre una línea y la siguiente.\n"
    "Margen del editor: ✓ línea evaluada sin errores, ✗ línea con errores.\n"
    "Clic en un token: ver cómo se reconoció (pestaña Autómatas).\nDoble clic en un error: ir a su posición.\n"
    "Al terminar se ofrece ver la tabla de símbolos.")


class VentanaPrincipal(tk.Tk):
    """Ventana de SmartLex Studio. Los métodos públicos son los que usan los atajos, los botones y las pruebas."""

    def __init__(self, solicitar_archivo: bool = True) -> None:
        super().__init__()
        self.estado = SIN_FUENTE
        self.sesion: SesionAnalisis | None = None
        self.ruta_actual: Path | None = None
        self._id_tick: str | None = None
        self._errores_vistos = 0
        self._linea_en_curso = 0   # última línea que el análisis ya empezó (0 = ninguna)
        self._lineas_fuente = 1
        self._ritmo = (0.0, 0, -1)  # (instante de referencia, líneas animadas desde entonces, pausa usada)
        self._texto_guardado = ""  # texto del editor en la última carga o guardado, para detectar cambios
        aplicar_tema(self)
        self._configurar_ventana()
        self._construir()
        self._registrar_atajos()
        self._poner_titulo()
        self._actualizar_estado(SIN_FUENTE)
        self.protocol("WM_DELETE_WINDOW", self.salir)
        if solicitar_archivo:
            self.after(100, self._solicitar_archivo_inicial)

    def destroy(self) -> None:
        """Cancela los `after` pendientes (latido, espera del editor, desplazamientos) antes de destruir.

        Si no, Tcl los ejecuta después y escribe «invalid command name … ("after" script)».
        """
        try:
            pendientes = self.tk.splitlist(self.tk.call("after", "info"))
        except tk.TclError:
            pendientes = ()
        for identificador in pendientes:
            # se cancela directo en Tcl; cada widget borra su propio comando al destruirse
            self.tk.call("after", "cancel", identificador)
        self._id_tick = None
        super().destroy()

    def _configurar_ventana(self) -> None:
        ancho = min(1280, self.winfo_screenwidth())
        alto = min(800, self.winfo_screenheight() - 60)
        self.geometry(f"{ancho}x{alto}")
        self.minsize(min(1100, ancho), min(650, alto))
        self.title("SmartLex Studio")

    def _construir(self) -> None:
        """Cabecera arriba; editor y manejador de errores en el medio; pestañas de resultados y barra de estado abajo."""
        self.cabecera = Cabecera(self, {
            "nuevo": self.nuevo_archivo, "abrir": self.abrir_archivo, "guardar": self.guardar_archivo,
            "analizar": self.analizar, "paso": self.paso_a_paso, "detener": self.detener,
            "limpiar": self.limpiar, "ayuda": self.mostrar_ayuda}, self.abrir_archivo, self.ver_tabla_simbolos)
        self.barra_estado = BarraEstado(self)
        self.cabecera.pack(side="top", fill="x")
        self.barra_estado.pack(side="bottom", fill="x")
        self.cuerpo = ttk.Panedwindow(self, orient="vertical")
        self.cuerpo.pack(fill="both", expand=True, padx=12, pady=(10, 8))
        self.superior = ttk.Panedwindow(self.cuerpo, orient="horizontal")
        self.editor = EditorCodigo(self.superior, al_cambiar=self._al_editar,
                                   al_mover_cursor=self.barra_estado.establecer_posicion)
        self.panel_errores = PanelErrores(self.superior, self._al_seleccionar_error)
        self.panel_resultados = PanelResultados(self.cuerpo, self._al_seleccionar_token)
        self.consola = self.panel_resultados.consola
        self.superior.add(self.editor, weight=3)
        self.superior.add(self.panel_errores, weight=2)
        self.cuerpo.add(self.superior, weight=3)
        self.cuerpo.add(self.panel_resultados, weight=2)
        self._colocar_divisores()

    def _colocar_divisores(self) -> None:
        """Tamaños iniciales: errores 38 % del ancho y resultados 40 % del alto; los divisores se pueden arrastrar."""
        self.update_idletasks()
        ancho, alto = self.superior.winfo_width(), self.cuerpo.winfo_height()
        self.superior.sashpos(0, ancho - int(ancho * 0.38))
        self.cuerpo.sashpos(0, alto - int(alto * 0.40))

    def _registrar_atajos(self) -> None:
        atajos = {"<Control-n>": self.nuevo_archivo, "<Control-o>": self.abrir_archivo, "<Control-s>": self.guardar_archivo,
                  "<F5>": self.analizar, "<F10>": self.paso_a_paso, "<Escape>": self.detener,
                  "<F1>": self.mostrar_ayuda, "<F2>": lambda: self.editor.ir_a_error(1),
                  "<Shift-F2>": lambda: self.editor.ir_a_error(-1)}
        if sys.platform == "darwin":
            atajos.update({"<Command-n>": self.nuevo_archivo, "<Command-o>": self.abrir_archivo, "<Command-s>": self.guardar_archivo})
        for secuencia, accion in atajos.items():
            self.bind_all(secuencia, lambda _e, f=accion: f())
        # El Text de Tk inserta un salto de línea con Ctrl+O; "break" evita que además de abrir el archivo lo haga
        self.editor.texto.bind("<Control-o>", lambda _e: (self.abrir_archivo(), "break")[1])

    def _actualizar_estado(self, estado: str, mensaje: str | None = None) -> None:
        self.estado = estado
        self.cabecera.habilitar(_BOTONES_POR_ESTADO[estado])
        textos = {SIN_FUENTE: "Sin archivo", LISTO: "Listo para analizar",
                  ANALIZANDO: "Analizando…", TERMINADO: "Análisis terminado"}
        self.barra_estado.establecer_estado(mensaje or textos[estado])

    def _poner_titulo(self) -> None:
        """Título de la ventana y del editor."""
        nombre = f" — {self.ruta_actual.name}" if self.ruta_actual else ""
        self.title(f"SmartLex Studio{nombre}")
        self.editor.establecer_nombre(self.ruta_actual.name if self.ruta_actual else None)

    def _cancelar_temporizador(self) -> None:
        if self._id_tick is not None:
            self.after_cancel(self._id_tick)
            self._id_tick = None

    def _reiniciar_resultados(self) -> None:
        self._cancelar_temporizador()
        self.sesion = None
        self._errores_vistos = 0
        self.panel_resultados.limpiar()
        self.panel_errores.limpiar()
        self._habilitar_simbolos(False)
        self.barra_estado.establecer_contadores(0, 0, 0, 0, 0)
        self.barra_estado.establecer_veredicto(None)
        self.editor.limpiar_marcas()
        self.editor.solo_lectura(False)

    def _solicitar_archivo_inicial(self) -> None:
        if self.estado == SIN_FUENTE and not self.editor.obtener_texto().strip():
            self.abrir_archivo()

    def _confirmar_descartar(self, titulo: str) -> bool:
        """True si se puede continuar: no hay cambios sin guardar, o el usuario los guardó o los descartó."""
        if self.editor.obtener_texto() == self._texto_guardado:
            return True
        respuesta = messagebox.askyesnocancel(titulo, "Hay cambios sin guardar. ¿Guardarlos antes de continuar?")
        if respuesta is None:
            return False
        if respuesta:
            self.guardar_archivo()
            return self.editor.obtener_texto() == self._texto_guardado  # sigue distinto si se canceló el guardado
        return True

    def abrir_archivo(self, ruta=None) -> None:
        """Abre un archivo (pide la ruta si no se da) y lo muestra en el editor."""
        if not self._confirmar_descartar("Abrir archivo"):
            return
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
        self._mostrar_fuente(Path(ruta), texto)

    def _mostrar_fuente(self, ruta: Path, texto: str) -> None:
        """Pone `texto` en el editor como el archivo abierto `ruta`; lo comparten abrir y crear."""
        self._reiniciar_resultados()
        self.editor.establecer_texto(texto)
        self.editor.resaltar(tokenizar(self.editor.obtener_texto()))
        self._texto_guardado = self.editor.obtener_texto()
        self.ruta_actual = ruta
        self._poner_titulo()
        self.consola.escribir(f"Archivo cargado: {ruta.name} ({len(texto)} caracteres)", "info")
        self._actualizar_estado(LISTO)

    def nuevo_archivo(self) -> None:
        """Crea un archivo con la plantilla mínima; antes pregunta por cambios sin guardar y por la ruta."""
        if not self._confirmar_descartar("Nuevo archivo"):
            return
        carpeta = self.ruta_actual.parent if self.ruta_actual else RAIZ_PROYECTO / "ejemplos"
        ruta = filedialog.asksaveasfilename(
            title="Nuevo archivo FlowLang", defaultextension=reglas.EXTENSIONES_PERMITIDAS[0],
            initialdir=str(carpeta), initialfile="nuevo" + reglas.EXTENSIONES_PERMITIDAS[0],
            filetypes=[("FlowLang", " ".join("*" + e for e in reglas.EXTENSIONES_PERMITIDAS))])
        if not ruta:
            return
        try:
            texto = crear_fuente(ruta)
        except ErrorArchivo as error:
            self._mostrar_error_archivo(error.diagnostico)
            return
        self._mostrar_fuente(Path(ruta), texto)
        self.editor.ir_a(2, len(texto.splitlines()[1]) + 1)  # al final de la línea sangrada de la plantilla

    def _mostrar_error_archivo(self, diagnostico: Diagnostico) -> None:
        self.consola.escribir(f"✗ {diagnostico.codigo} {diagnostico.mensaje} {diagnostico.sugerencia}", "error")
        self.panel_errores.quitar_errores_de_archivo()
        self.panel_errores.agregar_error(diagnostico)
        messagebox.showerror(diagnostico.titulo, f"{diagnostico.mensaje}\n\n{diagnostico.sugerencia}")

    def guardar_archivo(self) -> None:
        """Guarda el editor; pide la ruta si el archivo es nuevo."""
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
        self._texto_guardado = self.editor.obtener_texto()
        self._poner_titulo()
        self.consola.escribir(f"Guardado: {ruta.name}", "info")

    def _sincronizar_con_texto(self) -> None:
        """Si se escribió texto sin abrir archivo, el editor ya sirve como fuente."""
        if self.estado == SIN_FUENTE and self.editor.obtener_texto().strip():
            self._actualizar_estado(LISTO)

    def _iniciar_sesion(self) -> None:
        fuente = self.editor.obtener_texto()
        self.editor.descartar_cambio_pendiente()
        self._reiniciar_resultados()
        self.sesion = SesionAnalisis(fuente)
        self._linea_en_curso = 0
        self._lineas_fuente = fuente.count("\n") + 1
        self.editor.solo_lectura(True)
        self.consola.limpiar()
        self.panel_resultados.mostrar("tokens")
        self.consola.escribir(f"Analizando {self.ruta_actual.name if self.ruta_actual else 'texto del editor'}…", "info")
        self._actualizar_estado(ANALIZANDO)

    def analizar(self) -> None:
        """Inicia o continúa la evaluación progresiva con un temporizador."""
        self._sincronizar_con_texto()
        if self.estado == SIN_FUENTE:
            self.abrir_archivo()
            return
        if self._id_tick is not None:
            return
        if self.estado != ANALIZANDO:
            self._iniciar_sesion()
        self.panel_resultados.mostrar("tokens")
        self._ritmo = (time.monotonic(), 0, self._pausa_efectiva())
        self._id_tick = self.after(1, self._tick)

    def _pausa_efectiva(self) -> int:
        """Pausa entre líneas: la del deslizador, acortada para que un archivo largo no pase del tope."""
        return min(self.cabecera.pausa_ms(), DURACION_MAXIMA_ANIMACION_MS // max(1, self._lineas_fuente))

    def _atrasado(self) -> bool:
        """True si el reloj va por detrás del ritmo `líneas × pausa`.

        El trabajo de cada línea se suma a la pausa, así que sin esto la animación duraría más
        de lo que marca el deslizador. Si el deslizador cambia, el ritmo se reinicia.
        """
        pausa = self._pausa_efectiva()
        inicio, lineas, pausa_usada = self._ritmo
        if pausa != pausa_usada:
            self._ritmo = (time.monotonic(), 0, pausa)
            return pausa == 0
        return pausa == 0 or (time.monotonic() - inicio) * 1000 > lineas * pausa

    def _tick(self) -> None:
        """Un latido: consume pasos hasta terminar la línea en curso y espera la pausa.

        Si va atrasado, sigue con la línea siguiente sin esperar, pero cede a Tk al pasar
        PRESUPUESTO_TICK_S para que la ventana se repinte.
        """
        self._id_tick = None
        linea = self._linea_en_curso
        limite = time.monotonic() + PRESUPUESTO_TICK_S
        for _ in range(PASOS_MAXIMOS_POR_TICK):
            if not self._consumir_paso(educativo=False):
                return
            if self._linea_en_curso != linea:
                inicio, lineas, pausa_usada = self._ritmo
                self._ritmo = (inicio, lineas + 1, pausa_usada)
                linea = self._linea_en_curso
                if not self._atrasado() or time.monotonic() >= limite:
                    self._id_tick = self.after(max(1, self._pausa_efectiva()), self._tick)
                    return
        self._id_tick = self.after(1, self._tick)

    def paso_a_paso(self) -> None:
        """Consume un solo paso y lo explica en la pestaña Autómatas."""
        self._sincronizar_con_texto()
        if self.estado == SIN_FUENTE:
            self.abrir_archivo()
            return
        self._cancelar_temporizador()
        if self.estado != ANALIZANDO:
            self._iniciar_sesion()
        self._consumir_paso(educativo=True)

    def detener(self) -> None:
        """Pausa la evaluación; Analizar y Paso a paso la continúan."""
        if self._id_tick is not None:
            self._cancelar_temporizador()
            self._actualizar_estado(ANALIZANDO, "Evaluación detenida (F5 continúa, F10 avanza un paso)")

    def _consumir_paso(self, educativo: bool) -> bool:
        """Aplica un paso a las vistas, para el temporizador y «Paso a paso»; False cuando la sesión terminó."""
        paso = self.sesion.siguiente_paso()
        if paso is None:
            self._finalizar()
            return False
        resultado = self.sesion.resultado
        if paso.token is not None:
            if paso.token.linea != self._linea_en_curso:
                self._cerrar_linea_en_curso()
                self._linea_en_curso = paso.token.linea
            self.panel_resultados.agregar_token(paso.numero, paso.token)
            self.editor.resaltar_token_actual(paso.token)
        self.consola.escribir(paso.descripcion, "error" if paso.diagnosticos else "normal")
        for diagnostico in paso.diagnosticos:
            self._errores_vistos += 1
            self.panel_errores.agregar_error(diagnostico)
            self.editor.marcar_errores([diagnostico])
            if paso.token is None:
                self.editor.ir_a(diagnostico.linea, diagnostico.columna)
        self.barra_estado.establecer_contadores(*self.editor.conteo_lineas(), len(resultado.tokens),
                                                len(resultado.tabla), self._errores_vistos)
        if educativo:
            self.panel_resultados.mostrar("automatas")
            if paso.token is not None:
                self.panel_resultados.mostrar_explicacion(explicar_token(paso.token, resultado.tabla))
        return True

    def _cerrar_linea_en_curso(self) -> None:
        """La línea que se recorría terminó: recibe su ✓ o su ✗."""
        if self._linea_en_curso > 0:
            self.editor.marcar_lineas_evaluadas([self._linea_en_curso])

    def _finalizar(self) -> None:
        resultado = self.sesion.resultado
        self._cancelar_temporizador()
        self._cerrar_linea_en_curso()
        self.editor.solo_lectura(False)
        self.editor.resaltar_token_actual(None)
        self.consola.escribir("— Fin del análisis —", "info")
        self._veredictos_en_consola(resultado)
        self.panel_resultados.mostrar_estadisticas(resultado)
        self.panel_resultados.mostrar_tabla_simbolos(resultado.tabla)
        self._habilitar_simbolos(True)
        self.barra_estado.establecer_contadores(*self.editor.conteo_lineas(), len(resultado.tokens),
                                                len(resultado.tabla), self._errores_vistos)
        self.barra_estado.establecer_veredicto(resultado.es_valida)
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
        """Muestra la pestaña de la tabla de símbolos, que solo existe al terminar."""
        if self.panel_resultados.tabla_simbolos_habilitada():
            self.panel_resultados.mostrar("simbolos")

    def _habilitar_simbolos(self, activo: bool) -> None:
        """Lo mismo que el botón de la cabecera y la pestaña."""
        self.panel_resultados.habilitar_tabla_simbolos(activo)
        self.cabecera.habilitar_ver_tabla(activo)

    def limpiar(self) -> None:
        """Deja la aplicación sin archivo y sin resultados; pregunta si hay cambios sin guardar."""
        if not self._confirmar_descartar("Limpiar"):
            return
        self._reiniciar_resultados()
        self.editor.limpiar()
        self.consola.limpiar()
        self._texto_guardado = ""
        self.ruta_actual = None
        self._poner_titulo()
        self._actualizar_estado(SIN_FUENTE)

    def salir(self) -> None:
        """Cierra la ventana preguntando por cambios sin guardar; `destroy` no pregunta."""
        if self._confirmar_descartar("Salir"):
            self.destroy()

    def mostrar_ayuda(self) -> None:
        """Muestra los atajos y el modo de uso."""
        messagebox.showinfo("Ayuda de SmartLex Studio", _AYUDA)

    def _al_editar(self) -> None:
        """El usuario cambió el texto: vuelve a colorear y deja obsoletos los resultados."""
        if self.estado == ANALIZANDO:
            return
        texto = self.editor.obtener_texto()
        self.barra_estado.establecer_veredicto(None)
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
