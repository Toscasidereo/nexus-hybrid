# ==============================================================================
# 🎛️ nexus_tablero.py — TABLERO ÚNICO DE CONFIGURACIÓN (GEOMETRÍA WFO + RESERVA CIEGA)
# 🛡️ CÓDEX NEXUS-HYBRID V3.0 — AXIOMA 3: lo que debe coincidir entre fases vive en UN solo archivo.
# ==============================================================================
# Qué es: el ÚNICO lugar donde se definen los folds, la proporción IS/OOS, la reserva ciega y la memoria FIFO.
#         Fase 3, Fase 4 y Fase 4.5 lo IMPORTAN; ninguna vuelve a definir esas constantes ni a recalcular
#         la geometría (cierra H-12: geometría duplicada Fase 3 <-> Fase 4).
# Qué NO es: no contiene matemática de scoring (eso es nexus_formulas_core.py) ni decide nada solo.
#
# 📋 BITÁCORA V1.0.0:
#    - Defaults IDÉNTICOS al comportamiento histórico (N_FOLDS=2, RATIO=2.0, RESERVA_FINAL=0.0, MEMORIA_FIFO=100):
#      importar este módulo no cambia ningún resultado hasta que el CRO edite los números de abajo.
#    - RESERVA_FINAL: fracción FINAL del archivo que Fase 3 y Fase 4 NO cargan (ventana ciega de Fase 4.5).
#      Ejemplo "2/4 IS · 1/4 OOS Fase 4 · último 1/4 ciego":  N_FOLDS=1, RATIO_TRAIN_TEST=2.0, RESERVA_FINAL=0.25.
#    - SELLO: cada fase estampa en sus salidas lo que REALMENTE usó (hash de parámetros, N total, N efectivo, reserva).
#      La fase siguiente lo verifica y se NIEGA a continuar si no coincide (otra geometría, otro archivo, reserva ignorada).
#    - ⚠️ Cambiar cualquier número invalida resultados previos: Fase 3 debe volver a correr (el sello lo hace explícito).
#    - ⚠️ La reserva "se gasta": si se ajusta la configuración mirando el resultado de 4.5, deja de ser ciega.
#    - Aislamiento LÓGICO (este módulo). Para certificación formal ante el directorio, partir el archivo por fecha
#      (aislamiento físico) sigue siendo más creíble.
# ==============================================================================
import hashlib
import json
import re

TABLERO_VERSION = "1.0.0"

# ==============================================================================
# 🎚️ PERILLAS (editar SOLO acá)
# ==============================================================================
N_FOLDS = 2                 # nº de folds Walk-Forward
RATIO_TRAIN_TEST = 2.0      # tamaño IS / tamaño OOS dentro de cada fold
RESERVA_FINAL = 0.0         # fracción final del archivo reservada (ciega). 0.0 = sin reserva (comportamiento histórico)
MEMORIA_FIFO = 100          # memoria de la mediana rodante del saturador (debe ser idéntica en todas las fases)
EXIGIR_SELLO = True         # True: una fase se niega a seguir si la anterior no estampó sello (poner False SOLO de forma explícita y temporal)


class ErrorTablero(Exception):
    """Configuración inválida o geometría imposible para el N dado."""


class ErrorSello(Exception):
    """El sello de una fase anterior no coincide con el tablero actual (o falta)."""


# ==============================================================================
# 📐 GEOMETRÍA
# ==============================================================================
def _validar():
    if not (isinstance(N_FOLDS, int) and N_FOLDS >= 1):
        raise ErrorTablero(f"N_FOLDS inválido: {N_FOLDS!r}")
    if not RATIO_TRAIN_TEST > 0:
        raise ErrorTablero(f"RATIO_TRAIN_TEST inválido: {RATIO_TRAIN_TEST!r}")
    if not (0.0 <= RESERVA_FINAL < 0.9):
        raise ErrorTablero(f"RESERVA_FINAL fuera de [0, 0.9): {RESERVA_FINAL!r}")
    if not (isinstance(MEMORIA_FIFO, int) and MEMORIA_FIFO >= 5):
        raise ErrorTablero(f"MEMORIA_FIFO inválida: {MEMORIA_FIFO!r}")


def n_efectivo(n_total):
    """Velas que Fase 3 y Fase 4 SÍ cargan (el resto es la reserva ciega)."""
    _validar()
    return int(int(n_total) * (1.0 - RESERVA_FINAL))


def recortar(df):
    """Aplica la reserva al cargar el archivo: devuelve el mismo DataFrame si no hay reserva, o las primeras n_ef filas."""
    n_ef = n_efectivo(len(df))
    return df if n_ef == len(df) else df.iloc[:n_ef].copy()


def geometria(n_total):
    """
    Geometría WFO única para TODAS las fases. Con RESERVA_FINAL=0 reproduce EXACTAMENTE la fórmula histórica:
        TEST = int(N / (RATIO + N_FOLDS)); TRAIN = int(TEST * RATIO)
        fold f (1-based): train=[(f-1)*TEST, +TRAIN)  test=[fin_train, +TEST)
    Devuelve dict con n_total, n_ef, test, train, folds{f:(s_tr,e_tr,s_te,e_te)}, reserva(a,b)|None, ciega(bool).
    """
    _validar()
    n_total = int(n_total); n_ef = n_efectivo(n_total)
    test = int(n_ef / (RATIO_TRAIN_TEST + N_FOLDS)); train = int(test * RATIO_TRAIN_TEST)
    if test < 1 or train < 1:
        raise ErrorTablero(f"N efectivo={n_ef} demasiado chico para N_FOLDS={N_FOLDS}, RATIO={RATIO_TRAIN_TEST}")
    folds = {}
    for f in range(1, N_FOLDS + 1):
        s_tr = (f - 1) * test; e_tr = s_tr + train; s_te = e_tr; e_te = s_te + test
        if e_te > n_ef:
            raise ErrorTablero(f"fold {f}: end_test={e_te} excede N efectivo={n_ef}")
        folds[f] = (s_tr, e_tr, s_te, e_te)
    return {'n_total': n_total, 'n_ef': n_ef, 'test': test, 'train': train, 'folds': folds,
            'reserva': (n_ef, n_total) if n_total > n_ef else None, 'ciega': n_total > n_ef}


