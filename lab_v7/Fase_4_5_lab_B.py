# ==============================================================================
# 🧠 NEXUS FASE 4.5B V12.0 — ETAPA B: COMPOSICIÓN DE ESTADÍSTICAS Y CURVAS OOS
# ⚡ ANÁLISIS DE ESTRÉS CONCURRENTE + DRAWDOWN FLOTANTE + DECAIMIENTO TEMPORAL
# 🎯 INTEGRACIÓN TOTAL TABLERO ÚNICO + SOPORTE MULTI-ESCALÓN E0..E3 (V12.0)
# ==============================================================================
# 📋 BITÁCORA LAB-V7 V0.1 (2026-11-04) — COPIA DE LABORATORIO de Fase_4_5_V_12_0_B.py (rama lab-v7; `main` intacto):
#    Solo cambia la carpeta de entrada: usa el mismo sufijo `_LAB_...` que Fase_4_5_lab_A.py (variables NEXUS_LAB_*). Apagadas = main.
# ==============================================================================
# 📋 BITÁCORA V12.0 (promoción mayor — paridad con Etapa A V12.0 y SSoT V3.3):
#    - [H-45B-01 CERRADO] Sincronización dinámica de directorio de entrada/salida
#      con el escalón activo: `DIR_SALIDA = f"F45_V12_{ESCALON}"`.
#    - [H-45B-02 CERRADO] Corregido el eje X de la curva E2 (supervivencia): ahora calcula
#      la edad real de la vela viva (`Idx - Idx_In + 1`), mostrando con precisión que en
#      los escalones con inmunidad (E1..E3) las inferencias de T_pred inician en la vela 3.
#    - [TRAZABILIDAD ESCALÓN] `portafolios_por_rank.csv` incorpora la columna `Escalon`.
#    - [REGLA 7] Preservación íntegra del historial forense de cabecera.
# ==============================================================================
# 📋 BITÁCORA rev.c (TABLERO — ver parche_fase45_tablero.py y Fase_4_5b_V11_0.tablero.diff):
#    - Lee geometria.ciega de meta.json: sin reserva imprime un aviso y estampa en rojo "VENTANA NO CIEGA" en TODAS las imágenes;
#      portafolios_por_rank.csv lleva la columna Ventana_Ciega.
#    - Corregido el eje X de la curva E2 (T_pred se evalúa desde la 1ª vela en el contrato E0; estaba corrido 2 velas con rótulo erróneo).
# ==============================================================================
# 📋 BITÁCORA V11.0:
#    - Lee SOLO lo que dejó la Etapa A (F45_V11/): motores, trades, velas, tiempo, meta. No re-simula.
#    - Todas las métricas del juez (score, Sortino-NEXUS, PF, WR, MaxDD, RF, T) vienen de nexus_formulas_core (Axioma 3).
#    - Niveles: MOTOR (tabla) -> SÍMBOLO (ficha) -> PORTAFOLIO por Rank (la cuenta). Un portafolio rechazado por el juez
#      se informa como RECHAZADO con la condición que falló (no como ceros).
#    - Exposición = nº de posiciones abiertas DURANTE el minuto (toda vela con posición cuenta, incluida la de cierre).
#    - Drawdown flotante por minuto con CONCURRENCIA: equity cerrada + suma de flotantes de las posiciones abiertas
#      (flotante marcado a la apertura de la vela siguiente, igual que la decisión del simulador). No incluye excursión intravela.
#    - Decaimiento: pendiente de la mediana de T por BLOQUES NO SOLAPADOS (las rodantes solapadas están autocorrelacionadas
#      y subestimarían el error). 'DECAY' solo si el IC95 completo es negativo.
#    - Rodantes indexadas por trade, ventana min(n//3+1, 50). Curvas A1-F1 del catálogo (E1/E2 requieren la Etapa A).
#    ⚠️ Premisa abierta (CRO): suma de pips de pares distintos con lote fijo. D1/D2 muestran cuánto pesa cada par.
# ==============================================================================

import os
import json
import glob
import math
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from nexus_formulas_core import eval_robustez_numba_v6, FORMULAS_CORE_VERSION

warnings.simplefilter('ignore')

