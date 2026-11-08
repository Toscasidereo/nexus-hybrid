# NEXUS LAB-V7 — laboratorio paralelo de Score_v7 y T_v2

> **Versiones.** Esta carpeta es la misma en las ramas `lab-v7` y `lab-v8`: la versión la dice la rama. En `lab-v8` se añaden las reformas de Vida v3 (ver `VERSIONES.md` para saber qué archivo es de cada versión y `ESPECIFICACION_VIDA_V3_EXT.md` para la extensión). El resto de este README describe lab-v7.

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
| `lab_pruebas.py` | Controles L1-L16 de las copias (paridad bit a bit con `main`, sin fuga IS→OOS, targets, grilla de K, interruptores, **L8: el texto exportado del Ridge de tamaño, leído por una emulación escalar del EA, reproduce la escala del lab igual bit a bit**). `python lab_v7/lab_pruebas.py` (~40 s). |
| `lab_pruebas_resultados.json` | Resultado de la última corrida. |
| `lab_escala.py` | Kernels de la escala de `v_req` compartidos por Fase 4 del lab, Fase 4.5 A del lab y el EA gemelo (mismo orden de operaciones). |
| `Fase_4_5_lab_A.py` / `Fase_4_5_lab_B.py` | Copias de Fase 4.5 A y B. Mismo tag por las mismas variables `NEXUS_LAB_*`; A lee `tam_*` del `.txt` y simula con la escala (`simular_motor` recibe `escala_v`). Apagadas = main. |
| `Fase_3_lab.py` | Copia de `Fase_3.py` con `NEXUS_LAB_METRICA` (híbrido Score_v7) y modo de medición opcional. Ver sección propia. |
| `correr_f3_lab.sh` | Corre solo Fase 3 lab (la fase pesada, aparte). |
| `correr_lab.sh` | Corre Fase 4 lab → 4.5 A → 4.5 B con los mismos interruptores; 5.º parámetro elige el CSV de Fase 3. Fases 0 y 1&2 no cambian. |
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
| `NEXUS_LAB_METRICA` | `final` (defecto), `v7` | **Métrica de selección de Fase 4.** `final` = `Score_final` (igual a `main`). `v7` = `Score_v7` (DSR, estabilidad, captura frente al gemelo nulo R=20, cola) en la compuerta de la base, el escaneo de K, las evaluaciones OOS y el ranking. El reporte trae ambas métricas sobre los mismos trades (`SF_IS, V7_IS, SF_OOS, V7_OOS`). `Base_Rechazado` sigue por `Score_final` para no romper la paridad con Fase 4.5. Límites: sin deflación por el N_t de Optuna de Fase 3 (Fase 3 sigue con `Score_final`); `T_v2` como target de Ridge no está implementado (H-V7-06); Close≈Open; `n_min` = `min_trades` existente. Comparación: correr `final` y `v7` y cotejar el OOS de cada ganador. |

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

## Fase_3_lab.py: Score_v7 en la búsqueda (2026-11-05)
Copia de `Fase_3.py` V5.11 con dos interruptores. Sin ninguno, es `Fase_3.py` (control L16: solo cambian 6 líneas de una lista cerrada).
| Variable | Valores | Efecto |
|---|---|---|
| `NEXUS_LAB_METRICA` | `final` (defecto), `v7` | `v7` = **híbrido**. (1) Optuna maximiza `Score_v7` con R=0: C1 (DSR), C2 (estabilidad) y C4 (cola); C3 (captura frente al gemelo nulo) queda neutro en 0.5. La escala `h` y los arreglos float64 se calculan una vez por ventana. (2) El top se reevalúa con `Score_v7` completo (nulo R=20) en IS y OOS. (3) El DSR de IS se deflacta con el **N_t real** (trials completos del estudio) y `sigma_sr` (desvío del Sharpe de alfa entre esos trials). (4) El rango final se ordena por `Score_v7` completo en IS, nunca por OOS. |
| `NEXUS_LAB_F3_MEDIR` | `0` (defecto), `N` | Modo de medición: un símbolo, un fold, N trials, sin escribir CSV; imprime ms por trial de cada métrica. Opcional: no hace falta correrlo. |
El CSV de `v7` se llama `Reporte_Fase3_WFO_V5.8_{SIMBOLO}_MV7.csv` (no pisa el de main) y trae las columnas extra `Metrica_F3, SF_IS, V7_IS, SF_OOS, V7_OOS, N_t, Sigma_SR`. Fase 4 lab lo lee con `NEXUS_LAB_F3=v7`.
**El nulo de `Score_v7` (C3) no es una corrida aparte:** son 20 réplicas dentro del cálculo, sobre la muestra evaluada (IS o OOS). Costo medido con datos sintéticos de 725 mil velas: `Score_final` 0,02-0,3 ms; `Score_v7` completo 25-35 ms, de los cuales ~9,5 ms eran `escala_h` (ahora en caché). El costo real sobre datos reales `[PENDIENTE / NO VERIFICABLE]`.
Límites: `v7` reordena y deflacta el top que Optuna encuentra con `Score_v7(R=0)`; el nulo no guía la búsqueda. N_t = trials completos (sobreestima los independientes: deflación conservadora). Close≈Open. Nada corrió con datos reales.

