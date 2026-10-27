#!/usr/bin/env python3
"""
E2 — Verificación de coherencia de tableros y contratos de nombres de la cadena NEXUS.
Solo LEE (ast + regex). No importa ni ejecuta las fases. No modifica nada.

Uso:  python verificar_tableros.py [DIR_REPO] [--salida tablero_produccion.json]
Código de salida: 0 = sin discrepancias; 1 = hay discrepancias (ver JSON y consola).
"""
import ast, io, json, re, sys, os, argparse, tokenize

ARCHIVOS = {
    'F0': 'Fase_0.py', 'F12': 'Fase_1___2.py', 'F3': 'Fase_3.py', 'F4': 'Fase_4_V12_0.py',
    'F45A': 'Fase_4_5_V_12_0_A.py', 'F45B': 'Fase_4_5_V_12_0_B.py',
    'CORE': 'nexus_formulas_core.py', 'TAB': 'nexus_tablero.py',
}
EXTRACTOR_CANDIDATOS = ['extraxtor_mt5_rangofecha.py', 'extractor_mt5_rangofecha.py']

hallazgos, evidencia = [], {}

def leer(ruta):
    with open(ruta, encoding='utf-8') as f:
        return f.read()

def evaluar(nodo, entorno):
    """Evaluador mínimo y seguro: constantes, f-strings, listas, TAB.X, nombres ya resueltos."""
    if isinstance(nodo, ast.Constant): return nodo.value
    if isinstance(nodo, ast.JoinedStr):
        out = ''
        for v in nodo.values:
            if isinstance(v, ast.Constant): out += str(v.value)
            elif isinstance(v, ast.FormattedValue):
                r = evaluar(v.value, entorno)
                out += '{?}' if r is None else str(r)
        return out
    if isinstance(nodo, (ast.List, ast.Tuple)): return [evaluar(e, entorno) for e in nodo.elts]
    if isinstance(nodo, ast.Name): return entorno.get(nodo.id)
    if isinstance(nodo, ast.Attribute) and isinstance(nodo.value, ast.Name):
        return f"{nodo.value.id}.{nodo.attr}"
    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.USub):
        v = evaluar(nodo.operand, entorno); return -v if isinstance(v, (int, float)) else None
    if isinstance(nodo, ast.BinOp):
        a, b = evaluar(nodo.left, entorno), evaluar(nodo.right, entorno)
        try:
            if isinstance(nodo.op, ast.Add): return a + b
            if isinstance(nodo.op, ast.Mult): return a * b
        except Exception: return None
    if isinstance(nodo, ast.IfExp):
        return None  # condicionales: no se resuelven; se reporta como None
    return None

def constantes(src):
    """Asignaciones de nivel módulo -> {nombre: (valor_evaluado, linea)}."""
    arbol = ast.parse(src); ent, res = {}, {}
    for n in arbol.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            nombre = n.targets[0].id; val = evaluar(n.value, ent)
            ent[nombre] = val; res[nombre] = (val, n.lineno)
    return res

def sin_comentarios(src):
    """Blanquea los comentarios (conserva posiciones) para que las regex no lean bitácoras."""
    lineas = src.split('\n')
    for t in tokenize.generate_tokens(io.StringIO(src).readline):
        if t.type == tokenize.COMMENT:
            (f, c), (_, c2) = t.start, t.end
            lineas[f - 1] = lineas[f - 1][:c] + ' ' * (c2 - c) + lineas[f - 1][c2:]
    return '\n'.join(lineas)

def hallazgo(sev, cod, msg): hallazgos.append({'severidad': sev, 'codigo': cod, 'detalle': msg})

def comparar(cod, desc, a, b, sev='CRITICO'):
    ok = (a == b); evidencia[cod] = {'descripcion': desc, 'A': a, 'B': b, 'ok': ok}
    if not ok: hallazgo(sev, cod, f"{desc}: {a!r} != {b!r}")
    return ok