FASE45B_VERSION = "V12.0"
ESCALON = 'E3'                             # Debe coincidir con la Etapa A ejecutada
# [LAB-V7] mismo tag que Fase_4_lab.py (variables NEXUS_LAB_*; apagadas = idéntico a la Fase 4.5 de main)
LAB_TAMANO = os.environ.get('NEXUS_LAB_TAMANO', 'off')           # 'off' | 'A' | 'B'
LAB_CIERRE = os.environ.get('NEXUS_LAB_CIERRE', 'T_terminal')    # 'T_terminal' | 'dT_cont' | 'G_pips'
LAB_NULO = os.environ.get('NEXUS_LAB_NULO', '0') == '1'
LAB_METRICA = os.environ.get('NEXUS_LAB_METRICA', 'final')       # 'final' | 'v7' (solo cambia el tag: 4.5 no usa Score_v7)
assert LAB_METRICA in ('final', 'v7'), f"NEXUS_LAB_METRICA invalido: {LAB_METRICA}"
assert LAB_TAMANO in ('off', 'A', 'B'), f"NEXUS_LAB_TAMANO invalido: {LAB_TAMANO}"
assert LAB_CIERRE in ('T_terminal', 'dT_cont', 'G_pips'), f"NEXUS_LAB_CIERRE invalido: {LAB_CIERRE}"
assert not (LAB_NULO and LAB_TAMANO != 'off'), "Gemelo nulo con Ridge de tamaño no es exportable: la escala desplazada no sale en el .txt"
LAB_ACTIVO = (LAB_TAMANO != 'off') or (LAB_CIERRE != 'T_terminal') or LAB_NULO or (LAB_METRICA != 'final')
_SUF_LAB = (f"_LAB_{LAB_TAMANO}_{LAB_CIERRE}" + ("_MV7" if LAB_METRICA == "v7" else "") + ("_NULO" if LAB_NULO else "")) if LAB_ACTIVO else ""
DIR_SALIDA = f"F45_V12_{ESCALON}" + _SUF_LAB
DIR_GRAF = os.path.join(DIR_SALIDA, "graficos")

RANKS_COMPOSICION = tuple(range(1, 11))    # Estadísticas para los 10 ranks
RANKS_GRAFICOS = (1,)                      # Generación de gráficos (Rank 1 por defecto)
MIN_OPS_PORTAFOLIO = 100                   # Significancia institucional de cartera
VENTANA_ROLLING_MAX = 50
MIN_BLOQUES_DECAY = 6
CAUSAS = {1: 'TimeStop', 2: 'SmartTrailing', 3: 'Saturador', 4: 'Aborto K', 5: 'EOF'}
DPI = 110
_AVISO = ''
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}


# ==============================================================================
# 📥 CARGA
# ==============================================================================
def cargar():
    ruta_meta = os.path.join(DIR_SALIDA, "meta.json")
    if not os.path.exists(ruta_meta):
        raise RuntimeError(f"🛑 FATAL: {ruta_meta} no existe. Ejecutar primero la Etapa A (Fase_4_5_V_12_0.py con ESCALON={ESCALON}).")
    with open(ruta_meta, encoding='utf-8') as f:
        meta = json.load(f)
    tiempo = pd.read_parquet(os.path.join(DIR_SALIDA, "tiempo.parquet"))['Time'].to_numpy('datetime64[ns]')

    def leer(patron, parquet):
        rutas = sorted(glob.glob(os.path.join(DIR_SALIDA, patron)))
        if not rutas:
            raise RuntimeError(f"🛑 FATAL: no hay archivos '{patron}' en {DIR_SALIDA}.")
        return pd.concat([pd.read_parquet(r) if parquet else pd.read_csv(r, encoding='utf-8-sig') for r in rutas], ignore_index=True)

    return meta, tiempo, leer("motores_*.csv", False), leer("trades_*.parquet", True), leer("velas_*.parquet", True)


# ==============================================================================
# 📐 ESTADÍSTICAS Y UTILIDADES
# ==============================================================================
def _v32(df, col):
    return np.ascontiguousarray(df[col].to_numpy()).astype(np.float32)


def stats_core(tr, min_trades):
    n = len(tr)
    base = {
        'n': n, 'Score': 0.0, 'MedMFE': np.nan, 'MedMAE': np.nan, 'MedProfit': np.nan,
        'WR': np.nan, 'PF': np.nan, 'MaxDD': np.nan, 'RF': np.nan, 'Sortino': np.nan,
        'T_med': np.nan, 'Rechazado': True, 'Causa': 'sin_trades',
        'Pips_Netos': float(tr['Profit_Pips'].sum()) if n else 0.0
    }
    if n == 0:
        return base
    r = eval_robustez_numba_v6(_v32(tr, 'MFE_Pips'), _v32(tr, 'MAE_Pips'), _v32(tr, 'Profit_Pips'), _v32(tr, 'T_Score'), min_trades)
    base['T_med'] = float(np.median(tr['T_Score'].to_numpy()))
    base['MedProfit'] = float(np.median(tr['Profit_Pips'].to_numpy()))
    if r[0] > 0.0:
        base.update({
            'Score': float(r[0]), 'MedMFE': float(r[1]), 'MedMAE': float(r[2]), 'MedProfit': float(r[3]),
            'WR': float(r[6]), 'PF': float(r[7]), 'MaxDD': float(r[8]), 'RF': float(r[9]), 'Sortino': float(r[11]),
            'T_med': float(r[12]), 'Rechazado': False, 'Causa': ''
        })
        return base
    if n < min_trades:
        base['Causa'] = f"n={n} < min_trades={min_trades}"
    else:
        p = tr['Profit_Pips'].to_numpy(); gan = p[p > 0].sum(); per = np.abs(p[p <= 0]).sum()
        mfe = np.median(tr['MFE_Pips'].to_numpy())
        base['Causa'] = ("mediana_profit<=0.05" if np.median(p) <= 0.05 else
                         "ganancias<=perdidas (PF<=1)" if gan <= per else
                         "mediana_MFE<=0" if mfe <= 0.0 else "score_cero")
    return base


