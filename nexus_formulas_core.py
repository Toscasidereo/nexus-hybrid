# ==============================================================================
# 🧮 nexus_formulas_core.py — MÓDULO SSOT DE FÓRMULAS COMPARTIDAS
# 🛡️ CÓDEX NEXUS-HYBRID V3.0 — REGLA 3 (Paridad Python↔Python Cross-Fase)
# ==============================================================================
# Única fuente de verdad para: Sortino (diseño propio, ver nota abajo), MaxDD,
# Profit Factor, Win Rate, T(t) "Vida Virtuosa" per-trade y score_final.
# Recibe SIEMPRE vectores numpy — nunca DataFrames ni nombres de columna
# (Regla 3). Cada pipeline (Fase 3, Fase 4, Fase 4.5, Fase 5) conserva su
# propio esquema de datos; la ecuación es lo único compartido.
#
# ⚠️ EL EA MQL5 NO IMPORTA ESTE MÓDULO. Recibe pesos congelados vía export
# D.R.Y unidireccional (Axioma 2: "Python dicta, MQL5 acata"). Este módulo
# NO tiene acoplamiento runtime con el EA — sólo afecta a las fases Python
# que lo importan explícitamente. Un cambio aquí jamás desincroniza un
# componente estático (EA ya desplegado) de uno dinámico (Python), porque
# el EA no vuelve a leer esta fuente tras el export.
#
# ⚠️ VERSIONADO FORENSE (Regla 7): cualquier cambio de fórmula aquí invalida
# la comparabilidad retroactiva de Scores/T(t) ya exportados a .txt/CSV.
# Todo artefacto de salida debe estampar FORMULAS_CORE_VERSION en cabecera
# para que una auditoría futura sepa contra qué definición fue calibrado
# cada candidato/EA histórico.
# ==============================================================================
# 📋 BITÁCORA DE CONSOLIDACIÓN V1.1.0 (Auditoría NEXUS — Consolidación T4-T6):
#    - [T5-H_SSOT / T6-H_SSOT CERRADO] La fórmula T(t) per-trade
#      (`fee * fet * (tanh(ivr)+1)/2`) estaba reimplementada de forma
#      IDÉNTICA en Fase_3.py (motores Long/Short) y Fase_4.py (motores
#      duales Long/Short) — cuatro copias fuera de este módulo SSOT,
#      violación literal del Axioma 3. Extraída aquí como
#      `calcular_t_score_trade_numba`, invocable por ambos pipelines vía
#      `njit` inlining (sin penalidad de performance). Ninguna fase debe
#      volver a calcular esta fórmula localmente.
#    - [Ratificado por CRO] `sortino` NO es Sortino textbook (que usa
#      desviación downside de retornos vs. MAR). Es una métrica de riesgo
#      de diseño NEXUS: el denominador downside se calcula sobre
#      `min(profit_trade, MAE_trade)` — el peor escenario entre resultado
#      cerrado y excursión adversa máxima por operación. Se mantiene el
#      nombre `sortino` por decisión de diseño explícita, documentado aquí
#      para que ninguna auditoría futura lo compare inválidamente contra
#      un benchmark de Sortino estándar.
#    - Constantes de normalización de scoring (2.5 / 4.0 / 8.0) promovidas
#      a constantes nombradas a nivel de módulo. Se documenta su rol; su
#      valor numérico NO fue re-derivado ni justificado en esta pasada
#      (no hay fuente de verdad provista para hacerlo bajo Ley
#      Zero-Hallucination) — permanecen como constantes de diseño vigentes,
#      sujetas a ratificación/documentación formal futura por el CRO.
#    - [RESERVA DE AUDITORÍA ABIERTA — NO CERRADA] `memoria_disponible_bytes()`
#      permanece duplicada byte-a-byte respecto de su homónima en
#      Fase_1___2.py. El código NO se auto-exime de esta violación de
#      Axioma 3 (una auto-clasificación previa de "menor, no bloqueante"
#      dentro del propio comentario fue rechazada en auditoría — la
#      severidad de una violación de Códex la determina el Códex, no el
#      autor del código auditado). Pendiente de decisión explícita del CRO:
#      extraer a un módulo `nexus_hpc_utils.py` común, o ratificar la
#      duplicación como aceptada y documentada.
#    - [RESERVA DE AUDITORÍA ABIERTA — NO CERRADA] `autocalibrar_n_jobs_optuna`
#      usa `overhead_por_worker = 150 * 1024 * 1024` (150 MB) sin medición
#      empírica, a diferencia de la autocalibración de Fase 1&2 (que mide
#      huella real vía dry-run antes de fijar concurrencia). El valor NO
#      fue alterado en esta pasada por ausencia de fuente de verdad
#      verificable en el contexto auditado — se deja constancia explícita
#      en lugar de inventar una justificación retroactiva.
# ==============================================================================
import numpy as np
from numba import njit