def ventana_portafolio(n_total):
    """
    Ventana que usa Fase 4.5 para componer el portafolio.
    Con reserva: (n_ef, n_total, True)  -> tramo CIEGO (Fases 3 y 4 no lo cargaron).
    Sin reserva: (N-TEST, N, False)     -> comportamiento histórico; NO es ciega (se solapa con el OOS de Fase 4). 4.5 debe advertirlo.
    """
    g = geometria(n_total)
    if g['reserva'] is not None:
        return g['reserva'][0], g['reserva'][1], True
    return g['n_total'] - g['test'], g['n_total'], False


# ==============================================================================
# 🔏 SELLO DE TRAZABILIDAD ENTRE FASES
# ==============================================================================
def hash_params():
    """Hash de los parámetros que DEBEN coincidir entre fases (no incluye la versión del módulo)."""
    base = {'N_FOLDS': N_FOLDS, 'RATIO_TRAIN_TEST': float(RATIO_TRAIN_TEST),
            'RESERVA_FINAL': float(RESERVA_FINAL), 'MEMORIA_FIFO': MEMORIA_FIFO}
    return hashlib.sha1(json.dumps(base, sort_keys=True).encode('utf-8')).hexdigest()[:12]


def sello(n_total):
    """Columnas de sello para estampar en un CSV (todas las filas llevan el mismo valor)."""
    n_total = int(n_total)
    return {'Tab_Ver': TABLERO_VERSION, 'Tab_Hash': hash_params(), 'Tab_N_Total': n_total, 'Tab_N_Ef': n_efectivo(n_total),
            'Tab_Reserva': float(RESERVA_FINAL), 'Tab_N_Folds': N_FOLDS, 'Tab_Ratio': float(RATIO_TRAIN_TEST)}


def sello_linea(n_total):
    """Línea de texto parseable para la cabecera de los .txt."""
    s = sello(n_total)
    return (f"TABLERO v{s['Tab_Ver']} hash={s['Tab_Hash']} n_total={s['Tab_N_Total']} n_ef={s['Tab_N_Ef']} "
            f"reserva={s['Tab_Reserva']} n_folds={s['Tab_N_Folds']} ratio={s['Tab_Ratio']}")


def parsear_linea(texto):
    """Extrae el sello de una línea/cabecera de texto. None si no hay sello."""
    m = re.search(r"TABLERO\s+v[\w.]+\s+hash=(\w+)\s+n_total=(\d+)\s+n_ef=(\d+)\s+reserva=([0-9.]+)", str(texto))
    if not m:
        return None
    return {'hash': m.group(1), 'n_total': int(m.group(2)), 'n_ef': int(m.group(3)), 'reserva': float(m.group(4))}


def _campos(fuente):
    if isinstance(fuente, str):
        return parsear_linea(fuente)
    if hasattr(fuente, 'columns'):                      # DataFrame de un CSV
        cols = ['Tab_Hash', 'Tab_N_Total', 'Tab_N_Ef', 'Tab_Reserva']
        if any(c not in fuente.columns for c in cols):
            return None
        d = {}
        for c in cols:
            u = fuente[c].dropna().unique()
            if len(u) != 1:
                raise ErrorSello(f"sello inconsistente: '{c}' tiene {len(u)} valores distintos en el mismo archivo")
            d[c] = u[0]
        return {'hash': str(d['Tab_Hash']), 'n_total': int(d['Tab_N_Total']), 'n_ef': int(d['Tab_N_Ef']), 'reserva': float(d['Tab_Reserva'])}
    return dict(fuente)


def verificar_sello(fuente, n_total=None, origen="fuente"):
    """
    Verifica el sello de una fase anterior contra el tablero actual.
    Retorna 'ok' | 'sin_sello_tolerado'. Lanza ErrorSello si falta (y EXIGIR_SELLO) o no coincide.
    n_total: nº de filas REAL del parquet que la fase actual acaba de leer (detecta archivo distinto).
    """
    d = _campos(fuente)
    if d is None:
        if EXIGIR_SELLO:
            raise ErrorSello(f"{origen}: sin sello de tablero. Regenerar con la fase actualizada "
                             f"(o EXIGIR_SELLO=False, explícito y temporal).")
        return 'sin_sello_tolerado'
    if d['hash'] != hash_params():
        raise ErrorSello(f"{origen}: hash de tablero distinto (la fase anterior usó {d['hash']}, el tablero actual es {hash_params()}). "
                         f"Se corrió con otra geometría: re-correr la fase anterior.")
    if n_total is not None:
        if d['n_total'] != int(n_total):
            raise ErrorSello(f"{origen}: N total distinto (fase anterior {d['n_total']}, parquet actual {int(n_total)}): no es el mismo archivo.")
        if d['n_ef'] != n_efectivo(n_total):
            raise ErrorSello(f"{origen}: N efectivo distinto (fase anterior {d['n_ef']}, esperado {n_efectivo(n_total)}): la reserva no se aplicó igual.")
    return 'ok'
