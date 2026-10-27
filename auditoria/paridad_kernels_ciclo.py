#!/usr/bin/env python3
"""
M2-b — Paridad bit a bit de los kernels de ciclo/saturador triplicados en Fase 3 (fastmath=True),
Fase 4 y Fase 4.5 A (fastmath=False). Extrae las funciones POR AST (no importa los scripts, que
ejecutan trabajo pesado al importar) y las compila tal cual están escritas.

Solo LEE. Uso: python -I paridad_kernels_ciclo.py DIR_REPO [N] [SEMILLAS]
Archivos esperados en DIR_REPO (nombres canónicos): Fase_3.py, Fase_4_V12_0.py, Fase_4_5_V_12_0_A.py
"""
import ast, sys, os, numpy as np
from numba import njit

repo = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 200_000
SEMILLAS = int(sys.argv[3]) if len(sys.argv) > 3 else 5
ARCHIVOS = {'F3': 'Fase_3.py', 'F4': 'Fase_4_V12_0.py', 'F45A': 'Fase_4_5_V_12_0_A.py'}
FUNCS = ['calcular_extremos_numba', 'calcular_acum_ciclo_numba', 'obtener_extremos_ciclo_numba', 'rolling_median_causal_numba']

def extraer(ruta):
    src = open(ruta, encoding='utf-8').read(); lineas = src.split('\n')
    ns = {'np': np, 'njit': njit, 'math': __import__('math')}
    flags = {}
    for nodo in ast.parse(src).body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name in FUNCS:
            ini = min([d.lineno for d in nodo.decorator_list] + [nodo.lineno]) - 1
            texto = '\n'.join(lineas[ini:nodo.end_lineno])
            # cache=True exige un archivo real (locator); en la copia extraída se desactiva. No afecta a la numérica.
            texto = texto.replace('cache=True', 'cache=False')
            dec =ast.get_source_segment(src, nodo.decorator_list[0]) if nodo.decorator_list else ''
            flags[nodo.name] = dec.replace('@njit', '').strip('()')
            exec(compile(texto, f"{ruta}:{nodo.name}", 'exec'), ns)
    faltan = [f for f in FUNCS if f not in ns]
    if faltan: raise SystemExit(f"{ruta}: faltan {faltan}")
    return {f: ns[f] for f in FUNCS}, flags

IMPL, FLAGS = {}, {}
for k, a in ARCHIVOS.items():
    IMPL[k], FLAGS[k] = extraer(os.path.join(repo, a))
    print(f"{k}: " + " | ".join(f"{f.replace('_numba','')}[{FLAGS[k][f][:40]}]" for f in FUNCS))

def canal(I, base, metrica, modo, fifo=100):
    signos = np.sign(base).astype(np.float32)
    signos[signos == 0] = 1.0
    cambios = np.concatenate(([0], (signos[1:] != signos[:-1]).astype(np.int32))).astype(np.int32)
    ciclos = cambios.cumsum().astype(np.int32)
    acum = I['calcular_acum_ciclo_numba'](metrica.copy(), cambios)
    ext = I['calcular_extremos_numba'](signos, acum, cambios)
    mx, mn = I['obtener_extremos_ciclo_numba'](ciclos, acum, signos, int(ciclos[-1]))
    sat = I['rolling_median_causal_numba'](mn, -1, fifo) if modo == 'inf' else I['rolling_median_causal_numba'](mx, 1, fifo)
    return {'acum': acum, 'extremo': ext, 'max_ciclo': mx, 'min_ciclo': mn, 'sat': sat[ciclos]}

def iguales(a, b):
    return bool(np.array_equal(a, b, equal_nan=True))

tot = {}
for semilla in range(SEMILLAS):
    rng = np.random.default_rng(semilla)
    base = np.convolve(rng.normal(size=N), np.ones(15) / 15, mode='same').astype(np.float32)   # ciclos de decenas de velas
    metrica = (rng.normal(size=N) * rng.gamma(2.0, 1.0, N)).astype(np.float32)
    for modo in ('inf', 'sup'):
        R = {k: canal(IMPL[k], base, metrica, modo) for k in IMPL}
        for otro in ('F4', 'F45A'):
            for campo in R['F3']:
                clave = (f"F3 vs {otro}", campo)
                ok = iguales(R['F3'][campo], R[otro][campo])
                d = np.nanmax(np.abs(R['F3'][campo].astype(np.float64) - R[otro][campo].astype(np.float64))) if not ok else 0.0
                t = tot.setdefault(clave, [0, 0, 0.0]); t[0] += 1; t[1] += (0 if ok else 1); t[2] = max(t[2], d)
        for campo in R['F4']:
            ok = iguales(R['F4'][campo], R['F45A'][campo])
            t = tot.setdefault(("F4 vs F45A", campo), [0, 0, 0.0]); t[0] += 1; t[1] += (0 if ok else 1)

print(f"\nN={N} velas, {SEMILLAS} semillas x 2 modos (inf/sup). 'difieren' = corridas con al menos 1 elemento distinto (bit a bit, NaN==NaN)")
for (par, campo), (n, mal, dmax) in sorted(tot.items()):
    print(f"{par:12s} {campo:10s} corridas={n:2d} difieren={mal:2d} max|Δ|={dmax:.3e}")
print("\nVEREDICTO:", "IDÉNTICOS bit a bit en todas las corridas" if all(m == 0 for _, m, _ in tot.values()) else "HAY DIFERENCIAS (ver tabla)")
