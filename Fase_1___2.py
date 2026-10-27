# ==============================================================================
# 🧠 FASE 1 & 2 KURAMOTO: ENGINE MULTI-Z CON ACELERACIÓN CINEMÁTICA NUMBA (JIT)
# ⚡ V2.0 — AUTOCALIBRACIÓN DE CONCURRENCIA (SIN HARDCODEAR RECURSOS)
# 🎛️ TIER 1: PYARROW DIRECTO, TRANSPOSICIÓN, SLICING ZERO-OVERHEAD
# 🛡️ CÓDEX M1-B Y M3: INTEGRACIÓN DE MÁSCARAS FANTASMA Y AMPUTACIÓN RIGUROSA
# ==============================================================================
# 📋 BITÁCORA DE CONSOLIDACIÓN V2.1 (Auditoría NEXUS — Turno 3/8):
#    - [T3-H1 CERRADO] Fatal Error explícito (ya NO fallback silencioso a
#      np.zeros) si un símbolo carece de columna '{simbolo}_phantom' en el
#      Parquet de origen. Este era el eslabón empírico que confirmaba el
#      Hallazgo Crítico de Turno 2: sin esta corrección, el pipeline asumía
#      "cero fricción de gaps" para ese símbolo sin ninguna advertencia,
#      violando la Ley Zero-Hallucination.
#    - [T3-H2 CERRADO] Calibración de RAM corregida: se mide el pico real
#      transitorio (dict_res completo + dict_res_recortado coexistiendo en
#      memoria antes del `del`), y se estima el tamaño real de columnas
#      dtype=object (ej. 'Simbolo') vía costo de puntero + contenido en
#      heap, en lugar de sólo `.nbytes` (que para object sólo cuenta el
#      puntero de 8 bytes/elemento y subestima sistemáticamente el pico).
#      Esto corrige una violación del propio Axioma 4 (estimación no
#      miope de RAM) detectada en la autocalibración del enjambre.
#    - [T3-H3 CERRADO] Instrumentado el segundo `ffill().dropna()` sobre el
#      Parquet ya suturado por Fase 0: ahora reporta explícitamente cuántas
#      filas adicionales elimina (si las elimina). Si el conteo es > 0, se
#      emite una alerta de discrepancia S.S.O.T. (el contrato de Fase 0
#      declara el dropna final como CERRADO — si este segundo paso corta
#      filas, ese contrato no se cumple al 100% y debe investigarse antes
#      de considerar Fase 0 blindada). Si es 0, se confirma explícitamente
#      como no-operativo en lugar de dejarlo como código mudo sin veredicto.
#    - [T3-Patrón CERRADO] Detección de pares vía `col.endswith('_Close')`
#      en lugar de `'_Close' in col` — mismo patrón de robustecimiento ya
#      aplicado en Fase 0 (Turno 2) para homólogos OHLC.
#    - [T3-Cosmético CERRADO] Corregida imprecisión terminológica: la
#      memoria compartida entre threads de Python es acceso directo, no
#      "Copy-on-Write" (semántica propia de `fork()`/multiprocessing).
# ==============================================================================
# ==============================================================================
# 📋 BITÁCORA V2.2 (Auditoría NEXUS — Bloque Fase 0→1→2). EL MOTOR NUMÉRICO NO CAMBIÓ:
#    `_procesar_core_numba`, `calc_robust_zscore_numba` y la matemática FPP/Kuramoto son
#    idénticos a V2.1 (las columnas de salida son idénticas bit a bit; sólo se agregan
#    metadatos en el Parquet). Cambios exclusivamente de contrato, validación y cierre:
#    - [N7-A2 CERRADO] Reloj: ya no se "adivina" la columna de fecha (con índice llamado
#      distinto de 'time' se convertía la 1ª columna de PRECIOS en fecha, sin error).
#      Ahora: 'time' como columna si existe; si no, el índice debe ser DatetimeIndex
#      (se renombra a 'time'); si no, FATAL. Además: sin NaT, orden cronológico,
#      sin duplicados y cadencia M1 (paso mediano = 1 min).
#    - [N7-A1 CERRADO] Escritura atómica (.tmp + os.replace). Las salidas previas de los
#      símbolos a procesar se borran al inicio (nunca coexisten versiones mezcladas).
#      Si algún símbolo falla, el proceso termina con RuntimeError (ya NO imprime
#      "COMPLETADO" con fallos). Se exige len(índice) > START_IDX.
#    - [N7-M1 ACLARADO — NO se elimina `div_cuad`] Como Σ|fpp_temp| = 1/N, siempre
#      |S| <= 1/N, luego max(S², 1/N²) ≡ 1/N²: la parte ADAPTATIVA nunca se activa. PERO el
#      factor constante N² que resulta SÍ es funcional: fija la escala a la que opera el
#      acople no lineal tanh(k - fpp_original). Quitarlo cambia las señales (verificado:
#      corr. del Z de FPP_V = 0.41, signo distinto en ~37% de las filas). Se conserva el
#      cálculo idéntico y se agrega un diagnóstico que avisa si algún día deja de ser constante.
#      (Una versión previa de esta auditoría lo calificó erróneamente de "sin efecto".)
#    - [N7-M3 CERRADO] Sello 'nexus_fase12' en los metadatos de cada salida (versión,
#      configuración, START_IDX, símbolos y sello heredado de Fase 0). Si el Parquet de
#      origen trae sello 'nexus_fase0' se verifica su conteo de filas; si no, se avisa.
#    - [Validaciones de datos] OHLC presentes por símbolo, Close finito > 0, Phantom ∈ {0,1}.
#    - [N7-B1] Warm-up con array de SOLO LECTURA (misma firma que las filas de GLOBAL_FPP).
#    - DECISIÓN PENDIENTE (no cambiada): N7-M2 — FPP_{TF}_{res} es idéntico entre las 4
#      resoluciones (63 columnas con sus Z redundantes). Se conservan por compatibilidad
#      de nombres con Fase 3/4/EA.
# ==============================================================================
import sys
import os
import time
import json
import math
import warnings
import gc
import threading
import concurrent.futures

