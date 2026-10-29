# ==============================================================================
# 📋 BITÁCORA V5.11 (TRAZABILIDAD DEL PRESUPUESTO DE BÚSQUEDA — REFACTORIZACION FASE_3_PARAMETROS, orden del CRO):
#    - El presupuesto de búsqueda queda agrupado en UN bloque (PRESUPUESTO DE BÚSQUEDA) y se estampa en el CSV
#      (columnas Busq_*) junto al sello del tablero: MIN_OPS_IS_REPORTE, MIN_OPS_OOS_REPORTE, N_SIMULACIONES,
#      STARTUP_TRIALS, TOP_REPORTE, RANGO_ARMADO, RANGO_CHASQUIDO y su hash SHA-1 (Busq_Hash).
#    - El literal 3 del umbral OOS (antes escrito dos veces en el cuerpo) pasa a la constante MIN_OPS_OOS_REPORTE = 3 (mismo valor).
#    - Valores fijados por el CRO en esta versión (cambian el comportamiento; los reportes anteriores NO son comparables):
#        MIN_OPS_IS_REPORTE 50 -> 200 · N_SIMULACIONES 5000 -> 20000 · STARTUP_TRIALS 1000 -> 5000.
#      El resto de valores del bloque queda igual que en V5.10. Sin ningún otro cambio de lógica.
#    - Nota: los trials podados cuentan para STARTUP_TRIALS (sampler TPE) pero NO para N_SIMULACIONES (solo completos).
# ==============================================================================
# ==============================================================================
# 📋 BITÁCORA V5.10 (TABLERO ÚNICO — edición programática, ver parche_fase3_tablero.py y Fase_3.tablero.diff):
#    - N_FOLDS, RATIO_TRAIN_TEST y MEMORIA_FIFO ya NO se definen acá: se importan de nexus_tablero.py (Axioma 3; cierra H-12).
#    - La geometría de folds (IS/OOS) sale de TAB.geometria(N_total): una sola fórmula para Fase 3, Fase 4 y Fase 4.5.
#    - RESERVA CIEGA: TAB.recortar() descarta el tramo final reservado ANTES de construir cualquier matriz. Con RESERVA_FINAL=0
#      (default) el comportamiento es idéntico a V5.9.
#    - El CSV de salida lleva columnas de sello (Tab_*). Nombre del archivo SIN cambios (contrato V5.8 con Fase 4, Axioma 2).
#    - Sin ningún otro cambio de lógica. Cambiar el tablero invalida resultados previos: volver a correr Fase 3.
# ==============================================================================
# ==============================================================================
# 🧠 FASE 3: EL ORÁCULO OHLC DESACOPLADO (MOTORES L/S INDEPENDIENTES)
# ⚡ BATCH MULTI-SÍMBOLO CON TPE BAYESIANO DINÁMICO CONDICIONAL "TREE-BRANCHING"
# ⚙️ V5.9 CONSOLIDADA — EXPANSIVA: (5 FAMILIAS X 3 TFs) OOS D.R.Y
# ==============================================================================
# 📋 BITÁCORA MLOPS INYECTADA V5.7:
#    - [THIRD WAY] Arquitectura Bayesiana Jerárquica OOS (Zero Dead-Prune Error).
#    - Buffer MLL Numba protegido a `(N_Velas // 2) + 5` GIL Open Loop True.
#    - Asimilador Target "Vida Virtuosa T(Life)" y Matrix Spreads SSOT Institucional.
# ==============================================================================
# 📋 BITÁCORA DE CONSOLIDACIÓN V5.7.1 (Auditoría NEXUS V3.0):
#    - eval_robustez_numba_v6 y MATRIZ_SPREADS/SPREAD_FALLBACK MIGRADOS a
#      nexus_formulas_core.py (SSOT compartido, candidato a reutilizar en
#      Fase 4). El EA MQL5 no importa este módulo — acoplamiento unidireccional
#      vía export D.R.Y (Axioma 2), sin riesgo de desincronizar estático/dinámico.
#    - N_JOBS=32 hardcodeado REEMPLAZADO por autocalibrar_n_jobs_optuna()
#      por-fold: mide dimensión REAL de las matrices compartidas por fork()
#      (num_metricas × TOTAL_FOLD_LEN), no tamaño de archivo en disco.
#    - edad_gatillo (filtro de frescura de señal del EA en vivo): CERRADO por
#      decisión de diseño de CRO — es un filtro de EJECUCIÓN en tiempo real,
#      no una propiedad a replicar en backtest vela-a-vela. Sin código.
#    - FAMILIAS_A_EVALUAR (asimetría de autoinclusión de métrica base cruda
#      en familia 'FPP' vs las otras 4): CERRADO — intencionalidad confirmada
#      por CRO. Sin cambio.
#    - [C1-Saturador] Alineación Topológica EA: rolling_median ya no recorta a
#      abs(>5.0), validando signos direccionales (>=0.0 / <=0.0). obtener_extremos
#      separa tracking min/max basado en polaridad final de ciclo.
#    - [M1-B Phantom] Injectado phantom_arr: omite incrementos espurios t_gain/loss.
#    - [A2-A4 Telemetría] Inclusión Simbolo, Versioning SSoT, Reemplazo 0.0->RECHAZADO.
# ==============================================================================
# 📋 BITÁCORA DE CONSOLIDACIÓN V5.8 (Auditoría NEXUS — Turno 5/8):
#    - [T5-H1 CERRADO — BLOQUEANTE MÁXIMO RESUELTO] Bug crítico de presupuesto
#      de simulaciones: `run_opt_L`/`run_opt_S` calculaban
#      `target_completas = N_SIMULACIONES // N_JOBS` y lo cotejaban contra
#      `local_study.trials`, que es el conteo GLOBAL compartido vía SQLite
#      (no un conteo local del worker). Resultado real: el enjambre se
#      detenía al alcanzar `N_SIMULACIONES / N_JOBS` trials completos —
#      NO `N_SIMULACIONES` como declaraba el comentario original ("Garantiza
#      N simulaciones COMPLETAS"). Con N_JOBS≥5, el objetivo real podía caer
#      por debajo de STARTUP_TRIALS=1000, degradando TPE a muestreo
#      aleatorio puro sin ningún síntoma visible. CORREGIDO: el objetivo ya
#      no se divide por N_JOBS — el conteo global se coteja contra el total
#      real deseado. Aplicado idéntico en ambas ramas (Long/Short).
#    - [T5-H_SSOT CERRADO] La fórmula T(t) per-trade, antes reimplementada
#      inline en `simular_motor_long_T`/`simular_motor_short_T` (idéntica a
#      la de Fase_4.py), ahora se importa desde
#      `nexus_formulas_core.calcular_t_score_trade_numba` — cierra la
#      violación de Axioma 3 (S.S.O.T.) confirmada en auditoría cruzada
#      Turno 5 ↔ Turno 6. Numba permite inlining de funciones @njit sin
#      penalidad de performance.
#    - [T5-Doc CERRADO] Documentado explícitamente el mecanismo de
#      auto-exclusión temporal por `shift` en `rolling_median_causal_numba`
#      — verificado sin fuga temporal en auditoría (rastreo completo), pero
#      el mecanismo no es evidente a primera lectura y merece nota
#      explicativa para futuros auditores.
#    - [Estampado FORMULAS_CORE_VERSION] Confirmado: ya se importaba y
#      estampaba correctamente en el CSV de salida (columna 'Core_Ver').
#      Sin cambios necesarios en este punto — el pendiente crítico
#      equivalente detectado en Fase_4.py se resuelve en su propio turno.
#    - [Reserva ABIERTA, no resuelta aquí] `min_trades=3` en la validación
#      OOS permanece sin cambio — pendiente de decisión del CRO sobre si
#      debe elevarse, dado que Fase 4 re-filtra con MIN_OPS_OOS_EXPORT=30
#      antes de exportar al EA. No se asume unilateralmente cuál es el
#      valor correcto.
# ==============================================================================
# 📋 BITÁCORA DE CONSOLIDACIÓN V5.9 (Auditoría Integral NEXUS — Octubre 2026):
#    - [C1 CERRADO — CRÍTICO] Corrección de flags Fastmath en LLVM:
#      `rolling_median_causal_numba` utilizaba `fastmath=True`, habilitando el flag
#      `nnan` ("No NaNs") en LLVM. Esto provocaba que `np.isnan(val)` y
#      `not np.isnan(shifted[i])` se plegaran incorrectamente a False/True,
#      propagando NaN por todo `sat_inf` y bloqueando por completo la apertura de
#      trades Long (0 trades IS -> podados todos los trials Long).
#      CORREGIDO: Se restringe fastmath al conjunto seguro sin 'nnan' ni 'ninf':
#      `fastmath={'reassoc', 'nsz', 'arcp', 'contract', 'afn'}`.
#      Se agrega aserción de regresión en el warm-up JIT.
#    - [A1 CERRADO — ALTO] Guarda de corte por podas masivas (Anti-Hang):
#      En `run_opt_L` y `run_opt_S`, el bucle `while True` evaluaba únicamente
#      `TrialState.COMPLETE >= N_SIMULACIONES`. Ante combinaciones con podas del
#      100% (TrialPruned no incrementa COMPLETE), el enjambre quedaba colgado
#      indefinidamente. CORREGIDO: Se incorpora techo absoluto de simulaciones
#      `max_trials_totales = N_SIMULACIONES * 20` para terminar ordenadamente.
#    - [A2 CERRADO — ALTO] Eliminación de cuello de botella I/O en SQLite:
#      `[t for t in local_study.trials if ...]` deserializaba la base entera cada
#      10 trials por worker (costo cuadrático O(N^2)). CORREGIDO: Se sustituye por
#      `len(local_study.get_trials(deepcopy=False, states=(TrialState.COMPLETE,)))`
#      reduciendo la latencia de serialización de ~460ms a ~3ms por consulta.
#    - [A3 CERRADO — ALTO] Resiliencia de Workers ante contención de SQLite:
#      El bloque try/except envolvía el `while True` completo; un error transitorio
#      de SQLite (e.g. database locked) mataba al worker permanentemente.
#      CORREGIDO: Se implementa try/except por iteración con reintentos y
#      backoff progresivo (hasta 5 reintentos), y validación post-pool alertando
#      si el número de trials completados fue inferior a N_SIMULACIONES.
#    - [M3 CERRADO — MEDIO] Limpieza activa de SQLite en `/dev/shm`:
#      Se añade remoción explícita (`os.remove`) de las bases temporales (.db,
#      -shm, -wal) al finalizar cada estudio (Long y Short), liberando la RAM
#      física de tmpfs y evitando la reducción acumulativa de MemAvailable.
#    - [M5 CERRADO — MEDIO] Unificación de firmas JIT en warm-up:
#      El calentamiento inicial utilizaba float64 (`1.2`, `100.0`) mientras que
#      los workers invocaban con `float32`. CORREGIDO: Se castea a `np.float32`
#      en la compilación seca para asegurar una única firma compilada.
#    - [M1 CERRADO — MEDIO] Blindaje de paridad Phantom y Parquet ausente:
#      Se erradica el fallback silencioso `if 'Phantom' in df` por una excepción
#      estricta `RuntimeError` (Códex M1-B). Se añade log de advertencia en caso
#      de no encontrar el parquet del símbolo antes de saltar.
#    - [B7 CERRADO — HIGIENE] Código muerto y excepciones desnudas:
#      Eliminados imports sin uso (`sys`, `math`, `traceback`), eliminadas
#      variables muertas (`idx_in_L`, `idx_in_S`) y tipado de `except OSError:`.
#    - [REGISTRO DE RESERVAS Y HALLAZGOS METODOLÓGICOS (AUDITORÍA 2026)]:
#      * [M2 - Reserva CRO]: Umbral `min_trades=3` en OOS se conserva; se deja
#        constancia de que neutraliza el castigo `n_factor` (vale 1.0 para n>=3)
#        a la espera de la directiva formal de armonización con Fase 4 (umbral 30).
#      * [M4 - Nota Metodológica WFO]: Se documenta que el OOS de Fold 0 forma
#        parte del Train de Fold 1; no deben promediarse como folds independientes.
#      * [M6 - Consulta CRO]: Velas fantasma modulan `t_gain`/`t_loss`; aperturas
#        y cierres en velas sintéticas permanecen según diseño original.
#      * [B1-B3 - HPC Core]: Notas sobre os.cpu_count() en containers, doble
#        descuento de RAM en autocalibración y redundancia columnar 17x en 2D.
#      * [CONTRATO V5.8 CSV]: El artefacto de salida conserva el nombre
#        `Reporte_Fase3_WFO_V5.8_{SIMBOLO}.csv` para estricta compatibilidad con
#        los importadores de Fase 4 (Axioma 2).
# ==============================================================================

