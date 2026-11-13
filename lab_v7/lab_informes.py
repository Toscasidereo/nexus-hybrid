# ==============================================================================
# NEXUS LAB-V8 — INFORMES DE FASE 4: censo, vista acotada, resumen y manifiesto
# Carpeta: lab_v7/ (rama lab-v8)
# ==============================================================================
# 📋 BITÁCORA
#   V0.1 (2026-11-10) — Creación. Orden del CRO: "LUZ VERDE: INFORMES FASE 4 (censo, resumen, manifiesto)" más un archivo acotado
#     (25 o 50 por fold y dirección) para lectura directa. Requisito: informes auditables, trazables y utilizables por dos lectores
#     (el CRO y el sistema).
#     Qué hace: NO calcula nada del laboratorio. Solo ordena y escribe valores que Fase_4_lab.py ya calculó.
#       - Censo_Fase4_{tag}_{SIMBOLO}.csv : una fila por configuración LEÍDA por Fase 4 (pase o no), con la etapa donde cayó.
#       - Vista_Fase4_{tag}_{SIMBOLO}.csv : las primeras N (NEXUS_LAB_VISTA_TOP, defecto 50) por dirección y fold, columnas reducidas.
#       - Resumen_Fase4_{tag}.md          : embudo, Ridge 1, Ridge 2, nulo de entrada y exportados. Se calcula SOLO desde los censos
#                                           del disco (cualquier cifra se puede recalcular): `python lab_informes.py TAG [carpeta]`.
#       - Manifiesto_Fase4_{tag}.json     : una entrada por corrida: código (sha1, commit), tablero, geometría, datos, salidas (sha1).
#     Qué NO hace: no cambia selección, entrenamiento, cerebro ni Reporte_OOS. Con NEXUS_LAB_CENSO=0 (defecto del código) este
#     módulo ni se importa.
#     Límites declarados: las configuraciones que caen antes del OOS no tienen números de OOS (solo la causa). Las configuraciones
#     de un símbolo se parecen entre sí: el censo muestra tendencias, no pruebas independientes.
# ==============================================================================
import os, re, sys, json, glob, time, hashlib, platform, datetime, functools, threading
import numpy as np
import pandas as pd

INFORMES_VERSION = '0.1'
ERRORES = {}                      # causa -> veces. Un fallo de este módulo NUNCA debe cambiar ni cortar la corrida: se cuenta y se informa.
_lock_err = threading.Lock()


def anotar_error(donde, e):
    with _lock_err:
        k = f"{donde}:{type(e).__name__}:{str(e)[:120]}"; ERRORES[k] = ERRORES.get(k, 0) + 1


def _seguro(defecto):
    """Las funciones llamadas desde dentro del torneo no lanzan: devuelven `defecto()` y cuentan el error (Jidoka: excepción contenida y visible)."""
    def deco(fn):
        @functools.wraps(fn)
        def envoltura(*a, **k):
            try: return fn(*a, **k)
            except Exception as e:
                anotar_error(fn.__name__, e); return defecto()
        return envoltura
    return deco


def reloj():
    return time.perf_counter()
R_NOMBRES = ('score', 'med_mfe', 'med_mae', 'med_pips', 'efic', 'ratio_mfe_mae', 'wr', 'pf', 'maxdd', 'rf', 'n', 'sortino', 'med_T')
EXTRAS = ('sf', 'v7', 'v52', 'pips', 'C1', 'C2', 'C3', 'C4', 'alfa', 'n_sen')   # [JUEZ-V52] 'v52' (2026-11-13)
ETAPAS = ('1_preparacion', '2_ridge1', '3_tamano', '4_base_is', '5_ridge2', '6_compuerta_oos')
BLOQUES = ('is_base', 'is_sup', 'oos_base', 'oos_sup')
COLS_ID = ['simbolo', 'dir', 'fold', 'rank_f3', 'idx_f3', 'base_in', 'acum_in', 'arm_in', 'chq_in', 'base_out', 'acum_out', 'arm_out', 'chq_out']
COLS_EMBUDO = ['estado', 'etapa', 'causa', 'rank_ia', 'en_cerebro']
COLS_R1 = ['ml_n', 'ml_wr', 'ml_med_pips', 'ml_pips', 'r1_med_v', 'r1_mad_v', 'r1_atrac_t', 'r1_r2_T', 'r1_T_min']
COLS_R2 = ['r2_n_fotos', 'r2_n_trades', 'r2v_corr_max', 'K_opt', 'retencion_raw', 'retencion', 'score_armonico', 'score_flujo', 'clave_rank']
COLS_VER = ['ridge2', 'd_pf', 'd_med_pips', 'd_pips', 't_seg']
_ID_F3 = {'Simbolo', 'Dir', 'Fold', 'Rank', '⚖️ BASE IN', '📊 ACUM IN', '⚙️ Arm_IN', '⚡ Chq_IN', '⚖️ BASE OUT', '📊 ACUM OUT', '⚙️ Arm_OUT', '⚡ Chq_OUT',
          '|', '||', '|||', 'Core_Ver'}


