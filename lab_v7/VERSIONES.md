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
| Documentos | `README.md` (notas iniciales) · `DEBATE_VIDA_V3.md` (solo formato de tablas: barras escapadas) |

**Sin cambios respecto de lab-v7 (son de v7):**
`Fase_3_lab.py` · `lab_escala.py` · `v7_metricas.py` · `v7_pruebas.py` · `v7_pruebas_resultados.json` · `vida_pruebas.py` · `vida_pruebas_resultados.json` · `correr_lab.sh` · `correr_f3_lab.sh` · `ESPECIFICACION_VIDA_V3.md`

Nota (2026-11-08): Fase 3 no cambiaba en v8; las reformas empezaban en Fase 4.

**Actualización 2026-11-13:** `Fase_3_lab.py` pasa a "modificado en v8" (F3-V52: `NEXUS_LAB_METRICA=v52`; CENSO-F3: `NEXUS_LAB_F3_CENSO`). `Fase_4_lab.py` y `lab_informes.py` agregan JUEZ-V52 (`NEXUS_LAB_F3=v52`, `NEXUS_LAB_METRICA=v52`). Fase 4.5 A/B no se adaptan: con v52 el corredor corre solo Fase 4. Pruebas L21–L23 en `lab_pruebas.py`.

*Medido con `git diff --name-status origin/lab-v7 origin/lab-v8` (2026-11-08). Esta lista es una instantánea: cuando una rama cambie, se actualiza o se regenera con ese comando.*

## Cambios posteriores a la instantánea

| Fecha | Commit | Qué cambió |
|---|---|---|
| 2026-11-09 | df69b3a | Parches H-AUD8-01 (`lab_escala_v` en `Fase_4_lab.py`: la decisión sin dato de actividad se excluye del ajuste) y H-AUD8-02 (`_bloque_mql5`: el bloque RANK #1 termina en salto de línea). Pruebas L18 y L19 en `lab_pruebas.py`. La rama `lab-v7` NO lleva estos parches. |
| 2026-11-10 | ba9a4ca, 2fb54cf | Solo documentos: notas en `README.md` (registros, alcance de las pruebas de extremo a extremo, lab-v7 se corre desde lab-v8) y tablas de `DEBATE_VIDA_V3.md` con barras escapadas. Sin cambios de código. |
| 2026-11-10 | (commit de informes) | Informes de Fase 4, con luz verde del CRO. Nuevos: `lab_informes.py`, `armar_entrega.py`. Modificados: `Fase_4_lab.py` (anota valores ya calculados y escribe censo, vista, resumen y manifiesto con `NEXUS_LAB_CENSO=1`), `tablero_lab.env`, `correr_tablero.sh`, `verificar_vm.py`, `lab_pruebas.py` (L20), `LEEME_VM.md`. Cerebro y `Reporte_OOS` no cambian. |
