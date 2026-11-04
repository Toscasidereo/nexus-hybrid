# ==============================================================================
# 🧠 NEXUS FASE 4.5 V12.0 — ETAPA A: GEMELO DIGITAL (SUPERSET UNIVERSAL E0..E3)
# ⚡ SIMULADOR FORENSE OOS + AUDITORÍA DE PARIDAD DE SILICIO + TRIBUNAL DE CARTERA
# 🎯 INTEGRACIÓN TOTAL TABLERO ÚNICO + PARIDAD ACTIVA CON FASE 4 V12 Y EA V12.01+
# ==============================================================================
# 📋 BITÁCORA LAB-V7 V0.1 (2026-11-04) — COPIA DE LABORATORIO de Fase_4_5_V_12_0_A.py (rama lab-v7; `main` intacto):
#    Orden del CRO: "Alinea todas las fases de python, para que funcione el lab 7".
#    - Tag y carpeta de salida desde las mismas variables NEXUS_LAB_* que Fase_4_lab.py (apagadas = nombres y comportamiento de main).
#    - `parse_tam` lee los campos `tam_*` del .txt (Ridge de tamaño); `simular_motor` recibe `escala_v` y multiplica `v_req_tmp` como el
#      kernel de Fase 4 y el EA gemelo. La escala se calcula con `lab_escala.py` (mismo código que Fase 4) sobre TODO el parquet
#      (el EA la aplica siempre); en el OOS del fold coincide con la de Fase 4, que solo la define en la ventana IS+OOS.
#    - Sin campos `tam_*` en el bloque: escala 1 (comportamiento de main). Gemelo nulo + tamaño: no exportable, se rechaza al iniciar.
#    - Control: lab_v7/lab_pruebas.py (L9: con escala 1 el kernel iguala bit a bit al de main; el texto exportado reproduce la escala).
# ==============================================================================
# 📋 BITÁCORA V12.0 (promoción mayor — paridad superset con Fase 4 V12 y EA V12.01+):
#    - [H-45-01 / H-45-04 CERRADO] Homologación a Superset Universal E0..E3.
#      Soporte nativo para Cabeza B (w_T[10], bias_T, t_min_admision, cabeza_t_activa)
#      y Ridge 2 extendido a 10 features (w_superv[10], ΔT vivo y ΔT·Θ).
#    - [H-45-02 CERRADO] TAG_ARCHIVOS_FASE4 alineado con `PROD_V12_{ESCALON}`.
#    - [H-45-03 CERRADO] Incorporada guarda anti-asfixia dura `velas_abiertas > inm`
#      en kernel `simular_motor` (idéntica a Fase 4 V12 y EA V12.01).
#    - [PARIDAD BIT-A-BIT] Tracking de ΔT vivo integrado con envolvente completa MFE/MAE
#      y acumulación estricta de t_gain/t_loss.
#    - [WARMUP JIT] Rutina `_warmup_jit()` precalienta LLVM antes del bucle de símbolos.
# ==============================================================================
# 📋 BITÁCORA rev.c (TABLERO ÚNICO — edición programática, ver parche_fase45_tablero.py y Fase_4_5_V11_0.tablero.diff):
#    - N_FOLDS, RATIO_TRAIN_TEST y MEMORIA_FIFO se importan de nexus_tablero.py; geometria() delega en TAB.geometria (una sola fórmula
#      para Fase 3, Fase 4 y Fase 4.5; cierra H-12). Paridad = OOS de cada fold sobre el N efectivo; portafolio = tramo RESERVADO.
#    - Se VERIFICAN los sellos: cabecera del .txt y CSV de Fase 4 (mismo tablero, mismo parquet, reserva aplicada). Si no coinciden, el
#      símbolo se salta con causa explícita ('Sello_Fase4_invalido' / 'Sello_CSV_Fase4_invalido', estado 'tablero_desalineado').
#    - Sin reserva (RESERVA_FINAL=0) la ventana de portafolio sigue siendo el último TEST (comportamiento histórico) pero se marca
#      NO CIEGA (aviso en consola, en meta.json y en las imágenes de la Etapa B). Con reserva > 0 es el tramo ciego de Fases 3 y 4.
#    - Sin ningún otro cambio de lógica (parser, kernel, paridad, streams: intactos).
# ==============================================================================
# 📋 BITÁCORA V11.0 (reescritura sobre la especificación "Fase 4.5 V11.0"):
#    - Entradas SOLO por archivo: Cerebro_MQL5_<tag>_<SIM>.txt + parquet de Fase 1&2 (+ CSV de Fase 4, opcional, para paridad).
#      No usa memoria ni estado de Fase 4. El spread sale del .txt (SSOT), no de MATRIZ_SPREADS.
#    - [G-01] Parser estricto: encabezados con paréntesis anidados y bloques de rank 2-10 dentro de /* */ (V9.5 no leía ni el rank 1).
#      Variable ausente => error de ESA configuración con causa registrada (nunca 0.0 por defecto).
#    - [G-02] Fid con V_cruda unificada (idéntica a Fase 4 V10/V11 y EA V11.83). El .txt debe declarar FID_VELOCIDAD_UNIFICADA = True.
#    - [G-03] Sin `except: continue`: contadores de cobertura por causa; error fatal si cero símbolos se procesan.
#    - [G-04] ratio_captura y tolerancia_vida se LEEN del .txt. Solo contrato E0 (8 pesos de supervivencia); LAB ESCALON != E0 => se rechaza.
#    - [G-05] Ventanas con la MISMA semántica de rebanada que Fase 4 (estado plano al inicio, cierre forzado en la última vela):
#      paridad = OOS del Fold del motor; portafolio = tramo común [N-TEST, N).
#    - [G-07] Eje temporal por fecha: el vector 'Time' debe ser IDÉNTICO en los 28 parquets (si no, error fatal).
#    - Kernel PROPIO (registra vela a vela) e independiente del de Fase 4; la prueba de paridad (test_fase45_v11.py) garantiza que no se desfasen.
#    - Cada motor se simula con y sin supervivencia (contrafactual). Salidas: TRADES y VELAS (disperso) en parquet.
#    ⚠️ Premisa abierta (CRO): la cuenta suma pips de pares distintos con lote fijo.
# ==============================================================================

import os
import re
import gc
import sys
import json
import math
import time
import warnings
from collections import OrderedDict

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from numba import njit, set_num_threads

from nexus_formulas_core import (
    eval_robustez_numba_v6, calcular_t_score_trade_numba, FORMULAS_CORE_VERSION
)

import nexus_tablero as TAB
from lab_escala import ACT_VENTANA, lab_actividad_nb, x10_desde_arreglos, escala_desde_parametros   # [LAB-V7]

warnings.simplefilter('ignore')

# ==============================================================================
# 🎛️ TABLERO DE CONTROL MAESTRO
# ==============================================================================
FASE45_VERSION = "V12.0"
LISTA_SIMBOLOS = ['EURUSDm', 'EURJPYm', 'EURCADm', 'EURAUDm', 'EURGBPm', 'EURCHFm', 'EURNZDm',
                  'GBPUSDm', 'GBPAUDm', 'GBPNZDm', 'GBPCHFm', 'GBPCADm', 'GBPJPYm',
                  'AUDJPYm', 'AUDUSDm', 'AUDNZDm', 'AUDCADm', 'AUDCHFm',
                  'NZDJPYm', 'NZDUSDm', 'NZDCHFm', 'NZDCADm',
                  'USDCADm', 'USDJPYm', 'USDCHFm',
                  'CADCHFm', 'CADJPYm', 'CHFJPYm']

ESCALON = 'E3'                       # Escalón objetivo por defecto ('E0', 'E1', 'E2', 'E3')
assert ESCALON in ('E0', 'E1', 'E2', 'E3')