def plantilla(txt):
    """Normaliza placeholders de f-string para comparar nombres de archivo entre fases."""
    return re.sub(r'\{[^}]*\}', '{*}', txt)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('repo', nargs='?', default='.')
    ap.add_argument('--salida', default='tablero_produccion.json'); a = ap.parse_args()
    S, C = {}, {}
    for k, f in ARCHIVOS.items():
        r = os.path.join(a.repo, f)
        if not os.path.exists(r): hallazgo('CRITICO', f'ARCHIVO_AUSENTE_{k}', f"No existe {f}"); continue
        S[k] = leer(r)
        try: S[k + '_code'] = sin_comentarios(S[k])
        except Exception: S[k + '_code'] = S[k]
        try: C[k] = constantes(S[k])
        except SyntaxError as e: hallazgo('CRITICO', f'SINTAXIS_{k}', f"{f}: {e}")
    ext_src = None
    for e in EXTRACTOR_CANDIDATOS:
        if os.path.exists(os.path.join(a.repo, e)): ext_src = leer(os.path.join(a.repo, e)); C['EXT'] = constantes(ext_src); break
    if len(C) < 8:
        json.dump({'hallazgos': hallazgos}, open(a.salida, 'w'), indent=2, ensure_ascii=False)
        print('FALTAN ARCHIVOS'); [print(' -', h['detalle']) for h in hallazgos]; return 1

    g = lambda k, n: C[k].get(n, (None, None))[0]

    # --- 1. Escalón y versiones ---
    esc = {k: g(k, 'ESCALON') for k in ('F4', 'F45A', 'F45B')}
    evidencia['ESCALON'] = esc
    if len(set(esc.values())) != 1: hallazgo('CRITICO', 'ESCALON_DISTINTO', f"ESCALON por fase: {esc}")
    E = esc['F4']
    for k in ('F4', 'F45A'): C[k]['ESCALON_'] = (E, 0)
    versiones = {'F0': g('F0', 'FASE0_VERSION'), 'F12': g('F12', 'FASE12_VERSION'), 'F4': g('F4', 'FASE4_VERSION'),
                 'F45A': g('F45A', 'FASE45_VERSION'), 'F45B': g('F45B', 'FASE45B_VERSION'),
                 'CORE': g('CORE', 'FORMULAS_CORE_VERSION'), 'TABLERO': g('TAB', 'TABLERO_VERSION')}
    evidencia['versiones'] = versiones
    if None in versiones.values(): hallazgo('MEDIO', 'VERSION_NO_RESUELTA', f"{versiones}")
    if len({versiones['F4'], versiones['F45A'], versiones['F45B']}) != 1:
        hallazgo('MEDIO', 'VERSION_F4_F45_DISTINTA', f"F4={versiones['F4']} 4.5A={versiones['F45A']} 4.5B={versiones['F45B']}")

    # --- 2. Tags y directorios (f-strings resueltas con el ESCALON vigente) ---
    res = lambda s: s.replace('{ESCALON}', E) if isinstance(s, str) else s
    tag4, tag45 = res(g('F4', 'TAG_ARCHIVOS')), res(g('F45A', 'TAG_ARCHIVOS_FASE4'))
    comparar('TAG_F4_vs_F45A', 'TAG_ARCHIVOS (Fase 4) vs TAG_ARCHIVOS_FASE4 (4.5A)', tag4, tag45)
    comparar('DIR_SALIDA_A_vs_B', 'DIR_SALIDA 4.5A vs 4.5B', res(g('F45A', 'DIR_SALIDA')), res(g('F45B', 'DIR_SALIDA')))

    # --- 3. Lista de símbolos ---
    L = {k: g(k, 'LISTA_SIMBOLOS') for k in ('F3', 'F4', 'F45A')}
    comparar('SIMBOLOS_F3_vs_F4', 'LISTA_SIMBOLOS Fase 3 vs Fase 4', L['F3'], L['F4'])
    comparar('SIMBOLOS_F4_vs_F45A', 'LISTA_SIMBOLOS Fase 4 vs 4.5A', L['F4'], L['F45A'])
    spreads = set(re.findall(r"'([A-Z]{6}m)':", S['CORE']))
    faltan = sorted(set(L['F4'] or []) - spreads)
    evidencia['SIMBOLOS_sin_spread'] = faltan
    if faltan: hallazgo('MEDIO', 'SIMBOLO_SIN_SPREAD', f"Sin entrada en MATRIZ_SPREADS (usarán fallback): {faltan}")
    if ext_src:
        base = g('EXT', 'PARES_BASE') or []
        comparar('SIMBOLOS_EXTRACTOR_vs_F4', 'PARES_BASE+"m" (extractor) vs LISTA_SIMBOLOS (como conjunto)',
                 sorted(p + 'm' for p in base), sorted(L['F4'] or []), sev='MEDIO')

    # --- 4. Contratos de nombres de archivo entre fases ---
    pq = {k: set(map(plantilla, re.findall(r"""['"](nexus_df_salida_3D_[^'"]*\.parquet)['"]""", S[k + '_code']))) for k in ('F12', 'F3', 'F4', 'F45A')}
    evidencia['parquet_plantillas'] = {k: sorted(v) for k, v in pq.items()}
    ref = pq['F12']
    for k in ('F3', 'F4', 'F45A'):
        if pq[k] != ref: hallazgo('CRITICO', f'PARQUET_{k}', f"Plantilla de parquet {sorted(pq[k])} != salida de Fase 1&2 {sorted(ref)}")
    csv3_esc = set(map(plantilla, re.findall(r"""f?['"](Reporte_Fase3_WFO_[^'"]*\.csv)['"]""", S['F3_code'])))
    csv3_lee = plantilla(g('F4', 'PATRON_CSV_FASE3') or '')
    evidencia['csv_fase3'] = {'escribe_F3': sorted(csv3_esc), 'lee_F4': csv3_lee}
    if csv3_lee not in csv3_esc: hallazgo('CRITICO', 'CSV_FASE3', f"Fase 4 lee {csv3_lee!r}; Fase 3 escribe {sorted(csv3_esc)}")
    rep4 = plantilla(re.search(r"""f?["'](Reporte_OOS_Phase4_[^"']*\.csv)["']""", S['F4_code']).group(1))
    rep45 = plantilla(re.search(r"""f?["'](Reporte_OOS_Phase4_[^"']*\.csv)["']""", S['F45A_code']).group(1))
    comparar('CSV_FASE4_plantilla', 'CSV de Fase 4 (escribe vs lee 4.5A)', rep4, rep45)
    txt4 = plantilla(re.search(r"""f?["'](Cerebro_MQL5_[^"']*\.txt)["']""", S['F4_code']).group(1))
    txt45 = plantilla(re.search(r"""f?["'](Cerebro_MQL5_[^"']*\.txt)["']""", S['F45A_code']).group(1))
    comparar('TXT_CEREBRO_plantilla', '.txt cerebro (escribe F4 vs lee 4.5A)', txt4, txt45)
    ruta_csv = g('F0', 'RUTA_CSV'); ruta_pq0 = g('F0', 'RUTA_PARQUET')
    comparar('F0_PARQUET_vs_F12', 'Parquet que escribe Fase 0 vs RUTA_PARQUET_ORIGEN de Fase 1&2',
             (ruta_csv or '').replace('.csv.gz', '.parquet'), g('F12', 'RUTA_PARQUET_ORIGEN'))
    if ext_src: comparar('EXTRACTOR_ALIAS_vs_F0', 'NOMBRE_ALIAS_FASE0 (extractor) vs RUTA_CSV (Fase 0)', g('EXT', 'NOMBRE_ALIAS_FASE0'), ruta_csv)

    # --- 5. Contrato extractor -> Fase 0 (aborto por extracción parcial) ---
    if ext_src and 'ABORTAR_SI_EXTRACCION_PARCIAL' in ext_src and 'ABORTAR_SI_EXTRACCION_PARCIAL' not in S['F0']:
        hallazgo('MEDIO', 'ABORTO_PARCIAL_INEXISTENTE',
                 "El extractor anuncia que Fase 0 abortará (ABORTAR_SI_EXTRACCION_PARCIAL) pero Fase_0.py no implementa ese flag: "
                 "solo imprime los pares parciales del manifest. Una extracción parcial NO detiene la cadena.")

    # --- 6. Tablero único: las fases deben IMPORTAR, no redefinir ---
    for k in ('F3', 'F4', 'F45A'):
        for n in ('N_FOLDS', 'RATIO_TRAIN_TEST', 'MEMORIA_FIFO'):
            v = g(k, n); ok = isinstance(v, str) and v == f'TAB.{n}'
            evidencia[f'TABLERO_{k}_{n}'] = v
            if not ok: hallazgo('CRITICO', f'TABLERO_REDEFINIDO_{k}_{n}', f"{k}.{n} = {v!r} (debe ser TAB.{n})")
    tab = {n: g('TAB', n) for n in ('N_FOLDS', 'RATIO_TRAIN_TEST', 'RESERVA_FINAL', 'MEMORIA_FIFO', 'EXIGIR_SELLO')}
    evidencia['tablero_vigente'] = tab
    if tab['RESERVA_FINAL'] == 0.0:
        hallazgo('INFO', 'VENTANA_NO_CIEGA', "RESERVA_FINAL=0.0: la ventana de portafolio de 4.5B se solapa con el OOS de Fase 4 (no es evidencia fuera de muestra). Decisión del CRO.")
    if tab['EXIGIR_SELLO'] is not True: hallazgo('CRITICO', 'EXIGIR_SELLO_OFF', f"EXIGIR_SELLO={tab['EXIGIR_SELLO']!r}")

    # --- 7. Umbrales de trades dispersos (solo reporte, con archivo:línea) ---
    umbrales = []
    pat = re.compile(r'^\s*(MIN_OPS_\w+|MIN_TRADES_\w+|MIN_BLOQUES_\w+)\s*=\s*([^#\n]+)', re.M)
    for k in ('F3', 'F4', 'F45A', 'F45B'):
        for m in pat.finditer(S[k]):
            umbrales.append({'archivo': ARCHIVOS[k], 'linea': S[k][:m.start()].count('\n') + 1, 'nombre': m.group(1), 'valor': m.group(2).strip()})
        for m in re.finditer(r'eval_robustez_numba_v6\([^\n]*?,\s*([A-Z_]+|\d+)\)', S[k]):
            umbrales.append({'archivo': ARCHIVOS[k], 'linea': S[k][:m.start()].count('\n') + 1, 'nombre': 'min_trades (arg de eval_robustez)', 'valor': m.group(1)})
    evidencia['umbrales_trades_dispersos'] = umbrales
    evidencia['otras_constantes_decision'] = {n: g(k, n) for k, n in (('F4', 'Q_ADMISION_T'), ('F4', 'RATIO_CAPTURA_VELOCIDAD'),
        ('F4', 'TOLERANCIA_VIDA_MEDIA'), ('F3', 'N_SIMULACIONES'), ('F3', 'STARTUP_TRIALS'), ('F4', 'TOP_CANDIDATOS'))}

    # --- 8. Variables de entorno de humo (no deben existir en producción) ---
    for k in ('F0', 'F12', 'F3', 'F4', 'F45A', 'F45B'):
        if 'NEXUS_SMOKE' in S[k]: hallazgo('MEDIO', f'SMOKE_EN_PRODUCCION_{k}', f"{ARCHIVOS[k]} contiene NEXUS_SMOKE: el humo debe vivir solo en copias.")

    sal = {'repo': os.path.abspath(a.repo), 'escalon': E, 'hallazgos': hallazgos, 'evidencia': evidencia}
    with open(a.salida, 'w', encoding='utf-8') as f: json.dump(sal, f, indent=2, ensure_ascii=False, default=str)
    orden = {'CRITICO': 0, 'MEDIO': 1, 'INFO': 2}
    print(f"ESCALON={E} | tablero={tab}")
    for h in sorted(hallazgos, key=lambda x: orden[x['severidad']]): print(f"[{h['severidad']}] {h['codigo']}: {h['detalle']}")
    crit = sum(h['severidad'] == 'CRITICO' for h in hallazgos)
    print(f"\n{len(hallazgos)} hallazgos ({crit} críticos). JSON: {a.salida}")
    return 1 if crit else 0

if __name__ == '__main__':
    sys.exit(main())