def ordenar(tr):
    return tr.sort_values(['Idx_Out', 'Idx_In', 'Simbolo', 'Dir'], kind='mergesort').reset_index(drop=True)


def unir_claves(df, claves):
    return df.merge(claves[['Simbolo', 'Dir', 'Rank']].drop_duplicates(), on=['Simbolo', 'Dir', 'Rank'], how='inner')


def curvas_minuto(tr, vl, N, a0):
    L = N - a0
    w = tr['Profit_Pips'].to_numpy(); ix = tr['Idx_Out'].to_numpy() - a0
    ok = (ix >= 0) & (ix < L)
    closed = np.bincount(ix[ok], weights=w[ok], minlength=L)[:L]
    eq_c = np.cumsum(closed)
    if len(vl):
        m = vl[vl['Cierra'] == 0]; iv = m['Idx'].to_numpy() + 1 - a0; okv = (iv >= 0) & (iv < L)
        flo = np.bincount(iv[okv], weights=m['Profit_Flot'].to_numpy()[okv], minlength=L)[:L]
        ie = vl['Idx'].to_numpy() - a0; oke = (ie >= 0) & (ie < L)
        expo = np.bincount(ie[oke], minlength=L)[:L]
    else:
        flo = np.zeros(L); expo = np.zeros(L)
    eq_f = eq_c + flo
    dd_c = np.maximum(np.maximum.accumulate(eq_c), 0.0) - eq_c
    dd_f = np.maximum(np.maximum.accumulate(eq_f), 0.0) - eq_f
    return {'eq_c': eq_c, 'eq_f': eq_f, 'dd_c': dd_c, 'dd_f': dd_f, 'expo': expo}


def pnl_diario(tr, tiempo):
    if len(tr) == 0: return pd.DataFrame()
    d = tr.assign(Dia=tiempo[tr['Idx_Out'].to_numpy()].astype('datetime64[D]'))
    return d.pivot_table(index='Dia', columns='Simbolo', values='Profit_Pips', aggfunc='sum', fill_value=0.0).sort_index()


