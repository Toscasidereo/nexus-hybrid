# ==============================================================================
# NEXUS LAB-V7 — PRUEBAS DE VIDA v3 (SINTÉTICAS; ANTES DE USAR DATOS REALES)
# Carpeta: lab_v7/
# ==============================================================================
# BITÁCORA
#   V0.1 (2026-11-06) — Creación. Reglas fijadas antes de correr (ESPECIFICACION_VIDA_V3.md §5):
#     V1 descriptores: caso armado a mano (EFR, D_h, FET_v3, REC, RIT en una foto concreta; REC no aplicable -> S = 0.5).
#     V2 causalidad: el valor vivo en la última foto es igual al terminal (comparado en float32, que es el tipo del target; corregido el mismo día: la primera versión comparaba float64 con float32); invariancia de prefijo (truncar un trade en m fotos no cambia
#        los primeros m valores vivos, con las mismas constantes).
#     V3 no mecánica: trayectorias con deriva positiva: cortar cada trade en un punto al azar de su vida no sube la mediana de V3
#        (tolerancia 0.01); con deriva cero: |diferencia de medianas| <= 0.05.
#     V4 contra sustitutos: entradas informativas (deriva positiva) puntúan por encima de entradas al azar (mediana, margen 0.05).
#     V5 aprendibilidad: R² agrupado con relación lineal conocida > 0.8; con el target permutado |R²| < 0.05.
#     V6 compuesto: V3 en [0, 1]; pesos suman 1; un descriptor no aplicable queda en 0.5.
#     V7 integración con Fase_4_lab: fotos de extractor_trayectoria_{long,short}_v2 -> lab_target_cierre('V3') devuelve un valor por foto,
#        finito, en [0, 1], constante dentro de cada trade; lab_grid_k('V3') usa percentiles de la predicción (no la grilla de main).
#   Uso: python lab_v7/vida_pruebas.py   Escribe lab_v7/vida_pruebas_resultados.json
# ==============================================================================
import os, sys, json
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, '..'))
sys.path.insert(0, RAIZ); sys.path.insert(0, AQUI)
import vida_v3 as VV

PM = 10000.0


def trayectorias(rng, n_trades, drift, vol=1.0, c=1.0, dur=(5, 60)):
    """Fotos sintéticas por trade: g = camino bruto en pips (recorrido aleatorio con deriva); prof = g - c; MFE/MAE brutos corrientes."""
    P, F, A, T, V, FIN = [], [], [], [], [], []
    for t in range(n_trades):
        d = int(rng.integers(dur[0], dur[1] + 1)); g = np.cumsum(rng.normal(drift, vol, d))
        prof = g - c
        mfe = np.maximum(np.maximum.accumulate(np.maximum(g, 0.0)), prof + c); mae = np.minimum(np.minimum.accumulate(np.minimum(g, 0.0)), prof + c)
        P.append(prof); F.append(mfe); A.append(mae); T.append(np.full(d, t)); V.append(np.arange(1, d + 1))
    return [np.concatenate(x) for x in (P, F, A, T, V)]


def entradas(rng, n, lado):
    f = lambda x: np.asarray(x, dtype=np.float32)
    if lado == 'long':
        sin_, ext_in, sat_in, ac_in = -np.ones(n), -np.ones(n), -np.ones(n), rng.uniform(-0.85, 1, n)
        sout = np.where(rng.random(n) < 0.04, 1.0, -1.0); ext_out, sat_out, ac_out = np.ones(n), np.ones(n), rng.uniform(-1, 0.85, n)
    else:
        sin_, ext_in, sat_in, ac_in = np.ones(n), np.ones(n), np.ones(n), rng.uniform(-1, 0.85, n)
        sout = np.where(rng.random(n) < 0.04, -1.0, 1.0); ext_out, sat_out, ac_out = -np.ones(n), -np.ones(n), rng.uniform(-0.85, 1, n)
    zs = [f(rng.normal(0, 1, n)) for _ in range(8)]
    o = 1.10 + np.cumsum(rng.normal(0, 0.8, n)) / PM
    h = o + np.abs(rng.normal(0, 0.5, n)) / PM; l = o - np.abs(rng.normal(0, 0.5, n)) / PM
    return (f(sin_), f(ext_in), f(sat_in), f(ac_in), f(sout), f(ext_out), f(sat_out), f(ac_out), *zs, o, h, l), np.zeros(n, dtype=np.float32)