# [LAB-V7] mismo tag que Fase_4_lab.py (variables NEXUS_LAB_*; apagadas = idéntico a la Fase 4.5 de main)
LAB_TAMANO = os.environ.get('NEXUS_LAB_TAMANO', 'off')           # 'off' | 'A' | 'B'
LAB_CIERRE = os.environ.get('NEXUS_LAB_CIERRE', 'T_terminal')    # 'T_terminal' | 'dT_cont' | 'G_pips'
LAB_NULO = os.environ.get('NEXUS_LAB_NULO', '0') == '1'
LAB_METRICA = os.environ.get('NEXUS_LAB_METRICA', 'final')       # 'final' | 'v7' (solo cambia el tag: 4.5 no usa Score_v7)
assert LAB_METRICA in ('final', 'v7'), f"NEXUS_LAB_METRICA invalido: {LAB_METRICA}"
assert LAB_TAMANO in ('off', 'A', 'B'), f"NEXUS_LAB_TAMANO invalido: {LAB_TAMANO}"
assert LAB_CIERRE in ('T_terminal', 'dT_cont', 'G_pips'), f"NEXUS_LAB_CIERRE invalido: {LAB_CIERRE}"
assert not (LAB_NULO and LAB_TAMANO != 'off'), "Gemelo nulo con Ridge de tamaño no es exportable: la escala desplazada no sale en el .txt"
LAB_ACTIVO = (LAB_TAMANO != 'off') or (LAB_CIERRE != 'T_terminal') or LAB_NULO or (LAB_METRICA != 'final')
_SUF_LAB = (f"_LAB_{LAB_TAMANO}_{LAB_CIERRE}" + ("_MV7" if LAB_METRICA == "v7" else "") + ("_NULO" if LAB_NULO else "")) if LAB_ACTIVO else ""
TAG_ARCHIVOS_FASE4 = f"PROD_V12_{ESCALON}" + _SUF_LAB  # Sincronizado con Fase 4 V12.0 / Fase_4_lab.py
DIR_ENTRADA = "."
DIR_SALIDA = f"F45_V12_{ESCALON}" + _SUF_LAB

RANKS_A_SIMULAR = tuple(range(1, 11))
N_FOLDS = TAB.N_FOLDS
RATIO_TRAIN_TEST = TAB.RATIO_TRAIN_TEST
MEMORIA_FIFO = TAB.MEMORIA_FIFO
MIN_OPS_OOS_EXPORT = 30
MIN_OPS_BASE = 3
MIN_OPS_MOTOR_PF = 3
CHEQUEAR_PARIDAD = True
PERMITIR_FID_NO_DECLARADA = False
MAX_CACHE_CANALES = 10
COL_TIEMPO = 'TIME'
TOL_PARIDAD = 1e-6

COLS_OHLC = {'open': 'OPENM1', 'high': 'HIGHM1', 'low': 'LOWM1', 'phantom': 'PHANTOM'}

# ==============================================================================
# 🔬 FORENSE Y COBERTURA
# ==============================================================================
_descartes = {}
_cobertura = {'ok': 0, 'sin_txt': [], 'sin_parquet': [], 'txt_invalido': [], 'escalon_no_soportado': [],
              'fid_no_soportada': [], 'sin_motores': [], 'datos_invalidos': [], 'tablero_desalineado': []}


def _registrar_descarte(simbolo, motor, causa):
    clave = f"{simbolo}|{motor}|{causa}"
    _descartes[clave] = _descartes.get(clave, 0) + 1


class ErrorConfig(Exception):
    """Error recuperable de una configuración."""


class ErrorSimbolo(Exception):
    """Error que impide procesar el símbolo completo."""
    def __init__(self, estado, msg):
        super().__init__(msg)
        self.estado = estado


# ==============================================================================
# 🔍 PARSER ESTRICTO SUPERSET V12.0
# ==============================================================================
_RE_HDR = re.compile(r'//[^\n]*?\b(LONG|SHORT)\b[^\n]*?RANK\s*#(\d+)')
_PREF = {'LONG': ('toro', 'ml_toro', 'superv_toro'), 'SHORT': ('oso', 'ml_oso', 'superv_oso')}
_MARCOS = ('Fast', 'Mid', 'Slow')


def _var(cuerpo, nombre):
    m = re.search(r'g_pares\[idx\]\.' + re.escape(nombre) + r'\s*=\s*([^;]+);', cuerpo)
    if not m:
        raise ErrorConfig(f"variable_ausente:{nombre}")
    return m.group(1).strip()


def _flt(cuerpo, nombre):
    s = _var(cuerpo, nombre)
    try:
        v = float(s)
    except ValueError:
        raise ErrorConfig(f"valor_no_numerico:{nombre}")
    if not math.isfinite(v):
        raise ErrorConfig(f"valor_no_finito:{nombre}")
    return v


def _enum(s, prefijo, nombre):
    if not s.startswith(prefijo):
        raise ErrorConfig(f"enum_invalido:{nombre}")
    return s[len(prefijo):]


def _parse_lado(cuerpo, cfg, lado):
    marco = _enum(_var(cuerpo, f"cfg.{cfg}.marco_{lado}"), 'MARCO_', f'marco_{lado}').capitalize()
    if marco not in _MARCOS:
        raise ErrorConfig(f"marco_desconocido:{lado}")
    res = _enum(_var(cuerpo, f"cfg.{cfg}.res_{lado}"), 'RES_', f'res_{lado}')
    try:
        pz = int(_var(cuerpo, f"cfg.{cfg}.pz_{lado}"))
    except ValueError:
        raise ErrorConfig(f"pz_invalido:{lado}")
    return {'marco': marco, 'res': res, 'pz': pz,
            'base_enum': _var(cuerpo, f"cfg.{cfg}.base_{lado}"),
            'acum_enum': _var(cuerpo, f"cfg.{cfg}.tension_{lado}"),
            'armado': _flt(cuerpo, f"cfg.{cfg}.armado_{lado}"),
            'chasquido': _flt(cuerpo, f"cfg.{cfg}.chasquido_{lado}")}


def parse_tam(cuerpo, ml):
    """[LAB-V7] Parámetros del Ridge de tamaño del bloque, o None si el bloque no los trae (main / EA V12.01)."""
    if not re.search(r'g_pares\[idx\]\.' + re.escape(ml) + r'\.tam_modo\s*=', cuerpo):
        return None
    modo = int(_flt(cuerpo, f"{ml}.tam_modo"))
    if modo not in (1, 2):
        raise ErrorConfig("tam_modo_invalido")
    tam = {'modo': 'A' if modo == 1 else 'B', 'act_med': _flt(cuerpo, f"{ml}.tam_act_med"), 'a_is_med': _flt(cuerpo, f"{ml}.tam_a_is_med"),
           'esc_min': _flt(cuerpo, f"{ml}.tam_esc_min"), 'esc_max': _flt(cuerpo, f"{ml}.tam_esc_max")}
    if not (tam['act_med'] > 0 and tam['a_is_med'] > 0 and tam['esc_min'] > 0 and tam['esc_max'] >= tam['esc_min']):
        raise ErrorConfig("tam_parametros_invalidos")
    if modo == 1:
        tam['intercept'] = _flt(cuerpo, f"{ml}.tam_intercept"); tam['med_pred'] = _flt(cuerpo, f"{ml}.tam_med_pred")
        for nom, clave in (('tam_w', 'coef'), ('tam_mu', 'mu'), ('tam_sd', 'sd')):
            tam[clave] = np.array([_flt(cuerpo, f"{ml}.{nom}[{k}]") for k in range(11)], dtype=np.float64)
        if not (tam['med_pred'] > 0 and (tam['sd'] > 0).all()):
            raise ErrorConfig("tam_parametros_invalidos")
    return tam


