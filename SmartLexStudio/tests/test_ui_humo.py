"""Prueba de humo de la interfaz: flujo progresivo, navegacion y casos de la auditoria."""
from __future__ import annotations

import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

def _hay_tk() -> bool:
    """Prueba en un subproceso si se puede abrir una ventana (un Tk() de prueba destruido
    antes de las pruebas hace fallar al siguiente en macOS con Tk 9)."""
    try:
        resultado = subprocess.run([sys.executable, "-c", "import tkinter; tkinter.Tk().destroy()"],
                                   capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return resultado.returncode == 0


HAY_TK = _hay_tk()

RAIZ = Path(__file__).resolve().parent.parent
INCORRECTO = str(RAIZ / "ejemplos" / "incorrecto.flow")
CORRECTO = str(RAIZ / "ejemplos" / "correcto.flow")


@unittest.skipUnless(HAY_TK, "tkinter o pantalla no disponibles")
class TestUIHumo(unittest.TestCase):
    def setUp(self):
        from ui import interfaz
        self.interfaz = interfaz
        parches = [mock.patch.object(interfaz, "messagebox"), mock.patch.object(interfaz, "filedialog")]
        self.messagebox, self.filedialog = [p.start() for p in parches]
        for p in parches:
            self.addCleanup(p.stop)
        self.messagebox.askyesno.return_value = False
        self.messagebox.askyesnocancel.return_value = False  # el MagicMock por defecto es verdadero (D-70)
        self.ventanas = []

    def crear(self, **kwargs):
        ventana = self.interfaz.VentanaPrincipal(**kwargs)
        ventana.cabecera.establecer_pausa(0)
        self.ventanas.append(ventana)
        self.addCleanup(ventana.destroy)
        return ventana

    def bombear(self, ventana, condicion, limite=10.0):
        fin = time.time() + limite
        while not condicion() and time.time() < fin:
            ventana.update()
            time.sleep(0.005)
        self.assertTrue(condicion(), "la condición no se cumplió a tiempo")

    @staticmethod
    def filas(arbol):
        return len(arbol.get_children())

    def terminar(self, ruta):
        v = self.crear(solicitar_archivo=False)
        v.abrir_archivo(ruta)
        v.analizar()
        self.bombear(v, lambda: v.estado == "TERMINADO")
        return v

    def test_flujo_completo_incorrecto(self):
        v = self.terminar(INCORRECTO)
        p = v.panel_resultados
        self.assertEqual(self.filas(p.arbol_tokens), 57)
        self.assertEqual(self.filas(v.panel_errores.arbol_errores), 15)
        self.messagebox.askyesno.assert_called_once()
        self.assertIn("tabla de símbolos", self.messagebox.askyesno.call_args[0][1])
        self.assertTrue(p.tabla_simbolos_habilitada())
        v.ver_tabla_simbolos()
        self.assertEqual(self.filas(p.arbol_simbolos), 18)

    def test_progresividad(self):
        v = self.crear(solicitar_archivo=False)
        v.abrir_archivo(INCORRECTO)
        v.paso_a_paso()
        self.assertEqual(self.filas(v.panel_resultados.arbol_tokens), 1)
        self.assertEqual(v.estado, "ANALIZANDO")
        self.assertFalse(v.panel_resultados.tabla_simbolos_habilitada())
        self.assertNotIn("Seleccione un token", v.panel_resultados.educativo.get("1.0", "end"))

    def test_archivo_inexistente(self):
        v = self.crear(solicitar_archivo=False)
        v.abrir_archivo(str(RAIZ / "no_existe.flow"))
        self.messagebox.showerror.assert_called_once()
        self.assertEqual(v.estado, "SIN_FUENTE")

    def test_requisito_6_solicita_archivo(self):
        self.filedialog.askopenfilename.return_value = CORRECTO
        v = self.crear(solicitar_archivo=True)
        self.bombear(v, lambda: v.estado == "LISTO")
        self.filedialog.askopenfilename.assert_called_once()
        self.assertIn("inicio", v.editor.obtener_texto())

    def test_requisito_6_cancelado(self):
        self.filedialog.askopenfilename.return_value = ""
        v = self.crear(solicitar_archivo=True)
        self.bombear(v, lambda: self.filedialog.askopenfilename.called)
        v.update()
        self.assertEqual(v.estado, "SIN_FUENTE")

    def test_errores_durante_la_evaluacion(self):
        v = self.crear(solicitar_archivo=False)
        v.abrir_archivo(INCORRECTO)
        while self.filas(v.panel_errores.arbol_errores) == 0:
            v.paso_a_paso()
        self.assertEqual(self.filas(v.panel_errores.arbol_errores), 1)
        rangos = [str(i) for i in v.editor.texto.tag_ranges("marca_error")]
        self.assertEqual(rangos, ["2.11", "2.14"])
        self.assertFalse(v.sesion.terminada)

    def test_un_solo_error_de_archivo(self):
        v = self.crear(solicitar_archivo=False)
        for _ in range(2):
            v.abrir_archivo(str(RAIZ / "no_existe.flow"))
        self.assertEqual(self.filas(v.panel_errores.arbol_errores), 1)
        v = self.terminar(INCORRECTO)
        for _ in range(2):
            v.abrir_archivo(str(RAIZ / "no_existe.flow"))
        self.assertEqual(self.filas(v.panel_errores.arbol_errores), 16)
        codigos = [v.panel_errores.arbol_errores.item(i, "values")[0]
                   for i in v.panel_errores.arbol_errores.get_children()]
        self.assertEqual(sum(c.startswith("ARC") for c in codigos), 1)

    def test_navegacion_a_un_error(self):
        v = self.terminar(INCORRECTO)
        diag = next(d for d in v.sesion.resultado.diagnosticos if (d.linea, d.columna) == (6, 24))
        v._al_seleccionar_error(diag)
        self.assertEqual(v.editor.posicion_cursor(), (6, 24))

    def test_colisiones_en_el_resumen(self):
        v = self.terminar(CORRECTO)
        resumen = v.panel_resultados.etiqueta_resumen.cget("text")
        self.assertIn("Colisiones al insertar: 14", resumen)
        self.assertIn("En la tabla actual: 7", resumen)

    def test_retorno_de_carro(self):
        v = self.crear(solicitar_archivo=False)
        v.editor.establecer_texto("x\r\ny")
        v.analizar()
        self.bombear(v, lambda: v.estado == "TERMINADO")
        token_y = [t for t in v.sesion.resultado.tokens if t.lexema == "y"][0]
        self.assertEqual((token_y.linea, token_y.columna), (2, 1))

    def test_fuera_del_bmp(self):
        import tkinter
        if tkinter.TkVersion < 9:
            self.skipTest("Tk 8.6 cuenta los emoji como dos unidades (D-34)")
        v = self.crear(solicitar_archivo=False)
        v.editor.establecer_texto('inicio "😀" x fin')
        v.analizar()
        self.bombear(v, lambda: v.estado == "TERMINADO")
        from core.modelos import Token, TipoToken
        v.editor.resaltar([Token(TipoToken.IDENTIFICADOR, "x", 1, 12)])
        rangos = [str(i) for i in v.editor.texto.tag_ranges("tok_IDENTIFICADOR")]
        self.assertEqual(rangos, ["1.11", "1.12"])

    def test_editor_tags_y_normalizacion(self):
        v = self.crear(solicitar_archivo=False)
        v.editor.establecer_texto("a\r\nb\rc")
        self.assertEqual(v.editor.obtener_texto(), "a\nb\nc")
        from core.modelos import Token, TipoToken
        v.editor.establecer_texto("x\n123456 abcde")
        v.editor.resaltar([Token(TipoToken.IDENTIFICADOR, "abcde", 2, 8)])
        self.assertEqual([str(i) for i in v.editor.texto.tag_ranges("tok_IDENTIFICADOR")], ["2.7", "2.12"])

    def test_limpiar_vuelve_a_sin_fuente(self):
        v = self.terminar(CORRECTO)
        v.limpiar()
        self.assertEqual(v.estado, "SIN_FUENTE")
        self.assertEqual(self.filas(v.panel_resultados.arbol_tokens), 0)
        self.assertFalse(v.panel_resultados.tabla_simbolos_habilitada())


if __name__ == "__main__":
    unittest.main()
