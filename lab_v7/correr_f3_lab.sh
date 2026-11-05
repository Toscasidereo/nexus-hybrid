#!/usr/bin/env bash
# ==============================================================================
# NEXUS LAB-V7 — CORREDOR DE FASE 3 LAB (solo Fase 3; es la fase pesada y se corre aparte)
# Carpeta: lab_v7/
# ==============================================================================
# BITÁCORA
#   V0.1 (2026-11-05) — Creación. Orden del CRO: "fase 3 con las métricas refinadas de lab 7 ... un lab7 de fase 3, 4 y 4.5".
# Uso (desde la carpeta de trabajo que ya contiene los parquets de la Fase 1&2):
#     bash /ruta/al/repo/lab_v7/correr_f3_lab.sh [METRICA: final|v7] [MEDIR: 0|N]
# Ejemplos:
#     bash .../correr_f3_lab.sh v7 200     # MEDICIÓN: un símbolo, un fold, 200 trials; imprime ms por trial y estima el tiempo total. No escribe CSV.
#     bash .../correr_f3_lab.sh v7         # corrida completa: escribe Reporte_Fase3_WFO_V5.8_{SIMBOLO}_MV7.csv (no pisa el de main)
#     bash .../correr_f3_lab.sh final      # equivale a Fase_3.py (escribe el CSV con el nombre de siempre)
# Después, Fase 4 lab lee ese CSV con el 5.º parámetro de correr_lab.sh (FASE3=v7).
# ==============================================================================
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$RAIZ:$RAIZ/lab_v7:${PYTHONPATH:-}"
export NEXUS_LAB_METRICA="${1:-final}"
export NEXUS_LAB_F3_MEDIR="${2:-0}"
echo "LAB-V7 FASE 3: métrica=$NEXUS_LAB_METRICA medir=$NEXUS_LAB_F3_MEDIR | carpeta de trabajo: $(pwd)"
python "$RAIZ/lab_v7/Fase_3_lab.py"
