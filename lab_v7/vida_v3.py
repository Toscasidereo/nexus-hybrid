# ==============================================================================
# NEXUS LAB-V7 — VIDA v3: descriptores de la vida del trade y compuesto aprendible
# Carpeta: lab_v7/   |   Especificación: lab_v7/ESPECIFICACION_VIDA_V3.md (fijada antes de implementar)
# ==============================================================================
# BITÁCORA
#   V0.1 (2026-11-06) — Creación. Orden del CRO: aprobó el diseño de cinco descriptores (captura, hundimiento, tiempo a favor,
#     recuperación, ritmo) y su compuesto, y pidió implementarlo. Trabaja sobre las fotos de la trayectoria de Fase 4
#     (extractor_trayectoria_*_v2): por foto, velas abiertas, profit_apertura, MFE/MAE corrientes y trade_id.
#     Solo usa datos del trade hasta la foto (causal). Constantes de normalización (med, escala) solo del IS.
#     Aditivo: no se importa desde main; Fase_4_lab.py lo usa con NEXUS_LAB_CIERRE=V3.
#   V0.2 (2026-11-07, rama lab-v8) — Extensión. Orden del CRO ("extender v3 ... luz verde"). Agrega: (a) funciones njit compartidas por Python, núcleos de
#     simulación y EA (v3_raw_nb, v3_comp_nb, v3_vivo_nb); (b) vector de constantes v3p (18 valores: h, rit_vmin, rec_na, med[5], escala[5], pesos[5]);
#     (c) v3p_poblacion: constantes desde las operaciones del extractor de entrada (población IS sin compuerta ML); (d) vida_v31 (VER 3.0 | 3.1).
#     VER 3.0 = fórmulas de lab-v7 (rit_vmin = 1, REC no aplicable = 0.5). VER 3.1 = parches H-V3-02 (RIT con duración mínima = mediana de duración IS)
#     y H-V3-03 (REC no aplicable = 1.0). vida_v3 (V0.1) se conserva sin cambios.
# ==============================================================================
import math
import numpy as np
from numba import njit

DESCRIPTORES = ('EFR', 'D_h', 'FET_v3', 'REC', 'RIT')
PESOS_V3 = np.full(5, 0.2)          # [DEFAULT / CRO-OVERRIDE] pesos iguales de partida
PASO_H = 60.0                       # velas M1 por hora (h/60 = movimiento típico por vela)


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def _vivos_nb(prof, mfe, mae, tid, vela, c, h):
    """Descriptores brutos vivos por foto. Devuelve (raw[n,5], aplica_rec[n]). Las fotos de un trade son contiguas y ascendentes en vela."""
    n = len(prof)
    raw = np.zeros((n, 5)); apl = np.zeros(n, dtype=np.bool_)
    cur = -2147483647; cg = 0.0; cn = 0.0; minp = 1e30; vmin = 0.0
    hv = h / 60.0
    for k in range(n):
        if tid[k] != cur:
            cur = tid[k]; cg = 0.0; cn = 0.0; minp = 1e30; vmin = 0.0
        v = float(vela[k]); p = float(prof[k])
        if v >= 2.0:
            cn += 1.0
            if p > 0.0:
                cg += 1.0
        fet = 0.5 if v <= 2.0 else cg / cn
        if p < minp:
            minp = p; vmin = v
        efr = (1.0 + p / (float(mfe[k]) + abs(float(mae[k])) + c + 1e-12)) / 2.0
        if efr < 0.0: efr = 0.0
        if efr > 1.0: efr = 1.0
        dh = 1.0 / (1.0 + abs(float(mae[k])) / h)
        raw[k, 0] = efr; raw[k, 1] = dh; raw[k, 2] = fet
        if -minp > c:
            apl[k] = True
            den = max(v - vmin, 1.0) * hv + 1e-12
            raw[k, 3] = (p - minp) / den
        raw[k, 4] = p / (v * hv + 1e-12)
    return raw, apl


def _ultimas_fotos(tid):
    """Índice de la última foto de cada trade y vector inverso (foto -> posición del trade)."""
    tu, rev = np.unique(tid[::-1], return_index=True)
    ult = len(tid) - 1 - rev
    inv = np.searchsorted(tu, tid)
    return ult, inv


