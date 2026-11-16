"""Pruebas de los modelos y del analizador léxico."""
from __future__ import annotations

import dataclasses
import time
import unittest
from pathlib import Path

from core.lexer import Lexer, reconocer_lexema
from core.modelos import Diagnostico, TipoToken, Token

RAIZ = Path(__file__).resolve().parent.parent
T = TipoToken


def analizar(fuente: str):
    """Tokens como tuplas y diagnósticos como (código, línea, columna, lexema)."""
    lexer = Lexer(fuente)
    tokens = lexer.analizar()
    return ([(t.tipo, t.lexema, t.linea, t.columna) for t in tokens],
            [(d.codigo, d.linea, d.columna, d.lexema) for d in lexer.manejador.diagnosticos])


class TestModelos(unittest.TestCase):
    def test_inmutables(self):
        token = Token(T.ENTERO, "10", 1, 1)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            token.lexema = "x"
        diagnostico = Diagnostico("LEX-001", None, "t", "m", "s", 1, 1)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            diagnostico.linea = 2

    def test_trece_tipos(self):
        self.assertEqual(len(T), 13)

    def test_longitud_y_significativo(self):
        self.assertEqual(Token(T.CADENA, '"ab"', 1, 1).longitud, 4)
        self.assertTrue(Token(T.IDENTIFICADOR, "x", 1, 1).es_significativo)
        self.assertFalse(Token(T.COMENTARIO, "//", 1, 1).es_significativo)
        self.assertFalse(Token(T.ERROR, "@", 1, 1).es_significativo)


class TestReconocerLexema(unittest.TestCase):
    def test_coincidencia(self):
        c = reconocer_lexema("45.5;", 0)
        self.assertEqual((c.longitud, c.tipo, c.reconocedor), (4, T.DECIMAL, "AFD de números"))
        c = reconocer_lexema("a>=b", 1)
        self.assertEqual((c.longitud, c.recorrido, c.reconocedor),
                         (2, (), "Tabla de operadores y delimitadores"))
        c = reconocer_lexema("@", 0)
        self.assertEqual((c.longitud, c.codigo_error, c.reconocedor), (1, "LEX-001", "Ninguno"))
        self.assertEqual(reconocer_lexema("sino").tipo, T.PALABRA_RESERVADA)


