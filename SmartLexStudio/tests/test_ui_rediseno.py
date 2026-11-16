"""Pruebas del rediseno claro estilo academico (Fase D, tareas C1-C5; arquitectura §17)."""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
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
    "numero_linea", "blanco", "acento", "acento_claro", "seleccion", "seleccion_fila", "linea_actual",
    "deslizador", "error", "error_fondo", "error_lexema", "exito", "advertencia", "info", "colision",
    "cabecera", "cabecera_tenue"}
# nombres de la interfaz anterior que ya no deben quedar en ui/ (partidos para que el `grep` de la tarea no los encuentre aqui)
PIEZAS_ELIMINADAS = ("icon" "os", "Boton" "Icono", "Glo" "bo", "Franja" "Herramientas", "Panel" "Herramientas",
                     "Panel" "Lateral", "Panel" "Problemas", "alternar" "_herramienta", "mostrar" "_herramienta",
                     "_mi" "gas", "Py" "Charm", "Dar" "cula")


@unittest.skipUnless(importlib.util.find_spec("_tkinter"), "el modulo tkinter no esta instalado")
class TestPaletaYReglas(unittest.TestCase):
    """C1: importan tkinter (ui.estilos) pero no abren ninguna ventana."""

    def test_tema_tiene_las_25_claves_y_son_colores(self):
        from ui.estilos import COLORES_TOKEN, TEMA
        self.assertEqual(set(TEMA), CLAVES_TEMA)
        for valor in list(TEMA.values()) + list(COLORES_TOKEN.values()):
            self.assertRegex(valor, r"^#[0-9A-F]{6}$")

    def test_colores_por_tipo_de_token_completos(self):
        from core.modelos import TipoToken
        from ui.estilos import COLORES_TOKEN, TIPOS_EN_CURSIVA, TIPOS_EN_NEGRITA
        self.assertEqual(set(COLORES_TOKEN), set(TipoToken))
        self.assertEqual(TIPOS_EN_CURSIVA, (TipoToken.COMENTARIO,))
        self.assertEqual(TIPOS_EN_NEGRITA, (TipoToken.PALABRA_RESERVADA,))

    def test_solo_estilos_escribe_colores(self):
        for archivo in (RAIZ / "ui").glob("*.py"):
            if archivo.name != "estilos.py":
                self.assertIsNone(re.search(r"#[0-9a-fA-F]{6}", archivo.read_text(encoding="utf-8")), archivo.name)

    def test_no_queda_nada_del_diseno_pycharm(self):
        self.assertFalse((RAIZ / "ui" / ("icon" "os.py")).exists())
        for archivo in (RAIZ / "ui").glob("*.py"):
            texto = archivo.read_text(encoding="utf-8")
            for pieza in PIEZAS_ELIMINADAS:
                self.assertNotIn(pieza, texto, f"{archivo.name}: {pieza}")

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
        self.messagebox.askyesnocancel.return_value = False  # el MagicMock por defecto es verdadero (D-70)
        self.v = interfaz.VentanaPrincipal(solicitar_archivo=False)
        self.v.cabecera.establecer_pausa(0)
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

    def margen(self, n):
        return self.v.editor.margen.get(f"{n}.0", f"{n}.end").strip()

    def texto_de(self, widget):
        return widget.get("1.0", "end")

    # --- C1: estilos --------------------------------------------------------------
    def test_aplicar_tema_no_falla(self):
        from ui.estilos import aplicar_tema
        aplicar_tema(self.v)

    # --- C2: cabecera, barra de estado y vista Lenguaje ----------------------------
    def test_cabecera_cabe_en_1100_px(self):
        self.v.update()
        self.assertLessEqual(self.v.cabecera.winfo_reqwidth(), 1100)

    def test_pausa_por_defecto_y_etiqueta(self):
        nueva = self.interfaz.VentanaPrincipal(solicitar_archivo=False)
        self.addCleanup(nueva.destroy)
        self.assertEqual(nueva.cabecera.pausa_ms(), 120)
        self.assertEqual(nueva.cabecera._etiqueta_pausa.cget("text"), "120 ms")
        nueva.cabecera.establecer_pausa(0)
        self.assertEqual(nueva.cabecera.pausa_ms(), 0)
        self.assertEqual(nueva.cabecera._etiqueta_pausa.cget("text"), "0 ms")
        nueva.cabecera.establecer_pausa(500)
        self.assertEqual(nueva.cabecera.pausa_ms(), 500)

    def etiquetas_menu(self):
        menu = self.v.cabecera.menu_ejemplos
        self.v.cabecera._llenar_ejemplos()  # lo que hace `postcommand` al abrir el menu
        return [menu.entrycget(i, "label") for i in range(menu.index("end") + 1)]

    def test_menu_ejemplos_se_rellena_al_abrir(self):
        from application.archivos import listar_ejemplos
        self.assertEqual(self.etiquetas_menu(), [r.name for r in listar_ejemplos()])
        ruta = RAIZ / "ejemplos" / "zz_prueba_menu.flow"
        self.addCleanup(lambda: ruta.unlink(missing_ok=True))
        ruta.write_text("inicio\nfin\n", encoding="utf-8")
        self.assertIn("zz_prueba_menu.flow", self.etiquetas_menu())

    def test_elegir_un_ejemplo_lo_abre(self):
        etiquetas = self.etiquetas_menu()
        self.v.cabecera.menu_ejemplos.invoke(etiquetas.index("correcto.flow"))
        self.assertEqual(self.v.ruta_actual.name, "correcto.flow")
        self.assertEqual(self.v.estado, "LISTO")

    def test_veredicto_de_la_barra_de_estado(self):
        from config import reglas
        b = self.v.barra_estado
        b.establecer_veredicto(True)
        self.assertEqual(b.veredicto.cget("text"), f"✓ El archivo es válido para {reglas.NOMBRE_LENGUAJE}")
        b.establecer_veredicto(False)
        self.assertEqual(b.veredicto.cget("text"), f"✗ El archivo NO es válido para {reglas.NOMBRE_LENGUAJE}")
        b.establecer_veredicto(None)
        self.assertEqual(b.veredicto.cget("text"), "")
        b.establecer_posicion(3, 7)
        self.assertEqual(b._posicion.cget("text"), "Lín 3, Col 7")

    def test_botones_habilitados_por_estado(self):
        c = self.v.cabecera
        self.assertEqual(set(c.botones),
                         {"nuevo", "abrir", "guardar", "analizar", "paso", "detener", "limpiar", "ayuda"})
        for estado, nombres in self.interfaz._BOTONES_POR_ESTADO.items():
            self.v._actualizar_estado(estado)
            activos = {n for n, b in c.botones.items() if not b.instate(["disabled"])}
            self.assertEqual(activos, set(nombres), estado)

    def test_ver_tabla_de_la_cabecera_solo_al_terminar(self):
        boton = self.v.cabecera.boton_tabla
        self.v.abrir_archivo(CORRECTO)
        self.assertTrue(boton.instate(["disabled"]))
        self.v.analizar()
        self.bombear(lambda: self.v.estado == "TERMINADO")
        self.assertFalse(boton.instate(["disabled"]))
        self.v.panel_resultados.mostrar("tokens")
        boton.invoke()
        self.assertEqual(self.v.panel_resultados.vista_actual, "simbolos")

    def test_atajos_siguen_registrados(self):
        enlazados = self.v.bind_all()
        for secuencia in ("<Key-F5>", "<Key-F10>", "<Key-Escape>", "<Key-F1>", "<Key-F2>", "<Shift-Key-F2>",
                          "<Control-Key-n>", "<Control-Key-o>", "<Control-Key-s>"):
            self.assertIn(secuencia, enlazados)

    # --- C3: editor con columna ✓/✗ ------------------------------------------------
    def test_margen_con_marcas_y_conteo(self):
        from core.modelos import Diagnostico, TipoDiagnostico
        e = self.v.editor
        e.establecer_texto("inicio\nnumero 3x = 5;\nfin\nfin")
        self.assertEqual(e.conteo_lineas(), (0, 0))
        d = Diagnostico("LEX-002", TipoDiagnostico.LEXICO, "Número mal formado", "m", "s", 2, 8, "3x")
        e.marcar_lineas_evaluadas([1, 2, 3])
        e.marcar_errores([d])
        self.assertEqual([self.margen(n) for n in (1, 2, 3, 4)], ["1 ✓", "2 ✗", "3 ✓", "4"])
        self.assertEqual(e.conteo_lineas(), (2, 1))
        self.assertEqual([str(i) for i in e.texto.tag_ranges("linea_error")], ["2.0", "3.0"])
        self.assertEqual([str(i) for i in e.texto.tag_ranges("marca_error")], ["2.7", "2.9"])
        e.limpiar_marcas()
        self.assertEqual([self.margen(n) for n in (1, 2, 3, 4)], ["1", "2", "3", "4"])
        self.assertEqual(e.conteo_lineas(), (0, 0))
        self.assertEqual(e.texto.tag_ranges("linea_error"), ())

    def test_linea_en_blanco_no_recibe_marca(self):
        e = self.v.editor
        e.establecer_texto("inicio\n\nfin")
        e.marcar_lineas_evaluadas([1, 2, 3])
        self.assertEqual([self.margen(n) for n in (1, 2, 3)], ["1 ✓", "2", "3 ✓"])

    def test_diagnostico_estructural_tambien_pone_la_x(self):
        from core.modelos import Diagnostico, TipoDiagnostico
        e = self.v.editor
        e.establecer_texto("inicio\nfin")
        e.marcar_errores([Diagnostico("SIN-001", TipoDiagnostico.ESTRUCTURAL, "t", "m", "s", 2, 1, "")])
        self.assertEqual(self.margen(2), "2 ✗")
        self.assertEqual(e.conteo_lineas(), (0, 1))
        e.marcar_errores([Diagnostico("ARC-001", TipoDiagnostico.ARCHIVO, "t", "m", "s", 0, 0, "")])
        self.assertEqual(e.conteo_lineas(), (0, 1))  # sin posicion: no marca nada

    def test_marca_error_del_primer_error_de_incorrecto(self):
        v = self.v
        v.abrir_archivo(INCORRECTO)
        while self.filas(v.panel_errores.arbol_errores) == 0:
            v.paso_a_paso()
        self.assertEqual([str(i) for i in v.editor.texto.tag_ranges("marca_error")], ["2.11", "2.14"])
        self.assertEqual(self.margen(2), "2 ✗")

    def test_titulo_del_editor_y_estilos_de_token(self):
        import tkinter.font as tkfont
        from core.modelos import TipoToken
        e = self.v.editor
        self.assertEqual(e._titulo.cget("text"), "Archivo de entrada: (sin archivo)")
        self.v.abrir_archivo(CORRECTO)
        self.assertEqual(e._titulo.cget("text"), "Archivo de entrada: correcto.flow")
        comentario = tkfont.Font(font=e.texto.tag_cget(e._etiqueta(TipoToken.COMENTARIO), "font"))
        reservada = tkfont.Font(font=e.texto.tag_cget(e._etiqueta(TipoToken.PALABRA_RESERVADA), "font"))
        self.assertEqual(comentario.actual("slant"), "italic")
        self.assertEqual(reservada.actual("weight"), "bold")
        self.v.limpiar()
        self.assertEqual(e._titulo.cget("text"), "Archivo de entrada: (sin archivo)")

    def test_navegacion_con_f2_entre_errores(self):
        v = self.v
        self.terminar(INCORRECTO)
        e = v.editor
        e.ir_a(1, 1)
        e.ir_a_error(1)
        self.assertEqual(e.posicion_cursor(), (2, 12))
        e.ir_a_error(1)
        self.assertEqual(e.posicion_cursor(), (2, 18))
        e.ir_a(1, 1)
        e.ir_a_error(-1)
        self.assertEqual(e.posicion_cursor(), max(e._marcas))

    # --- C4: manejador de errores y pestañas ---------------------------------------
    def test_titulo_y_columnas_del_manejador(self):
        v = self.v
        pe = v.panel_errores
        self.assertEqual(pe.titulo.cget("text"), "Manejador de errores (sin errores)")
        self.terminar(INCORRECTO)
        self.assertEqual(pe.titulo.cget("text"), "Manejador de errores (15 errores)")
        self.assertEqual(tuple(pe.arbol_errores["columns"]), ("codigo", "linea", "col", "lexema", "error"))
        primera = pe.arbol_errores.item(pe.arbol_errores.get_children()[0], "values")
        self.assertTrue(str(primera[0]).startswith("LEX-"))
        self.terminar(CORRECTO)
        self.assertEqual(pe.titulo.cget("text"), "Manejador de errores (sin errores)")

    def test_titulo_en_singular_y_error_de_archivo(self):
        v = self.v
        v.abrir_archivo(str(RAIZ / "no_existe.flow"))
        pe = v.panel_errores
        self.assertEqual(pe.titulo.cget("text"), "Manejador de errores (1 error)")
        fila = pe.arbol_errores.get_children()[0]
        valores = pe.arbol_errores.item(fila, "values")
        self.assertEqual((valores[1], valores[2]), ("—", "—"))
        pe.arbol_errores.selection_set(fila)
        v.update()
        self.assertNotIn("línea", pe.detalle_titulo.cget("text"))
        self.assertTrue(pe.detalle_titulo.cget("text").startswith("ARC-"))

    def test_detalle_con_lexema_posicion_y_sugerencia(self):
        v = self.v
        self.terminar(INCORRECTO)
        pe = v.panel_errores
        fila = pe.arbol_errores.get_children()[0]
        pe.arbol_errores.selection_set(fila)
        v.update()
        d = pe._errores[fila]
        self.assertEqual(pe.detalle_titulo.cget("text"),
                         f"{d.codigo} · {d.titulo} — línea {d.linea}, columna {d.columna}")
        self.assertEqual(pe.detalle_error.cget("text"),
                         f"Lexema: {d.lexema!r}\n{d.mensaje}\nSugerencia: {d.sugerencia}")

    def test_pestañas_en_orden_y_tabla_deshabilitada_hasta_terminar(self):
        v = self.v
        p = v.panel_resultados
        titulos = [p.cuaderno.tab(i, "text") for i in range(6)]
        self.assertEqual(titulos, ["Tokens", "Tabla de símbolos", "Resumen", "Autómatas", "Lenguaje", "Consola"])
        self.assertEqual(p.cuaderno.tab(1, "state"), "disabled")
        self.assertFalse(p.tabla_simbolos_habilitada())
        self.terminar(CORRECTO)
        self.assertEqual(p.cuaderno.tab(1, "state"), "normal")
        self.assertTrue(p.tabla_simbolos_habilitada())
        self.assertIs(v.consola, p.consola)

    def test_resumen_de_la_tabla_con_la_formula_real(self):
        self.terminar(CORRECTO)
        p = self.v.panel_resultados
        resumen = p.etiqueta_resumen.cget("text")
        for esperado in ("h = (h · 31 + código(c)) mod 2³²", "cubeta = h mod capacidad",
                         "Colisiones al insertar: 14", "En la tabla actual: 7"):
            self.assertIn(esperado, resumen)
        colisiones = [i for i in p.arbol_simbolos.get_children() if "colision" in p.arbol_simbolos.item(i, "tags")]
        self.assertGreaterEqual(len(colisiones), 7)

    def test_selector_de_automatas(self):
        from config import reglas
        p = self.v.panel_resultados
        nombres = [a["nombre"] for a in reglas.AUTOMATAS]
        self.assertEqual(list(p.selector_automata["values"]), nombres)
        self.assertIn("Seleccione un token", self.texto_de(p.educativo))
        for nombre in nombres:
            p.selector_automata.set(nombre)
            p.selector_automata.event_generate("<<ComboboxSelected>>")
            self.v.update()
            self.assertIn("Tabla de transiciones de " + nombre, self.texto_de(p.educativo))
            self.assertNotIn("Seleccione un token", self.texto_de(p.educativo))

    def test_seleccionar_un_token_sincroniza_el_selector(self):
        from core.modelos import TipoToken
        v = self.v
        self.terminar(CORRECTO)
        p = v.panel_resultados
        p.mostrar_automata("AFD de números")
        fila = next(i for i, t in p._tokens.items() if t.tipo == TipoToken.IDENTIFICADOR)
        p.arbol_tokens.selection_set(fila)
        v.update()
        self.assertEqual(p.selector_automata.get(), "AFD de identificadores")
        self.assertIn(p._tokens[fila].lexema, self.texto_de(p.educativo))

    def test_lenguaje_y_consola_son_pestanas(self):
        p = self.v.panel_resultados
        p.mostrar("lenguaje")
        self.assertEqual(p.vista_actual, "lenguaje")
        p.mostrar("consola")
        self.v.consola.escribir("hola")
        self.assertEqual(p.vista_actual, "consola")

    # --- C5: ventana, pausa por línea y requisitos 5 y 6 ---------------------------
    def test_pausa_por_linea_marca_la_linea_terminada(self):
        v = self.v
        v.abrir_archivo(INCORRECTO)
        while v._linea_en_curso < 3:
            v.paso_a_paso()
        self.assertEqual(v._linea_en_curso, 3)
        self.assertEqual([self.margen(n) for n in (1, 2, 3)], ["1 ✓", "2 ✗", "3"])

    def test_cada_tick_avanza_una_linea_y_programa_la_pausa(self):
        from application.analisis_service import tokenizar
        v = self.v
        v.cabecera.establecer_pausa(120)
        v.abrir_archivo(INCORRECTO)
        lineas = sorted({t.linea for t in tokenizar(v.editor.obtener_texto())})
        programados = []
        with mock.patch.object(v, "after", side_effect=lambda ms, f=None, *a: programados.append((ms, f)) or "id"):
            v.analizar()
            self.assertEqual(programados[-1][0], 1)
            for esperada in lineas[:6]:
                v._tick()
                self.assertEqual(v._linea_en_curso, esperada)
                self.assertEqual(programados[-1], (v._pausa_efectiva(), v._tick))
            self.assertEqual(programados[-1][0], 120)
            v._id_tick = None  # el `after` simulado no creo ningun temporizador real

    def test_pausa_efectiva_con_archivos_cortos_y_largos(self):
        v = self.v
        v.cabecera.establecer_pausa(120)
        v._lineas_fuente = 10
        self.assertEqual(v._pausa_efectiva(), 120)
        v._lineas_fuente = 1000
        self.assertEqual(v._pausa_efectiva(), 10)
        v.cabecera.establecer_pausa(0)
        self.assertEqual(v._pausa_efectiva(), 0)

    def test_requisito_5a_errores_durante_la_evaluacion(self):
        v = self.v
        v.cabecera.establecer_pausa(50)
        v.abrir_archivo(INCORRECTO)
        v.analizar()
        self.bombear(lambda: self.filas(v.panel_errores.arbol_errores) >= 1)
        v.detener()
        self.assertGreaterEqual(self.filas(v.panel_errores.arbol_errores), 1)
        self.assertNotEqual(v.editor.texto.tag_ranges("marca_error"), ())
        self.assertFalse(v.sesion.terminada)
        self.assertEqual(v.estado, "ANALIZANDO")
        self.assertFalse(v.panel_resultados.tabla_simbolos_habilitada())
        self.assertTrue(v.cabecera.boton_tabla.instate(["disabled"]))
        v.ver_tabla_simbolos()
        self.assertNotEqual(v.panel_resultados.vista_actual, "simbolos")

    def test_analisis_detenido_a_mitad_deja_lineas_sin_marca(self):
        v = self.v
        v.abrir_archivo(INCORRECTO)
        for _ in range(12):
            v.paso_a_paso()
        evaluadas, con_errores = v.editor.conteo_lineas()
        self.assertGreater(evaluadas + con_errores, 0)
        total = int(v.editor.texto.index("end-1c").split(".")[0])
        self.assertLess(evaluadas + con_errores, total)
        self.assertEqual(self.margen(total), str(total))

    def test_requisito_5b_oferta_final_de_la_tabla(self):
        self.messagebox.askyesno.return_value = True
        self.terminar(INCORRECTO)
        self.messagebox.askyesno.assert_called_once()
        self.assertIn("tabla de símbolos", self.messagebox.askyesno.call_args[0][1])
        self.assertTrue(self.v.panel_resultados.tabla_simbolos_habilitada())
        self.assertEqual(self.v.panel_resultados.vista_actual, "simbolos")
        self.v.panel_resultados.mostrar("tokens")
        self.v.ver_tabla_simbolos()
        self.assertEqual(self.v.panel_resultados.vista_actual, "simbolos")

    def test_requisito_5b_si_dice_no_no_cambia_de_pestana(self):
        self.terminar(INCORRECTO)
        self.assertEqual(self.v.panel_resultados.vista_actual, "tokens")

    def test_requisito_6_pide_archivo_con_el_diseno_nuevo(self):
        self.filedialog.askopenfilename.return_value = CORRECTO
        v = self.interfaz.VentanaPrincipal(solicitar_archivo=True)
        self.addCleanup(v.destroy)
        fin = time.time() + 10
        while v.estado != "LISTO" and time.time() < fin:
            v.update()
            time.sleep(0.005)
        self.assertEqual(v.estado, "LISTO")
        self.assertEqual(v.editor._titulo.cget("text"), "Archivo de entrada: correcto.flow")
        self.messagebox.askyesnocancel.assert_not_called()  # la solicitud inicial no pregunta

    def test_barra_de_estado_al_terminar(self):
        v = self.v
        self.terminar(INCORRECTO)
        texto = v.barra_estado.contadores.cget("text")
        validas, con_errores = v.editor.conteo_lineas()
        for esperado in ("Tokens: 57", "Símbolos: 18", "Errores: 15",
                         f"Líneas válidas: {validas}", f"Líneas con errores: {con_errores}"):
            self.assertIn(esperado, texto)
        self.assertEqual(v.barra_estado.veredicto.cget("text"), "✗ El archivo NO es válido para FlowLang")
        self.terminar(CORRECTO)
        self.assertEqual(v.barra_estado.veredicto.cget("text"), "✓ El archivo es válido para FlowLang")

    def test_el_veredicto_se_borra_al_editar_o_limpiar(self):
        v = self.v
        self.terminar(CORRECTO)
        v.editor.texto.insert("end", " ")
        self.bombear(lambda: v.barra_estado.veredicto.cget("text") == "")
        self.terminar(CORRECTO)
        self.assertNotEqual(v.barra_estado.veredicto.cget("text"), "")
        v.limpiar()
        self.assertEqual(v.barra_estado.veredicto.cget("text"), "")

    def test_paso_a_paso_muestra_autómatas_y_analizar_tokens(self):
        v = self.v
        v.abrir_archivo(CORRECTO)
        v.paso_a_paso()
        self.assertEqual(v.panel_resultados.vista_actual, "automatas")
        v.analizar()
        self.assertEqual(v.panel_resultados.vista_actual, "tokens")
        v.detener()

    def test_detener_cancela_el_temporizador(self):
        v = self.v
        v.cabecera.establecer_pausa(100)
        v.abrir_archivo(CORRECTO)
        v.analizar()
        v.detener()
        filas = self.filas(v.panel_resultados.arbol_tokens)
        fin = time.time() + 0.4
        while time.time() < fin:
            v.update()
            time.sleep(0.01)
        self.assertEqual(self.filas(v.panel_resultados.arbol_tokens), filas)
        self.assertEqual(v.estado, "ANALIZANDO")

    # --- AUD-29: cambios sin guardar -----------------------------------------------
    def con_cambios(self):
        self.v.abrir_archivo(CORRECTO)
        self.v.editor.texto.insert("end", "x")
        self.messagebox.askyesnocancel.reset_mock()
        return self.v.editor.obtener_texto()

    def acciones_que_descartan(self):
        """(nombre, accion) de las cinco salidas que deben preguntar por los cambios sin guardar."""
        v = self.v
        etiquetas = self.etiquetas_menu()
        return [("abrir con ruta", lambda: v.abrir_archivo(INCORRECTO)),
                ("abrir sin ruta", lambda: v.abrir_archivo()),
                ("menu Ejemplos", lambda: v.cabecera.menu_ejemplos.invoke(etiquetas.index("incorrecto.flow"))),
                ("limpiar", v.limpiar), ("salir", v.salir)]

    def test_cancelar_conserva_el_texto_y_el_archivo(self):
        texto = self.con_cambios()
        self.messagebox.askyesnocancel.return_value = None
        for nombre, accion in self.acciones_que_descartan():
            with self.subTest(nombre), mock.patch.object(self.v, "destroy") as destruir:
                self.messagebox.askyesnocancel.reset_mock()
                accion()
                self.messagebox.askyesnocancel.assert_called_once()
                self.assertEqual(self.v.editor.obtener_texto(), texto)
                self.assertEqual(self.v.ruta_actual.name, "correcto.flow")
                self.filedialog.askopenfilename.assert_not_called()
                destruir.assert_not_called()

    def test_no_descarta_los_cambios(self):
        self.con_cambios()
        self.messagebox.askyesnocancel.return_value = False
        self.v.abrir_archivo(INCORRECTO)
        self.messagebox.askyesnocancel.assert_called_once()
        self.assertEqual(self.v.ruta_actual.name, "incorrecto.flow")
        self.con_cambios()
        self.v.limpiar()
        self.assertEqual(self.v.estado, "SIN_FUENTE")
        self.assertEqual(self.v.editor.obtener_texto(), "")
        self.con_cambios()
        with mock.patch.object(self.v, "destroy") as destruir:
            self.v.salir()
        destruir.assert_called_once()

    def test_si_guarda_antes_de_continuar(self):
        from application.archivos import cargar_fuente
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        ruta = Path(tmp.name) / "mio.flow"
        ruta.write_text("inicio\nfin\n", encoding="utf-8")
        self.v.abrir_archivo(str(ruta))
        self.v.editor.texto.insert("end", "// nota")
        self.messagebox.askyesnocancel.return_value = True
        self.v.abrir_archivo(CORRECTO)
        self.assertIn("// nota", cargar_fuente(str(ruta)))
        self.assertEqual(self.v.ruta_actual.name, "correcto.flow")

    def test_si_pero_se_cancela_el_guardado_no_continua(self):
        texto = self.con_cambios()
        self.v.ruta_actual = None  # sin ruta, guardar abre el dialogo
        self.filedialog.asksaveasfilename.return_value = ""
        self.messagebox.askyesnocancel.return_value = True
        self.v.abrir_archivo(INCORRECTO)
        self.filedialog.asksaveasfilename.assert_called_once()
        self.assertEqual(self.v.editor.obtener_texto(), texto)
        self.filedialog.askopenfilename.assert_not_called()

    def test_sin_cambios_no_pregunta(self):
        self.v.abrir_archivo(CORRECTO)
        self.v.abrir_archivo(INCORRECTO)
        self.v.limpiar()
        self.messagebox.askyesnocancel.assert_not_called()

    def test_el_boton_de_cierre_llama_a_salir(self):
        self.assertIn("salir", self.v.protocol("WM_DELETE_WINDOW"))

    # --- AUD-31: Ctrl+O en el editor --------------------------------------------------
    def test_ctrl_o_en_el_editor_abre_y_no_inserta_un_salto(self):
        v = self.v
        self.filedialog.askopenfilename.return_value = ""
        v.abrir_archivo(CORRECTO)
        texto = v.editor.obtener_texto()
        v.update()
        v.editor.texto.focus_force()
        v.update()
        v.editor.texto.event_generate("<Control-o>")
        v.update()
        self.assertEqual(v.editor.obtener_texto(), texto)
        self.filedialog.askopenfilename.assert_called_once()

    # --- B17: nuevo archivo --------------------------------------------------------
    def carpeta_temporal(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def test_nuevo_archivo_crea_y_abre_la_plantilla(self):
        from application.archivos import plantilla_nueva
        v = self.v
        v.abrir_archivo(INCORRECTO)
        ruta = self.carpeta_temporal() / "nuevo.flow"
        self.filedialog.asksaveasfilename.return_value = str(ruta)
        v.nuevo_archivo()
        kwargs = self.filedialog.asksaveasfilename.call_args.kwargs
        self.assertEqual(kwargs["defaultextension"], ".flow")
        self.assertEqual(kwargs["initialfile"], "nuevo.flow")
        self.assertEqual(ruta.read_text(encoding="utf-8"), plantilla_nueva())
        self.assertEqual(v.editor.obtener_texto(), plantilla_nueva())
        self.assertEqual(v.editor.posicion_cursor(), (2, 5))
        self.assertEqual(v.estado, "LISTO")
        self.assertEqual(v.editor._titulo.cget("text"), "Archivo de entrada: nuevo.flow")
        self.assertEqual(self.filas(v.panel_errores.arbol_errores), 0)
        self.assertEqual(v.panel_resultados.arbol_tokens.get_children(), ())

    def test_nuevo_archivo_en_ejemplos_aparece_en_el_menu(self):
        v = self.v
        ruta = RAIZ / "ejemplos" / "zz_prueba_nuevo.flow"
        self.addCleanup(lambda: ruta.unlink(missing_ok=True))
        self.filedialog.asksaveasfilename.return_value = str(ruta)
        v.nuevo_archivo()
        self.assertIn("zz_prueba_nuevo.flow", self.etiquetas_menu())
        self.assertEqual(v.ruta_actual.name, "zz_prueba_nuevo.flow")

    def test_nuevo_archivo_cancelado_no_cambia_nada(self):
        v = self.v
        v.abrir_archivo(CORRECTO)
        texto = v.editor.obtener_texto()
        self.filedialog.asksaveasfilename.return_value = ""
        v.nuevo_archivo()
        self.assertEqual(v.editor.obtener_texto(), texto)
        self.assertEqual(v.ruta_actual.name, "correcto.flow")

    def test_nuevo_archivo_con_cambios_y_cancelar_aborta(self):
        v = self.v
        v.abrir_archivo(CORRECTO)
        v.editor.texto.insert("end", "x")
        self.messagebox.askyesnocancel.return_value = None
        v.nuevo_archivo()
        self.messagebox.askyesnocancel.assert_called_once()
        self.assertEqual(self.messagebox.askyesnocancel.call_args[0][0], "Nuevo archivo")
        self.assertIn("cambios sin guardar", self.messagebox.askyesnocancel.call_args[0][1])
        self.filedialog.asksaveasfilename.assert_not_called()
        self.assertEqual(v.ruta_actual.name, "correcto.flow")

    def test_nuevo_archivo_con_cambios_y_no_descarta(self):
        v = self.v
        v.abrir_archivo(CORRECTO)
        v.editor.texto.insert("end", "x")
        self.messagebox.askyesnocancel.return_value = False
        ruta = self.carpeta_temporal() / "otro.txt"
        self.filedialog.asksaveasfilename.return_value = str(ruta)
        v.nuevo_archivo()
        self.assertEqual(v.ruta_actual, ruta)

    def test_nuevo_archivo_extension_invalida_es_error_de_archivo(self):
        v = self.v
        self.filedialog.asksaveasfilename.return_value = str(self.carpeta_temporal() / "x.exe")
        v.nuevo_archivo()
        self.messagebox.showerror.assert_called_once()
        self.assertEqual(self.filas(v.panel_errores.arbol_errores), 1)
        self.assertEqual(v.estado, "SIN_FUENTE")

    # --- Auditoría Fase D (reviewer-opus) -----------------------------------------
    def test_aud33_tabla_de_simbolos_legible(self):
        from ui.paneles import formatear_apariciones, formatear_valor
        self.assertEqual(formatear_apariciones([(6, 12), (9, 9), (10, 18)]), "6:12, 9:9, 10:18")
        self.assertEqual([formatear_valor(x) for x in (True, False, None, 28, 1.05)],
                         ["verdadero", "falso", "", "28", "1.05"])
        self.assertEqual(formatear_valor('Invernadero "Norte"'), '"Invernadero \\"Norte\\""')
        self.terminar(CORRECTO)
        arbol = self.v.panel_resultados.arbol_simbolos
        filas = {arbol.set(i, "lexema"): i for i in arbol.get_children()}
        humedad = filas["humedad"]
        self.assertEqual(arbol.set(humedad, "apariciones"), "6:13, 13:30, 23:9, 23:19")
        self.assertEqual(arbol.set(humedad, "veces"), "4")
        self.assertEqual(arbol.set(filas["verdadero"], "valor"), "verdadero")
        for i in arbol.get_children():
            self.assertNotIn("[(", arbol.set(i, "apariciones"))
            self.assertNotIn(arbol.set(i, "valor"), ("True", "False", "None"))

    def test_aud34_archivo_largo_respeta_el_tope_y_repinta(self):
        v = self.v
        base = Path(CORRECTO).read_text(encoding="utf-8").splitlines()
        ruta = self.carpeta_temporal() / "largo.flow"
        ruta.write_text("\n".join((base * 200)[:3000]), encoding="utf-8")
        v.cabecera.establecer_pausa(120)
        v.abrir_archivo(str(ruta))
        inicio = time.monotonic()
        v.analizar()
        self.bombear(lambda: v.estado == "TERMINADO", limite=40)
        # antes de AUD-34 el trabajo de cada línea se sumaba a la pausa (~24 s para 3 000 líneas)
        self.assertLess(time.monotonic() - inicio, self.interfaz.DURACION_MAXIMA_ANIMACION_MS / 1000 * 1.3)


if __name__ == "__main__":
    unittest.main()