import os
import gc
import time
import multiprocessing as mp
import sqlite3
import logging
import warnings
from optuna.exceptions import ExperimentalWarning
from optuna.trial import TrialState

# 🛠️ SISTEMA DE LOGGING Y LIMPIEZA
logging.basicConfig(filename='errores_fase3_V5_9.log', filemode='a', format='%(asctime)s - [%(levelname)s] - %(message)s', level=logging.INFO)
logging.captureWarnings(True)
logger = logging.getLogger("Oraculo_V5")

warnings.filterwarnings("ignore", category=ExperimentalWarning)
warnings.filterwarnings("ignore", message=".*IProgress not found.*")
warnings.filterwarnings("ignore", category=UserWarning, module="optuna")
warnings.simplefilter('ignore', category=UserWarning)

try:
    from numba.core.errors import NumbaWarning
    warnings.simplefilter('ignore', category=NumbaWarning)
except ImportError:
    pass

import pandas as pd
import numpy as np
from numba import njit, set_num_threads
import optuna
from optuna.samplers import TPESampler
from optuna.storages import RDBStorage

# 🛡️ [FIX T5-H_SSOT] Se importa calcular_t_score_trade_numba — ÚNICA fuente
# de la fórmula T(t) per-trade. Ya no se reimplementa localmente.
from nexus_formulas_core import (
    eval_robustez_numba_v6, MATRIZ_SPREADS, SPREAD_FALLBACK,
    autocalibrar_n_jobs_optuna, FORMULAS_CORE_VERSION,
    calcular_t_score_trade_numba
)

import nexus_tablero as TAB   # [TABLERO] fuente única de folds / IS-OOS / reserva ciega / MEMORIA_FIFO
import hashlib, json

optuna.logging.set_verbosity(optuna.logging.WARNING)
set_num_threads(1)

t_global_start = time.perf_counter()
print("🚀 [Fase 3 HPC V5.9] Iniciando Oráculo Causal Condicional (Expansión WFO Bayes Tree)...")

# ==============================================================================
# 🎛️ TABLERO DE CONTROL MULTI-SÍMBOLO EXTREMO
# ==============================================================================
LISTA_SIMBOLOS =  ['EURUSDm', 'EURJPYm', 'EURCADm', 'EURAUDm', 'EURGBPm', 'EURCHFm', 'EURNZDm',
                  'GBPUSDm', 'GBPAUDm', 'GBPNZDm', 'GBPCHFm', 'GBPCADm', 'GBPJPYm',
                  'AUDJPYm', 'AUDUSDm', 'AUDNZDm', 'AUDCADm', 'AUDCHFm',
                  'NZDJPYm', 'NZDUSDm', 'NZDCHFm', 'NZDCADm',
                  'USDCADm', 'USDJPYm', 'USDCHFm', 'CADCHFm', 'CADJPYm', 'CHFJPYm']

# 🛡️ GATING Y LIMITES HPC BATCH
# ------------------------------------------------------------------------------
# 🔎 PRESUPUESTO DE BÚSQUEDA (V5.11) — se estampa completo en el CSV (columnas Busq_*)
# ------------------------------------------------------------------------------
MIN_OPS_IS_REPORTE = 200       # mínimo de operaciones IS: poda en el objetivo de Optuna y filtro del reporte
MIN_OPS_OOS_REPORTE = 3        # mínimo de operaciones OOS para puntuar (antes literal 3, dos veces)
N_SIMULACIONES = 20000         # trials COMPLETOS objetivo por (fold, dirección); tope de evaluados = N_SIMULACIONES * 20
STARTUP_TRIALS = 5000          # trials aleatorios iniciales del TPE (cuentan completos Y podados)
TOP_REPORTE = 100
RANGO_ARMADO    = (0.10, 0.98, 0.02)
RANGO_CHASQUIDO = (0.04, 0.90, 0.02)
# ------------------------------------------------------------------------------
MEMORIA_FIFO = TAB.MEMORIA_FIFO   # [TABLERO] no editar acá: nexus_tablero.py
N_FOLDS = TAB.N_FOLDS   # [TABLERO] no editar acá: nexus_tablero.py
RATIO_TRAIN_TEST = TAB.RATIO_TRAIN_TEST   # [TABLERO] no editar acá: nexus_tablero.py