## Cómo correr la cadena del lab
Fases 0 y 1&2 se corren una vez con los scripts de la raíz. Fase 3 se corre con el script de la raíz (main) o con `lab_v7/correr_f3_lab.sh [final|v7]` (lab). Después, desde la carpeta de trabajo: `bash lab_v7/correr_lab.sh [off|A|B] [T_terminal|dT_cont|G_pips] [0|1] [final|v7] [main|v7]`. El 5.º parámetro elige qué CSV de Fase 3 lee Fase 4 (`main` o `v7`). Las tres fases de abajo leen las mismas variables `NEXUS_LAB_*`, así que el tag (`_MV7`, `_F3V7`) y las carpetas coinciden.
Cadenas pareadas para comparar (cada una es una corrida aparte):
1. **main:** Fase 3 de la raíz + `correr_lab.sh` en defecto.
2. **Solo Fase 4 v7:** Fase 3 de la raíz + `correr_lab.sh off T_terminal 0 v7 main`.
3. **Solo Fase 3 v7:** `correr_f3_lab.sh v7` + `correr_lab.sh off T_terminal 0 final v7`.
4. **Cadena v7 completa:** `correr_f3_lab.sh v7` + `correr_lab.sh off T_terminal 0 v7 v7`.
La mejora cuenta si la cadena 4 supera a la 1 en el OOS y en la ventana ciega de Fase 4.5. `[PENDIENTE / NO VERIFICABLE]`: la cadena nunca se ejecutó de punta a punta con datos reales.

## Pendiente
- Adaptador que lea la salida de Fase 3 (tabla de trades por caso) y llame a `score_v7` y `t_v2`. Se escribe cuando exista una muestra real de esa salida.
- Prueba 2 y 3 de T_v2 (contra sustitutos y como target de Ridge). `T_v2` como target de cierre: agregar un modo a `lab_target_cierre` cuando se decida (H-V7-06 primero).
- Primera corrida real de `Fase_3_lab.py` y `Fase_4_lab.py` en la VM, con las cadenas pareadas de arriba.
- ~~Fase 4.5~~ **hecho (2026-11-04):** `Fase_4_5_lab_A/B.py` leen el tag del lab y `tam_*`. Controles L9–L11 pasan en datos sintéticos; no corrieron con datos reales.
- La escala de Fase 4.5 se calcula sobre todo el parquet (el EA la aplica siempre); la de Fase 4 solo existe en la ventana IS+OOS del fold. Coinciden en el OOS del fold, que es donde Fase 4.5 chequea paridad.
- Compilar `EA_V12.01_LAB.txt` en MetaEditor y repetir M7 con un cerebro de modo A y otro de modo B.

---
## Vida v3 y tablero de control (2026-11-06)
- `vida_v3.py`: cinco descriptores de la vida del trade (EFR, D_h, FET_v3, REC, RIT) y compuesto V3 (pesos iguales 0.2, valores de partida). Constantes de normalización solo del IS. Especificación: `ESPECIFICACION_VIDA_V3.md`. Pruebas: `vida_pruebas.py` (V1–V7).
- `NEXUS_LAB_CIERRE=V3`: el Ridge 2 aprende V3 terminal; la Cabeza B sigue en T_terminal (H-V7-08); el ΔT vivo sigue usando T(t) (H-V7-05). El EA no cambia.
- **Tablero único**: edita `tablero_lab.env` y corre `bash correr_tablero.sh [f3|f4|todo]` desde la carpeta con los parquets de Fase 1&2. Valida los valores antes de lanzar. Los scripts anteriores (`correr_lab.sh`, `correr_f3_lab.sh`) siguen funcionando.
- Límites declarados: nada corrió con datos reales; el humo con V3 ejecuta el camino hasta la evaluación OOS pero no el export (datos de prueba sin trades suficientes); el EA lab no está compilado en MetaEditor.

## Compatibilidad de cerebros con el EA lab (2026-11-06)
`python lab_v7/lab_compat_ea.py` compila con g++ el texto REAL de `EA_V12.01_LAB.txt` y lo compara bit a bit con Python:
C1 el bloque exportado por Fase 4 lab (long/short; tamaño off/A/B) compila contra los structs y enums del EA; C2 cobertura de índices; C3 escala de tamaño y actividad idénticas; C4 T_pred del Ridge 2 idéntico; C5 efecto del redondeo del export (0 en la escala).
Hallazgo H-EA-ULP (cerrado en el EA lab): el EA sumaba w8·dT + w9·(dT·Θ) como un bloque, Python en secuencia; 1 ULP en ~20% de evaluaciones. EA main sin modificar (mismo patrón, abierto).
Pendiente: compilación en MetaEditor (MQL5 real), y paridad de las características de entrada (Fid, D_, C_, T(t)) bajo el compilador de MetaQuotes.
