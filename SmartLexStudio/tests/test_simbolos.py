"""Pruebas de la funcion hash, la tabla de simbolos y el registro de tokens."""
from __future__ import annotations

import unittest

from core.lexer import Lexer
from core.modelos import TipoToken, Token
from core.simbolos import (TablaSimbolos, hash_polinomial, registrar_token,
                           siguiente_primo, valor_literal)

T = TipoToken


def ident(lexema: str, linea: int = 1, columna: int = 1) -> Token:
    return Token(T.IDENTIFICADOR, lexema, linea, columna)


class TestHashYPrimos(unittest.TestCase):
    def test_hash(self):
        esperados = {"": 0, "x": 120, "si": 3670, "10": 1567, "temperatura": 321701232,
                     "riego": 108509814, "activo": 2872016656}
        for lexema, valor in esperados.items():
            self.assertEqual(hash_polinomial(lexema), valor, lexema)

    def test_siguiente_primo(self):
        for n, primo in {1: 2, 17: 17, 34: 37, 74: 79, 158: 163}.items():
            self.assertEqual(siguiente_primo(n), primo)


class TestTabla(unittest.TestCase):
    def test_insercion_y_busqueda(self):
        tabla = TablaSimbolos()
        r = tabla.instalar(ident("x"))
        self.assertTrue(r.es_nueva)
        self.assertEqual(len(tabla), 1)
        self.assertIn("x", tabla)
        self.assertEqual(tabla.buscar("x").apariciones, [(1, 1)])
        self.assertIsNone(tabla.buscar("z"))

    def test_duplicados(self):
        tabla = TablaSimbolos()
        resultados = [tabla.instalar(ident("x", 1, c)) for c in (1, 5, 9)]
        self.assertEqual(len(tabla), 1)
        self.assertEqual(tabla.buscar("x").apariciones, [(1, 1), (1, 5), (1, 9)])
        for r in resultados[1:]:
            self.assertFalse(r.es_nueva)
            self.assertFalse(r.hubo_colision)

    def test_colisiones_naturales(self):
        for a, b, cubeta in (("si", "temperatura", 15), ("riego", "activo", 4), ("x", "total", 1)):
            tabla = TablaSimbolos(capacidad=17)
            primera = tabla.instalar(ident(a))
            segunda = tabla.instalar(ident(b))
            self.assertFalse(primera.hubo_colision)
            self.assertTrue(segunda.hubo_colision)
            self.assertEqual((tabla.indice(a), tabla.indice(b)), (cubeta, cubeta))
            self.assertEqual(tabla.colisiones, 1)
            self.assertEqual(len(tabla.cubetas()[cubeta]), 2)

    def test_colisiones_forzadas(self):
        tabla = TablaSimbolos(capacidad=5, funcion_hash=lambda s: 0, factor_carga_maximo=float("inf"))
        nombres = [f"v{i}" for i in range(10)]
        for nombre in nombres:
            tabla.instalar(ident(nombre))
        self.assertEqual((len(tabla), tabla.colisiones), (10, 9))
        self.assertEqual(len(tabla.cubetas()[0]), 10)
        self.assertTrue(all(tabla.buscar(n) is not None for n in nombres))
        self.assertEqual(tabla.estadisticas().cadena_mas_larga, 10)

    def test_forzadas_con_redimensionado_tambien_funciona(self):
        tabla = TablaSimbolos(capacidad=5, funcion_hash=lambda s: 0)
        for i in range(10):
            tabla.instalar(ident(f"v{i}"))
        self.assertEqual(len(tabla), 10)
        self.assertTrue(all(tabla.buscar(f"v{i}") for i in range(10)))

    def test_redimensionado(self):
        tabla = TablaSimbolos()
        nombres = [f"var{i}" for i in range(13)]
        resultados = [tabla.instalar(ident(n)) for n in nombres]
        self.assertFalse(any(r.redimensiono for r in resultados[:12]))
        self.assertTrue(resultados[12].redimensiono)
        self.assertEqual(tabla.capacidad, 37)
        for n in nombres:
            entrada = tabla.buscar(n)
            self.assertIn(entrada, tabla.cubetas()[tabla.indice(n)])
        self.assertEqual(resultados[12].indice, tabla.indice("var12"))

    def test_capacidad_no_cambia_antes_del_umbral(self):
        tabla = TablaSimbolos()
        for i in range(12):
            tabla.instalar(ident(f"var{i}"))
        self.assertEqual(tabla.capacidad, 17)

    def test_sin_redimensionado(self):
        tabla = TablaSimbolos(factor_carga_maximo=float("inf"))
        for i in range(100):
            tabla.instalar(ident(f"var{i}"))
        self.assertEqual(tabla.capacidad, 17)

    def test_capacidad_invalida(self):
        with self.assertRaises(ValueError):
            TablaSimbolos(capacidad=0)

    def test_estadisticas_coherentes(self):
        tabla = TablaSimbolos()
        for i in range(20):
            tabla.instalar(ident(f"var{i}"))
        e = tabla.estadisticas()
        self.assertEqual(e.cantidad, len(tabla))
        self.assertEqual(e.factor_carga, e.cantidad / e.capacidad)
        self.assertEqual(sum(len(c) for c in tabla.cubetas()), e.cantidad)
        self.assertEqual(len(tabla.cubetas()), e.capacidad)
        self.assertEqual(len(tabla.entradas()), e.cantidad)
        self.assertEqual(e.redimensionados, 1)