def rodantes(tr):
    n = len(tr)
    if n < 6: return None
    w = min(n // 3 + 1, VENTANA_ROLLING_MAX)
    mfe, mae, prof, ts = _v32(tr, 'MFE_Pips'), _v32(tr, 'MAE_Pips'), _v32(tr, 'Profit_Pips'), _v32(tr, 'T_Score')
    out = {k: np.full(n, np.nan) for k in ('Sortino', 'PF', 'WR', 'MaxDD', 'Score')}
    for k in range(w - 1, n):
        s = slice(k - w + 1, k + 1)
        r = eval_robustez_numba_v6(np.ascontiguousarray(mfe[s]), np.ascontiguousarray(mae[s]), np.ascontiguousarray(prof[s]),
                                   np.ascontiguousarray(ts[s]), w)
        if r[0] > 0.0:
            out['Sortino'][k] = r[11]; out['PF'][k] = r[7]; out['WR'][k] = r[6]; out['MaxDD'][k] = r[8]; out['Score'][k] = r[0]
    out['T'] = pd.Series(ts.astype(np.float64)).rolling(w).median().to_numpy()
    out['w'] = w
    return out


def decaimiento(T, w):
    k = len(T) // w
    if k < MIN_BLOQUES_DECAY: return None
    med = np.array([np.median(T[i * w:(i + 1) * w]) for i in range(k)]); x = np.arange(k, dtype=np.float64)
    slope, inter = np.polyfit(x, med, 1)
    res = med - (slope * x + inter); df_ = k - 2
    se = math.sqrt(max((res ** 2).sum() / df_, 0.0) / ((x - x.mean()) ** 2).sum())
    t = T95.get(df_, 2.0); lo, hi = slope - t * se, slope + t * se
    f = 100.0 / w
    return {'pend_100_trades': slope * f, 'IC_lo': lo * f, 'IC_hi': hi * f, 'bloques': k,
            'estado': 'DECAY' if hi < 0 else ('MEJORA' if lo > 0 else 'SIN_EVIDENCIA')}


def concentracion(tr):
    g = tr.groupby('Simbolo')['Profit_Pips'].sum()
    pos = g.clip(lower=0.0); tot = pos.sum()
    return {'HHI': float(((pos / tot) ** 2).sum()) if tot > 0 else np.nan,
            'Top1_%': float(100.0 * pos.max() / tot) if tot > 0 else np.nan, 'Simbolos_con_trades': int(g.size)}


# ==============================================================================
# 🧩 COMPOSICIÓN POR RANK
# ==============================================================================
def componer_rank(r, mot, tr_all, vl_all, tiempo, geom, escalon_meta):
    ms = mot[(mot['Rank'] == r) & (mot['Estado'] == 'OK')]
    if ms.empty: return None
    N = geom['N']; a0 = geom['vent_pf'][0]
    tr_s = ordenar(unir_claves(tr_all[(tr_all['Rank'] == r) & (tr_all['Superv'] == 1)], ms))
    tr_b = ordenar(unir_claves(tr_all[(tr_all['Rank'] == r) & (tr_all['Superv'] == 0)], ms))
    vl = unir_claves(vl_all[vl_all['Rank'] == r], ms)
    if tr_s.empty: return None

    por_fold = {f: ms[ms['Fold'] == f] for f in sorted(ms['Fold'].unique())}
    st = {
        'Rank': r, 'Escalon': escalon_meta, 'Motores': len(ms), 'Simbolos': ms['Simbolo'].nunique(),
        'Ventana_Ciega': bool(geom.get('ciega', False))
    }
    for pref, tr in (('S', tr_s), ('B', tr_b)):
        s = stats_core(tr, MIN_OPS_PORTAFOLIO)
        st.update({f'{pref}_{k}': v for k, v in s.items()})
    for f, mf in por_fold.items():
        s = stats_core(unir_claves(tr_s, mf), MIN_OPS_PORTAFOLIO)
        st.update({f'S_Fold{f}_{k}': s[k] for k in ('n', 'Score', 'PF', 'T_med', 'Pips_Netos', 'Rechazado')})

    cur = curvas_minuto(tr_s, vl, N, a0)
    st['MaxDD_cerrado_minuto'] = float(cur['dd_c'].max()); st['MaxDD_flotante_minuto'] = float(cur['dd_f'].max())
    st['Exposicion_media'] = float(cur['expo'].mean()); st['Exposicion_max'] = int(cur['expo'].max())
    meses = max((tiempo[N - 1] - tiempo[a0]) / np.timedelta64(1, 'D') / 30.4375, 1e-9)
    st['Trades_por_mes'] = float(len(tr_s) / meses)
    st.update({f'Conc_{k}': v for k, v in concentracion(tr_s).items()})

    rod = rodantes(tr_s)
    dec = decaimiento(_v32(tr_s, 'T_Score').astype(np.float64), rod['w']) if rod else None
    st['Decay_estado'] = dec['estado'] if dec else 'INSUFICIENTE'
    st['Decay_pend_100_trades'] = dec['pend_100_trades'] if dec else np.nan
    st['Decay_IC_lo'] = dec['IC_lo'] if dec else np.nan; st['Decay_IC_hi'] = dec['IC_hi'] if dec else np.nan

    filas_sim = []
    for sim, g in tr_s.groupby('Simbolo'):
        s = stats_core(g, MIN_OPS_PORTAFOLIO)
        filas_sim.append({
            'Simbolo': sim, 'Rank': r, 'Escalon': escalon_meta, 'n': s['n'],
            'n_LONG': int((g['Dir'] == 'LONG').sum()), 'n_SHORT': int((g['Dir'] == 'SHORT').sum()),
            'Pips_Netos': s['Pips_Netos'], 'Score': s['Score'], 'PF': s['PF'], 'WR': s['WR'],
            'MaxDD': s['MaxDD'], 'T_med': s['T_med'], 'Rechazado': s['Rechazado'], 'Causa': s['Causa']
        })
    return {
        'rank': r, 'ms': ms, 'tr_s': tr_s, 'tr_b': tr_b, 'vl': vl, 'stats': st,
        'cur': cur, 'rod': rod, 'dec': dec, 'sim_tab': pd.DataFrame(filas_sim), 'por_fold': por_fold
    }


# ==============================================================================
# 🎨 CURVAS DE ESTRÉS DE PORTAFOLIO
# ==============================================================================
def _vacio(ax, txt="sin datos"):
    ax.text(0.5, 0.5, txt, ha='center', va='center', transform=ax.transAxes, color='gray')
    ax.set_xticks([]); ax.set_yticks([])


def _guardar(fig, nombre):
    os.makedirs(DIR_GRAF, exist_ok=True)
    if _AVISO:
        fig.text(0.5, 0.992, _AVISO, color='red', ha='center', va='top', fontsize=9, weight='bold')
        fig.tight_layout(rect=(0, 0, 1, 0.975))
    else:
        fig.tight_layout()
    fig.savefig(os.path.join(DIR_GRAF, nombre), dpi=DPI)
    plt.close(fig)


def _eq_cerrada(tr, N, a0):
    L = N - a0
    if len(tr) == 0: return np.zeros(L)
    ix = tr['Idx_Out'].to_numpy() - a0; ok = (ix >= 0) & (ix < L)
    return np.cumsum(np.bincount(ix[ok], weights=tr['Profit_Pips'].to_numpy()[ok], minlength=L)[:L])


def lamina_rendimiento(c, tiempo, geom):
    N = geom['N']; a0 = geom['vent_pf'][0]; ts = tiempo[a0:N]; r = c['rank']
    fig, ax = plt.subplots(2, 2, figsize=(15, 8)); a = ax.ravel()
    a[0].plot(ts, c['cur']['eq_c'], 'k', lw=1.4, label='Portafolio (cerrada)')
    for f, mf in c['por_fold'].items():
        a[0].plot(ts, _eq_cerrada(unir_claves(c['tr_s'], mf), N, a0), lw=0.9, label=f'solo motores Fold {f}')
    a[0].set_title(f'A1 Equity acumulada (pips) — Rank {r} [{c["stats"]["Escalon"]}]'); a[0].legend(fontsize=8); a[0].grid(alpha=.3)
    a[1].fill_between(ts, -c['cur']['dd_c'], 0, color='tab:red', alpha=.5); a[1].set_title('A2 Drawdown cerrado (pips)'); a[1].grid(alpha=.3)
    a[2].fill_between(ts, -c['cur']['dd_f'], 0, color='tab:purple', alpha=.5)
    a[2].set_title('A3 Drawdown flotante por minuto, con concurrencia (pips)'); a[2].grid(alpha=.3)
    d = pnl_diario(c['tr_s'], tiempo)
    if d.empty: _vacio(a[3])
    else:
        cum = d.cumsum(); fin = cum.iloc[-1].sort_values()
        for s in cum.columns: a[3].plot(cum.index, cum[s], lw=0.7, alpha=.6)
        for s in list(fin.index[:3]) + list(fin.index[-3:]): a[3].annotate(s, (cum.index[-1], cum[s].iloc[-1]), fontsize=7)
        a[3].set_title('A4 Equity acumulada por símbolo (pips, diaria)'); a[3].grid(alpha=.3)
    _guardar(fig, f'R{r}_1_rendimiento.png')


def lamina_calidad(c):
    r = c['rank']; tr = c['tr_s']; rod = c['rod']
    fig, ax = plt.subplots(4, 2, figsize=(14, 13)); a = ax.ravel()
    if rod is None:
        for x in a: _vacio(x, "menos de 6 trades")
    else:
        n = len(tr); xs = np.arange(n)
        a[0].plot(xs, rod['T'], 'tab:blue'); a[0].set_title(f"B1 T mediano rodante (ventana {rod['w']})")
        if c['dec']:
            d = c['dec']; a[0].text(0.02, 0.05, f"{d['estado']}: {d['pend_100_trades']:+.4f}/100 trades  IC95[{d['IC_lo']:+.4f}, {d['IC_hi']:+.4f}]  ({d['bloques']} bloques)",
                                    transform=a[0].transAxes, fontsize=8, bbox=dict(fc='w', alpha=.8))
        for ax_, k, tit in ((a[2], 'Sortino', 'B2 Sortino-NEXUS rodante'), (a[3], 'PF', 'B2 Profit Factor rodante'),
                            (a[4], 'WR', 'B2 Win Rate rodante (%)'), (a[5], 'MaxDD', 'B2 MaxDD rodante (pips)'),
                            (a[6], 'Score', 'B2 score_final rodante')):
            ax_.plot(xs, rod[k], lw=1); ax_.set_title(tit + ' (NaN = rechazada por el juez)', fontsize=9)
    a[1].hist(tr['T_Score'], bins=40, color='tab:blue', alpha=.8); a[1].set_title('B3 Distribución de T')
    a[7].hist(tr['Profit_Pips'], bins=50, color='tab:green', alpha=.8); a[7].set_title('B3 Distribución de profit (pips)')
    for x in a: x.grid(alpha=.3)
    _guardar(fig, f'R{r}_2_calidad.png')


def lamina_composicion(c, tiempo, geom):
    r = c['rank']; tr = c['tr_s']; N = geom['N']; a0 = geom['vent_pf'][0]
    fig, ax = plt.subplots(3, 3, figsize=(16, 12)); a = ax.ravel()
    cz = tr['Tipo_Cierre'].value_counts(normalize=True).mul(100).sort_index()
    a[0].barh([CAUSAS[int(k)] for k in cz.index], cz.values, color='tab:cyan'); a[0].set_title('C1 Causas de cierre (%)')
    col = np.where(tr['Profit_Pips'] > 0, 'tab:green', 'tab:red')
    a[1].scatter(tr['MAE_Pips'], tr['MFE_Pips'], c=col, s=6, alpha=.5); a[1].set_xlabel('MAE'); a[1].set_ylabel('MFE'); a[1].set_title('C2 MAE vs MFE (verde=ganador)')
    a[2].hist(tr['Velas_Vida'], bins=40, color='tab:orange'); a[2].set_title('C3 Duración (velas)')
    mes = pd.Series(tiempo[tr['Idx_Out'].to_numpy()]).dt.to_period('M').value_counts().sort_index()
    a[3].bar(mes.index.astype(str), mes.values); a[3].set_title('C3 Trades por mes'); a[3].tick_params(axis='x', rotation=45)
    piv = tr.pivot_table(index='Simbolo', columns='Dir', values='Profit_Pips', aggfunc='sum', fill_value=0.0)
    im = a[4].imshow(piv.values, aspect='auto', cmap='RdYlGn', vmin=-np.abs(piv.values).max(), vmax=np.abs(piv.values).max())
    a[4].set_yticks(range(len(piv))); a[4].set_yticklabels(piv.index, fontsize=6); a[4].set_xticks(range(piv.shape[1])); a[4].set_xticklabels(piv.columns)
    a[4].set_title('D1 Pips netos por símbolo y dirección'); fig.colorbar(im, ax=a[4], fraction=.05)
    d = pnl_diario(tr, tiempo)
    if d.shape[1] >= 2:
        cm = d.corr(min_periods=10); im2 = a[5].imshow(cm.values, cmap='coolwarm', vmin=-1, vmax=1)
        a[5].set_xticks(range(len(cm))); a[5].set_xticklabels(cm.columns, rotation=90, fontsize=5)
        a[5].set_yticks(range(len(cm))); a[5].set_yticklabels(cm.index, fontsize=5); a[5].set_title('D2 Correlación de P&L diario entre pares'); fig.colorbar(im2, ax=a[5], fraction=.05)
    else: _vacio(a[5], "D2 requiere >=2 pares")
    ex = c['cur']['expo']; ts = tiempo[a0:N]
    h = pd.Series(ex, index=pd.to_datetime(ts)).resample('1h').max()
    a[6].plot(h.index, h.values, lw=.7); a[6].set_title('D3 Posiciones simultáneas (máx. por hora)'); a[6].tick_params(axis='x', rotation=30, labelsize=7)
    cc = concentracion(tr); st = c['stats']
    a[7].axis('off'); a[7].text(0.02, 0.95, "\n".join([
        f"Rank {r} [{st['Escalon']}] | motores {st['Motores']} | símbolos {st['Simbolos']}", f"Trades: {st['S_n']}  ({st['Trades_por_mes']:.1f}/mes)",
        f"Exposición media/máx: {st['Exposicion_media']:.2f} / {st['Exposicion_max']}",
        f"HHI contribución: {cc['HHI']:.3f} | Top-1 símbolo: {cc['Top1_%']:.1f}%",
        f"MaxDD flotante (minuto): {st['MaxDD_flotante_minuto']:.1f} pips"]), va='top', fontsize=10, family='monospace')
    a[8].axis('off')
    for x in (a[0], a[1], a[2], a[3], a[6]): x.grid(alpha=.3)
    _guardar(fig, f'R{r}_3_composicion.png')


def lamina_supervivencia(c, N, a0, tiempo):
    r = c['rank']; ts = tiempo[a0:N]
    fig, ax = plt.subplots(1, 3, figsize=(17, 5)); a = ax.ravel()
    es = _eq_cerrada(c['tr_s'], N, a0); eb = _eq_cerrada(c['tr_b'], N, a0)
    a[0].plot(ts, es, label=f"con supervivencia ({len(c['tr_s'])} trades)")
    a[0].plot(ts, eb, label=f"sin supervivencia ({len(c['tr_b'])} trades)")
    a[0].set_title('E1 Equity cerrada: con vs sin supervivencia'); a[0].legend(fontsize=8)
    a[1].fill_between(ts, es - eb, 0, color='tab:green', alpha=.5); a[1].set_title('E1 Diferencia (con − sin), pips')
    vl = c['vl']; tr = c['tr_s']
    if len(vl) and vl['T_Pred'].notna().any():
        m = vl.merge(tr[['Simbolo', 'Dir', 'Rank', 'Trade_Id', 'Idx_In', 'Tipo_Cierre']], on=['Simbolo', 'Dir', 'Rank', 'Trade_Id'], how='inner')
        m = m[m['T_Pred'].notna()].copy()
        # [H-45B-02 CERRADO] Edad física real de la vela abierta
        m['k'] = (m['Idx'] - m['Idx_In'] + 1).astype(int)
        for lab, sel, col in (('abortados por K', m['Tipo_Cierre'] == 4, 'tab:red'), ('resto', m['Tipo_Cierre'] != 4, 'tab:blue')):
            g = m[sel & (m['k'] <= 40)].groupby('k')['T_Pred']
            if len(g):
                q = g.quantile([.25, .5, .75]).unstack()
                a[2].plot(q.index, q[.5], color=col, label=lab)
                a[2].fill_between(q.index, q[.25], q[.75], color=col, alpha=.2)
        a[2].set_xlabel('Vela abierta del trade (evaluado tras inmunidad)')
        a[2].set_title(f'E2 T_pred a lo largo de la vida del trade [{c["stats"]["Escalon"]}]'); a[2].legend(fontsize=8)
    else:
        _vacio(a[2], "sin T_pred registrado")
    for x in a: x.grid(alpha=.3)
    _guardar(fig, f'R{r}_4_supervivencia.png')


def ficha_simbolo(sim, c, tiempo, geom):
    N = geom['N']; a0 = geom['vent_pf'][0]; ts = tiempo[a0:N]; r = c['rank']
    tr = c['tr_s'][c['tr_s']['Simbolo'] == sim]; tb = c['tr_b'][c['tr_b']['Simbolo'] == sim]; vl = c['vl'][c['vl']['Simbolo'] == sim]
    if tr.empty: return
    cur = curvas_minuto(tr, vl, N, a0)
    fig, ax = plt.subplots(2, 3, figsize=(16, 8)); a = ax.ravel(); s = stats_core(tr, MIN_OPS_PORTAFOLIO)
    for d, col in (('LONG', 'tab:green'), ('SHORT', 'tab:red')):
        a[0].plot(ts, _eq_cerrada(tr[tr['Dir'] == d], N, a0), color=col, lw=.9, label=d)
    a[0].plot(ts, cur['eq_c'], 'k', lw=1.2, label='total'); a[0].legend(fontsize=8); a[0].set_title(f'{sim} · Rank {r} [{c["stats"]["Escalon"]}] · A1 equity (pips)')
    a[1].fill_between(ts, -cur['dd_c'], 0, color='tab:red', alpha=.4, label='cerrado'); a[1].fill_between(ts, -cur['dd_f'], 0, color='tab:purple', alpha=.4, label='flotante')
    a[1].legend(fontsize=8); a[1].set_title('A2/A3 Drawdown (pips)')
    rod = rodantes(ordenar(tr))
    if rod is None: _vacio(a[2], f"B1: {len(tr)} trades (<6)")
    else:
        a[2].plot(rod['T']); a[2].set_title(f"B1 T rodante (ventana {rod['w']})")
    a[3].hist(tr['T_Score'], bins=25); a[3].set_title('B3 Distribución de T')
    cz = tr['Tipo_Cierre'].value_counts(normalize=True).mul(100).sort_index()
    a[4].barh([CAUSAS[int(k)] for k in cz.index], cz.values); a[4].set_title('C1 Causas de cierre (%)')
    a[5].plot(ts, _eq_cerrada(tr, N, a0), label='con supervivencia'); a[5].plot(ts, _eq_cerrada(tb, N, a0), label='sin supervivencia'); a[5].legend(fontsize=8); a[5].set_title('E1 con vs sin supervivencia')
    for x in a: x.grid(alpha=.3)
    fig.suptitle(f"{sim} | n={s['n']} | pips={s['Pips_Netos']:.0f} | " + ("RECHAZADO: " + s['Causa'] if s['Rechazado'] else f"Score={s['Score']:.1f} PF={s['PF']:.2f} WR={s['WR']:.1f}% T={s['T_med']:.3f}"), fontsize=10)
    _guardar(fig, f'R{r}_ficha_{sim}.png')


def grafico_paridad(mot):
    m = mot[mot['Paridad_Chequeada'] == True]
    if m.empty: return
    fig, ax = plt.subplots(1, 2, figsize=(12, 5.5))
    for k, (cx, cy, tit) in enumerate((('Par_n_F4', 'Par_n_45', 'Trades OOS (superv.)'), ('Par_T_F4', 'Par_T_45', 'T-SCORE OOS'))):
        for sim, g in m.groupby('Simbolo'): ax[k].scatter(g[cx], g[cy], s=14, alpha=.7, label=sim)
        lo = np.nanmin([m[cx].min(), m[cy].min()]); hi = np.nanmax([m[cx].max(), m[cy].max()])
        ax[k].plot([lo, hi], [lo, hi], 'k--', lw=.8); ax[k].set_xlabel('Fase 4 (CSV)'); ax[k].set_ylabel('Fase 4.5'); ax[k].set_title('F1 Paridad — ' + tit); ax[k].grid(alpha=.3)
    ok = int((m['Paridad_OK'] == True).sum()); fig.suptitle(f"Paridad exacta: {ok}/{len(m)} motores")
    _guardar(fig, 'F1_paridad.png')


# ==============================================================================
# 🚀 MAIN
# ==============================================================================
def _imprimir(st):
    print("=" * 95)
    print(f"📊 META-PORTAFOLIO RANK #{st['Rank']} [{st['Escalon']}] | motores {st['Motores']} | símbolos {st['Simbolos']} | trades {st['S_n']} ({st['Trades_por_mes']:.1f}/mes)")
    if st['S_Rechazado']: print(f"   ❌ RECHAZADO por el juez: {st['S_Causa']} | pips netos {st['S_Pips_Netos']:.1f} | T mediano {st['S_T_med']:.3f}")
    else:
        print(f"   Pips netos {st['S_Pips_Netos']:.1f} | PF {st['S_PF']:.2f} | WR {st['S_WR']:.1f}% | Sortino-NEXUS {st['S_Sortino']:.2f} | RF {st['S_RF']:.2f} | T mediano {st['S_T_med']:.3f} | Score {st['S_Score']:.1f}")
    print(f"   MaxDD core {st['S_MaxDD']:.1f} | cerrado(minuto) {st['MaxDD_cerrado_minuto']:.1f} | flotante concurrente {st['MaxDD_flotante_minuto']:.1f} | exposición media {st['Exposicion_media']:.2f} (máx {st['Exposicion_max']})")
    print(f"   Concentración: HHI {st['Conc_HHI']:.3f}, Top-1 {st['Conc_Top1_%']:.1f}% | Decaimiento: {st['Decay_estado']}")
    print(f"   Contrafactual SIN supervivencia: " + (f"RECHAZADO ({st['B_Causa']})" if st['B_Rechazado'] else f"PF {st['B_PF']:.2f}, T {st['B_T_med']:.3f}, pips {st['B_Pips_Netos']:.1f}") + f" | n={st['B_n']}")


def main():
    global _AVISO
    meta, tiempo, mot, tr_all, vl_all = cargar()
    geom = meta['geometria']; N = geom['N']; a0 = geom['vent_pf'][0]
    ciega = bool(geom.get('ciega', False))
    _AVISO = '' if ciega else '⚠ VENTANA NO CIEGA: se solapa con el OOS de Fase 4 — NO es evidencia fuera de muestra (RESERVA_FINAL en nexus_tablero.py)'
    print(('🔒 Ventana CIEGA (reserva de Fases 3 y 4)' if ciega else '⚠️  VENTANA NO CIEGA: se solapa con el OOS de Fase 4; las métricas NO son evidencia fuera de muestra') + f" | tablero {geom.get('tab_ver', '?')} hash {geom.get('tab_hash', '?')}")
    print(f"🚀 FASE 4.5B {FASE45B_VERSION} — ETAPA B (PORTAFOLIO) | core v{FORMULAS_CORE_VERSION} | Etapa A: {meta['fase45_version']} | ESCALÓN: {meta.get('escalon', ESCALON)} | N={N} | ventana [{a0}, {N})")

    resumen, sims = [], []
    escalon_meta = meta.get('escalon', ESCALON)
    for r in RANKS_COMPOSICION:
        c = componer_rank(r, mot, tr_all, vl_all, tiempo, geom, escalon_meta)
        if c is None:
            print(f"   ℹ️ Rank {r}: sin motores simulados."); continue
        resumen.append(c['stats']); sims.append(c['sim_tab']); _imprimir(c['stats'])
        c['tr_s'].to_csv(os.path.join(DIR_SALIDA, f"portafolio_rank{r}_trades.csv"), index=False, encoding='utf-8-sig')
        if r in RANKS_GRAFICOS:
            lamina_rendimiento(c, tiempo, geom); lamina_calidad(c); lamina_composicion(c, tiempo, geom)
            lamina_supervivencia(c, N, a0, tiempo)
            for sim in sorted(c['tr_s']['Simbolo'].unique()): ficha_simbolo(sim, c, tiempo, geom)

    if not resumen:
        raise RuntimeError("🛑 FATAL: ningún rank pudo componerse (¿la Etapa A no dejó motores simulados?).")

    pd.DataFrame(resumen).to_csv(os.path.join(DIR_SALIDA, "portafolios_por_rank.csv"), index=False, encoding='utf-8-sig')
    pd.concat(sims, ignore_index=True).to_csv(os.path.join(DIR_SALIDA, "simbolos_por_rank.csv"), index=False, encoding='utf-8-sig')
    grafico_paridad(mot)
    print(f"💾 Etapa B completa -> {DIR_SALIDA}/ (CSV) y {DIR_GRAF}/ (PNG)")


if __name__ == "__main__":
    main()