def main():
    out = {}
    # V1 caso a mano
    c, h = 1.0, 60.0
    prof = np.array([-1, -3, -4, -1, 3.0, 2, 2, 2.5]); mfe = np.array([0, 0, 0, 2, 4, 1, 2, 3.0]); mae = np.array([-1, -3, -4, -4, -4, -1, -1, -1.0])
    tid = np.array([0, 0, 0, 0, 0, 1, 1, 1]); vela = np.array([1, 2, 3, 4, 5, 1, 2, 3])
    raw, apl = VV._vivos_nb(prof, mfe, mae, tid, vela, c, h)
    esperado = np.array([(1 + 3 / 9) / 2, 1 / (1 + 4 / 60), 0.25, 3.5, 0.6])
    v1 = {'foto5_descriptores': bool(np.allclose(raw[4], esperado, atol=1e-12)), 'rec_no_aplica_sin_fondo': bool((not apl[0]) and (not apl[5]) and apl[1] and apl[4]),
          'rec_neutro_en_S': bool(VV.normalizar(raw, apl, {'med': np.zeros(5), 'escala': np.ones(5)})[0, 3] == 0.5)}
    out['V1_descriptores_a_mano'] = {'detalle': v1, 'pasa': all(v1.values())}

    # V2 causalidad
    rng = np.random.default_rng(1)
    P, F, A, T, V = trayectorias(rng, 300, 0.03)
    base = VV.vida_v3(P, F, A, T, V, 1.0, 4.0)
    st = base['stats']; ok_last = True; ok_pref = True
    for t in rng.choice(300, 40, replace=False):
        m = T == t; ult = np.where(m)[0][-1]
        ok_last &= bool(np.float32(base['V3'][ult]) == base['V3_term'][ult])   # V3_term se guarda en float32 (como T_terminal)
        mm = int(rng.integers(1, m.sum() + 1)); sel = np.where(m)[0][:mm]
        corto = VV.vida_v3(P[sel], F[sel], A[sel], T[sel], V[sel], 1.0, 4.0, stats=st)
        ok_pref &= bool(np.allclose(corto['V3'], base['V3'][sel], atol=1e-12) and np.allclose(corto['S'], base['S'][sel], atol=1e-12))
    out['V2_causalidad'] = {'detalle': {'vivo_ultima_foto_igual_terminal': bool(ok_last), 'invariancia_de_prefijo': bool(ok_pref)}, 'pasa': bool(ok_last and ok_pref)}

    # V3 no mecánica
    v3 = {}
    for nombre, drift in (('deriva_positiva', 0.08), ('deriva_cero', 0.0)):
        rng = np.random.default_rng(2)
        P, F, A, T, V = trayectorias(rng, 1500, drift)
        full = VV.vida_v3(P, F, A, T, V, 1.0, 4.0); st = full['stats']
        tu = np.unique(T); orig = np.array([full['V3'][np.where(T == t)[0][-1]] for t in tu])
        corte = np.array([full['V3'][np.where(T == t)[0][int(rng.integers(0, (T == t).sum()))]] for t in tu])
        dif = float(np.median(corte) - np.median(orig))
        v3[nombre + '_dif_mediana'] = round(dif, 4)
        v3[nombre + '_ok'] = bool(dif <= 0.01) if drift > 0 else bool(abs(dif) <= 0.05)
    out['V3_no_mecanica'] = {'detalle': v3, 'pasa': bool(v3['deriva_positiva_ok'] and v3['deriva_cero_ok'])}

    # V4 contra sustitutos (stats comunes: las de las entradas informativas no deben usarse solo para ellas)
    rng = np.random.default_rng(3)
    Pi, Fi, Ai, Ti, Vi = trayectorias(rng, 1200, 0.10)
    Pr, Fr, Ar, Tr, Vr = trayectorias(rng, 1200, 0.0)
    st = VV.vida_v3(np.concatenate([Pi, Pr]), np.concatenate([Fi, Fr]), np.concatenate([Ai, Ar]), np.concatenate([Ti, Tr + 5000]), np.concatenate([Vi, Vr]), 1.0, 4.0)['stats']
    mi = VV.vida_v3(Pi, Fi, Ai, Ti, Vi, 1.0, 4.0, stats=st); mr = VV.vida_v3(Pr, Fr, Ar, Tr, Vr, 1.0, 4.0, stats=st)
    ti = np.unique(Ti); tr_ = np.unique(Tr)
    med_i = float(np.median([mi['V3'][np.where(Ti == t)[0][-1]] for t in ti])); med_r = float(np.median([mr['V3'][np.where(Tr == t)[0][-1]] for t in tr_]))
    out['V4_contra_sustitutos'] = {'detalle': {'mediana_informativas': round(med_i, 4), 'mediana_azar': round(med_r, 4)}, 'pasa': bool(med_i > med_r + 0.05)}

    # V5 aprendibilidad
    rng = np.random.default_rng(4); X = rng.normal(size=(2000, 5)); y = X @ np.array([1.0, -0.5, 0.3, 0, 0]) + 0.3 * rng.normal(size=2000); g = np.arange(2000) // 8
    r_lin = VV.r2_agrupado(X, y, g); r_perm = VV.r2_agrupado(X, rng.permutation(y), g)
    out['V5_aprendibilidad'] = {'detalle': {'R2_lineal': round(r_lin, 4), 'R2_permutado': round(r_perm, 4)}, 'pasa': bool(r_lin > 0.8 and abs(r_perm) < 0.05)}

    # V6 compuesto
    rng = np.random.default_rng(5); P, F, A, T, V = trayectorias(rng, 400, 0.02)
    r = VV.vida_v3(P, F, A, T, V, 1.0, 4.0)
    nA = ~r['apl']
    v6 = {'V3_en_0_1': bool(r['V3'].min() >= 0 and r['V3'].max() <= 1), 'pesos_suman_1': bool(abs(VV.PESOS_V3.sum() - 1.0) < 1e-12),
          'no_aplicable_en_05': bool(np.all(r['S'][nA, 3] == 0.5)) and bool(nA.sum() > 0), 'terminal_constante_por_trade': bool(all(np.unique(r['V3_term'][T == t]).size == 1 for t in range(0, 400, 20)))}
    out['V6_compuesto'] = {'detalle': v6, 'pasa': all(v6.values())}

    # V7 integración con Fase_4_lab
    import Fase_4_lab as L
    v7 = {}
    rng = np.random.default_rng(6); n = 6000; pars = (0.5, 0.1, 0.5, 0.1, 1.2)
    WR = rng.normal(0, 0.05, 10); WT = rng.normal(0, 0.05, 10)
    for lado in ('long', 'short'):
        S, ph = entradas(rng, n, lado)
        ext_t = L.extractor_trayectoria_long_v2 if lado == 'long' else L.extractor_trayectoria_short_v2
        x_traj, y_t, prof_s, mae_s, mfe_s, tsc_s, tid_s, vela_s = ext_t(*S, ph, PM, n, *pars, WR, 0.0, 0.5, 0.1, 10.0, 0.0, WT, 0.0, -1.0, np.ones(n))
        vida = {}
        y = L.lab_target_cierre('V3', y_t, tsc_s, prof_s, tid_s, mfe_s, mae_s, vela_s, 1.2, float(L.V7.escala_h(S[16], PM)), vida)
        const = all(np.unique(y[tid_s == t]).size == 1 for t in np.unique(tid_s)[:60])
        v7[f'{lado}_un_valor_por_foto_finito_0_1'] = bool(len(y) == len(tid_s) > 50 and np.all(np.isfinite(y)) and y.min() >= 0 and y.max() <= 1)
        v7[f'{lado}_constante_por_trade'] = bool(const)
        v7[f'{lado}_descriptores_en_dict'] = bool('S_term' in vida and vida['S_term'].shape == (len(y), 5))
        gk = L.lab_grid_k('V3', x_traj, WR * 0 + 0.1, 0.3)
        v7[f'{lado}_grilla_percentiles'] = bool(len(gk) > 3 and np.all(np.diff(gk) > 0) and not np.array_equal(gk, L.CANDIDATOS_K_ABORTAR))
        # T_terminal intacto
        v7[f'{lado}_T_terminal_sin_cambio'] = bool(np.array_equal(L.lab_target_cierre('T_terminal', y_t, tsc_s, prof_s, tid_s), y_t))
    out['V7_integracion_Fase4_lab'] = {'detalle': v7, 'pasa': all(v7.values())}

    out['todas_pasan'] = all(v['pasa'] for k, v in out.items() if isinstance(v, dict) and 'pasa' in v)
    with open(os.path.join(AQUI, 'vida_pruebas_resultados.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
