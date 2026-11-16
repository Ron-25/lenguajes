"""Pruebas de integracion: servicio de analisis sobre los ejemplos y sesiones progresivas."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from application.analisis_service import (FASE_ESTRUCTURAL, FASE_LEXICA, SesionAnalisis,
                                          analizar_archivo, analizar_texto, explicar_token,
                                          tokenizar)
from application.archivos import ErrorArchivo
from config import reglas
from core.modelos import TipoToken, Token

RAIZ = Path(__file__).resolve().parent.parent
T = TipoToken


def ejemplo(nombre: str) -> Path:
    return RAIZ / "ejemplos" / nombre


class TestEjemplos(unittest.TestCase):
    def test_correcto(self):
        r = analizar_archivo(ejemplo("correcto.flow"))
        self.assertTrue(r.terminado and r.es_valida)
        self.assertEqual((len(r.tokens), len(r.diagnosticos)), (111, 0))
        e = r.tabla.estadisticas()
        self.assertEqual((len(r.tabla), e.capacidad, e.colisiones, e.redimensionados), (36, 79, 14, 2))
        self.assertEqual(r.conteo_por_tipo(), {
            T.PALABRA_RESERVADA: 21, T.IDENTIFICADOR: 21, T.ENTERO: 9, T.DECIMAL: 3, T.CADENA: 4,
            T.OPERADOR_ARITMETICO: 6, T.OPERADOR_RELACIONAL: 5, T.OPERADOR_LOGICO: 4,
            T.ASIGNACION: 7, T.DELIMITADOR: 29, T.COMENTARIO: 2})
        temperatura = r.tabla.buscar("temperatura")
        self.assertEqual((temperatura.tipo_dato, temperatura.linea_declaracion), ("numero", 5))
        self.assertEqual(r.tabla.buscar("bomba").tipo_dato, "dispositivo")
        self.assertEqual(r.tabla.buscar("humedad").apariciones, [(6, 13), (13, 30), (23, 9), (23, 19)])
        self.assertEqual(len(r.tabla.buscar("ciclos").apariciones), 5)
        self.assertEqual(r.tabla.buscar("45.5").valor, 45.5)

    def test_incorrecto(self):
        r = analizar_archivo(ejemplo("incorrecto.flow"))
        self.assertFalse(r.es_valida_lexicamente)
        self.assertFalse(r.es_valida_estructuralmente)
        self.assertFalse(r.es_valida)
        self.assertEqual(len(r.tokens), 57)
        self.assertEqual([d.codigo for d in r.diagnosticos], (
            ["LEX-004", "LEX-003", "LEX-003", "LEX-002", "LEX-006", "LEX-001", "LEX-001", "LEX-005",
             "LEX-001", "LEX-001", "LEX-001", "LEX-001", "LEX-007", "SIN-005", "SIN-003"]))
        self.assertEqual([(d.linea, d.columna) for d in r.diagnosticos][-2:], [(9, 8), (12, 22)])
        e = r.tabla.estadisticas()
        self.assertEqual((len(r.tabla), e.capacidad, e.colisiones), (18, 37, 7))
        self.assertEqual(r.lineas_invalidas(), [2, 3, 4, 5, 6, 7, 8, 10, 12, 13])

    def test_casos_limite(self):
        r = analizar_archivo(ejemplo("casos_limite.flow"))
        self.assertTrue(r.es_valida)
        self.assertEqual(len(r.tokens), 118)

    def test_archivo_inexistente_propaga_error(self):
        with self.assertRaises(ErrorArchivo):
            analizar_archivo(ejemplo("no_existe.flow"))


class TestAnalizarTexto(unittest.TestCase):
    def test_vacio(self):
        r = analizar_texto("")
        self.assertEqual(len(r.tokens), 0)
        self.assertEqual([d.codigo for d in r.diagnosticos], ["SIN-001"])
        self.assertFalse(r.es_valida)
        self.assertEqual((r.cantidad_lineas, r.cantidad_caracteres), (0, 0))

    def test_lexica_valida_pero_no_estructural(self):
        r = analizar_texto("x = 1;")
        self.assertTrue(r.es_valida_lexicamente)
        self.assertFalse(r.es_valida_estructuralmente)
        self.assertFalse(r.es_valida)
        self.assertEqual(r.cantidad_lineas, 1)

    def test_sesiones_independientes(self):
        a = analizar_texto("inicio x fin")
        b = analizar_texto("inicio x fin")
        self.assertIsNot(a.tabla, b.tabla)
        self.assertIsNot(a.manejador, b.manejador)

    def test_tokenizar(self):
        fuente = ejemplo("incorrecto.flow").read_text(encoding="utf-8")
        self.assertEqual(tokenizar(fuente), analizar_texto(fuente).tokens)


class TestSesion(unittest.TestCase):
    def test_pasos_lexicos(self):
        sesion = SesionAnalisis("inicio x = @ fin")
        pasos = []
        while (paso := sesion.siguiente_paso()) is not None and paso.fase == FASE_LEXICA:
            pasos.append(paso)
        self.assertEqual([p.numero for p in pasos], [1, 2, 3, 4, 5])
        self.assertEqual(pasos[3].token.tipo, T.ERROR)
        self.assertEqual([d.codigo for d in pasos[3].diagnosticos], ["LEX-001"])
        for i in (0, 1, 2, 4):
            self.assertEqual(pasos[i].diagnosticos, ())
        self.assertTrue(pasos[1].instalacion.es_nueva)
        self.assertIsNone(pasos[2].instalacion)

    def test_pasos_hasta_none(self):
        sesion = SesionAnalisis("inicio x = @ fin")
        self.assertEqual(len(list(sesion.pasos())), 5)
        self.assertTrue(sesion.terminada)
        self.assertIsNone(sesion.siguiente_paso())
        self.assertEqual(sesion.resultado.manejador.cantidad(), 1)

    def test_pasos_estructurales(self):
        pasos = list(SesionAnalisis("x = 1;").pasos())
        self.assertEqual([p.fase for p in pasos], [FASE_LEXICA] * 4 + [FASE_ESTRUCTURAL] * 2)
        for paso, codigo in zip(pasos[4:], ("SIN-002", "SIN-003")):
            self.assertIsNone(paso.token)
            self.assertEqual([d.codigo for d in paso.diagnosticos], [codigo])

    def test_progresividad(self):
        sesion = SesionAnalisis(ejemplo("incorrecto.flow").read_text(encoding="utf-8"))
        sesion.siguiente_paso()
        r = sesion.resultado
        self.assertEqual(len(r.tokens), 1)
        self.assertFalse(r.terminado)
        self.assertFalse(r.es_valida)
        self.assertIs(sesion.resultado, r)

    def test_terminar_a_mitad_equivale_a_analizar_texto(self):
        fuente = ejemplo("incorrecto.flow").read_text(encoding="utf-8")
        sesion = SesionAnalisis(fuente)
        for _ in range(10):
            sesion.siguiente_paso()
        parcial = sesion.terminar()
        completo = analizar_texto(fuente)
        self.assertEqual(parcial.tokens, completo.tokens)
        self.assertEqual(parcial.diagnosticos, completo.diagnosticos)
        self.assertEqual(len(parcial.tabla), len(completo.tabla))
        self.assertTrue(parcial.terminado)

    def test_descripcion(self):
        pasos = list(SesionAnalisis("inicio\n  x = @\nfin").pasos())
        paso_error = next(p for p in pasos if p.token and p.token.tipo == T.ERROR)
        self.assertIn("LEX-001", paso_error.descripcion)
        self.assertIn("2:7", paso_error.descripcion)
        paso_x = pasos[1]
        self.assertIn("2:3", paso_x.descripcion)
        self.assertIn("cubeta", paso_x.descripcion)
        self.assertIn("nueva", paso_x.descripcion)


class TestExplicarToken(unittest.TestCase):
    def test_decimal(self):
        e = explicar_token(Token(T.DECIMAL, "45.5", 6, 23))
        self.assertEqual(e.reconocedor, "AFD de números")
        self.assertEqual(e.recorrido, ("q0", "q1", "q1", "q2", "q3"))
        self.assertEqual(e.regex, reglas.INFO_CATEGORIAS[T.DECIMAL]["regex"])

    def test_reservada_operador_y_error(self):
        e = explicar_token(Token(T.PALABRA_RESERVADA, "si", 1, 1))
        self.assertIn(reglas.PALABRAS_RESERVADAS["si"], e.detalle)
        e = explicar_token(Token(T.OPERADOR_RELACIONAL, ">=", 1, 1))
        self.assertEqual(e.reconocedor, "Tabla de operadores y delimitadores")
        self.assertEqual(e.recorrido, ())
        e = explicar_token(Token(T.ERROR, "3.", 1, 1))
        self.assertIn("LEX-003", e.detalle)

    def test_con_tabla(self):
        r = analizar_texto("inicio numero x = 1; fin")
        token = next(t for t in r.tokens if t.lexema == "x")
        e = explicar_token(token, r.tabla)
        self.assertIn(f"cubeta {r.tabla.indice('x')}", e.detalle)
        self.assertIn("numero", e.detalle)


class TestDominioSinTkinter(unittest.TestCase):
    def test_dominio_sin_tkinter(self):
        codigo = ("import sys; import application.analisis_service, application.archivos; "
                  "assert 'tkinter' not in sys.modules")
        resultado = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ,
                                   capture_output=True, text=True)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)


if __name__ == "__main__":
    unittest.main()


class TestModoConsola(unittest.TestCase):
    def ejecutar(self, *argumentos, entrada="n\n"):
        return subprocess.run([sys.executable, "main.py", "--consola", *argumentos], cwd=RAIZ,
                              input=entrada, capture_output=True, text=True, encoding="utf-8")

    def test_consola_correcto(self):
        r = self.ejecutar("ejemplos/correcto.flow")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("VÁLIDA", r.stdout)
        self.assertNotIn("INVÁLIDA", r.stdout)

    def test_consola_incorrecto_con_tabla_y_sin_ruta(self):
        r = self.ejecutar(entrada="ejemplos/incorrecto.flow\ns\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("INVÁLIDA", r.stdout)
        self.assertIn("cubeta", r.stdout)

    def test_consola_archivo_inexistente(self):
        r = self.ejecutar("ejemplos/no_existe.flow")
        self.assertEqual(r.returncode, 1)
        self.assertIn("ARC-001", r.stdout)
