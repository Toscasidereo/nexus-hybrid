#!/usr/bin/env python3
"""
PILOTO DE MEDICIÓN DE FASE 3 — tasa de poda y tiempo por trial, por umbral de operaciones IS.

Qué hace: para cada umbral pedido, corre UNA copia temporal de Fase_3.py sobre UN símbolo, con muestreo 100 % aleatorio
(STARTUP_TRIALS enorme) y un N_SIMULACIONES pequeño. Con muestreo aleatorio, completos/evaluados estima la fracción de
configuraciones que superan el umbral (lo que verá el arranque aleatorio del TPE). Mide además segundos-núcleo por trial.
NO modifica el repositorio ni los parquets (los enlaza en una carpeta temporal).

Uso (en la máquina con los datos REALES de Fase 1&2):
  python3 auditoria/piloto_fase3.py --repo . --datos /ruta/con/los/parquets --simbolo EURUSDm
Opciones: --umbrales 50,200  --n-sim 100  --n-sim-final 20000  --n-simbolos 28

Límites: (1) el tiempo por trial depende del largo de la ventana: usa los datos reales. (2) La fracción medida es con
muestreo aleatorio; el TPE concentra la búsqueda y suele superarla, así que la proyección de tiempo es conservadora.
(3) Con pocos completos la estimación es ruidosa (se informa la cantidad).
"""
import argparse, os, re, shutil, subprocess, sys, tempfile, time

ap = argparse.ArgumentParser()
ap.add_argument('--repo', default='.'); ap.add_argument('--datos', default='.'); ap.add_argument('--simbolo', default='EURUSDm')
ap.add_argument('--umbrales', default='50,200'); ap.add_argument('--n-sim', type=int, default=100)
ap.add_argument('--n-sim-final', type=int, default=20000); ap.add_argument('--n-simbolos', type=int, default=28)
ap.add_argument('--timeout', type=int, default=7200)
a = ap.parse_args()
repo, datos, sim = os.path.abspath(a.repo), os.path.abspath(a.datos), a.simbolo
pq = os.path.join(datos, f'nexus_df_salida_3D_{sim}_MultiZ.parquet')
if not os.path.exists(pq): sys.exit(f"No existe {pq}")
f3 = open(os.path.join(repo, 'Fase_3.py'), encoding='utf-8').read()

def parchear(src, umbral):
    s = re.sub(r"LISTA_SIMBOLOS =  \[.*?\]\n", f"LISTA_SIMBOLOS = ['{sim}']\n", src, count=1, flags=re.S)
    for nombre, valor in (('MIN_OPS_IS_REPORTE', umbral), ('N_SIMULACIONES', a.n_sim), ('STARTUP_TRIALS', 10**9)):
        s, n = re.subn(rf"^{nombre} = \d+", f"{nombre} = {valor}", s, count=1, flags=re.M)
        if n != 1: sys.exit(f"No encontré {nombre} en Fase_3.py")
    # solo en la copia: imprimir SIEMPRE los conteos (el original solo avisa si hay menos completos que el objetivo)
    s = s.replace("if completas_L < N_SIMULACIONES:", "if True:").replace("if completas_S < N_SIMULACIONES:", "if True:")
    return s

filas = []
for u in [int(x) for x in a.umbrales.split(',')]:
    w = tempfile.mkdtemp(prefix=f'piloto_f3_{u}_')
    for f in ('nexus_tablero.py', 'nexus_formulas_core.py'): shutil.copy(os.path.join(repo, f), w)
    os.symlink(pq, os.path.join(w, os.path.basename(pq)))
    open(os.path.join(w, 'Fase_3.py'), 'w', encoding='utf-8').write(parchear(f3, u))
    print(f"\n== Umbral {u}: corriendo (carpeta temporal {w}) ...", flush=True)
    t0 = time.time()
    r = subprocess.run([sys.executable, 'Fase_3.py'], cwd=w, capture_output=True, text=True, timeout=a.timeout)
    dt = time.time() - t0
    out = r.stdout + r.stderr
    if r.returncode != 0: print(out[-2000:]); sys.exit(f"Fase_3 falló con umbral {u}")
    njobs = [int(x) for x in re.findall(r"N_JOBS calibrado=(\d+)", out)]
    conteos = re.findall(r"ALERTA (LONG|SHORT) \| Fold (\d+)\] Enjambre finalizó con (\d+)/(\d+) trials completos \(Total evaluados: (\d+)\)", out)
    comp = sum(int(c[2]) for c in conteos); tot = sum(int(c[4]) for c in conteos)
    if not conteos or tot == 0: sys.exit(f"No pude leer conteos en la salida (umbral {u}). Últimas líneas:\n{out[-1500:]}")
    nj = max(njobs) if njobs else (os.cpu_count() or 1)
    filas.append(dict(u=u, dt=dt, comp=comp, tot=tot, nj=nj, det=conteos))
    shutil.rmtree(w, ignore_errors=True)

print("\n" + "=" * 78 + f"\nRESULTADOS PILOTO — símbolo {sim} — N_SIMULACIONES piloto={a.n_sim}, muestreo aleatorio\n" + "=" * 78)
print(f"{'umbral':>7} {'completos':>10} {'evaluados':>10} {'sobreviven':>11} {'seg/trial·núcleo':>17} {'tiempo total(s)':>16}")
for f in filas:
    p = f['comp'] / f['tot']; tn = f['dt'] * f['nj'] / f['tot']
    f['p'] = p; f['tn'] = tn
    print(f"{f['u']:>7} {f['comp']:>10} {f['tot']:>10} {100*p:>10.2f}% {tn:>17.3f} {f['dt']:>16.0f}")
print("\nDetalle por conjunto (dirección, fold): completos/evaluados")
for f in filas:
    print(f"  umbral {f['u']}: " + " | ".join(f"{d[0][0]}F{d[1]}={d[2]}/{d[4]}" for d in f['det']))

print("\n" + "=" * 78 + f"\nPROYECCIÓN (estimación; ver límites en la cabecera del script)\n" + "=" * 78)
cores = os.cpu_count() or 1
for f in filas:
    if f['comp'] == 0:
        print(f"umbral {f['u']}: 0 completos en {f['tot']} evaluados -> fracción < {100/f['tot']:.2f}%: con el tope de x20 NO se alcanzaría el objetivo."); continue
    p = f['p']; evaluar = min(a.n_sim_final / p, a.n_sim_final * 20)
    completos = evaluar * p
    seg_simbolo = 4 * evaluar * f['tn'] / cores
    aviso = "  <-- alcanza el tope x20: se quedaría por debajo del objetivo" if a.n_sim_final / p > a.n_sim_final * 20 else ""
    print(f"umbral {f['u']}: fracción {100*p:.2f}% -> evaluados por conjunto ≈ {evaluar:,.0f} (completos ≈ {completos:,.0f}){aviso}")
    print(f"   ≈ {seg_simbolo/3600:.1f} h por símbolo en {cores} núcleos  ->  ≈ {a.n_simbolos*seg_simbolo/3600:.0f} h para {a.n_simbolos} símbolos (solo Fase 3)")
print("\nLectura: si la fracción de sobrevivientes es muy baja, el arranque aleatorio de 5000 aportará pocos completos al TPE.")
