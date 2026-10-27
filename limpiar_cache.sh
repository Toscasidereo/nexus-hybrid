#!/usr/bin/env bash
# Borra el caché de Numba (H-CACHE-01). Ejecutar SIEMPRE tras cambiar nexus_formulas_core.py o cualquier kernel,
# y al cambiar de versión de numba/llvmlite. No toca datos ni código.
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null
find . \( -name '*.nbi' -o -name '*.nbc' \) -delete 2>/dev/null
echo "Caché de Numba borrado."