try:
    from numba.core.errors import NumbaWarning
except ImportError:
    pass
warnings.simplefilter('ignore', category=UserWarning)
if 'NumbaWarning' in locals(): warnings.simplefilter('ignore', category=NumbaWarning)

import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from numba import njit, set_num_threads

# 🛡️ FORZAR 1 HILO POR WORKER: Evita que Numba canibalice los vCPUs
set_num_threads(1)

# ==============================================================================
# 🎛️ TABLERO DE CONTROL MASTER
# ==============================================================================
RUTA_PARQUET_ORIGEN = 'nexus_matrix_ohlc_m1_24m.parquet'
DIRECTORIO_SALIDA = '.'

# ⏱️ MARCOS TEMPORALES
TFS_CONFIG = {
    'Fast': 60,
    'Mid' : 120,
    'Slow': 360
}

# 📏 RESOLUCIONES CINEMÁTICAS (Tamaño ventanas OLS para V y A)
RESOLUCIONES_FPP = [30, 60, 120, 240]

# 🌊 VENTANAS Z-SCORE ROBUSTO (Periodos de cálculo Mediana/MAD)
VENTANAS_Z = [30, 60, 120, 240, 330, 500]

# 🎚️ AUTOCALIBRACIÓN — no hay MAX_VCPUS fijo. Solo parámetros de seguridad:
FACTOR_SEGURIDAD_RAM = 0.65
TECHO_MULTIPLICADOR_CPU = 2.0
TAM_PROBE_DISCO_MB = 300

INCLUIR_COLUMNA_SIMBOLO = True
INCLUIR_COLUMNA_TIEMPO = True

FASE12_VERSION = "V2.2"
SIGMA_ACOPLE = 0.25                # Acople Kuramoto (antes literal local en el bucle; mismo valor)
MAX_TIMESTAMPS_DUPLICADOS = 0
# Primer índice donde CERO valores falsos influyen en la ecuación de convolución (Códex M3)
START_IDX = max(TFS_CONFIG.values()) + max(RESOLUCIONES_FPP) + max(VENTANAS_Z) - 2
META_SALIDA = b'{}'                # sello 'nexus_fase12'; se completa en el orquestador
# ==============================================================================

