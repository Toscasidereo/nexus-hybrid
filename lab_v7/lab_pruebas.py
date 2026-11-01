# ==============================================================================
# NEXUS LAB-V7 — PRUEBAS DE LA COPIA DE LABORATORIO DE FASE 4 (Fase_4_lab.py)
# Carpeta: lab_v7/
# ==============================================================================
# BITÁCORA
#   V0.1 (2026-11-01) — Creación. Reglas fijadas antes de correr:
#     L1 paridad bit a bit con main (Fase_4_V12_0.py) con escala_v = 1: extractor_ml (15 columnas originales),
#        extractor_trayectoria (8 salidas) y simulador (4 salidas, con y sin supervivencia), lados long y short.
#     L2 la columna nueva Idx_Decision apunta a la vela de decisión (los features de la fila coinciden con los de esa vela).
#     L3 escala_v != 1 cambia el resultado del simulador (el parámetro se usa).
#     L4 lab_escala_v: 'off' = unos; rango [0.25, 4]; sin fuga IS->OOS (perturbar datos OOS no cambia la escala IS);
#        gemelo nulo conserva los valores de cada ventana y los reordena; determinista por semilla.
#     L5 lab_target_cierre: dT_cont y G_pips con caso armado a mano.
#     L6 lab_grid_k: T_terminal = grilla de main; otro target = percentiles de x·W_S + B_S.
#     L7 interruptores: por defecto TAG_ARCHIVOS igual que main; valor inválido falla; modos activos agregan sufijo.
#   Uso: python lab_v7/lab_pruebas.py  -> escribe lab_v7/lab_pruebas_resultados.json
# ==============================================================================
import os, sys, json, subprocess
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..'))
sys.path.insert(0, RAIZ); sys.path.insert(0, AQUI)
import Fase_4_V12_0 as M
import Fase_4_lab as L

PM = 10000.0


def entradas(rng, n, lado):
    """Arreglos sintéticos que activan entradas y salidas con frecuencia razonable."""
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
    S = (f(sin_), f(ext_in), f(sat_in), f(ac_in), f(sout), f(ext_out), f(sat_out), f(ac_out), *zs, o, h, l)
    return S, np.zeros(n, dtype=np.float32)


