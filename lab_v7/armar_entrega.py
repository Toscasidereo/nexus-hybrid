# ==============================================================================
# NEXUS LAB-V8 — ARMAR ENTREGA: un solo zip con lo que hay que mirar de una corrida. Uso (desde la carpeta de trabajo):
#     python /ruta/lab_v7/armar_entrega.py [carpeta_de_trabajo]
# 📋 BITÁCORA
#   V0.1 (2026-11-10) — Creación. Orden del CRO: informes auditables, trazables y utilizables por dos lectores (el CRO y el sistema).
#     Junta, sin modificar nada: Resumen_Fase4_*.md, Manifiesto_Fase4_*.json, Vista_Fase4_*.csv, Censo_Fase4_*.csv, Reporte_OOS_Phase4_*.csv,
#     Cerebro_MQL5_*.txt, Reporte_Fase3_WFO_*.csv, *.log, *.env, COMMIT.txt del código y, de las carpetas F45_*, los .csv/.json/.md/.txt
#     (los .parquet y las imágenes de F45 quedan fuera por tamaño; se listan en INDICE.txt).
#     Solo lee. No borra ni cambia archivos. Escribe entrega_AAAAMMDD_HHMM.zip e imprime su tamaño.
# ==============================================================================
import os, sys, glob, zipfile, datetime, hashlib

PATRONES = ('Resumen_Fase4_*.md', 'Manifiesto_Fase4_*.json', 'Vista_Fase4_*.csv', 'Censo_Fase4_*.csv', 'Reporte_OOS_Phase4_*.csv',
            'Cerebro_MQL5_*.txt', 'Reporte_Fase3_WFO_*.csv', '*.log', '*.env')
EXT_F45 = ('.csv', '.json', '.md', '.txt')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    carpeta = os.path.abspath(args[0] if args else os.getcwd())
    aqui = os.path.dirname(os.path.abspath(__file__))
    archivos = []
    for pat in PATRONES: archivos += sorted(glob.glob(os.path.join(carpeta, pat)))
    fuera = []
    for d in sorted(glob.glob(os.path.join(carpeta, 'F45_*'))):
        for raiz, _dirs, nombres in os.walk(d):
            for n in sorted(nombres):
                r = os.path.join(raiz, n)
                (archivos if n.lower().endswith(EXT_F45) else fuera).append(r)
    archivos = list(dict.fromkeys(archivos))
    if not archivos: sys.exit(f"No hay nada que entregar en {carpeta}")
    nombre = os.path.join(carpeta, f"entrega_{datetime.datetime.now():%Y%m%d_%H%M}.zip")
    indice = [f"ENTREGA {os.path.basename(nombre)} | carpeta {carpeta}", '', 'INCLUIDOS (bytes, sha1):']
    with zipfile.ZipFile(nombre, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for r in archivos:
            rel = os.path.relpath(r, carpeta); z.write(r, rel)
            h = hashlib.sha1(open(r, 'rb').read()).hexdigest()
            indice.append(f"  {rel} | {os.path.getsize(r)} | {h}")
        for c in (os.path.join(aqui, '..', 'COMMIT.txt'), os.path.join(aqui, 'COMMIT.txt')):
            if os.path.isfile(c): z.write(c, 'COMMIT.txt'); indice.append(f"  COMMIT.txt | {open(c, encoding='utf-8').read().strip()}"); break
        indice += ['', 'NO INCLUIDOS (por tamaño; quedan en la carpeta de trabajo):'] + [f"  {os.path.relpath(r, carpeta)} | {os.path.getsize(r)}" for r in fuera]
        z.writestr('INDICE.txt', '\n'.join(indice) + '\n')
    print(f"{nombre} | {len(archivos)} archivos | {os.path.getsize(nombre) / 2**20:.2f} MB | fuera por tamaño: {len(fuera)}")


if __name__ == '__main__':
    main()