def _num(v):
    try: return float(str(v).replace('%', '').strip())
    except (TypeError, ValueError): return float('nan')


def _ascii(s):
    return re.sub(r'[^A-Za-z0-9]+', '_', str(s)).strip('_')


def sha1_archivo(ruta, bloque=1 << 20):
    h = hashlib.sha1()
    with open(ruta, 'rb') as f:
        for b in iter(lambda: f.read(bloque), b''): h.update(b)
    return h.hexdigest()


@_seguro(dict)
def fila_r(pref, r, ex=None):
    """Vector de eval_robustez_numba_v6 (13 posiciones) -> columnas con nombre. r[0] es Score_v7 si la métrica es v7."""
    d = {f'{pref}_{n}': float(r[i]) for i, n in enumerate(R_NOMBRES)}
    d[f'{pref}_n'] = int(r[10])
    if ex:
        for k in EXTRAS:
            if k in ex: d[f'{pref}_{k}'] = float(ex[k])
    return d


@_seguro(dict)
def extras_v7(prof, res):
    """Componentes de Score_v7 ya calculados por V7.score_v7 (res) y pips totales de los mismos trades."""
    d = {'pips': float(np.sum(prof)) if len(prof) else 0.0}
    if res:
        for k_out, k_in in (('C1', 'C1'), ('C2', 'C2'), ('C3', 'C3'), ('C4', 'C4'), ('alfa', 'alfa_medio'), ('n_sen', 'N')):
            if k_in in res: d[k_out] = float(res[k_in])
    return d


@_seguro(dict)
def datos_ml(df_ml):
    """Población de entrenamiento de Ridge 1 (salida mecánica de Fase 3 en el IS)."""
    p = df_ml['Profit_Pips'].to_numpy()
    if len(p) == 0: return {'ml_n': 0}
    return {'ml_n': int(len(p)), 'ml_wr': float(100.0 * np.mean(p > 0)), 'ml_med_pips': float(np.median(p)), 'ml_pips': float(np.sum(p))}


def veredicto_r2(f):
    """Ridge 2 con y sin, en OOS. BASE_RECHAZADA usa la misma regla que Reporte_OOS (Score_final de la base <= 0)."""
    if 'oos_sup_pf' not in f or 'oos_base_pf' not in f: return 'SIN_OOS'
    if not (f.get('oos_base_sf', f.get('oos_base_score', 0.0)) > 0.0): return 'BASE_RECHAZADA'
    mejor = int(f['oos_sup_pf'] > f['oos_base_pf']) + int(f['oos_sup_med_pips'] > f['oos_base_med_pips'])
    return ('NO_APORTA', 'MIXTO', 'APORTA')[mejor]


@_seguro(dict)
def datos_vida(par_vida, nombres_desc):
    """Diagnóstico R2V_* que Fase 4 ya calcula con CIERRE=V3/dV3 (R² de valores terminales desde las features vivas; sin nulo, H-V3-04)."""
    d = {}
    if not par_vida: return d
    for n, v in zip(tuple(nombres_desc) + ('V3',), par_vida.get('r2', [])): d[f'r2v_{_ascii(n)}'] = float(v)
    if 'corr_max' in par_vida: d['r2v_corr_max'] = float(par_vida['corr_max'])
    return d


