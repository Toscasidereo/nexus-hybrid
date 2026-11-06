# Vida v3 — especificación (lab-v7, 2026-11-06)

Orden del CRO (2026-11-06): aprobó el diseño de una métrica de la vida del trade con cinco descriptores y pidió implementarlo en el lab.
Estado: ESPECIFICACIÓN FIJADA ANTES DE IMPLEMENTAR. Lo no cubierto aquí se declara como límite.

## 1. Objetivo
Describir la vida de un trade (no solo su resultado) con descriptores separados y un compuesto aprendible, para (a) medir qué aspectos de la vida del trade son predecibles y (b) entrenar el Ridge 2 con un target que conserva pendiente y no se anula con un factor en cero.

## 2. Descriptores (por trade, calculables en vivo desde las fotos de la trayectoria)
Notación por foto `k` de un trade: `v` = velas abiertas, `p` = profit_apertura (neto de spread), `MFE`/`MAE` corrientes (ya incluyen `p + spread`, como en la trayectoria de Fase 4), `c` = spread, `h` = mediana de |Close(t) − Close(t−60)| en pips sobre el IS (Close ≈ Open).

| # | Nombre | Fórmula bruta `x` | Notas |
|---|---|---|---|
| 1 | Captura (EFR) | `clip((1 + p / (MFE + \|MAE\| + c + 1e-12)) / 2, 0, 1)` | Dónde cerró dentro del recorrido que tuvo |
| 2 | Hundimiento (D_h) | `1 / (1 + \|MAE\| / h)` | En unidades de una hora típica del par |
| 3 | Tiempo a favor (FET_v3) | `0.5` si `v <= 2`; si no, fracción de fotos con `p > 0` entre las fotos de `v = 2` hasta `v` | Sin castigo de la vela de entrada |
| 4 | Recuperación (REC) | `(p − p_fondo) / (max(v − v_fondo, 1) · h/60 + 1e-12)`, con `p_fondo` = mínimo corriente de `p` y `v_fondo` su vela | Solo si el fondo es relevante: `−p_fondo > c`. Si no, el descriptor es *no aplicable* y su valor normalizado es 0.5 |
| 5 | Ritmo (RIT) | `p / (v · h/60 + 1e-12)` | Ganancia por vela; penaliza la duración sin premiar la salida temprana por sí sola |

## 3. Normalización y compuesto
- `s_j = (tanh((x_j − med_j) / escala_j) + 1) / 2`. `med_j` y `escala_j` salen **solo del IS** (un valor terminal por trade del IS; descriptor 4 solo con los trades donde aplica). `escala_j = MAD` si `MAD > 1e-6`; si no, el desvío estándar si `> 1e-6`; si no, 1.0.
- `V3 = Σ w_j · s_j` con `w_j = 0.2` (pesos iguales de partida, `[DEFAULT / CRO-OVERRIDE]`). Media aritmética: ningún factor anula a los demás.
- La versión viva de un trade en la foto `k` usa los valores corrientes con las mismas constantes. En la última foto es igual a la terminal.
- Target del Ridge 2 (modo `NEXUS_LAB_CIERRE=V3`): `V3` terminal del trade, repetido en todas sus fotos (igual que `T_terminal`). La grilla de K es la de percentiles 0..50 de la predicción IS (como `dT_cont` y `G_pips`).

## 4. Qué NO cambia (límites declarados)
- La Cabeza B de Ridge 1 sigue con `T_terminal` (`T(t)`): su `T_hat0` se mide en esa escala y alimenta `ΔT` en el escalón E3; cambiar su target sin cambiar `ΔT` mezclaría escalas. Queda como paso siguiente (H-V7-08).
- Las variables de entrada de Ridge 2 (incluida `ΔT`) siguen usando `T(t)` vivo. El EA no cambia: solo compara `T_pred < K_abortar` (`[INFERENCIA LÓGICA]`).
- Score de la búsqueda: `Score_v7` (no usa `T`). `Score_final` solo en el modo clásico.
- Pesos iguales y media aritmética son valores de partida, no derivaciones.

## 5. Pruebas fijadas antes de correr (sintéticas en el repo; reales en la VM)
1. **No mecánica:** con trayectorias de deriva positiva, cortar cada trade en un punto al azar no sube la mediana de `V3`; con deriva cero la diferencia es pequeña (|Δ| ≤ 0.05).
2. **Contra sustitutos:** entradas informativas (deriva positiva posterior) puntúan por encima de entradas al azar.
3. **Aprendibilidad:** R² fuera de pliegue (GroupKFold por trade) por descriptor y para `V3`; una relación lineal conocida da R² alto y un target permutado da R² ≈ 0.
4. **Comparabilidad:** `h` por par; medianas de `V3` por símbolo (se miden en la VM; no se pueden probar con datos sintéticos).
5. **Causalidad:** el valor vivo en la última foto es igual al terminal; invariancia de prefijo (los primeros `m` valores vivos no cambian al truncar el trade en `m`).
6. **Correlaciones:** matriz de correlación entre los cinco descriptores en el reporte (se descarta el redundante en una versión siguiente).
