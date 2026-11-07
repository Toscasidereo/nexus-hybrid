# Debate: Vida v3 en lab-v7 — hallazgos y propuestas de mejora (2026-11-07)

**Origen:** auditoría de solo lectura de `lab_v7/vida_v3.py`, `lab_v7/ESPECIFICACION_VIDA_V3.md`, `lab_v7/vida_pruebas_resultados.json` y `lab_v7/Fase_4_lab.py` (l. 1626-1641 y 1850-1880), commit `a7130bc`. No se corrió nada con datos reales.
**Estado:** PROPUESTA PARA DEBATE. Ningún archivo de código cambia hasta la orden del CRO ("LUZ VERDE: PARCHE H-V3-xx").

## 1. Qué es Vida v3
Cinco descriptores de la vida del trade, calculados en cada foto y al cierre (`p` = profit neto de spread, `v` = velas abiertas, `h` = movimiento típico de una hora del par en el IS):

| # | Descriptor | Fórmula | Qué mide |
|---|---|---|---|
| 1 | Captura (EFR) | `(1 + p / (MFE + |MAE| + spread)) / 2` | Dónde está el profit dentro del recorrido |
| 2 | Hundimiento (D_h) | `1 / (1 + |MAE| / h)` | Cuánto fue en contra, en horas típicas |
| 3 | Tiempo a favor (FET_v3) | fracción de fotos con `p > 0` desde la vela 2; 0.5 si `v ≤ 2` | Tiempo ganando |
| 4 | Recuperación (REC) | `(p − p_fondo) / (velas desde el fondo · h/60)`; 0.5 si no hubo hundimiento mayor que el spread | Velocidad de recuperación |
| 5 | Ritmo (RIT) | `p / (v · h/60)` | Ganancia por vela |

Cada uno se lleva a [0, 1] con `(tanh((x − mediana_IS) / MAD_IS) + 1) / 2`; `V3` = promedio (pesos 0.2). Con `NEXUS_LAB_CIERRE=V3`, el Ridge 2 aprende `V3` terminal en lugar de `T_terminal`.

## 2. Lo que está bien
- Causal: los valores vivos usan solo fotos hasta k; la prueba V2 lo confirma (prefijo e igualdad terminal).
- Constantes de normalización y `h` solo del IS.
- La media aritmética evita que un factor en cero anule al compuesto (corrige H-V7-06).
- `h` por par: comparable entre símbolos.
- Pruebas V1-V7 pasan (sintéticas).

## 3. Hallazgos
| ID | Severidad | Dónde | Fallo |
|---|---|---|---|
| H-V3-01 | Media | `lab_target_cierre`, modo V3 (`Fase_4_lab.py` l. 1631-1634) | El target es el **nivel** terminal de V3, repetido en todas las fotos. Abortar compara seguir contra cerrar ahora; el target que corresponde es la **diferencia** (`V3_terminal − V3_vivo`, como `dT_cont`) o los pips restantes (`G_pips`). Con el nivel, el Ridge aborta trades que van a terminar mal aunque cerrarlos ahora sea igual de malo. |
| H-V3-02 | Media | `_vivos_nb`, RIT (`vida_v3.py` l. 47) | `RIT = p / (v·h/60)` premia las salidas tempranas con ganancia: con `h = 4.5`, +2 pips en 2 velas ≈ 13; +15 pips en 120 velas ≈ 1.7; un trade de 1 vela (p ≈ −spread) ≈ −23. Contradice la especificación ("sin premiar la salida temprana"). Las pruebas V3 usan duraciones de 5-60 velas y no cubren ese régimen. |
| H-V3-03 | Baja | `normalizar`, REC (`vida_v3.py` l. 77) | Un trade que nunca se hundió más que el spread recibe 0.5; uno que se hundió y se recuperó rápido recibe más. El trade limpio queda peor ordenado. |
| H-V3-04 | Media | Diagnóstico `R2V_*` (`Fase_4_lab.py` l. 1865-1870) | R² de valores terminales desde features vivas, sin nulo. Las fotos cercanas al cierre ya contienen casi el valor terminal, así que el R² sube de forma mecánica (como el ρ = 0.62 engañoso de `T_terminal` en T1-T3). |

## 4. Propuestas de mejora
| Hallazgo | Propuesta | Alternativa |
|---|---|---|
| H-V3-01 | Nuevo modo `NEXUS_LAB_CIERRE=dV3`: target `V3_terminal − V3_vivo(t)` | Usar `G_pips / h` como target del aborto y V3 solo como diagnóstico |
| H-V3-02 | `RIT = p / (max(v, v_min) · h/60)`, con `v_min = 15` [DEFAULT / CRO-OVERRIDE] | Reemplazar RIT por pips netos en unidades de `h` |
| H-V3-03 | REC = 1.0 cuando no hubo hundimiento relevante | Definir REC como fracción recuperada `(p − p_fondo) / (−p_fondo)` |
| H-V3-04 | Informar `R2V_*` junto al gemelo nulo (`NEXUS_LAB_NULO=1`) y por tramo de vida (primer tercio, segundo, último) | — |
| Pruebas | Agregar a `vida_pruebas.py` trades de 1-3 velas en la prueba de no mecánica | — |

## 5. Preguntas para el debate
1. ¿El aborto debe optimizar calidad de vida (V3) o pips restantes (`G_pips`)? La métrica objetivo final propuesta es pips netos OOS por señal con su MaxDD, contra el gemelo nulo.
2. ¿Qué duración mínima tiene sentido para RIT (`v_min`)? ¿15 velas, o la mediana de duración del IS?
3. ¿REC debe premiar la recuperación o tratar igual al trade que nunca se hundió?
4. ¿Se mantienen los pesos iguales (0.2) hasta ver la matriz de correlación entre descriptores en la primera corrida real?

## 6. Cómo se decide (fijado antes)
Corridas pareadas en la VM, sobre los mismos candidatos: (1) `CIERRE=T_terminal`; (2) `CIERRE=V3`; (3) `CIERRE=dV3` o `G_pips`; cada una con su gemelo nulo. Gana el modo que mejore los pips netos OOS por señal y el MaxDD frente a (1) y frente a su nulo, en la mayoría de los símbolos.