# ==============================================================================
# 🚀 CORE CINEMÁTICO EN COMPILACIÓN NATIVA (ÁLGEBRA INTACTA)
# ==============================================================================
@njit(cache=True, nogil=True)
def _procesar_core_numba(fpp_arr, n):
    L = len(fpp_arr)

    fpp_crudo = np.full(L, np.nan, dtype=np.float32)
    v_fpp = np.full(L, np.nan, dtype=np.float32)
    a_fpp = np.full(L, np.nan, dtype=np.float32)
    int1_val = np.full(L, np.nan, dtype=np.float32)
    v_int1 = np.full(L, np.nan, dtype=np.float32)
    a_int1 = np.full(L, np.nan, dtype=np.float32)
    int2_val = np.full(L, np.nan, dtype=np.float32)
    v_int2 = np.full(L, np.nan, dtype=np.float32)
    a_int2 = np.full(L, np.nan, dtype=np.float32)

    X = np.zeros(n, dtype=np.float32)
    for i in range(n): X[i] = n - 1 - i
    X2 = X * X; X3 = X2 * X; X4 = X3 * X

    sx = 0.0; sx2 = 0.0; sx3 = 0.0; sx4 = 0.0
    for i in range(n):
        sx += X[i]; sx2 += X2[i]; sx3 += X3[i]; sx4 += X4[i]

    D = sx4 * (sx2 * n - sx * sx) - sx3 * (sx3 * n - sx * sx2) + sx2 * (sx3 * sx - sx2 * sx2)
    if D == 0.0: D = 1e-9

    Y = np.zeros(n, dtype=np.float32)
    Int1 = np.zeros(n, dtype=np.float32)
    Int2 = np.zeros(n, dtype=np.float32)

    for t in range(n - 1, L):
        for i in range(n):
            Y[i] = fpp_arr[t - i]

        Int1[n - 1] = Y[n - 1]
        for i in range(n - 2, -1, -1):
            Int1[i] = Int1[i + 1] + Y[i]

        Int2[n - 1] = Int1[n - 1]
        for i in range(n - 2, -1, -1):
            Int2[i] = Int2[i + 1] + Int1[i]

        sy, sxy, sx2y = 0.0, 0.0, 0.0
        for i in range(n):
            sy += Y[i]; sxy += Y[i] * X[i]; sx2y += Y[i] * X2[i]
        Da = sx2y * (sx2 * n - sx * sx) - sx3 * (sxy * n - sy * sx) + sx2 * (sxy * sx - sy * sx2)
        Db = sx4 * (sxy * n - sy * sx) - sx2y * (sx3 * n - sx * sx2) + sx2 * (sx3 * sy - sxy * sx2)
        a_f = Da / D
        v_f = 2.0 * a_f * (n - 1) + (Db / D)

        sy_i1, sxy_i1, sx2y_i1 = 0.0, 0.0, 0.0
        for i in range(n):
            sy_i1 += Int1[i]; sxy_i1 += Int1[i] * X[i]; sx2y_i1 += Int1[i] * X2[i]
        Da_i1 = sx2y_i1 * (sx2 * n - sx * sx) - sx3 * (sxy_i1 * n - sy_i1 * sx) + sx2 * (sxy_i1 * sx - sy_i1 * sx2)
        Db_i1 = sx4 * (sxy_i1 * n - sy_i1 * sx) - sx2y_i1 * (sx3 * n - sx * sx2) + sx2 * (sx3 * sy_i1 - sxy_i1 * sx2)
        a_f1 = Da_i1 / D
        v_f1 = 2.0 * a_f1 * (n - 1) + (Db_i1 / D)

        sy_i2, sxy_i2, sx2y_i2 = 0.0, 0.0, 0.0
        for i in range(n):
            sy_i2 += Int2[i]; sxy_i2 += Int2[i] * X[i]; sx2y_i2 += Int2[i] * X2[i]
        Da_i2 = sx2y_i2 * (sx2 * n - sx * sx) - sx3 * (sxy_i2 * n - sy_i2 * sx) + sx2 * (sxy_i2 * sx - sy_i2 * sx2)
        Db_i2 = sx4 * (sxy_i2 * n - sy_i2 * sx) - sx2y_i2 * (sx3 * n - sx * sx2) + sx2 * (sx3 * sy_i2 - sxy_i2 * sx2)
        a_f2 = Da_i2 / D
        v_f2 = 2.0 * a_f2 * (n - 1) + (Db_i2 / D)

        fpp_crudo[t] = Y[0];     v_fpp[t] = v_f;   a_fpp[t] = a_f
        int1_val[t]  = Int1[0];  v_int1[t] = v_f1; a_int1[t] = a_f1
        int2_val[t]  = Int2[0];  v_int2[t] = v_f2; a_int2[t] = a_f2

    return (fpp_crudo, v_fpp, a_fpp, int1_val, v_int1, a_int1, int2_val, v_int2, a_int2)