@_seguro(lambda: None)
def registrar(lista, cz, row_data, simbolo, dir_nombre, estado, causa):
    """Escribe (o corrige) la fila de censo de un candidato. Un candidato = una fila, aunque se llame dos veces."""
    idx, row = row_data
    f = cz.get('_fila')
    if f is None:
        f = {}; cz['_fila'] = f; lista.append(f)
    f.clear()
    f.update({'simbolo': simbolo, 'dir': dir_nombre, 'fold': int(_num(row.get('Fold'))) if _num(row.get('Fold')) == _num(row.get('Fold')) else -1,
              'rank_f3': _num(row.get('Rank')), 'idx_f3': int(idx),
              'base_in': row.get('⚖️ BASE IN'), 'acum_in': row.get('📊 ACUM IN'), 'arm_in': _num(row.get('⚙️ Arm_IN')), 'chq_in': _num(row.get('⚡ Chq_IN')),
              'base_out': row.get('⚖️ BASE OUT'), 'acum_out': row.get('📊 ACUM OUT'), 'arm_out': _num(row.get('⚙️ Arm_OUT')), 'chq_out': _num(row.get('⚡ Chq_OUT')),
              'estado': estado, 'etapa': cz.get('etapa', ''), 'causa': causa or '', 'rank_ia': float('nan'), 'en_cerebro': False})
    for k, v in row.items():                                   # lo que Fase 3 midió de esta configuración (salida mecánica, sin Ridge)
        if k in _ID_F3 or str(k).startswith(('Tab_', 'Busq_')): continue
        f['f3_' + _ascii(k)] = _num(v)
    for k, v in cz.items():
        if not k.startswith('_') and k != 'etapa': f[k] = v
    if '_t0' in cz: f['t_seg'] = time.perf_counter() - cz['_t0']
    f['ridge2'] = veredicto_r2(f)
    if f['ridge2'] != 'SIN_OOS':
        f['d_pf'] = f['oos_sup_pf'] - f['oos_base_pf']; f['d_med_pips'] = f['oos_sup_med_pips'] - f['oos_base_med_pips']
        if 'oos_sup_pips' in f and 'oos_base_pips' in f: f['d_pips'] = f['oos_sup_pips'] - f['oos_base_pips']
    return f


def _columnas(df):
    orden = COLS_ID + COLS_EMBUDO + sorted(c for c in df.columns if c.startswith('f3_')) + COLS_R1 + COLS_R2
    for b in BLOQUES:
        orden += [f'{b}_{n}' for n in R_NOMBRES] + [f'{b}_{k}' for k in EXTRAS]
    orden += COLS_VER
    return [c for c in orden if c in df.columns] + sorted(c for c in df.columns if c not in orden)


VISTA = [('simbolo', 'Simbolo'), ('dir', 'Dir'), ('fold', 'Fold'), ('rank_f3', 'Rank_F3'), ('estado', 'Estado'), ('etapa', 'Etapa'), ('causa', 'Causa'),
         ('en_cerebro', 'En_cerebro'), ('rank_ia', 'Rank_IA'), ('base_in', 'Base_IN'), ('acum_in', 'Acum_IN'), ('base_out', 'Base_OUT'), ('acum_out', 'Acum_OUT'),
         ('r1_r2_T', 'R2_CabezaB'), ('K_opt', 'K_abortar'), ('is_sup_score', 'Score_IS_conR2'), ('oos_sup_score', 'Score_OOS_conR2'),
         ('oos_base_n', 'Ops_OOS_sinR2'), ('oos_sup_n', 'Ops_OOS_conR2'), ('oos_base_pf', 'PF_OOS_sinR2'), ('oos_sup_pf', 'PF_OOS_conR2'),
         ('oos_base_med_pips', 'MedPips_OOS_sinR2'), ('oos_sup_med_pips', 'MedPips_OOS_conR2'), ('oos_base_pips', 'Pips_OOS_sinR2'), ('oos_sup_pips', 'Pips_OOS_conR2'),
         ('oos_sup_wr', 'WR_OOS_conR2'), ('oos_sup_maxdd', 'MaxDD_OOS_conR2'), ('oos_sup_C3', 'C3_nulo_entrada_OOS'), ('ridge2', 'Ridge2')]


def vista(df, top):
    """Primeras `top` filas por (dir, fold): primero las que pasaron (por clave de selección), luego el resto por score OOS con Ridge 2."""
    d = df.copy()
    d['_p'] = (d['estado'] != 'paso').astype(int)
    d['_k'] = -d['clave_rank'].fillna(-np.inf) if 'clave_rank' in d else 0.0
    d['_s'] = -d['oos_sup_score'].fillna(-np.inf) if 'oos_sup_score' in d else 0.0
    d = d.sort_values(['dir', 'fold', '_p', '_k', '_s', 'idx_f3'], kind='mergesort').groupby(['dir', 'fold'], sort=False).head(int(top))
    cols = [(a, b) for a, b in VISTA if a in d.columns]
    return d[[a for a, _ in cols]].rename(columns=dict(cols))


