# ==============================================================================
# NEXUS LAB-V7 — MÉTRICAS: Score_v7 Y T_v2 (ADITIVAS; NO REEMPLAZAN Score_final NI T(t))
# Carpeta: lab_v7/
# ==============================================================================
# BITÁCORA
#   V0.1 (2026-11-01) — Creación. Orden del CRO (2026-11-01): "generá un nuevo laboratorio paralelo en una rama nueva".
#     Implementa el formulario algebraico de claude/metricas_score_v7_propuesta.md, sección 6 (6.1 a 6.8), sin cambios
#     de fórmula. Módulo autónomo: no importa ni modifica nexus_formulas_core.py ni las Fases (laboratorio intocable).
#     Entrada: arrays OHLC de la ventana evaluada y la tabla de trades del motor (dirección, vela de entrada, vela de
#     salida, neto en pips con spread incluido). Salida: componentes C1-C4, Score_v7 y T_v2 por señal.
#     Observaciones registradas al implementar (ver README.md):
#     - H-V7-06: la media geométrica de T_v2 NO impide que un factor en 0 anule T_v2 (FET_v2 = 0 -> T_v2 = 0).
#       Se implementa tal como está especificado; no se cambia la fórmula sin orden del CRO.
#     - "Velas no fantasma" (sección 6.8): este módulo no recibe la máscara de velas fantasma; usa todas las velas.
# ==============================================================================
import math
import numpy as np
from numba import njit
from scipy.stats import norm, skew, kurtosis

GAMMA_E = 0.5772156649015329
GAP_FUSION = 2          # velas máximas entre salida y reapertura para fundir trades en una señal   [DEFAULT / CRO-OVERRIDE]
N_MIN = 100             # señales mínimas                                                          [DEFAULT / CRO-OVERRIDE]
BLOQUES = 4
R_NULO = 20
PESOS = (0.50, 0.20, 0.15, 0.15)                                                                  # [DEFAULT / CRO-OVERRIDE]


# ------------------------------------------------------------------ 6.1 señal
def fusionar(d, e, s, pi, gap=GAP_FUSION):
    """Trades consecutivos con la misma dirección y e[k+1] - s[k] <= gap forman una señal."""
    d, e, s, pi = (np.asarray(x) for x in (d, e, s, pi))
    n = len(d)
    if n == 0:
        z = np.zeros(0)
        return {'d': z.astype(np.int64), 'E': z.astype(np.int64), 'S': z.astype(np.int64), 'v': z.astype(np.int64),
                'pi': z, 'm': z.astype(np.int64)}
    gid = np.zeros(n, np.int64)
    for k in range(1, n):
        gid[k] = gid[k - 1] + (0 if (d[k] == d[k - 1] and e[k] - s[k - 1] <= gap) else 1)
    N = gid[-1] + 1
    E = np.zeros(N, np.int64); S = np.zeros(N, np.int64); D = np.zeros(N, np.int64)
    m = np.zeros(N, np.int64); P = np.zeros(N)
    for k in range(n):
        j = gid[k]
        if m[j] == 0:
            E[j] = e[k]; D[j] = d[k]
        S[j] = s[k]; m[j] += 1; P[j] += pi[k]
    return {'d': D, 'E': E, 'S': S, 'v': S - E, 'pi': P, 'm': m}


@njit(cache=False)
def camino(E, S, d, O, H, L, pm):
    """MFE (>= 0) y MAE (<= 0) en pips por señal, velas u = E .. S-1, referencia O[E]."""
    N = len(E); mfe = np.zeros(N); mae = np.zeros(N)
    for j in range(N):
        o = O[E[j]]
        for u in range(E[j], S[j]):
            if d[j] > 0:
                a = (H[u] - o) * pm; b = (L[u] - o) * pm
            else:
                a = (o - L[u]) * pm; b = (o - H[u]) * pm
            if a > mfe[j]: mfe[j] = a
            if b < mae[j]: mae[j] = b
    return mfe, mae


@njit(cache=False)
def fet_v2(E, S, d, O, pm, c):
    """Fracción de velas u = E+1 .. S-1 con ganancia neta de spread; 0.5 si v <= 2."""
    N = len(E); out = np.empty(N)
    for j in range(N):
        v = S[j] - E[j]
        if v <= 2:
            out[j] = 0.5; continue
        g = 0.0; cnt = 0.0
        for u in range(E[j] + 1, S[j]):
            if d[j] * (O[u] - O[E[j]]) * pm - c > 0.0:
                g += 1.0
            cnt += 1.0
        out[j] = g / cnt
    return out


def escala_h(C, pm, paso=60):
    """h = mediana |C[u] - C[u-paso]| en pips (movimiento típico de una hora con velas M1)."""
    C = np.asarray(C, float)
    if len(C) <= paso:
        raise ValueError('serie más corta que la ventana de h')
    return float(np.median(np.abs(C[paso:] - C[:-paso])) * pm)


# ------------------------------------------------------------------ 6.2 alfa
def alfa(sen, O, pm, opcion='A'):
    if opcion == 'A':
        mu = (O[-1] - O[0]) * pm / (len(O) - 1)
        return sen['pi'] - sen['d'] * mu * sen['v']
    return sen['pi'].copy()          # opción B: la simetría la aporta quien junta largos y cortos


# ------------------------------------------------------------------ 6.3 C1
def sr0(sigma_sr, nt):
    """Máximo esperado del Sharpe bajo azar entre nt juegos (Bailey y López de Prado, 2014). nt <= 1 -> 0."""
    if nt <= 1 or sigma_sr <= 0:
        return 0.0
    return float(sigma_sr * ((1 - GAMMA_E) * norm.ppf(1 - 1.0 / nt) + GAMMA_E * norm.ppf(1 - 1.0 / (nt * math.e))))


