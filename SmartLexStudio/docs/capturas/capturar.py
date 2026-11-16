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


def terminar(ruta):
    """Abre el ejemplo y lo analiza completo (pausa por linea 0)."""
    v.cabecera.establecer_pausa(0)
    v.abrir_archivo(ruta); v.analizar()
    while v.estado != "TERMINADO":
        esperar(100)
    esperar(300)


esperar(500)
terminar("ejemplos/correcto.flow")
pr.mostrar("tokens"); esperar(300); shot("1_correcto_tokens")
pr.mostrar("simbolos"); esperar(500); shot("2_tabla_simbolos")
pr.mostrar("resumen"); esperar(500); shot("3_resumen")
pr.arbol_tokens.selection_set(pr.arbol_tokens.get_children()[11]); pr.mostrar("automatas")
esperar(500); shot("4_automatas")
terminar("ejemplos/incorrecto.flow")
pr.mostrar("simbolos")
fila = v.panel_errores.arbol_errores.get_children()[3]
v.panel_errores.arbol_errores.selection_set(fila); v.panel_errores.arbol_errores.see(fila)
esperar(500); shot("5_incorrecto_errores")
# analisis detenido a mitad: pausa de 300 ms por linea y se detiene tras unas lineas
v.cabecera.establecer_pausa(300)
v.abrir_archivo("ejemplos/incorrecto.flow"); v.analizar()
esperar(2300); v.detener(); pr.mostrar("tokens")
esperar(500); shot("6_durante_evaluacion")
v.destroy()
