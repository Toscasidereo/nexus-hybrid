# ==============================================================================
# NEXUS LAB-V7 — KERNELS DE LA ESCALA DE v_req (Ridge de tamaño), COMPARTIDOS POR Fase_4_lab Y Fase_4_5_lab_A
# Carpeta: lab_v7/
# ==============================================================================
# BITÁCORA
#   V0.1 (2026-11-04) — Creación. Orden del CRO: "Alinea todas las fases de python, para que funcione el lab 7".
#     Mueve aquí, sin cambio de aritmética, los kernels que Fase_4_lab.py definía (lab_actividad_nb, _lab_esc_A_nb, _lab_esc_B_nb) y
#     agrega `lab_fase_nb` (sin(atan2(v, z)) con los mismos tipos float32 que el kernel de simulación) y `escala_desde_parametros`
#     (reconstruye la escala desde los parámetros exportados en el .txt). Fase 4 y Fase 4.5 usan el MISMO código: la escala que
#     simula Fase 4 es la que reproduce Fase 4.5 y la que calcula el EA gemelo (orden de operaciones idéntico).
#   Autónomo: numpy + numba. No importa Fase_*.py.
# ==============================================================================
import math
import numpy as np
from numba import njit

ACT_VENTANA = 60


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def lab_actividad_nb(opens, pm, ventana):
    """act[i] = suma ascendente (j = i-ventana+1 .. i) de d[j]; d[j] = |open[j]-open[j-1]|*pm; d[0] = 0. NaN si i < ventana-1.
    Mismo orden de operaciones que el EA gemelo (LabActividad)."""
    n = len(opens); d = np.empty(n); d[0] = 0.0
    for j in range(1, n):
        d[j] = abs(opens[j] - opens[j - 1]) * pm
    act = np.full(n, np.nan)
    for i in range(ventana - 1, n):
        t = 0.0
        for j in range(i - ventana + 1, i + 1):
            t += d[j]
        act[i] = t
    return act


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def lab_fase_nb(v, z):
    """sin(atan2(v, z)) elemento a elemento, con la MISMA tipificación que el kernel de simulación (entradas float32)."""
    n = len(v); out = np.empty(n)
    for i in range(n):
        out[i] = math.sin(math.atan2(v[i], z[i]))
    return out


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def _lab_esc_B_nb(act, act_med, a_is_med, emin, emax):
    n = len(act); out = np.empty(n)
    for r in range(n):
        a = act[r] / act_med
        if a != a:
            a = a_is_med
        e = a / a_is_med
        if e < emin: e = emin
        if e > emax: e = emax
        out[r] = e
    return out


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def _lab_esc_A_nb(X10, act, act_med, a_is_med, coef, inter, mu, sd, med_pred, emin, emax):
    n = len(act); out = np.empty(n)
    for r in range(n):
        a = act[r] / act_med
        if a != a:
            a = a_is_med
        t = 0.0
        for k in range(11):
            xk = X10[r, k] if k < 10 else a
            t += coef[k] * ((xk - mu[k]) / sd[k])
        e = (t + inter) / med_pred
        if e < emin: e = emin
        if e > emax: e = emax
        out[r] = e
    return out


def x10_desde_arreglos(zbi, viv, via, zbo, vov, voa, zm1, zm2):
    """Matriz (n, 10) float64 con los 10 features de Ridge 1 en el orden del EA (X_ML[0..9]). Entradas float32."""
    return np.column_stack([zbi, viv, via, lab_fase_nb(viv, zbi), zbo, vov, voa, lab_fase_nb(vov, zbo), zm1, zm2]).astype(np.float64)


def escala_desde_parametros(par, X10, act):
    """Escala por vela desde los parámetros exportados (dict: modo 'A'/'B', act_med, a_is_med, esc_min, esc_max y, en A, coef,
    intercept, mu, sd, med_pred). X10 solo se usa en modo A."""
    act = np.ascontiguousarray(act, dtype=np.float64)
    if par['modo'] == 'B':
        return _lab_esc_B_nb(act, par['act_med'], par['a_is_med'], par['esc_min'], par['esc_max'])
    return _lab_esc_A_nb(np.ascontiguousarray(X10, dtype=np.float64), act, par['act_med'], par['a_is_med'],
                         np.asarray(par['coef'], dtype=np.float64), par['intercept'], np.asarray(par['mu'], dtype=np.float64),
                         np.asarray(par['sd'], dtype=np.float64), par['med_pred'], par['esc_min'], par['esc_max'])
