"""Pruebas del rediseno visual estilo PyCharm (Fase C, tareas B11-B15; arquitectura §16)."""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
CORRECTO = str(RAIZ / "ejemplos" / "correcto.flow")
INCORRECTO = str(RAIZ / "ejemplos" / "incorrecto.flow")


def _hay_tk() -> bool:
    """Igual que en test_ui_humo (D-38): Tk se comprueba en un subproceso."""
    try:
        r = subprocess.run([sys.executable, "-c", "import tkinter; tkinter.Tk().destroy()"],
                           capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


HAY_TK = _hay_tk()
CLAVES_TEMA = {
    "fondo", "panel", "barra", "borde", "texto", "texto_codigo", "texto_secundario", "texto_tenue",
    "numero_linea", "blanco", "acento", "acento_claro", "seleccion", "seleccion_fila", "activo",
    "deslizador", "linea_actual", "error", "exito", "detener", "advertencia", "info", "colision", "ayuda_fondo"}


@unittest.skipUnless(importlib.util.find_spec("_tkinter"), "el modulo tkinter no esta instalado")
class TestPaletaYReglas(unittest.TestCase):
    """B11: importan tkinter (ui.estilos) pero no abren ninguna ventana."""

    def test_tema_tiene_las_24_claves_y_son_colores(self):
        from ui.estilos import COLORES_TOKEN, TEMA
        self.assertTrue(CLAVES_TEMA <= set(TEMA))
        for valor in list(TEMA.values()) + list(COLORES_TOKEN.values()):
            self.assertRegex(valor, r"^#[0-9A-Fa-f]{6}$")

    def test_colores_por_tipo_de_token_completos(self):
        from core.modelos import TipoToken
        from ui.estilos import COLORES_TOKEN, TIPOS_EN_CURSIVA
        self.assertEqual(set(COLORES_TOKEN), set(TipoToken))
        self.assertEqual(TIPOS_EN_CURSIVA, (TipoToken.COMENTARIO,))

    def test_solo_estilos_escribe_colores_y_no_quedan_pestanas(self):
        for archivo in (RAIZ / "ui").glob("*.py"):
            texto = archivo.read_text(encoding="utf-8")
            if archivo.name != "estilos.py":
                self.assertIsNone(re.search(r"#[0-9a-fA-F]{6}", texto), archivo.name)
            self.assertNotIn("Notebook", texto, archivo.name)
            self.assertNotIn("seleccionar_pestana", texto, archivo.name)

    def test_puntos_de_las_fuentes(self):
        from ui import estilos
        with mock.patch.object(estilos.sys, "platform", "darwin"):
            self.assertEqual(estilos._puntos(13), 13)
        with mock.patch.object(estilos.sys, "platform", "linux"):
            self.assertEqual(estilos._puntos(13), 10)


@unittest.skipUnless(HAY_TK, "tkinter o pantalla no disponibles")
class TestRediseno(unittest.TestCase):
    def setUp(self):
        from ui import interfaz
        self.interfaz = interfaz
        parches = [mock.patch.object(interfaz, "messagebox"), mock.patch.object(interfaz, "filedialog")]
        self.messagebox, self.filedialog = [p.start() for p in parches]
        for p in parches:
            self.addCleanup(p.stop)
        self.messagebox.askyesno.return_value = False
        self.v = interfaz.VentanaPrincipal(solicitar_archivo=False)
        self.addCleanup(self.v.destroy)

    def bombear(self, condicion, limite=30.0):
        fin = time.time() + limite
        while not condicion() and time.time() < fin:
            self.v.update()
            time.sleep(0.002)
        self.assertTrue(condicion(), "la condición no se cumplió a tiempo")

    def terminar(self, ruta):
        self.v.abrir_archivo(ruta)
        self.v.analizar()
        self.bombear(lambda: self.v.estado == "TERMINADO")

    @staticmethod
    def filas(arbol):
        return len(arbol.get_children())

    # --- B12: iconos y piezas base ----------------------------------------------
    def test_todos_los_iconos_se_dibujan(self):
        import tkinter as tk
        from ui import iconos
        lienzo = tk.Canvas(self.v)
        self.assertEqual(len(iconos.TRAZOS), 16)
        for nombre in iconos.TRAZOS:
            self.assertGreaterEqual(len(iconos.dibujar(lienzo, nombre, 0, 0, "#ffffff")), 1, nombre)

    def test_imagen_de_arbol_16x16(self):
        from ui import iconos
        foto = iconos.imagen("carpeta", self.v)
        self.assertEqual((foto.width(), foto.height()), (16, 16))

    def test_boton_icono_deshabilitado_no_ejecuta(self):
        from ui.componentes import BotonIcono
        llamadas = []
        boton = BotonIcono(self.v, "abrir", lambda: llamadas.append(1))
        boton.invocar()
        boton.habilitar(False)
        boton.invocar()
        self.assertEqual(llamadas, [1])
        relleno = BotonIcono(self.v, "analizar", relleno="exito")
        relleno.habilitar(False)
        self.assertEqual(len(relleno.find_all()), len(__import__("ui.iconos", fromlist=["x"]).TRAZOS["analizar"]))

    def test_panel_herramientas_cambia_de_vista_y_titulo(self):
        from tkinter import ttk
        from ui.componentes import PanelHerramientas
        panel = PanelHerramientas(self.v)
        panel.agregar_vista("a", "Vista A", ttk.Frame(panel.cuerpo))
        panel.agregar_vista("b", "Vista B", ttk.Frame(panel.cuerpo))
        self.assertEqual(panel.vista_actual, "a")
        panel.mostrar("b")
        self.assertEqual(panel.vista_actual, "b")
        self.assertEqual(panel._titulo.cget("text"), "Vista B")

    def test_franja_contador_no_falla(self):
        self.v.franja_izquierda.poner_contador("problemas", 3)
        self.v.franja_izquierda.poner_contador("problemas", 0)

    # --- B13: barra superior y barra de estado -------------------------------------
    def test_migas_de_pan(self):
        self.v.abrir_archivo("ejemplos/correcto.flow")
        texto = self.v.barra_estado.texto_ruta()
        self.assertEqual(texto, f"{RAIZ.name} › ejemplos › correcto.flow")
        self.assertIn("1:1", self.v.barra_estado._posicion.cget("text"))
        self.v.limpiar()
        self.assertEqual(self.v.barra_estado.texto_ruta(), RAIZ.name)

    def test_botones_habilitados_por_estado(self):
        for estado, nombres in self.interfaz._BOTONES_POR_ESTADO.items():
            self.v._actualizar_estado(estado)
            activos = {n for n, b in self.v.barra.botones.items() if b.habilitado}
            self.assertEqual(activos, set(nombres), estado)
        self.assertEqual(set(self.v.barra.botones),
                         {"abrir", "guardar", "analizar", "paso", "detener", "limpiar", "ayuda"})

    def test_menu_de_ejecucion_copia_el_estado(self):
        self.v.abrir_archivo(CORRECTO)
        menu = self.v.barra.menu_ejecucion
        self.v.barra.llenar_menu(menu, "ejecucion")
        estados = {menu.entrycget(i, "label"): menu.entrycget(i, "state") for i in range(menu.index("end") + 1)}
        self.assertEqual(estados["Detener"], "disabled")
        self.assertEqual(estados["Analizar"], "normal")

    def test_atajos_siguen_registrados(self):
        enlazados = self.v.bind_all()
        for secuencia in ("<Key-F5>", "<Key-F10>", "<Key-Escape>", "<Key-F1>", "<Key-F2>", "<Shift-Key-F2>",
                          "<Control-Key-o>", "<Control-Key-s>"):
            self.assertIn(secuencia, enlazados)

    # --- B14: tool windows --------------------------------------------------------
    def test_alternar_oculta_y_muestra_cada_zona(self):
        v = self.v
        v.update()
        for nombre, zona in (("proyecto", "izquierda"), ("tokens", "derecha"), ("consola", "inferior")):
            v.alternar_herramienta(nombre)
            v.update()
            self.assertFalse(v._zona_visible(zona), nombre)
            v.alternar_herramienta(nombre)
            v.update()
            self.assertTrue(v._zona_visible(zona), nombre)
            medida = v._paneles[zona].winfo_height() if zona == "inferior" else v._paneles[zona].winfo_width()
            self.assertGreaterEqual(medida, 150, nombre)

    def test_cambiar_de_vista_no_oculta(self):
        self.v.alternar_herramienta("lenguaje")
        self.assertTrue(self.v._zona_visible("izquierda"))
        self.assertEqual(self.v.panel_lateral.vista_actual, "lenguaje")

    def test_requisito_5_errores_durante_la_evaluacion(self):
        v = self.v
        v.abrir_archivo(INCORRECTO)
        v.analizar()
        self.bombear(lambda: self.filas(v.problemas.arbol_errores) >= 1)
        v.detener()
        self.assertEqual(v.inferior.vista_actual, "problemas")
        self.assertGreaterEqual(self.filas(v.problemas.arbol_errores), 1)
        self.assertGreater(v.franja_izquierda._botones["problemas"]._contador, 0)
        self.assertFalse(v.sesion.terminada)
        self.assertFalse(v.franja_derecha._botones["simbolos"].habilitado)
        v.ver_tabla_simbolos()
        self.assertNotEqual(v.panel_resultados.vista_actual, "simbolos")

    def test_requisito_5_oferta_final_de_la_tabla(self):
        self.messagebox.askyesno.return_value = True
        self.terminar(INCORRECTO)
        self.messagebox.askyesno.assert_called_once()
        self.assertTrue(self.v.franja_derecha._botones["simbolos"].habilitado)
        self.assertEqual(self.v.panel_resultados.vista_actual, "simbolos")
        self.v.mostrar_herramienta("tokens")
        self.v.ver_tabla_simbolos()
        self.assertEqual(self.v.panel_resultados.vista_actual, "simbolos")

    def test_requisito_6_pide_archivo_con_el_diseno_nuevo(self):
        self.filedialog.askopenfilename.return_value = CORRECTO
        v = self.interfaz.VentanaPrincipal(solicitar_archivo=True)
        self.addCleanup(v.destroy)
        fin = time.time() + 10
        while v.estado != "LISTO" and time.time() < fin:
            v.update()
            time.sleep(0.005)
        self.assertEqual(v.estado, "LISTO")
        self.assertEqual(v.editor._nombre.cget("text"), "correcto.flow")

    def test_paso_a_paso_muestra_el_modo_educativo(self):
        self.v.alternar_herramienta("tokens")  # oculta la zona derecha
        self.v.abrir_archivo(CORRECTO)
        self.v.paso_a_paso()
        self.assertTrue(self.v._zona_visible("derecha"))
        self.assertEqual(self.v.panel_resultados.vista_actual, "educativo")

    def test_arbol_de_proyecto_y_referencias_de_imagenes(self):
        from application.archivos import listar_ejemplos
        self.v.abrir_archivo(CORRECTO)
        lista = self.v.panel_lateral.lista
        carpeta = lista.get_children(lista.get_children()[0])[0]
        archivos = lista.get_children(carpeta)
        self.assertEqual(len(archivos), len(listar_ejemplos()))
        seleccion = lista.selection()
        self.assertEqual(lista.item(seleccion[0], "text").strip(), "correcto.flow")
        self.assertEqual(set(self.v.panel_lateral._imagenes), {"carpeta", "archivo"})

    # --- B15: editor ---------------------------------------------------------------
    def test_inspeccion_y_navegacion_de_errores(self):
        v = self.v
        self.terminar(INCORRECTO)
        e = v.editor
        self.assertTrue(e._lbl_estado.cget("text").startswith("✗"))
        self.assertEqual(e._lbl_estado.cget("text"), f"✗ {len(e._marcas)}")
        e.ir_a(1, 1)
        e.ir_a_error(1)
        self.assertEqual(e.posicion_cursor(), (2, 12))
        e.ir_a_error(1)
        self.assertEqual(e.posicion_cursor(), (2, 18))
        e.ir_a(1, 1)
        e.ir_a_error(-1)
        self.assertEqual(e.posicion_cursor(), max(e._marcas))

    def test_inspeccion_ok_y_oculta(self):
        v = self.v
        self.terminar(CORRECTO)
        self.assertEqual(v.editor._lbl_estado.cget("text"), "✓")
        self.assertTrue(v.editor._inspeccion.winfo_manager())
        v.limpiar()
        self.assertFalse(v.editor._inspeccion.winfo_manager())

    def test_comentarios_en_cursiva_y_pestana(self):
        import tkinter.font as tkfont
        from core.modelos import TipoToken
        e = self.v.editor
        fuente = tkfont.Font(font=e.texto.tag_cget(e._etiqueta(TipoToken.COMENTARIO), "font"))
        self.assertEqual(fuente.actual("slant"), "italic")
        self.assertEqual(e._nombre.cget("text"), "sin título")
        self.v.abrir_archivo(CORRECTO)
        self.assertEqual(e._nombre.cget("text"), "correcto.flow")
        self.v.limpiar()
        self.assertEqual(e._nombre.cget("text"), "sin título")


if __name__ == "__main__":
    unittest.main()