def estadisticas_is(raw_term, apl_term):
    """med y escala por descriptor, con un valor terminal por trade del IS (REC solo donde aplica)."""
    med = np.zeros(5); esc = np.ones(5)
    for j in range(5):
        x = raw_term[apl_term, j] if j == 3 else raw_term[:, j]
        if len(x) < 3:
            continue
        med[j] = np.median(x)
        mad = float(np.median(np.abs(x - med[j])))
        if mad > 1e-6: esc[j] = mad
        else:
            sd = float(np.std(x))
            esc[j] = sd if sd > 1e-6 else 1.0
    return {'med': med, 'escala': esc}


def normalizar(raw, apl, stats):
    S = (np.tanh((raw - stats['med']) / stats['escala']) + 1.0) / 2.0
    S[~apl, 3] = 0.5                 # recuperación no aplicable: neutro
    return S


def vida_v3(prof, mfe, mae, tid, vela, c, h, stats=None, pesos=None):
    """Vida v3 por foto (viva) y terminal por trade. `stats` = constantes del IS; si es None se calculan con estas mismas fotos
    (usar solo sobre IS). Devuelve dict con S (n,5), V3 (n), V3_term (n, float32), S_term (n,5), raw, apl, stats."""
    pesos = PESOS_V3 if pesos is None else np.asarray(pesos, dtype=np.float64)
    prof = np.ascontiguousarray(prof, dtype=np.float64); mfe = np.ascontiguousarray(mfe, dtype=np.float64)
    mae = np.ascontiguousarray(mae, dtype=np.float64); tid = np.ascontiguousarray(tid, dtype=np.int64)
    vela = np.ascontiguousarray(vela, dtype=np.int64)
    if len(tid) == 0:
        z = np.zeros((0, 5))
        return {'S': z, 'V3': np.zeros(0), 'V3_term': np.zeros(0, dtype=np.float32), 'S_term': z, 'raw': z, 'apl': np.zeros(0, bool),
                'stats': stats or {'med': np.zeros(5), 'escala': np.ones(5)}}
    raw, apl = _vivos_nb(prof, mfe, mae, tid, vela, float(c), float(h))
    ult, inv = _ultimas_fotos(tid)
    if stats is None:
        stats = estadisticas_is(raw[ult], apl[ult])
    S = normalizar(raw, apl, stats)
    V = S @ pesos
    return {'S': S, 'V3': V, 'V3_term': V[ult][inv].astype(np.float32), 'S_term': S[ult][inv], 'raw': raw, 'apl': apl, 'stats': stats}


def r2_agrupado(X, Y, grupos, k=5, lam=1.0):
    """R² fuera de pliegue (GroupKFold por trade: pliegue = grupo % k) de un Ridge cerrado (X estandarizada con el train). Y puede ser (n,) o (n,m)."""
    X = np.asarray(X, dtype=np.float64); Y = np.asarray(Y, dtype=np.float64)
    vector = (Y.ndim == 1)
    if vector: Y = Y[:, None]
    g = np.asarray(grupos, dtype=np.int64) % k
    oof = np.full(Y.shape, np.nan)
    for f in range(k):
        te = g == f; tr = ~te
        if te.sum() == 0 or tr.sum() < X.shape[1] + 2:
            continue
        mu = X[tr].mean(axis=0); sd = X[tr].std(axis=0); sd[sd < 1e-12] = 1.0
        A = (X[tr] - mu) / sd; ym = Y[tr].mean(axis=0)
        W = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ (Y[tr] - ym))
        oof[te] = ((X[te] - mu) / sd) @ W + ym
    ok = ~np.isnan(oof[:, 0])
    if ok.sum() < 3:
        r = np.full(Y.shape[1], np.nan)
    else:
        sse = ((Y[ok] - oof[ok]) ** 2).sum(axis=0); sst = ((Y[ok] - Y[ok].mean(axis=0)) ** 2).sum(axis=0)
        r = np.where(sst > 1e-12, 1.0 - sse / np.where(sst > 1e-12, sst, 1.0), np.nan)
    return float(r[0]) if vector else r


