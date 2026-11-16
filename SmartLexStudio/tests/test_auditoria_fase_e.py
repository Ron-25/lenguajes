"""Regresiones de la auditoría de la Fase E (literales de duración)."""
import re
import unittest
from pathlib import Path

from core.lexer import reconocer_lexema

RAIZ = Path(__file__).resolve().parent.parent
GUIA_HTML = RAIZ / "docs" / "guia_presentacion.html"


class TestGuiaRecorridosDeDuracion(unittest.TestCase):
    """AUD-38: los recorridos de duración que cita la guía son los que produce el AFD."""

    def test_recorridos_de_la_guia_coinciden_con_el_afd(self):
        html = GUIA_HTML.read_text(encoding="utf-8")
        for lexema in ("10s", "500ms", "10seg"):
            with self.subTest(lexema=lexema):
                hallado = re.search(rf"<code>{lexema}</code> → ((?:q\d+,? ?)+)[→;]", html)
                self.assertIsNotNone(hallado, f"la guía ya no cita {lexema}")
                citado = tuple(re.findall(r"q\d+", hallado.group(1)))
                self.assertEqual(citado, reconocer_lexema(lexema).recorrido)


if __name__ == "__main__":
    unittest.main()