@njit(cache=True, nogil=True)
def calc_robust_zscore_numba(arr, pz):
    L = len(arr)
    out = np.full(L, np.nan, dtype=np.float32)

    first_valid = -1
    for i in range(L):
        if not np.isnan(arr[i]):
            first_valid = i
            break

    if first_valid == -1 or L - first_valid < pz:
        return out

    start_idx = first_valid + pz - 1

    window_work = np.zeros(pz, dtype=np.float32)
    devs_work = np.zeros(pz, dtype=np.float32)

    for t in range(start_idx, L):

        for i in range(pz):
            window_work[i] = arr[t - pz + 1 + i]

        window_work.sort()

        if pz % 2 != 0:
            med = window_work[pz // 2]
        else:
            med = (window_work[(pz // 2) - 1] + window_work[pz // 2]) / 2.0

        for i in range(pz):
            devs_work[i] = abs(arr[t - pz + 1 + i] - med)

        devs_work.sort()
        if pz % 2 != 0:
            mad = devs_work[pz // 2]
        else:
            mad = (devs_work[(pz // 2) - 1] + devs_work[pz // 2]) / 2.0

        val_actual = arr[t]

        if mad > 1e-9:
            out[t] = np.float32((val_actual - med) / mad)
        else:
            out[t] = 0.0

    return out

# ==============================================================================
# 🌐 VARIABLES GLOBALES
# 🛡️ [FIX T3-Cosmético] La memoria se comparte entre THREADS por acceso
# directo (no hay copia de por medio). "Copy-on-Write" es semántica propia
# de fork()/multiprocessing, no aplica aquí — el término anterior inducía
# a un futuro auditor a asumir semántica de proceso donde hay semántica
# de hilo. Numba libera el GIL (`nogil=True`) durante el cómputo pesado,
# lo cual es lo que efectivamente habilita el paralelismo real.
# ==============================================================================
GLOBAL_INDEX = None
GLOBAL_FPP = {}
GLOBAL_OHLC = {}
GLOBAL_PHANTOM = {}   # Códex M1-B: Retención Forense

# ==============================================================================
# 🔧 UTILIDADES DE AUTOCALIBRACIÓN
# ==============================================================================
def memoria_disponible_bytes():
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

def calibrar_throughput_disco(directorio, tam_mb=300):
    ruta_test = os.path.join(directorio, '_probe_io_nexus.tmp')
    chunk = os.urandom(1024 * 1024)
    t0 = time.time()
    try:
        with open(ruta_test, 'wb') as f:
            for _ in range(tam_mb):
                f.write(chunk)
            f.flush()
            os.fsync(f.fileno())
        dt = max(time.time() - t0, 1e-6)
        return tam_mb / dt
    finally:
        try: os.remove(ruta_test)
        except Exception: pass

def escrituras_concurrentes_desde_throughput(mbps):
    if mbps > 2500: return 6
    if mbps > 1200: return 4
    if mbps > 500:  return 2
    return 1


def _tamano_real_bytes(arr):
    """
    🛡️ [FIX T3-H2] Estimación de tamaño real en memoria de un array numpy.
    Para dtypes numéricos estándar, `.nbytes` es exacto. Para `dtype=object`
    (ej. la columna 'Simbolo', que contiene strings de Python), `.nbytes`
    SÓLO cuenta el tamaño del puntero (8 bytes/elemento en CPython de
    64 bits) — NO el contenido real del string en el heap. Esto subestima
    sistemáticamente la huella real, violando el Axioma 4 (estimación de
    RAM no miope). Aquí se suma el costo del objeto real vía
    `sys.getsizeof` sobre cada elemento.
    """
    if arr.dtype == object:
        return arr.nbytes + sum(sys.getsizeof(x) for x in arr)
    return arr.nbytes


def _huella_ram_pico(dict_res, dict_res_recortado):
    """
    🛡️ [FIX T3-H2] Estima el PICO real de RAM del worker, no sólo el
    tamaño de `dict_res`. Antes de que ocurra el `del dict_res, ...`,
    `dict_res` (longitud completa) y `dict_res_recortado` (post-slice)
    coexisten simultáneamente en memoria — el pico transitorio real de un
    worker concurrente incluye ambos, no sólo el primero.
    """
    bytes_dict_res = sum(_tamano_real_bytes(a) for a in dict_res.values())
    bytes_dict_res_recortado = sum(_tamano_real_bytes(a) for a in dict_res_recortado.values())
    return bytes_dict_res + bytes_dict_res_recortado

# ==============================================================================
# 🏭 WORKER AUTÓNOMO
# ==============================================================================
SEMAFORO_ESCRITURA = None

def procesar_simbolo_worker(args):
    idx_target, simbolo = args
    t_inicio = time.time()
    ruta_tmp = None

    try:
        dict_res = {}

        for tf_name in TFS_CONFIG.keys():
            fpp_arr_simbolo = GLOBAL_FPP[tf_name][idx_target, :]

            for resolucion in RESOLUCIONES_FPP:
                (f_crudo, v_f, a_f, i1_val, v_i1, a_i1, i2_val, v_i2, a_i2) = _procesar_core_numba(fpp_arr_simbolo, resolucion)

                prefijo = f"_{tf_name}_{resolucion}"

                temp_dict = {
                    f'FPP{prefijo}': f_crudo, f'FPP_V{prefijo}': v_f, f'FPP_A{prefijo}': a_f,
                    f'Int_Area{prefijo}': i1_val, f'Int_V{prefijo}': v_i1, f'Int_A{prefijo}': a_i1,
                    f'Int2_Area{prefijo}': i2_val, f'Int2_V{prefijo}': v_i2, f'Int2_A{prefijo}': a_i2
                }

                for col_name, arr in temp_dict.items():
                    dict_res[col_name] = arr
                    for pz in VENTANAS_Z:
                        out_col_name = f'Z{pz}_{col_name}'
                        dict_res[out_col_name] = calc_robust_zscore_numba(arr, pz)

        if INCLUIR_COLUMNA_SIMBOLO:
            dict_res['Simbolo'] = np.full(len(GLOBAL_INDEX), simbolo, dtype=object)

        dict_res['OpenM1']   = GLOBAL_OHLC[f'{simbolo}_Open']
        dict_res['HighM1']   = GLOBAL_OHLC[f'{simbolo}_High']
        dict_res['LowM1']    = GLOBAL_OHLC[f'{simbolo}_Low']
        dict_res['CierreM1'] = GLOBAL_OHLC[f'{simbolo}_Close']
        dict_res['Phantom']  = GLOBAL_PHANTOM[simbolo] # Códex M1-B: Marcador Forense

        # 🔧 SLICING POR start_idx CORREGIDO (Códex M3)
        # Primer índice donde CERO valores falsos influyen en la ecuación de convolución
        start_idx = START_IDX
        dict_res_recortado = {k: v[start_idx:] for k, v in dict_res.items()}

        if INCLUIR_COLUMNA_TIEMPO:
            dict_res_recortado['Time'] = GLOBAL_INDEX[start_idx:].values

        # 🛡️ [FIX T3-H2] Huella de pico real (dict_res + dict_res_recortado
        # coexistiendo), calculada ANTES del `del` — refleja el momento de
        # mayor presión de memoria real del worker, con sizing correcto
        # también para la columna dtype=object.
        bytes_pico_real_estimado = _huella_ram_pico(dict_res, dict_res_recortado)

        tabla = pa.table(dict_res_recortado).replace_schema_metadata({b'nexus_fase12': META_SALIDA})

        ruta_salida = os.path.join(DIRECTORIO_SALIDA, f'nexus_df_salida_3D_{simbolo}_MultiZ.parquet')
        ruta_tmp = ruta_salida + '.tmp'   # [N7-A1] escritura atómica

        with SEMAFORO_ESCRITURA:
            pq.write_table(tabla, ruta_tmp, compression='zstd', compression_level=3)
        os.replace(ruta_tmp, ruta_salida)

        del dict_res, dict_res_recortado, tabla, temp_dict
        gc.collect()

        t_fin = time.time()
        return {
            "simbolo": simbolo, "status": "OK", "tiempo": round(t_fin - t_inicio, 1),
            "ruta": ruta_salida, "bytes_pico_real_estimado": bytes_pico_real_estimado
        }

    except Exception as e:
        if ruta_tmp and os.path.exists(ruta_tmp):
            try: os.remove(ruta_tmp)
            except Exception: pass
        return {"simbolo": simbolo, "status": "ERROR", "error": f"{type(e).__name__}: {e}"}

# ==============================================================================
# ⚙️ ORQUESTADOR Y CÁLCULO GLOBAL
# ==============================================================================
if __name__ == '__main__':
    print("🧮 Cargando dataset Capa Plata (Fase 0)...")
    inicio_total = time.time()

    try:
        df_raw = pd.read_parquet(RUTA_PARQUET_ORIGEN)
    except Exception as e:
        raise RuntimeError(f"🛑 Error al leer el Parquet original. Detalles: {e}")

    # 🛡️ [V2.2 N7-A2] Reloj sin adivinar: 'time' como columna, o índice DatetimeIndex (se renombra).
    if 'time' in df_raw.columns:
        df_raw = df_raw.set_index('time')
    if not isinstance(df_raw.index, pd.DatetimeIndex):
        raise RuntimeError("🛑 FATAL [Reloj]: el Parquet no tiene columna 'time' ni un índice temporal (DatetimeIndex). Regenerar con Fase_0.py V3.3.")
    df_raw.index.name = 'time'
    if df_raw.index.isna().any():
        raise RuntimeError("🛑 FATAL [Reloj]: el índice temporal contiene NaT.")
    if not df_raw.index.is_monotonic_increasing:
        print("⚠️  [V2.2] El índice venía desordenado: se reordena cronológicamente.")
        df_raw = df_raw.sort_index()
    _n_dup = int(df_raw.index.duplicated().sum())
    if _n_dup > MAX_TIMESTAMPS_DUPLICADOS:
        raise RuntimeError(f"🛑 FATAL [Reloj]: {_n_dup} timestamps duplicados en el Parquet de origen.")
    _paso = df_raw.index.to_series().diff().dropna().median()
    if _paso != pd.Timedelta(minutes=1):
        raise RuntimeError(f"🛑 FATAL [Reloj]: paso mediano {_paso}, no 1 minuto (el origen no es M1).")

    # 🛡️ [V2.2 N7-M3] Sello forense de Fase 0 (si existe) — se hereda a las salidas.
    try:
        meta_f0 = json.loads((pq.read_schema(RUTA_PARQUET_ORIGEN).metadata or {})[b'nexus_fase0'].decode('utf-8'))
    except Exception:
        meta_f0 = {}
    if meta_f0:
        print(f"🧾 Sello Fase 0: {meta_f0.get('version')} | zona: {meta_f0.get('tz')} | {meta_f0.get('filas')} filas | "
              f"{meta_f0.get('t_inicio')} → {meta_f0.get('t_fin')}")
        if meta_f0.get('filas') != len(df_raw):
            raise RuntimeError(f"🛑 FATAL [Sello]: el sello declara {meta_f0.get('filas')} filas y el Parquet tiene "
                               f"{len(df_raw)} (archivo alterado o truncado).")
    else:
        print("⚠️  [V2.2] Parquet de origen SIN sello 'nexus_fase0' (anterior a Fase 0 V3.3): se valida sólo contra los datos.")

    # 🛡️ [FIX T3-H3] Instrumentación del segundo ffill().dropna(). Fase 0
    # (bitácora V3.1/V3.2) declara el dropna final como CERRADO sobre el
    # Parquet que persiste. Si este segundo paso, aplicado sobre ESE MISMO
    # Parquet ya suturado, elimina filas adicionales, es evidencia directa
    # de que el contrato S.S.O.T. de Fase 0 no se cumple al 100% en algún
    # caso no cubierto — se advierte explícitamente en lugar de aplicar el
    # parche en silencio.
    filas_antes_f12 = len(df_raw)
    df_raw = df_raw.ffill().dropna()
    filas_despues_f12 = len(df_raw)
    filas_eliminadas_f12 = filas_antes_f12 - filas_despues_f12

    if filas_eliminadas_f12 > 0:
        print(f"⚠️  [AUDITORÍA T3-H3] ALERTA DE DISCREPANCIA S.S.O.T.: ffill().dropna() en "
              f"Fase 1&2 eliminó {filas_eliminadas_f12} fila(s) adicionales sobre un Parquet "
              f"que Fase 0 declara ya suturado y blindado (dropna final CERRADO, bitácora "
              f"V3.2). Esto indica que el contrato de Fase 0 no se cumple al 100% para este "
              f"dataset, o existe una fuente de NaN no contemplada. Investigar el origen "
              f"antes de considerar la capa Plata (Fase 0) verdaderamente blindada.")
    else:
        print(f"✅ [AUDITORÍA T3-H3] ffill().dropna() confirmado NO-OPERATIVO en este dataset: "
              f"{filas_antes_f12} filas sin cambios. Contrato S.S.O.T. de Fase 0 verificado "
              f"en este punto — el paso se mantiene como guarda defensiva, no como parche activo.")

    print(f"✅ Reloj alineado (Market Time puro): {len(df_raw)} velas útiles.")

    GLOBAL_INDEX = df_raw.index

    print("🧮 Calculando Fuerza de Presión del Precio (FPP) Cruzada Global...")

    # 🛡️ [FIX T3-Patrón] Detección robusta por sufijo EXACTO ('_Close'), no
    # por substring laxo ('_Close' in col) — mismo patrón de robustecimiento
    # aplicado en Fase 0 (Turno 2) para homólogos OHLC.
    pares = [col[:-len('_Close')] for col in df_raw.columns if col.endswith('_Close')]
    if not pares:
        raise RuntimeError("🛑 FATAL [Datos]: el Parquet no contiene ninguna columna '*_Close'.")
    _faltan_ohlc = [f'{p}_{x}' for p in pares for x in ('Open', 'High', 'Low') if f'{p}_{x}' not in df_raw.columns]
    if _faltan_ohlc:
        raise RuntimeError(f"🛑 FATAL [Datos]: columnas OHLC ausentes en el Parquet: {_faltan_ohlc}")

    df_close = df_raw[[f"{p}_Close" for p in pares]].copy()

    # 🛡️ [FIX T3-H1] Carga de OHLC + PHANTOM con Fatal Error explícito.
    faltantes_phantom = []
    for p in pares:
        GLOBAL_OHLC[f'{p}_Open'] = df_raw[f'{p}_Open'].values.astype(np.float32)
        GLOBAL_OHLC[f'{p}_High'] = df_raw[f'{p}_High'].values.astype(np.float32)
        GLOBAL_OHLC[f'{p}_Low']  = df_raw[f'{p}_Low'].values.astype(np.float32)
        GLOBAL_OHLC[f'{p}_Close']= df_raw[f'{p}_Close'].values.astype(np.float32)

        # Códex M1-B: Extracción del marcador phantom
        col_phantom = f'{p}_phantom'
        if col_phantom in df_raw.columns:
            GLOBAL_PHANTOM[p] = df_raw[col_phantom].values.astype(np.float32)
        else:
            faltantes_phantom.append(p)

    # 🛡️ [FIX T3-H1] FATAL EXPLÍCITO — Ley Zero-Hallucination.
    # Antes: `GLOBAL_PHANTOM[p] = np.zeros(...)` — asumía silenciosamente
    # "cero fricción de gaps" para el símbolo. Esto confirmaba empíricamente
    # el Hallazgo Crítico de Turno 2 (cadena de fallo silencioso Fase 0 →
    # Fase 1&2). Ahora se aborta: si Fase 0 fue consolidada correctamente
    # (Turno 2, fix T2-H1), esta rama nunca debería activarse — si se
    # activa, es señal de un Parquet de origen que no pasó por la Fase 0
    # ya corregida, y no debe procesarse a ciegas.
    if faltantes_phantom:
        raise RuntimeError(
            f"🛑 FATAL [Auditoría T3-H1]: {len(faltantes_phantom)} símbolo(s) no tienen "
            f"columna '_phantom' en el Parquet de origen: {faltantes_phantom}. "
            f"Ley Zero-Hallucination: el pipeline NO asume 'cero fricción de gaps' por "
            f"defecto para un símbolo sin marcador forense. Verificar que el Parquet "
            f"provenga de una ejecución de Fase_0.py V3.2+ (con el fix T2-H1 aplicado) "
            f"antes de reintentar."
        )

    _v = df_close.values
    if not np.isfinite(_v).all() or (_v <= 0).any():
        raise RuntimeError("🛑 FATAL [Datos]: hay Close no finitos o <= 0 en el Parquet de origen.")
    _ph_malos = [p for p in pares if not np.isin(GLOBAL_PHANTOM[p], (0.0, 1.0)).all()]
    if _ph_malos:
        raise RuntimeError(f"🛑 FATAL [Datos]: el marcador Phantom de {_ph_malos} contiene valores distintos de 0/1.")
    del _v

    divisores = np.array([0.01 if 'JPY' in p else 0.0001 for p in pares], dtype=np.float32)
    min_div_cuad = 1.0 / (len(pares) ** 2)

    filas_adaptativas = 0   # diagnóstico N7-M1
    for tf_name, shift_velas in TFS_CONFIG.items():
        df_delta = (df_close - df_close.shift(shift_velas)).values / divisores

        pips_totales = np.nansum(np.abs(df_delta), axis=1)
        pips_totales_safe = np.where(pips_totales > 0, pips_totales * len(pares), 1.0)
        fpp_temp = df_delta / pips_totales_safe[:, np.newaxis]

        suma_fpp_neta = np.nansum(fpp_temp, axis=1)
        # [N7-M1] Como Σ|fpp_temp| = 1/N, |suma_fpp_neta| <= 1/N y por tanto div_cuad ≡ min_div_cuad = 1/N²
        # (la parte adaptativa nunca se activa). El factor constante N² resultante SÍ es funcional: fija la
        # escala del acople tanh de abajo. NO eliminar sin re-derivar las señales (cambia los Z downstream).
        div_cuad = np.maximum(np.abs(suma_fpp_neta)**2, min_div_cuad)
        filas_adaptativas += int((np.abs(suma_fpp_neta) ** 2 > min_div_cuad * 1.0001).sum())

        fpp_original = fpp_temp / div_cuad[:, np.newaxis]

        suma_abs_fpp = np.nansum(np.abs(fpp_original), axis=1)
        suma_rel_fpp = np.nansum(fpp_original, axis=1)
        k_kuramoto = np.divide(suma_rel_fpp, suma_abs_fpp, out=np.zeros_like(suma_rel_fpp), where=(suma_abs_fpp > 0))

        sigma_acople = SIGMA_ACOPLE
        diferencia_fase = k_kuramoto[:, np.newaxis] - fpp_original
        friccion_tanh = np.tanh(diferencia_fase)
        fpp_actual = fpp_original + (sigma_acople * friccion_tanh)

        matriz_limpia = np.nan_to_num(fpp_actual, nan=0.0).astype(np.float32)

        matriz_transpuesta = np.ascontiguousarray(matriz_limpia.T)
        matriz_transpuesta.flags.writeable = False
        GLOBAL_FPP[tf_name] = matriz_transpuesta

    if filas_adaptativas:
        print(f"⚠️  [N7-M1] div_cuad dejó de ser constante en {filas_adaptativas} filas: la identidad |S| <= 1/N "
              f"ya no se cumple; revisar la normalización de pips_totales antes de confiar en las señales.")
    else:
        print("✅ [N7-M1] div_cuad ≡ 1/N² en todas las filas (identidad verificada; normalización constante).")

    del df_delta, fpp_temp, df_close, df_raw
    gc.collect()

    print("🔥 [JIT WARM-UP] Calentando compilador C++ antes del Enjambre...")
    _dummy_fpp = np.zeros(200, dtype=np.float32)
    _dummy_fpp.flags.writeable = False   # [N7-B1] misma firma (solo lectura) que las filas de GLOBAL_FPP
    _procesar_core_numba(_dummy_fpp, 15)
    _dummy_res = np.zeros(100, dtype=np.float32)
    calc_robust_zscore_numba(_dummy_res, 30)
    print("✅ Caché JIT lista. Previniendo Race Conditions del compilador.")

    if len(GLOBAL_INDEX) <= START_IDX:
        raise RuntimeError(f"🛑 FATAL: el dataset tiene {len(GLOBAL_INDEX)} filas y el recorte causal exige > {START_IDX}.")
    _borradas = 0
    for _p in pares:
        _r = os.path.join(DIRECTORIO_SALIDA, f'nexus_df_salida_3D_{_p}_MultiZ.parquet')
        if os.path.exists(_r):
            os.remove(_r); _borradas += 1
    if _borradas:
        print(f"🧹 [N7-A1] {_borradas} salida(s) de corridas previas eliminadas (no coexisten versiones mezcladas).")
    META_SALIDA = json.dumps({
        'version': FASE12_VERSION, 'start_idx': START_IDX, 'filas_salida': len(GLOBAL_INDEX) - START_IDX,
        'tfs': TFS_CONFIG, 'resoluciones_fpp': RESOLUCIONES_FPP, 'ventanas_z': VENTANAS_Z,
        'sigma_acople': SIGMA_ACOPLE, 'pip_divisor': 'JPY=0.01 / resto=0.0001', 'pares': pares,
        'fase0': {k: meta_f0.get(k) for k in ('version', 'tz', 'filas', 't_inicio', 't_fin', 'phantom_pct')} if meta_f0 else None,
    }).encode('utf-8')

    tareas = [(i, pares[i]) for i in range(len(pares))]

    SEMAFORO_ESCRITURA = threading.Semaphore(1)

    print("\n🧪 [AUTOCALIBRACIÓN 1/2] Midiendo huella de memoria real (pico transitorio)...")
    idx_prueba, simbolo_prueba = tareas[0]
    resultado_prueba = procesar_simbolo_worker((idx_prueba, simbolo_prueba))
    if resultado_prueba["status"] != "OK":
        raise RuntimeError(f"🛑 Falló el símbolo de calibración ({simbolo_prueba}): {resultado_prueba.get('error')}")

    # 🛡️ [FIX T3-H2] Se usa la huella de PICO real (dict_res + recortado,
    # con sizing correcto de columnas object), no la subestimación anterior.
    bytes_por_worker = resultado_prueba["bytes_pico_real_estimado"]
    ram_disponible = memoria_disponible_bytes()
    n_compute_por_ram = max(1, int((ram_disponible * FACTOR_SEGURIDAD_RAM) / bytes_por_worker))
    n_compute_por_cpu = max(1, int(os.cpu_count() * TECHO_MULTIPLICADOR_CPU))
    N_COMPUTE = max(1, min(n_compute_por_ram, n_compute_por_cpu, max(1, len(pares) - 1)))

    print(f"   ↳ Huella medida (pico real, dict_res + recortado): {bytes_por_worker/(1024**3):.2f} GB/símbolo")
    print(f"   ↳ ✅ Concurrencia de CÓMPUTO autocalibrada: {N_COMPUTE} símbolos simultáneos")

    print("\n🧪 [AUTOCALIBRACIÓN 2/2] Midiendo throughput de disco...")
    mbps_medido = calibrar_throughput_disco(DIRECTORIO_SALIDA, TAM_PROBE_DISCO_MB)
    N_ESCRITURAS = escrituras_concurrentes_desde_throughput(mbps_medido)
    SEMAFORO_ESCRITURA = threading.Semaphore(N_ESCRITURAS)
    print(f"   ↳ ✅ Escrituras Parquet concurrentes autocalibradas: {N_ESCRITURAS}")

    print(f"\n🚀 [FASE ENJAMBRE] Lanzando ThreadPoolExecutor con {N_COMPUTE} workers de cómputo...")

    tareas_restantes = tareas[1:]
    resultados_exitosos = 1
    fallidos = []
    print(f"  [+] {resultado_prueba['simbolo']} procesado en {resultado_prueba['tiempo']}s -> 💾 {resultado_prueba['ruta']} (calibración)")

    with concurrent.futures.ThreadPoolExecutor(max_workers=N_COMPUTE) as executor:
        futuros = {executor.submit(procesar_simbolo_worker, tarea): tarea for tarea in tareas_restantes}

        for futuro in concurrent.futures.as_completed(futuros):
            res = futuro.result()
            if res["status"] == "OK":
                resultados_exitosos += 1
                print(f"  [+] {res['simbolo']} procesado en {res['tiempo']}s -> 💾 {res['ruta']}")
            else:
                fallidos.append(res['simbolo'])
                print(f"  [!] ERROR en {res['simbolo']}: {res['error']}")

    segundos_totales = time.time() - inicio_total
    if fallidos or resultados_exitosos != len(pares):
        raise RuntimeError(f"🛑 FASE 1&2 INCOMPLETA ({round(segundos_totales, 1)} s): {resultados_exitosos}/{len(pares)} símbolos OK. "
                           f"Fallidos: {fallidos}. Sus archivos NO existen (se borraron al inicio); no continuar a Fase 3.")
    print(f"\n🏆 ¡PROCESO COMPLETADO EN {round(segundos_totales, 1)} SEGUNDOS!")
