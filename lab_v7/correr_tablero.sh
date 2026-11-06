#!/usr/bin/env bash
# ==============================================================================
# NEXUS LAB-V7 — CORREDOR POR TABLERO. Uso: bash correr_tablero.sh [f3|f4|todo] [ruta/tablero.env]
#   f3   = solo Fase 3 lab (la pesada)   |  f4 = Fase 4 lab + 4.5 A + 4.5 B   |  todo = f3 y luego f4
# Bitácora V0.1 (2026-11-06): creación. Orden del CRO: tablero único de control para la VM.
# Corre desde la carpeta de trabajo que contiene los parquets de Fase 1&2.
# ==============================================================================
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODO="${1:-todo}"; TABLERO="${2:-$RAIZ/lab_v7/tablero_lab.env}"
[ -f "$TABLERO" ] || { echo "No existe el tablero: $TABLERO"; exit 2; }
set -a; . "$TABLERO"; set +a
export PYTHONPATH="$RAIZ:$RAIZ/lab_v7:${PYTHONPATH:-}"
case "$NEXUS_LAB_METRICA" in final|v7) ;; *) echo "METRICA inválida"; exit 2;; esac
case "$NEXUS_LAB_F3" in main|v7) ;; *) echo "F3 inválido"; exit 2;; esac
case "$NEXUS_LAB_CIERRE" in T_terminal|dT_cont|G_pips|V3) ;; *) echo "CIERRE inválido"; exit 2;; esac
case "$NEXUS_LAB_TAMANO" in off|A|B) ;; *) echo "TAMANO inválido"; exit 2;; esac
case "$NEXUS_LAB_NULO" in 0|1) ;; *) echo "NULO inválido"; exit 2;; esac
if [ "$NEXUS_LAB_NULO" = 1 ] && [ "$NEXUS_LAB_TAMANO" != off ]; then echo "NULO=1 con TAMANO≠off no es exportable"; exit 2; fi
echo "TABLERO: metrica=$NEXUS_LAB_METRICA f3=$NEXUS_LAB_F3 cierre=$NEXUS_LAB_CIERRE tamano=$NEXUS_LAB_TAMANO nulo=$NEXUS_LAB_NULO medir=$NEXUS_LAB_F3_MEDIR | $(pwd)"
if [ "$MODO" = f3 ] || [ "$MODO" = todo ]; then python "$RAIZ/lab_v7/Fase_3_lab.py"; fi
if [ "$MODO" = f3 ] || { [ "$MODO" = todo ] && [ "$NEXUS_LAB_F3_MEDIR" != 0 ]; }; then exit 0; fi
if [ "$MODO" = f4 ] || [ "$MODO" = todo ]; then
  python "$RAIZ/lab_v7/Fase_4_lab.py"; python "$RAIZ/lab_v7/Fase_4_5_lab_A.py"; python "$RAIZ/lab_v7/Fase_4_5_lab_B.py"
fi
