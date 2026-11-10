#!/usr/bin/env python3
"""
H-AUD8-02 — Un cerebro con exactamente un campeón LONG y uno SHORT debe leerse COMPLETO en Fase 4.5 A.
Arma el texto con el `_bloque_mql5` REAL de Fase_4_V12_0.py (unido como en la exportación) y lo lee con el
`leer_cerebro` REAL de Fase_4_5_V_12_0_A.py. Solo lee el repo; escribe en una carpeta temporal.

Uso: python auditoria/prueba_cerebro_un_long_un_short.py [DIR_REPO]     (sale con código 1 si falla)
Demuestra: con un campeón por dirección, 4.5 A lee los dos motores del texto que escribe Fase 4.
No demuestra: que MetaEditor compile el archivo, ni nada sobre datos reales.
Bitácora V0.1 (2026-11-09): creación, junto con el parche H-AUD8-02 de main (luz verde del CRO: "Procede con el parche en main").
"""
import os, sys, tempfile
import numpy as np
REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, REPO)
import Fase_4_V12_0 as F4
import Fase_4_5_V_12_0_A as F45


def candidato(lado):
    g = np.random.default_rng(5 if lado == 'LONG' else 6)
    row = {'Fold': 1, 'Rank': 1, '⚖️ BASE IN': 'FPP_MID_60', '📊 ACUM IN': 'Z20_FPP_MID_60', '⚙️ Arm_IN': '35%', '⚡ Chq_IN': '70%',
           '⚖️ BASE OUT': 'INT_V_FAST_30', '📊 ACUM OUT': 'Z30_INT_V_FAST_30', '⚙️ Arm_OUT': '40%', '⚡ Chq_OUT': '65%'}
    return {'row': row, 'W_R': g.normal(0, 1, 10), 'B_R': float(g.normal()), 'W_S': g.normal(0, 0.3, 10), 'B_S': float(g.normal(0.4, 0.1)),
            'K_opt': 0.31234, 'W_T': g.normal(0, 1, 10), 'B_T': float(g.normal()), 'T_min': 0.55, 'med_v': 0.7, 'mad_v': 0.4, 'atrac_t': 30.0,
            'ClaveRank': 1.0, 'ScoreFlujo': 2.0, 'Med_T_OOS': 0.5}


txt = (f"// ESCALON={F4.ESCALON} | prueba H-AUD8-02\n// FID_VELOCIDAD_UNIFICADA = True\n\n    else if(sym == \"EURUSDm\") {{\n      g_pares[idx].spread_asumido_ia = 0.6000;\n\n"
       + F4._bloque_mql5(candidato('LONG'), 0, 'LONG', 'toro', 'ml_toro', 'superv_toro', '🟢', 0.5)
       + F4._bloque_mql5(candidato('SHORT'), 0, 'SHORT', 'oso', 'ml_oso', 'superv_oso', '🔴', 0.5)
       + "\n      g_pares[idx].cfg.configurado = true;\n    }\n")
with tempfile.TemporaryDirectory() as td:
    ruta = os.path.join(td, 'cerebro.txt')
    with open(ruta, 'w', encoding='utf-8') as fh: fh.write(txt)
    _, motores, errores = F45.leer_cerebro(ruta, tuple(range(1, 11)))
mezcla = [ln[:60] for ln in txt.split('\n') if 'RANK #' in ln and 'g_pares[idx]' in ln]
print(f"motores leídos: {len(motores)} (esperado 2) | errores: {errores} | líneas que mezclan asignación y cabecera: {len(mezcla)}")
ok = len(motores) == 2 and not errores and not mezcla
print('PASA' if ok else 'FALLA'); sys.exit(0 if ok else 1)