def _parse_bloque(direccion, rank, fold, cuerpo, escalon_txt):
    cfg, ml, sv = _PREF[direccion]
    m = {'Dir': direccion, 'Rank': rank, 'Fold': fold,
         'In': _parse_lado(cuerpo, cfg, 'in'), 'Out': _parse_lado(cuerpo, cfg, 'out')}

    # 1. Cabeza A de Entrada (Velocidad)
    m['ml'] = {
        'umbral': _flt(cuerpo, f"{ml}.umbral"), 'bias': _flt(cuerpo, f"{ml}.bias"),
        'med_v': _flt(cuerpo, f"{ml}.mediana_v"), 'mad_v': _flt(cuerpo, f"{ml}.mad_v"),
        'atrac_t': _flt(cuerpo, f"{ml}.limite_tiempo"),
        'ratio_captura': _flt(cuerpo, f"{ml}.ratio_captura"),
        'tolerancia_vida': _flt(cuerpo, f"{ml}.tolerancia_vida"),
        'w': np.array([_flt(cuerpo, f"{ml}.w[{k}]") for k in range(10)], dtype=np.float64)
    }

    # 2. Cabeza B de Entrada (Calidad OOF) — Superset V12
    m_cb = re.search(r'g_pares\[idx\]\.' + re.escape(ml) + r'\.cabeza_t_activa\s*=\s*(true|false);', cuerpo)
    cabeza_activa = (m_cb.group(1).lower() == 'true') if m_cb else (escalon_txt in ('E2', 'E3'))
    w_T = np.zeros(10, dtype=np.float64)
    bias_T = 0.0
    t_min = -1.0
    if cabeza_activa:
        bias_T = _flt(cuerpo, f"{ml}.bias_T")
        t_min = _flt(cuerpo, f"{ml}.t_min_admision")
        for k in range(10):
            w_T[k] = _flt(cuerpo, f"{ml}.w_T[{k}]")
    m['ml']['cabeza_t_activa'] = cabeza_activa
    m['ml']['w_T'] = w_T
    m['ml']['bias_T'] = bias_T
    m['ml']['t_min'] = t_min

    # 3. Ridge 2 de Supervivencia Continua (8 o 10 Features) — Superset V12
    m_nf = re.search(r'g_pares\[idx\]\.' + re.escape(sv) + r'\.n_features\s*=\s*(\d+);', cuerpo)
    n_features = int(m_nf.group(1)) if m_nf else (10 if escalon_txt == 'E3' else 8)

    m_inm = re.search(r'g_pares\[idx\]\.' + re.escape(sv) + r'\.inmunidad_velas\s*=\s*(\d+);', cuerpo)
    inmunidad = int(m_inm.group(1)) if m_inm else (0 if escalon_txt == 'E0' else 2)

    w_superv = np.zeros(10, dtype=np.float64)
    for k in range(n_features):
        w_superv[k] = _flt(cuerpo, f"{sv}.w_superv[{k}]")

    m['sv'] = {
        'bias': _flt(cuerpo, f"{sv}.b_superv"),
        'k': _flt(cuerpo, f"{sv}.k_abortar"),
        'inmunidad_velas': inmunidad,
        'n_features': n_features,
        'w': w_superv
    }

    m['tam'] = parse_tam(cuerpo, ml)
    if m['ml']['atrac_t'] <= 0 or m['ml']['mad_v'] <= 0 or m['ml']['tolerancia_vida'] <= 0:
        raise ErrorConfig("parametros_no_positivos(atrac_t/mad_v/tolerancia_vida)")
    return m


def leer_cerebro(ruta, ranks):
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            txt = f.read()
    except Exception as e:
        raise ErrorSimbolo('txt_invalido', f"no se pudo leer {ruta}: {type(e).__name__}")

    mes = re.search(r'ESCALON=(\w+)', txt)
    escalon = mes.group(1) if mes else 'E0'
    if escalon not in ('E0', 'E1', 'E2', 'E3'):
        raise ErrorSimbolo('escalon_no_soportado', f"ESCALON={escalon} desconocido en .txt")

    mf = re.search(r'FID_VELOCIDAD_UNIFICADA\s*=\s*(True|False)', txt)
    if mf and mf.group(1) == 'False':
        raise ErrorSimbolo('fid_no_soportada', "el .txt declara FID_VELOCIDAD_UNIFICADA = False: no soportado")
    if not mf and not PERMITIR_FID_NO_DECLARADA:
        raise ErrorSimbolo('fid_no_soportada', "el .txt no declara FID_VELOCIDAD_UNIFICADA")

    msp = re.search(r'spread_asumido_ia\s*=\s*([^;\s]+)\s*;', txt)
    if not msp:
        raise ErrorSimbolo('txt_invalido', "spread_asumido_ia ausente en el .txt")
    try:
        spread = float(msp.group(1))
    except ValueError:
        raise ErrorSimbolo('txt_invalido', "spread_asumido_ia no numérico")
    if not (math.isfinite(spread) and spread > 0):
        raise ErrorSimbolo('txt_invalido', "spread_asumido_ia no positivo")

    bloques = []
    actual = None
    for ln in txt.split('\n'):
        mh = _RE_HDR.search(ln)
        if mh and 'SUPERVIVENCIA' in ln:
            if actual is not None:
                bloques.append(actual)
            mfold = re.search(r'Fold:\s*(\d+)', ln)
            actual = {'dir': mh.group(1), 'rank': int(mh.group(2)),
                      'fold': int(mfold.group(1)) if mfold else None, 'cuerpo': []}
        elif actual is not None:
            actual['cuerpo'].append(ln)
    if actual is not None:
        bloques.append(actual)
    if not bloques:
        raise ErrorSimbolo('sin_motores', "el .txt no contiene ningún bloque RANK reconocible")

    motores, errores, vistos = [], [], set()
    for b in bloques:
        if b['rank'] not in ranks:
            continue
        clave = (b['dir'], b['rank'])
        if clave in vistos:
            errores.append((b['dir'], b['rank'], 'bloque_duplicado'))
            continue
        vistos.add(clave)
        try:
            if b['fold'] is None:
                raise ErrorConfig("fold_ausente_en_encabezado")
            motores.append(_parse_bloque(b['dir'], b['rank'], b['fold'], '\n'.join(b['cuerpo']), escalon))
        except ErrorConfig as e:
            errores.append((b['dir'], b['rank'], str(e)))
    return {'spread': spread, 'escalon': escalon, 'tablero': TAB.parsear_linea(txt)}, motores, errores


# ==============================================================================
# 🧭 RESOLUCIÓN DE COLUMNAS
# ==============================================================================
def deducir_features(base_col, acum_col):
    partes = str(base_col).split('_')
    res = partes[-1]; tf = partes[-2]
    familia = "_".join(partes[:-2])
    if familia in ("Int_Area", "Int_V"): v_f, a_f = "Int_V", "Int_A"
    elif familia in ("Int2_Area", "Int2_V"): v_f, a_f = "Int2_V", "Int2_A"
    elif familia == "FPP": v_f, a_f = "FPP_V", "FPP_A"
    else: return None, None
    match = re.match(r'Z(\d+)_', str(acum_col))
    if match:
        pz = match.group(1)
        return f"Z{pz}_{v_f}_{tf}_{res}", f"Z{pz}_{a_f}_{tf}_{res}"
    return f"{v_f}_{tf}_{res}", f"{a_f}_{tf}_{res}"


def obtener_z_base(base_col, acum_col):
    match = re.match(r'Z(\d+)_', str(acum_col))
    return f"Z{match.group(1)}_{base_col}" if match else base_col


def obtener_contexto_macro(base_col, acum_col):
    partes = str(base_col).split('_'); res = partes[-1]; marco_actual = partes[-2]
    base_name = "_".join(partes[:-2])
    m1, m2 = [m for m in _MARCOS if m != marco_actual][:2]
    match = re.match(r'Z(\d+)_', str(acum_col))
    if match:
        pz = match.group(1)
        return f"Z{pz}_{base_name}_{m1}_{res}", f"Z{pz}_{base_name}_{m2}_{res}"
    return f"{base_name}_{m1}_{res}", f"{base_name}_{m2}_{res}"


