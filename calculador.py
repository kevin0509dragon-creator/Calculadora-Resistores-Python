import tkinter as tk
from tkinter import ttk, messagebox
import itertools
import threading
import math

def mostrar_instrucciones():
    texto = (
        "📌 INSTRUCCIONES DE USO\n\n"
        "1. Ingresa la resistencia teórica que necesitas (ej. 330, 4.7k, 4,7k, 1M).\n"
        "2. Selecciona la norma comercial de tolerancia.\n"
        "3. Presiona 'Calcular'. El algoritmo evaluará todas las topologías "
        "y te dibujará la resistencia con su código de colores exacto."
    )
    messagebox.showinfo("¿Cómo funciona?", texto)

def decodificar_entrada(texto):
    texto = texto.strip().replace(" ", "").replace(",", ".")
    if not texto:
        raise ValueError("Entrada vacía")
    
    if texto.endswith('k') or texto.endswith('K'): return float(texto[:-1]) * 1e3
    elif texto.endswith('M'): return float(texto[:-1]) * 1e6
    elif texto.endswith('m'): return float(texto[:-1]) * 1e-3
    elif texto.endswith('G') or texto.endswith('g'): return float(texto[:-1]) * 1e9
    
    valor = float(texto)
    if not math.isfinite(valor) or valor <= 0:
        raise ValueError("El valor debe ser positivo y finito")
    return valor

