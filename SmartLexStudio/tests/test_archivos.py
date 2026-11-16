"""Pruebas de lectura, escritura y listado de archivos fuente."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from application.archivos import ErrorArchivo, cargar_fuente, crear_fuente, guardar_fuente, listar_ejemplos
from config import reglas
from core.modelos import TipoDiagnostico


class TestArchivos(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def crear(self, nombre: str, datos: bytes) -> Path:
        ruta = self.dir / nombre
        ruta.write_bytes(datos)
        return ruta

    def codigo_de(self, ruta) -> str:
        with self.assertRaises(ErrorArchivo) as contexto:
            cargar_fuente(ruta)
        return contexto.exception.diagnostico.codigo

    def test_errores(self):
        (self.dir / "x.flow").mkdir()
        casos = [
            (self.dir / "nada.flow", "ARC-001"),
            (self.dir / "x.flow", "ARC-005"),
            (self.crear("datos.pdf", b"inicio fin"), "ARC-002"),
            (self.crear("vacio.flow", b""), "ARC-003"),
            (self.crear("blancos.flow", b"  \n\t\r\n "), "ARC-003"),
            (self.crear("mal.flow", b"\xff\xfe\x00inicio"), "ARC-004"),
            (self.crear("grande.flow", b"a" * (reglas.TAMANO_MAXIMO_BYTES + 1)), "ARC-006"),
        ]
        for ruta, codigo in casos:
            with self.subTest(ruta=ruta.name):
                self.assertEqual(self.codigo_de(ruta), codigo)

    def test_diagnostico_de_archivo(self):
        with self.assertRaises(ErrorArchivo) as contexto:
            cargar_fuente(self.dir / "falta.flow")
        error = contexto.exception
        self.assertEqual(error.diagnostico.tipo, TipoDiagnostico.ARCHIVO)
        self.assertEqual(error.diagnostico.linea, 0)
        self.assertIn("falta.flow", error.diagnostico.mensaje)
        self.assertEqual(str(error), error.diagnostico.mensaje)

    def test_lecturas_validas(self):
        self.assertEqual(cargar_fuente(self.crear("A.FLOW", b"inicio fin")), "inicio fin")
        self.assertEqual(cargar_fuente(self.crear("a.txt", b"inicio fin")), "inicio fin")
        self.assertEqual(cargar_fuente(self.crear("bom.flow", b"\xef\xbb\xbfinicio")), "inicio")
        self.assertEqual(cargar_fuente(self.crear("crlf.flow", b"a\r\nb\rc\n")), "a\nb\nc\n")

    def test_guardar_y_cargar(self):
        texto = "inicio\n// año ñandú\nfin\n"
        ruta = self.dir / "salida.flow"
        guardar_fuente(ruta, texto)
        self.assertEqual(cargar_fuente(ruta), texto)

    def test_guardar_en_directorio_inexistente(self):
        with self.assertRaises(ErrorArchivo) as contexto:
            guardar_fuente(self.dir / "no_existe" / "a.flow", "x")
        self.assertEqual(contexto.exception.diagnostico.codigo, "ARC-005")

    def test_listar_ejemplos(self):
        nombres = [p.name for p in listar_ejemplos()]
        self.assertEqual(nombres, ["casos_limite.flow", "correcto.flow", "incorrecto.flow"])
        self.assertEqual(listar_ejemplos(self.dir / "no_existe"), [])

    def test_crear_fuente_escribe_una_plantilla_valida(self):
        from application.analisis_service import analizar_texto
        ruta = self.dir / "nuevo.flow"
        texto = crear_fuente(ruta)
        self.assertEqual(ruta.read_text(encoding="utf-8"), texto)
        self.assertEqual(cargar_fuente(ruta), texto)
        self.assertTrue(texto.startswith(reglas.PALABRA_INICIO) and texto.rstrip().endswith(reglas.PALABRA_FIN))
        self.assertTrue(analizar_texto(texto).es_valida)

    def test_crear_fuente_extension_no_permitida(self):
        ruta = self.dir / "nuevo.exe"
        with self.assertRaises(ErrorArchivo) as contexto:
            crear_fuente(ruta)
        self.assertEqual(contexto.exception.diagnostico.codigo, "ARC-002")
        self.assertFalse(ruta.exists())

    def test_crear_fuente_en_carpeta_inexistente_es_arc_005(self):
        with self.assertRaises(ErrorArchivo) as contexto:
            crear_fuente(self.dir / "no_existe" / "x.flow")
        self.assertEqual(contexto.exception.diagnostico.codigo, "ARC-005")


if __name__ == "__main__":
    unittest.main()