def resolver_columnas(motor, cols_up):
    def R(nombre):
        real = cols_up.get(nombre.upper())
        if real is None:
            raise ErrorConfig(f"columna_ausente:{nombre}")
        return real

    def base_acum(lado):
        d = motor[lado]
        base = _enum(d['base_enum'], 'BASE_', 'base')
        if base.endswith('_CRUDO'): base = base[:-6]
        ac = _enum(d['acum_enum'], 'ACUM_', 'acum')
        if d['pz'] > 0:
            if not ac.startswith('Z_'):
                raise ErrorConfig("acum_sin_Z_con_pz>0")
            ac = ac[2:]
        elif ac.startswith('Z_'):
            raise ErrorConfig("acum_Z_con_pz==0")
        if ac.endswith('_CRUDO'): ac = ac[:-6]
        sufijo = f"{d['marco']}_{d['res']}"
        col_base = R(f"{base}_{sufijo}")
        col_acum = R(f"Z{d['pz']}_{ac}_{sufijo}" if d['pz'] > 0 else f"{ac}_{sufijo}")
        v, a = deducir_features(col_base, col_acum)
        if v is None:
            raise ErrorConfig("familia_features_desconocida")
        zb = obtener_z_base(col_base, col_acum)
        return col_base, col_acum, R(v), R(a), R(zb)

    cb_i, ca_i, v_i, a_i, z_i = base_acum('In')
    cb_o, ca_o, v_o, a_o, z_o = base_acum('Out')
    m1, m2 = obtener_contexto_macro(cb_i, ca_i)
    return {'base_in': cb_i, 'acum_in': ca_i, 'v_in': v_i, 'a_in': a_i, 'zbase_in': z_i,
            'base_out': cb_o, 'acum_out': ca_o, 'v_out': v_o, 'a_out': a_o, 'zbase_out': z_o,
            'macro1': R(m1), 'macro2': R(m2)}


