"""Regresiones de la auditoría final: cada prueba fija un defecto ya corregido."""
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
    """Igual que en test_ui_humo: Tk se comprueba en un subproceso."""
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


_SCRIPT_DESTRUIR = """
import time
from unittest import mock
from ui import interfaz
mock.patch.object(interfaz, "messagebox").start(); mock.patch.object(interfaz, "filedialog").start()
v = interfaz.VentanaPrincipal(solicitar_archivo=True)
v.abrir_archivo("ejemplos/correcto.flow"); v.update()
v.editor.texto.insert("end", " x"); v.update()
v.analizar()
v.consola.escribir("y")
v.destroy()
w = interfaz.VentanaPrincipal(solicitar_archivo=False)
fin = time.time() + 0.8
while time.time() < fin:
    w.update(); time.sleep(0.01)
w.destroy()
"""


@unittest.skipUnless(HAY_TK, "tkinter o pantalla no disponibles")
class TestDestruccion(unittest.TestCase):
    def test_aud28_destruir_con_after_pendientes(self):
        """Destruir la ventana con el latido, la espera del editor y los desplazamientos pendientes no deja
        callbacks huérfanos («invalid command name … ("after" script)»). Va en un subproceso porque
        Tcl escribe ese error directo en el descriptor 2."""
        r = subprocess.run([sys.executable, "-c", _SCRIPT_DESTRUIR], cwd=RAIZ,
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("after", r.stderr)
        self.assertNotIn("invalid command name", r.stderr)


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
        self.messagebox.askyesnocancel.return_value = False  # el MagicMock devuelve verdadero por defecto
        self.v = interfaz.VentanaPrincipal(solicitar_archivo=False)
        self.v.cabecera.establecer_pausa(0)
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
        """Escribir y analizar enseguida: el aviso de cambio (espera de 300 ms) ya no marca como
        desactualizado un resultado calculado con ese mismo texto."""
        self.v.editor.texto.insert("1.0", "inicio x fin")
        self.v.update()
        self.v.analizar()
        self.bombear(lambda: self.v.estado == "TERMINADO")
        self.esperar(0.6)
        self.assertEqual(self.v.estado, "TERMINADO")

    def test_aud17_un_solo_desplazamiento_por_tick(self):
        """Con muchos pasos por latido, Treeview.see (que cuesta más cuantas más filas hay) no se llama por cada token."""
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
        """Los ocho botones de la cabecera son ttk.Button con texto y no heredan el ancho mínimo del
        tema clam (width=0); la cabecera cabe en el ancho mínimo de la ventana."""
        from tkinter import ttk
        self.v.update()
        botones = self.v.cabecera.botones
        self.assertEqual(set(botones), {"nuevo", "abrir", "guardar", "analizar", "paso", "detener", "limpiar", "ayuda"})
        for nombre, boton in botones.items():
            self.assertIsInstance(boton, ttk.Button, nombre)
            self.assertTrue(str(boton.cget("text")), nombre)
            self.assertLess(boton.winfo_reqwidth(), 170, nombre)
        self.assertLessEqual(self.v.cabecera.winfo_reqwidth(), 1100)

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
        pr = self.v.panel_errores
        fila = pr.arbol_errores.get_children()[7]
        pr.arbol_errores.selection_set(fila)
        self.v.update()
        d = pr._errores[fila]
        texto = str(pr.detalle_error.cget("text"))
        self.assertIn(d.mensaje, texto)
        self.assertIn(d.sugerencia, texto)
        titulo = str(pr.detalle_titulo.cget("text"))
        self.assertIn(d.codigo, titulo)
        self.assertIn(f"línea {d.linea}, columna {d.columna}", titulo)
        pr.limpiar()
        self.assertNotIn(d.mensaje, str(pr.detalle_error.cget("text")))


if __name__ == "__main__":
    unittest.main()
