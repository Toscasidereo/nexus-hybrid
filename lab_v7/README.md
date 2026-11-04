# NEXUS LAB-V7 — laboratorio paralelo de Score_v7 y T_v2

Rama `lab-v7`, creada desde `main` el 2026-11-01 por orden del CRO. **No se fusiona con `main`.** No modifica ningún archivo del laboratorio (`nexus_formulas_core.py`, `Fase_*.py`, EA). Todo el código vive en `lab_v7/`.

Fórmulas: `claude/metricas_score_v7_propuesta.md` (sección 6) del proyecto Auditoría. Auditoría de la propuesta: `claude/auditoria_score_v7.md`.

## Principio: aditivo
`Score_v7` y `T_v2` se calculan **al lado** de `Score_final` y `T(t)`, sobre los mismos casos. No cambian la selección ni la exportación. El reemplazo se decide después, con la comparación pareada de la corrida de producción.

## Archivos
| Archivo | Qué hace |
|---|---|
| `v7_metricas.py` | Fusión de ráfagas en señales, alfa (opción A o B), C1 (DSR), C2, C3, C4, `Score_v7`, `T_v2`. Autónomo (numpy, scipy, numba). |
| `v7_pruebas.py` | Controles sintéticos P1-P7. `python lab_v7/v7_pruebas.py` (~10 s). |
| `v7_pruebas_resultados.json` | Resultado de la última corrida de los controles. |
| `Fase_4_lab.py` | Copia de `Fase_4_V12_0.py` con tres interruptores (Ridge de tamaño, Ridge de cierre, gemelo nulo). Apagados = igual que `main`. |
| `lab_pruebas.py` | Controles L1-L8 de la copia (paridad bit a bit con `main`, sin fuga IS→OOS, targets, grilla de K, interruptores, **L8: el texto exportado del Ridge de tamaño, leído por una emulación escalar del EA, reproduce la escala del lab igual bit a bit**). `python lab_v7/lab_pruebas.py` (~40 s). |
| `lab_pruebas_resultados.json` | Resultado de la última corrida. |
| `lab_escala.py` | Kernels de la escala de `v_req` compartidos por Fase 4 del lab, Fase 4.5 A del lab y el EA gemelo (mismo orden de operaciones). |
| `Fase_4_5_lab_A.py` / `Fase_4_5_lab_B.py` | Copias de Fase 4.5 A y B. Mismo tag por las mismas variables `NEXUS_LAB_*`; A lee `tam_*` del `.txt` y simula con la escala (`simular_motor` recibe `escala_v`). Apagadas = main. |
| `correr_lab.sh` | Corre Fase 4 lab → 4.5 A → 4.5 B con los mismos interruptores. Fases 0, 1&2 y 3 no cambian. |
| `EA_V12.01_LAB.txt` | **EA gemelo.** Copia de `EA_V12.01.txt` (el original no se toca; solo se agregaron líneas) con el Ridge de tamaño del lab (`tam_*`, `LabActividad`, `LabEscalaTamano`). Con `tam_modo = 0` se comporta como V12.01. |

## Entrada del módulo
Por símbolo y ventana: arrays `O, H, L, C` (velas M1 de la ventana evaluada), `pm` (100 JPY, 10 000 resto), `c` (spread en pips) y la tabla de trades del motor: dirección, vela de entrada, vela de salida, neto en pips con spread incluido. `nt` = juegos evaluados por el buscador y `sigma_sr` = desvío del Sharpe entre esos juegos, para el umbral `SR0` del DSR.

## Controles (reglas fijadas antes de correr)
| # | Prueba | Criterio | Resultado 2026-11-01 |
|---|---|---|---|
| P1 | Fusión de ráfagas en caso armado a mano | exacto | Pasa |
| P2 | `dsr()` frente a la fórmula de Bailey y López de Prado; `SR0` monótono | exacto | Pasa |
| P3 | Control negativo (azar, con spread), 150 réplicas | C1 ≥ 0.95 en ≤ 12 % | 0 % |
| P3b | Calibración (azar, sin spread), 300 réplicas | entre 1 % y 12 % (nominal 5 %) | 6.7 % |
| P4 | Control positivo (régimen de deriva sembrado), 40 réplicas | C1 ≥ 0.95 en ≥ 90 % | 100 %, Score_v7 mediano 83.8 |
| P5 | Deriva pura, solo largos, 60 réplicas | alfa A: ≤ 12 %; DSR crudo ≥ 50 % | 0 % frente a 100 %: la opción A elimina la deriva |
| P6 | T_v2 no mecánico (cortar salidas al azar) | sube ≤ 0.02 | Baja 0.034 |
| P7 | Documenta H-V7-06 | informativo | FET_v2 = 0 da T_v2 = 0 |

`[HECHO VERIFICADO]` en datos sintéticos. No hay evidencia de mercado todavía.

## Observaciones registradas al implementar
- **H-V7-06 (Baja):** la propuesta dice que la media geométrica evita que un factor anule a los demás. No es así: con `FET_v2 = 0` (trade que nunca estuvo en ganancia neta tras la segunda vela), `T_v2 = 0`. Se implementó la fórmula tal cual; cambiarla (por ejemplo, un piso en cada factor) exige orden del CRO.
- La máscara de velas fantasma (sección 6.8) no se recibe; el módulo usa todas las velas.
- La prueba P7 usa una serie plana (h = 0) y emite una advertencia de división por cero. En datos reales h > 0.
- `escala_h` falla si la serie es más corta que la ventana de 60 velas.