# ==============================================================================
# 🚀 KERNELS NUMBA SUPERSET V12.0 (fastmath=False — paridad C/Py)
# ==============================================================================
@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
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


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def calcular_acum_ciclo_numba(metrica_arr, cambios):
    N = len(metrica_arr); out = np.empty(N, dtype=np.float32); running_sum = 0.0
    for i in range(N):
        if cambios[i] == 1: running_sum = metrica_arr[i]
        else: running_sum += metrica_arr[i]
        out[i] = running_sum
    return out


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
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


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def rolling_median_causal_numba(extremos_ciclo, direction=1, memoria_fifo=100, min_periods=5):
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


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def _velocidad_snapshot(mfe_actual, mae_previo, profit_apertura, v_ef, spread_pips):
    bruto = profit_apertura + spread_pips
    m_mfe = max(mfe_actual, bruto)
    m_mae = min(mae_previo, bruto)
    return (m_mfe - abs(m_mae)) / (v_ef * (1.0 + (abs(m_mae) / 10.0)))


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def simular_motor(
    direccion, idx_off,
    signos_in, extremo_in, sat_in, acum_in, signos_out, extremo_out, sat_out, acum_out,
    z_base_in, in_v, in_a, z_base_out, out_v, out_a, z_macro_1, z_macro_2,
    opens_arr, highs_arr, lows_arr, phantom_arr, pips_mult, n_velas,
    armado_in, chasquido_in, armado_out, chasquido_out, spread_pips,
    W_R, B_R, med_v, mad_v, atrac_t, umbral_z_ia, ratio_captura, tolerancia_vida,
    activar_superv, W_S, B_S, K_abortar,
    inmunidad_velas, n_features_superv,
    cabeza_t_activa, W_T, B_T, T_min, escala_v):
    """
    Simulador Gemelo Digital V12.0 (Superset Universal E0..E3).
    Soporta:
      - Cabeza B (Admisión por T_raw >= T_min con T_hat0 registrado).
      - Guarda anti-asfixia dura (velas_abiertas > inmunidad_velas).
      - Ridge 2 continuo de 8 o 10 dimensiones con ΔT vivo.
    """
    max_trades = (n_velas // 2) + 5
    tr = np.empty((max_trades, 9), dtype=np.float64)
    vl = np.empty((n_velas + 5, 9), dtype=np.float64)
    cnt = 0; nv = 0; last_row = -1

    pos = 0; p_in = 0.0; max_v = 0.0; min_v = 0.0; idx_in = 0; v_req = 0.0; Z_pred = 0.0
    t_gain = 0.0; t_loss = 0.0; trade_tuvo_iteracion = False; T_hat0 = 0.0
    mae_previo = 0.0; mfe_actual = 0.0; profit_apertura = 0.0
    lim_T_seguro = (atrac_t * tolerancia_vida) + 1e-9 if atrac_t > 0 else 50.0

    for i in range(1, n_velas - 1):
        if pos != 0:
            trade_tuvo_iteracion = True
            if highs_arr[i] > max_v: max_v = highs_arr[i]
            if lows_arr[i] < min_v: min_v = lows_arr[i]

            if direccion == 1: prof_vela = ((opens_arr[i] - p_in) * pips_mult) - spread_pips
            else: prof_vela = ((p_in - opens_arr[i]) * pips_mult) - spread_pips
            fav = 1.0 if prof_vela > 0.0 else 0.0
            if phantom_arr[i] == 0.0:
                if prof_vela > 0.0: t_gain += 1.0
                else: t_loss += 1.0

            velas_abiertas = max(float(i - idx_in + 1), 1.0)
            if direccion == 1:
                mae_previo = (min_v - p_in) * pips_mult; mfe_actual = (max_v - p_in) * pips_mult
                profit_apertura = ((opens_arr[i+1] - p_in) * pips_mult) - spread_pips
            else:
                mae_previo = (p_in - max_v) * pips_mult; mfe_actual = (p_in - min_v) * pips_mult
                profit_apertura = ((p_in - opens_arr[i+1]) * pips_mult) - spread_pips
            closed = False; m_mae = mae_previo; tipo = 0; t_pred = np.nan

            # 1. TimeStop / 2. SmartTrailing (Brazo Ofensivo)
            if atrac_t > 0 and velas_abiertas > lim_T_seguro:
                closed = True; tipo = 1; m_mae = min(mae_previo, profit_apertura + spread_pips)
            else:
                target_req = max((v_req * velas_abiertas * (1.0 + (abs(mae_previo) / 10.0))) + (abs(mae_previo) * 0.5), spread_pips + 1.0)
                if profit_apertura >= target_req:
                    closed = True; tipo = 2; m_mae = mae_previo

            # 3. Saturador de salida estructural
            if not closed:
                if direccion == 1:
                    if signos_out[i] > 0 and extremo_out[i] >= (sat_out[i] * armado_out) and acum_out[i] <= (extremo_out[i] * (1.0 - chasquido_out)):
                        closed = True; tipo = 3; m_mae = min(mae_previo, profit_apertura + spread_pips)
                else:
                    if signos_out[i] < 0 and extremo_out[i] <= (sat_out[i] * armado_out) and acum_out[i] >= (extremo_out[i] * (1.0 - chasquido_out)):
                        closed = True; tipo = 3; m_mae = min(mae_previo, profit_apertura + spread_pips)

            # 4. Supervivencia Ridge 2 (Brazo Defensivo) con guarda anti-asfixia dura [H-45-03]
            if not closed and activar_superv and velas_abiertas > inmunidad_velas:
                v_ef = max(velas_abiertas, 3.0)
                V_z = (_velocidad_snapshot(mfe_actual, mae_previo, profit_apertura, v_ef, spread_pips) - med_v) / (mad_v + 1e-9)
                if velas_abiertas <= 2.0: Fid = 0.5
                else: Fid = (math.tanh(V_z - Z_pred) + 1.0) / 2.0
                D_ = 1.0 / (1.0 + (abs(mae_previo) / (mad_v * v_ef + 1e-9)))
                Theta = 1.0 - min(velas_abiertas / lim_T_seguro, 1.0)
                C_ = (math.tanh(mfe_actual / (mad_v * v_ef + 1e-9)) + 1.0) / 2.0
                inter_TD = Theta * D_; inter_FD = Fid * D_
                Z_pred_norm = math.tanh(Z_pred); v_ef_norm = math.tanh(v_ef / lim_T_seguro)

                t_pred = (W_S[0]*Fid + W_S[1]*D_ + W_S[2]*Theta + W_S[3]*C_ + W_S[4]*Z_pred_norm + W_S[5]*v_ef_norm + W_S[6]*inter_TD + W_S[7]*inter_FD)

                # Expansión E3 (10D): Inyección de ΔT y ΔT·Θ [H-45-04]
                if n_features_superv == 10:
                    bruto_s = profit_apertura + spread_pips
                    m_mfe_s = max(mfe_actual, bruto_s); m_mae_s = min(mae_previo, bruto_s)
                    t_obs_s = calcular_t_score_trade_numba(m_mfe_s, m_mae_s, profit_apertura, t_gain, t_loss, spread_pips)
                    dT = min(max(t_obs_s - T_hat0, -1.0), 1.0)
                    t_pred += (W_S[8]*dT) + (W_S[9]*(dT * Theta))

                t_pred += B_S
                if t_pred < K_abortar:
                    closed = True; tipo = 4; m_mae = min(mae_previo, profit_apertura + spread_pips)

            # Registro de stream VELAS
            vl[nv, 0] = float(cnt); vl[nv, 1] = float(idx_off + i); vl[nv, 2] = profit_apertura
            vl[nv, 3] = mae_previo; vl[nv, 4] = mfe_actual; vl[nv, 5] = fav; vl[nv, 6] = phantom_arr[i]
            vl[nv, 7] = t_pred; vl[nv, 8] = 1.0 if closed else 0.0
            last_row = nv; nv += 1

            if closed:
                if cnt < max_trades:
                    m_mfe = max(mfe_actual, profit_apertura + spread_pips)
                    ts = calcular_t_score_trade_numba(m_mfe, m_mae, profit_apertura, t_gain, t_loss, spread_pips)
                    tr[cnt, 0] = float(idx_off + idx_in); tr[cnt, 1] = float(idx_off + i + 1)
                    tr[cnt, 2] = profit_apertura; tr[cnt, 3] = m_mae; tr[cnt, 4] = m_mfe; tr[cnt, 5] = ts
                    tr[cnt, 6] = velas_abiertas; tr[cnt, 7] = float(tipo)
                    tr[cnt, 8] = t_pred if tipo == 4 else np.nan
                    cnt += 1
                pos = 0

        elif pos == 0:
            gatillo = False
            if direccion == 1:
                if signos_in[i] < 0 and extremo_in[i] <= (sat_in[i] * armado_in) and acum_in[i] >= (extremo_in[i] * (1.0 - chasquido_in)):
                    gatillo = True
            else:
                if signos_in[i] > 0 and extremo_in[i] >= (sat_in[i] * armado_in) and acum_in[i] <= (extremo_in[i] * (1.0 - chasquido_in)):
                    gatillo = True

            if gatillo:
                autorizado = True; v_req_tmp = 0.0; z_tmp = 0.0; t_raw = 0.0
                z_tmp = (W_R[0]*z_base_in[i] + W_R[1]*in_v[i] + W_R[2]*in_a[i] + W_R[3]*math.sin(math.atan2(in_v[i], z_base_in[i])) +
                         W_R[4]*z_base_out[i] + W_R[5]*out_v[i] + W_R[6]*out_a[i] + W_R[7]*math.sin(math.atan2(out_v[i], z_base_out[i])) +
                         W_R[8]*z_macro_1[i] + W_R[9]*z_macro_2[i]) + B_R

                if z_tmp < umbral_z_ia:
                    autorizado = False
                else:
                    v_req_tmp = ((z_tmp * mad_v) + med_v) * ratio_captura

                # Admisión Cabeza B [H-45-04]
                if autorizado and cabeza_t_activa:
                    t_raw = (W_T[0]*z_base_in[i] + W_T[1]*in_v[i] + W_T[2]*in_a[i] + W_T[3]*math.sin(math.atan2(in_v[i], z_base_in[i])) +
                             W_T[4]*z_base_out[i] + W_T[5]*out_v[i] + W_T[6]*out_a[i] + W_T[7]*math.sin(math.atan2(out_v[i], z_base_out[i])) +
                             W_T[8]*z_macro_1[i] + W_T[9]*z_macro_2[i]) + B_T
                    if t_raw < T_min:
                        autorizado = False

                if autorizado:
                    pos = direccion; p_in = opens_arr[i+1]; max_v = p_in; min_v = p_in; idx_in = i + 1
                    v_req = v_req_tmp * escala_v[i]; Z_pred = z_tmp; T_hat0 = min(max(t_raw, 0.0), 1.0)
                    t_gain = 0.0; t_loss = 0.0; trade_tuvo_iteracion = False

    # Cierre forzado EOF
    if pos != 0 and trade_tuvo_iteracion and cnt < max_trades:
        idx_final = n_velas - 1
        if pos == 1:
            profit_apertura = ((opens_arr[idx_final] - p_in) * pips_mult) - spread_pips
            mae_previo = (min_v - p_in) * pips_mult; mfe_actual = (max_v - p_in) * pips_mult
        else:
            profit_apertura = ((p_in - opens_arr[idx_final]) * pips_mult) - spread_pips
            mae_previo = (p_in - max_v) * pips_mult; mfe_actual = (p_in - min_v) * pips_mult
        m_mfe = max(mfe_actual, profit_apertura + spread_pips)
        m_mae = min(mae_previo, profit_apertura + spread_pips)
        ts = calcular_t_score_trade_numba(m_mfe, m_mae, profit_apertura, t_gain, t_loss, spread_pips)
        tr[cnt, 0] = float(idx_off + idx_in); tr[cnt, 1] = float(idx_off + idx_final)
        tr[cnt, 2] = profit_apertura; tr[cnt, 3] = m_mae; tr[cnt, 4] = m_mfe; tr[cnt, 5] = ts
        tr[cnt, 6] = float(idx_final - idx_in); tr[cnt, 7] = 5.0; tr[cnt, 8] = np.nan
        if last_row >= 0: vl[last_row, 8] = 1.0
        cnt += 1

    return tr[:cnt], vl[:nv]


# ==========================================================
# 🔥 JIT WARM-UP (Precalentamiento Numba Pre-Pool)
# ==========================================================
def _warmup_jit():
    n = 100
    f32 = np.zeros(n, dtype=np.float32); p64 = np.ones(n, dtype=np.float64)
    ph = np.zeros(n, dtype=np.float32); w10 = np.zeros(10, dtype=np.float64)
    # Calentamiento simular_motor
    simular_motor(1, 0, f32, f32, f32, f32, f32, f32, f32, f32,
                  f32, f32, f32, f32, f32, f32, f32, f32,
                  p64, p64, p64, ph, 100.0, n,
                  0.5, 0.1, 0.5, 0.1, 1.2,
                  w10, 0.0, 0.5, 0.1, 10.0, 0.0, 0.60, 1.5,
                  True, w10, 0.0, 0.3,
                  2, 10, True, w10, 0.0, -1.0, p64)
    # Calentamiento ciclos
    cambios = np.zeros(n, dtype=np.int32); cambios[0] = 0
    signos = np.ones(n, dtype=np.float32)
    acum = calcular_acum_ciclo_numba(f32, cambios)
    calcular_extremos_numba(signos, acum, cambios)
    mx, mn = obtener_extremos_ciclo_numba(cambios, acum, signos, 0)
    rolling_median_causal_numba(mn, direction=-1, memoria_fifo=MEMORIA_FIFO)
    rolling_median_causal_numba(mx, direction=1, memoria_fifo=MEMORIA_FIFO)
    eval_robustez_numba_v6(f32, f32, f32, f32, 5)


# ==============================================================================
# 🧮 UTILIDADES DE DATOS Y MÉTRICAS
# ==============================================================================
def calc_canal(ARR, col_base, col_acum, modo):
    signos = np.sign(ARR[col_base]).astype(np.float32)
    mask_zero = (signos == 0)
    if mask_zero.any():
        idx_validos = np.where(~mask_zero)[0]
        if len(idx_validos) > 0:
            if mask_zero[0]: signos[0] = 1.0
            idx_arr = np.arange(len(signos))
            idx_arr[mask_zero] = 0
            idx_arr = np.maximum.accumulate(idx_arr)
            signos = signos[idx_arr]
        else:
            signos[:] = 1.0
    cambios = np.concatenate(([0], (signos[1:] != signos[:-1]).astype(np.int32))).astype(np.int32)
    ciclos = cambios.cumsum().astype(np.int32)
    acum = calcular_acum_ciclo_numba(ARR[col_acum].copy(), cambios)
    extremo = calcular_extremos_numba(signos, acum, cambios)
    max_v, min_v = obtener_extremos_ciclo_numba(ciclos, acum, signos, int(ciclos[-1]))
    if modo == 'inf': sat_series = rolling_median_causal_numba(min_v, -1, MEMORIA_FIFO)
    else: sat_series = rolling_median_causal_numba(max_v, 1, MEMORIA_FIFO)
    return signos, extremo, sat_series[ciclos], acum


def geometria(N):
    g = TAB.geometria(N)
    par = {f: (v[2], v[3]) for f, v in g['folds'].items()}
    a, b, ciega = TAB.ventana_portafolio(N)
    return g['test'], par, (a, b), ciega


def _f32(tr, col):
    return np.ascontiguousarray(tr[:, col]).astype(np.float32)


def evaluar_core(tr, min_trades):
    return eval_robustez_numba_v6(_f32(tr, 4), _f32(tr, 3), _f32(tr, 2), _f32(tr, 5), min_trades)


def _escritura_atomica_df(df, ruta, parquet):
    tmp = ruta + ".tmp"
    if parquet: df.to_parquet(tmp, index=False, compression='zstd')
    else: df.to_csv(tmp, index=False, encoding='utf-8-sig')
    os.replace(tmp, ruta)


def df_trades(tr, sim, dir_, rank, fold, superv):
    return pd.DataFrame({
        'Simbolo': sim, 'Dir': dir_, 'Rank': rank, 'Fold': fold, 'Superv': np.int8(1 if superv else 0),
        'Trade_Id': np.arange(len(tr), dtype=np.int32),
        'Idx_In': tr[:, 0].astype(np.int64), 'Idx_Out': tr[:, 1].astype(np.int64),
        'Profit_Pips': tr[:, 2], 'MAE_Pips': tr[:, 3], 'MFE_Pips': tr[:, 4], 'T_Score': tr[:, 5],
        'Velas_Vida': tr[:, 6], 'Tipo_Cierre': tr[:, 7].astype(np.int8), 'T_Pred_Cierre': tr[:, 8]
    })


def df_velas(vl, sim, dir_, rank):
    return pd.DataFrame({
        'Simbolo': sim, 'Dir': dir_, 'Rank': rank,
        'Trade_Id': vl[:, 0].astype(np.int32), 'Idx': vl[:, 1].astype(np.int64),
        'Profit_Flot': vl[:, 2], 'MAE': vl[:, 3], 'MFE': vl[:, 4],
        'Favorable': vl[:, 5].astype(np.int8), 'Phantom': vl[:, 6].astype(np.int8),
        'T_Pred': vl[:, 7], 'Cierra': vl[:, 8].astype(np.int8)
    })


# ==============================================================================
# ⚖️ PARIDAD CONTRA EL CSV DE FASE 4 V12.0
# ==============================================================================
def chequear_paridad(row, r_s, r_b):
    det = []

    def cmp(nombre, v45, dec=None):
        try:
            v4 = float(row[nombre])
        except Exception:
            det.append(f"{nombre}:no_numerico_en_CSV"); return
        v45 = round(float(v45), dec) if dec is not None else float(v45)
        if abs(v4 - v45) > TOL_PARIDAD:
            det.append(f"{nombre}: F4={v4} vs 4.5={v45}")

    cmp('Trades_OOS_Superv', int(r_s[10])); cmp('Trades_OOS_Ridge', int(r_b[10]))
    cmp('T-SCORE_OOS', r_s[12], 2); cmp('PF_OOS_Superv', r_s[7], 2); cmp('WR_OOS_Superv_%', r_s[6], 1)
    cmp('MaxDD_OOS_Superv', r_s[8], 1); cmp('MedProfitPips_OOS_Superv', r_s[3], 1)
    rech45 = bool(r_b[0] <= 0.0); rech4 = str(row['PF_OOS_Ridge']) == 'RECHAZADO'
    if rech45 != rech4:
        det.append(f"Base_Rechazado: F4={rech4} vs 4.5={rech45}")
    elif not rech45:
        cmp('PF_OOS_Ridge', r_b[7], 2); cmp('WR_OOS_Ridge_%', r_b[6], 1)
        cmp('MaxDD_OOS_Ridge', r_b[8], 1); cmp('MedProfitPips_OOS_Ridge', r_b[3], 1)
    return len(det) == 0, " | ".join(det)


def _metricas_motor(prefijo, tr, min_trades):
    r = evaluar_core(tr, min_trades)
    return {f'{prefijo}_n': int(r[10]), f'{prefijo}_Score': float(r[0]), f'{prefijo}_T': float(r[12]),
            f'{prefijo}_PF': float(r[7]), f'{prefijo}_WR': float(r[6]), f'{prefijo}_MaxDD': float(r[8]),
            f'{prefijo}_MedProfit': float(r[3]), f'{prefijo}_Rechazado': bool(r[0] <= 0.0)}, r


# ==============================================================================
# 🔄 PROCESAMIENTO POR SÍMBOLO
# ==============================================================================
def procesar_simbolo(sim, ctx):
    print("\n" + "█" * 90)
    print(f"🪙 FASE 4.5 {FASE45_VERSION} — ETAPA A (GEMELO DIGITAL SUPERSET): {sim}")
    print("█" * 90)
    ruta_txt = os.path.join(DIR_ENTRADA, f"Cerebro_MQL5_{TAG_ARCHIVOS_FASE4}_{sim}.txt")
    ruta_pq = os.path.join(DIR_ENTRADA, f"nexus_df_salida_3D_{sim}_MultiZ.parquet")
    ruta_csv = os.path.join(DIR_ENTRADA, f"Reporte_OOS_Phase4_{TAG_ARCHIVOS_FASE4}_Superv_{sim}.csv")

    if not os.path.exists(ruta_txt):
        print(f"   ⚠️ [{sim}] sin .txt ({ruta_txt}). Saltado."); return 'sin_txt'
    if not os.path.exists(ruta_pq):
        print(f"   ⚠️ [{sim}] sin parquet ({ruta_pq}). Saltado."); return 'sin_parquet'

    try:
        meta, motores, errores = leer_cerebro(ruta_txt, RANKS_A_SIMULAR)
    except ErrorSimbolo as e:
        print(f"   ⛔ [{sim}] {e}"); _registrar_descarte(sim, 'ALL', e.estado); return e.estado

    for d, r, causa in errores:
        _registrar_descarte(sim, f"{d}#{r}", causa)

    spread = round(float(meta['spread']), 4)
    n_filas = pq.ParquetFile(ruta_pq).metadata.num_rows

    try:
        TAB.verificar_sello(meta['tablero'] or "", n_total=n_filas, origen=f"cabecera del .txt ({ruta_txt})")
    except TAB.ErrorSello as e:
        print(f"   ⛔ [{sim}] {e}"); _registrar_descarte(sim, 'ALL', 'Sello_Fase4_invalido'); return 'tablero_desalineado'

    names = pq.ParquetFile(ruta_pq).schema.names
    cols_up = {n.upper(): n for n in names}
    for k in (COL_TIEMPO, *COLS_OHLC.values()):
        if k not in cols_up:
            raise RuntimeError(f"🛑 FATAL [{sim}]: columna obligatoria '{k}' ausente en el parquet (Fase 1&2).")
    c_t = cols_up[COL_TIEMPO]; c_o = cols_up['OPENM1']; c_h = cols_up['HIGHM1']; c_l = cols_up['LOWM1']; c_p = cols_up['PHANTOM']

    validos = []
    for m in motores:
        try:
            m['cols'] = resolver_columnas(m, cols_up)
            validos.append(m)
        except ErrorConfig as e:
            _registrar_descarte(sim, f"{m['Dir']}#{m['Rank']}", str(e))
    if not validos:
        print(f"   ⚠️ [{sim}] sin motores válidos."); return 'sin_motores'

    req = {c_t, c_o, c_h, c_l, c_p}
    for m in validos:
        req.update(m['cols'].values())
    df = pd.read_parquet(ruta_pq, columns=sorted(req)).reset_index(drop=True)
    N = len(df)

    t = pd.to_datetime(df[c_t]).to_numpy('datetime64[ns]')
    if ctx['t_ref'] is None:
        ctx['t_ref'] = t.copy(); ctx['t_ref_sim'] = sim
    elif len(t) != len(ctx['t_ref']) or not np.array_equal(t, ctx['t_ref']):
        raise RuntimeError(f"🛑 FATAL [Alineación]: vector 'Time' de {sim} no coincide con el de {ctx['t_ref_sim']}.")

    opens = df[c_o].to_numpy(dtype=np.float64, copy=True)
    highs = df[c_h].to_numpy(dtype=np.float64, copy=True)
    lows = df[c_l].to_numpy(dtype=np.float64, copy=True)
    phantom = df[c_p].to_numpy(dtype=np.float32, copy=True)

    if not (np.isfinite(opens).all() and np.isfinite(highs).all() and np.isfinite(lows).all() and np.isfinite(phantom).all()):
        print(f"   ⛔ [{sim}] OHLC/Phantom con NaN/Inf."); _registrar_descarte(sim, 'ALL', 'OHLC_no_finito'); return 'datos_invalidos'

    ARR = {c: df[c].to_numpy(dtype=np.float32, copy=True) for c in req if c not in (c_t, c_o, c_h, c_l, c_p)}
    del df; gc.collect()

    pips_mult = 100.0 if 'JPY' in sim else 10000.0
    TEST, vent_par, vent_pf, ciega = geometria(N)

    if ctx['geom'] is None:
        ctx['geom'] = {
            'N': N, 'TEST': TEST, 'vent_par': {k: list(v) for k, v in vent_par.items()},
            'vent_pf': list(vent_pf), 'ciega': bool(ciega), 'n_ef': TAB.n_efectivo(N),
            'reserva': TAB.RESERVA_FINAL, 'tab_hash': TAB.hash_params(), 'tab_ver': TAB.TABLERO_VERSION
        }

    if not ciega:
        print(f"   ⚠️ [{sim}] VENTANA DE PORTAFOLIO NO CIEGA: {list(vent_pf)} se solapa con OOS de Fase 4.")
    a_min = min([v[0] for v in vent_par.values()] + [vent_pf[0]])
    print(f"   📐 N={N} | TEST={TEST} | Paridad F1={vent_par[1]} F2={vent_par.get(2)} | Portafolio={vent_pf} | spread={spread:.4f} | motores={len(validos)} | ESCALON={meta['escalon']}")

    csv_par = {}
    if CHEQUEAR_PARIDAD and os.path.exists(ruta_csv):
        dfc = pd.read_csv(ruta_csv, encoding='utf-8-sig')
        try:
            TAB.verificar_sello(dfc, n_total=n_filas, origen=f"CSV de Fase 4 ({ruta_csv})")
        except TAB.ErrorSello as e:
            print(f"   ⛔ [{sim}] {e}"); _registrar_descarte(sim, 'ALL', 'Sello_CSV_Fase4_invalido'); return 'tablero_desalineado'
        for _, r in dfc.iterrows():
            csv_par[(str(r['Dir']), int(r['Rank_IA']))] = r

    cache = OrderedDict()

    def canal(cb, ca, modo):
        k = (cb, ca, modo)
        if k in cache:
            cache.move_to_end(k); return cache[k]
        v = calc_canal(ARR, cb, ca, modo); cache[k] = v
        while len(cache) > MAX_CACHE_CANALES: cache.popitem(last=False)
        return v

    filas, lst_tr, lst_vl = [], [], []
    act_arr_sim = None   # [LAB-V7] actividad de 60 velas, una vez por símbolo si algún motor trae Ridge de tamaño
    for m in validos:
        dir_ = m['Dir']; rank = m['Rank']; fold = m['Fold']; tag_m = f"{dir_}#{rank}"
        try:
            if fold not in vent_par:
                raise ErrorConfig("fold_fuera_de_rango")
            cols = m['cols']; dir_code = 1 if dir_ == 'LONG' else -1
            modo_in = 'inf' if dir_code == 1 else 'sup'; modo_out = 'sup' if dir_code == 1 else 'inf'
            sig_i, ext_i, sat_i, ac_i = canal(cols['base_in'], cols['acum_in'], modo_in)
            sig_o, ext_o, sat_o, ac_o = canal(cols['base_out'], cols['acum_out'], modo_out)
            zbi = ARR[cols['zbase_in']]; viv = ARR[cols['v_in']]; via = ARR[cols['a_in']]
            zbo = ARR[cols['zbase_out']]; vov = ARR[cols['v_out']]; voa = ARR[cols['a_out']]
            zm1 = ARR[cols['macro1']]; zm2 = ARR[cols['macro2']]
            chk = (sig_i, ext_i, sat_i, ac_i, sig_o, ext_o, sat_o, ac_o, zbi, viv, via, zbo, vov, voa, zm1, zm2)
            if not all(np.isfinite(x[a_min:]).all() for x in chk):
                raise ErrorConfig("NaN_Inf_en_ventana")
        except ErrorConfig as e:
            _registrar_descarte(sim, tag_m, str(e)); continue
        except KeyError as e:
            _registrar_descarte(sim, tag_m, f"KeyError:{e}"); continue

        ml, sv = m['ml'], m['sv']
        arm_i, chq_i = m['In']['armado'], m['In']['chasquido']
        arm_o, chq_o = m['Out']['armado'], m['Out']['chasquido']

        tam = m.get('tam')   # [LAB-V7]
        if tam is None:
            ESC_m = np.ones(N, dtype=np.float64)
        else:
            if act_arr_sim is None:
                act_arr_sim = lab_actividad_nb(opens, pips_mult, ACT_VENTANA)
            X10_m = x10_desde_arreglos(zbi, viv, via, zbo, vov, voa, zm1, zm2) if tam['modo'] == 'A' else None
            ESC_m = escala_desde_parametros(tam, X10_m, act_arr_sim)
            if not np.isfinite(ESC_m).all():
                _registrar_descarte(sim, tag_m, "Lab_escala_no_finita"); continue

        def S(a, b):
            return (sig_i[a:b], ext_i[a:b], sat_i[a:b], ac_i[a:b], sig_o[a:b], ext_o[a:b], sat_out[a:b] if 'sat_out' in locals() else sat_o[a:b], ac_o[a:b],
                    zbi[a:b], viv[a:b], via[a:b], zbo[a:b], vov[a:b], voa[a:b], zm1[a:b], zm2[a:b],
                    opens[a:b], highs[a:b], lows[a:b])

        def correr(a, b, superv):
            return simular_motor(dir_code, a, *S(a, b), phantom[a:b], pips_mult, b - a,
                                 arm_i, chq_i, arm_o, chq_o, spread,
                                 ml['w'], ml['bias'], ml['med_v'], ml['mad_v'], ml['atrac_t'], ml['umbral'],
                                 ml['ratio_captura'], ml['tolerancia_vida'],
                                 superv, sv['w'], sv['bias'], sv['k'],
                                 sv['inmunidad_velas'], sv['n_features'],
                                 ml['cabeza_t_activa'], ml['w_T'], ml['bias_T'], ml['t_min'], ESC_m[a:b])

        a_pf, b_pf = vent_pf
        try:
            tr_s, vl_s = correr(a_pf, b_pf, True)
            tr_b, _ = correr(a_pf, b_pf, False)
        except Exception as e:
            _registrar_descarte(sim, tag_m, f"Excepcion_simulacion:{type(e).__name__}"); continue

        fila = {'Simbolo': sim, 'Dir': dir_, 'Rank': rank, 'Fold': fold, 'Estado': 'OK', 'Escalon': meta['escalon'],
                'Spread': spread, 'K_Abortar': sv['k']}
        d_s, r_s_pf = _metricas_motor('PF_S', tr_s, MIN_OPS_MOTOR_PF); d_b, _ = _metricas_motor('PF_B', tr_b, MIN_OPS_MOTOR_PF)
        fila.update(d_s); fila.update(d_b)
        fila.update({'Paridad_Chequeada': False, 'Paridad_OK': None, 'Paridad_Detalle': '',
                     'Par_n_F4': np.nan, 'Par_n_45': np.nan, 'Par_T_F4': np.nan, 'Par_T_45': np.nan})

        row = csv_par.get((dir_, rank))
        if row is not None:
            a_p, b_p = vent_par[fold]
            ts_p, _ = correr(a_p, b_p, True); tb_p, _ = correr(a_p, b_p, False)
            r_s = evaluar_core(ts_p, MIN_OPS_OOS_EXPORT); r_b = evaluar_core(tb_p, MIN_OPS_BASE)
            ok, det = chequear_paridad(row, r_s, r_b)
            if int(row['Fold']) != fold:
                ok = False; det = (det + " | " if det else "") + f"Fold: F4={int(row['Fold'])} vs .txt={fold}"
            fila.update({'Paridad_Chequeada': True, 'Paridad_OK': bool(ok), 'Paridad_Detalle': det,
                         'Par_n_F4': float(row['Trades_OOS_Superv']), 'Par_n_45': float(int(r_s[10])),
                         'Par_T_F4': float(row['T-SCORE_OOS']), 'Par_T_45': round(float(r_s[12]), 2)})
        elif csv_par:
            fila['Paridad_Detalle'] = 'sin_fila_en_CSV_de_Fase4'

        filas.append(fila)
        lst_tr.append(df_trades(tr_s, sim, dir_, rank, fold, True))
        lst_tr.append(df_trades(tr_b, sim, dir_, rank, fold, False))
        lst_vl.append(df_velas(vl_s, sim, dir_, rank))

    if not filas:
        print(f"   ⚠️ [{sim}] ningún motor se pudo simular."); return 'sin_motores'

    os.makedirs(DIR_SALIDA, exist_ok=True)
    df_m = pd.DataFrame(filas)
    _escritura_atomica_df(df_m, os.path.join(DIR_SALIDA, f"motores_{sim}.csv"), parquet=False)
    _escritura_atomica_df(pd.concat(lst_tr, ignore_index=True), os.path.join(DIR_SALIDA, f"trades_{sim}.parquet"), parquet=True)
    _escritura_atomica_df(pd.concat(lst_vl, ignore_index=True), os.path.join(DIR_SALIDA, f"velas_{sim}.parquet"), parquet=True)

    n_chk = int(df_m['Paridad_Chequeada'].sum()); n_ok = int((df_m['Paridad_OK'] == True).sum())
    print(f"   ✅ [{sim}] motores simulados: {len(filas)} | paridad: {n_ok}/{n_chk} OK"
          + (f"  ⚠️ {n_chk - n_ok} DISCREPANCIAS (ver Paridad_Detalle)" if n_chk != n_ok else ""))
    del ARR, cache; gc.collect()
    ctx['paridad_chk'] += n_chk; ctx['paridad_ok'] += n_ok
    return 'ok'


# ==============================================================================
# 🚀 MAIN
# ==============================================================================
def main():
    set_num_threads(1)
    t0 = time.perf_counter()
    print(f"🚀 FASE 4.5 {FASE45_VERSION} — ETAPA A (GEMELO DIGITAL SUPERSET) | core v{FORMULAS_CORE_VERSION} | ESCALÓN: {ESCALON}")
    _warmup_jit()

    ctx = {'t_ref': None, 't_ref_sim': None, 'geom': None, 'paridad_chk': 0, 'paridad_ok': 0}
    for sim in LISTA_SIMBOLOS:
        estado = procesar_simbolo(sim, ctx)
        if estado == 'ok': _cobertura['ok'] += 1
        else: _cobertura.setdefault(estado, []).append(sim)
        gc.collect()

    print("\n" + "=" * 90)
    print(f"📊 [COBERTURA] símbolos simulados: {_cobertura['ok']}/{len(LISTA_SIMBOLOS)}")
    for k, v in _cobertura.items():
        if k != 'ok' and v: print(f"   ↳ {k}: {v}")
    if ctx['paridad_chk']:
        print(f"⚖️ [PARIDAD vs Fase 4] {ctx['paridad_ok']}/{ctx['paridad_chk']} motores en paridad exacta")
    if _descartes:
        print("🔬 [FORENSE] configuraciones descartadas (símbolo|dirección#rank|causa):")
        for k, c in sorted(_descartes.items(), key=lambda x: -x[1]): print(f"   - {k}: {c}")
    print("=" * 90)

    if _cobertura['ok'] == 0:
        raise RuntimeError(f"🛑 FATAL: CERO símbolos simulados. Verificar TAG_ARCHIVOS_FASE4 ({TAG_ARCHIVOS_FASE4}) y parquets.")

    os.makedirs(DIR_SALIDA, exist_ok=True)
    pd.DataFrame({'Time': ctx['t_ref']}).to_parquet(os.path.join(DIR_SALIDA, "tiempo.parquet"), index=False)
    meta = {
        'fase45_version': FASE45_VERSION, 'core_version': FORMULAS_CORE_VERSION,
        'tag_fase4': TAG_ARCHIVOS_FASE4, 'escalon': ESCALON, 'geometria': ctx['geom'],
        'simbolos_ok': _cobertura['ok'], 'paridad_chequeada': ctx['paridad_chk'],
        'paridad_ok': ctx['paridad_ok'], 'cobertura': {k: v for k, v in _cobertura.items() if k != 'ok'},
        'segundos': round(time.perf_counter() - t0, 1)
    }
    with open(os.path.join(DIR_SALIDA, "meta.json"), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"💾 Etapa A completa -> {DIR_SALIDA}/ | {meta['segundos']} s. Siguiente: Fase_4_5b_V11_0.py (Etapa B: curvas de portafolio).")


if __name__ == "__main__":
    main()