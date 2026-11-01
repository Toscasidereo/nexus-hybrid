# ==============================================================================
# NEXUS LAB-V7 — PRUEBAS DEL LABORATORIO (SINTÉTICAS; ANTES DE USAR DATOS REALES)
# Carpeta: lab_v7/
# ==============================================================================
# BITÁCORA
#   V0.1 (2026-11-01) — Creación. Reglas fijadas antes de correr (se listan en README.md):
#     P1 fusión de ráfagas exacta (caso a mano).
#     P2 DSR: SR0 = 0, curtosis 3, asimetría 0 -> coincide con Phi(SR·sqrt(N-1)/sqrt(1+SR²/2)); monótono en el umbral.
#     P3b calibración sin spread: tasa de C1 >= 0.95 entre 1 % y 12 % (300 réplicas; nominal 5 %).
#     P3 control negativo: mercado sin ventaja, entradas al azar -> tasa de C1 >= 0.95 <= 12 % (esperado ~5 %).
#     P4 control positivo: ventaja sembrada (régimen de deriva conocido) -> C1 >= 0.95 en >= 90 % de las réplicas.
#     P5 deriva: mercado con deriva fuerte y solo largos al azar -> el DSR crudo la detecta como "ventaja" y el alfa
#        opción A no (tasa de C1 >= 0.95 <= 12 %).
#     P6 T_v2 no mecánico: cortar cada trade en un punto uniforme de su vida no sube la mediana de T_v2 más de 0.02.
#     P7 H-V7-06: FET_v2 = 0 anula T_v2 (se documenta el comportamiento; no es un criterio de aprobación).
#   Uso: python lab_v7/v7_pruebas.py   (~1-2 min). Escribe lab_v7/v7_pruebas_resultados.json
# ==============================================================================
import os, sys, json, math
import numpy as np
from scipy.stats import norm

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import v7_metricas as V

PM, SPREAD, SIGMA, DIA = 10000.0, 0.5, 0.8, 1440


def mercado(rng, n, deriva=0.0, p0=1.10):
    ret = rng.normal(0, SIGMA, n) + deriva
    C = p0 + np.cumsum(ret) / PM
    O = np.r_[p0, C[:-1]]
    w = np.abs(rng.normal(0, SIGMA * 0.5, (2, n))) / PM
    return O, np.maximum(O, C) + w[0], np.minimum(O, C) - w[1], C


def operaciones(rng, O, dir_fn, solo_largos=False, rafaga=0.3, spread=SPREAD):
    n = len(O); t = 100; d, e, s, pi = [], [], [], []
    while True:
        h = int(rng.integers(5, 120))
        if t + h >= n - 1:
            break
        sg = 1 if solo_largos else dir_fn(t)
        d.append(sg); e.append(t); s.append(t + h)
        pi.append(sg * (O[t + h] - O[t]) * PM - spread)
        t = t + h + (int(rng.integers(1, 3)) if rng.random() < rafaga else int(rng.integers(20, 200)))
    return np.array(d), np.array(e), np.array(s), np.array(pi)


def replica(seed, deriva=0.0, modo='azar', sembrado=0.0, solo_largos=False, nt=1, spread=SPREAD):
    rng = np.random.default_rng(seed); n = DIA * 40
    if modo == 'regimen':
        reg = np.ones(n); estado = 1.0
        flips = rng.random(n) < 1 / 120
        for i in range(n):
            if flips[i]: estado = -estado
            reg[i] = estado
        O, H, L, C = mercado(rng, n, deriva=sembrado * reg)
        fn = lambda t: int(reg[t])
    else:
        O, H, L, C = mercado(rng, n, deriva=deriva)
        fn = lambda t: int(rng.choice([-1, 1]))
    d, e, s, pi = operaciones(rng, O, fn, solo_largos, spread=spread)
    r = V.score_v7(d, e, s, pi, O, H, L, C, PM, spread, nt=nt, rng=rng, R=10)
    return r, (d, e, s, pi, O, H, L, C)


