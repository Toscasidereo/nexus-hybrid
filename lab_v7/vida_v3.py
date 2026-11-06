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
# ==============================================================================
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