class TestLexer(unittest.TestCase):
    def verificar(self, fuente, tokens, diagnosticos=()):
        obtenidos, diags = analizar(fuente)
        self.assertEqual(obtenidos, tokens, repr(fuente))
        self.assertEqual(diags, list(diagnosticos), repr(fuente))

    def test_basicos(self):
        self.verificar("numero x = 10;", [
            (T.PALABRA_RESERVADA, "numero", 1, 1), (T.IDENTIFICADOR, "x", 1, 8),
            (T.ASIGNACION, "=", 1, 10), (T.ENTERO, "10", 1, 12), (T.DELIMITADOR, ";", 1, 14)])
        self.verificar("7 8.25", [(T.ENTERO, "7", 1, 1), (T.DECIMAL, "8.25", 1, 3)])

    def test_maximal_munch(self):
        self.verificar("a>=b", [(T.IDENTIFICADOR, "a", 1, 1), (T.OPERADOR_RELACIONAL, ">=", 1, 2),
                                (T.IDENTIFICADOR, "b", 1, 4)])
        self.verificar("a>b", [(T.IDENTIFICADOR, "a", 1, 1), (T.OPERADOR_RELACIONAL, ">", 1, 2),
                               (T.IDENTIFICADOR, "b", 1, 3)])
        self.verificar("<=<==", [(T.OPERADOR_RELACIONAL, "<=", 1, 1),
                                 (T.OPERADOR_RELACIONAL, "<=", 1, 3), (T.ASIGNACION, "=", 1, 5)])
        self.verificar("!x!=y", [(T.OPERADOR_LOGICO, "!", 1, 1), (T.IDENTIFICADOR, "x", 1, 2),
                                 (T.OPERADOR_RELACIONAL, "!=", 1, 3), (T.IDENTIFICADOR, "y", 1, 5)])
        self.verificar("a= =b", [(T.IDENTIFICADOR, "a", 1, 1), (T.ASIGNACION, "=", 1, 2),
                                 (T.ASIGNACION, "=", 1, 4), (T.IDENTIFICADOR, "b", 1, 5)])
        self.verificar("a/b", [(T.IDENTIFICADOR, "a", 1, 1), (T.OPERADOR_ARITMETICO, "/", 1, 2),
                               (T.IDENTIFICADOR, "b", 1, 3)])

    def test_comentarios(self):
        self.verificar("a // c\nb", [(T.IDENTIFICADOR, "a", 1, 1), (T.COMENTARIO, "// c", 1, 3),
                                     (T.IDENTIFICADOR, "b", 2, 1)])
        self.verificar("/* a\n b */ c", [(T.COMENTARIO, "/* a\n b */", 1, 1),
                                        (T.IDENTIFICADOR, "c", 2, 7)])

    def test_reservadas_y_mayusculas(self):
        self.verificar("si2 sino", [(T.IDENTIFICADOR, "si2", 1, 1), (T.PALABRA_RESERVADA, "sino", 1, 5)])
        self.verificar("Inicio", [(T.IDENTIFICADOR, "Inicio", 1, 1)])

    def test_cadenas_validas(self):
        self.verificar(r'"ok\n\t\"\\"', [(T.CADENA, r'"ok\n\t\"\\"', 1, 1)])
        self.verificar('"" ""', [(T.CADENA, '""', 1, 1), (T.CADENA, '""', 1, 4)])

    def test_cadenas_con_error(self):
        self.verificar('"hola', [(T.ERROR, '"hola', 1, 1)], [("LEX-002", 1, 1, '"hola')])
        self.verificar('"a\nb', [(T.ERROR, '"a', 1, 1), (T.IDENTIFICADOR, "b", 2, 1)],
                       [("LEX-002", 1, 1, '"a')])
        self.verificar('"a\\', [(T.ERROR, '"a\\', 1, 1)], [("LEX-002", 1, 1, '"a\\')])
        self.verificar('"a\\qb" x', [(T.ERROR, '"a\\qb"', 1, 1), (T.IDENTIFICADOR, "x", 1, 8)],
                       [("LEX-006", 1, 3, "\\q")])
        self.verificar('"a\\qb\\zc"', [(T.ERROR, '"a\\qb\\zc"', 1, 1)],
                       [("LEX-006", 1, 3, "\\q"), ("LEX-006", 1, 6, "\\z")])
        self.verificar('"a\\qb', [(T.ERROR, '"a\\qb', 1, 1)], [("LEX-002", 1, 1, '"a\\qb')])

    def test_numeros_mal_formados(self):
        self.verificar("x=3.;", [(T.IDENTIFICADOR, "x", 1, 1), (T.ASIGNACION, "=", 1, 2),
                                 (T.ERROR, "3.", 1, 3), (T.DELIMITADOR, ";", 1, 5)],
                       [("LEX-003", 1, 3, "3.")])
        for texto in ("3.4.5", "3..5", ".5", "1.5abc"):
            self.verificar(texto, [(T.ERROR, texto, 1, 1)], [("LEX-003", 1, 1, texto)])
        for texto in ("12abc", "1_000", "12abc.5"):
            self.verificar(texto, [(T.ERROR, texto, 1, 1)], [("LEX-004", 1, 1, texto)])
        self.verificar("x1.5", [(T.IDENTIFICADOR, "x1", 1, 1), (T.ERROR, ".5", 1, 3)],
                       [("LEX-003", 1, 3, ".5")])

    def test_duraciones_validas(self):
        for texto in ("10s", "500ms", "5m", "2h", "007s"):
            self.verificar(texto, [(T.DURACION, texto, 1, 1)])

    def test_duraciones_mal_escritas(self):
        for texto in ("10x", "10sx", "5mm", "10S", "5min", "10seg"):
            self.verificar(texto, [(T.ERROR, texto, 1, 1)], [("LEX-004", 1, 1, texto)])
        for texto in ("3.5s", "1.5s"):
            self.verificar(texto, [(T.ERROR, texto, 1, 1)], [("LEX-003", 1, 1, texto)])

    def test_duracion_coincidencia_mas_larga_y_espacios(self):
        self.verificar("10ms", [(T.DURACION, "10ms", 1, 1)])
        self.verificar("10 s", [(T.ENTERO, "10", 1, 1), (T.IDENTIFICADOR, "s", 1, 4)])
        self.verificar("10s;", [(T.DURACION, "10s", 1, 1), (T.DELIMITADOR, ";", 1, 4)])
        self.verificar("s m h ms", [(T.IDENTIFICADOR, x, 1, c) for x, c in
                                    (("s", 1), ("m", 3), ("h", 5), ("ms", 7))])

    def test_caracteres_desconocidos(self):
        _, diags = analizar("x.")
        self.assertEqual(diags, [("LEX-001", 1, 2, ".")])
        lexer = Lexer("x.")
        lexer.analizar()
        self.assertIn("3.14", lexer.manejador.diagnosticos[0].sugerencia)
        self.verificar("@#", [(T.ERROR, "@", 1, 1), (T.ERROR, "#", 1, 2)],
                       [("LEX-001", 1, 1, "@"), ("LEX-001", 1, 2, "#")])
        self.assertEqual(analizar("'a'")[1], [("LEX-001", 1, 1, "'"), ("LEX-001", 1, 3, "'")])
        tokens, diags = analizar("año")
        self.assertEqual([t[1] for t in tokens], ["a", "ñ", "o"])
        self.assertEqual(diags, [("LEX-001", 1, 2, "ñ")])

    def test_ampersand_suelto(self):
        lexer = Lexer("a&&b&c")
        tokens = lexer.analizar()
        self.assertEqual((tokens[1].tipo, tokens[1].lexema, tokens[1].columna), (T.OPERADOR_LOGICO, "&&", 2))
        (diagnostico,) = lexer.manejador.diagnosticos
        self.assertEqual((diagnostico.codigo, diagnostico.columna), ("LEX-001", 5))
        self.assertIn("&&", diagnostico.sugerencia)

    def test_longitud_de_identificador(self):
        self.verificar("x" * 32, [(T.IDENTIFICADOR, "x" * 32, 1, 1)])
        self.verificar("x" * 33, [(T.ERROR, "x" * 33, 1, 1)], [("LEX-005", 1, 1, "x" * 33)])

    def test_bloque_sin_cerrar(self):
        fuente = "/* sin cerrar\n x"
        self.verificar(fuente, [(T.ERROR, fuente, 1, 1)], [("LEX-007", 1, 1, fuente)])

    def test_errores_consecutivos(self):
        tokens, diags = analizar('3. 12a @ "x')
        self.assertEqual([t[0] for t in tokens], [T.ERROR] * 4)
        self.assertEqual([(d[0], d[2]) for d in diags],
                         [("LEX-003", 1), ("LEX-004", 4), ("LEX-001", 8), ("LEX-002", 10)])

    def test_entradas_triviales(self):
        self.verificar("", [])
        self.verificar("  \n\t ", [])
        self.verificar("\tx\r\ny", [(T.IDENTIFICADOR, "x", 1, 2), (T.IDENTIFICADOR, "y", 2, 1)])
        self.verificar("x x x", [(T.IDENTIFICADOR, "x", 1, 1), (T.IDENTIFICADOR, "x", 1, 3),
                                 (T.IDENTIFICADOR, "x", 1, 5)])

    def test_generador_perezoso(self):
        lexer = Lexer("a @")
        generador = lexer.tokens()
        self.assertEqual(next(generador).lexema, "a")
        self.assertEqual(lexer.manejador.cantidad(), 0)
        next(generador)
        self.assertEqual(lexer.manejador.cantidad(), 1)

    def test_manejador_inyectado(self):
        from core.errores import ManejadorErrores
        manejador = ManejadorErrores()
        lexer = Lexer("@", manejador)
        lexer.analizar()
        self.assertIs(lexer.manejador, manejador)
        self.assertEqual(manejador.cantidad(), 1)

    def test_entrada_grande(self):
        fuente = "numero x1 = 10 + 2.5; // c\n" * 5000
        inicio = time.perf_counter()
        lexer = Lexer(fuente)
        tokens = lexer.analizar()
        self.assertLess(time.perf_counter() - inicio, 5)
        self.assertEqual(len(tokens), 40000)
        self.assertEqual(tokens[-1].linea, 5000)
        self.assertEqual(lexer.manejador.cantidad(), 0)