def main():
    out = {}
    # P1
    d = np.array([1, 1, 1, -1, -1, 1]); e = np.array([0, 12, 40, 50, 63, 90]); s = np.array([10, 38, 45, 60, 80, 99])
    pi = np.array([1., 2., 3., 4., 5., 6.]); f = V.fusionar(d, e, s, pi)
    # trades 0-1: gap 2 -> fundidos; trade 2: gap 2 (40-38) -> fundido; trade 3: dirección distinta; 4: gap 3 -> separado; 5 separado
    out['P1_fusion'] = bool(list(f['m']) == [3, 1, 1, 1] and list(f['E']) == [0, 50, 63, 90] and list(f['S']) == [45, 60, 80, 99]
                            and abs(f['pi'][0] - 6.0) < 1e-12)
    # P2
    rng = np.random.default_rng(3); a = rng.normal(0.05, 1.0, 300); a = (a - a.mean()) / a.std(ddof=1) * 1.0 + 0.1
    from scipy.stats import skew, kurtosis
    # construir muestra con skew~0 y kurt~3 no es exacto; se compara contra la fórmula general implementada a mano
    sr = a.mean() / a.std(ddof=1); g3, g4 = skew(a), kurtosis(a, fisher=False)
    ref = norm.cdf(sr * math.sqrt(len(a) - 1) / math.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr * sr))
    out['P2_dsr_formula'] = bool(abs(V.dsr(a, 0.0) - ref) < 1e-12 and V.dsr(a, 0.0) > V.dsr(a, 0.05) > V.dsr(a, 0.2)
                                 and V.sr0(1.0, 1) == 0.0 and V.sr0(1.0, 100) > V.sr0(1.0, 10) > 0)
    # P3
    neg = [replica(1000 + i)[0] for i in range(150)]
    t3 = float(np.mean([r['C1'] >= 0.95 for r in neg]))
    out['P3_control_negativo'] = {'tasa_C1>=0.95': t3, 'N_mediano': float(np.median([r['N'] for r in neg])),
                                  'score_mediano': float(np.median([r['score_v7'] for r in neg])), 'pasa': bool(t3 <= 0.12)}
    # P3b calibración: sin spread la media verdadera es 0 y la tasa debe rondar el nivel nominal (5 %)
    neg0 = [replica(1500 + i, spread=0.0)[0] for i in range(300)]
    t3b = float(np.mean([r['C1'] >= 0.95 for r in neg0]))
    out['P3b_calibracion_sin_spread'] = {'tasa_C1>=0.95': t3b, 'repeticiones': 300, 'pasa': bool(0.01 <= t3b <= 0.12)}
    # P4
    pos = [replica(2000 + i, modo='regimen', sembrado=0.05)[0] for i in range(40)]
    t4 = float(np.mean([r['C1'] >= 0.95 for r in pos]))
    out['P4_control_positivo'] = {'tasa_C1>=0.95': t4, 'score_mediano': float(np.median([r['score_v7'] for r in pos])),
                                  'pasa': bool(t4 >= 0.90)}
    # P5
    dr = [replica(3000 + i, deriva=0.03, solo_largos=True)[0] for i in range(60)]
    t5 = float(np.mean([r['C1'] >= 0.95 for r in dr])); t5c = float(np.mean([r['c1_crudo'] >= 0.95 for r in dr]))
    out['P5_deriva'] = {'tasa_C1_alfa>=0.95': t5, 'tasa_DSR_crudo>=0.95': t5c, 'pasa': bool(t5 <= 0.12 and t5c >= 0.50)}
    # P6
    difs = []
    for i in range(20):
        r, (d, e, s, pi, O, H, L, C) = replica(4000 + i, modo='regimen', sembrado=0.05)
        base = np.median(V.t_v2(d, e, s, pi, O, H, L, C, PM, SPREAD)['T_v2'])
        g = np.random.default_rng(i)
        s2 = e + np.maximum((g.random(len(e)) * (s - e)).astype(np.int64), 1)
        pi2 = d * (O[s2] - O[e]) * PM - SPREAD
        difs.append(np.median(V.t_v2(d, e, s2, pi2, O, H, L, C, PM, SPREAD)['T_v2']) - base)
    out['P6_T_v2_no_mecanico'] = {'dif_mediana_media': float(np.mean(difs)), 'pasa': bool(np.mean(difs) <= 0.02)}
    # P7
    O = np.full(200, 1.10); H = O + 1e-4; L = O - 1e-4
    O2 = O.copy(); O2[1:] = 1.10 - 0.5e-4                  # nunca en ganancia
    r7 = V.t_v2(np.array([1]), np.array([0]), np.array([30]), np.array([-1.0]), O2, H, L, O2, PM, SPREAD)
    out['P7_H_V7_06'] = {'FET_v2': float(r7['FET_v2'][0]), 'T_v2': float(r7['T_v2'][0]), 'anula': bool(r7['T_v2'][0] == 0.0)}
    out['todas_pasan'] = bool(out['P1_fusion'] and out['P2_dsr_formula'] and out['P3_control_negativo']['pasa'] and out['P3b_calibracion_sin_spread']['pasa']
                              and out['P4_control_positivo']['pasa'] and out['P5_deriva']['pasa']
                              and out['P6_T_v2_no_mecanico']['pasa'])
    with open(os.path.join(AQUI, 'v7_pruebas_resultados.json'), 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
