"""Driver de capturas: abre la app real, analiza ejemplos y toma screenshots de la ventana."""
import subprocess, sys, os
proy, salida = sys.argv[1], sys.argv[2]
sys.path.insert(0, proy); os.chdir(proy)
from tkinter import messagebox
messagebox.askyesno = lambda *a, **k: True
messagebox.showinfo = lambda *a, **k: None
from ui.interfaz import VentanaPrincipal
v = VentanaPrincipal(solicitar_archivo=False)
v.geometry("1440x880+0+30"); v.lift(); v.attributes("-topmost", True)
def al_frente():
    """Trae la ventana al primer plano (si no, screencapture fotografia otra aplicacion)."""
    subprocess.run(["osascript", "-e", f'tell application "System Events" to set frontmost of '
                    f'(first process whose unix id is {os.getpid()}) to true'], capture_output=True)
    v.lift(); v.focus_force()
def shot(nombre):
    """Fotografia la ventana por su id (aunque otra aplicacion la tape); si falla, lo informa."""
    al_frente(); v.update(); import time; time.sleep(0.3); v.update()
    aqui = os.path.dirname(os.path.abspath(__file__))
    ident = subprocess.run(["swift", f"{aqui}/id_ventana.swift", str(os.getpid()), str(v.winfo_width())], capture_output=True, text=True)
    wid = ident.stdout.strip()
    if not wid:
        print("sin id de ventana:", ident.stderr[-300:])
    r = subprocess.run(["screencapture", "-x", "-o", f"-l{wid}", f"{salida}/{nombre}.png"], capture_output=True, text=True)
    print(nombre, wid, r.returncode, r.stderr.strip())
pr = v.panel_resultados


def esperar(ms):
    """Atiende eventos (y los `after` del analisis) durante `ms` milisegundos."""
    import time
    fin = time.time() + ms / 1000
    while time.time() < fin:
        v.update(); time.sleep(0.01)


def paso(espera, accion):
    esperar(espera); accion()


esperar(500)
v.abrir_archivo("ejemplos/correcto.flow"); v.analizar()
esperar(6000); v.mostrar_herramienta("tokens"); esperar(300); shot("1_correcto_tokens")
v.mostrar_herramienta("simbolos"); esperar(500); shot("2_tabla_simbolos")
v.mostrar_herramienta("estadisticas"); esperar(500); shot("3_estadisticas")
pr.arbol_tokens.selection_set(pr.arbol_tokens.get_children()[11]); v.mostrar_herramienta("educativo")
esperar(500); shot("4_modo_educativo")
v.abrir_archivo("ejemplos/incorrecto.flow"); v.analizar()
esperar(6000)
v.mostrar_herramienta("tokens"); v.mostrar_herramienta("problemas")
fila = v.problemas.arbol_errores.get_children()[3]
v.problemas.arbol_errores.selection_set(fila); v.problemas.arbol_errores.see(fila)
esperar(500); shot("5_incorrecto_errores")
v.alternar_herramienta("proyecto"); v.alternar_herramienta("problemas")
esperar(500); shot("6_paneles_ocultos")
v.destroy()
