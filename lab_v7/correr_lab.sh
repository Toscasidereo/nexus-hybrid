#!/usr/bin/env bash
# ==============================================================================
# NEXUS LAB-V7 — CORREDOR DE LA CADENA DEL LAB (Fase 4 lab -> Fase 4.5 A -> Fase 4.5 B)
# Carpeta: lab_v7/
# ==============================================================================
# BITÁCORA
#   V0.1 (2026-11-04) — Creación. Orden del CRO: "Alinea todas las fases de python, para que funcione el lab 7".
#     Las Fases 0, 1&2 y 3 NO cambian: se corren una sola vez, con los scripts de la raíz, y sus salidas las comparten main y el lab.
#     Este script corre las tres fases que sí tienen copia de laboratorio, con los mismos interruptores en las tres (así el tag coincide).
# Uso (desde la carpeta de trabajo que ya contiene las salidas de las Fases 0 a 3: parquets por símbolo y CSV de Fase 3):
#     bash /ruta/al/repo/lab_v7/correr_lab.sh [TAMANO: off|A|B] [CIERRE: T_terminal|dT_cont|G_pips] [NULO: 0|1]
# Ejemplos:
#     bash .../correr_lab.sh                      # copia en defecto (= main), nombres iguales a main
#     bash .../correr_lab.sh B dT_cont            # Ridge de tamaño B + cierre dT_cont
#     bash .../correr_lab.sh off dT_cont 1        # gemelo nulo del cierre (tamaño + nulo no es exportable y se rechaza)
# Corridas pareadas por configuración: (1) defecto, (2) modo a probar, (3) modo a probar con NULO=1 (solo cierre).
# ==============================================================================
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$RAIZ:$RAIZ/lab_v7:${PYTHONPATH:-}"
export NEXUS_LAB_TAMANO="${1:-off}"
export NEXUS_LAB_CIERRE="${2:-T_terminal}"
export NEXUS_LAB_NULO="${3:-0}"
echo "LAB-V7: tamaño=$NEXUS_LAB_TAMANO cierre=$NEXUS_LAB_CIERRE nulo=$NEXUS_LAB_NULO | carpeta de trabajo: $(pwd)"
python "$RAIZ/lab_v7/Fase_4_lab.py"
python "$RAIZ/lab_v7/Fase_4_5_lab_A.py"
python "$RAIZ/lab_v7/Fase_4_5_lab_B.py"