def dsr(a, sr_umbral=0.0):
    a = np.asarray(a, float); N = len(a)
    if N < 3 or a.std(ddof=1) == 0:
        return 0.0
    sr = a.mean() / a.std(ddof=1)
    g3 = float(skew(a)); g4 = float(kurtosis(a, fisher=False))
    den = 1.0 - g3 * sr + (g4 - 1.0) / 4.0 * sr ** 2
    if den <= 0:
        return 0.0
    return float(norm.cdf((sr - sr_umbral) * math.sqrt(N - 1) / math.sqrt(den)))


# ------------------------------------------------------------------ 6.4 C2
def c2_estabilidad(a, E, n_velas, B=BLOQUES):
    a = np.asarray(a, float); blk = np.minimum((np.asarray(E) * B) // n_velas, B - 1)
    pos, ts = [], []
    for b in range(B):
        x = a[blk == b]
        if len(x) < 5:
            return 0.0
        sd = x.std(ddof=1)
        pos.append(1.0 if x.mean() > 0 else 0.0)
        ts.append(x.mean() * math.sqrt(len(x)) / sd if sd > 0 else 0.0)
    return float(0.5 * np.mean(pos) + 0.5 * norm.cdf(min(ts)))


# ------------------------------------------------------------------ 6.5 C3
def _kappa(beta, mfe):
    return np.where(mfe > 0, np.clip(beta / np.where(mfe > 0, mfe, 1.0), -1.0, 1.0), -1.0)


# ------------------------------------------------------------------ 6.6 C4
def c4_cola(a, mae, h):
    a = np.asarray(a, float); k = max(int(math.ceil(0.05 * len(a))), 1)
    cvar = max(-float(np.sort(a)[:k].mean()), 0.0)
    mae90 = float(np.quantile(np.abs(mae), 0.90))
    return float(0.5 / (1 + cvar / h) + 0.5 / (1 + mae90 / h)), cvar, mae90


# ------------------------------------------------------------------ 6.7 Score_v7
def score_v7(d, e, s, pi, O, H, L, C, pm, c, nt=1, sigma_sr=0.0, opcion='A', bars_dia=1440, rng=None, R=R_NULO,
             pesos=PESOS, n_min=N_MIN):
    """Devuelve dict con N, C1..C4, Score_v7 y el DSR sin neutralizar (informativo, 'c1_crudo')."""
    rng = rng or np.random.default_rng(0)
    O, H, L, C = (np.ascontiguousarray(x, dtype=np.float64) for x in (O, H, L, C))
    sen = fusionar(d, e, s, pi)
    N = len(sen['E'])
    if N < 3:
        return {'N': N, 'score_v7': 0.0}
    a = alfa(sen, O, pm, opcion)
    mfe, mae = camino(sen['E'], sen['S'], sen['d'], O, H, L, pm)
    h = escala_h(C, pm)
    u0 = sr0(sigma_sr, nt)
    c1 = dsr(a, u0)
    c2 = c2_estabilidad(a, sen['E'], len(O))
    beta = sen['pi'] + sen['m'] * c                                  # bruto: neto + spreads pagados
    kap = _kappa(beta, mfe)
    nul = []
    for _ in range(R):
        lo = (sen['E'] // bars_dia) * bars_dia
        hi = np.minimum(lo + bars_dia, len(O) - 1 - sen['v'])
        ok = hi > lo
        E2 = np.where(ok, lo + (rng.random(N) * np.where(ok, hi - lo, 1)).astype(np.int64), sen['E'])
        S2 = E2 + sen['v']
        beta2 = sen['d'] * (O[S2] - O[E2]) * pm
        mfe2, _m = camino(E2.astype(np.int64), S2.astype(np.int64), sen['d'], O, H, L, pm)
        nul.append(np.median(_kappa(beta2, mfe2)))
    c3 = float(np.clip(0.5 + (np.median(kap) - np.median(nul)), 0.0, 1.0))
    c4, cvar, mae90 = c4_cola(a, mae, h)
    ok_gate = (N >= n_min) and (a.mean() > 0)
    sc = 100.0 * (pesos[0] * c1 + pesos[1] * c2 + pesos[2] * c3 + pesos[3] * c4) if ok_gate else 0.0
    return {'N': N, 'alfa_medio': float(a.mean()), 'C1': c1, 'C2': c2, 'C3': c3, 'C4': c4, 'cvar5': cvar, 'mae90': mae90,
            'h': h, 'SR0': u0, 'c1_crudo': dsr(sen['pi'], u0), 'compuerta': bool(ok_gate), 'score_v7': float(sc)}


# ------------------------------------------------------------------ 6.8 T_v2
def t_v2(d, e, s, pi, O, H, L, C, pm, c):
    """T_v2 por señal = (EFR · FET_v2 · D_h)^(1/3). Devuelve dict de arrays."""
    O, H, L, C = (np.ascontiguousarray(x, dtype=np.float64) for x in (O, H, L, C))
    sen = fusionar(d, e, s, pi)
    mfe, mae = camino(sen['E'], sen['S'], sen['d'], O, H, L, pm)
    cj = sen['m'] * c
    efr = np.clip((1.0 + sen['pi'] / (mfe + np.abs(mae) + cj + 1e-12)) / 2.0, 0.0, 1.0)
    fet = fet_v2(sen['E'], sen['S'], sen['d'], O, pm, c)
    dh = 1.0 / (1.0 + np.abs(mae) / escala_h(C, pm))
    return {'T_v2': (efr * fet * dh) ** (1.0 / 3.0), 'EFR': efr, 'FET_v2': fet, 'D_h': dh, 'senal': sen}