def main():
    out = {}
    rng = np.random.default_rng(5); n = 6000
    pars = (0.5, 0.1, 0.5, 0.1, 1.2)
    WR = rng.normal(0, 0.05, 10); WT = rng.normal(0, 0.05, 10); WS = rng.normal(0, 0.1, 10)
    uno = np.ones(n)
    l1, l2, l3 = {}, {}, {}
    for lado in ('long', 'short'):
        S, ph = entradas(rng, n, lado)
        ext_r = (M.extractor_ml_long, L.extractor_ml_long) if lado == 'long' else (M.extractor_ml_short, L.extractor_ml_short)
        ext_t = (M.extractor_trayectoria_long_v2, L.extractor_trayectoria_long_v2) if lado == 'long' else (M.extractor_trayectoria_short_v2, L.extractor_trayectoria_short_v2)
        sim = (M.simular_motor_long_superv_T, L.simular_motor_long_superv_T) if lado == 'long' else (M.simular_motor_short_superv_T, L.simular_motor_short_superv_T)
        # L1/L2 extractor_ml
        a = ext_r[0](*S, ph, PM, n, *pars); b = ext_r[1](*S, ph, PM, n, *pars)
        idx = b[:, 15].astype(np.int64)
        l1[f'ml_{lado}'] = bool(len(a) > 20 and b.shape[1] == 16 and np.array_equal(a, b[:, :15]))
        l2[lado] = bool(np.array_equal(b[:, 0], S[8][idx]) and np.array_equal(b[:, 9], S[15][idx]) and np.all(np.diff(idx) > 0))
        # L1 trayectoria
        targs = (WR, 0.0, 0.5, 0.1, 10.0, 0.0, WT, 0.0, -1.0)
        ta = ext_t[0](*S, ph, PM, n, *pars, *targs); tb = ext_t[1](*S, ph, PM, n, *pars, *targs, uno)
        l1[f'traj_{lado}'] = bool(len(ta[0]) > 50 and all(np.array_equal(x, y) for x, y in zip(ta, tb)))
        # L1 simulador, con y sin supervivencia, y L3
        res = []
        for sup in (False, True):
            sargs = (True, WR, 0.0, 0.5, 0.1, 10.0, 0.0, sup, WS, 0.0, 0.3, WT, 0.0, -1.0)
            sa = sim[0](*S, ph, PM, n, *pars, *sargs); sb = sim[1](*S, ph, PM, n, *pars, *sargs, uno)
            res.append(bool(len(sa[0]) > 20 and all(np.array_equal(x, y) for x, y in zip(sa, sb))))
            if not sup:
                sc = sim[1](*S, ph, PM, n, *pars, *sargs, np.full(n, 3.0))
                l3[lado] = bool(len(sc[0]) != len(sa[0]) or not np.array_equal(sa[2], sc[2]))
        l1[f'sim_{lado}'] = all(res)
    out['L1_paridad_con_main'] = {'detalle': l1, 'pasa': all(l1.values())}
    out['L2_Idx_Decision'] = {'detalle': l2, 'pasa': all(l2.values())}
    out['L3_escala_se_usa'] = {'detalle': l3, 'pasa': all(l3.values())}

    # L4
    N = 4000; itr, ftr, ite, fte = 100, 2000, 2000, 3500
    g = np.random.default_rng(9)
    act = np.abs(g.normal(30, 8, N)); act[:59] = np.nan
    idec = np.sort(g.choice(np.arange(60, 1900), 150, replace=False))
    X10 = g.normal(0, 1, (fte - itr, 10))
    xi = X10[idec - 0]  # features en la vela de decisión (ventana desde itr: se indexa con idec relativo)
    df = pd.DataFrame(g.normal(0, 1, (150, 10)), columns=L.COLS_X_ENTRADA)
    df['MFE_Pips'] = 5 + 2 * df.iloc[:, 0] + np.abs(g.normal(0, 1, 150)) + 3; df['Idx_Decision'] = idec - itr
    t4 = {}
    off = L.lab_escala_v('off', False, g, N, itr, ftr, ite, fte, df, act, None)
    t4['off_unos'] = bool(np.all(off == 1.0))
    for modo in ('A', 'B'):
        e1 = L.lab_escala_v(modo, False, np.random.default_rng(1), N, itr, ftr, ite, fte, df, act, X10 if modo == 'A' else None)
        t4[f'{modo}_rango'] = bool(e1[itr:fte].min() >= 0.25 and e1[itr:fte].max() <= 4.0 and np.all(e1[:itr] == 1.0) and np.all(e1[fte:] == 1.0))
        act2 = act.copy(); act2[ite:fte] *= 3.0; X2 = X10.copy(); X2[ite - itr:] += 5.0
        e2 = L.lab_escala_v(modo, False, np.random.default_rng(1), N, itr, ftr, ite, fte, df, act2, X2 if modo == 'A' else None)
        t4[f'{modo}_sin_fuga_IS'] = bool(np.array_equal(e1[itr:ftr], e2[itr:ftr]) and not np.array_equal(e1[ite:fte], e2[ite:fte]))
        n1 = L.lab_escala_v(modo, True, np.random.default_rng(7), N, itr, ftr, ite, fte, df, act, X10 if modo == 'A' else None)
        n2 = L.lab_escala_v(modo, True, np.random.default_rng(7), N, itr, ftr, ite, fte, df, act, X10 if modo == 'A' else None)
        t4[f'{modo}_nulo'] = bool(np.array_equal(n1, n2) and not np.array_equal(n1[itr:ftr], e1[itr:ftr])
                                  and np.array_equal(np.sort(n1[itr:ftr]), np.sort(e1[itr:ftr]))
                                  and np.array_equal(np.sort(n1[ite:fte]), np.sort(e1[ite:fte])))
    out['L4_escala'] = {'detalle': t4, 'pasa': all(t4.values())}

    # L5
    tid = np.array([0, 0, 0, 1, 1]); prof = np.array([1., 2., 3., -1., -2.], dtype=np.float32)
    tsc = np.array([.1, .2, .3, .4, .5], dtype=np.float32); y = np.array([.9, .9, .9, .2, .2], dtype=np.float32)
    d = L.lab_target_cierre('dT_cont', y, tsc, prof, tid); gp = L.lab_target_cierre('G_pips', y, tsc, prof, tid)
    out['L5_targets'] = {'dT_cont': d.tolist(), 'G_pips': gp.tolist(),
                         'pasa': bool(np.allclose(d, [.8, .7, .6, -.2, -.3]) and np.allclose(gp, [2, 1, 0, -1, 0])
                                      and np.array_equal(L.lab_target_cierre('T_terminal', y, tsc, prof, tid), y))}

    # L6
    xt = np.random.default_rng(3).normal(0, 1, (500, 10)); ws = np.random.default_rng(4).normal(0, 1, 10)
    gk = L.lab_grid_k('dT_cont', xt, ws, 0.25)
    ref = np.unique(np.percentile(xt @ ws + 0.25, np.arange(0, 55, 5)))
    out['L6_grilla_K'] = {'n_valores': int(len(gk)), 'pasa': bool(np.allclose(gk, ref) and np.array_equal(L.lab_grid_k('T_terminal', xt, ws, 0.0), M.CANDIDATOS_K_ABORTAR))}

    # L7
    def tag(env):
        e = {**os.environ, **env}
        r = subprocess.run([sys.executable, '-c', f"import sys; sys.path[:0]=[{RAIZ!r},{AQUI!r}]; import Fase_4_lab as L; print(L.TAG_ARCHIVOS)"],
                           capture_output=True, text=True, env=e)
        return r.returncode, r.stdout.strip()
    c0, t0 = tag({}); c1, t1 = tag({'NEXUS_LAB_TAMANO': 'A', 'NEXUS_LAB_CIERRE': 'dT_cont', 'NEXUS_LAB_NULO': '1'}); c2, _ = tag({'NEXUS_LAB_TAMANO': 'Z'})
    out['L7_interruptores'] = {'tag_defecto': t0, 'tag_lab': t1, 'pasa': bool(c0 == 0 and t0 == M.TAG_ARCHIVOS and c1 == 0 and t1.endswith('_LAB_A_dT_cont_NULO') and c2 != 0)}

    out['todas_pasan'] = all(v['pasa'] for k, v in out.items() if isinstance(v, dict) and 'pasa' in v)
    with open(os.path.join(AQUI, 'lab_pruebas_resultados.json'), 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
