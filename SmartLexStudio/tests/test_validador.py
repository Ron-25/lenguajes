"""Pruebas del validador estructural (reglas E1-E4)."""
from __future__ import annotations

import unittest
from pathlib import Path

from core.lexer import Lexer
from core.validador import validar_estructura

RAIZ = Path(__file__).resolve().parent.parent


def validar(fuente: str):
    return [(d.codigo, d.linea, d.columna, d.lexema)
            for d in validar_estructura(Lexer(fuente).analizar())]


class TestValidador(unittest.TestCase):
    def test_validos(self):
        self.assertEqual(validar("inicio fin"), [])
        self.assertEqual(validar("inicio si (x) { y = (1); } fin"), [])
        self.assertEqual(validar('inicio // (\n "(" fin'), [])

    def test_vacio(self):
        for fuente in ("", "// solo comentario", "@"):
            self.assertEqual(validar(fuente), [("SIN-001", 1, 1, "")], repr(fuente))

    def test_inicio_y_fin(self):
        self.assertEqual(validar("x = 1; fin"), [("SIN-002", 1, 1, "x")])
        self.assertEqual(validar("inicio x = 1;"), [("SIN-003", 1, 13, ";")])
        self.assertEqual(validar("fin"), [("SIN-002", 1, 1, "fin")])

    def test_balance(self):
        self.assertEqual(validar("inicio ) fin"), [("SIN-004", 1, 8, ")")])
        self.assertEqual(validar("inicio ( fin"), [("SIN-005", 1, 8, "(")])
        self.assertEqual(validar("inicio ( } fin"), [("SIN-006", 1, 10, "}")])
        self.assertEqual(validar("inicio { ( fin"), [("SIN-005", 1, 8, "{"), ("SIN-005", 1, 10, "(")])

    def test_incorrecto_flow(self):
        fuente = (RAIZ / "ejemplos" / "incorrecto.flow").read_text(encoding="utf-8")
        self.assertEqual([d[:3] for d in validar(fuente)], [("SIN-005", 9, 8), ("SIN-003", 12, 22)])


if __name__ == "__main__":
    unittest.main()
