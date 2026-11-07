# ==============================================================================
# NEXUS LAB-V8 — PRUEBAS de Vida v3 extendida (núcleos con V3 vivo). Criterios N1-N5 de ESPECIFICACION_VIDA_V3_EXT.md, fijados antes de implementar.
# Bitácora V0.1 (2026-11-07): creación. Cada prueba dice qué demuestra y qué no (campo 'demuestra' / 'no_demuestra').
# Uso: python lab_v7/v8_pruebas.py  -> v8_pruebas_resultados.json
# ==============================================================================
import os, sys, json
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.abspath(os.path.join(AQUI, '..')), AQUI]
import Fase_4_V12_0 as M
import Fase_4_lab as L
import vida_v3 as VV
from lab_pruebas import entradas, PM

out = {}
rng = np.random.default_rng(5); n = 6000
pars = (0.5, 0.1, 0.5, 0.1, 1.2)
WR = rng.normal(0, 0.05, 10); WT = rng.normal(0, 0.05, 10); WS = rng.normal(0, 0.1, 10)
uno = np.ones(n); SPREAD = pars[-1]
n1, n3, n4, n5, nx = {}, {}, {}, {}, {}
for lado in ('long', 'short'):
    S, ph = entradas(rng, n, lado)
    ext_r = L.extractor_ml_long if lado == 'long' else L.extractor_ml_short
    ext_t = L.extractor_trayectoria_long_v2 if lado == 'long' else L.extractor_trayectoria_short_v2
    sim = L.simular_motor_long_superv_T if lado == 'long' else L.simular_motor_short_superv_T
    sim_ix = L.simular_motor_long_superv_T_ix if lado == 'long' else L.simular_motor_short_superv_T_ix
    # N5: población del extractor de entrada
    a = ext_r(*S, ph, PM, n, *pars); b = ext_r(*S, ph, PM, n, *pars, True)
    n5[f'{lado}_columnas_19'] = bool(b.shape[1] == 19 and np.array_equal(a, b[:, :16]))
    fet, pf, vf = b[:, 16], b[:, 17], b[:, 18]
    n5[f'{lado}_valores_validos'] = bool(np.isfinite(b).all() and np.all((fet >= 0) & (fet <= 1)) and np.all(vf >= 1) and np.all(pf <= b[:, 10] + 1e-3))
    h = 4.5
    v3p, raw, apl = VV.v3p_poblacion(b[:, 10], b[:, 12], b[:, 11], b[:, 13], fet, pf, vf, SPREAD, h, '3.1')
    n5[f'{lado}_v3p_finito'] = bool(np.isfinite(v3p).all() and len(v3p) == VV.N_V3P and v3p[1] >= 1.0 and v3p[2] == 1.0 and np.all(v3p[8:13] > 0))
    Vt = VV.v3_terminal_poblacion(raw, apl, v3p)
    n5[f'{lado}_V3_terminal_en_0_1'] = bool(np.all((Vt >= 0) & (Vt <= 1)))
    # N3: V3 vivo del extractor de trayectoria (ΔT) == Python sobre las fotos guardadas
    targs = (WR, 0.0, 0.5, 0.1, 10.0, 0.0, WT, 0.0, -1.0)
    t0 = ext_t(*S, ph, PM, n, *pars, *targs, uno)               # sin v3p: ΔT con T(t)
    t1 = ext_t(*S, ph, PM, n, *pars, *targs, uno, v3p)          # con v3p: ΔT con V3 vivo
    X0, X1 = t0[0], t1[0]
    n1[f'{lado}_traj_sin_v3p_igual_a_antes'] = bool(len(X0) > 50)
    n3[f'{lado}_cols_0_7_intactas'] = bool(np.array_equal(X0[:, :8], X1[:, :8]))
    prof, mae, mfe, tsc, tid, vela = t1[2], t1[3], t1[4], t1[5], t1[6], t1[7]
    py = VV.vida_v31(prof, mfe, mae, tid, vela, SPREAD, h, ver='3.1', v3p=v3p)
    # T_hat0 por foto: recupero con la columna ΔT de T(t): dT0 = clip(tsc - T_hat0) -> comparo ΔT_V3 con clip(V3_py - T_hat0) donde T_hat0 sale de la fila de entrada
    T_hat0 = tsc - X0[:, 8]                                   # exacto donde ΔT no saturó
    ok_sat = np.abs(X0[:, 8]) < 0.999
    esperado = np.clip(py['V3'] - T_hat0, -1.0, 1.0)
    d = np.abs(esperado[ok_sat] - X1[ok_sat, 8])
    n3[f'{lado}_dT_V3_nucleo_vs_python_max'] = float(d.max()) if d.size else float('nan')
    n3[f'{lado}_dT_V3_nucleo_vs_python_ok'] = bool(d.size > 50 and d.max() < 1e-4)   # tolerancia: fotos float32 en Python
    # N4: causalidad (V3 vivo en foto k no depende de fotos posteriores): recorto cada trade a la mitad y comparo prefijo
    ult, inv = VV._ultimas_fotos(tid)
    tid_ok = np.ones(len(tid), dtype=bool); corte = np.zeros(len(tid), dtype=bool)
    mitad = vela <= (vela[ult][inv] // 2 + 1)
    py2 = VV.vida_v31(prof[mitad], mfe[mitad], mae[mitad], tid[mitad], vela[mitad], SPREAD, h, ver='3.1', v3p=v3p)
    n4[f'{lado}_prefijo_igual'] = bool(np.array_equal(py['V3'][mitad], py2['V3']))
    # simuladores: v3p=None idéntico (ya cubierto por L1 con main); con v3p distinto de None cambia solo si hay ΔT en juego
    sargs = (True, WR, 0.0, 0.5, 0.1, 10.0, 0.0, True, WS, 0.0, 0.3, WT, 0.0, -1.0)
    s0 = sim(*S, ph, PM, n, *pars, *sargs, uno); s1 = sim(*S, ph, PM, n, *pars, *sargs, uno, v3p)
    ix0 = sim_ix(*S, ph, PM, n, *pars, *sargs, uno); ix1 = sim_ix(*S, ph, PM, n, *pars, *sargs, uno, v3p)
    nx[f'{lado}_sim_corre_con_v3p'] = bool(len(s1[0]) > 5)
    nx[f'{lado}_ix_misma_salida_que_sim'] = bool(all(np.array_equal(x, y) for x, y in zip(s1, ix1[:4])))
    nx[f'{lado}_ix_sin_v3p_igual_sim'] = bool(all(np.array_equal(x, y) for x, y in zip(s0, ix0[:4])))
    WSd = np.zeros(10); WSd[8] = 1.0                         # solo pesa ΔT: aborta cuando ΔT < K
    sdargs = (True, WR, 0.0, 0.5, 0.1, 10.0, 0.0, True, WSd, 0.0, 0.0, WT, 0.0, -1.0)
    d0 = sim(*S, ph, PM, n, *pars, *sdargs, uno); d1 = sim(*S, ph, PM, n, *pars, *sdargs, uno, v3p)
    nx[f'{lado}_v3p_cambia_decisiones_cuando_solo_pesa_dT'] = bool(len(d1[0]) > 5 and (len(d1[0]) != len(d0[0]) or not np.array_equal(d0[2], d1[2])))

out['N1_defecto_sin_cambios'] = {'detalle': n1, 'pasa': all(n1.values()), 'demuestra': 'la trayectoria sin v3p produce datos; la identidad bit a bit con main está en lab_pruebas L1', 'no_demuestra': 'nada sobre datos reales'}
out['N3_V3_vivo_nucleo_vs_python'] = {'detalle': n3, 'pasa': all(v for k, v in n3.items() if isinstance(v, bool)), 'demuestra': 'el ΔT con V3 vivo del extractor coincide con vida_v31 sobre las fotos guardadas (tolerancia por float32)', 'no_demuestra': 'paridad con el EA (ver lab_compat_ea)'}
out['N4_causalidad'] = {'detalle': n4, 'pasa': all(n4.values()), 'demuestra': 'V3 vivo no usa fotos posteriores', 'no_demuestra': 'causalidad del resto del pipeline (cubierta por las pruebas de main)'}
out['N5_poblacion_IS'] = {'detalle': n5, 'pasa': all(n5.values()), 'demuestra': 'columnas extra consistentes y constantes finitas', 'no_demuestra': 'ausencia de fuga si se pasan datos OOS (la ventana IS la fija Fase 4)'}
out['NX_simuladores_con_v3p'] = {'detalle': nx, 'pasa': all(nx.values()), 'demuestra': 'los simuladores corren con v3p, _ix == original, y el ΔT con V3 realmente cambia las decisiones', 'no_demuestra': 'que V3 sea mejor que T(t)'}
out['todas_pasan'] = all(v['pasa'] for v in out.values())
json.dump(out, open(os.path.join(AQUI, 'v8_pruebas_resultados.json'), 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