# ------------------------------------------------------------------ V0.2: núcleo compartido (Python / simuladores / EA)
N_V3P = 18          # [0]=h  [1]=rit_vmin  [2]=rec_na  [3:8]=med  [8:13]=escala  [13:18]=pesos
VERSIONES = ('3.0', '3.1')


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def v3_raw_nb(p, mfe, mae, v, cg, cn, minp, vfondo, c, h, rit_vmin):
    """Descriptores brutos en una foto. p=profit neto de spread, mfe/mae=corrientes con cierre, v=velas abiertas (float), cg/cn=fotos con p>0 / fotos desde la vela 2,
    minp/vfondo=mínimo corriente de p y su vela. Devuelve (efr, dh, fet, rec, aplica_rec, rit)."""
    hv = h / 60.0
    fet = 0.5 if v <= 2.0 else cg / cn
    efr = (1.0 + p / (mfe + abs(mae) + c + 1e-12)) / 2.0
    if efr < 0.0: efr = 0.0
    if efr > 1.0: efr = 1.0
    dh = 1.0 / (1.0 + abs(mae) / h)
    apl = (-minp) > c
    rec = 0.0
    if apl:
        rec = (p - minp) / (max(v - vfondo, 1.0) * hv + 1e-12)
    rit = p / (max(v, rit_vmin) * hv + 1e-12)
    return efr, dh, fet, rec, apl, rit


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def v3_comp_nb(efr, dh, fet, rec, apl, rit, v3p):
    """Compuesto V3 (suma secuencial fija: ((((w0*s0 + w1*s1) + w2*s2) + w3*s3) + w4*s4))."""
    s0 = (math.tanh((efr - v3p[3]) / v3p[8]) + 1.0) / 2.0
    s1 = (math.tanh((dh - v3p[4]) / v3p[9]) + 1.0) / 2.0
    s2 = (math.tanh((fet - v3p[5]) / v3p[10]) + 1.0) / 2.0
    s3 = v3p[2]
    if apl:
        s3 = (math.tanh((rec - v3p[6]) / v3p[11]) + 1.0) / 2.0
    s4 = (math.tanh((rit - v3p[7]) / v3p[12]) + 1.0) / 2.0
    return (((v3p[13] * s0 + v3p[14] * s1) + v3p[15] * s2) + v3p[16] * s3) + v3p[17] * s4


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def v3_vivo_nb(p, mfe, mae, v, cg, cn, minp, vfondo, c, v3p):
    r = v3_raw_nb(p, mfe, mae, v, cg, cn, minp, vfondo, c, v3p[0], v3p[1])
    return v3_comp_nb(r[0], r[1], r[2], r[3], r[4], r[5], v3p)


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def _serie_raw_nb(prof, mfe, mae, tid, vela, c, h, rit_vmin):
    """Descriptores brutos por foto con el mismo estado que los núcleos (fotos de un trade contiguas y ascendentes)."""
    n = len(prof)
    raw = np.zeros((n, 5)); apl = np.zeros(n, dtype=np.bool_)
    cur = -2147483647; cg = 0.0; cn = 0.0; minp = 1e30; vf = 0.0
    for k in range(n):
        if tid[k] != cur:
            cur = tid[k]; cg = 0.0; cn = 0.0; minp = 1e30; vf = 0.0
        v = float(vela[k]); p = float(prof[k])
        if v >= 2.0:
            cn += 1.0
            if p > 0.0: cg += 1.0
        if p < minp:
            minp = p; vf = v
        r = v3_raw_nb(p, float(mfe[k]), float(mae[k]), v, cg, cn, minp, vf, c, h, rit_vmin)
        raw[k, 0] = r[0]; raw[k, 1] = r[1]; raw[k, 2] = r[2]; raw[k, 3] = r[3]; raw[k, 4] = r[5]; apl[k] = r[4]
    return raw, apl


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def _serie_comp_nb(raw, apl, v3p):
    n = raw.shape[0]; V = np.zeros(n); S = np.zeros((n, 5))
    for k in range(n):
        V[k] = v3_comp_nb(raw[k, 0], raw[k, 1], raw[k, 2], raw[k, 3], apl[k], raw[k, 4], v3p)
    return V


