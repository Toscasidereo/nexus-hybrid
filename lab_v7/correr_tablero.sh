#!/usr/bin/env bash
# ==============================================================================
# NEXUS LAB-V7 — CORREDOR POR TABLERO. Uso: bash correr_tablero.sh [f3|f4|todo] [ruta/tablero.env]
#   f3   = solo Fase 3 lab (la pesada)   |  f4 = Fase 4 lab + 4.5 A + 4.5 B   |  todo = f3 y luego f4
# Bitácora V0.1 (2026-11-06): creación. Orden del CRO: tablero único de control para la VM.
# Bitácora V0.3 (2026-11-10, lab-v8): interruptores NEXUS_LAB_CENSO (0|1) y NEXUS_LAB_VISTA_TOP (informes de Fase 4). Defectos = sin archivos nuevos.
# Bitácora V0.2 (2026-11-07, lab-v8): interruptores NEXUS_LAB_T (T|V3) y NEXUS_LAB_VIDA (3.0|3.1); CIERRE acepta dV3. Defectos = lab-v7.
# Corre desde la carpeta de trabajo que contiene los parquets de Fase 1&2.
# ==============================================================================
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODO="${1:-todo}"; TABLERO="${2:-$RAIZ/lab_v7/tablero_lab.env}"
[ -f "$TABLERO" ] || { echo "No existe el tablero: $TABLERO"; exit 2; }
set -a; . "$TABLERO"; set +a
export PYTHONPATH="$RAIZ:$RAIZ/lab_v7:${PYTHONPATH:-}"
case "$NEXUS_LAB_METRICA" in final|v7|v52) ;; *) echo "METRICA inválida"; exit 2;; esac
if [ "$NEXUS_LAB_METRICA" = v52 ] && [ "$MODO" != f3 ]; then echo "METRICA=v52 solo con modo f3 (Fase 4 lab todavía no lee el CSV _MV52)"; exit 2; fi   # [F3-V52]
case "$NEXUS_LAB_F3" in main|v7) ;; *) echo "F3 inválido"; exit 2;; esac
case "$NEXUS_LAB_CIERRE" in T_terminal|dT_cont|G_pips|V3|dV3) ;; *) echo "CIERRE inválido"; exit 2;; esac
NEXUS_LAB_T="${NEXUS_LAB_T:-T}"; NEXUS_LAB_VIDA="${NEXUS_LAB_VIDA:-3.0}"; export NEXUS_LAB_T NEXUS_LAB_VIDA   # [LAB-V8] defectos = lab-v7
case "$NEXUS_LAB_T" in T|V3) ;; *) echo "T inválido"; exit 2;; esac
case "$NEXUS_LAB_VIDA" in 3.0|3.1) ;; *) echo "VIDA inválida"; exit 2;; esac
case "$NEXUS_LAB_TAMANO" in off|A|B) ;; *) echo "TAMANO inválido"; exit 2;; esac
NEXUS_LAB_CENSO="${NEXUS_LAB_CENSO:-0}"; NEXUS_LAB_VISTA_TOP="${NEXUS_LAB_VISTA_TOP:-50}"; export NEXUS_LAB_CENSO NEXUS_LAB_VISTA_TOP   # [LAB-V8 informes] defecto = sin archivos nuevos
case "$NEXUS_LAB_CENSO" in 0|1) ;; *) echo "CENSO inválido"; exit 2;; esac
case "$NEXUS_LAB_VISTA_TOP" in ''|*[!0-9]*) echo "VISTA_TOP inválido"; exit 2;; esac
case "$NEXUS_LAB_NULO" in 0|1) ;; *) echo "NULO inválido"; exit 2;; esac
if [ -n "${NEXUS_LAB_N_SIM:-}" ] && [ -n "${NEXUS_LAB_STARTUP:-}" ] && [ "$NEXUS_LAB_STARTUP" -ge "$NEXUS_LAB_N_SIM" ]; then echo "STARTUP debe ser menor que N_SIM"; exit 2; fi
python -c "import nexus_tablero as T; print('GEOMETRÍA:', T.N_FOLDS, 'folds | ratio', T.RATIO_TRAIN_TEST, '| reserva', T.RESERVA_FINAL, '| FIFO', T.MEMORIA_FIFO, '| hash', T.hash_params())"
if [ "$NEXUS_LAB_NULO" = 1 ] && [ "$NEXUS_LAB_TAMANO" != off ]; then echo "NULO=1 con TAMANO≠off no es exportable"; exit 2; fi
echo "TABLERO: simbolos=${NEXUS_LAB_SIMBOLOS:-TODOS} n_sim=${NEXUS_LAB_N_SIM:-20000} startup=${NEXUS_LAB_STARTUP:-5000} metrica=$NEXUS_LAB_METRICA f3=$NEXUS_LAB_F3 cierre=$NEXUS_LAB_CIERRE t=$NEXUS_LAB_T vida=$NEXUS_LAB_VIDA tamano=$NEXUS_LAB_TAMANO nulo=$NEXUS_LAB_NULO censo=$NEXUS_LAB_CENSO vista=$NEXUS_LAB_VISTA_TOP medir=$NEXUS_LAB_F3_MEDIR | $(pwd)"
if [ "$MODO" = f3 ] || [ "$MODO" = todo ]; then python "$RAIZ/lab_v7/Fase_3_lab.py"; fi
if [ "$MODO" = f3 ] || { [ "$MODO" = todo ] && [ "$NEXUS_LAB_F3_MEDIR" != 0 ]; }; then exit 0; fi
if [ "$MODO" = f4 ] || [ "$MODO" = todo ]; then
  python "$RAIZ/lab_v7/Fase_4_lab.py"; python "$RAIZ/lab_v7/Fase_4_5_lab_A.py"; python "$RAIZ/lab_v7/Fase_4_5_lab_B.py"
fi