def nombres(tag, simbolo=None):
    if simbolo is None: return f"Resumen_Fase4_{tag}.md", f"Manifiesto_Fase4_{tag}.json"
    return f"Censo_Fase4_{tag}_{simbolo}.csv", f"Vista_Fase4_{tag}_{simbolo}.csv"


def _csv_atomico(df, ruta):
    tmp = ruta + '.tmp'; df.to_csv(tmp, index=False, encoding='utf-8', float_format='%.6g'); os.replace(tmp, ruta)


def escribir_censo(simbolo, tag, filas, sello, top_vista, leidas):
    """filas: lista de dicts de `registrar`. leidas: {'LONG': (filas en el CSV de Fase 3, filas leídas), 'SHORT': (...)}."""
    df = pd.DataFrame(filas)
    if df.empty: return None
    df = df[_columnas(df)].sort_values(['dir', 'fold', 'idx_f3'], kind='mergesort').reset_index(drop=True)
    df['tag'] = tag
    for d_, (n_csv, n_leidas) in leidas.items():
        df.loc[df['dir'] == d_, 'f3_filas_csv'] = n_csv; df.loc[df['dir'] == d_, 'f3_filas_leidas'] = n_leidas
    for k, v in sello.items(): df[k] = v
    a_censo, a_vista = nombres(tag, simbolo)
    _csv_atomico(df, a_censo); _csv_atomico(vista(df, top_vista), a_vista)
    return a_censo, a_vista, len(df)


# ------------------------------------------------------------------ resumen (solo desde los censos del disco)
def _md(df):
    cab = '| ' + ' | '.join(str(c) for c in df.columns) + ' |\n|' + '---|' * len(df.columns) + '\n'
    def fmt(v):
        if isinstance(v, float): return '' if v != v else (f'{v:.0f}' if abs(v) >= 1000 or v == int(v) else f'{v:.3f}')
        return str(v)
    return cab + ''.join('| ' + ' | '.join(fmt(v) for v in fila) + ' |\n' for fila in df.itertuples(index=False))


def _med(s):
    s = pd.to_numeric(s, errors='coerce').dropna()
    return float(s.median()) if len(s) else float('nan')


def tablas_resumen(df):
    """Devuelve un dict nombre -> DataFrame. Función pura: la prueba la recalcula a mano."""
    out = {}; g_keys = ['simbolo', 'dir']
    def por_grupo(f):
        filas = [dict(zip(g_keys, k), **f(g)) for k, g in df.groupby(g_keys, sort=True)]
        filas.append(dict(simbolo='TODOS', dir='', **f(df)))
        return pd.DataFrame(filas)
    def embudo(g):
        d = {'leidas': len(g)}
        for e in ETAPAS: d['cae_' + e] = int(((g['estado'] != 'paso') & (g['etapa'] == e)).sum())
        d['pasan'] = int((g['estado'] == 'paso').sum()); d['en_cerebro'] = int(g['en_cerebro'].astype(bool).sum())
        if 'f3_filas_csv' in g:
            _gg = g.groupby(['simbolo', 'dir']); d['recortadas_por_tope'] = int((_gg['f3_filas_csv'].first() - _gg['f3_filas_leidas'].first()).sum())
        return d
    out['embudo'] = por_grupo(embudo)
    def r1(g):
        s = pd.to_numeric(g.get('r1_r2_T', pd.Series(dtype=float)), errors='coerce').dropna()
        return {'con_R2': len(s), 'R2_positivo': int((s > 0).sum()), 'R2_mediana': _med(s), 'R2_p25': float(s.quantile(0.25)) if len(s) else float('nan'),
                'R2_p75': float(s.quantile(0.75)) if len(s) else float('nan'), 'T_min_mediana': _med(g.get('r1_T_min', pd.Series(dtype=float)))}
    out['ridge1'] = por_grupo(r1)
    def r2(g, solo_paso=False):
        h = g[g['ridge2'] != 'SIN_OOS']
        if solo_paso: h = h[h['estado'] == 'paso']
        d = {'con_OOS': len(h)}
        for v in ('APORTA', 'MIXTO', 'NO_APORTA', 'BASE_RECHAZADA'): d[v] = int((h['ridge2'] == v).sum())
        c = h[h['ridge2'] != 'BASE_RECHAZADA']
        d['d_pf_mediana'] = _med(c.get('d_pf', pd.Series(dtype=float))); d['d_med_pips_mediana'] = _med(c.get('d_med_pips', pd.Series(dtype=float)))
        d['d_pips_mediana'] = _med(c.get('d_pips', pd.Series(dtype=float)))
        return d
    out['ridge2_todas'] = por_grupo(r2); out['ridge2_solo_las_que_pasaron'] = por_grupo(lambda g: r2(g, True))
    if 'oos_sup_C3' in df.columns:
        def c3(g):
            s = pd.to_numeric(g['oos_sup_C3'], errors='coerce').dropna(); b = pd.to_numeric(g.get('oos_base_C3', pd.Series(dtype=float)), errors='coerce').dropna()
            return {'con_C3': len(s), 'C3_conR2_mediana': _med(s), 'C3_conR2_sobre_0.5': int((s > 0.5).sum()), 'C3_sinR2_mediana': _med(b), 'C3_sinR2_sobre_0.5': int((b > 0.5).sum())}
        out['nulo_entrada_C3_OOS'] = por_grupo(c3)
    ex = df[df['en_cerebro'].astype(bool)].sort_values(['simbolo', 'dir', 'rank_ia'])
    cols = [c for c in ('simbolo', 'dir', 'rank_ia', 'fold', 'rank_f3', 'K_opt', 'r1_r2_T', 'oos_base_n', 'oos_sup_n', 'oos_base_pf', 'oos_sup_pf',
                        'oos_base_med_pips', 'oos_sup_med_pips', 'oos_base_pips', 'oos_sup_pips', 'oos_sup_C3', 'ridge2') if c in ex.columns]
    out['exportados'] = ex[cols].reset_index(drop=True)
    return out