## Protocolo para usar datos reales (fijado antes)
1. Unidades agrupadas por símbolo y transición; bootstrap por bloques de tiempo; dos colas.
2. Métrica primaria única: diferencia pareada (top-10 por Score_v7 menos top-10 por Score_final) en el tramo siguiente, en pips por señal, con intervalo. Margen de relevancia 0.2 pips por señal [DEFAULT / CRO-OVERRIDE].
3. `N_t` real y efectivo de Optuna para el DSR; ≥ 30 réplicas nulas; informe de cobertura (casos medibles de cada criterio).
4. Opción A y opción B del alfa informadas por separado; la opción B es la medida de neutralidad.
5. Un resultado sin diferencia mayor que el margen se informa como "no concluyente" o "sin efecto mayor que el margen", nunca como "no hay efecto".
6. Datos: salida de la corrida de producción (VM). Hasta entonces, el laboratorio solo tiene controles sintéticos.

## Fase_4_lab.py: Ridges nuevos, aditivos
Se ejecuta igual que Fase 4 (mismos insumos: CSV de Fase 3 y parquet de Fase 1&2). Interruptores por variable de entorno:

| Variable | Valores | Qué hace |
|---|---|---|
| `NEXUS_LAB_TAMANO` | `off` (defecto), `A`, `B` | **Ridge de tamaño.** `A`: Ridge entrenado en el IS con target MFE (features de Ridge 1 + actividad). `B`: actividad pura. La escala por vela (0.25-4, normalizada por la mediana IS) multiplica `v_req`. |
| `NEXUS_LAB_CIERRE` | `T_terminal` (defecto), `dT_cont`, `G_pips` | **Ridge de cierre** (Ridge 2) con otro target. `dT_cont` = lo que falta de T. `G_pips` = pips finales menos profit actual. Con target distinto la grilla de K son los percentiles 0-50 de la predicción IS. |
| `NEXUS_LAB_NULO` | `0` (defecto), `1` | **Gemelo nulo.** Desplaza en círculo la escala dentro de cada ventana y permuta el target de Ridge 2 entre fotos del IS. Con todo en defecto es el gemelo nulo del Ridge 2 de `main`. |

Los archivos de salida llevan el sufijo `_LAB_<tamaño>_<cierre>[_NULO]`: no pisan los de `main`.

**Corridas pareadas por configuración:** (1) `main` o la copia en defecto; (2) el modo a probar; (3) el modo a probar con `NEXUS_LAB_NULO=1`. La mejora cuenta solo si (2) supera a (1) y a (3) sobre los mismos candidatos.

**Límites declarados**
- `[HECHO VERIFICADO]` Con `escala_v = 1` la copia es idéntica bit a bit a `main` en extractores y simuladores (long y short). Probado en datos sintéticos.
- `[PENDIENTE / NO VERIFICABLE]` `procesar_candidato` completo no se ejecutó: falta el parquet de Fase 1&2 y el CSV de Fase 3 reales. Las funciones nuevas están probadas aisladas.
- La actividad usa Σ|ΔOpen| de 60 velas (el parquet no trae Close). La exploración usó Close.
- **EA gemelo (2026-11-04):** los modos de TAMAÑO (A y B) se exportan con campos `tam_*` y los ejecuta `EA_V12.01_LAB.txt`. Los modos de CIERRE (`dT_cont`, `G_pips`) usan los mismos campos de Ridge 2 y `k_abortar`: no requieren cambios del EA. `[PENDIENTE / NO VERIFICABLE]`: compilación en MetaEditor y paridad M7 contra Python (no hay compilador MQL5 en el entorno de trabajo).
- La escala por vela se calcula con parámetros redondeados a 8 decimales y sumas secuenciales (no `pandas.rolling`), para que Python y EA hagan las mismas operaciones. Sin historia suficiente (menos de 61 velas) el EA usa escala neutra del modo.
- Los nulos (`NEXUS_LAB_NULO`) no se exportan al EA: son controles de Python.
- La grilla de K de los modos de cierre se redondea a 5 decimales (el export escribe `k_abortar` con %.5f).
- El gemelo nulo cubre solo estas piezas. Ridge 1 y la Cabeza B no tienen gemelo.
- Falta `G_acotado` (requiere la actividad de entrada por trade).

## Cómo correr la cadena del lab
Fases 0, 1&2 y 3 se corren una vez con los scripts de la raíz (sin cambios). Después, desde la carpeta de trabajo con sus salidas: `bash lab_v7/correr_lab.sh [off|A|B] [T_terminal|dT_cont|G_pips] [0|1]`. Las tres fases del lab leen las mismas variables `NEXUS_LAB_*`, así que el tag y las carpetas (`F45_V12_E3_LAB_...`) coinciden. `[PENDIENTE / NO VERIFICABLE]`: la cadena nunca se ejecutó de punta a punta con datos reales.

## Pendiente
- Adaptador que lea la salida de Fase 3 (tabla de trades por caso) y llame a `score_v7` y `t_v2`. Se escribe cuando exista una muestra real de esa salida.
- Prueba 2 y 3 de T_v2 (contra sustitutos y como target de Ridge). `T_v2` como target de cierre: agregar un modo a `lab_target_cierre` cuando se decida (H-V7-06 primero).
- Primera corrida real de `Fase_4_lab.py` en la VM, con las tres corridas pareadas.
- ~~Fase 4.5~~ **hecho (2026-11-04):** `Fase_4_5_lab_A/B.py` leen el tag del lab y `tam_*`. Controles L9–L11 pasan en datos sintéticos; no corrieron con datos reales.
- La escala de Fase 4.5 se calcula sobre todo el parquet (el EA la aplica siempre); la de Fase 4 solo existe en la ventana IS+OOS del fold. Coinciden en el OOS del fold, que es donde Fase 4.5 chequea paridad.
- Compilar `EA_V12.01_LAB.txt` en MetaEditor y repetir M7 con un cerebro de modo A y otro de modo B.