def sello_busqueda():
    """Columnas de trazabilidad del presupuesto de búsqueda (todas las filas del CSV llevan el mismo valor)."""
    _p = {'min_ops_is': MIN_OPS_IS_REPORTE, 'min_ops_oos': MIN_OPS_OOS_REPORTE, 'n_sim': N_SIMULACIONES,
          'startup': STARTUP_TRIALS, 'top': TOP_REPORTE, 'r_arm': list(RANGO_ARMADO), 'r_chq': list(RANGO_CHASQUIDO)}
    _h = hashlib.sha1(json.dumps(_p, sort_keys=True).encode('utf-8')).hexdigest()[:16]
    return {'Busq_Min_Ops_IS': MIN_OPS_IS_REPORTE, 'Busq_Min_Ops_OOS': MIN_OPS_OOS_REPORTE, 'Busq_N_Sim': N_SIMULACIONES,
            'Busq_Startup': STARTUP_TRIALS, 'Busq_Top': TOP_REPORTE, 'Busq_Hash': _h}

# 🔥 INYECCIÓN MACRO EXPANDIDA V5.7 (Condiciones Paramétricas 5x3x2 Dimensional)
FAMILIAS_A_EVALUAR = {
    'FPP':       ['FPP', 'FPP_V', 'FPP_A', 'Z_FPP', 'Z_FPP_V', 'Z_FPP_A'],
    'Int_Area':  ['Int_V', 'Int_A', 'Z_Int_Area', 'Z_Int_V', 'Z_Int_A'],
    'Int_V':     ['Int_A', 'Z_Int_V', 'Z_Int_A'],
    'Int2_Area': ['Int2_V', 'Int2_A', 'Z_Int2_Area', 'Z_Int2_V', 'Z_Int2_A'],
    'Int2_V':    ['Int2_A', 'Z_Int2_V', 'Z_Int2_A']
}
TFS_A_EVALUAR = ['Fast', 'Mid', 'Slow']
PERIODOS_Z_A_EVALUAR = [30, 60, 120, 240, 330, 500]
RES_A_EVALUAR = ['30', '60', '120', '240']


# ==============================================================================
# 🚀 CORE MLOps JIT: SILICIO ACELERADO Y T-LIFE INYECCIÓN SCORING P3
# ==============================================================================