def leer_censos(tag, carpeta='.'):
    rutas = sorted(glob.glob(os.path.join(carpeta, f"Censo_Fase4_{tag}_*.csv")))
    if not rutas: return None, []
    return pd.concat([pd.read_csv(r) for r in rutas], ignore_index=True), rutas


TEXTO = {
    'embudo': "Etapa donde cayó cada configuración leída. `recortadas_por_tope` > 0 significa que el CSV de Fase 3 traía más filas que TOP_CANDIDATOS y Fase 4 no las leyó.",
    'ridge1': "Cabeza B de Ridge 1: R² fuera de pliegue (OOF) dentro del IS. Solo las configuraciones que llegaron a entrenarla. R² <= 0 se descarta.",
    'ridge2_todas': "Ridge 2 con y sin, en OOS, sobre TODAS las configuraciones que llegaron al OOS (pasen o no el filtro). d_* = con Ridge 2 menos sin Ridge 2; las medianas excluyen BASE_RECHAZADA.",
    'ridge2_solo_las_que_pasaron': "Lo mismo, solo sobre las que pasaron el filtro OOS. Están elegidas por su resultado CON Ridge 2: esta tabla favorece a Ridge 2 por construcción. Comparar con la anterior.",
    'nulo_entrada_C3_OOS': "Componente C3 de Score_v7 en OOS: 0.5 = igual que el gemelo nulo (misma dirección y duración, entrada al azar dentro del día); sobre 0.5 = mejor que el nulo.",
    'exportados': "Configuraciones que entraron al cerebro (hasta EXPORTAR_MQL5_TOP por dirección).",
}


def resumen(tag, carpeta='.'):
    df, rutas = leer_censos(tag, carpeta)
    a_res, a_man = nombres(tag)
    if df is None: return None
    t = tablas_resumen(df)
    L = [f"# Resumen de Fase 4 — {tag}\n",
         f"Generado {datetime.datetime.now().isoformat(timespec='seconds')} por lab_informes v{INFORMES_VERSION} desde {len(rutas)} censo(s): "
         f"{df['simbolo'].nunique()} símbolo(s), {len(df)} configuraciones leídas. Trazabilidad: `{a_man}`.\n",
         "Toda cifra de este archivo sale de los `Censo_Fase4_*.csv` y se puede recalcular: `python lab_informes.py TAG`.\n",
         "**Cómo leer.** Las configuraciones de un mismo símbolo se parecen entre sí y los símbolos comparten divisas: los conteos muestran "
         "tendencias, no pruebas independientes. El OOS de Fase 4 se usa como filtro de exportación; la medición sin filtro es la reserva ciega de Fase 4.5.\n"]
    for k, d in t.items():
        L.append(f"\n## {k.replace('_', ' ')}\n\n{TEXTO.get(k, '')}\n\n" + (_md(d) if len(d) else "_sin filas_\n"))
    with open(os.path.join(carpeta, a_res) + '.tmp', 'w', encoding='utf-8') as f: f.write(''.join(L))
    os.replace(os.path.join(carpeta, a_res) + '.tmp', os.path.join(carpeta, a_res))
    return a_res


