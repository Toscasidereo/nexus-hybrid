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
#   V0.2 (2026-11-04) — EA gemelo. Reglas fijadas antes de correr:
#     L6 (ajustada): la grilla de K con otro target se redondea a 5 decimales (precisión de export de k_abortar).
#     L8 contrato de export del Ridge de tamaño: el texto C++ de `lab_bloque_tam` se parsea y una emulación independiente del EA
#        (bucles escalares de Python, mismo orden de operaciones que el código MQL5 del EA gemelo) reproduce la escala de
#        `lab_escala_v` IGUAL BIT A BIT en modos A y B, y la actividad `lab_actividad_nb` iguala la suma del EA (desplazamiento 59 → 0).
#        Con modo 'off' el bloque es vacío (texto idéntico a main).
#   V0.3 (2026-11-04) — Cadena alineada (Fase 4.5 del lab). Reglas fijadas antes de correr:
#     L9  Fase_4_5_lab_A.simular_motor con escala = 1 iguala bit a bit a Fase_4_5_V_12_0_A.simular_motor (main), long y short, con y
#         sin supervivencia; con escala != 1 el resultado cambia.
#     L10 el texto exportado (lab_bloque_tam) leído por Fase_4_5_lab_A.parse_tam y reconstruido con lab_escala.escala_desde_parametros
#         reproduce IGUAL BIT A BIT la escala de lab_escala_v (modos A y B); un bloque sin tam_* da None.
#     L11 tag y carpeta: con interruptores apagados Fase_4_5_lab_A/B igualan a main; con interruptores activos el tag coincide con el de
#         Fase_4_lab.TAG_ARCHIVOS; tamaño + gemelo nulo se rechaza al iniciar.
#   V0.4 (2026-11-04) — Métrica de selección (NEXUS_LAB_METRICA). Reglas fijadas antes de correr:
#     L12 kernels `_ix`: las 4 primeras salidas iguales bit a bit a las de los kernels originales del lab (long y short, con y sin
#         supervivencia); vela de entrada < vela de salida; el pip neto de cada trade = dirección*(Open[salida]-Open[entrada])*pm - spread.
#     L13 `lab_eval_v7`: r[0] = Score_v7 (igual a llamar V7.score_v7 directo); ex['sf'] = Score_final de los mismos trades; r[1:] = los de
#         eval_robustez_numba_v6. `lab_escanear_k_v7` (con evaluador simulado de puntajes conocidos): elige el K de mayor puntaje, devuelve
#         None si ninguno es positivo, usa nt = len(grilla), es determinista.
#     L11 (ampliada): el tag con NEXUS_LAB_METRICA=v7 lleva _MV7 y coincide entre Fase 4 lab y Fase 4.5 lab A/B.
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
import Fase_4_5_V_12_0_A as M45
import Fase_4_5_lab_A as L45
from lab_escala import escala_desde_parametros

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
    ref = np.unique(np.round(np.percentile(xt @ ws + 0.25, np.arange(0, 55, 5)), 5))
    out['L6_grilla_K'] = {'n_valores': int(len(gk)), 'pasa': bool(np.allclose(gk, ref) and np.array_equal(L.lab_grid_k('T_terminal', xt, ws, 0.0), M.CANDIDATOS_K_ABORTAR))}

    # L7
    def tag(env):
        e = {**os.environ, **env}
        r = subprocess.run([sys.executable, '-c', f"import sys; sys.path[:0]=[{RAIZ!r},{AQUI!r}]; import Fase_4_lab as L; print(L.TAG_ARCHIVOS)"],
                           capture_output=True, text=True, env=e)
        return r.returncode, r.stdout.strip()
    c0, t0 = tag({}); c1, t1 = tag({'NEXUS_LAB_TAMANO': 'A', 'NEXUS_LAB_CIERRE': 'dT_cont', 'NEXUS_LAB_NULO': '1'}); c2, _ = tag({'NEXUS_LAB_TAMANO': 'Z'})
    out['L7_interruptores'] = {'tag_defecto': t0, 'tag_lab': t1, 'pasa': bool(c0 == 0 and t0 == M.TAG_ARCHIVOS and c1 == 0 and t1.endswith('_LAB_A_dT_cont_NULO') and c2 != 0)}


    # L8 contrato de export del Ridge de tamaño + emulación del EA gemelo
    import re
    def ea_actividad(op, i, pm):
        t = 0.0
        for m in range(59, -1, -1):
            t += abs(op[i - m] - op[i - m - 1]) * pm
        return t
    def ea_escala(tp, xrow, act):
        a = act / tp['act_med'] if act >= 0.0 else tp['a_is_med']
        if tp['modo'] == 2:
            e = a / tp['a_is_med']
        else:
            t = 0.0
            for k in range(11):
                xk = xrow[k] if k < 10 else a
                t += tp['w'][k] * ((xk - tp['mu'][k]) / tp['sd'][k])
            e = (t + tp['intercept']) / tp['med_pred']
        return min(max(e, tp['esc_min']), tp['esc_max'])
    def parsear(txt):
        tp = {'w': [0.0] * 11, 'mu': [0.0] * 11, 'sd': [1.0] * 11}
        for nom, k, v in re.findall(r'tam_(w|mu|sd)\[(\d+)\]=([-\d.]+);', txt):
            tp[nom][int(k)] = float(v)
        for nom, v in re.findall(r'\.tam_(modo|act_med|a_is_med|esc_min|esc_max|intercept|med_pred) = ([-\d.]+);', txt):
            tp[nom] = int(v) if nom == 'modo' else float(v)
        return tp
    gg = np.random.default_rng(21); Nn = 4000
    op = 1.10 + np.cumsum(gg.normal(0, 0.8, Nn)) / PM
    ACT = L.lab_actividad_nb(op, PM, 60)
    t8 = {'act_nan_prefijo': bool(np.isnan(ACT[:59]).all() and np.isfinite(ACT[59:]).all()),
          'act_igual_EA': bool(all(ACT[i] == ea_actividad(op, i, PM) for i in range(100, Nn, 37)))}
    idec8 = np.sort(gg.choice(np.arange(120, 1900), 150, replace=False)); X8 = gg.normal(0, 1, (3500 - 100, 10))
    df8 = pd.DataFrame(X8[idec8 - 100], columns=L.COLS_X_ENTRADA)
    df8['MFE_Pips'] = 5 + 2 * df8.iloc[:, 0] + np.abs(gg.normal(0, 1, 150)) + 3; df8['Idx_Decision'] = idec8 - 100
    for modo in ('A', 'B'):
        par = {}
        e8 = L.lab_escala_v(modo, False, np.random.default_rng(1), Nn, 100, 2000, 2000, 3500, df8, ACT, X8 if modo == 'A' else None, par)
        tp = parsear('X' + L.lab_bloque_tam('ml_toro', par))
        ok_modo = bool(tp.get('modo') == (1 if modo == 'A' else 2))
        filas = range(100, 3500, 29)
        iguales = all(e8[i] == ea_escala(tp, X8[i - 100], ACT[i]) for i in filas)
        t8[f'{modo}_modo_y_parametros'] = ok_modo
        t8[f'{modo}_escala_igual_bit_a_bit'] = bool(iguales)
        t8[f'{modo}_rango'] = bool(e8[100:3500].min() >= 0.25 and e8[100:3500].max() <= 4.0)
    t8['off_bloque_vacio'] = bool(L.lab_bloque_tam('ml_toro', {}) == '' and L.lab_bloque_tam('ml_oso', {'modo': 'off'}) == '')
    out['L8_export_tamano_y_EA_gemelo'] = {'detalle': t8, 'pasa': all(t8.values())}

    # L9 kernel de Fase 4.5 del lab vs main
    l9 = {}
    rng9 = np.random.default_rng(11); n9 = 6000; WR9 = rng9.normal(0, 0.05, 10); WT9 = rng9.normal(0, 0.05, 10); WS9 = rng9.normal(0, 0.1, 10)
    for lado, dcode in (('long', 1), ('short', -1)):
        S9, ph9 = entradas(rng9, n9, lado)
        for sup in (False, True):
            args = (dcode, 0, *S9, ph9, PM, n9, 0.5, 0.1, 0.5, 0.1, 1.2, WR9, 0.0, 0.5, 0.1, 10.0, 0.0, 0.60, 1.5,
                    sup, WS9, 0.0, 0.3, 2, 10, True, WT9, 0.0, -1.0)
            a9 = M45.simular_motor(*args); b9 = L45.simular_motor(*args, np.ones(n9))
            l9[f'{lado}_superv{int(sup)}_igual_main'] = bool(len(a9[0]) > 10 and all(np.array_equal(x, y, equal_nan=True) for x, y in zip(a9, b9)))
        c9 = L45.simular_motor(*args, np.full(n9, 3.0))
        l9[f'{lado}_escala_se_usa'] = bool(len(c9[0]) != len(a9[0]) or not np.array_equal(c9[0], a9[0], equal_nan=True))
    out['L9_kernel_45_lab'] = {'detalle': l9, 'pasa': all(l9.values())}

    # L10 texto exportado -> parse_tam -> escala (bit a bit)
    l10 = {}
    for modo in ('A', 'B'):
        par = {}
        e10 = L.lab_escala_v(modo, False, np.random.default_rng(1), Nn, 100, 2000, 2000, 3500, df8, ACT, X8 if modo == 'A' else None, par)
        tam = L45.parse_tam('X' + L.lab_bloque_tam('ml_toro', par), 'ml_toro')
        rec = escala_desde_parametros(tam, X8 if modo == 'A' else None, ACT[100:3500])
        l10[f'{modo}_modo'] = bool(tam['modo'] == modo)
        l10[f'{modo}_escala_igual_bit_a_bit'] = bool(np.array_equal(rec, e10[100:3500]))
    l10['sin_tam_da_None'] = bool(L45.parse_tam('g_pares[idx].ml_toro.umbral = 0.0;', 'ml_toro') is None)
    out['L10_export_parse_escala'] = {'detalle': l10, 'pasa': all(l10.values())}

    # L11 tag y carpeta de Fase 4.5 del lab
    def val(modulo, expr, env):
        e = {**os.environ, **env}
        r = subprocess.run([sys.executable, '-c', f"import sys; sys.path[:0]=[{RAIZ!r},{AQUI!r}]; import {modulo} as X; print({expr})"],
                           capture_output=True, text=True, env=e)
        return r.returncode, r.stdout.strip()
    l11 = {}
    for nombre, env in (('defecto', {}), ('cierre', {'NEXUS_LAB_CIERRE': 'dT_cont'}), ('tamano', {'NEXUS_LAB_TAMANO': 'B'}),
                        ('nulo_cierre', {'NEXUS_LAB_CIERRE': 'G_pips', 'NEXUS_LAB_NULO': '1'}),
                        ('metrica_v7', {'NEXUS_LAB_METRICA': 'v7'})):
        c4, t4 = val('Fase_4_lab', 'X.TAG_ARCHIVOS', env)
        cA, tA = val('Fase_4_5_lab_A', 'X.TAG_ARCHIVOS_FASE4', env)
        cA2, dA = val('Fase_4_5_lab_A', 'X.DIR_SALIDA', env)
        cB, dB = val('Fase_4_5_lab_B', 'X.DIR_SALIDA', env)
        l11[f'{nombre}_tag_igual_Fase4'] = bool(c4 == 0 and cA == 0 and t4 == tA)
        l11[f'{nombre}_carpetas_A_B_iguales'] = bool(cA2 == 0 and cB == 0 and dA == dB and dA == 'F45_V12_E3' + tA[len('PROD_V12_E3'):])
    l11['metrica_v7_lleva_MV7'] = bool(val('Fase_4_lab', 'X.TAG_ARCHIVOS', {'NEXUS_LAB_METRICA': 'v7'})[1].endswith('_MV7'))
    l11['defecto_igual_main'] = bool(M45.TAG_ARCHIVOS_FASE4 == 'PROD_V12_E3' and M45.DIR_SALIDA == 'F45_V12_E3')
    cX, _ = val('Fase_4_5_lab_A', 'X.DIR_SALIDA', {'NEXUS_LAB_TAMANO': 'A', 'NEXUS_LAB_NULO': '1'})
    l11['tamano_mas_nulo_rechazado'] = bool(cX != 0)
    out['L11_tag_y_carpeta_45'] = {'detalle': l11, 'pasa': all(l11.values())}

    # L12 kernels _ix
    l12 = {}
    rng12 = np.random.default_rng(31); n12 = 6000; WR12 = rng12.normal(0, 0.05, 10); WT12 = rng12.normal(0, 0.05, 10); WS12 = rng12.normal(0, 0.1, 10)
    uno12 = np.ones(n12)
    for lado, dcode in (('long', 1), ('short', -1)):
        S12, ph12 = entradas(rng12, n12, lado)
        k_o = L.simular_motor_long_superv_T if lado == 'long' else L.simular_motor_short_superv_T
        k_x = L.simular_motor_long_superv_T_ix if lado == 'long' else L.simular_motor_short_superv_T_ix
        for sup in (False, True):
            sargs = (True, WR12, 0.0, 0.5, 0.1, 10.0, 0.0, sup, WS12, 0.0, 0.3, WT12, 0.0, -1.0)
            a12 = k_o(*S12, ph12, PM, n12, *pars, *sargs, uno12); b12 = k_x(*S12, ph12, PM, n12, *pars, *sargs, uno12)
            l12[f'{lado}_superv{int(sup)}_4_salidas_iguales'] = bool(len(a12[0]) > 10 and len(b12) == 6 and all(np.array_equal(x, y) for x, y in zip(a12, b12[:4])))
            ent, sal = b12[4], b12[5]; op12 = S12[16]
            esperado = dcode * (op12[sal] - op12[ent]) * PM - pars[4]
            l12[f'{lado}_superv{int(sup)}_indices_y_pip_neto'] = bool(np.all(ent < sal) and np.all(np.diff(ent) > 0) and np.allclose(b12[2], esperado, atol=1e-3))
    out['L12_kernels_ix'] = {'detalle': l12, 'pasa': all(l12.values())}

    # L13 evaluador y escaneo de K
    import v7_metricas as V7
    l13 = {}
    S13, ph13 = entradas(np.random.default_rng(41), 8000, 'long')
    tup13 = L.simular_motor_long_superv_T_ix(*S13, ph13, PM, 8000, *pars, True, WR12, 0.0, 0.5, 0.1, 10.0, 0.0, False, WS12, 0.0, 0.3, WT12, 0.0, -1.0, np.ones(8000))
    O13, H13, L13_ = S13[16], S13[17], S13[18]
    r13, ex13 = L.lab_eval_v7(tup13, 1, O13, H13, L13_, PM, pars[4], 1, 0.0, 20, 20, 5)
    direc = V7.score_v7(np.ones(len(tup13[2]), dtype=np.int64), tup13[4], tup13[5], tup13[2].astype(np.float64), O13, H13, L13_, O13, PM, pars[4],
                        nt=1, sigma_sr=0.0, opcion=L.LAB_V7_OPCION, rng=np.random.default_rng(5), R=L.LAB_V7_R, n_min=20)['score_v7']
    ref13 = np.asarray(L.eval_robustez_numba_v6(*tup13[:4], 20), dtype=np.float64)
    l13['r0_es_score_v7'] = bool(r13[0] == ex13['v7'] == direc)
    l13['sf_igual_Score_final'] = bool(ex13['sf'] == float(ref13[0]))
    l13['resto_de_r_intacto'] = bool(np.array_equal(r13[1:], ref13[1:], equal_nan=True))
    registro = {}
    def fake_eval(tup, dircode, O, H, Lw, pm, c, nt, sigma_sr, n_min, min_trades, seed):
        registro['nt'] = nt; registro['sigma'] = sigma_sr
        sc = {0.1: 3.0, 0.2: 9.0, 0.3: 5.0}[round(float(tup[0][0]), 1)]       # el simulador falso codifica K en mfe[0]
        return np.array([sc, 0.0]), {'sf': 1.0, 'v7': sc}
    def sim_falso(act, k):
        n = 30; e = np.arange(n) * 10; sal = e + 5
        mfe = np.full(n, k, dtype=np.float32); pi = (np.arange(n) % 5 - 1.0).astype(np.float32)
        return mfe, mfe, pi, mfe, e.astype(np.int64), sal.astype(np.int64)
    orig = L.lab_eval_v7
    try:
        L.lab_eval_v7 = fake_eval
        k_sel, r_sel, ex_sel = L.lab_escanear_k_v7(sim_falso, [0.1, 0.2, 0.3], 1, O13, H13, L13_, PM, 1.0, 20, 5)
        k_sel2, _, _ = L.lab_escanear_k_v7(sim_falso, [0.1, 0.2, 0.3], 1, O13, H13, L13_, PM, 1.0, 20, 5)
        def todos_cero(tup, dircode, O, H, Lw, pm, c, nt, sigma_sr, n_min, min_trades, seed):
            return np.array([0.0, 0.0]), {'sf': 1.0, 'v7': 0.0}
        L.lab_eval_v7 = todos_cero
        k_nada, _, _ = L.lab_escanear_k_v7(sim_falso, [0.1, 0.2, 0.3], 1, O13, H13, L13_, PM, 1.0, 20, 5)
    finally:
        L.lab_eval_v7 = orig
    l13['escaneo_elige_el_mayor'] = bool(k_sel == 0.2 and r_sel[0] == 9.0 and ex_sel['v7'] == 9.0)
    l13['escaneo_usa_nt_grilla'] = bool(registro['nt'] == 3 and registro['sigma'] >= 0.0)
    l13['escaneo_determinista'] = bool(k_sel == k_sel2)
    l13['escaneo_sin_positivos_da_None'] = bool(k_nada is None)
    out['L13_evaluador_v7'] = {'detalle': l13, 'pasa': all(l13.values())}

    out['todas_pasan'] = all(v['pasa'] for k, v in out.items() if isinstance(v, dict) and 'pasa' in v)
    with open(os.path.join(AQUI, 'lab_pruebas_resultados.json'), 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
