# Qué archivo es de qué versión (carpeta `lab_v7/`)

La carpeta se llama `lab_v7` en todas las ramas de laboratorio por razones históricas: así `git diff` entre ramas muestra solo lo que cambió. **La versión la dice la rama**, no el nombre de la carpeta ni de los archivos.

- Rama `lab-v7`: estado de lab-v7.
- Rama `lab-v8`: nació de `lab-v7` (commit ff7ae24); contiene lab-v7 más las reformas de v8.

Cómo saber en qué rama estás: `git branch --show-current`. Cómo ver solo lo que añade v8: `git diff --name-status lab-v7 lab-v8` (en GitHub: `compare/lab-v7...lab-v8`). Dentro de cada archivo, las bitácoras de cabecera (`BITÁCORA LAB-V7 ...`, `BITÁCORA LAB-V8 ...`) y las marcas `[LAB-V7]` / `[LAB-V8]` del código señalan el origen de cada cambio.

## Estado de los archivos en `lab-v8`

**Nuevos en v8 (no existen en lab-v7):**
`ESPECIFICACION_VIDA_V3_EXT.md` · `v8_pruebas.py` · `v8_pruebas_resultados.json` · este archivo, `VERSIONES.md`

**Modificados en v8 (nacieron en v7):**

| Grupo | Archivos |
|---|---|
| Código del laboratorio | `Fase_4_lab.py` · `Fase_4_5_lab_A.py` · `Fase_4_5_lab_B.py` · `vida_v3.py` |
| EA gemelo y su chequeo con g++ | `EA_V12.01_LAB.txt` · `lab_compat_ea.py` · `lab_compat_ea_resultados.json` |
| Pruebas | `lab_pruebas.py` · `lab_pruebas_resultados.json` |
| Tablero y VM | `tablero_lab.env` · `correr_tablero.sh` · `verificar_vm.py` · `LEEME_VM.md` |

**Sin cambios respecto de lab-v7 (son de v7):**
`Fase_3_lab.py` · `lab_escala.py` · `v7_metricas.py` · `v7_pruebas.py` · `v7_pruebas_resultados.json` · `vida_pruebas.py` · `vida_pruebas_resultados.json` · `correr_lab.sh` · `correr_f3_lab.sh` · `README.md` (salvo la nota inicial) · `ESPECIFICACION_VIDA_V3.md` · `DEBATE_VIDA_V3.md`

Nota: Fase 3 no cambia en v8. Las reformas de v8 empiezan en Fase 4.

*Medido con `git diff --name-status origin/lab-v7 origin/lab-v8` (2026-11-08). Esta lista es una instantánea: cuando una rama cambie, se actualiza o se regenera con ese comando.*