FORMULAS_CORE_VERSION = "1.1.0"

# ==============================================================================
# 🎚️ CONSTANTES DE DISEÑO — NORMALIZACIÓN DE SCORE_FINAL
# Documentadas por nombre para trazabilidad; valores heredados de la
# implementación original sin re-derivación (ver bitácora V1.1.0 arriba).
# ==============================================================================
UMBRAL_NORM_SORTINO = 2.5   # Divisor de normalización del componente Sortino-diseño en score_base
UMBRAL_NORM_RF      = 4.0   # Divisor de normalización del componente Recovery Factor en score_base
RF_SENTINEL_SIN_DD  = 8.0   # Valor centinela de RF cuando max_dd==0.0 y hay equity positiva (sin drawdown observado)


@njit(cache=True, fastmath=True, boundscheck=False, nogil=True)
def calcular_t_score_trade_numba(mfe_trade, mae_trade, prof_neta_trade, t_gain, t_loss, spread_pips):
    """
    🛡️ [SSOT — Regla 3] Fórmula T(t) "Vida Virtuosa" per-trade — ÚNICA fuente
    de verdad. Antes reimplementada de forma idéntica en Fase_3.py (motores
    Long/Short) y Fase_4.py (motores duales Long/Short); consolidada aquí
    para que ningún pipeline vuelva a divergir silenciosamente.

    T = FEE * FET * [(tanh(IVR) + 1) / 2]

    Donde:
      FEE = Fracción de Eficiencia de Precio, acotada por el spread del
            instrumento — mide cuánto del rango MFE/MAE disponible capturó
            el trade en términos netos.
      FET = Fracción de Tiempo a favor — proporción de velas vivas donde el
            trade estuvo en ganancia flotante neta de spread, respecto al
            total de velas vivas (excluye velas fantasma, Códex M1-B).
      IVR = Velocidad de Recuperación normalizada — pips netos por unidad
            de tiempo adverso, acotada por tanh a rango [0,1] tras el
            reescalado.

    Recibe exclusivamente escalares (el llamador extrae los valores del
    trade cerrado en el punto de cierre) — sin acceso a series temporales,
    sin riesgo de fuga causal por diseño.

    Retorna: t_score (float32), en rango [0, 1].
    """
    fee = mfe_trade / (mfe_trade + abs(mae_trade) + spread_pips + 1e-9)
    fet = t_gain / max(t_gain + t_loss, 1.0)
    mae_piso = max(abs(mae_trade), spread_pips)
    ivr_crudo = (prof_neta_trade - mae_trade) / (max(t_loss, 1.0) * mae_piso + 1e-9)
    return np.float32(fee * fet * ((np.tanh(ivr_crudo) + 1.0) / 2.0))


