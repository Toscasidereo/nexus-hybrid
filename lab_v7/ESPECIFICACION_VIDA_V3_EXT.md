# Especificación — Vida v3 extendida (lab-v8) — fijada antes de implementar (2026-11-07)
Orden del CRO: extender Vida v3 a la Cabeza B y al ΔT vivo, adaptar la línea de laboratorio y el EA gemelo, verificar que no se rompa el flujo ni las operaciones ML. Rama nueva: `lab-v8` (sale de `lab-v7`).

## 1. Lectura de intención
Que V3 sea LA medida de calidad de vida del trade en todo el sistema de supervivencia, y no solo el objetivo del Ridge 2: (a) la Cabeza B predice V3 terminal al entrar; (b) el ΔT vivo es `V3_vivo(t) − T_hat0`, con T_hat0 en la escala de V3; (c) el EA calcula V3 en vivo igual que el laboratorio. Se descarta T_v2 (superado por V3). No se toca `main` ni el EA de producción.

## 2. Interruptores (tablero_lab.env). El defecto del CÓDIGO de cada interruptor reproduce lab-v7; el tablero del CRO fija T=V3 y VIDA=3.1
| Interruptor | Valores | Defecto del código | Efecto |
|---|---|---|---|
| NEXUS_LAB_T | `T` / `V3` | `T` | `V3`: Cabeza B aprende V3 terminal; ΔT = clip(V3_vivo − T_hat0, −1, 1) en extractor, simuladores, 4.5 y EA |
| NEXUS_LAB_VIDA | `3.0` / `3.1` | `3.0` | fórmulas de Vida (ver §3). `3.0` reproduce lab-v7 |
| NEXUS_LAB_CIERRE | `T_terminal` / `dT_cont` / `G_pips` / `V3` / `dV3` | `T_terminal` | objetivo del Ridge 2. `dV3` = V3_terminal − V3_vivo(t) (H-V3-01) |

## 3. Fórmulas (Bloque D)
Por foto: `p` = profit neto de spread; `v` = velas abiertas; `mfe`,`mae` = corrientes con cierre (`max(MFE,p+c)`, `min(MAE,p+c)`); `c` = spread; `h` = movimiento típico de una hora del par (solo IS).
- EFR = clip((1 + p/(mfe+|mae|+c+1e-12))/2, 0, 1) · D_h = 1/(1+|mae|/h) · FET_v3 = 0.5 si v ≤ 2, si no cg/cn (cn = fotos desde la vela 2; cg = las de p > 0).
- REC = (p − p_fondo)/(max(v − v_fondo, 1)·h/60 + 1e-12) si −p_fondo > c; si no, REC no aplica.
- RIT = p/(max(v, rit_vmin)·h/60 + 1e-12).
- Normalización de cada descriptor x: s = (tanh((x − med)/escala) + 1)/2; REC no aplicable: s = rec_na.
- V3 = ((((w0 s0 + w1 s1) + w2 s2) + w3 s3) + w4 s4), w_j = 0.2.
- **VER 3.0** (lab-v7): rit_vmin = 1, rec_na = 0.5. **VER 3.1** (parches H-V3-02 y H-V3-03, `[DEFAULT / CRO-OVERRIDE]`): rit_vmin = mediana de duración IS (≥ 1), rec_na = 1.0.
- Constantes `med`, `escala`, `rit_vmin` y `h` solo del IS. Con `NEXUS_LAB_T=V3` salen de la población del extractor de entrada (operaciones IS sin compuerta ML), porque deben existir antes de extraer trayectorias; sin V3 en Cabeza B/ΔT salen de los terminales de las trayectorias (como lab-v7).

## 4. Dónde actúa (Bloque P resumido)
1. Extractor de entrada: con T=V3 agrega 3 columnas por operación (FET_v3, p_fondo, v_fondo) → constantes v3p y objetivo V3 de la Cabeza B (`T_min` = cuantil Q=0.70 OOF de esa predicción).
2. Extractor de trayectorias y simuladores (4 + 4.5 A/B): estado vivo (cg, cn, p_fondo, v_fondo) en cada vela; con v3p ≠ None, ΔT usa V3 vivo.
3. Export: el bloque del cerebro agrega `vida_*` (h, rit_vmin, rec_na, med[5], escala[5], pesos[5]).
4. EA gemelo: calcula V3 vivo con el mismo orden de operaciones; estado por ticket en variables globales; reconstrucción desde el histórico al reiniciar.

## 5. Criterios de prueba fijados antes (cada uno booleano)
- N1 No regresión: con T=T, VIDA=3.0 y CIERRE=T_terminal, todas las salidas de los núcleos son idénticas bit a bit a las de lab-v7 (y las de modo `final` a main), y L1–L16 pasan.
- N2 Con T=T y CIERRE=V3, VIDA=3.0: objetivo V3 igual a lab-v7 dentro de 1e-6.
- N3 V3 vivo del núcleo = V3 vivo de Python (`vida_v31`) en todas las fotos, bit a bit.
- N4 Causalidad: V3 vivo en la foto k no cambia si se recortan las fotos posteriores.
- N5 Constantes de población: dependen solo de datos IS; la población coincide con las operaciones del extractor.
- N6 Export: el bloque compila contra los structs del EA; 4.5 lee de vuelta las constantes exactas.
- N7 EA compilado con g++ == núcleo Python (V3 vivo y T_pred), bit a bit o, si no, diferencia declarada.
- N8 Humo punta a punta con los tres interruptores activos, sin excepciones.
- N9 El diff contra `lab-v7` no toca `main` ni archivos ajenos al laboratorio.
Fracaso: cualquier N1–N7 en falso deja el hallazgo abierto y la reforma sin declarar lista.

## 6. Hipótesis (no hechos)
Alinear Cabeza B y ΔT con la medida que aprende el Ridge 2 reduce la incoherencia de escalas y mejora el aborto. No está probado; se decide con corridas pareadas en la VM (lab-v7 vs lab-v8, cada una con su nulo).
