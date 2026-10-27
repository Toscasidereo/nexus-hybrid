#!/usr/bin/env bash
# H-CACHE-01 — ¿Un cambio en una función njit(cache=True) de OTRO archivo invalida el caché del llamador?
# Reproduce el patrón real: Fases 3/4/4.5 (llamadores, cache=True) invocan calcular_t_score_trade_numba
# de nexus_formulas_core.py (otro archivo, cache=True). Solo escribe en un directorio temporal.
# Uso: bash prueba_cache_numba.sh
set -e
D="$(mktemp -d)"; cd "$D"
cat > mod_b.py <<'EOF'
from numba import njit
@njit(cache=True)
def g(x):
    return x + 1
EOF
cat > mod_a.py <<'EOF'
from numba import njit
from mod_b import g
@njit(cache=True)
def f(x):
    return g(x) * 2
EOF
run() { python3 -I -c "import sys; sys.path.insert(0,'.'); import mod_a; print('f(1) =', mod_a.f(1))"; }
echo "corrida 1 (g = x+1): esperado f(1) = 4";   run
sed -i 's/return x + 1/return x + 100/' mod_b.py
echo "corrida 2 (g cambió a x+100): esperado f(1) = 202 si el caché se invalida"; run
rm -f __pycache__/*.nbi __pycache__/*.nbc
echo "corrida 3 (caché borrado): esperado f(1) = 202"; run
echo
echo "Si la corrida 2 mostró 4, el caché del llamador quedó VIEJO tras cambiar el otro archivo."
echo "Directorio temporal: $D (puedes borrarlo)"