class TestValorLiteral(unittest.TestCase):
    def test_valores(self):
        self.assertEqual(valor_literal(Token(T.ENTERO, "007", 1, 1)), 7)
        self.assertEqual(valor_literal(Token(T.DECIMAL, "45.5", 1, 1)), 45.5)
        self.assertEqual(valor_literal(Token(T.CADENA, '"a\\n\\"b"', 1, 1)), 'a\n"b')
        self.assertIs(valor_literal(Token(T.PALABRA_RESERVADA, "verdadero", 1, 1)), True)
        self.assertIs(valor_literal(Token(T.PALABRA_RESERVADA, "falso", 1, 1)), False)
        self.assertIsNone(valor_literal(Token(T.PALABRA_RESERVADA, "si", 1, 1)))
        self.assertIsNone(valor_literal(ident("x")))


class TestRegistrarToken(unittest.TestCase):
    def registrar_fuente(self, fuente: str) -> TablaSimbolos:
        tabla = TablaSimbolos()
        anterior = None
        for token in Lexer(fuente).tokens():
            registrar_token(tabla, token, anterior)
            if token.es_significativo:
                anterior = token
        return tabla

    def test_no_instalables(self):
        tabla = TablaSimbolos()
        for tipo, lexema in ((T.OPERADOR_ARITMETICO, "+"), (T.ERROR, "@"), (T.COMENTARIO, "// x")):
            self.assertIsNone(registrar_token(tabla, Token(tipo, lexema, 1, 1)))
        self.assertEqual(len(tabla), 0)

    def test_declaracion(self):
        tabla = self.registrar_fuente("numero x = 1;\nx = 2;\ntexto x;")
        x = tabla.buscar("x")
        self.assertEqual((x.tipo_dato, x.linea_declaracion), ("numero", 1))
        self.assertEqual(len(x.apariciones), 3)

    def test_sin_declarar_y_literales(self):
        tabla = self.registrar_fuente('y = 5 + 2.5 + "a" + verdadero;')
        self.assertIsNone(tabla.buscar("y").tipo_dato)
        self.assertIsNone(tabla.buscar("y").linea_declaracion)
        for lexema, tipo, valor in (("5", "numero", 5), ("2.5", "decimal", 2.5),
                                    ('"a"', "texto", "a"), ("verdadero", "booleano", True)):
            entrada = tabla.buscar(lexema)
            self.assertEqual((entrada.tipo_dato, entrada.valor), (tipo, valor))


if __name__ == "__main__":
    unittest.main()
