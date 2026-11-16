"""Regresiones de la primera auditoría: cada prueba fija un defecto ya corregido."""
from __future__ import annotations

import re
import tempfile
import time
import unittest
from pathlib import Path

from application.analisis_service import SesionAnalisis, analizar_texto, explicar_token
from application.archivos import ErrorArchivo, cargar_fuente, guardar_fuente
from config import reglas
from core.lexer import Lexer
from core.modelos import TipoToken, Token

RAIZ = Path(__file__).resolve().parent.parent


class TestAuditoriaFaseA(unittest.TestCase):
    def test_aud01_sesion_lineal_en_cantidad_de_diagnosticos(self):
        """Cada paso copiaba la lista completa de diagnósticos, así que el costo crecía al cuadrado."""
        fuente = "@" * 60000
        inicio = time.perf_counter()
        Lexer(fuente).analizar()
        solo_lexer = time.perf_counter() - inicio
        inicio = time.perf_counter()
        resultado = analizar_texto(fuente)
        con_sesion = time.perf_counter() - inicio
        self.assertEqual(len(resultado.diagnosticos), 60001)  # 60000 LEX-001 más SIN-001
        self.assertLess(con_sesion, 4 * solo_lexer + 0.5)

    def test_aud02_guardar_texto_no_codificable_no_trunca(self):
        """Un texto no codificable lanzaba UnicodeEncodeError en vez de ARC-005 y dejaba el archivo vacío."""
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "a.flow"
            ruta.write_text("ORIGINAL", encoding="utf-8")
            with self.assertRaises(ErrorArchivo) as contexto:
                guardar_fuente(ruta, "x \ud83d y")  # un sustituto suelto no es UTF-8 válido
            self.assertEqual(contexto.exception.diagnostico.codigo, "ARC-005")
            self.assertEqual(ruta.read_text(encoding="utf-8"), "ORIGINAL")

    def test_aud03_regex_informativas_coinciden_con_los_datos(self):
        """Las regex de INFO_CATEGORIAS deben describir exactamente los lexemas de `reglas`."""
        reservadas = reglas.INFO_CATEGORIAS[TipoToken.PALABRA_RESERVADA]["regex"]
        self.assertEqual(set(reservadas.split("|")), set(reglas.PALABRAS_RESERVADAS))
        simbolos = {**reglas.OPERADORES, **reglas.DELIMITADORES}
        categorias = set(simbolos.values())
        for lexema, tipo in simbolos.items():
            self.assertTrue(re.fullmatch(reglas.INFO_CATEGORIAS[tipo]["regex"], lexema), lexema)
        # y ninguna regex de símbolos acepta un lexema de otra categoría
        for tipo in categorias:
            aceptados = {l for l in simbolos if re.fullmatch(reglas.INFO_CATEGORIAS[tipo]["regex"], l)}
            self.assertEqual(aceptados, {l for l, t in simbolos.items() if t == tipo}, tipo)

    def test_aud05_espacios_unicode_no_son_archivo_vacio(self):
        """ARC-003 usaba str.strip(), que quita espacios Unicode, en vez de reglas.ESPACIOS."""
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "nbsp.flow"
            ruta.write_bytes(" \f".encode("utf-8"))
            self.assertEqual(cargar_fuente(ruta), " \f")
            ruta.write_bytes(b" \t\r\n ")
            with self.assertRaises(ErrorArchivo) as contexto:
                cargar_fuente(ruta)
            self.assertEqual(contexto.exception.diagnostico.codigo, "ARC-003")

    def test_aud06_explicacion_usa_la_sugerencia_especifica(self):
        """La explicación de un token mostraba la sugerencia genérica de LEX-001 para `&`."""
        lexer = Lexer("&")
        lexer.analizar()
        esperada = lexer.manejador.diagnosticos[0].sugerencia
        detalle = explicar_token(Token(TipoToken.ERROR, "&", 1, 1)).detalle
        self.assertIn(f"Sugerencia: {esperada}", detalle)
        self.assertIn("&&", detalle)
        self.assertIn("LEX-003", explicar_token(Token(TipoToken.ERROR, "3.", 1, 1)).detalle)

    def test_aud07_narracion_de_colision_con_redimensionado(self):
        """La descripción de una colisión con redimensionado mezclaba la cubeta vieja y la nueva."""
        fuente = (RAIZ / "ejemplos" / "correcto.flow").read_text(encoding="utf-8")
        pasos = [p for p in SesionAnalisis(fuente).pasos()
                 if p.instalacion is not None and p.instalacion.redimensiono]
        self.assertEqual(len(pasos), 2)
        for paso in pasos:
            self.assertIn(f"ahora en cubeta {paso.instalacion.indice}", paso.descripcion)


if __name__ == "__main__":
    unittest.main()
