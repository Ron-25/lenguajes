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
def shot(nombre):
    v.update(); x, y, w, h = v.winfo_rootx(), v.winfo_rooty(), v.winfo_width(), v.winfo_height()
    r = subprocess.run(["screencapture", "-x", f"-R{x},{y-28},{w},{h+28}", f"{salida}/{nombre}.png"], capture_output=True, text=True)
    print(nombre, r.returncode, r.stderr.strip())
pr = v.panel_resultados
pasos = [
 (500, lambda: (v.abrir_archivo("ejemplos/correcto.flow"), v.analizar())),
 (6000, lambda: shot("1_correcto_tokens")),
 (300, lambda: (pr.seleccionar_pestana("simbolos"))),
 (800, lambda: shot("2_tabla_simbolos")),
 (300, lambda: (pr.seleccionar_pestana("estadisticas"))),
 (800, lambda: shot("3_estadisticas")),
 (300, lambda: (pr.arbol_tokens.selection_set(pr.arbol_tokens.get_children()[11]), pr.seleccionar_pestana("educativo"))),
 (800, lambda: shot("4_modo_educativo")),
 (300, lambda: (v.abrir_archivo("ejemplos/incorrecto.flow"), v.analizar())),
 (6000, lambda: (pr.seleccionar_pestana("errores"), pr.arbol_errores.selection_set(pr.arbol_errores.get_children()[3]))),
 (800, lambda: shot("5_incorrecto_errores")),
 (300, v.destroy),
]
t = 0
for espera, f in pasos:
    t += espera; v.after(t, f)
v.mainloop()
