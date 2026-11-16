"""Punto de entrada de SmartLex Studio: interfaz grafica o, con --consola, modo texto."""
from __future__ import annotations

import sys

from application.analisis_service import analizar_archivo
from application.archivos import ErrorArchivo


def _modo_consola(argumentos: list[str]) -> int:
    """Analiza un archivo e imprime tokens, diagnosticos y veredicto (sin tkinter)."""
    ruta = argumentos[0] if argumentos else input("Archivo de entrada: ")
    try:
        r = analizar_archivo(ruta)
    except ErrorArchivo as error:
        d = error.diagnostico
        print(f"{d.codigo} {d.mensaje} {d.sugerencia}")
        return 1
    for n, t in enumerate(r.tokens, 1):
        print(f"{n:>4}  {t.linea}:{t.columna:<4} {t.tipo.value:<22} {t.lexema!r}")
    for d in r.diagnosticos:
        print(f"✗ {d.codigo} [{d.linea}:{d.columna}] {d.mensaje} {d.sugerencia}")
    print(f"Léxico: {'válido' if r.es_valida_lexicamente else 'inválido'} · "
          f"Estructura: {'válida' if r.es_valida_estructuralmente else 'inválida'}")
    print(f"Cadena de entrada: {'VÁLIDA' if r.es_valida else 'INVÁLIDA'} ({r.manejador.resumen()})")
    if input("¿Desea ver la tabla de símbolos? (s/n) ").strip().lower() == "s":
        for cubeta, entradas in enumerate(r.tabla.cubetas()):
            for e in entradas:
                print(f"cubeta {cubeta:>3}  hash {e.valor_hash:>10}  {e.lexema!r}  {e.categoria.value}  "
                      f"tipo={e.tipo_dato}  apariciones={len(e.apariciones)}")
    return 0


def main(argumentos: list[str]) -> int:
    """Devuelve el codigo de salida del proceso."""
    if argumentos and argumentos[0] == "--consola":
        return _modo_consola(argumentos[1:])
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print("No se pudo cargar tkinter. Instale Tk (en Linux: sudo apt install python3-tk; "
              "en macOS: brew install python-tk) o use el modo texto: python main.py --consola archivo.flow")
        return 1
    from ui.interfaz import VentanaPrincipal
    VentanaPrincipal().mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