@njit(cache=True, fastmath=True, boundscheck=False, nogil=True)
def eval_robustez_numba_v6(mfe_lst, mae_lst, prof_lst, tscore_lst, min_trades):
    """
    Juez evaluador único de robustez de trayectoria de trades.

    ⚠️ NOTA DE DISEÑO — 'sortino' (ratificado por CRO, ver bitácora V1.1.0):
    esta métrica NO es Sortino textbook (desviación downside de retornos
    vs. Minimum Acceptable Return). Es una métrica de riesgo de diseño
    NEXUS: el denominador downside se acumula sobre
    `min(profit_trade, MAE_trade)` por operación — el peor escenario entre
    resultado cerrado y excursión adversa máxima. Se conserva el nombre
    'sortino' por decisión de diseño explícita del CRO; no comparar contra
    benchmarks de Sortino estándar sin ajustar por esta diferencia.

    Retorna: (score_final, med_mfe, med_mae, med_prof, efic, ratio_mfe_mae,
              win_rate, pf, max_dd, rf, n, sortino, med_T)
    """
    n = len(prof_lst)
    if n < min_trades:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, float(n), 0.0, 0.0

    sum_prof = 0.0; sum_neg_sq = 0.0; ganadores = 0; sum_ganancias = 0.0
    perdedores_sum = 0.0; cum_equity = 0.0; peak = 0.0; max_dd = 0.0
    for i in range(n):
        p = prof_lst[i]; mae = mae_lst[i]
        equidad_flotante_minima = cum_equity + min(mae, 0.0)
        dd_flotante = peak - equidad_flotante_minima
        if dd_flotante > max_dd: max_dd = dd_flotante
        riesgo_trade = min(p, mae)
        if riesgo_trade < 0: sum_neg_sq += (riesgo_trade * riesgo_trade)
        sum_prof += p
        if p > 0: ganadores += 1; sum_ganancias += p
        else: perdedores_sum += np.abs(p)
        cum_equity += p
        if cum_equity > peak: peak = cum_equity
        dd_cierre = peak - cum_equity
        if dd_cierre > max_dd: max_dd = dd_cierre

    prof_copy = prof_lst.copy(); prof_copy.sort()
    mfe_copy = mfe_lst.copy(); mfe_copy.sort()
    mae_copy = mae_lst.copy(); mae_copy.sort()
    t_copy = tscore_lst.copy(); t_copy.sort()

    if n % 2 == 1:
        med_prof = prof_copy[n // 2]; med_mfe = mfe_copy[n // 2]
        med_mae = mae_copy[n // 2]; med_T = t_copy[n // 2]
    else:
        med_prof = (prof_copy[(n // 2) - 1] + prof_copy[n // 2]) / 2.0
        med_mfe = (mfe_copy[(n // 2) - 1] + mfe_copy[n // 2]) / 2.0
        med_mae = (mae_copy[(n // 2) - 1] + mae_copy[n // 2]) / 2.0
        med_T = (t_copy[(n // 2) - 1] + t_copy[n // 2]) / 2.0

    if med_prof <= 0.05 or sum_ganancias <= perdedores_sum or med_mfe <= 0.0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, float(n), 0.0, 0.0

    avg_prof = sum_prof / n
    win_rate = (ganadores / n) * 100.0
    pf = sum_ganancias / (perdedores_sum + 0.01)
    efic = (med_prof / med_mfe) * 100.0
    ratio_mfe_mae = med_mfe / (np.abs(med_mae) + 0.01)
    downside_std = np.sqrt(sum_neg_sq / max(n, 1))
    if downside_std < 0.01: downside_std = 0.01
    sortino = avg_prof / downside_std  # ver docstring: métrica de diseño NEXUS, no Sortino textbook

    if max_dd > 0.0: rf = cum_equity / max_dd
    elif max_dd == 0.0 and cum_equity > 0.0: rf = RF_SENTINEL_SIN_DD
    else: rf = 0.0

    s_sortino = min(max(sortino, 0.0) / UMBRAL_NORM_SORTINO, 1.0)
    s_rf      = min(max(rf, 0.0) / UMBRAL_NORM_RF, 1.0)
    s_pf      = min(max(pf - 1.0, 0.0) / 1.0, 1.0)
    s_wr      = win_rate / 100.0
    s_T_val   = max(min(med_T, 1.0), 0.0)

    n_factor = min(np.sqrt(n) / np.sqrt(min_trades), 1.0)

    score_base = (s_sortino * 25.0) + (s_rf * 25.0) + (s_T_val * 30.0) + (s_pf * 10.0) + (s_wr * 10.0)
    score_final = score_base * n_factor
    return score_final, med_mfe, med_mae, med_prof, efic, ratio_mfe_mae, win_rate, pf, max_dd, rf, n, sortino, med_T


# 📉 MATRIZ SSOT DE SPREADS (Costo-Fricción por Instrumento)
MATRIZ_SPREADS = {
    'EURUSDm': 0.6, 'USDJPYm': 0.8, 'GBPUSDm': 1.0, 'USDCHFm': 1.2,
    'AUDUSDm': 1.2, 'USDCADm': 1.2, 'NZDUSDm': 1.2, 'EURJPYm': 1.5,
    'GBPJPYm': 2.0, 'EURAUDm': 2.5, 'EURNZDm': 3.0, 'GBPAUDm': 2.5,
    'GBPNZDm': 3.5, 'AUDJPYm': 1.5, 'NZDJPYm': 1.8, 'CADJPYm': 1.5,
    'CHFJPYm': 2.0, 'EURGBPm': 1.0, 'EURCADm': 2.0, 'EURCHFm': 1.2,
    'GBPCHFm': 2.0, 'GBPCADm': 2.5, 'AUDCADm': 1.8, 'AUDCHFm': 1.8,
    'AUDNZDm': 2.0, 'NZDCADm': 2.0, 'NZDCHFm': 2.0, 'CADCHFm': 1.5
}
SPREAD_FALLBACK = 2.0


# ==============================================================================
# 🎛️ AUTOCALIBRACIÓN N_JOBS — HPC UTIL (uso: Fase 3; candidato a Fase 4)
# ==============================================================================
def memoria_disponible_bytes():
    """
    RAM disponible del sistema. psutil con fallback a /proc/meminfo.

    ⚠️ [RESERVA DE AUDITORÍA ABIERTA — Axioma 3] Esta función está
    duplicada byte-a-byte en Fase_1___2.py. NO se auto-clasifica aquí como
    "menor" — esa auto-exención fue explícitamente rechazada en auditoría
    (Turno 4): la severidad de una violación de Códex la determina el
    Códex, no un comentario dentro del propio código auditado. Pendiente
    de decisión formal del CRO: extraer a `nexus_hpc_utils.py` común, o
    ratificar la duplicación como aceptada y documentar por qué.
    """
    try:
        import psutil
        return psutil.virtual_memory().available
    except ImportError:
        try:
            with open('/proc/meminfo') as f:
                for linea in f:
                    if linea.startswith('MemAvailable:'):
                        return int(linea.split()[1]) * 1024
        except Exception:
            pass
        return 8 * (1024 ** 3)


def autocalibrar_n_jobs_optuna(num_metricas, n_velas, total_fold_len, factor_seguridad_ram=0.65, techo_multiplicador_cpu=1.0, n_jobs_piso=1):
    """
    Autocalibración de N_JOBS para el enjambre multiprocessing de Fase 3,
    basada en la huella teórica de las matrices compartidas por fork().

    ⚠️ [RESERVA DE AUDITORÍA ABIERTA] `overhead_por_worker` (150 MB) es una
    constante fija SIN medición empírica, a diferencia de la autocalibración
    de Fase 1&2 (que mide huella real vía un worker de prueba antes de
    fijar concurrencia). No se alteró el valor en esta consolidación por
    ausencia de fuente de verdad verificable — queda como reserva abierta,
    no como hallazgo cerrado.
    """
    import os
    # 1. Memoria compartida una sola vez por el proceso padre (Copy-On-Write real
    #    vía fork() — semántica correcta en ESTE módulo, a diferencia del
    #    comentario ya corregido en Fase_1___2.py que usaba threads).
    # signos_2d, extremo_2d, acum_2d, ciclos_id_2d = 4 matrices de tamaño físico (n_velas, num_metricas)
    # sat_sup_fold, sat_inf_fold = 2 matrices de tamaño (total_fold_len, num_metricas)
    bytes_compartidos = (4 * n_velas + 2 * total_fold_len) * num_metricas * 4

    ram_disponible = memoria_disponible_bytes()

    # 2. Overhead real por worker para el heap de Python, Optuna y copias JIT locales
    overhead_por_worker = 150 * 1024 * 1024

    # 3. RAM efectiva disponible para los workers
    ram_para_workers = (ram_disponible * factor_seguridad_ram) - bytes_compartidos

    if ram_para_workers <= 0:
        n_por_ram = 1
    else:
        n_por_ram = max(1, int(ram_para_workers / overhead_por_worker))

    n_por_cpu = max(1, int(os.cpu_count() * techo_multiplicador_cpu))
    n_jobs = max(n_jobs_piso, min(n_por_ram, n_por_cpu))

    return n_jobs, ram_disponible, overhead_por_worker