def obtener_lista_colores(valor, tol_str):
    if valor <= 0: return []
    colores = ["Negro", "Marrón", "Rojo", "Naranja", "Amarillo", "Verde", "Azul", "Violeta", "Gris", "Blanco"]
    mult_colores = {-3: "?", -2: "Plata", -1: "Oro", 0: "Negro", 1: "Marrón", 2: "Rojo", 3: "Naranja", 
                    4: "Amarillo", 5: "Verde", 6: "Azul", 7: "Violeta", 8: "Gris", 9: "Blanco"}
    
    valor = round(valor, 6)
    exp = int(math.floor(math.log10(valor)))
    
    if "1%" in tol_str:
        tol_color = "Marrón"
        norm = round(valor / (10**(exp - 2)))
        mult = exp - 2
        if norm >= 1000:
            norm //= 10
            mult += 1
        d1, d2, d3 = (norm // 100) % 10, (norm // 10) % 10, norm % 10
        return [colores[int(d1)], colores[int(d2)], colores[int(d3)], mult_colores.get(mult, '?'), tol_color]
    else:
        tol_color = "Oro" if "5%" in tol_str else "Plata"
        norm = round(valor / (10**(exp - 1)))
        mult = exp - 1
        if norm >= 100:
            norm //= 10
            mult += 1
        d1, d2 = (norm // 10) % 10, norm % 10
        return [colores[int(d1)], colores[int(d2)], mult_colores.get(mult, '?'), tol_color]

def dibujar_resistencia(parent, valor, tol_str):
    hex_colors = {
        "Negro": "#000000", "Marrón": "#8B4513", "Rojo": "#FF0000", "Naranja": "#FF8C00", 
        "Amarillo": "#FFFF00", "Verde": "#008000", "Azul": "#0000FF", "Violeta": "#800080", 
        "Gris": "#808080", "Blanco": "#FFFFFF", "Oro": "#FFD700", "Plata": "#C0C0C0", "?": "#FF00FF"
    }
    bg_color = "#2d2d2d"
    body_color = "#85c1e9" if "1%" in tol_str else "#E8C396" 

    val_str = f"{valor/1e6:g} MΩ" if valor >= 1e6 else f"{valor/1e3:g} kΩ" if valor >= 1e3 else f"{valor:g} Ω"

    frame = tk.Frame(parent, bg=bg_color)
    canvas = tk.Canvas(frame, width=100, height=30, bg=bg_color, highlightthickness=0)
    canvas.pack()
    tk.Label(frame, text=val_str, bg=bg_color, fg="#ffffff", font=("Consolas", 10, "bold")).pack()

    canvas.create_line(0, 15, 15, 15, fill="#a0a0a0", width=2)
    canvas.create_line(85, 15, 100, 15, fill="#a0a0a0", width=2)
    canvas.create_polygon(15, 10, 20, 5, 80, 5, 85, 10, 85, 20, 80, 25, 20, 25, 15, 20, fill=body_color, outline="#555555")

    colores = obtener_lista_colores(valor, tol_str)
    x_pos = [25, 38, 51, 72] if len(colores) == 4 else [22, 33, 44, 55, 72]
    
    for i, c in enumerate(colores):
        canvas.create_rectangle(x_pos[i], 5, x_pos[i]+5, 25, fill=hex_colors.get(c, "#000000"), outline="")
    return frame

def formatear_configuracion(tipo, comp):
    def f(v): return f"{v/1e6:g} MΩ" if v >= 1e6 else f"{v/1e3:g} kΩ" if v >= 1e3 else f"{v:g} Ω"
    if tipo == "1": return "➔ 1 Resistor:"
    elif tipo == "2S": return f"➔ 2 en Serie:\n   {f(comp[0])} + {f(comp[1])}"
    elif tipo == "2P": return f"➔ 2 en Paralelo:\n   {f(comp[0])} || {f(comp[1])}"
    elif tipo == "3S": return f"➔ 3 en Serie:\n   {f(comp[0])} + {f(comp[1])} + {f(comp[2])}"
    elif tipo == "3P": return f"➔ 3 en Paralelo:\n   {f(comp[0])} || {f(comp[1])} || {f(comp[2])}"
    elif tipo == "3M1": return f"➔ Mixto:\n   ({f(comp[0])} || {f(comp[1])}) + {f(comp[2])}"
    elif tipo == "3M2": return f"➔ Mixto:\n   ({f(comp[0])} + {f(comp[1])}) || {f(comp[2])}"
    return ""

def procesar_hilo_seguro(target, tol_str):
    try:
        algoritmo_busqueda(target, tol_str)
    except Exception as e:
        root.after(0, restaurar_interfaz_error, str(e))

def restaurar_interfaz_error(mensaje):
    btn_calcular.config(state=tk.NORMAL, text="Calcular Mejor Combinación")
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    texto_resultado.insert(tk.END, f"Error durante el cálculo: {mensaje}")
    texto_resultado.config(state="disabled")

def iniciar_calculo():
    try:
        objetivo = decodificar_entrada(entrada_res.get())
    except ValueError as e:
        messagebox.showerror("Error", f"Entrada inválida: {str(e)}")
        return

    btn_calcular.config(state=tk.DISABLED, text="Evaluando topologías...")
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    texto_resultado.insert(tk.END, "Optimizando rutas matemáticas...\n\nPor favor, espera ⏳")
    texto_resultado.config(state="disabled")

    threading.Thread(target=procesar_hilo_seguro, args=(objetivo, combo_tol.get()), daemon=True).start()

def algoritmo_busqueda(target, tol_str):
    bases_10 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
    bases_5 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 
               3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    bases_1 = [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 
               1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74, 
               1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 
               2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 
               3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12, 
               4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 
               5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32, 
               7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76]

    if "10%" in tol_str: bases, limite_tol = bases_10, 10
    elif "5%" in tol_str: bases, limite_tol = bases_5, 5
    else: bases, limite_tol = bases_1, 1

    multiplicadores = [10**i for i in range(-2, 7)]
    todos_r = sorted(list({round(b * m, 6) for b in bases for m in multiplicadores}))
    
    # Pools dinámicos para optimización
    pool_amplio = [r for r in todos_r if target / 100 <= r <= target * 100]
    pool_estricto = [r for r in todos_r if target / 10 <= r <= target * 10]

    mejores = {1: (float('inf'), 0, [], ""), 2: (float('inf'), 0, [], ""), 3: (float('inf'), 0, [], "")}

    for r in pool_amplio:
        if abs(target - r) < mejores[1][0]: mejores[1] = (abs(target - r), r, [r], "1")

    for r1, r2 in itertools.combinations_with_replacement(pool_amplio, 2):
        req_s = r1 + r2
        if abs(target - req_s) < mejores[2][0]: mejores[2] = (abs(target - req_s), req_s, [r1, r2], "2S")
        req_p = (r1 * r2) / (r1 + r2)
        if abs(target - req_p) < mejores[2][0]: mejores[2] = (abs(target - req_p), req_p, [r1, r2], "2P")

    for r1, r2, r3 in itertools.combinations_with_replacement(pool_estricto, 3):
        if r1==0 or r2==0 or r3==0: continue
        req_s = r1 + r2 + r3
        if abs(target - req_s) < mejores[3][0]: mejores[3] = (abs(target - req_s), req_s, [r1, r2, r3], "3S")
        req_p = 1 / (1/r1 + 1/r2 + 1/r3)
        if abs(target - req_p) < mejores[3][0]: mejores[3] = (abs(target - req_p), req_p, [r1, r2, r3], "3P")
        
        for a, b, c in [(r2, r3, r1), (r1, r3, r2), (r1, r2, r3)]:
            mix1 = ((a * b) / (a + b)) + c
            if abs(target - mix1) < mejores[3][0]: mejores[3] = (abs(target - mix1), mix1, [a, b, c], "3M1")
            mix2 = ((a + b) * c) / (a + b + c)
            if abs(target - mix2) < mejores[3][0]: mejores[3] = (abs(target - mix2), mix2, [a, b, c], "3M2")

    resultados_finales = {}
    for num in [1, 2, 3]:
        diff, req, comp, tipo = mejores[num]
        resultados_finales[num] = (diff, req, formatear_configuracion(tipo, comp), comp)

    root.after(0, mostrar_resultados, target, resultados_finales, limite_tol, tol_str)

def mostrar_resultados(target, resultados_finales, limite_tol, tol_str):
    btn_calcular.config(state=tk.NORMAL, text="Calcular Mejor Combinación")
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    
    res_texto_init = f"🎯 Resistencia Deseada: {target} Ω (Margen {limite_tol}%)\n" + "-"*75 + "\n"
    texto_resultado.insert(tk.END, res_texto_init)

    for num in [1, 2, 3]:
        diff, req, config, comp = resultados_finales[num]
        error = (diff / target) * 100
        estado = "✓ Cumple" if error <= limite_tol else "✗ Falla"
        texto_resultado.insert(tk.END, f"{config}\n   = {req:.3f} Ω  (Error: {error:.4f}% - {estado})\n")

        frame_imagenes = tk.Frame(texto_resultado, bg="#2d2d2d")
        for val in comp:
            dibujar_resistencia(frame_imagenes, val, tol_str).pack(side=tk.LEFT, padx=10, pady=5)
        texto_resultado.window_create(tk.END, window=frame_imagenes)
        texto_resultado.insert(tk.END, "\n\n")
    texto_resultado.config(state="disabled")

root = tk.Tk()
root.title("Calculadora de Resistores PRO (Gráficos Vectoriales y Optimizada)")
ancho, alto = 650, 720
root.geometry(f"{ancho}x{alto}+{(root.winfo_screenwidth() // 2) - (ancho // 2)}+{(root.winfo_screenheight() // 2) - (alto // 2)}")
root.configure(bg="#1a1a1a")

style = ttk.Style()
style.theme_use('clam')
style.configure("TLabel", background="#1a1a1a", foreground="#f0f0f0", font=("Segoe UI", 12))
style.configure("TButton", font=("Segoe UI", 11, "bold"), background="#007acc", foreground="#ffffff", borderwidth=0)

ttk.Button(root, text="💡 ¿Cómo funciona?", command=mostrar_instrucciones).pack(pady=(15, 0), ipadx=5, ipady=2)
ttk.Label(root, text="Resistencia objetivo (ej. 220, 4.7k, 1M):").pack(pady=(10, 5))
entrada_res = ttk.Entry(root, font=("Segoe UI", 12), justify="center")
entrada_res.pack(pady=5, ipadx=10, ipady=3)

ttk.Label(root, text="Tolerancia y Serie Comercial:").pack(pady=(10, 5))
combo_tol = ttk.Combobox(root, values=["10% (E12)", "5% (E24)", "1% (E96)"], state="readonly", font=("Segoe UI", 12), justify="center")
combo_tol.current(2)
combo_tol.pack(pady=5, ipadx=10, ipady=3)

btn_calcular = ttk.Button(root, text="Calcular Mejor Combinación", command=iniciar_calculo)
btn_calcular.pack(pady=15, ipadx=10, ipady=5)

frame_resultados = tk.Frame(root, bg="#2d2d2d")
frame_resultados.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
scrollbar = ttk.Scrollbar(frame_resultados)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
texto_resultado = tk.Text(frame_resultados, font=("Consolas", 10), bg="#2d2d2d", fg="#a6e22e", relief="flat", wrap=tk.WORD, yscrollcommand=scrollbar.set)
texto_resultado.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
scrollbar.config(command=texto_resultado.yview)

texto_resultado.insert(tk.END, "Esperando datos...")
texto_resultado.config(state="disabled")

root.mainloop()