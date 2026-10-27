#!/usr/bin/env python3
"""
Genera un CSV M1 SINTÉTICO con la misma estructura que espera Fase 0 (columna 'time' + {SIMBOLO}_Open/High/Low/Close
para los 28 pares). Sirve SOLO para probar el encadenamiento (humo). No representa mercado real.

Uso: python generar_datos_sinteticos.py SALIDA.csv.gz [N_VELAS] [SEMILLA]
- Factor común + ruido idiosincrático (evita series degeneradas en el acople cruzado de Fase 1&2).
- ~0,3 % de velas faltantes por símbolo (NaN en O/H/L/C) para ejercitar la lógica de velas fantasma.
- Tiempo contiguo a 1 minuto (Fase 0 exige paso mediano de 1 min y cero duplicados).
"""
import sys, numpy as np, pandas as pd

salida = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 6000; semilla = int(sys.argv[3]) if len(sys.argv) > 3 else 7
SIMBOLOS = ['EURUSDm', 'EURJPYm', 'EURCADm', 'EURAUDm', 'EURGBPm', 'EURCHFm', 'EURNZDm', 'GBPUSDm', 'GBPAUDm', 'GBPNZDm',
            'GBPCHFm', 'GBPCADm', 'GBPJPYm', 'AUDJPYm', 'AUDUSDm', 'AUDNZDm', 'AUDCADm', 'AUDCHFm', 'NZDJPYm', 'NZDUSDm',
            'NZDCHFm', 'NZDCADm', 'USDCADm', 'USDJPYm', 'USDCHFm', 'CADCHFm', 'CADJPYm', 'CHFJPYm']
rng = np.random.default_rng(semilla)
t = pd.date_range('2026-09-01 00:00:00', periods=N, freq='min')
factor = rng.normal(0, 1, N)
cols = {}
for s in SIMBOLOS:
    base = 150.0 if 'JPY' in s else rng.uniform(0.6, 1.6)
    vol = (0.00006 if 'JPY' not in s else 0.006) * rng.uniform(0.7, 1.4)
    ret = vol * (0.6 * factor + 0.8 * rng.normal(0, 1, N))
    close = base * np.exp(np.cumsum(ret) / (1.0 if 'JPY' not in s else 100.0) * (1.0 if 'JPY' not in s else 1.0))
    if 'JPY' in s: close = base + np.cumsum(ret)
    open_ = np.concatenate(([close[0]], close[:-1]))
    mecha = np.abs(rng.normal(0, vol * (1.0 if 'JPY' in s else base) * 0.5, N))
    high = np.maximum(open_, close) + mecha
    low = np.minimum(open_, close) - mecha
    faltan = rng.random(N) < 0.003
    faltan[:5] = False                       # sin NaN iniciales: la retención de Fase 0 debe ser ~100 %
    for nombre, v in (('Open', open_), ('High', high), ('Low', low), ('Close', close)):
        x = v.astype(np.float32).copy(); x[faltan] = np.nan; cols[f"{s}_{nombre}"] = x
df = pd.DataFrame(cols); df.insert(0, 'time', t)
df.to_csv(salida, index=False, compression='gzip')
print(f"{salida}: {N} velas x {len(SIMBOLOS)} pares ({df.shape[1]} columnas) | NaN totales: {int(df.isna().sum().sum())}")
