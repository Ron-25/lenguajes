"""Pruebas del catálogo y del manejador de errores."""
from __future__ import annotations

import unittest

from core.errores import CATALOGO, ManejadorErrores, crear_diagnostico
from core.modelos import TipoDiagnostico


class TestCatalogo(unittest.TestCase):
    def test_diecinueve_codigos_con_tipo_correcto(self):
        self.assertEqual(len(CATALOGO), 19)
        esperado = {"LEX": TipoDiagnostico.LEXICO, "SIN": TipoDiagnostico.ESTRUCTURAL,
                    "ARC": TipoDiagnostico.ARCHIVO}
        cuentas = {"LEX": 0, "SIN": 0, "ARC": 0}
        for codigo, datos in CATALOGO.items():
            cuentas[codigo[:3]] += 1
            self.assertEqual(datos["tipo"], esperado[codigo[:3]])
            for campo in ("titulo", "mensaje", "sugerencia"):
                self.assertTrue(datos[campo].strip(), (codigo, campo))
        self.assertEqual(cuentas, {"LEX": 7, "SIN": 6, "ARC": 6})

    def test_crear_diagnostico(self):
        d = crear_diagnostico("LEX-001", 3, 7, "@")
        self.assertIn("'@'", d.mensaje)
        self.assertEqual((d.linea, d.columna, d.tipo), (3, 7, TipoDiagnostico.LEXICO))
        self.assertEqual(d.sugerencia, CATALOGO["LEX-001"]["sugerencia"])

    def test_sugerencia_personalizada_y_codigo_desconocido(self):
        d = crear_diagnostico("LEX-001", 1, 1, "&", sugerencia="otra")
        self.assertEqual(d.sugerencia, "otra")
        with self.assertRaises(KeyError):
            crear_diagnostico("XXX-999")


class TestManejador(unittest.TestCase):
    def setUp(self):
        self.m = ManejadorErrores()

    def test_ordenados_por_posicion(self):
        self.m.reportar("LEX-001", 5, 1, "@")
        self.m.reportar("LEX-001", 2, 9, "#")
        self.m.reportar("LEX-001", 2, 3, "$")
        self.assertEqual([(d.linea, d.columna) for d in self.m.ordenados()], [(2, 3), (2, 9), (5, 1)])
        self.assertEqual(self.m.diagnosticos[0].linea, 5)  # el orden de reporte no cambia

    def test_consultas(self):
        self.m.reportar("LEX-001", 1, 1, "@")
        self.m.reportar("LEX-002", 1, 5, '"a')
        self.m.agregar(crear_diagnostico("SIN-001", 1, 1))
        self.m.extender([crear_diagnostico("SIN-003", 4, 2, "x")])
        self.assertEqual(self.m.cantidad(), 4)
        self.assertEqual(self.m.cantidad(TipoDiagnostico.LEXICO), 2)
        self.assertEqual(len(self.m.por_tipo(TipoDiagnostico.ESTRUCTURAL)), 2)
        self.assertEqual(sorted(self.m.por_linea()), [1, 4])
        self.assertEqual(len(self.m.por_linea()[1]), 3)
        self.assertTrue(self.m.hay_errores(TipoDiagnostico.LEXICO))
        self.assertFalse(self.m.hay_errores(TipoDiagnostico.ARCHIVO))

    def test_resumen(self):
        self.assertEqual(self.m.resumen(), "Sin errores")
        for i in range(13):
            self.m.reportar("LEX-001", i + 1, 1, "@")
        self.m.reportar("SIN-001")
        self.m.reportar("SIN-001")
        self.assertEqual(self.m.resumen(), "15 errores: 13 léxicos, 2 estructurales")

    def test_limpiar_y_copia(self):
        self.m.reportar("LEX-001", 1, 1, "@")
        self.m.diagnosticos.clear()
        self.assertEqual(self.m.cantidad(), 1)
        self.m.limpiar()
        self.assertFalse(self.m.hay_errores())


if __name__ == "__main__":
    unittest.main()
