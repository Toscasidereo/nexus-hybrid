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

## Pendiente
- Adaptador que lea la salida de Fase 3 (tabla de trades por caso) y llame a `score_v7` y `t_v2`. Se escribe cuando exista una muestra real de esa salida.
- Prueba 2 y 3 de T_v2 (contra sustitutos y como target de Ridge).