class TestEjemplos(unittest.TestCase):
    def leer(self, nombre):
        return (RAIZ / "ejemplos" / nombre).read_text(encoding="utf-8").replace("\r\n", "\n")

    def test_correcto(self):
        lexer = Lexer(self.leer("correcto.flow"))
        tokens = lexer.analizar()
        self.assertEqual(len(tokens), 111)
        self.assertEqual(sum(t.tipo == T.DURACION for t in tokens), 1)
        duracion = next(t for t in tokens if t.tipo == T.DURACION)
        self.assertEqual((duracion.lexema, duracion.linea, duracion.columna), ("30s", 15, 17))
        self.assertEqual(lexer.manejador.cantidad(), 0)
        primero = next(t for t in tokens if t.es_significativo)
        ultimo = [t for t in tokens if t.es_significativo][-1]
        self.assertEqual((primero.lexema, primero.linea, primero.columna), ("inicio", 2, 1))
        self.assertEqual((ultimo.lexema, ultimo.linea, ultimo.columna), ("fin", 29, 1))

    def test_casos_limite(self):
        lexer = Lexer(self.leer("casos_limite.flow"))
        self.assertEqual(len(lexer.analizar()), 139)
        self.assertEqual(lexer.manejador.cantidad(), 0)

    def test_incorrecto(self):
        lexer = Lexer(self.leer("incorrecto.flow"))
        tokens = lexer.analizar()
        self.assertEqual(len(tokens), 63)
        self.assertEqual(sum(t.tipo == T.ERROR for t in tokens), 15)
        esperados = [
            ("LEX-004", 2, 12, "2pi"), ("LEX-003", 2, 18, "3.14.15"), ("LEX-003", 3, 21, "5."),
            ("LEX-002", 4, 20, '"Hola mundo;'), ("LEX-006", 5, 21, "\\q"), ("LEX-001", 6, 24, "@"),
            ("LEX-001", 7, 29, "&"), ("LEX-005", 8, 12, "identificador_demasiado_largo_para_flowlang"),
            ("LEX-001", 10, 17, "'"), ("LEX-001", 10, 23, "'"), ("LEX-001", 12, 19, "$"),
            ("LEX-001", 12, 21, "#"), ("LEX-004", 13, 13, "5min"), ("LEX-003", 13, 27, "1.5s"),
        ]
        obtenidos = [(d.codigo, d.linea, d.columna, d.lexema) for d in lexer.manejador.diagnosticos]
        self.assertEqual(obtenidos[:14], esperados)
        self.assertEqual(obtenidos[14][:3], ("LEX-007", 14, 1))
        self.assertEqual(len(obtenidos), 15)


if __name__ == "__main__":
    unittest.main()