def v3p_armar(h, ver, stats, rit_vmin):
    """Vector de constantes v3p a partir de las estadísticas IS (med, escala), la versión y rit_vmin."""
    if ver not in VERSIONES: raise ValueError(f"versión de Vida inválida: {ver}")
    v = np.zeros(N_V3P)
    v[0] = float(h); v[1] = float(rit_vmin); v[2] = 0.5 if ver == '3.0' else 1.0
    v[3:8] = stats['med']; v[8:13] = stats['escala']; v[13:18] = PESOS_V3
    return v


def v3p_poblacion(p, mfe, mae, vel, fet, pfondo, vfondo, c, h, ver):
    """Constantes v3p desde las operaciones del extractor de entrada (un registro terminal por operación: profit, MFE y MAE con cierre,
    velas, FET_v3 y mínimo corriente con su vela, tomados por el núcleo). rit_vmin = 1 (3.0) o mediana de duración IS (3.1)."""
    p = np.asarray(p, dtype=np.float64); n = len(p)
    rit_vmin = 1.0 if ver == '3.0' else max(1.0, float(np.median(vel))) if n else 1.0
    raw = np.zeros((n, 5)); apl = np.zeros(n, dtype=bool)
    for k in range(n):
        r = v3_raw_nb(float(p[k]), float(mfe[k]), float(mae[k]), float(vel[k]), 0.0, 1.0, float(pfondo[k]), float(vfondo[k]), float(c), float(h), rit_vmin)
        raw[k, 0] = r[0]; raw[k, 1] = r[1]; raw[k, 2] = float(fet[k]); raw[k, 3] = r[3]; raw[k, 4] = r[5]; apl[k] = r[4]
    return v3p_armar(h, ver, estadisticas_is(raw, apl), rit_vmin), raw, apl


def v3_terminal_poblacion(raw, apl, v3p):
    """V3 terminal por operación de la población (objetivo de la Cabeza B)."""
    return _serie_comp_nb(np.ascontiguousarray(raw), np.ascontiguousarray(apl), v3p)


def vida_v31(prof, mfe, mae, tid, vela, c, h, ver='3.1', v3p=None):
    """Vida v3 por foto y terminal por trade con la versión `ver`. Con v3p=None las constantes salen de los terminales de estas mismas fotos (solo IS).
    Devuelve dict: V3 (vivo, n), V3_term (float32), S_term=None, raw, apl, v3p."""
    prof = np.ascontiguousarray(prof, dtype=np.float64); mfe = np.ascontiguousarray(mfe, dtype=np.float64)
    mae = np.ascontiguousarray(mae, dtype=np.float64); tid = np.ascontiguousarray(tid, dtype=np.int64); vela = np.ascontiguousarray(vela, dtype=np.int64)
    if len(tid) == 0:
        z = np.zeros((0, 5)); return {'V3': np.zeros(0), 'V3_term': np.zeros(0, dtype=np.float32), 'raw': z, 'apl': np.zeros(0, bool), 'v3p': v3p}
    ult, inv = _ultimas_fotos(tid)
    if v3p is None:
        rit_vmin = 1.0 if ver == '3.0' else max(1.0, float(np.median(vela[ult])))
        raw, apl = _serie_raw_nb(prof, mfe, mae, tid, vela, float(c), float(h), rit_vmin)
        v3p = v3p_armar(h, ver, estadisticas_is(raw[ult], apl[ult]), rit_vmin)
    else:
        raw, apl = _serie_raw_nb(prof, mfe, mae, tid, vela, float(c), float(h), float(v3p[1]))
    v3p = np.ascontiguousarray(v3p, dtype=np.float64)
    V = _serie_comp_nb(raw, apl, v3p)
    S = (np.tanh((raw - v3p[3:8]) / v3p[8:13]) + 1.0) / 2.0          # descriptores normalizados (diagnóstico R2V/correlación; no entra en la paridad)
    S[~apl, 3] = v3p[2]
    return {'V3': V, 'V3_term': V[ult][inv].astype(np.float32), 'S': S, 'S_term': S[ult][inv], 'raw': raw, 'apl': apl, 'v3p': v3p}
