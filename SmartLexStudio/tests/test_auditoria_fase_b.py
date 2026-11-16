"""Pruebas de regresion de la auditoria final (AUD-15 en adelante, docs/06_auditoria.md)."""
from __future__ import annotations

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
    """Igual que en test_ui_humo (D-38): se comprueba Tk en un subproceso."""
    try:
        r = subprocess.run([sys.executable, "-c", "import tkinter; tkinter.Tk().destroy()"],
                           capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


HAY_TK = _hay_tk()


class TestModoConsola(unittest.TestCase):
    def test_aud21_fin_de_entrada_no_lanza_excepcion(self):
        """Con la entrada cerrada (EOF) el modo consola termina sin traza."""
        r = subprocess.run([sys.executable, "main.py", "--consola", "ejemplos/correcto.flow"],
                           cwd=RAIZ, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("VÁLIDA", r.stdout)


@unittest.skipUnless(HAY_TK, "tkinter o pantalla no disponibles")
class TestAuditoriaFaseB(unittest.TestCase):
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

    def esperar(self, segundos):
        fin = time.time() + segundos
        while time.time() < fin:
            self.v.update()
            time.sleep(0.01)

    def test_aud16_cambio_pendiente_no_invalida_un_analisis_terminado(self):
        """Escribir y analizar enseguida: el aviso de cambio (debounce 300 ms) ya no marca
        como desactualizado un resultado que se calculó con ese mismo texto."""
        self.v.editor.texto.insert("1.0", "inicio x fin")
        self.v.update()
        self.v.analizar()
        self.bombear(lambda: self.v.estado == "TERMINADO")
        self.esperar(0.6)
        self.assertEqual(self.v.estado, "TERMINADO")

    def test_aud17_un_solo_desplazamiento_por_tick(self):
        """Con muchos pasos por tick, Treeview.see (lineal en filas) no se llama por cada token."""
        fuente = "inicio\n" + "numero x = 1 + 2.5 * y; // c\n" * 1000 + "fin\n"
        self.v.editor.establecer_texto(fuente)
        llamadas = []
        original = self.v.panel_resultados.arbol_tokens.see
        self.v.panel_resultados.arbol_tokens.see = lambda iid: (llamadas.append(iid), original(iid))
        inicio = time.perf_counter()
        self.v.analizar()
        self.bombear(lambda: self.v.estado == "TERMINADO", limite=60)
        filas = len(self.v.panel_resultados.arbol_tokens.get_children())
        self.assertGreater(filas, 10000)
        self.assertLess(len(llamadas), filas // 20)
        self.assertLess(time.perf_counter() - inicio, 30)

    def test_aud18_botones_con_ancho_natural(self):
        """La barra no impone el ancho minimo de 11 caracteres del tema clam."""
        self.v.update()
        b = self.v.barra.botones
        self.assertLess(b["abrir"].winfo_reqwidth(), b["analizar"].winfo_reqwidth())

    def test_aud19_cursor_y_vista_al_inicio(self):
        """Tras abrir, el cursor está en 1:1; al terminar, la vista vuelve al cursor."""
        self.v.abrir_archivo(CORRECTO)
        self.assertEqual(self.v.editor.posicion_cursor(), (1, 1))
        self.v.analizar()
        self.bombear(lambda: self.v.estado == "TERMINADO")
        self.v.update()
        self.assertEqual(self.v.editor.texto.yview()[0], 0.0)

    def test_aud20_detalle_completo_del_error(self):
        """Seleccionar una fila de Errores muestra el mensaje y la sugerencia completos."""
        self.v.abrir_archivo(INCORRECTO)
        self.v.analizar()
        self.bombear(lambda: self.v.estado == "TERMINADO")
        pr = self.v.panel_resultados
        fila = pr.arbol_errores.get_children()[7]
        pr.arbol_errores.selection_set(fila)
        self.v.update()
        d = pr._errores[fila]
        texto = str(pr.detalle_error.cget("text"))
        self.assertIn(d.mensaje, texto)
        self.assertIn(d.sugerencia, texto)
        pr.limpiar()
        self.assertNotIn(d.mensaje, str(pr.detalle_error.cget("text")))


if __name__ == "__main__":
    unittest.main()
