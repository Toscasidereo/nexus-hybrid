#!/usr/bin/env python3
"""
H-FM-01 — Mide el efecto de fastmath=True de nexus_formulas_core.calcular_t_score_trade_numba
cuando se invoca desde un kernel compilado con fastmath=False (caso de Fase 4 y Fase 4.5).

Solo LEE el core. No modifica nada. Uso: python medir_fastmath_tscore.py DIR_REPO [N]
Compara tres cosas sobre las MISMAS entradas:
  A) llamador fastmath=False -> función del core (fastmath=True)           [lo que ejecuta producción]
  B) llamador fastmath=False -> copia estricta de la misma fórmula (py_func) [referencia estricta en Numba]
  C) numpy float64 puro, castear a float32                                  [referencia sin Numba]
"""
import sys, numpy as np
from numba import njit

repo = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 2_000_000
sys.path.insert(0, repo)
import nexus_formulas_core as core

f_core = core.calcular_t_score_trade_numba
f_estricta = njit(cache=False, fastmath=False)(f_core.py_func)   # misma fuente, sin fastmath

def hacer_llamador(f):
    @njit(cache=False, fastmath=False, boundscheck=False)
    def llamador(mfe, mae, prof, tg, tl, sp):
        out = np.empty(len(mfe), dtype=np.float32)
        for i in range(len(mfe)):
            out[i] = f(mfe[i], mae[i], prof[i], tg[i], tl[i], sp[i])
        return out
    return llamador

rng = np.random.default_rng(12345)
mfe = rng.gamma(2.0, 15.0, N); mae = -rng.gamma(2.0, 10.0, N)
prof = rng.normal(5.0, 25.0, N); tg = rng.integers(0, 400, N).astype(np.float64)
tl = rng.integers(0, 400, N).astype(np.float64); sp = rng.choice([0.6, 0.8, 1.0, 1.5, 2.0, 3.5], N)
# casos de borde: ceros, MAE nulo, tiempos nulos, spread mínimo
mfe[:5] = 0.0; mae[:5] = 0.0; prof[:5] = 0.0; tg[:5] = 0.0; tl[:5] = 0.0

A = hacer_llamador(f_core)(mfe, mae, prof, tg, tl, sp)
B = hacer_llamador(f_estricta)(mfe, mae, prof, tg, tl, sp)

fee = mfe / (mfe + np.abs(mae) + sp + 1e-9)
fet = tg / np.maximum(tg + tl, 1.0)
piso = np.maximum(np.abs(mae), sp)
ivr = (prof - mae) / (np.maximum(tl, 1.0) * piso + 1e-9)
C = (fee * fet * ((np.tanh(ivr) + 1.0) / 2.0)).astype(np.float32)

def informe(nombre, x, y):
    d = np.abs(x.astype(np.float64) - y.astype(np.float64))
    distintos = int((x != y).sum())
    ulp = np.abs(x.view(np.int32).astype(np.int64) - y.view(np.int32).astype(np.int64))
    print(f"{nombre}: distintos={distintos}/{len(x)} ({100*distintos/len(x):.4f}%) | max|Δ|={d.max():.3e} | "
          f"max ULP={int(ulp.max())} | ULP>=2: {int((ulp>=2).sum())}")
    return d.max()

print(f"numba/numpy: ver pip | N={N} | nan A={int(np.isnan(A).sum())} B={int(np.isnan(B).sum())} C={int(np.isnan(C).sum())}")
informe("A(core fastmath=True) vs B(estricta Numba)", A, B)
informe("A(core fastmath=True) vs C(numpy float64) ", A, C)
informe("B(estricta Numba)     vs C(numpy float64) ", B, C)
print(f"rango A: [{A.min():.6f}, {A.max():.6f}]")
