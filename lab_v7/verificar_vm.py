# ==============================================================================
# NEXUS LAB-V7 — VERIFICADOR PREVIO PARA LA VM (solo lectura). Uso: python lab_v7/verificar_vm.py [carpeta_de_trabajo]
# Bitácora V0.1 (2026-11-06): creación. Orden del CRO: "dejar listos los tableros y configuraciones".
# Bitácora V0.3 (2026-11-10, lab-v8): acepta NEXUS_LAB_CENSO (0|1), muestra NEXUS_LAB_VISTA_TOP y exige lab_informes.py (informes de Fase 4).
# Comprueba: versión de Python y paquetes, módulos del repo, tablero de geometría, tablero_lab.env, parquets y CSV por símbolo,
# RAM/CPU/disco. Sale con código 1 si algo bloquea. No ejecuta ninguna fase.
# ==============================================================================
import os, sys, re, glob, importlib.metadata as im
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, '..'))
TRABAJO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
sys.path[:0] = [RAIZ, AQUI]
mal = []; avisos = []
def ok(m): print('  OK   ', m)
def no(m): print('  FALLA', m); mal.append(m)
def av(m): print('  AVISO', m); avisos.append(m)
print('1. Python y paquetes'); v = sys.version_info
(ok if (3, 13) <= v[:2] <= (3, 14) else av)(f'Python {v[0]}.{v[1]} (requirements.txt: 3.13 o 3.14)')
for l in open(os.path.join(RAIZ, 'requirements.txt'), encoding='utf-8'):
    m = re.match(r'^([A-Za-z0-9_.-]+)==([\w.]+)', l.strip())
    if not m: continue
    try:
        got = im.version(m.group(1)); (ok if got == m.group(2) else av)(f'{m.group(1)} {got} (pedido {m.group(2)})')
    except im.PackageNotFoundError: no(f'falta {m.group(1)}=={m.group(2)}')
print('2. Archivos del repo')
for f in ('nexus_formulas_core.py', 'nexus_tablero.py', 'lab_v7/Fase_3_lab.py', 'lab_v7/Fase_4_lab.py', 'lab_v7/Fase_4_5_lab_A.py', 'lab_v7/Fase_4_5_lab_B.py',
          'lab_v7/v7_metricas.py', 'lab_v7/vida_v3.py', 'lab_v7/lab_escala.py', 'lab_v7/lab_informes.py', 'lab_v7/tablero_lab.env', 'lab_v7/correr_tablero.sh'):
    (ok if os.path.isfile(os.path.join(RAIZ, f)) else no)(f)
print('3. Tablero de geometría (nexus_tablero.py)')
try:
    import nexus_tablero as T
    ok(f'{T.N_FOLDS} folds | ratio {T.RATIO_TRAIN_TEST} | reserva {T.RESERVA_FINAL} | FIFO {T.MEMORIA_FIFO} | hash {T.hash_params()} | EXIGIR_SELLO={T.EXIGIR_SELLO}')
except Exception as e: no(f'tablero: {e}')
print('4. tablero_lab.env')
cfg = {}
for l in open(os.path.join(AQUI, 'tablero_lab.env'), encoding='utf-8'):
    l = l.strip()
    if l and not l.startswith('#') and '=' in l: k, _, val = l.partition('='); cfg[k] = val.strip()
perm = {'NEXUS_LAB_METRICA': ('final', 'v7', 'v52'), 'NEXUS_LAB_F3': ('main', 'v7'), 'NEXUS_LAB_CIERRE': ('T_terminal', 'dT_cont', 'G_pips', 'V3', 'dV3'), 'NEXUS_LAB_T': ('T', 'V3'), 'NEXUS_LAB_VIDA': ('3.0', '3.1'),
        'NEXUS_LAB_TAMANO': ('off', 'A', 'B'), 'NEXUS_LAB_NULO': ('0', '1'), 'NEXUS_LAB_CENSO': ('0', '1')}
for k, p in perm.items(): (ok if cfg.get(k) in p else no)(f'{k}={cfg.get(k)!r} (permitidos {p})')
for k in ('NEXUS_LAB_SIMBOLOS', 'NEXUS_LAB_N_SIM', 'NEXUS_LAB_STARTUP', 'NEXUS_LAB_F3_MEDIR', 'NEXUS_LAB_VISTA_TOP'): ok(f'{k}={cfg.get(k)!r}')
if cfg.get('NEXUS_LAB_NULO') == '1' and cfg.get('NEXUS_LAB_TAMANO') != 'off': no('NULO=1 con TAMANO distinto de off no es exportable')
print(f'5. Datos en la carpeta de trabajo: {TRABAJO}')
simb = [s.strip() for s in cfg.get('NEXUS_LAB_SIMBOLOS', '').split(',') if s.strip()]
if not simb:
    m = re.search(r"LISTA_SIMBOLOS\s*=\s*\[(.*?)\]", open(os.path.join(AQUI, 'Fase_4_lab.py'), encoding='utf-8').read(), re.S); simb = re.findall(r"'(\w+)'", m.group(1))
sfx = '_MV7' if cfg.get('NEXUS_LAB_F3') == 'v7' else ''
faltan_pq = [s for s in simb if not os.path.isfile(os.path.join(TRABAJO, f'nexus_df_salida_3D_{s}_MultiZ.parquet'))]
(ok if not faltan_pq else no)(f'parquets de Fase 1&2: {len(simb) - len(faltan_pq)}/{len(simb)}' + (f' | faltan {faltan_pq[:5]}' if faltan_pq else ''))
faltan_csv = [s for s in simb if not os.path.isfile(os.path.join(TRABAJO, f'Reporte_Fase3_WFO_V5.8_{s}{sfx}.csv'))]
print('      (CSV de Fase 3: se necesitan solo para correr Fase 4; Fase 3 los genera)')
(ok if not faltan_csv else av)(f'CSV de Fase 3 (sufijo {sfx or "ninguno"}): {len(simb) - len(faltan_csv)}/{len(simb)}')
print('6. Recursos')
try:
    import psutil; ok(f'RAM {psutil.virtual_memory().total / 2**30:.1f} GB | CPU lógicas {psutil.cpu_count()} | disco libre {psutil.disk_usage(TRABAJO).free / 2**30:.1f} GB')
except Exception as e: av(f'psutil: {e}')
print(f'\nRESULTADO: {len(mal)} bloqueos, {len(avisos)} avisos'); sys.exit(1 if mal else 0)