# ------------------------------------------------------------------ manifiesto
def _commit(dir_codigo):
    for ruta in (os.path.join(dir_codigo, '..', 'COMMIT.txt'), os.path.join(dir_codigo, 'COMMIT.txt')):
        if os.path.isfile(ruta):
            try: return open(ruta, encoding='utf-8').read().strip() + ' (COMMIT.txt)'
            except OSError: pass
    try:
        import subprocess
        r = subprocess.run(['git', '-C', dir_codigo, 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True, timeout=10)
        s = subprocess.run(['git', '-C', dir_codigo, 'status', '--porcelain'], capture_output=True, text=True, timeout=10)
        if r.returncode == 0: return r.stdout.strip() + (' (git, con cambios sin commit)' if s.stdout.strip() else ' (git)')
    except Exception: pass
    return 'desconocido'


def fechas_parquet(ruta, cortes):
    """Fecha de cada corte de índice (posición de fila). Devuelve {} si el parquet no trae una columna o índice de tiempo."""
    try:
        import pyarrow.parquet as pq
        esquema = pq.read_schema(ruta); cand = [n for n in esquema.names if n.lower() in ('time', 'datetime', 'fecha', 'date', '__index_level_0__')]
        if not cand: return {}
        col = pq.read_table(ruta, columns=[cand[0]]).column(0).to_pandas()
        return {k: (str(col.iloc[min(max(int(v), 0), len(col) - 1)]) if len(col) else '') for k, v in cortes.items()}
    except Exception as e:
        return {'_error': f'{type(e).__name__}: {e}'}


def manifiesto(tag, entrada, carpeta='.'):
    """Agrega una entrada (una por corrida de Fase 4) al manifiesto del tag. Nunca borra entradas anteriores."""
    _, a_man = nombres(tag); ruta = os.path.join(carpeta, a_man)
    doc = {'tag': tag, 'corridas': []}
    if os.path.isfile(ruta):
        try: doc = json.load(open(ruta, encoding='utf-8'))
        except (OSError, ValueError): doc = {'tag': tag, 'corridas': [], 'aviso': 'manifiesto anterior ilegible: se reinició'}
    dir_codigo = os.path.dirname(os.path.abspath(__file__))
    base = {'informes_version': INFORMES_VERSION, 'commit': _commit(dir_codigo), 'python': platform.python_version(), 'plataforma': platform.platform(),
            'paquetes': {}, 'codigo_sha1': {}}
    for p in ('numpy', 'pandas', 'numba', 'llvmlite', 'scikit-learn', 'scipy', 'pyarrow', 'optuna'):
        try:
            import importlib.metadata as im; base['paquetes'][p] = im.version(p)
        except Exception: base['paquetes'][p] = 'no instalado'
    raiz = os.path.abspath(os.path.join(dir_codigo, '..'))
    for rel in ('lab_v7/Fase_4_lab.py', 'lab_v7/lab_informes.py', 'lab_v7/vida_v3.py', 'lab_v7/lab_escala.py', 'lab_v7/v7_metricas.py', 'lab_v7/tablero_lab.env',
                'nexus_formulas_core.py', 'nexus_tablero.py'):
        r_ = os.path.join(raiz, rel)
        if os.path.isfile(r_): base['codigo_sha1'][rel] = sha1_archivo(r_)
    base.update(entrada)
    with _lock_err: base['errores_informes'] = dict(ERRORES)
    for a in base.get('salidas', []):
        r_ = os.path.join(carpeta, a['archivo'])
        if os.path.isfile(r_): a['sha1'] = sha1_archivo(r_); a['bytes'] = os.path.getsize(r_)
    doc['corridas'].append(base)
    with open(ruta + '.tmp', 'w', encoding='utf-8') as f: json.dump(doc, f, ensure_ascii=False, indent=1, default=str)
    os.replace(ruta + '.tmp', ruta)
    return a_man


if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit("Uso: python lab_informes.py TAG [carpeta]   (regenera Resumen_Fase4_TAG.md desde los censos)")
    r = resumen(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '.')
    print(r or f"No hay censos Censo_Fase4_{sys.argv[1]}_*.csv en la carpeta")
