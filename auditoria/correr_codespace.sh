#!/usr/bin/env bash
# Corre TODAS las pruebas de solo lectura de las auditorías M0-M2 y deja un único informe de texto.
# NO modifica el repo: copia los .py a una carpeta temporal con nombres canónicos y trabaja ahí.
#
# Uso (desde cualquier carpeta):
#   bash auditoria/correr_codespace.sh              # usa la carpeta actual como repo
#   bash auditoria/correr_codespace.sh /ruta/repo   # o indica el repo
#
# Requiere en la MISMA carpeta que este script: medir_fastmath_tscore.py, paridad_kernels_ciclo.py,
# prueba_cache_numba.sh. Requiere: python3 con numba, numpy, pandas, pyarrow (pip install numba pandas pyarrow).
set -u
REPO="$(cd "${1:-$(pwd)}" && pwd)"
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$AQUI/informe_codespace_$(date +%Y%m%d_%H%M%S).txt"
T="$(mktemp -d)"; mkdir -p "$T/repo"

say() { echo -e "$*" | tee -a "$OUT"; }
bloque() { say "\n=================================================================\n$1\n================================================================="; }

# --- copia con nombres canónicos (sin tocar el repo) ---
pick() { for c in "$@"; do [ -f "$REPO/$c" ] && { echo "$REPO/$c"; return; }; done; }
copiar() { local dst="$1"; shift; local src; src="$(pick "$@")"
  if [ -n "$src" ]; then cp "$src" "$T/repo/$dst"; say "copiado: $(basename "$src") -> $dst"; else say "FALTA: $dst (buscado: $*)"; fi; }

bloque "0. IDENTIDAD DEL REPO"
say "repo: $REPO"
say "commit: $(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo 'no es repo git')"
say "rama:   $(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '-')"
say "tag pre-auditoria apunta a: $(git -C "$REPO" rev-parse 'pre-auditoria^{commit}' 2>/dev/null || echo 'no encontrado')"
copiar Fase_0.py Fase_0.py
copiar Fase_1___2.py Fase_1___2.py
copiar Fase_3.py Fase_3.py
copiar Fase_4_V12_0.py Fase_4_V12_0.py Fase_4_V12.0.py
copiar Fase_4_5_V_12_0_A.py Fase_4_5_V_12_0_A.py Fase_4.5_V_12.0_A.py
copiar Fase_4_5_V_12_0_B.py Fase_4_5_V_12_0_B.py Fase_4.5_V_12.0_B.py
copiar nexus_formulas_core.py nexus_formulas_core.py
copiar nexus_tablero.py nexus_tablero.py
copiar extraxtor_mt5_rangofecha.py extraxtor_mt5_rangofecha.py
say "\nSHA-256 (16 primeros) de cada archivo copiado:"
( cd "$T/repo" && sha256sum *.py | awk '{print substr($1,1,16), $2}' ) | tee -a "$OUT"

bloque "1. ENTORNO (versiones reales; el repo no las fija)"
say "python: $(python3 --version 2>&1)"
python3 - <<'EOF' 2>&1 | tee -a "$OUT"
import importlib
for m in ("numba","llvmlite","numpy","pandas","pyarrow","sklearn","optuna","psutil"):
    try: print(f"{m}: {importlib.import_module(m).__version__}")
    except Exception as e: print(f"{m}: NO INSTALADO ({type(e).__name__})")
EOF
say "CPU: $(nproc) núcleos | $(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2 | xargs)"
say "RAM visible (free -b):"; free -b 2>&1 | tee -a "$OUT"
say "cgroup v2 memory.max: $(cat /sys/fs/cgroup/memory.max 2>/dev/null || echo 'no existe')"
say "cgroup v1 limit:      $(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo 'no existe')"
say "(Si memory.max/limit es MENOR que la RAM de free, psutil sobreestima la RAM disponible: caso H-RAM-01)"

if ! python3 -c "import numba, numpy, pandas" 2>/dev/null; then
  say "\nFALTA numba/numpy/pandas. Ejecuta: pip install numba pandas pyarrow   y vuelve a correr este script."; exit 1; fi

bloque "2. COMPILACIÓN SINTÁCTICA"
for f in "$T"/repo/*.py; do python3 -m py_compile "$f" 2>&1 && say "compila: $(basename "$f")" || say "ERROR de sintaxis: $(basename "$f")"; done

bloque "3. VERIFICADOR DE TABLEROS (contratos entre fases)"
V="$(pick auditoria/verificar_tableros.py 'auditoria/Verificar Tableros')"
if [ -n "$V" ]; then python3 "$V" "$T/repo" --salida "$T/tablero_produccion.json" 2>&1 | tee -a "$OUT"; cp "$T/tablero_produccion.json" "$AQUI/" 2>/dev/null
else say "No se encontró el verificador en auditoria/."; fi

bloque "4. H-CACHE-01 — caché de Numba entre archivos"
bash "$AQUI/prueba_cache_numba.sh" 2>&1 | tee -a "$OUT"

bloque "5. H-FM-01 — fastmath del T-score del core (2.000.000 de entradas)"
( cd "$T" && python3 -I "$AQUI/medir_fastmath_tscore.py" "$T/repo" 2000000 ) 2>&1 | tee -a "$OUT"

bloque "6. H-KER-01 — paridad bit a bit de kernels de ciclo F3 vs F4 vs 4.5A"
( cd "$T" && python3 -I "$AQUI/paridad_kernels_ciclo.py" "$T/repo" 200000 5 ) 2>&1 | tee -a "$OUT"

bloque "FIN"
say "Informe guardado en: $OUT"
say "Temporales en: $T (puedes borrarlos). El repo NO fue modificado."
