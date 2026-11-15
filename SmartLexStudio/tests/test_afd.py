"""Pruebas de las reglas (config), el motor AFD y la equivalencia regex <-> AFD."""
from __future__ import annotations

import itertools
import re
import unittest

from config import reglas
from core.afd import AFD, clase_caracter
from core.modelos import TipoToken


class TestReglas(unittest.TestCase):
    def test_conteos(self):
        self.assertEqual(len(reglas.PALABRAS_RESERVADAS), 17)
        self.assertEqual(len(reglas.OPERADORES), 15)
        self.assertEqual(len(reglas.DELIMITADORES), 6)
        self.assertEqual(len(reglas.LETRAS), 52)
        self.assertEqual(len(reglas.SUGERENCIAS_CARACTER), 8)
        self.assertEqual(len(reglas.AUTOMATAS), 4)

    def test_palabras_referenciadas_son_reservadas(self):
        for palabra in (*reglas.TIPOS_DE_DATO, *reglas.VALORES_BOOLEANOS,
                        reglas.PALABRA_INICIO, reglas.PALABRA_FIN):
            self.assertIn(palabra, reglas.PALABRAS_RESERVADAS)

    def test_info_categorias_completa_y_regex_compilan(self):
        self.assertEqual(set(reglas.INFO_CATEGORIAS), set(TipoToken))
        for tipo, info in reglas.INFO_CATEGORIAS.items():
            if info["regex"] is None:
                self.assertEqual(tipo, TipoToken.ERROR)
            else:
                re.compile(info["regex"])

    def test_escapes_coinciden_con_afd_cadena(self):
        fila = reglas.AFD_CADENA["transiciones"]["q2"]
        claves = {c for c in fila if c != reglas.OTRO}
        self.assertEqual(claves, set(reglas.ESCAPES_VALIDOS))

    def test_destinos_de_cada_afd_existen(self):
        for definicion in reglas.AUTOMATAS:
            conocidos = (set(definicion["transiciones"]) | set(definicion["aceptacion"])
                         | set(definicion["errores"]) | {definicion["inicial"]})
            for fila in definicion["transiciones"].values():
                for destino in fila.values():
                    self.assertIn(destino, conocidos, definicion["nombre"])


class TestMotorAFD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.numero = AFD(reglas.AFD_NUMERO)
        cls.identificador = AFD(reglas.AFD_IDENTIFICADOR)
        cls.comentario = AFD(reglas.AFD_COMENTARIO)

    def test_clase_caracter(self):
        self.assertEqual(clase_caracter("a"), reglas.LETRA)
        self.assertEqual(clase_caracter("7"), reglas.DIGITO)
        self.assertEqual(clase_caracter("\n"), reglas.SALTO)
        self.assertEqual(clase_caracter("ñ"), "ñ")

    def test_recorridos_de_la_especificacion(self):
        casos = [
            ("28", ("q0", "q1", "q1"), TipoToken.ENTERO, None),
            ("45.5", ("q0", "q1", "q1", "q2", "q3"), TipoToken.DECIMAL, None),
            ("3.", ("q0", "q1", "q2"), None, "LEX-003"),
            ("3.4.5", ("q0", "q1", "q2", "q3", "q4", "q4"), None, "LEX-003"),
            (".5", ("q0", "q6", "q4"), None, "LEX-003"),
            ("12abc", ("q0", "q1", "q1", "q5", "q5", "q5"), None, "LEX-004"),
            ("1.5abc", ("q0", "q1", "q2", "q3", "q4", "q4", "q4"), None, "LEX-003"),
        ]
        for texto, recorrido, tipo, codigo in casos:
            with self.subTest(texto=texto):
                r = self.numero.reconocer(texto)
                self.assertEqual(r.longitud, len(texto))
                self.assertEqual(r.recorrido, recorrido)
                self.assertEqual(r.tipo, tipo)
                self.assertEqual(r.codigo_error, codigo)

    def test_prefijo_mas_largo_y_posicion_inicial(self):
        self.assertEqual(self.identificador.reconocer("abc def", 0).longitud, 3)
        self.assertEqual(self.identificador.reconocer("abc", 3).longitud, 0)
        self.assertEqual(self.identificador.reconocer("abc", 3).recorrido, ("q0",))

    def test_otro_no_consume_salto_de_linea(self):
        self.assertEqual(self.comentario.reconocer("// a\nb", 0).longitud, 4)

    def test_siguiente_estado_determinista(self):
        self.assertEqual(self.numero.siguiente_estado("q0", "5"), "q1")
        self.assertIsNone(self.numero.siguiente_estado("q0", "a"))
        self.assertIsNone(self.numero.siguiente_estado("qX", "a"))

    def test_acepta(self):
        self.assertTrue(self.identificador.acepta("_x1"))
        self.assertFalse(self.identificador.acepta(""))
        self.assertFalse(self.identificador.acepta("1x"))
        self.assertFalse(self.numero.acepta("3."))  # termina en estado de error


class TestEquivalenciaRegexAFD(unittest.TestCase):
    ALFABETO = ["a", "1", "_", ".", '"', "\\", "\n", "/", "*", " ", "q", "n", "t"]

    def test_equivalencia_hasta_longitud_5(self):
        parejas = [
            (reglas.AFD_IDENTIFICADOR, TipoToken.IDENTIFICADOR),
            (reglas.AFD_NUMERO, TipoToken.ENTERO),
            (reglas.AFD_NUMERO, TipoToken.DECIMAL),
            (reglas.AFD_CADENA, TipoToken.CADENA),
            (reglas.AFD_COMENTARIO, TipoToken.COMENTARIO),
        ]
        casos = [(AFD(d), re.compile(reglas.INFO_CATEGORIAS[t]["regex"]), t) for d, t in parejas]
        diferencias = []
        for largo in range(0, 6):
            for letras in itertools.product(self.ALFABETO, repeat=largo):
                cadena = "".join(letras)
                for afd, patron, tipo in casos:
                    r = afd.reconocer(cadena, 0)
                    por_afd = r.longitud == len(cadena) and r.tipo == tipo
                    if por_afd != (patron.fullmatch(cadena) is not None):
                        diferencias.append((tipo.name, cadena))
        self.assertEqual(diferencias, [])


if __name__ == "__main__":
    unittest.main()