# 🛡️ [FIX C1] Fastmath explícito sin 'nnan' ni 'ninf' para prevenir que LLVM
# pliegue `np.isnan` a False. Preserva comportamiento determinista de centinelas NaN.
@njit(cache=True, fastmath={'reassoc', 'nsz', 'arcp', 'contract', 'afn'}, boundscheck=False, nogil=True)
def rolling_median_causal_numba(extremos_ciclo, direction=1, memoria_fifo=100, min_periods=5):
    """
    Mediana rodante causal (FIFO) sobre picos de ciclo, usada como saturador
    de armado/chasquido.

    🛡️ [DOC T5-Doc] MECANISMO DE AUTO-EXCLUSIÓN TEMPORAL — verificado sin
    fuga causal en auditoría (Turno 5, rastreo completo línea por línea):

    1. El bucle principal calcula `result[i]` usando la ventana FIFO
       ACUMULADA HASTA `i` inclusive (mediana de hasta `memoria_fifo` picos
       ya observados).
    2. El bloque `shifted[1:] = result[:-1]` desplaza esa serie UNA posición
       hacia adelante: el saturador efectivo en la posición `i` queda
       construido exclusivamente con picos de ciclos `< i`, EXCLUYENDO
       explícitamente el propio ciclo `i` de su propio umbral.
    3. Esto es lo que garantiza que, al indexar este saturador con
       `ciclos_global[start_train:end_test]` (ver bucle de folds más abajo,
       construido sobre TRAIN+TEST concatenados), un ciclo activo `c` en
       la ventana TRAIN jamás pueda indexar contra información de ciclos
       cerrados en la ventana TEST — el shift lo hace estructuralmente
       imposible, no por casualidad de los límites de slicing.
    4. La continuidad de la memoria FIFO cruzando la frontera train→test es
       INTENCIONAL: replica el comportamiento real del EA en vivo
       (`ObtenerSatCausalOptimizada`), que tampoco resetea su memoria de
       ciclos al cruzar una frontera arbitraria de backtest.
    """
    n = len(extremos_ciclo); result = np.full(n, np.nan, dtype=np.float32); window = np.empty(memoria_fifo, dtype=np.float32)
    count = 0; idx = 0
    for i in range(n):
        val = extremos_ciclo[i]
        if not np.isnan(val): 
            if (direction == 1 and val >= 0.0) or (direction == -1 and val <= 0.0):
                window[idx] = val; idx = (idx + 1) % memoria_fifo; count = min(count + 1, memoria_fifo)
        if count >= min_periods:
            temp = window[:count].copy(); temp.sort()
            if count % 2 == 1: result[i] = temp[count // 2]
            else: result[i] = (temp[(count // 2) - 1] + temp[count // 2]) / 2.0
    shifted = np.full(n, np.nan, dtype=np.float32)
    if n > 0: shifted[1:] = result[:-1]
    last = np.nan
    for i in range(n):
        if not np.isnan(shifted[i]): last = shifted[i]
        if not np.isnan(last): result[i] = last
        else: result[i] = 10.0 if direction == 1 else -10.0
    return result

@njit(cache=True, fastmath=True, boundscheck=False, nogil=True)
def simular_motor_long_T(signos_in, extremo_in, sat_inf_in, acum_in, signos_out, extremo_out, sat_sup_out, acum_out, opens_arr, highs_arr, lows_arr, phantom_arr, pips_mult, n_velas, armado_in, chasquido_in, armado_out, chasquido_out, spread_pips):
    pos_L = 0; p_in_L = 0.0; max_L = 0.0; min_L = 0.0
    t_gain_L = 0.0; t_loss_L = 0.0
    
    max_trades = (n_velas // 2) + 5
    mfe_L = np.empty(max_trades, dtype=np.float32); mae_L = np.empty(max_trades, dtype=np.float32)
    prof_L = np.empty(max_trades, dtype=np.float32); tscore_L = np.empty(max_trades, dtype=np.float32) 
    cnt_L = 0

    for i in range(1, n_velas - 1):
        if pos_L == 1:
            if highs_arr[i] > max_L: max_L = highs_arr[i]
            if lows_arr[i] < min_L: min_L = lows_arr[i]
            
            if phantom_arr[i] == 0.0:
                prof_vela_vivente = ((opens_arr[i] - p_in_L) * pips_mult) - spread_pips
                if prof_vela_vivente > 0.0: t_gain_L += 1.0
                else: t_loss_L += 1.0

            if signos_out[i] > 0 and extremo_out[i] >= (sat_sup_out[i] * armado_out) and acum_out[i] <= (extremo_out[i] * (1.0 - chasquido_out)):
                prof_bruto = (opens_arr[i+1] - p_in_L) * pips_mult
                mfe_actual = (max_L - p_in_L) * pips_mult; mae_actual = (min_L - p_in_L) * pips_mult

                if cnt_L < max_trades:
                    mfe_L[cnt_L] = max(mfe_actual, prof_bruto); mae_L[cnt_L] = min(mae_actual, prof_bruto)
                    prof_neta = prof_bruto - spread_pips; prof_L[cnt_L] = prof_neta
                    # 🛡️ [FIX T5-H_SSOT] T(t) vía función SSOT compartida
                    tscore_L[cnt_L] = calcular_t_score_trade_numba(mfe_L[cnt_L], mae_L[cnt_L], prof_neta, t_gain_L, t_loss_L, spread_pips)
                    cnt_L += 1
                pos_L = 0

        elif pos_L == 0:
            if signos_in[i] < 0 and extremo_in[i] <= (sat_inf_in[i] * armado_in) and acum_in[i] >= (extremo_in[i] * (1.0 - chasquido_in)):
                pos_L = 1; p_in_L = opens_arr[i+1]; max_L = p_in_L; min_L = p_in_L; t_gain_L = 0.0; t_loss_L = 0.0

    if pos_L == 1 and cnt_L < max_trades:
        prof_bruto = (opens_arr[n_velas - 1] - p_in_L) * pips_mult; mfe_actual = (max_L - p_in_L) * pips_mult; mae_actual = (min_L - p_in_L) * pips_mult
        mfe_L[cnt_L] = max(mfe_actual, prof_bruto); mae_L[cnt_L] = min(mae_actual, prof_bruto); prof_neta = prof_bruto - spread_pips; prof_L[cnt_L] = prof_neta
        # 🛡️ [FIX T5-H_SSOT] T(t) vía función SSOT compartida (cierre forzado de fin de ventana)
        tscore_L[cnt_L] = calcular_t_score_trade_numba(mfe_L[cnt_L], mae_L[cnt_L], prof_neta, t_gain_L, t_loss_L, spread_pips)
        cnt_L += 1

    return mfe_L[:cnt_L], mae_L[:cnt_L], prof_L[:cnt_L], tscore_L[:cnt_L]

@njit(cache=True, fastmath=True, boundscheck=False, nogil=True)
def simular_motor_short_T(signos_in, extremo_in, sat_sup_in, acum_in, signos_out, extremo_out, sat_inf_out, acum_out, opens_arr, highs_arr, lows_arr, phantom_arr, pips_mult, n_velas, armado_in, chasquido_in, armado_out, chasquido_out, spread_pips):
    pos_S = 0; p_in_S = 0.0; max_S = 0.0; min_S = 0.0
    t_gain_S = 0.0; t_loss_S = 0.0

    max_trades = (n_velas // 2) + 5
    mfe_S = np.empty(max_trades, dtype=np.float32); mae_S = np.empty(max_trades, dtype=np.float32)
    prof_S = np.empty(max_trades, dtype=np.float32); tscore_S = np.empty(max_trades, dtype=np.float32)
    cnt_S = 0

    for i in range(1, n_velas - 1):
        if pos_S == -1:
            if highs_arr[i] > max_S: max_S = highs_arr[i]
            if lows_arr[i] < min_S: min_S = lows_arr[i]

            if phantom_arr[i] == 0.0:
                prof_vela_vivente = ((p_in_S - opens_arr[i]) * pips_mult) - spread_pips
                if prof_vela_vivente > 0.0: t_gain_S += 1.0
                else: t_loss_S += 1.0

            if signos_out[i] < 0 and extremo_out[i] <= (sat_inf_out[i] * armado_out) and acum_out[i] >= (extremo_out[i] * (1.0 - chasquido_out)):
                prof_bruto = (p_in_S - opens_arr[i+1]) * pips_mult
                mfe_actual = (p_in_S - min_S) * pips_mult; mae_actual = (p_in_S - max_S) * pips_mult

                if cnt_S < max_trades:
                    mfe_S[cnt_S] = max(mfe_actual, prof_bruto); mae_S[cnt_S] = min(mae_actual, prof_bruto)
                    prof_neta = prof_bruto - spread_pips; prof_S[cnt_S] = prof_neta
                    # 🛡️ [FIX T5-H_SSOT] T(t) vía función SSOT compartida
                    tscore_S[cnt_S] = calcular_t_score_trade_numba(mfe_S[cnt_S], mae_S[cnt_S], prof_neta, t_gain_S, t_loss_S, spread_pips)
                    cnt_S += 1
                pos_S = 0

        elif pos_S == 0:
            if signos_in[i] > 0 and extremo_in[i] >= (sat_sup_in[i] * armado_in) and acum_in[i] <= (extremo_in[i] * (1.0 - chasquido_in)):
                pos_S = -1; p_in_S = opens_arr[i+1]; max_S = p_in_S; min_S = p_in_S; t_gain_S = 0.0; t_loss_S = 0.0

    if pos_S == -1 and cnt_S < max_trades:
        prof_bruto = (p_in_S - opens_arr[n_velas - 1]) * pips_mult; mfe_actual = (p_in_S - min_S) * pips_mult; mae_actual = (p_in_S - max_S) * pips_mult
        mfe_S[cnt_S] = max(mfe_actual, prof_bruto); mae_S[cnt_S] = min(mae_actual, prof_bruto); prof_neta = prof_bruto - spread_pips; prof_S[cnt_S] = prof_neta
        # 🛡️ [FIX T5-H_SSOT] T(t) vía función SSOT compartida (cierre forzado de fin de ventana)
        tscore_S[cnt_S] = calcular_t_score_trade_numba(mfe_S[cnt_S], mae_S[cnt_S], prof_neta, t_gain_S, t_loss_S, spread_pips)
        cnt_S += 1

    return mfe_S[:cnt_S], mae_S[:cnt_S], prof_S[:cnt_S], tscore_S[:cnt_S]

@njit(cache=True, fastmath=True, boundscheck=False, nogil=True)
def calcular_extremos_numba(signos_arr, acum_arr, cambios):
    n_velas = len(signos_arr); extremo_arr = np.zeros(n_velas, dtype=np.float32); running_val = 0.0
    for i in range(n_velas):
        if cambios[i] == 1: running_val = acum_arr[i]
        else:
            if signos_arr[i] > 0:
                if acum_arr[i] > running_val: running_val = acum_arr[i]
            else:
                if acum_arr[i] < running_val: running_val = acum_arr[i]
        extremo_arr[i] = running_val
    return extremo_arr

@njit(cache=True, fastmath=True, boundscheck=False, nogil=True)
def calcular_acum_ciclo_numba(metrica_arr, cambios):
    N = len(metrica_arr); out = np.empty(N, dtype=np.float32); running_sum = 0.0
    for i in range(N):
        if cambios[i] == 1: running_sum = metrica_arr[i]
        else: running_sum += metrica_arr[i]
        out[i] = running_sum
    return out

@njit(cache=True, fastmath=True, boundscheck=False, nogil=True)
def obtener_extremos_ciclo_numba(ciclos_id, acum_arr, signos_arr, max_ciclo):
    max_arr = np.full(max_ciclo + 1, np.nan, dtype=np.float32)
    min_arr = np.full(max_ciclo + 1, np.nan, dtype=np.float32)
    temp_max = np.full(max_ciclo + 1, -1e9, dtype=np.float32)
    temp_min = np.full(max_ciclo + 1, 1e9, dtype=np.float32)
    cycle_sign = np.zeros(max_ciclo + 1, dtype=np.int32)
    for i in range(len(ciclos_id)):
        c = ciclos_id[i]; val = acum_arr[i]
        if val > temp_max[c]: temp_max[c] = val
        if val < temp_min[c]: temp_min[c] = val
        cycle_sign[c] = 1 if signos_arr[i] > 0 else -1
    for c in range(max_ciclo + 1):
        if cycle_sign[c] == 1: max_arr[c] = temp_max[c]
        elif cycle_sign[c] == -1: min_arr[c] = temp_min[c]
    return max_arr, min_arr

# 👻 COMPILACIÓN SECA Y TEST DE REGRESIÓN DE FIRMAS (M5 & C1)
_d32 = np.zeros(100, dtype=np.float32)
_dummy_spread = np.float32(1.2)
_dummy_pips_mult = np.float32(100.0)

# 🛡️ [TEST REGRESIÓN C1] Verificar que los centinelas NaN no sean eliminados por LLVM fastmath
_test_extremos = np.array([np.nan, 1.5, np.nan, 2.0, 1.8], dtype=np.float32)
_test_sat = rolling_median_causal_numba(_test_extremos, direction=1, memoria_fifo=10, min_periods=2)
assert not np.isnan(_test_sat[-1]), "🚨 [REGRESIÓN C1] rolling_median_causal_numba propagó NaN por optimización de fastmath!"

_ = simular_motor_long_T(_d32,_d32,_d32,_d32,_d32,_d32,_d32,_d32,_d32,_d32,_d32,_d32,_dummy_pips_mult,100,0.5,0.1,0.5,0.1,_dummy_spread)
_ = simular_motor_short_T(_d32,_d32,_d32,_d32,_d32,_d32,_d32,_d32,_d32,_d32,_d32,_d32,_dummy_pips_mult,100,0.5,0.1,0.5,0.1,_dummy_spread)
_ = eval_robustez_numba_v6(_d32,_d32,_d32,_d32,5)

# Replace_Function crear_sampler
def crear_sampler(seed=None):
    # group=True inyectado (Códex A3): Obligatorio para muestreo multivariado en espacios condicionales
    return TPESampler(multivariate=True, group=True, constant_liar=True, seed=seed, n_startup_trials=STARTUP_TRIALS)

# ==============================================================================
# 🔄 BUCLE DE EXTRAYENTE OPTUNA-TP MULTIDIMENSIONAL H.P.C V5.9
# ==============================================================================
for SIMBOLO_A_EVALUAR in LISTA_SIMBOLOS:
    print("\n" + "█"*100)
    print(f"🪙 INICIANDO ORÁCULO CAUSAL F3 V5.9 EXPANDIDO WFO OOS P/ T_SCORE_INSTA: {SIMBOLO_A_EVALUAR}")
    print("█"*100)
    
    SPREAD_ACTIVO = MATRIZ_SPREADS.get(SIMBOLO_A_EVALUAR, SPREAD_FALLBACK)
    ARCHIVO_ENTRADA = f'nexus_df_salida_3D_{SIMBOLO_A_EVALUAR}_MultiZ.parquet'
    
    # 🛡️ [FIX M1] Detección explícita de archivo con log y alerta
    if not os.path.exists(ARCHIVO_ENTRADA):
        msg_omision = f"⚠️ [OMISIÓN] Archivo no encontrado: {ARCHIVO_ENTRADA}. Se omite símbolo {SIMBOLO_A_EVALUAR}."
        print(f"❌ {msg_omision}")
        logger.warning(msg_omision)
        continue
    
    df_map = pd.read_parquet(ARCHIVO_ENTRADA).reset_index(drop=True)
    N_total = len(df_map); df_map = TAB.recortar(df_map)   # [TABLERO] reserva ciega: Fase 3 no ve el tramo reservado
    
    # 🛡️ [FIX M1] Fallback de Phantom eliminado según Códex M1-B (prohibición de asumir cero fricción)
    if 'Phantom' not in df_map.columns:
        raise RuntimeError(f"🚨 [CÓDEX M1-B FATAL] Falta columna 'Phantom' en {ARCHIVO_ENTRADA}. No se permite fallback a cero fricción.")
    
    PIPS_MULT = np.float32(100.0 if 'JPY' in SIMBOLO_A_EVALUAR else 10000.0)
    opens_arr = df_map['OpenM1'].astype(np.float32).values; highs_arr = df_map['HighM1'].astype(np.float32).values; lows_arr = df_map['LowM1'].astype(np.float32).values
    phantom_arr = df_map['Phantom'].astype(np.float32).values
    N_velas = len(df_map)

    GEOM = TAB.geometria(N_total)   # [TABLERO] geometría única (reemplaza TEST_SIZE=int(N/(RATIO+N_FOLDS)) local)
    assert GEOM['n_ef'] == N_velas, f"[TABLERO] N efectivo {GEOM['n_ef']} != filas cargadas {N_velas}"
    TEST_SIZE = GEOM['test']; TRAIN_SIZE = GEOM['train']
    print(f"   🧭 [TABLERO v{TAB.TABLERO_VERSION} | hash {TAB.hash_params()}] N_total={N_total} N_efectivo={N_velas} "
          f"reserva={'[%d, %d)' % GEOM['reserva'] if GEOM['reserva'] else 'ninguna'} | folds={N_FOLDS} | IS/OOS={TRAIN_SIZE}/{TEST_SIZE}")

    nombres_metricas = []; nombres_bases = []; signos_list = []; acum_list = []; extremo_list = []; ciclos_id_list = []
    lookup_idx = {}  

    # EXTRACCIÓN DINÁMICA MATRICIAL ARAMAYO T-C Array 
    for base_family, acumuladores in FAMILIAS_A_EVALUAR.items():
        for tf in TFS_A_EVALUAR:
            for res in RES_A_EVALUAR:
                col_base = f"{base_family}_{tf}_{res}"
                if col_base not in df_map.columns: continue

                valores_base = df_map[col_base].values; signos_arr = np.sign(valores_base); mask_zero = (signos_arr == 0)
                if mask_zero.any():
                    idx_validos = np.where(~mask_zero)[0]
                    if len(idx_validos) > 0:
                        if mask_zero[0]: signos_arr[0] = 1.0
                        idx_arr = np.arange(len(signos_arr)); idx_arr[mask_zero] = 0; idx_arr = np.maximum.accumulate(idx_arr); signos_arr = signos_arr[idx_arr]
                    else: signos_arr[:] = 1.0

                cambios = (signos_arr[1:] != signos_arr[:-1]).astype(np.int32); cambios = np.concatenate((np.array([0], dtype=np.int32), cambios)); ciclos_id = cambios.cumsum().astype(np.int32)
                columnas_vistas_este_base = set()

                for metrica_raw in acumuladores:
                    es_z = metrica_raw.startswith('Z_')
                    if es_z: metrica_raiz = metrica_raw.replace('Z_', ''); periodos_a_iterar = PERIODOS_Z_A_EVALUAR
                    else: metrica_raiz = metrica_raw; periodos_a_iterar = [0] 

                    for pz in periodos_a_iterar:
                        col_acumular = f"Z{pz}_{metrica_raiz}_{tf}_{res}" if es_z else f"{metrica_raiz}_{tf}_{res}"
                        if col_acumular in columnas_vistas_este_base or col_acumular not in df_map.columns: continue
                        columnas_vistas_este_base.add(col_acumular)

                        metrica_arr = df_map[col_acumular].astype(np.float32).values
                        acum_arr = calcular_acum_ciclo_numba(metrica_arr, cambios); extremo_arr = calcular_extremos_numba(signos_arr, acum_arr, cambios)
                        
                        idx_actual = len(nombres_metricas)  
                        nombres_metricas.append(col_acumular); nombres_bases.append(col_base); signos_list.append(signos_arr.astype(np.float32)); extremo_list.append(extremo_arr); acum_list.append(acum_arr); ciclos_id_list.append(ciclos_id)
                        
                        # INDEXACIÓN C ++ VECTOR ABSOLUTA SSOT
                        lookup_idx[(base_family, tf, res, metrica_raw, pz)] = idx_actual

    num_metricas = len(nombres_metricas)
    signos_2d = np.array(np.column_stack(signos_list), order='F'); extremo_2d = np.array(np.column_stack(extremo_list), order='F')
    acum_2d = np.array(np.column_stack(acum_list), order='F'); ciclos_id_2d = np.array(np.column_stack(ciclos_id_list), order='F', dtype=np.int32)
    
    del signos_list, extremo_list, acum_list, ciclos_id_list, df_map; gc.collect()
    resultados_optuna = []

    for fold in range(N_FOLDS):
        start_train, end_train, start_test, end_test = GEOM['folds'][fold + 1]   # [TABLERO] ventanas únicas
        TRAIN_LEN = end_train - start_train; TEST_LEN = end_test - start_test; TOTAL_FOLD_LEN = end_test - start_train
        
        sat_sup_fold = np.empty((TOTAL_FOLD_LEN, num_metricas), dtype=np.float32, order='F'); sat_inf_fold = np.empty((TOTAL_FOLD_LEN, num_metricas), dtype=np.float32, order='F')

        for m in range(num_metricas):
            acum_global = acum_2d[:, m]; ciclos_global = ciclos_id_2d[:, m]; max_ciclo_total = ciclos_global[end_test - 1]
            signos_global = signos_2d[:, m]
            max_vals_total, min_vals_total = obtener_extremos_ciclo_numba(ciclos_global[:end_test], acum_global[:end_test], signos_global[:end_test], max_ciclo_total)
            sat_sup_series = rolling_median_causal_numba(max_vals_total, direction=1, memoria_fifo=MEMORIA_FIFO, min_periods=5)
            sat_inf_series = rolling_median_causal_numba(min_vals_total, direction=-1, memoria_fifo=MEMORIA_FIFO, min_periods=5)
            cycle_idx_total = np.clip(ciclos_global[start_train:end_test], 0, len(sat_sup_series) - 1)
            sat_sup_fold[:, m] = sat_sup_series[cycle_idx_total]; sat_inf_fold[:, m] = sat_inf_series[cycle_idx_total]

        N_JOBS, ram_disp_bytes, huella_bytes = autocalibrar_n_jobs_optuna(num_metricas, N_velas, TOTAL_FOLD_LEN)
        print(f"   🎛️ [AUTOCALIBRACIÓN N_JOBS | Fold {fold+1}] RAM disp={ram_disp_bytes/(1024**3):.1f}GB | "
              f"Huella fork/worker≈{huella_bytes/(1024**3):.3f}GB | N_JOBS calibrado={N_JOBS} "
              f"(nexus_formulas_core v{FORMULAS_CORE_VERSION})")

        sat_sup_train = sat_sup_fold[:TRAIN_LEN, :]; sat_inf_train = sat_inf_fold[:TRAIN_LEN, :]
        sat_sup_test = sat_sup_fold[TRAIN_LEN:, :];  sat_inf_test = sat_inf_fold[TRAIN_LEN:, :]

        signos_train = signos_2d[start_train:end_train, :]; extremo_train = extremo_2d[start_train:end_train, :]; acum_train = acum_2d[start_train:end_train, :]
        opens_train = opens_arr[start_train:end_train]; highs_train = highs_arr[start_train:end_train]; lows_train = lows_arr[start_train:end_train]; phantom_train = phantom_arr[start_train:end_train]
        
        signos_test = signos_2d[start_test:end_test, :]; extremo_test = extremo_2d[start_test:end_test, :]; acum_test = acum_2d[start_test:end_test, :]
        opens_test = opens_arr[start_test:end_test]; highs_test = highs_arr[start_test:end_test]; lows_test = lows_arr[start_test:end_test]; phantom_test = phantom_arr[start_test:end_test]

        def _resolver_idx(trial, sufijo):
            familia = trial.suggest_categorical(f'familia_{sufijo}', list(FAMILIAS_A_EVALUAR.keys()))
            tf = trial.suggest_categorical(f'tf_{sufijo}', TFS_A_EVALUAR)
            res = trial.suggest_categorical(f'res_{sufijo}', RES_A_EVALUAR)
            metrica_raw = trial.suggest_categorical(f'metrica_{sufijo}_{familia}', FAMILIAS_A_EVALUAR[familia])
            es_z = metrica_raw.startswith('Z_')
            if es_z: pz = trial.suggest_categorical(f'pz_{sufijo}', PERIODOS_Z_A_EVALUAR)
            else: pz = 0
            return lookup_idx.get((familia, tf, res, metrica_raw, pz))

        def _resolver_idx_desde_params(params, sufijo):
            familia = params[f'familia_{sufijo}']
            tf = params[f'tf_{sufijo}']
            res = params[f'res_{sufijo}']
            metrica_raw = params[f'metrica_{sufijo}_{familia}']  
            pz = params.get(f'pz_{sufijo}', 0)
            return lookup_idx.get((familia, tf, res, metrica_raw, pz))

        # ==================== MÁQUINA C++ VECTOR _ COMPRAS (LONG) OPTUNA ====================
        def objective_long(trial):
            idx_in = _resolver_idx(trial, 'in'); idx_out = _resolver_idx(trial, 'out')
            if idx_in is None or idx_out is None or idx_in == idx_out: raise optuna.exceptions.TrialPruned()

            arm_in = trial.suggest_float('armado_in', RANGO_ARMADO[0], RANGO_ARMADO[1], step=RANGO_ARMADO[2]); chq_in = trial.suggest_float('chasquido_in', RANGO_CHASQUIDO[0], RANGO_CHASQUIDO[1], step=RANGO_CHASQUIDO[2])
            arm_out = trial.suggest_float('armado_out', RANGO_ARMADO[0], RANGO_ARMADO[1], step=RANGO_ARMADO[2]); chq_out = trial.suggest_float('chasquido_out', RANGO_CHASQUIDO[0], RANGO_CHASQUIDO[1], step=RANGO_CHASQUIDO[2])

            mfe_L, mae_L, prof_L, tscore_L = simular_motor_long_T(
                signos_train[:, idx_in], extremo_train[:, idx_in], sat_inf_train[:, idx_in], acum_train[:, idx_in],
                signos_train[:, idx_out], extremo_train[:, idx_out], sat_sup_train[:, idx_out], acum_train[:, idx_out],
                opens_train, highs_train, lows_train, phantom_train, PIPS_MULT, TRAIN_LEN, arm_in, chq_in, arm_out, chq_out, np.float32(SPREAD_ACTIVO)
            )

            score, _, _, _, _, _, _, _, _, _, n_l, _, _ = eval_robustez_numba_v6(mfe_L, mae_L, prof_L, tscore_L, MIN_OPS_IS_REPORTE)
            if score <= 0.0 or n_l < MIN_OPS_IS_REPORTE: raise optuna.exceptions.TrialPruned()
            return score

        nombre_db_L = f"/dev/shm/optuna_{SIMBOLO_A_EVALUAR}_L_F{fold}.db"; db_path_L = f"sqlite:///{nombre_db_L}"; study_name_L = f"L_{SIMBOLO_A_EVALUAR}_{fold}"
        for ext in ["", "-shm", "-wal"]:
            try: os.remove(nombre_db_L + ext)
            except OSError: pass

        with sqlite3.connect(nombre_db_L) as conn: conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA synchronous=OFF"); conn.execute("PRAGMA temp_store=MEMORY"); conn.execute("PRAGMA mmap_size=3000000000")
        storage_master_L = RDBStorage(url=db_path_L, engine_kwargs={"connect_args": {"timeout": 60.0}})
        study_L = optuna.create_study(direction='maximize', storage=storage_master_L, study_name=study_name_L, load_if_exists=False, sampler=crear_sampler(seed=42))

        # Replace_Function run_opt_L
        def run_opt_L(worker_id):
            semilla_dinamica = 42 + fold + worker_id 
            try:
                local_storage_L = RDBStorage(url=db_path_L, engine_kwargs={"connect_args": {"timeout": 60.0}})
                local_study = optuna.load_study(study_name=study_name_L, storage=local_storage_L, sampler=crear_sampler(seed=semilla_dinamica))
            except Exception as e:
                logger.error(f"❌ [Worker L {worker_id}] Error al inicializar almacenamiento SQLite: {e}")
                return

            target_completas = max(1, N_SIMULACIONES)
            # 🛡️ [FIX A1] Techo absoluto de seguridad para evitar cuelgues por podas masivas (TrialPruned)
            max_trials_totales = N_SIMULACIONES * 20
            errores_consecutivos = 0
            MAX_ERRORES_CONSECUTIVOS = 5

            while True:
                try:
                    # 🛡️ [FIX A2] Consulta O(1) shallow-copy filtrada por estado: evita deserializar miles de objetos
                    completas = len(local_study.get_trials(deepcopy=False, states=(TrialState.COMPLETE,)))
                    if completas >= target_completas:
                        break

                    # 🛡️ [FIX A1] Verificación periódica del volumen total evaluado
                    totales = len(local_study.get_trials(deepcopy=False))
                    if totales >= max_trials_totales:
                        logger.warning(f"⚠️ [Worker L {worker_id}] Techo máximo de trials ({totales}) alcanzado. Salida ordenada.")
                        break

                    local_study.optimize(objective_long, n_trials=10, gc_after_trial=False)
                    errores_consecutivos = 0
                except Exception as e:
                    # 🛡️ [FIX A3] Aislamiento de fallos transitorios con backoff progresivo
                    errores_consecutivos += 1
                    logger.warning(f"⚠️ [Worker L {worker_id}] Excepción transitoria #{errores_consecutivos}: {e}")
                    if errores_consecutivos >= MAX_ERRORES_CONSECUTIVOS:
                        logger.error(f"❌ [Worker L {worker_id}] Caída permanente tras {errores_consecutivos} fallos consecutivos.")
                        break
                    time.sleep(0.5 * errores_consecutivos)

        ctx = mp.get_context('fork')
        with ctx.Pool(N_JOBS) as pool: pool.map(run_opt_L, range(N_JOBS)) 

        # 🛡️ [FIX A3] Verificación post-pool de completitud
        completas_L = len(study_L.get_trials(deepcopy=False, states=(TrialState.COMPLETE,)))
        if completas_L < N_SIMULACIONES:
            totales_L = len(study_L.get_trials(deepcopy=False))
            msg_warn_L = f"⚠️ [ALERTA LONG | Fold {fold+1}] Enjambre finalizó con {completas_L}/{N_SIMULACIONES} trials completos (Total evaluados: {totales_L})."
            print(f"   {msg_warn_L}")
            logger.warning(msg_warn_L)

        # 🛡️ [FIX A2] get_trials shallow-copy para construcción del ranking final
        completed_trials_L = [t for t in study_L.get_trials(deepcopy=False, states=(TrialState.COMPLETE,)) if t.value is not None and t.value > 0]
        completed_trials_L = sorted(completed_trials_L, key=lambda t: t.value, reverse=True); seen_params_L = set(); rank = 1

        for t in completed_trials_L:
            frozen_p = tuple(sorted((k, round(v, 3) if isinstance(v, float) else v) for k, v in t.params.items()))
            if frozen_p in seen_params_L: continue
            seen_params_L.add(frozen_p)

            b_L = t.params; idx_in = _resolver_idx_desde_params(b_L, 'in'); idx_out = _resolver_idx_desde_params(b_L, 'out')
            if idx_in is None or idx_out is None: continue 

            mfe_L_is, mae_L_is, prof_L_is, tsc_is = simular_motor_long_T(
                signos_train[:, idx_in], extremo_train[:, idx_in], sat_inf_train[:, idx_in], acum_train[:, idx_in],
                signos_train[:, idx_out], extremo_train[:, idx_out], sat_sup_train[:, idx_out], acum_train[:, idx_out],
                opens_train, highs_train, lows_train, phantom_train, PIPS_MULT, TRAIN_LEN, b_L['armado_in'], b_L['chasquido_in'], b_L['armado_out'], b_L['chasquido_out'], np.float32(SPREAD_ACTIVO)
            )

            score_is, _, _, _, _, _, wr_is, pf_is, _, _, n_is, sort_is, mT_is = eval_robustez_numba_v6(mfe_L_is, mae_L_is, prof_L_is, tsc_is, MIN_OPS_IS_REPORTE)
            if n_is < MIN_OPS_IS_REPORTE or score_is <= 0.0: continue

            mfe_L_oos, mae_L_oos, prof_L_oos, tsc_oos = simular_motor_long_T(
                signos_test[:, idx_in], extremo_test[:, idx_in], sat_inf_test[:, idx_in], acum_test[:, idx_in],
                signos_test[:, idx_out], extremo_test[:, idx_out], sat_sup_test[:, idx_out], acum_test[:, idx_out],
                opens_test, highs_test, lows_test, phantom_test, PIPS_MULT, TEST_LEN, b_L['armado_in'], b_L['chasquido_in'], b_L['armado_out'], b_L['chasquido_out'], np.float32(SPREAD_ACTIVO)
            )
            score_oos, _, _, _, _, _, wr_oos, pf_oos, max_dd_oos, rf_oos, n_oos, sort_oos, mT_oos = eval_robustez_numba_v6(mfe_L_oos, mae_L_oos, prof_L_oos, tsc_oos, MIN_OPS_OOS_REPORTE)

            if score_oos == 0.0:
                pf_oos_str = "RECHAZADO"; wr_oos_str = "RECHAZADO"; max_dd_oos_str = "RECHAZADO"; rf_oos_str = "RECHAZADO"; mT_oos_str = "RECHAZADO"
            else:
                pf_oos_str = f"{pf_oos:.2f}"; wr_oos_str = f"{wr_oos:.1f}%"; max_dd_oos_str = f"{round(max_dd_oos, 1)}"; rf_oos_str = f"{rf_oos:.2f}"; mT_oos_str = f"{round(mT_oos, 2)}"

            resultados_optuna.append({
                'Simbolo': SIMBOLO_A_EVALUAR, 'Core_Ver': FORMULAS_CORE_VERSION,
                'Fold': fold + 1, 'Dir': '🟢 LONG', 'Rank': rank,
                '⚖️ BASE IN': nombres_bases[idx_in], '📊 ACUM IN': nombres_metricas[idx_in], '⚙️ Arm_IN': f"{b_L['armado_in']*100:.1f}%", '⚡ Chq_IN': f"{b_L['chasquido_in']*100:.1f}%", '|': '|',
                '⚖️ BASE OUT': nombres_bases[idx_out], '📊 ACUM OUT': nombres_metricas[idx_out], '⚙️ Arm_OUT': f"{b_L['armado_out']*100:.1f}%", '⚡ Chq_OUT': f"{b_L['chasquido_out']*100:.1f}%", '||': '||',
                'Ops_IS': int(n_is), 'PF_IS': f"{pf_is:.2f}", 'WR_IS': f"{wr_is:.1f}%", '🏅 SCORE_T(Life)IS': round(mT_is, 2),  '🏆 SCORE_TPE_IS': round(score_is, 1), '|||': '|||', 
                'Ops_OOS': int(n_oos), 'PF_OOS': pf_oos_str, 'WR_OOS': wr_oos_str, '🏅 SCORE_T(Life)OOS': mT_oos_str, '⚠️ RF_OOS': rf_oos_str, 'MaxDD_OOS': max_dd_oos_str 
            })
            rank += 1
            if rank > TOP_REPORTE: break

        del study_L, storage_master_L; gc.collect()
        # 🛡️ [FIX M3] Liberación explícita de archivos SQLite en /dev/shm para prevenir saturación de tmpfs
        for ext in ["", "-shm", "-wal"]:
            try: os.remove(nombre_db_L + ext)
            except OSError: pass

        # ==================== MÁQUINA C++ VECTOR_ : VENTAS (SHORT) OPTUNA ====================
        def objective_short(trial):
            idx_in = _resolver_idx(trial, 'in'); idx_out = _resolver_idx(trial, 'out')
            if idx_in is None or idx_out is None or idx_in == idx_out: raise optuna.exceptions.TrialPruned()

            arm_in = trial.suggest_float('armado_in', RANGO_ARMADO[0], RANGO_ARMADO[1], step=RANGO_ARMADO[2]); chq_in = trial.suggest_float('chasquido_in', RANGO_CHASQUIDO[0], RANGO_CHASQUIDO[1], step=RANGO_CHASQUIDO[2])
            arm_out = trial.suggest_float('armado_out', RANGO_ARMADO[0], RANGO_ARMADO[1], step=RANGO_ARMADO[2]); chq_out = trial.suggest_float('chasquido_out', RANGO_CHASQUIDO[0], RANGO_CHASQUIDO[1], step=RANGO_CHASQUIDO[2])

            mfe_S, mae_S, prof_S, tsc_S = simular_motor_short_T(
                signos_train[:, idx_in], extremo_train[:, idx_in], sat_sup_train[:, idx_in], acum_train[:, idx_in],
                signos_train[:, idx_out], extremo_train[:, idx_out], sat_inf_train[:, idx_out], acum_train[:, idx_out],
                opens_train, highs_train, lows_train, phantom_train, PIPS_MULT, TRAIN_LEN, arm_in, chq_in, arm_out, chq_out, np.float32(SPREAD_ACTIVO)
            )

            score, _, _, _, _, _, _, _, _, _, n_s, _, med_t = eval_robustez_numba_v6(mfe_S, mae_S, prof_S, tsc_S, MIN_OPS_IS_REPORTE)
            if score <= 0.0 or n_s < MIN_OPS_IS_REPORTE : raise optuna.exceptions.TrialPruned()
            return score

        nombre_db_S = f"/dev/shm/optuna_{SIMBOLO_A_EVALUAR}_S_F{fold}.db"; db_path_S = f"sqlite:///{nombre_db_S}"; study_name_S = f"S_{SIMBOLO_A_EVALUAR}_{fold}"
        for ext in ["", "-shm", "-wal"]:
            try: os.remove(nombre_db_S + ext)
            except OSError: pass

        with sqlite3.connect(nombre_db_S) as conn: conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA synchronous=OFF"); conn.execute("PRAGMA temp_store=MEMORY"); conn.execute("PRAGMA mmap_size=3000000000")
        storage_master_S = RDBStorage(url=db_path_S, engine_kwargs={"connect_args": {"timeout": 60.0}})
        study_S = optuna.create_study(direction='maximize', storage=storage_master_S, study_name=study_name_S, load_if_exists=False, sampler=crear_sampler(seed=43))

        # @Replace_Function run_opt_S
        def run_opt_S(worker_id):
            semilla_dinamica = 43 + fold + worker_id 
            try:
                local_storage_S = RDBStorage(url=db_path_S, engine_kwargs={"connect_args": {"timeout": 60.0}})
                local_study = optuna.load_study(study_name=study_name_S, storage=local_storage_S, sampler=crear_sampler(seed=semilla_dinamica))
            except Exception as e:
                logger.error(f"❌ [Worker S {worker_id}] Error al inicializar almacenamiento SQLite: {e}")
                return

            target_completas = max(1, N_SIMULACIONES)
            # 🛡️ [FIX A1] Techo absoluto de seguridad para evitar cuelgues por podas masivas (TrialPruned)
            max_trials_totales = N_SIMULACIONES * 20
            errores_consecutivos = 0
            MAX_ERRORES_CONSECUTIVOS = 5

            while True:
                try:
                    # 🛡️ [FIX A2] Consulta O(1) shallow-copy filtrada por estado
                    completas = len(local_study.get_trials(deepcopy=False, states=(TrialState.COMPLETE,)))
                    if completas >= target_completas:
                        break

                    # 🛡️ [FIX A1] Verificación periódica del volumen total evaluado
                    totales = len(local_study.get_trials(deepcopy=False))
                    if totales >= max_trials_totales:
                        logger.warning(f"⚠️ [Worker S {worker_id}] Techo máximo de trials ({totales}) alcanzado. Salida ordenada.")
                        break

                    local_study.optimize(objective_short, n_trials=10, gc_after_trial=False)
                    errores_consecutivos = 0
                except Exception as e:
                    # 🛡️ [FIX A3] Aislamiento de fallos transitorios con backoff progresivo
                    errores_consecutivos += 1
                    logger.warning(f"⚠️ [Worker S {worker_id}] Excepción transitoria #{errores_consecutivos}: {e}")
                    if errores_consecutivos >= MAX_ERRORES_CONSECUTIVOS:
                        logger.error(f"❌ [Worker S {worker_id}] Caída permanente tras {errores_consecutivos} fallos consecutivos.")
                        break
                    time.sleep(0.5 * errores_consecutivos)

        ctx = mp.get_context('fork')
        with ctx.Pool(N_JOBS) as pool: pool.map(run_opt_S, range(N_JOBS))

        # 🛡️ [FIX A3] Verificación post-pool de completitud
        completas_S = len(study_S.get_trials(deepcopy=False, states=(TrialState.COMPLETE,)))
        if completas_S < N_SIMULACIONES:
            totales_S = len(study_S.get_trials(deepcopy=False))
            msg_warn_S = f"⚠️ [ALERTA SHORT | Fold {fold+1}] Enjambre finalizó con {completas_S}/{N_SIMULACIONES} trials completos (Total evaluados: {totales_S})."
            print(f"   {msg_warn_S}")
            logger.warning(msg_warn_S)

        # 🛡️ [FIX A2] get_trials shallow-copy para construcción del ranking final
        completed_trials_S = [t for t in study_S.get_trials(deepcopy=False, states=(TrialState.COMPLETE,)) if t.value is not None and t.value > 0]
        completed_trials_S = sorted(completed_trials_S, key=lambda t: t.value, reverse=True); seen_params_S = set(); rank = 1

        for t in completed_trials_S:
            frozen_p = tuple(sorted((k, round(v, 3) if isinstance(v, float) else v) for k, v in t.params.items()))
            if frozen_p in seen_params_S: continue
            seen_params_S.add(frozen_p)

            b_S = t.params; idx_in = _resolver_idx_desde_params(b_S, 'in'); idx_out = _resolver_idx_desde_params(b_S, 'out')
            if idx_in is None or idx_out is None: continue

            mfe_S_is, mae_S_is, prof_S_is, tsc_is_s = simular_motor_short_T(
                signos_train[:, idx_in], extremo_train[:, idx_in], sat_sup_train[:, idx_in], acum_train[:, idx_in],
                signos_train[:, idx_out], extremo_train[:, idx_out], sat_inf_train[:, idx_out], acum_train[:, idx_out],
                opens_train, highs_train, lows_train, phantom_train, PIPS_MULT, TRAIN_LEN, b_S['armado_in'], b_S['chasquido_in'], b_S['armado_out'], b_S['chasquido_out'], np.float32(SPREAD_ACTIVO)
            )

            score_is, _, _, _, _, _, wr_is, pf_is, _, _, n_is, sort_is, mT_S = eval_robustez_numba_v6(mfe_S_is, mae_S_is, prof_S_is, tsc_is_s, MIN_OPS_IS_REPORTE)
            if n_is < MIN_OPS_IS_REPORTE or score_is <= 0.0: continue

            mfe_S_oos, mae_S_oos, prof_S_oos, tsc_oos_s = simular_motor_short_T(
                signos_test[:, idx_in], extremo_test[:, idx_in], sat_sup_test[:, idx_in], acum_test[:, idx_in],
                signos_test[:, idx_out], extremo_test[:, idx_out], sat_inf_test[:, idx_out], acum_test[:, idx_out],
                opens_test, highs_test, lows_test, phantom_test, PIPS_MULT, TEST_LEN, b_S['armado_in'], b_S['chasquido_in'], b_S['armado_out'], b_S['chasquido_out'], np.float32(SPREAD_ACTIVO)
            )
            score_oos, _, _, _, _, _, wr_oos, pf_oos, max_dd_oos, rf_oos, n_oos, sort_oos, mT_oos_S = eval_robustez_numba_v6(mfe_S_oos, mae_S_oos, prof_S_oos, tsc_oos_s, MIN_OPS_OOS_REPORTE)

            if score_oos == 0.0:
                pf_oos_str = "RECHAZADO"; wr_oos_str = "RECHAZADO"; max_dd_oos_str = "RECHAZADO"; rf_oos_str = "RECHAZADO"; mT_oos_str = "RECHAZADO"
            else:
                pf_oos_str = f"{pf_oos:.2f}"; wr_oos_str = f"{wr_oos:.1f}%"; max_dd_oos_str = f"{round(max_dd_oos, 1)}"; rf_oos_str = f"{rf_oos:.2f}"; mT_oos_str = f"{round(mT_oos_S, 2)}"

            resultados_optuna.append({
                'Simbolo': SIMBOLO_A_EVALUAR, 'Core_Ver': FORMULAS_CORE_VERSION,
                'Fold': fold + 1, 'Dir': '🔴 SHORT', 'Rank': rank,
                '⚖️ BASE IN': nombres_bases[idx_in], '📊 ACUM IN': nombres_metricas[idx_in], '⚙️ Arm_IN': f"{b_S['armado_in']*100:.1f}%", '⚡ Chq_IN': f"{b_S['chasquido_in']*100:.1f}%", '|': '|',
                '⚖️ BASE OUT': nombres_bases[idx_out], '📊 ACUM OUT': nombres_metricas[idx_out], '⚙️ Arm_OUT': f"{b_S['armado_out']*100:.1f}%", '⚡ Chq_OUT': f"{b_S['chasquido_out']*100:.1f}%", '||': '||',
                'Ops_IS': int(n_is), 'PF_IS': f"{pf_is:.2f}", 'WR_IS': f"{wr_is:.1f}%", '🏅 SCORE_T(Life)IS': round(mT_S, 2), '🏆 SCORE_TPE_IS': round(score_is, 1), '|||': '|||', 
                'Ops_OOS': int(n_oos), 'PF_OOS': pf_oos_str, 'WR_OOS': wr_oos_str, '🏅 SCORE_T(Life)OOS': mT_oos_S, '⚠️ RF_OOS': rf_oos_str, 'MaxDD_OOS': max_dd_oos_str 
            })
            rank += 1
            if rank > TOP_REPORTE: break

        del study_S, storage_master_S; gc.collect()
        # 🛡️ [FIX M3] Liberación explícita de archivos SQLite en /dev/shm para prevenir saturación de tmpfs
        for ext in ["", "-shm", "-wal"]:
            try: os.remove(nombre_db_S + ext)
            except OSError: pass

    df_reporte = pd.DataFrame(resultados_optuna)
    if not df_reporte.empty:
        df_reporte = df_reporte.sort_values(by=['Fold', 'Dir', 'Rank'], ascending=[True, True, True])
        for _k, _v in TAB.sello(N_total).items(): df_reporte[_k] = _v   # [TABLERO] sello de trazabilidad (Fase 4 lo verifica)
        for _k, _v in sello_busqueda().items(): df_reporte[_k] = _v     # [V5.11] presupuesto de búsqueda (trazabilidad)
        # 🛡️ [CONTRATO DE COMPATIBILIDAD FASE 4] Se conserva la convención de
        # nombre 'Reporte_Fase3_WFO_V5.8_{SIMBOLO}.csv' requerida por el pipeline
        # de exportación de Fase 4 (Axioma 2: estabilidad de interfaces inter-fase).
        nombre_archivo = f"Reporte_Fase3_WFO_V5.8_{SIMBOLO_A_EVALUAR}.csv"
        nombre_temp = nombre_archivo + ".tmp"
        df_reporte.to_csv(nombre_temp, index=False, encoding='utf-8-sig')
        os.replace(nombre_temp, nombre_archivo) # Transacción O(1) a nivel de sistema de archivos
        print(f"✅ V5.9 Árbol Dimensional Extenso Condicional (T-Score_Hpc) P3 completado -> 💾 : {nombre_archivo}")
    else: print(f"⚠️ {SIMBOLO_A_EVALUAR}: Poda completa bajo métrica T-Score Asintótico IA. Densidad IS OOS Insuficiente. ")

    del df_reporte, resultados_optuna; gc.collect()

t_global_end = time.perf_counter()
print(f"\n🎉 OPTUNA TPE + MATRIX HIERARCHICAL BRANCH CONDICIONADO FINAL: {t_global_end - t_global_start:.2f} sec.")