# ==============================================================================
# 🧠 LABORATORIO ML V12.0 (PRODUCCIÓN / LAB) — RIDGE DUAL (V + T) + RIDGE 2 CON ΔT
# ⚡ HPC THREAD-POOL CON AUTOCALIBRACIÓN DE RAM (cgroup-aware) | SPREADS DINÁMICOS
# 🎯 INTEGRACIÓN TOTAL TABLERO ÚNICO + PARIDAD ACTIVA EA DUAL V12.01+
# ==============================================================================
# 📋 BITÁCORA LAB-V8 V0.3 (2026-11-10) — INFORMES DE FASE 4 (rama lab-v8; `main` y lab-v7 intactos). Orden del CRO: "LUZ VERDE: INFORMES FASE 4 (censo, resumen, manifiesto)"
#      más un archivo acotado para lectura directa. Requisito del CRO: informes auditables, trazables y utilizables por dos lectores (el CRO y el sistema).
#      • Interruptor nuevo NEXUS_LAB_CENSO = 0 | 1 (defecto del código 0 = comportamiento anterior, sin archivos nuevos; el tablero lo pone en 1) y NEXUS_LAB_VISTA_TOP (defecto 50).
#      • Con CENSO=1 se escriben, además de lo de siempre: Censo_Fase4_{tag}_{SIMBOLO}.csv (una fila por configuración LEÍDA, pase o no, con la etapa donde cayó y todo lo
#        calculado hasta ahí: Ridge 1, base IS, Ridge 2, OOS con y sin Ridge 2), Vista_Fase4_{tag}_{SIMBOLO}.csv (primeras N por dirección y fold), Resumen_Fase4_{tag}.md y
#        Manifiesto_Fase4_{tag}.json. La lógica de escritura vive en lab_informes.py; aquí solo se anotan valores que ya se calculaban (`cz`).
#      • El censo se escribe aunque el símbolo quede 'sin_campeones' (es cuando más se necesita). No cambia entrenamiento, selección, compuerta, cerebro ni Reporte_OOS:
#        la identidad byte a byte de esos dos archivos (código anterior vs CENSO=0 vs CENSO=1) se comprobó con una cadena sintética fuera del repo (ver LEEME_VM §6);
#        L20 de lab_pruebas.py cubre el módulo lab_informes. `lab_eval_v7` agrega claves al diccionario `ex` solo con CENSO=1.
#      • Blindaje: las funciones de lab_informes llamadas dentro del torneo no lanzan (devuelven vacío y cuentan el error en `errores_informes` del manifiesto);
#        la escritura de censo, resumen y manifiesto va en try/except: un fallo de informes nunca descarta un candidato ni corta la corrida.
#      • Datos por configuración: identidad y métricas de Fase 3 (f3_*), población de Ridge 1 (ml_*), R² OOF y T_min de la Cabeza B, constantes de Ridge 1, fotos y trades
#        de Ridge 2, diagnóstico R2V_*, K, base IS, IS con Ridge 2, OOS sin y con Ridge 2 (13 métricas + Score_final, Score_v7, C1..C4, alfa, pips totales), retención,
#        score de flujo, clave de selección, veredicto de Ridge 2 (APORTA = mejoran PF y mediana de pips en OOS), rango final, si entró al cerebro y segundos de cómputo.
#      • Límite declarado: las configuraciones que caen antes del OOS no tienen números de OOS. No se agregó ninguna simulación. No hay comparación con/sin compuerta de Ridge 1.
# ------------------------------------------------------------------------------
# 📋 BITÁCORA LAB-V8 V0.2 (2026-11-09) — PARCHES H-AUD8-01 Y H-AUD8-02 (rama lab-v8; `main` y lab-v7 intactos). Orden del CRO: "Debemos corregir ambos hallazgos luz verde" + elección "Excluir ese trade".
#      • H-AUD8-01 (`lab_escala_v`): con NEXUS_LAB_TAMANO = A | B, una decisión IS sin dato de actividad (NaN en las primeras 59 velas del archivo; solo posible en el fold 1)
#        descartaba al candidato entero con `Lab_actividad_invalida`. Ahora esas decisiones se excluyen del ajuste (mediana `a_is_med` y Ridge de tamaño). La simulación no cambia:
#        el kernel ya trataba el NaN como actividad relativa = `a_is_med`. Sin NaN en las decisiones, el resultado es idéntico bit a bit (prueba L19). Sigue inválido: todas NaN, o algún infinito.
#      • H-AUD8-02 (`_bloque_mql5`): el bloque RANK #1 termina en salto de línea. Antes, con exactamente un campeón LONG, su última línea quedaba pegada a la cabecera del SHORT y
#        Fase 4.5 A descartaba el motor LONG (`variable_ausente`). DESVIACIÓN respecto de main/lab-v7: el texto del cerebro gana un salto de línea por bloque RANK #1 (ningún valor cambia;
#        para el compilador MQL5 es espacio en blanco). `Fase_4_V12_0.py` (main) conserva el defecto: requiere su propia luz verde. Prueba L18.
# 📋 BITÁCORA LAB-V8 V0.1 (2026-11-07; cabecera añadida 2026-11-08, H-V8-01) — VIDA v3 EXTENDIDA A CABEZA B, ΔT VIVO Y KERNELS (rama lab-v8, sobre lab-v7 ff7ae24; `main` y lab-v7 intactos):
#      Orden del CRO: "extender v3 ... luz verde". Las marcas `[LAB-V8]` del código (desde la importación de vida_v3) señalan cada cambio.
#      • Interruptores nuevos: NEXUS_LAB_T = T (defecto, = lab-v7) | V3 (la Cabeza B aprende V3 terminal y ΔT = clip(V3_vivo − T_hat0)); NEXUS_LAB_VIDA = 3.0 (defecto) | 3.1;
#        NEXUS_LAB_CIERRE acepta además dV3 (target V3_terminal − V3_vivo). Con los defectos, las salidas y el comportamiento son los de lab-v7.
#      • Kernels de simulación: argumentos finales opcionales (`v3p=None`, `v3_cols=None`) con ramas `if v3p is not None`; sin ellos, bit a bit igual a main (prueba L1).
#      • Constantes de Vida (v3p, 18 valores, redondeadas a 8 decimales) desde las operaciones IS del extractor de Ridge 1; las filas del extractor ganan 3 columnas (FET_v3, P_fondo, V_fondo).
#      • El bloque exportado agrega los campos `vida_*` solo con V3 activo; las etiquetas de salida llevan `_TV3` / `_VID31`. `T_hat0` sigue siendo clip(T_raw, 0, 1), ahora en escala V3 si T=V3.
#      • Estado: [HECHO EJECUTADO] lab_pruebas L1–L17, v8_pruebas y lab_compat_ea pasan con datos sintéticos (commits 90c80a1, c7b6bf2).
#        [NO CORRIDO] exportación de punta a punta con datos reales. Que V3 supere a T(t) es hipótesis, a decidir con corridas pareadas.
# 📋 BITÁCORA LAB-V7 V0.5 (2026-11-06) — VIDA v3 COMO TARGET DE RIDGE 2 (orden del CRO: aprobó el diseño de la métrica de la vida del trade y pidió implementarlo):
#      • NEXUS_LAB_CIERRE = V3: el Ridge 2 aprende `V3` terminal (compuesto de 5 descriptores: captura, hundimiento, tiempo a favor, recuperación,
#        ritmo; ver vida_v3.py y ESPECIFICACION_VIDA_V3.md). Constantes de normalización (med, escala) y `h` solo del IS de cada candidato.
#        Grilla de K = percentiles 0..50 de la predicción IS (como dT_cont y G_pips). El EA no cambia (solo compara T_pred < K_abortar).
#      • Con V3 el reporte agrega R2V_EFR, R2V_D_h, R2V_FET_v3, R2V_REC, R2V_RIT, R2V_V3 (R² fuera de pliegue, GroupKFold por trade, sobre las
#        fotos del IS usadas para entrenar) y Corr_max_desc (máx. |correlación| entre los 5 descriptores terminales). Es la prueba de aprendibilidad.
#      • NO cambia: la Cabeza B de Ridge 1 (sigue con T_terminal; ver ESPECIFICACION §4, H-V7-08) ni las variables de entrada de Ridge 2 (ΔT con T(t)).
#      • Defecto (cierre = T_terminal) = main; no se importa nada nuevo en la ruta por defecto salvo el módulo vida_v3.
# 📋 BITÁCORA LAB-V7 V0.4 (2026-11-04) — MÉTRICA DE SELECCIÓN (orden del CRO: mejorar las métricas con las que Fase 4 selecciona, para comparar con las anteriores):
#      • NEXUS_LAB_METRICA = final | v7. `final` (defecto) = Score_final, idéntico a main. `v7` reemplaza r[0] (el puntaje) por Score_v7
#        en: gate de la base IS, escaneo de K (elige el K de mayor Score_v7 IS), puntaje OOS, ClaveRank/Score_flujo. Resto de r[...] intacto.
#      • Kernels `simular_motor_{long,short}_superv_T_ix`: copia exacta de los originales + 2 salidas (vela de entrada y de salida por trade);
#        las 4 primeras salidas son idénticas a las originales. El modo `final` no los usa.
#      • DSR del escaneo de K: nt = cantidad de K de la grilla; sigma_sr = desvío del Sharpe de alfa entre esos K (pasada previa). Para base
#        y OOS: nt = 1. NO deflaciona por la búsqueda de Fase 3 (Optuna): su N_t no llega a Fase 4. [PENDIENTE: N_t real, protocolo punto 3]
#      • N mínimo de señales = el min_trades que ya usa cada evaluación (IS 20, OOS 30, base OOS 3), no N_MIN = 100 de la propuesta.
#      • Close no está en el parquet: la escala h de Score_v7 se calcula con Open (declarado). Sin máscara de velas fantasma.
#      • El reporte agrega las columnas Metrica, SF_IS, V7_IS, SF_OOS, V7_OOS (ambos puntajes sobre los MISMOS trades elegidos), para la
#        comparación pareada. En `final` los V7_* quedan en NaN.
#      • Ridge de entrada/Cabeza B y Ridge 2 siguen entrenando con T(t) / T_terminal. T_v2 como objetivo: NO implementado (H-V7-06).
#      • Fase 3 (Optuna) sigue usando Score_final: los candidatos llegan filtrados por esa métrica.
#
# 📋 BITÁCORA LAB-V7 V0.3 (2026-11-04) — ALINEACIÓN DE LA CADENA (orden del CRO: "Alinea todas las fases de python, para que funcione el lab 7"):
#      • Los kernels de la escala viven ahora en `lab_v7/lab_escala.py` (compartidos con `Fase_4_5_lab_A.py`); sin cambio de aritmética.
#      • Los features sin(atan2(v, z)) de X10 se calculan con `lab_fase_nb` (misma tipificación float32 que el kernel de simulación y
#        que el Z de Ridge 1) en vez de numpy.
#      • Fase 4.5 A/B del lab: `lab_v7/Fase_4_5_lab_A.py` y `Fase_4_5_lab_B.py` (copias; leen el mismo tag por las mismas variables NEXUS_LAB_*).
#
# 📋 BITÁCORA LAB-V7 V0.2 (2026-11-04) — EA GEMELO DEL LAB (orden del CRO: "terminar de alinear el EA para que sea gemelo digital de Lab 7"):
#    El export del Ridge de tamaño pasa a ser ejecutable por el EA gemelo `lab_v7/EA_V12.01_LAB.txt`. Esta entrada reemplaza en
#    la práctica el aviso ⚠️ de V0.1 (que se conserva abajo como historia) para los modos de TAMAÑO con el EA gemelo.
#      • Parámetros del Ridge de tamaño redondeados a DEC_W ANTES de calcular la escala (misma regla que W_R): la escala que simula
#        Python es la que reconstruye el EA desde el texto exportado.
#      • Escala calculada con kernels @njit secuenciales (`_lab_esc_A_nb`, `_lab_esc_B_nb`), mismo orden de operaciones que el EA.
#      • `ACT_ARR` pasa de pandas.rolling a suma directa secuencial (`lab_actividad_nb`): mismo orden que el EA (ascendente en la
#        vela; en el EA, desplazamiento 59 → 0).
#      • `lab_grid_k` redondea la grilla de K a 5 decimales (el export escribe `k_abortar` con %.5f; con percentiles había desfase).
#      • `lab_escala_v(..., params_out=None)`: devuelve por diccionario los parámetros exportables; `lab_bloque_tam` los emite como
#        asignaciones C++ (`tam_modo`, `tam_act_med`, `tam_a_is_med`, `tam_esc_min/max`, y en modo A `tam_intercept`, `tam_med_pred`,
#        `tam_w[0..10]`, `tam_mu[0..10]`, `tam_sd[0..10]`). Con LAB_TAMANO = off no se emite nada: el texto es idéntico al de main.
#      • Los modos de CIERRE no necesitan campos nuevos (mismos pesos y `k_abortar`).
#      • Pendiente: compilar el EA gemelo en MetaEditor; Fase 4.5 (tag por entorno y lectura de `tam_*`); repetir M7 (ver README).
#
# 📋 BITÁCORA LAB-V7 V0.1 (2026-11-01) — COPIA DE LABORATORIO PARALELA (rama lab-v7; `main` intacto):
#    Orden del CRO (2026-11-01): "Refactoriza pero deja el main intacto". Esta copia de Fase_4_V12_0.py agrega tres
#    interruptores por variable de entorno. Con todos apagados (valores por defecto) el comportamiento es el de main.
#      • NEXUS_LAB_TAMANO = off | A | B   Ridge de TAMAÑO. A: Ridge (ALPHAS_RIDGE) entrenado en el IS con target MFE_Pips y
#        features COLS_X_ENTRADA + act_rel. B: act_rel puro. Escala por vela `escala_v` (clip 0.25-4, normalizada por la
#        mediana IS) que multiplica `v_req` en la entrada (kernels long/short de simulación y de trayectoria).
#        act = Σ|ΔOpen| de las 60 velas M1 hasta la vela de decisión, en pips (el parquet no trae Close: aproximación
#        causal declarada; la exploración usó Close).
#      • NEXUS_LAB_CIERRE = T_terminal | dT_cont | G_pips   Ridge de CIERRE (Ridge 2). T_terminal = main. dT_cont = T_terminal
#        − T_obs(t). G_pips = pips finales − profit_apertura(t). Con target distinto de T_terminal la grilla de K pasa a ser
#        los percentiles 0..50 (paso 5) de la predicción IS (la grilla absoluta 0.10-0.50 no aplica a otra escala).
#      • NEXUS_LAB_NULO = 0 | 1   Gemelo nulo: la escala se desplaza en círculo dentro de cada ventana (desfase al azar 10-90 %)
#        y el target de Ridge 2 se permuta entre fotos del IS. Semilla por (símbolo, dirección, candidato).
#    Cambios de código respecto de main (todo lo demás idéntico): parámetro `escala_v` al final de 4 kernels; columna 15
#    `Idx_Decision` en extractor_ml_*; bloque LAB en procesar_candidato; archivos con sufijo `_LAB_...` en TAG_ARCHIVOS.
#    ⚠️ Los modos LAB no son exportables al EA (el EA no implementa `escala_v`): no hay paridad M7 hasta decisión del CRO.
#    Controles: lab_v7/lab_pruebas.py (paridad bit a bit con main con escala_v = 1).
#
# 📋 BITÁCORA V12.0 (promoción mayor — paridad activa con silicio EA V12.01+):
#    - [H-M7-01 / H-M0-01 CERRADO EN SILICIO] El generador `_bloque_mql5` deja de emitir
#      la Cabeza B y Ridge 2 extendido como comentarios de "contrato pendiente". Ahora
#      emite asignaciones C++ ejecutables directas compatibles con `EA_Dual_V12_01.mq5`:
#        • Cabeza B: `g_pares[idx].{ml}.cabeza_t_activa = true/false;`, `bias_T`,
#          `t_min_admision`, y vector completo `w_T[0..9]`.
#        • Ridge 2: `inmunidad_velas = INMUNIDAD_VELAS_EFECTIVA;`, `n_features = N_FEAT_SUPERV;`,
#          y el vector `w_superv` exportando exactamente N_FEAT_SUPERV pesos (8 o 10).
#    - [H-M2-02 CERRADO] Precalentamiento JIT de `eval_robustez_numba_v6` incorporado formalmente
#      en `_warmup_jit()`. Erradica la contención de lock en Numba durante el primer candidato.
#    - [TAG ARCHIVOS] Promovido a `PROD_V12_{ESCALON}`. Sincronizado con la arquitectura
#      de Tablero Único (`nexus_tablero.py`).
# ==============================================================================
# 📋 BITÁCORA rev.c (TABLERO ÚNICO — edición programática, ver parche_fase4_tablero.py y Fase_4_V11_0.tablero.diff):
#    - N_FOLDS, RATIO_TRAIN_TEST y MEMORIA_FIFO ya NO se definen acá: se importan de nexus_tablero.py (Axioma 3; cierra H-12).
#    - Geometría de folds desde TAB.geometria(N_total): idéntica a la de Fase 3 y Fase 4.5 (una sola fórmula).
#    - RESERVA CIEGA: TAB.recortar() descarta el tramo final reservado ANTES de construir los arrays. Con RESERVA_FINAL=0 (default)
#      el comportamiento es idéntico al de rev.b.
#    - Se VERIFICA el sello del CSV de Fase 3 (mismo tablero, mismo parquet, reserva aplicada). Si no coincide, el símbolo se salta
#      con causa explícita 'Sello_Fase3_invalido' (nunca se calcula con una geometría distinta en silencio).
#    - Se ESTAMPA el sello propio en el CSV (columnas Tab_*) y en la cabecera del .txt (línea '// TABLERO ...').
#    - Sin ningún otro cambio de lógica (kernels, Ridge 1/2, compuertas, export: intactos).
# ==============================================================================
# 📋 BITÁCORA V11.0 (reescritura programática desde V10.0 — Python únicamente; EA APLAZADO):
#    ⚠️ CAMBIO DE SEMÁNTICA (Regla 7): con ESCALON != 'E0' los pesos/umbrales NO son comparables con V10.0
#       y el contrato del EA cambia (ver ESCALON). NO DESPLEGAR escalones != E0 sin el EA correspondiente.
#    - [REV3.1] Ridge 1 gana una CABEZA T (target = T_terminal del Core, mismas 10 features). La cabeza V
#      (velocidad -> v_req -> Brazo 1) queda INTACTA. Admisión: Z>=0 Y T_hat >= T_min, con
#      T_min = Percentil_{Q_ADMISION_T}(T_hat OOF sin recortar). Validez: R² OOF > 0 o se descarta.
#    - [REV3.1] Ridge 2: +2 features ΔT=clip(T_obs-T_hat0,-1,1) y ΔT·Θ (solo ESCALON E3). T_obs = Tscore_snap.
#    - [REV3.1] Inmunidad: aborto por K bloqueado en velas_abiertas<=2 (E1+); Ridge 2 se entrena solo con
#      snapshots velas>2 (dominio de entrenamiento = dominio de uso).
#    - [HV-18] extractor_ml_* recibe phantom_arr y cuenta t_gain/t_loss (misma regla que la trayectoria);
#      el dataset pasa de 14 a 15 columnas (col 14 = T_Terminal, calculada con calcular_t_score_trade_numba).
#    - E0 usa parámetros neutros (W_T=0, B_T=0, T_min=-1, inmunidad=0, 8 features): reproduce V10.0 sin ramas distintas.
#    - [rev.b] Pisos de trades IS parametrizados: E2/E3 usan 20 (MIN_OPS_IS_LAB / MIN_TRADES_SUPERV_IS) en base IS, escaneo de K y Ridge 2;
#      E0/E1 conservan 50. Telemetría: Trades_IS_Base / Trades_IS_Superv_Sim / Trades_IS_Superv_Train. Descarte OOS desdoblado
#      (trades_insuficientes vs score_no_positivo). MIN_OPS_OOS_EXPORT=30 NO se toca (decisión CRO) pero puede volverse el límite activo.
#    - Salidas con tag LAB_V11_<ESCALON>: aisladas de producción (Fase 4.5 busca el tag V9.2).
#    - SIN CAMBIOS: Brazo 1, cierres por tiempo/saturador, sample_weight=None, geometría WFO, Juez, core.
#    🔓 ABIERTO: EA (E1: velas>2; E2: T_hat al entrar; E3: T_obs vivo => t_gain/t_loss + phantom); pendientes H-02, H-16, Q-01..Q-05.
# ==============================================================================
# 📚 HISTORIAL V10.0 (conservado íntegro — Regla 7)
# ==============================================================================
# ==============================================================================
# 🧠 LABORATORIO ML V10.0 — MOTOR DE SUPERVIVENCIA KINEMÁTICA CONTINUA
# ⚡ HPC THREAD-POOL CON AUTOCALIBRACIÓN DE RAM (cgroup-aware) | SPREADS DINÁMICOS
# 🎯 RIDGE ENTRADA CAUSAL + RIDGE SUPERVIVENCIA T(t) CONTINUA [0,1]
# ==============================================================================
# 📋 BITÁCORA V10.0 (reescritura completa — Auditoría NEXUS Fase_4 + core v1.1.0):
#
#    ⚠️ CAMBIO DE SEMÁNTICA (Regla 7 — invalida comparabilidad retroactiva):
#    - [H-07 CERRADO] La "Fidelidad" (Fid) del snapshot comparaba una velocidad
#      de otra escala que la usada para entrenar el Ridge de entrada (z de
#      V_cruda = (MFE-|MAE|)/(vida*(1+|MAE|/10)) vs. z de profit/v_ef). La
#      auditoría midió sesgo ≈ -1 MAD (corr 0.77, datos sintéticos). Ahora
#      UNA sola función (`_velocidad_snapshot`) define la velocidad del
#      snapshot con la MISMA fórmula que el extractor ML. Para velas>=3
#      (únicas donde Fid se usa) la paridad es exacta (v_ef == vida).
#      Flag `FID_VELOCIDAD_UNIFICADA` (True por defecto) permite reproducir
#      V9.x. Con True: pesos W_S/B_S/K de V9.x NO son comparables, y el EA
#      debe replicar la fórmula unificada (ver cabecera del .txt exportado).
#    - [H-10 MITIGADO] El OOS actúa como compuerta de exportación. Las
#      métricas OOS exportadas están, por construcción, condicionadas a haber
#      pasado ese filtro. Se exportan por (Fold, Dir): N_Cand_OOS_Evaluados,
#      N_Cand_Compuerta_OK y Mediana_ScoreOOS_Todos (sobre TODOS los evaluados,
#      incluidos los rechazados) para dimensionar el sesgo de selección.
#    - [H-11 / H-14 CERRADO] Workers = min(vCPU por afinidad, RAM efectiva /
#      huella por candidato). RAM efectiva = min(psutil/proc del core, límite
#      cgroup v2/v1). Se cargan del parquet SÓLO las columnas requeridas por
#      el Top-N de candidatos; los arrays float32 se crean una vez y se
#      comparten de solo-lectura (antes: ~9 copias por candidato). El
#      pre-cómputo de ciclos/saturadores se acota a [0:end_test]: equivalente
#      por prefijo-invarianza (verificada en auditoría S3: causal).
#    - [H-02 CERRADO] Formato de BASE/ACUM validado en procesar_candidato
#      (descarte forense "Formato_MQL5_invalido") — antes un IndexError podía
#      matar la corrida durante el export.
#    - [H-04 CERRADO] Rama redundante `tipo_cierre==2` eliminada del extractor
#      de trayectoria (matemáticamente idéntica: profit>=spread+1 => el min()
#      devuelve mae_previo).
#    - [H-05 CERRADO] Constante mágica 50.0 -> LIM_T_FALLBACK_VELAS (nombrada).
#    - [H-01 / H-16 CERRADO] Versión única FASE4_VERSION; sin literales "V9.x"
#      en banners/exports; ejecución dentro de main() con guard __main__.
#
#    🔓 RESERVAS ABIERTAS (requieren decisión CRO / cambio en el core):
#    - [H-17] `n_factor` de eval_robustez_numba_v6 es ≡ 1.0 (código muerto):
#      no hay penalización por muestra pequeña. NO se toca aquí (core).
#    - [H-18] score_final no es intensivo mientras RF<4: la media armónica
#      IS/OOS favorece al tramo IS (≈2x velas). NO se corrige aquí (core).
#    - [H-12] Geometría WFO (TEST=N/(RATIO+N_FOLDS)) duplicada vs Fase 3;
#      verificar manualmente contra Fase_3.py.
#    - [EA] N4-A1 / N4-A2 siguen abiertos del lado del EA: NO desplegar.
#    - F4-05 (kernels de ciclo duplicados Fase3<->Fase4), F4-09 (linaje
#      CSV<->parquet): diferidos, sin cambio.
# ==============================================================
# 📚 HISTORIAL FORENSE V9.0–V9.5 (conservado íntegro — Regla 7)
# ==============================================================
# ==============================================================================
# 🧠 LABORATORIO ML V9.4 — MOTOR DE SUPERVIVENCIA KINEMÁTICA CONTINUA
# ⚡ ENTORNO HPC THREAD-POOL PROTECTED (SSOT RAM ALLOCATION): SPREADS DINÁMICOS
# 🎯 MATRIZ: RIDGE ENTRADA CAUSAL + RIDGE SUPERVIVENCIA T(t) CONTINUA [0,1]
# ==============================================================================
# 📋 BITÁCORA V9.0-V9.3: ver historial previo. V9.3 resolvió (verificado en
#    auditoría cruzada): paridad FET LONG/SHORT, guard de trade fantasma EOF
#    simétrico, firma correcta de warm-up JIT, MAE EOF simétrico, y sustituyó
#    el atajo O(N) de escaneo de K por re-simulación real por candidato
#    (más costosa, más correcta — resuelve la limitación metodológica que
#    yo mismo había dejado abierta en V9.0/V9.1).
# ==============================================================================
# 📋 BITÁCORA V9.4 (Auditoría cruzada de dos informes + directiva CRO):
#    - [F4-13 CERRADO — CAUSA RAÍZ] `deducir_features()` retornaba SIEMPRE
#      las columnas V/A crudas (`{familia}_V_{tf}_{res}`), sin importar si
#      Optuna seleccionó un acumulador Z-scoreado para ese motor. El EA
#      (`ActualizarCinematicaCerebro`, `tension > 8`) Z-scorea base+V+A
#      TODOS JUNTOS cuando el acumulador configurado es una variante Z.
#      Python entrenaba el Ridge de entrada sobre V/A crudos para
#      candidatos que el EA evaluará en escala Z — corrompiendo Z_pred,
#      umbral de entrada y v_req para todo candidato Z-scoreado. CORREGIDO:
#      `deducir_features(base_col, acum_col)` ahora aplica el mismo regex
#      de detección Z que ya usan `obtener_z_base` y `obtener_contexto_macro`
#      (reutiliza el patrón ya validado en el archivo, no uno nuevo).
#    - [F4-01 CERRADO] `Fold` se exporta explícitamente en el CSV. AMBOS
#      folds siguen entrenándose y exportándose sin cambio de alcance
#      (directiva explícita del CRO) — el fix es de trazabilidad
#      (desambigua `Rank_Opt_Orig`, que colisiona entre folds en Fase 3),
#      no de selección de datos.
#    - [F4-02 CERRADO] Eliminada la normalización `score/(LEN/10000)`.
#      `score_final` de `eval_robustez_numba_v6` ya es una magnitud
#      intensiva (acotada [0,100], `n_factor` satura) — la división por
#      longitud sesgaba la media armónica IS/OOS a favor de OOS por la
#      sola razón de que `TRAIN_LEN ≈ 2×TEST_LEN` (RATIO_TRAIN_TEST=2.0),
#      sin relación con el mérito real del candidato.
#    - [F4-03 CERRADO] Métricas OOS-baseline con `score==0` (rechazo de
#      `eval_robustez_numba_v6`) se exportan como `"RECHAZADO"`, no como
#      `0.0` literal — restaura el estándar ya usado en `Fase_3.py`.
#    - [F4-08 MITIGADO] Contadores globales de símbolos procesados/saltados
#      con log explícito por causa (sin CSV, sin parquet, sin candidatos).
#      Si CERO símbolos se procesan en toda la corrida, se levanta
#      `RuntimeError` — cubre el escenario de peligro real (28/28 saltados
#      en silencio, el script imprime "COMPLETADO") sin convertir ausencias
#      parciales legítimas en fallos duros.
#    - [Higiene, sin impacto de diseño] Rango de `alphas` de `RidgeCV`
#      ampliado para el Ridge de Supervivencia (`ALPHAS_RIDGE_SUPERV`,
#      hasta 10000) — con decenas de miles de snapshots el rango original
#      (hasta 100) puede no contener el óptimo real de regularización.
#      El Ridge de entrada (muchos menos trades) conserva su rango
#      original sin cambios.
#    - [NO RESUELTO — REQUIERE RATIFICACIÓN DEL CRO, NO DECIDIDO AQUÍ]
#      La ponderación `sample_weight = 1/n_snapshots` (peso por trade, no
#      por snapshot) presente en `entrenar_modelo_supervivencia_ridge`
#      CONTRADICE la ratificación explícita previa del CRO ("no
#      aplicaremos pesos 1/velas... sesgo de diseño intencionado a favor
#      de la protección de la cuenta"). Se mantiene tal cual estaba en
#      V9.3 — NO es una decisión que corresponda a "a mi criterio", es la
#      reversión de una orden de negocio ya dada. Sigue pendiente.
#    - [DIFERIDO — fuera de alcance de este turno, documentado, no tocado]
#      F4-05 (kernels de ciclo/saturador duplicados Fase3↔Fase4, violación
#      Axioma 3), F4-06 (sin autocalibración de RAM en ThreadPoolExecutor),
#      F4-09 (sin linaje CSV↔parquet), F4-04 (sombreo semántico "Base"
#      entre Fase 3 y Fase 4, preexistente desde V8.1).
# ==============================================================================
# 📋 BITÁCORA V9.5 (decisiones CRO + parches Clase A de BITACORA_NEXUS_AUDITORIA):
#    - [N1-A4 CERRADO — decisión CRO] Ridge de Supervivencia SIN ponderación:
#      `sample_weight=None`. Cada snapshot es un dato unitario; el error se
#      penaliza proporcionalmente al total de snapshots en vida real (los
#      trades largos pesan más, sesgo intencionado pro-protección de cuenta).
#      Invalida comparabilidad retroactiva de pesos W_S/B_S de V9.4 (Regla 7).
#    - [N1-A1 CERRADO] "RECHAZADO" del baseline OOS se decide por score==0
#      (`Base_Rechazado`), no por Ops>0 (n real se devuelve aun si rechaza).
#      Columnas *_Ridge ahora redondeadas como las *_Superv (N1-B5).
#    - [N3-A1 CERRADO] PATRON_CSV_FASE3 -> V5.8 (typo heredado).
#    - [N1-M6 CERRADO] Comentario F4-07 corregido (no hay commit previo de .tmp).
#    - [N4-B2 CERRADO] Mensajes "EA sin superv" eliminados (el EA ya lo implementa).
#      Sigue vigente: no desplegar hasta cerrar N4-A1/N4-A2 (lado EA).
#    - [N1-B4] Símbolo sin 'Phantom' ahora entra en contadores de cobertura.
#    - [N5-M3] Validación de columnas del CSV de Fase 3 tras read_csv.
#    - [N5-M2] Fallbacks Ridge(alpha=1.0) contados y reportados al final.
#    - [N1-B1] MAX_VCPUS por sched_getaffinity (respeta cgroups/afinidad).
#    - DESCARTADO por CRO: N5-A1 (caché numba). ACLARADO: Retención = métrica
#      comparativa de comportamiento (liberar vs recortar operaciones).
# ==============================================================================

import os
import gc
import math
import re
import threading
import warnings
import concurrent.futures
import zlib
import numpy as np
import pandas as pd
from numba import njit, set_num_threads
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.model_selection import GroupKFold, KFold

try:
    from threadpoolctl import threadpool_limits
    _TPL_OK = True
except ImportError:
    _TPL_OK = False

# 🛡️ IMPORTACIÓN S.S.O.T (REGLA 3)
from nexus_formulas_core import (
    eval_robustez_numba_v6, MATRIZ_SPREADS, SPREAD_FALLBACK,
    FORMULAS_CORE_VERSION, calcular_t_score_trade_numba, memoria_disponible_bytes
)

import nexus_tablero as TAB   # [TABLERO] fuente única de folds / IS-OOS / reserva ciega / MEMORIA_FIFO
import v7_metricas as V7   # [LAB-V7 V0.4] Score_v7 / T_v2
import vida_v3 as VV
from vida_v3 import v3_vivo_nb   # [LAB-V8] núcleo de Vida v3 compartido con los simuladores       # [LAB-V7 V0.5] Vida v3
from lab_escala import lab_actividad_nb, lab_fase_nb, _lab_esc_A_nb, _lab_esc_B_nb   # [LAB-V7 V0.3] kernels compartidos con Fase_4_5_lab_A

warnings.simplefilter('ignore')

try: MAX_VCPUS = len(os.sched_getaffinity(0))
except AttributeError: MAX_VCPUS = os.cpu_count() or 1

# ==========================================================
# 🎚️ TABLERO DE CONTROL MAESTRO Y ORÁCULO
# ==========================================================
LISTA_SIMBOLOS = ['EURUSDm', 'EURJPYm', 'EURCADm', 'EURAUDm', 'EURGBPm', 'EURCHFm', 'EURNZDm',
                  'GBPUSDm', 'GBPAUDm', 'GBPNZDm', 'GBPCHFm', 'GBPCADm', 'GBPJPYm',
                  'AUDJPYm', 'AUDUSDm', 'AUDNZDm', 'AUDCADm', 'AUDCHFm',
                  'NZDJPYm', 'NZDUSDm', 'NZDCHFm', 'NZDCADm',
                  'USDCADm', 'USDJPYm', 'USDCHFm',
                  'CADCHFm', 'CADJPYm', 'CHFJPYm']

# LAB-V7 (2026-11-06): lista de símbolos desde el tablero (NEXUS_LAB_SIMBOLOS="EURUSDm,GBPUSDm"); vacío = lista completa de arriba.
if os.environ.get('NEXUS_LAB_SIMBOLOS', '').strip():
    _lab_sel = [s.strip() for s in os.environ['NEXUS_LAB_SIMBOLOS'].split(',') if s.strip()]
    _lab_mal = [s for s in _lab_sel if s not in LISTA_SIMBOLOS]
    if _lab_mal: raise SystemExit(f"NEXUS_LAB_SIMBOLOS: símbolos desconocidos {_lab_mal}")
    LISTA_SIMBOLOS = _lab_sel

TOP_CANDIDATOS = 1000
IMPRIMIR_CONSOLA_TOP = 3
EXPORTAR_MQL5_TOP = 10

Z_SCORE_MINIMO_LONG = 0.0
Z_SCORE_MINIMO_SHORT = 0.0

RATIO_CAPTURA_VELOCIDAD = 0.60
TOLERANCIA_VIDA_MEDIA = 1.5
LIM_T_FALLBACK_VELAS = 50.0     # [H-05] límite de vida (velas) usado en Theta/v_ef_norm cuando atrac_t<=0
FID_VELOCIDAD_UNIFICADA = True  # [H-07] False => reproduce la Fid de V9.x (NO comparable con V10.0)
MEMORIA_FIFO = TAB.MEMORIA_FIFO   # [TABLERO] no editar acá: nexus_tablero.py
N_FOLDS = TAB.N_FOLDS   # [TABLERO] no editar acá: nexus_tablero.py
RATIO_TRAIN_TEST = TAB.RATIO_TRAIN_TEST   # [TABLERO] no editar acá: nexus_tablero.py

MIN_OPS_IS_REPORTE = 50
MIN_OPS_OOS_EXPORT = 30

CANDIDATOS_K_ABORTAR = np.array([0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50], dtype=np.float64)

PATRON_CSV_FASE3 = "Reporte_Fase3_WFO_V5.8_{simbolo}" + ("_MV7" if os.environ.get("NEXUS_LAB_F3", "main") == "v7" else "") + ".csv"   # LAB-V7 V0.5: NEXUS_LAB_F3=v7 lee la salida de Fase_3_lab.py

RANKEAR_SOLO_IS = True
PERMITIR_PHANTOM_AUSENTE = False
ALPHAS_RIDGE = [0.1, 1.0, 10.0, 100.0]
ALPHAS_RIDGE_SUPERV = [0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0]
K_FOLDS_CV_SUPERV = 5
DEC_W = 8
DEC_PCT = 4
DEC_SPREAD = 4
DEC_T = 6

FASE4_VERSION = "V12.0"    # ÚNICA fuente de versión (banners, headers, CSV)

# 🧪 [V12.0 / ESCALERA DE ABLACIÓN]
#   E0 = V10.0 (referencia, parámetros neutros)      E1 = E0 + inmunidad de arranque (aborto K bloqueado en velas<=2)
#   E2 = E1 + Cabeza T de Ridge 1 como compuerta     E3 = E2 + features ΔT y ΔT·Θ en Ridge 2 (8 -> 10)
ESCALON = 'E3'
assert ESCALON in ('E0', 'E1', 'E2', 'E3')
INMUNIDAD_VELAS_EFECTIVA = 0 if ESCALON == 'E0' else 2       # el aborto por K exige velas_abiertas > este valor
_GATE_T_ACTIVO = ESCALON in ('E2', 'E3')
N_FEAT_SUPERV = 10 if ESCALON == 'E3' else 8                 # columnas de X_traj usadas para entrenar Ridge 2
Q_ADMISION_T = 0.70      # percentil de T_hat OOF que fija T_min (declarado; variante 0.50 en la escalera)
N_FOLDS_OOF_T = 5        # KFold sin mezclar (bloques contiguos: los trades están ordenados en el tiempo)

MIN_OPS_IS_LAB = 20 if _GATE_T_ACTIVO else MIN_OPS_IS_REPORTE        
MIN_TRADES_SUPERV_IS = 20 if _GATE_T_ACTIVO else MIN_OPS_IS_REPORTE  
# [LAB-V7] interruptores del laboratorio (por defecto todo apagado = comportamiento de main)
LAB_TAMANO = os.environ.get('NEXUS_LAB_TAMANO', 'off')           # 'off' | 'A' | 'B'
LAB_CIERRE = os.environ.get('NEXUS_LAB_CIERRE', 'T_terminal')    # 'T_terminal' | 'dT_cont' | 'G_pips' | 'V3'
LAB_NULO = os.environ.get('NEXUS_LAB_NULO', '0') == '1'
# [LAB-V8] Vida v3 extendida: NEXUS_LAB_T = T (defecto, como lab-v7) | V3 (Cabeza B y ΔT con V3); NEXUS_LAB_VIDA = 3.0 (defecto) | 3.1 (parches H-V3-02/03)
LAB_T = os.environ.get('NEXUS_LAB_T', 'T')
LAB_VIDA = os.environ.get('NEXUS_LAB_VIDA', '3.0')
LAB_CENSO = os.environ.get('NEXUS_LAB_CENSO', '0') == '1'            # [LAB-V8 informes] 1 = escribe censo, vista, resumen y manifiesto (0 = nada nuevo)
LAB_VISTA_TOP = int(os.environ.get('NEXUS_LAB_VISTA_TOP', '') or 50)  # [LAB-V8 informes] filas por (dirección, fold) en la vista acotada
if LAB_CENSO: import lab_informes as INF
LAB_METRICA = os.environ.get('NEXUS_LAB_METRICA', 'final')       # 'final' = Score_final (main) | 'v7' = Score_v7 en la selección
LAB_F3 = os.environ.get('NEXUS_LAB_F3', 'main')   # CSV de Fase 3 que se lee: 'main' (el de siempre) | 'v7' (el de Fase_3_lab.py con NEXUS_LAB_METRICA=v7, sufijo _MV7)
assert LAB_F3 in ('main', 'v7'), f"NEXUS_LAB_F3 invalido: {LAB_F3}"
assert LAB_TAMANO in ('off', 'A', 'B'), f"NEXUS_LAB_TAMANO invalido: {LAB_TAMANO}"
assert LAB_CIERRE in ('T_terminal', 'dT_cont', 'G_pips', 'V3', 'dV3'), f"NEXUS_LAB_CIERRE invalido: {LAB_CIERRE}"
assert LAB_T in ('T', 'V3'), f"NEXUS_LAB_T invalido: {LAB_T}"
assert LAB_VIDA in ('3.0', '3.1'), f"NEXUS_LAB_VIDA invalido: {LAB_VIDA}"
LAB_USA_VIDA = (LAB_T == 'V3') or (LAB_CIERRE in ('V3', 'dV3'))   # [LAB-V8] ¿se calcula Vida v3 en esta corrida?
assert LAB_METRICA in ('final', 'v7'), f"NEXUS_LAB_METRICA invalido: {LAB_METRICA}"
LAB_ACTIVO = (LAB_TAMANO != 'off') or (LAB_CIERRE != 'T_terminal') or LAB_NULO or (LAB_METRICA != 'final') or (LAB_F3 != 'main') or (LAB_T != 'T') or (LAB_VIDA != '3.0')
LAB_V7_OPCION = 'A'      # alfa neutral a la deriva local (opción A de la propuesta)   [DEFAULT / CRO-OVERRIDE]
LAB_V7_R = 20            # réplicas del gemelo de captura (C3)                          [DEFAULT / CRO-OVERRIDE]
ACT_VENTANA = 60
ESCALA_MIN, ESCALA_MAX = 0.25, 4.0
PERCENTILES_K_LAB = np.arange(0, 55, 5)
TAG_ARCHIVOS = f"PROD_V12_{ESCALON}" + (f"_LAB_{LAB_TAMANO}_{LAB_CIERRE}" + ("_MV7" if LAB_METRICA == "v7" else "") + ("_F3V7" if LAB_F3 == "v7" else "") + ("_TV3" if LAB_T == "V3" else "") + ("_VID31" if (LAB_VIDA == "3.1" and LAB_USA_VIDA) else "") + ("_NULO" if LAB_NULO else "") if LAB_ACTIVO else "")   
COLS_REQ_FASE3 = ['Dir', 'Fold', 'Rank', '⚖️ BASE IN', '📊 ACUM IN', '⚙️ Arm_IN', '⚡ Chq_IN', '⚖️ BASE OUT', '📊 ACUM OUT', '⚙️ Arm_OUT', '⚡ Chq_OUT']
MARCOS_VALIDOS = ('Fast', 'Mid', 'Slow')

COLS_X_ENTRADA = ['X1_ZBase_In', 'X2_V_In', 'X3_A_In', 'X4_Fase_In', 'X5_ZBase_Out',
                  'X6_V_Out', 'X7_A_Out', 'X8_Fase_Out', 'X9_Macro_1', 'X10_Macro_2']

BYTES_POR_VELA_CANDIDATO = 192
FACTOR_SEGURIDAD_RAM = 0.60

# ==========================================================
# 🔬 FORENSE DE DESCARTES (clave compuesta símbolo|dirección|causa — Ley 7)
# ==========================================================
_descartes = {}
_lock_descartes = threading.Lock()

def _registrar_descarte(simbolo, direccion, causa):
    clave = f"{simbolo}|{direccion}|{causa}"
    with _lock_descartes:
        _descartes[clave] = _descartes.get(clave, 0) + 1

_manif_simbolos = {}   # [LAB-V8 informes]
_T_INICIO = __import__('datetime').datetime.now()
_cobertura = {'ok': 0, 'sin_csv': [], 'sin_parquet': [], 'sin_campeones': [], 'sin_phantom': [], 'csv_invalido': []}
_fallbacks_ridge = {'entrada': 0, 'superv': 0, 'T': 0}
_lock_fallbacks = threading.Lock()

def _registrar_fallback_ridge(tipo):
    with _lock_fallbacks:
        _fallbacks_ridge[tipo] += 1

# ==========================================================
# 🎛️ RAM EFECTIVA Y WORKERS [H-11 / H-14]
# ==========================================================
def _limite_cgroup_disponible():
    try:
        with open('/sys/fs/cgroup/memory.max') as f: lim = f.read().strip()
        if lim != 'max':
            with open('/sys/fs/cgroup/memory.current') as f: uso = int(f.read().strip())
            return max(int(lim) - uso, 0)
        return None
    except Exception:
        pass
    try:
        with open('/sys/fs/cgroup/memory/memory.limit_in_bytes') as f: lim = int(f.read().strip())
        with open('/sys/fs/cgroup/memory/memory.usage_in_bytes') as f: uso = int(f.read().strip())
        if lim < (1 << 60): return max(lim - uso, 0)
    except Exception:
        pass
    return None

def _ram_efectiva_bytes():
    ram = memoria_disponible_bytes()          # SSOT del core (host)
    cg = _limite_cgroup_disponible()          # límite real del contenedor
    return min(ram, cg) if cg is not None else ram

def _calibrar_workers(n_velas, bytes_cache):
    ram = _ram_efectiva_bytes()
    huella = BYTES_POR_VELA_CANDIDATO * n_velas
    util = ram * FACTOR_SEGURIDAD_RAM - bytes_cache
    n_ram = 1 if util <= huella else int(util // huella)
    return max(1, min(MAX_VCPUS, n_ram)), ram, huella

# ==========================================================
# 🧠 UTILERÍAS MQL Y MÉTODOS DE REDUCCIÓN, KERNELS NUMBA, EXTRACTORES, SIMULADORES Y RIDGE
# ==========================================================
def parse_pct(x):
    return round(float(str(x).replace('%', '')) / 100.0, DEC_PCT)

def parse_mql5_gatillo(base_str, acum_str, armado_str, chasquido_str):
    partes = str(base_str).split('_')
    if len(partes) < 3 or partes[-2].upper() not in ('FAST', 'MID', 'SLOW') or not partes[-1]:
        raise ValueError(f"Formato BASE inválido: {base_str!r}")
    res = partes[-1]; marco = partes[-2]
    base_name = "_".join(partes[:-2]).upper()

    if base_name == "FPP": base_enum = "BASE_FPP_CRUDO"
    else: base_enum = f"BASE_{base_name}"

    marco_enum = f"MARCO_{marco.upper()}"; res_enum = f"RES_{res}"
    sufijo = f"_{marco}_{res}"; core = str(acum_str).replace(sufijo, "")
    pz = 0
    if core.startswith('Z'):
        match = re.match(r'Z(\d+)(_.*)', core)
        if match:
            pz = int(match.group(1))
            core_rest = match.group(2).upper().lstrip('_')
            if core_rest == "FPP": acum_enum = "ACUM_Z_FPP_CRUDO"
            else: acum_enum = f"ACUM_Z_{core_rest}"
        else: acum_enum = f"ACUM_{core.upper()}"
    else:
        if core.upper() == "FPP": acum_enum = "ACUM_FPP_CRUDO"
        else: acum_enum = f"ACUM_{core.upper()}"

    return marco_enum, res_enum, pz, base_enum, acum_enum, parse_pct(armado_str), parse_pct(chasquido_str)

def deducir_features(base_col, acum_col):
    partes = str(base_col).split('_')
    res = partes[-1]; tf = partes[-2]
    familia = "_".join(partes[:-2])

    if familia == "Int_Area": v_familia, a_familia = "Int_V", "Int_A"
    elif familia == "Int_V": v_familia, a_familia = "Int_V", "Int_A"
    elif familia == "Int2_Area": v_familia, a_familia = "Int2_V", "Int2_A"
    elif familia == "Int2_V": v_familia, a_familia = "Int2_V", "Int2_A"
    elif familia == "FPP": v_familia, a_familia = "FPP_V", "FPP_A"
    else:
        return None, None

    match = re.match(r'Z(\d+)_', str(acum_col))
    if match:
        pz = match.group(1)
        return f"Z{pz}_{v_familia}_{tf}_{res}", f"Z{pz}_{a_familia}_{tf}_{res}"
    return f"{v_familia}_{tf}_{res}", f"{a_familia}_{tf}_{res}"

def obtener_z_base(base_col, acum_col):
    match = re.match(r'Z(\d+)_', str(acum_col))
    if match: return f"Z{match.group(1)}_{base_col}"
    return base_col

def obtener_contexto_macro(base_col, acum_col):
    partes = str(base_col).split('_'); res = partes[-1]; marco_actual = partes[-2]
    base_name = "_".join(partes[:-2]); todos_los_marcos = ['Fast', 'Mid', 'Slow']
    otros_marcos = [m for m in todos_los_marcos if m != marco_actual]
    if len(otros_marcos) < 2: otros_marcos = ['Mid', 'Slow']
    m1, m2 = otros_marcos[0], otros_marcos[1]
    match = re.match(r'Z(\d+)_', str(acum_col))
    if match:
        pz = match.group(1); return f"Z{pz}_{base_name}_{m1}_{res}", f"Z{pz}_{base_name}_{m2}_{res}"
    return f"{base_name}_{m1}_{res}", f"{base_name}_{m2}_{res}"

# ==========================================================
# 🚀 MATEMÁTICA NUMBA JIT KERNELS (fastmath=False — paridad C/Py)
# ==========================================================
@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def _velocidad_snapshot(mfe_actual, mae_previo, profit_apertura, v_ef, spread_pips):
    if FID_VELOCIDAD_UNIFICADA:
        bruto = profit_apertura + spread_pips
        m_mfe = max(mfe_actual, bruto)
        m_mae = min(mae_previo, bruto)
        return (m_mfe - abs(m_mae)) / (v_ef * (1.0 + (abs(m_mae) / 10.0)))
    return profit_apertura / v_ef

@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def _pred10(W, B, a0, a1, a2, a3, a4, a5, a6, a7, a8, a9):
    return (W[0]*a0 + W[1]*a1 + W[2]*a2 + W[3]*a3 + W[4]*a4 + W[5]*a5 + W[6]*a6 + W[7]*a7 + W[8]*a8 + W[9]*a9) + B

@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def calcular_extremos_numba(signos_arr, acum_arr, cambios):
    n_velas = len(signos_arr); extremo_arr = np.zeros(n_velas, dtype=np.float32); running_val = 0.0
    for i in range(n_velas):
        if cambios[i] == 1: running_val = acum_arr[i]
        else:
            if signos_arr[i] > 0:
                if acum_arr[i] > running_val: running_val = acum_arr[i]
            else:
                if acum_arr[i] < running_val: running_val = acum_arr[i]
        extremo_arr[i] = running_val
    return extremo_arr

@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def calcular_acum_ciclo_numba(metrica_arr, cambios):
    N = len(metrica_arr); out = np.empty(N, dtype=np.float32); running_sum = 0.0
    for i in range(N):
        if cambios[i] == 1: running_sum = metrica_arr[i]
        else: running_sum += metrica_arr[i]
        out[i] = running_sum
    return out

@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def obtener_extremos_ciclo_numba(ciclos_id, acum_arr, signos_arr, max_ciclo):
    max_arr = np.full(max_ciclo + 1, np.nan, dtype=np.float32)
    min_arr = np.full(max_ciclo + 1, np.nan, dtype=np.float32)
    temp_max = np.full(max_ciclo + 1, -1e9, dtype=np.float32)
    temp_min = np.full(max_ciclo + 1, 1e9, dtype=np.float32)
    cycle_sign = np.zeros(max_ciclo + 1, dtype=np.int32)
    for i in range(len(ciclos_id)):
        c = ciclos_id[i]; val = acum_arr[i]
        if val > temp_max[c]: temp_max[c] = val
        if val < temp_min[c]: temp_min[c] = val
        cycle_sign[c] = 1 if signos_arr[i] > 0 else -1
    for c in range(max_ciclo + 1):
        if cycle_sign[c] == 1: max_arr[c] = temp_max[c]
        elif cycle_sign[c] == -1: min_arr[c] = temp_min[c]
    return max_arr, min_arr

@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def rolling_median_causal_numba(extremos_ciclo, direction=1, memoria_fifo=100, min_periods=5):
    n = len(extremos_ciclo); result = np.full(n, np.nan, dtype=np.float32); window = np.empty(memoria_fifo, dtype=np.float32)
    count = 0; idx = 0
    for i in range(n):
        val = extremos_ciclo[i]
        if not np.isnan(val):
            if (direction == 1 and val >= 0.0) or (direction == -1 and val <= 0.0):
                window[idx] = val; idx = (idx + 1) % memoria_fifo; count = min(count + 1, memoria_fifo)
        if count >= min_periods:
            temp = window[:count].copy(); temp.sort()
            if count % 2 == 1: result[i] = temp[count // 2]
            else: result[i] = (temp[(count // 2) - 1] + temp[count // 2]) / 2.0
    shifted = np.full(n, np.nan, dtype=np.float32)
    if n > 0: shifted[1:] = result[:-1]
    last = np.nan
    for i in range(n):
        if not np.isnan(shifted[i]): last = shifted[i]
        if not np.isnan(last): result[i] = last
        else: result[i] = 10.0 if direction == 1 else -10.0
    return result

# ==========================================================
# 🚀 1. EXTRACTOR ML CAUSAL PRIMARIO (RIDGE DE ENTRADA)
# ==========================================================
@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def extractor_ml_long(
    signos_in, extremo_in, sat_inf_in, acum_in, signos_out, extremo_out, sat_sup_out, acum_out,
    z_base_in, in_v, in_a, z_base_out, out_v, out_a, z_macro_1, z_macro_2,
    opens_arr, highs_arr, lows_arr, phantom_arr, pips_mult, n_velas, armado_in, chasquido_in, armado_out, chasquido_out, spread_pips, v3_cols=None):
    pos = 0; p_in = 0.0; max_v = 0.0; min_v = 0.0; idx_in = 0; tuvo_iter = False; t_gain = 0.0; t_loss = 0.0
    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0   # [LAB-V8] estado vivo de Vida v3
    max_trades = (n_velas // 2) + 5
    dataset = np.empty((max_trades, (16 if v3_cols is None else 19)), dtype=np.float32); cnt = 0; foto_X = np.zeros(10, dtype=np.float32)

    for i in range(1, n_velas - 1):
        if pos == 1:
            tuvo_iter = True
            if phantom_arr[i] == 0.0:
                prof_vela = ((opens_arr[i] - p_in) * pips_mult) - spread_pips
                if prof_vela > 0.0: t_gain += 1.0
                else: t_loss += 1.0
            if highs_arr[i] > max_v: max_v = highs_arr[i]
            if lows_arr[i] < min_v: min_v = lows_arr[i]
            if v3_cols is not None:   # [LAB-V8] estado vivo de Vida v3
                v_v3 = max(float(i - idx_in + 1), 1.0); p_v3 = ((opens_arr[i+1] - p_in) * pips_mult) - spread_pips
                if v_v3 >= 2.0:
                    cn_v += 1.0
                    if p_v3 > 0.0: cg_v += 1.0
                if p_v3 < minp_v: minp_v = p_v3; vfondo_v = v_v3
            if signos_out[i] > 0 and extremo_out[i] >= (sat_sup_out[i] * armado_out) and acum_out[i] <= (extremo_out[i] * (1.0 - chasquido_out)):
                p_out = opens_arr[i+1]; prof_bruto = (p_out - p_in) * pips_mult
                if cnt < max_trades:
                    dataset[cnt, 0:10] = foto_X; dataset[cnt, 15] = float(idx_in - 1); dataset[cnt, 10] = prof_bruto - spread_pips
                    dataset[cnt, 11] = min((min_v - p_in)*pips_mult, prof_bruto); dataset[cnt, 12] = max((max_v - p_in)*pips_mult, prof_bruto); dataset[cnt, 13] = float(max((i + 1) - idx_in, 1))
                    dataset[cnt, 14] = calcular_t_score_trade_numba(dataset[cnt, 12], dataset[cnt, 11], dataset[cnt, 10], t_gain, t_loss, spread_pips)
                    if v3_cols is not None:
                        dataset[cnt, 16] = 0.5 if dataset[cnt, 13] <= 2.0 else cg_v / cn_v; dataset[cnt, 17] = minp_v; dataset[cnt, 18] = vfondo_v
                    cnt += 1
                pos = 0

        elif pos == 0:
            if signos_in[i] < 0 and extremo_in[i] <= (sat_inf_in[i] * armado_in) and acum_in[i] >= (extremo_in[i] * (1.0 - chasquido_in)):
                pos = 1; p_in = opens_arr[i+1]; max_v = p_in; min_v = p_in; idx_in = i + 1; tuvo_iter = False; t_gain = 0.0; t_loss = 0.0
                cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0
                foto_X[0] = z_base_in[i]; foto_X[1] = in_v[i]; foto_X[2] = in_a[i]; foto_X[3] = math.sin(math.atan2(in_v[i], z_base_in[i]))
                foto_X[4] = z_base_out[i]; foto_X[5] = out_v[i]; foto_X[6] = out_a[i]; foto_X[7] = math.sin(math.atan2(out_v[i], z_base_out[i]))
                foto_X[8] = z_macro_1[i]; foto_X[9] = z_macro_2[i]

    if pos == 1 and tuvo_iter and cnt < max_trades:
        p_out = opens_arr[n_velas - 1]; prof_bruto = (p_out - p_in) * pips_mult
        dataset[cnt, 0:10] = foto_X; dataset[cnt, 15] = float(idx_in - 1); dataset[cnt, 10] = prof_bruto - spread_pips
        dataset[cnt, 11] = min((min_v - p_in)*pips_mult, prof_bruto); dataset[cnt, 12] = max((max_v - p_in)*pips_mult, prof_bruto); dataset[cnt, 13] = float(max((n_velas - 1) - idx_in, 1))
        dataset[cnt, 14] = calcular_t_score_trade_numba(dataset[cnt, 12], dataset[cnt, 11], dataset[cnt, 10], t_gain, t_loss, spread_pips)
        if v3_cols is not None:
            dataset[cnt, 16] = 0.5 if dataset[cnt, 13] <= 2.0 else cg_v / cn_v; dataset[cnt, 17] = minp_v; dataset[cnt, 18] = vfondo_v
        cnt += 1
    return dataset[:cnt]

@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def extractor_ml_short(
    signos_in, extremo_in, sat_sup_in, acum_in, signos_out, extremo_out, sat_inf_out, acum_out,
    z_base_in, in_v, in_a, z_base_out, out_v, out_a, z_macro_1, z_macro_2,
    opens_arr, highs_arr, lows_arr, phantom_arr, pips_mult, n_velas, armado_in, chasquido_in, armado_out, chasquido_out, spread_pips, v3_cols=None):
    pos = 0; p_in = 0.0; max_v = 0.0; min_v = 0.0; idx_in = 0; tuvo_iter = False; t_gain = 0.0; t_loss = 0.0
    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0   # [LAB-V8] estado vivo de Vida v3
    max_trades = (n_velas // 2) + 5
    dataset = np.empty((max_trades, (16 if v3_cols is None else 19)), dtype=np.float32); cnt = 0; foto_X = np.zeros(10, dtype=np.float32)

    for i in range(1, n_velas - 1):
        if pos == -1:
            tuvo_iter = True
            if phantom_arr[i] == 0.0:
                prof_vela = ((p_in - opens_arr[i]) * pips_mult) - spread_pips
                if prof_vela > 0.0: t_gain += 1.0
                else: t_loss += 1.0
            if highs_arr[i] > max_v: max_v = highs_arr[i]
            if lows_arr[i] < min_v: min_v = lows_arr[i]
            if v3_cols is not None:   # [LAB-V8] estado vivo de Vida v3
                v_v3 = max(float(i - idx_in + 1), 1.0); p_v3 = ((p_in - opens_arr[i+1]) * pips_mult) - spread_pips
                if v_v3 >= 2.0:
                    cn_v += 1.0
                    if p_v3 > 0.0: cg_v += 1.0
                if p_v3 < minp_v: minp_v = p_v3; vfondo_v = v_v3
            if signos_out[i] < 0 and extremo_out[i] <= (sat_inf_out[i] * armado_out) and acum_out[i] >= (extremo_out[i] * (1.0 - chasquido_out)):
                p_out = opens_arr[i+1]; prof_bruto = (p_in - p_out) * pips_mult
                if cnt < max_trades:
                    dataset[cnt, 0:10] = foto_X; dataset[cnt, 15] = float(idx_in - 1); dataset[cnt, 10] = prof_bruto - spread_pips
                    dataset[cnt, 11] = min((p_in - max_v)*pips_mult, prof_bruto); dataset[cnt, 12] = max((p_in - min_v)*pips_mult, prof_bruto); dataset[cnt, 13] = float(max((i + 1) - idx_in, 1))
                    dataset[cnt, 14] = calcular_t_score_trade_numba(dataset[cnt, 12], dataset[cnt, 11], dataset[cnt, 10], t_gain, t_loss, spread_pips)
                    if v3_cols is not None:
                        dataset[cnt, 16] = 0.5 if dataset[cnt, 13] <= 2.0 else cg_v / cn_v; dataset[cnt, 17] = minp_v; dataset[cnt, 18] = vfondo_v
                    cnt += 1
                pos = 0

        elif pos == 0:
            if signos_in[i] > 0 and extremo_in[i] >= (sat_sup_in[i] * armado_in) and acum_in[i] <= (extremo_in[i] * (1.0 - chasquido_in)):
                pos = -1; p_in = opens_arr[i+1]; max_v = p_in; min_v = p_in; idx_in = i + 1; tuvo_iter = False; t_gain = 0.0; t_loss = 0.0
                cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0
                foto_X[0] = z_base_in[i]; foto_X[1] = in_v[i]; foto_X[2] = in_a[i]; foto_X[3] = math.sin(math.atan2(in_v[i], z_base_in[i]))
                foto_X[4] = z_base_out[i]; foto_X[5] = out_v[i]; foto_X[6] = out_a[i]; foto_X[7] = math.sin(math.atan2(out_v[i], z_base_out[i]))
                foto_X[8] = z_macro_1[i]; foto_X[9] = z_macro_2[i]

    if pos == -1 and tuvo_iter and cnt < max_trades:
        p_out = opens_arr[n_velas - 1]; prof_bruto = (p_in - p_out) * pips_mult
        dataset[cnt, 0:10] = foto_X; dataset[cnt, 15] = float(idx_in - 1); dataset[cnt, 10] = prof_bruto - spread_pips
        dataset[cnt, 11] = min((p_in - max_v)*pips_mult, prof_bruto); dataset[cnt, 12] = max((p_in - min_v)*pips_mult, prof_bruto); dataset[cnt, 13] = float(max((n_velas - 1) - idx_in, 1))
        dataset[cnt, 14] = calcular_t_score_trade_numba(dataset[cnt, 12], dataset[cnt, 11], dataset[cnt, 10], t_gain, t_loss, spread_pips)
        if v3_cols is not None:
            dataset[cnt, 16] = 0.5 if dataset[cnt, 13] <= 2.0 else cg_v / cn_v; dataset[cnt, 17] = minp_v; dataset[cnt, 18] = vfondo_v
        cnt += 1
    return dataset[:cnt]

# ==========================================================
# 🚀 2. EXTRACTORES DE TRAYECTORIA CONTINUA
# ==========================================================
@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def extractor_trayectoria_long_v2(
    signos_in, extremo_in, sat_inf_in, acum_in, signos_out, extremo_out, sat_sup_out, acum_out,
    z_base_in, in_v, in_a, z_base_out, out_v, out_a, z_macro_1, z_macro_2,
    opens_arr, highs_arr, lows_arr, phantom_arr, pips_mult, n_velas,
    armado_in, chasquido_in, armado_out, chasquido_out, spread_pips,
    W_R, B_R, med_v, mad_v, atrac_t, umbral_z_ia, W_T, B_T, T_min, escala_v, v3p=None):

    max_snaps = n_velas + 5
    X_traj = np.empty((max_snaps, 10), dtype=np.float32)
    Profit_snap = np.empty(max_snaps, dtype=np.float32)
    MAE_snap = np.empty(max_snaps, dtype=np.float32)
    MFE_snap = np.empty(max_snaps, dtype=np.float32)
    Tscore_snap = np.empty(max_snaps, dtype=np.float32)
    Y_target = np.zeros(max_snaps, dtype=np.float32)
    TradeId_snap = np.full(max_snaps, -1, dtype=np.int32)
    Vela_snap = np.zeros(max_snaps, dtype=np.int32)

    cnt_snaps = 0; pos = 0; p_in = 0.0; min_v = 0.0; max_v = 0.0; idx_in = 0; v_req = 0.0; Z_pred = 0.0
    t_gain = 0.0; t_loss = 0.0; trade_id = -1; trade_start_snap = 0; T_hat0 = 0.0
    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0   # [LAB-V8] estado vivo de Vida v3
    lim_T_seguro = (atrac_t * TOLERANCIA_VIDA_MEDIA) + 1e-9 if atrac_t > 0 else LIM_T_FALLBACK_VELAS

    for i in range(1, n_velas - 1):
        if pos == 1:
            if highs_arr[i] > max_v: max_v = highs_arr[i]
            if lows_arr[i] < min_v: min_v = lows_arr[i]

            if phantom_arr[i] == 0.0:
                prof_vela = ((opens_arr[i] - p_in) * pips_mult) - spread_pips
                if prof_vela > 0.0: t_gain += 1.0
                else: t_loss += 1.0

            velas_abiertas = max(float(i - idx_in + 1), 1.0)
            mae_previo = (min_v - p_in) * pips_mult; mfe_actual = (max_v - p_in) * pips_mult
            profit_apertura = ((opens_arr[i+1] - p_in) * pips_mult) - spread_pips
            if v3p is not None:   # [LAB-V8] estado vivo de Vida v3
                if velas_abiertas >= 2.0:
                    cn_v += 1.0
                    if profit_apertura > 0.0: cg_v += 1.0
                if profit_apertura < minp_v: minp_v = profit_apertura; vfondo_v = velas_abiertas
            closed = False

            if atrac_t > 0 and velas_abiertas > lim_T_seguro:
                closed = True
            else:
                target_req = max((v_req * velas_abiertas * (1.0 + (abs(mae_previo) / 10.0))) + (abs(mae_previo) * 0.5), spread_pips + 1.0)
                if profit_apertura >= target_req:
                    closed = True

            if not closed:
                if signos_out[i] > 0 and extremo_out[i] >= (sat_sup_out[i] * armado_out) and acum_out[i] <= (extremo_out[i] * (1.0 - chasquido_out)):
                    closed = True

            v_ef = max(velas_abiertas, 3.0)
            V_z = (_velocidad_snapshot(mfe_actual, mae_previo, profit_apertura, v_ef, spread_pips) - med_v) / (mad_v + 1e-9)
            if velas_abiertas <= 2.0: Fid = 0.5
            else: Fid = (math.tanh(V_z - Z_pred) + 1.0) / 2.0

            D_ = 1.0 / (1.0 + (abs(mae_previo) / (mad_v * v_ef + 1e-9)))
            Theta = 1.0 - min(velas_abiertas / lim_T_seguro, 1.0)
            C_ = (math.tanh(mfe_actual / (mad_v * v_ef + 1e-9)) + 1.0) / 2.0

            Z_pred_norm = math.tanh(Z_pred)
            v_ef_norm = math.tanh(v_ef / lim_T_seguro)

            if cnt_snaps < max_snaps:
                X_traj[cnt_snaps, 0] = Fid; X_traj[cnt_snaps, 1] = D_; X_traj[cnt_snaps, 2] = Theta; X_traj[cnt_snaps, 3] = C_
                X_traj[cnt_snaps, 4] = Z_pred_norm; X_traj[cnt_snaps, 5] = v_ef_norm
                X_traj[cnt_snaps, 6] = Theta * D_; X_traj[cnt_snaps, 7] = Fid * D_

                m_mfe_snap = max(mfe_actual, profit_apertura + spread_pips)
                m_mae_snap = min(mae_previo, profit_apertura + spread_pips)
                t_obs_snap = calcular_t_score_trade_numba(m_mfe_snap, m_mae_snap, profit_apertura, t_gain, t_loss, spread_pips)
                dT = min(max(t_obs_snap - T_hat0, -1.0), 1.0)
                if v3p is not None:   # [LAB-V8] ΔT con Vida v3 vivo (T_hat0 en escala V3 cuando NEXUS_LAB_T=V3)
                    dT = min(max(v3_vivo_nb(profit_apertura, m_mfe_snap, m_mae_snap, velas_abiertas, cg_v, cn_v, minp_v, vfondo_v, spread_pips, v3p) - T_hat0, -1.0), 1.0)
                X_traj[cnt_snaps, 8] = dT; X_traj[cnt_snaps, 9] = dT * Theta
                Vela_snap[cnt_snaps] = int(velas_abiertas)

                Profit_snap[cnt_snaps] = profit_apertura
                MFE_snap[cnt_snaps] = m_mfe_snap
                MAE_snap[cnt_snaps] = m_mae_snap
                Tscore_snap[cnt_snaps] = t_obs_snap
                TradeId_snap[cnt_snaps] = trade_id
                cnt_snaps += 1

            if closed:
                m_mae_terminal = min(mae_previo, profit_apertura + spread_pips)
                m_mfe_terminal = max(mfe_actual, profit_apertura + spread_pips)
                terminal_T = calcular_t_score_trade_numba(m_mfe_terminal, m_mae_terminal, profit_apertura, t_gain, t_loss, spread_pips)
                for k in range(trade_start_snap, cnt_snaps):
                    Y_target[k] = terminal_T
                pos = 0

        elif pos == 0:
            if signos_in[i] < 0 and extremo_in[i] <= (sat_inf_in[i] * armado_in) and acum_in[i] >= (extremo_in[i] * (1.0 - chasquido_in)):
                Z = (W_R[0]*z_base_in[i] + W_R[1]*in_v[i] + W_R[2]*in_a[i] + W_R[3]*math.sin(math.atan2(in_v[i], z_base_in[i])) +
                     W_R[4]*z_base_out[i] + W_R[5]*out_v[i] + W_R[6]*out_a[i] + W_R[7]*math.sin(math.atan2(out_v[i], z_base_out[i])) +
                     W_R[8]*z_macro_1[i] + W_R[9]*z_macro_2[i]) + B_R
                T_raw = _pred10(W_T, B_T, z_base_in[i], in_v[i], in_a[i], math.sin(math.atan2(in_v[i], z_base_in[i])), z_base_out[i], out_v[i], out_a[i], math.sin(math.atan2(out_v[i], z_base_out[i])), z_macro_1[i], z_macro_2[i])
                if Z >= umbral_z_ia and T_raw >= T_min:
                    pos = 1; p_in = opens_arr[i+1]; max_v = p_in; min_v = p_in; idx_in = i + 1
                    Z_pred = Z; v_req = ((Z * mad_v) + med_v) * RATIO_CAPTURA_VELOCIDAD * escala_v[i]; T_hat0 = min(max(T_raw, 0.0), 1.0)
                    t_gain = 0.0; t_loss = 0.0; trade_id += 1; trade_start_snap = cnt_snaps
                    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0

    if pos == 1 and cnt_snaps > trade_start_snap:
        idx_final = cnt_snaps - 1
        m_mfe_terminal = MFE_snap[idx_final]
        m_mae_terminal = MAE_snap[idx_final]
        prof_terminal = Profit_snap[idx_final]
        terminal_T = calcular_t_score_trade_numba(m_mfe_terminal, m_mae_terminal, prof_terminal, t_gain, t_loss, spread_pips)
        for k in range(trade_start_snap, cnt_snaps):
            Y_target[k] = terminal_T

    return (X_traj[:cnt_snaps], Y_target[:cnt_snaps], Profit_snap[:cnt_snaps],
            MAE_snap[:cnt_snaps], MFE_snap[:cnt_snaps], Tscore_snap[:cnt_snaps], TradeId_snap[:cnt_snaps], Vela_snap[:cnt_snaps])

@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def extractor_trayectoria_short_v2(
    signos_in, extremo_in, sat_sup_in, acum_in, signos_out, extremo_out, sat_inf_out, acum_out,
    z_base_in, in_v, in_a, z_base_out, out_v, out_a, z_macro_1, z_macro_2,
    opens_arr, highs_arr, lows_arr, phantom_arr, pips_mult, n_velas,
    armado_in, chasquido_in, armado_out, chasquido_out, spread_pips,
    W_R, B_R, med_v, mad_v, atrac_t, umbral_z_ia, W_T, B_T, T_min, escala_v, v3p=None):

    max_snaps = n_velas + 5
    X_traj = np.empty((max_snaps, 10), dtype=np.float32)
    Profit_snap = np.empty(max_snaps, dtype=np.float32)
    MAE_snap = np.empty(max_snaps, dtype=np.float32)
    MFE_snap = np.empty(max_snaps, dtype=np.float32)
    Tscore_snap = np.empty(max_snaps, dtype=np.float32)
    Y_target = np.zeros(max_snaps, dtype=np.float32)
    TradeId_snap = np.full(max_snaps, -1, dtype=np.int32)
    Vela_snap = np.zeros(max_snaps, dtype=np.int32)

    cnt_snaps = 0; pos = 0; p_in = 0.0; min_v = 0.0; max_v = 0.0; idx_in = 0; v_req = 0.0; Z_pred = 0.0
    t_gain = 0.0; t_loss = 0.0; trade_id = -1; trade_start_snap = 0; T_hat0 = 0.0
    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0   # [LAB-V8] estado vivo de Vida v3
    lim_T_seguro = (atrac_t * TOLERANCIA_VIDA_MEDIA) + 1e-9 if atrac_t > 0 else LIM_T_FALLBACK_VELAS

    for i in range(1, n_velas - 1):
        if pos == -1:
            if highs_arr[i] > max_v: max_v = highs_arr[i]
            if lows_arr[i] < min_v: min_v = lows_arr[i]

            if phantom_arr[i] == 0.0:
                prof_vela = ((p_in - opens_arr[i]) * pips_mult) - spread_pips
                if prof_vela > 0.0: t_gain += 1.0
                else: t_loss += 1.0

            velas_abiertas = max(float(i - idx_in + 1), 1.0)
            mae_previo = (p_in - max_v) * pips_mult; mfe_actual = (p_in - min_v) * pips_mult
            profit_apertura = ((p_in - opens_arr[i+1]) * pips_mult) - spread_pips
            if v3p is not None:   # [LAB-V8] estado vivo de Vida v3
                if velas_abiertas >= 2.0:
                    cn_v += 1.0
                    if profit_apertura > 0.0: cg_v += 1.0
                if profit_apertura < minp_v: minp_v = profit_apertura; vfondo_v = velas_abiertas
            closed = False

            if atrac_t > 0 and velas_abiertas > lim_T_seguro:
                closed = True
            else:
                target_req = max((v_req * velas_abiertas * (1.0 + (abs(mae_previo) / 10.0))) + (abs(mae_previo) * 0.5), spread_pips + 1.0)
                if profit_apertura >= target_req:
                    closed = True

            if not closed:
                if signos_out[i] < 0 and extremo_out[i] <= (sat_inf_out[i] * armado_out) and acum_out[i] >= (extremo_out[i] * (1.0 - chasquido_out)):
                    closed = True

            v_ef = max(velas_abiertas, 3.0)
            V_z = (_velocidad_snapshot(mfe_actual, mae_previo, profit_apertura, v_ef, spread_pips) - med_v) / (mad_v + 1e-9)
            if velas_abiertas <= 2.0: Fid = 0.5
            else: Fid = (math.tanh(V_z - Z_pred) + 1.0) / 2.0

            D_ = 1.0 / (1.0 + (abs(mae_previo) / (mad_v * v_ef + 1e-9)))
            Theta = 1.0 - min(velas_abiertas / lim_T_seguro, 1.0)
            C_ = (math.tanh(mfe_actual / (mad_v * v_ef + 1e-9)) + 1.0) / 2.0

            Z_pred_norm = math.tanh(Z_pred)
            v_ef_norm = math.tanh(v_ef / lim_T_seguro)

            if cnt_snaps < max_snaps:
                X_traj[cnt_snaps, 0] = Fid; X_traj[cnt_snaps, 1] = D_; X_traj[cnt_snaps, 2] = Theta; X_traj[cnt_snaps, 3] = C_
                X_traj[cnt_snaps, 4] = Z_pred_norm; X_traj[cnt_snaps, 5] = v_ef_norm
                X_traj[cnt_snaps, 6] = Theta * D_; X_traj[cnt_snaps, 7] = Fid * D_

                m_mfe_snap = max(mfe_actual, profit_apertura + spread_pips)
                m_mae_snap = min(mae_previo, profit_apertura + spread_pips)
                t_obs_snap = calcular_t_score_trade_numba(m_mfe_snap, m_mae_snap, profit_apertura, t_gain, t_loss, spread_pips)
                dT = min(max(t_obs_snap - T_hat0, -1.0), 1.0)
                if v3p is not None:   # [LAB-V8] ΔT con Vida v3 vivo (T_hat0 en escala V3 cuando NEXUS_LAB_T=V3)
                    dT = min(max(v3_vivo_nb(profit_apertura, m_mfe_snap, m_mae_snap, velas_abiertas, cg_v, cn_v, minp_v, vfondo_v, spread_pips, v3p) - T_hat0, -1.0), 1.0)
                X_traj[cnt_snaps, 8] = dT; X_traj[cnt_snaps, 9] = dT * Theta
                Vela_snap[cnt_snaps] = int(velas_abiertas)

                Profit_snap[cnt_snaps] = profit_apertura
                MFE_snap[cnt_snaps] = m_mfe_snap
                MAE_snap[cnt_snaps] = m_mae_snap
                Tscore_snap[cnt_snaps] = t_obs_snap
                TradeId_snap[cnt_snaps] = trade_id
                cnt_snaps += 1

            if closed:
                m_mae_terminal = min(mae_previo, profit_apertura + spread_pips)
                m_mfe_terminal = max(mfe_actual, profit_apertura + spread_pips)
                terminal_T = calcular_t_score_trade_numba(m_mfe_terminal, m_mae_terminal, profit_apertura, t_gain, t_loss, spread_pips)
                for k in range(trade_start_snap, cnt_snaps):
                    Y_target[k] = terminal_T
                pos = 0

        elif pos == 0:
            if signos_in[i] > 0 and extremo_in[i] >= (sat_sup_in[i] * armado_in) and acum_in[i] <= (extremo_in[i] * (1.0 - chasquido_in)):
                Z = (W_R[0]*z_base_in[i] + W_R[1]*in_v[i] + W_R[2]*in_a[i] + W_R[3]*math.sin(math.atan2(in_v[i], z_base_in[i])) +
                     W_R[4]*z_base_out[i] + W_R[5]*out_v[i] + W_R[6]*out_a[i] + W_R[7]*math.sin(math.atan2(out_v[i], z_base_out[i])) +
                     W_R[8]*z_macro_1[i] + W_R[9]*z_macro_2[i]) + B_R
                T_raw = _pred10(W_T, B_T, z_base_in[i], in_v[i], in_a[i], math.sin(math.atan2(in_v[i], z_base_in[i])), z_base_out[i], out_v[i], out_a[i], math.sin(math.atan2(out_v[i], z_base_out[i])), z_macro_1[i], z_macro_2[i])
                if Z >= umbral_z_ia and T_raw >= T_min:
                    pos = -1; p_in = opens_arr[i+1]; max_v = p_in; min_v = p_in; idx_in = i + 1
                    Z_pred = Z; v_req = ((Z * mad_v) + med_v) * RATIO_CAPTURA_VELOCIDAD * escala_v[i]; T_hat0 = min(max(T_raw, 0.0), 1.0)
                    t_gain = 0.0; t_loss = 0.0; trade_id += 1; trade_start_snap = cnt_snaps
                    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0

    if pos == -1 and cnt_snaps > trade_start_snap:
        idx_final = cnt_snaps - 1
        m_mfe_terminal = MFE_snap[idx_final]
        m_mae_terminal = MAE_snap[idx_final]
        prof_terminal = Profit_snap[idx_final]
        terminal_T = calcular_t_score_trade_numba(m_mfe_terminal, m_mae_terminal, prof_terminal, t_gain, t_loss, spread_pips)
        for k in range(trade_start_snap, cnt_snaps):
            Y_target[k] = terminal_T

    return (X_traj[:cnt_snaps], Y_target[:cnt_snaps], Profit_snap[:cnt_snaps],
            MAE_snap[:cnt_snaps], MFE_snap[:cnt_snaps], Tscore_snap[:cnt_snaps], TradeId_snap[:cnt_snaps], Vela_snap[:cnt_snaps])

# ==========================================================
# 🚀 3. SIMULADORES HÍBRIDOS
# ==========================================================
@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def simular_motor_long_superv_T(
    signos_in, extremo_in, sat_inf_in, acum_in, signos_out, extremo_out, sat_sup_out, acum_out,
    z_base_in, in_v, in_a, z_base_out, out_v, out_a, z_macro_1, z_macro_2,
    opens_arr, highs_arr, lows_arr, phantom_arr, pips_mult, n_velas,
    armado_in, chasquido_in, armado_out, chasquido_out, spread_pips,
    activar_ml, W_R, B_R, med_v, mad_v, atrac_t, umbral_z_ia,
    activar_superv, W_S, B_S, K_abortar, W_T, B_T, T_min, escala_v, v3p=None):

    pos = 0; p_in = 0.0; max_v = 0.0; min_v = 0.0; idx_in = 0; v_req = 0.0; Z_pred = 0.0
    t_gain = 0.0; t_loss = 0.0; trade_tuvo_iteracion = False; T_hat0 = 0.0
    mae_previo = 0.0; mfe_actual = 0.0; profit_apertura = 0.0
    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0   # [LAB-V8] estado vivo de Vida v3

    max_trades = (n_velas // 2) + 5
    mfe_A = np.empty(max_trades, dtype=np.float32); mae_A = np.empty(max_trades, dtype=np.float32)
    prof_A = np.empty(max_trades, dtype=np.float32); tscore_A = np.empty(max_trades, dtype=np.float32)
    cnt = 0
    lim_T_seguro = (atrac_t * TOLERANCIA_VIDA_MEDIA) + 1e-9 if atrac_t > 0 else LIM_T_FALLBACK_VELAS

    for i in range(1, n_velas - 1):
        if pos == 1:
            trade_tuvo_iteracion = True
            if highs_arr[i] > max_v: max_v = highs_arr[i]
            if lows_arr[i] < min_v: min_v = lows_arr[i]

            if phantom_arr[i] == 0.0:
                prof_vela = ((opens_arr[i] - p_in) * pips_mult) - spread_pips
                if prof_vela > 0.0: t_gain += 1.0
                else: t_loss += 1.0

            velas_abiertas = max(float(i - idx_in + 1), 1.0)
            mae_previo = (min_v - p_in) * pips_mult; mfe_actual = (max_v - p_in) * pips_mult
            profit_apertura = ((opens_arr[i+1] - p_in) * pips_mult) - spread_pips
            if v3p is not None:   # [LAB-V8] estado vivo de Vida v3
                if velas_abiertas >= 2.0:
                    cn_v += 1.0
                    if profit_apertura > 0.0: cg_v += 1.0
                if profit_apertura < minp_v: minp_v = profit_apertura; vfondo_v = velas_abiertas
            closed = False; m_mae = mae_previo

            if activar_ml:
                if atrac_t > 0 and velas_abiertas > lim_T_seguro:
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)
                else:
                    target_req = max((v_req * velas_abiertas * (1.0 + (abs(mae_previo) / 10.0))) + (abs(mae_previo) * 0.5), spread_pips + 1.0)
                    if profit_apertura >= target_req: closed = True; m_mae = mae_previo
            if not closed:
                if signos_out[i] > 0 and extremo_out[i] >= (sat_sup_out[i] * armado_out) and acum_out[i] <= (extremo_out[i] * (1.0 - chasquido_out)):
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)

            if not closed and activar_superv and velas_abiertas > INMUNIDAD_VELAS_EFECTIVA:
                v_ef = max(velas_abiertas, 3.0); V_z = (_velocidad_snapshot(mfe_actual, mae_previo, profit_apertura, v_ef, spread_pips) - med_v) / (mad_v + 1e-9)
                if velas_abiertas <= 2.0: Fid = 0.5
                else: Fid = (math.tanh(V_z - Z_pred) + 1.0) / 2.0

                D_ = 1.0 / (1.0 + (abs(mae_previo) / (mad_v * v_ef + 1e-9)))
                Theta = 1.0 - min(velas_abiertas / lim_T_seguro, 1.0)
                C_ = (math.tanh(mfe_actual / (mad_v * v_ef + 1e-9)) + 1.0) / 2.0
                inter_TD = Theta * D_; inter_FD = Fid * D_

                Z_pred_norm = math.tanh(Z_pred)
                v_ef_norm = math.tanh(v_ef / lim_T_seguro)

                bruto_s = profit_apertura + spread_pips
                t_obs = calcular_t_score_trade_numba(max(mfe_actual, bruto_s), min(mae_previo, bruto_s), profit_apertura, t_gain, t_loss, spread_pips)
                dT = min(max(t_obs - T_hat0, -1.0), 1.0)
                if v3p is not None:   # [LAB-V8] ΔT con Vida v3 vivo
                    dT = min(max(v3_vivo_nb(profit_apertura, max(mfe_actual, bruto_s), min(mae_previo, bruto_s), velas_abiertas, cg_v, cn_v, minp_v, vfondo_v, spread_pips, v3p) - T_hat0, -1.0), 1.0)
                T_pred = (W_S[0]*Fid + W_S[1]*D_ + W_S[2]*Theta + W_S[3]*C_ + W_S[4]*Z_pred_norm + W_S[5]*v_ef_norm + W_S[6]*inter_TD + W_S[7]*inter_FD + W_S[8]*dT + W_S[9]*(dT*Theta)) + B_S

                if T_pred < K_abortar:
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)

            if closed:
                if cnt < max_trades:
                    m_mfe = max(mfe_actual, profit_apertura + spread_pips)
                    mfe_A[cnt] = m_mfe; mae_A[cnt] = m_mae; prof_A[cnt] = profit_apertura
                    tscore_A[cnt] = calcular_t_score_trade_numba(m_mfe, m_mae, profit_apertura, t_gain, t_loss, spread_pips)
                    cnt += 1
                pos = 0

        elif pos == 0:
            if signos_in[i] < 0 and extremo_in[i] <= (sat_inf_in[i] * armado_in) and acum_in[i] >= (extremo_in[i] * (1.0 - chasquido_in)):
                autorizado = True; v_req_tmp = 0.0; z_tmp = 0.0; t_raw = 0.0
                if activar_ml:
                    z_tmp = (W_R[0]*z_base_in[i] + W_R[1]*in_v[i] + W_R[2]*in_a[i] + W_R[3]*math.sin(math.atan2(in_v[i], z_base_in[i])) +
                             W_R[4]*z_base_out[i] + W_R[5]*out_v[i] + W_R[6]*out_a[i] + W_R[7]*math.sin(math.atan2(out_v[i], z_base_out[i])) +
                             W_R[8]*z_macro_1[i] + W_R[9]*z_macro_2[i]) + B_R
                    if z_tmp < umbral_z_ia: autorizado = False
                    else: v_req_tmp = ((z_tmp * mad_v) + med_v) * RATIO_CAPTURA_VELOCIDAD
                    t_raw = _pred10(W_T, B_T, z_base_in[i], in_v[i], in_a[i], math.sin(math.atan2(in_v[i], z_base_in[i])), z_base_out[i], out_v[i], out_a[i], math.sin(math.atan2(out_v[i], z_base_out[i])), z_macro_1[i], z_macro_2[i])
                    if t_raw < T_min: autorizado = False
                if autorizado:
                    pos = 1; p_in = opens_arr[i+1]; max_v = p_in; min_v = p_in; idx_in = i + 1
                    v_req = v_req_tmp * escala_v[i]; Z_pred = z_tmp; T_hat0 = min(max(t_raw, 0.0), 1.0); t_gain = 0.0; t_loss = 0.0; trade_tuvo_iteracion = False
                    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0

    if pos == 1 and trade_tuvo_iteracion and cnt < max_trades:
        idx_final = n_velas - 1
        profit_apertura = ((opens_arr[idx_final] - p_in) * pips_mult) - spread_pips
        mae_previo = (min_v - p_in) * pips_mult; mfe_actual = (max_v - p_in) * pips_mult
        m_mfe = max(mfe_actual, profit_apertura + spread_pips)
        m_mae = min(mae_previo, profit_apertura + spread_pips)
        mfe_A[cnt] = m_mfe; mae_A[cnt] = m_mae; prof_A[cnt] = profit_apertura
        tscore_A[cnt] = calcular_t_score_trade_numba(m_mfe, m_mae, profit_apertura, t_gain, t_loss, spread_pips)
        cnt += 1

    return mfe_A[:cnt], mae_A[:cnt], prof_A[:cnt], tscore_A[:cnt]

@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def simular_motor_short_superv_T(
    signos_in, extremo_in, sat_sup_in, acum_in, signos_out, extremo_out, sat_inf_out, acum_out,
    z_base_in, in_v, in_a, z_base_out, out_v, out_a, z_macro_1, z_macro_2,
    opens_arr, highs_arr, lows_arr, phantom_arr, pips_mult, n_velas,
    armado_in, chasquido_in, armado_out, chasquido_out, spread_pips,
    activar_ml, W_R, B_R, med_v, mad_v, atrac_t, umbral_z_ia,
    activar_superv, W_S, B_S, K_abortar, W_T, B_T, T_min, escala_v, v3p=None):

    pos = 0; p_in = 0.0; max_v = 0.0; min_v = 0.0; idx_in = 0; v_req = 0.0; Z_pred = 0.0
    t_gain = 0.0; t_loss = 0.0; trade_tuvo_iteracion = False; T_hat0 = 0.0
    mae_previo = 0.0; mfe_actual = 0.0; profit_apertura = 0.0
    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0   # [LAB-V8] estado vivo de Vida v3

    max_trades = (n_velas // 2) + 5
    mfe_A = np.empty(max_trades, dtype=np.float32); mae_A = np.empty(max_trades, dtype=np.float32)
    prof_A = np.empty(max_trades, dtype=np.float32); tscore_A = np.empty(max_trades, dtype=np.float32)
    cnt = 0
    lim_T_seguro = (atrac_t * TOLERANCIA_VIDA_MEDIA) + 1e-9 if atrac_t > 0 else LIM_T_FALLBACK_VELAS

    for i in range(1, n_velas - 1):
        if pos == -1:
            trade_tuvo_iteracion = True
            if highs_arr[i] > max_v: max_v = highs_arr[i]
            if lows_arr[i] < min_v: min_v = lows_arr[i]

            if phantom_arr[i] == 0.0:
                prof_vela = ((p_in - opens_arr[i]) * pips_mult) - spread_pips
                if prof_vela > 0.0: t_gain += 1.0
                else: t_loss += 1.0

            velas_abiertas = max(float(i - idx_in + 1), 1.0)
            mae_previo = (p_in - max_v) * pips_mult; mfe_actual = (p_in - min_v) * pips_mult
            profit_apertura = ((p_in - opens_arr[i+1]) * pips_mult) - spread_pips
            if v3p is not None:   # [LAB-V8] estado vivo de Vida v3
                if velas_abiertas >= 2.0:
                    cn_v += 1.0
                    if profit_apertura > 0.0: cg_v += 1.0
                if profit_apertura < minp_v: minp_v = profit_apertura; vfondo_v = velas_abiertas
            closed = False; m_mae = mae_previo

            if activar_ml:
                if atrac_t > 0 and velas_abiertas > lim_T_seguro:
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)
                else:
                    target_req = max((v_req * velas_abiertas * (1.0 + (abs(mae_previo) / 10.0))) + (abs(mae_previo) * 0.5), spread_pips + 1.0)
                    if profit_apertura >= target_req: closed = True; m_mae = mae_previo
            if not closed:
                if signos_out[i] < 0 and extremo_out[i] <= (sat_inf_out[i] * armado_out) and acum_out[i] >= (extremo_out[i] * (1.0 - chasquido_out)):
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)

            if not closed and activar_superv and velas_abiertas > INMUNIDAD_VELAS_EFECTIVA:
                v_ef = max(velas_abiertas, 3.0); V_z = (_velocidad_snapshot(mfe_actual, mae_previo, profit_apertura, v_ef, spread_pips) - med_v) / (mad_v + 1e-9)
                if velas_abiertas <= 2.0: Fid = 0.5
                else: Fid = (math.tanh(V_z - Z_pred) + 1.0) / 2.0

                D_ = 1.0 / (1.0 + (abs(mae_previo) / (mad_v * v_ef + 1e-9)))
                Theta = 1.0 - min(velas_abiertas / lim_T_seguro, 1.0)
                C_ = (math.tanh(mfe_actual / (mad_v * v_ef + 1e-9)) + 1.0) / 2.0
                inter_TD = Theta * D_; inter_FD = Fid * D_

                Z_pred_norm = math.tanh(Z_pred)
                v_ef_norm = math.tanh(v_ef / lim_T_seguro)

                bruto_s = profit_apertura + spread_pips
                t_obs = calcular_t_score_trade_numba(max(mfe_actual, bruto_s), min(mae_previo, bruto_s), profit_apertura, t_gain, t_loss, spread_pips)
                dT = min(max(t_obs - T_hat0, -1.0), 1.0)
                if v3p is not None:   # [LAB-V8] ΔT con Vida v3 vivo
                    dT = min(max(v3_vivo_nb(profit_apertura, max(mfe_actual, bruto_s), min(mae_previo, bruto_s), velas_abiertas, cg_v, cn_v, minp_v, vfondo_v, spread_pips, v3p) - T_hat0, -1.0), 1.0)
                T_pred = (W_S[0]*Fid + W_S[1]*D_ + W_S[2]*Theta + W_S[3]*C_ + W_S[4]*Z_pred_norm + W_S[5]*v_ef_norm + W_S[6]*inter_TD + W_S[7]*inter_FD + W_S[8]*dT + W_S[9]*(dT*Theta)) + B_S

                if T_pred < K_abortar:
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)

            if closed:
                if cnt < max_trades:
                    m_mfe = max(mfe_actual, profit_apertura + spread_pips)
                    mfe_A[cnt] = m_mfe; mae_A[cnt] = m_mae; prof_A[cnt] = profit_apertura
                    tscore_A[cnt] = calcular_t_score_trade_numba(m_mfe, m_mae, profit_apertura, t_gain, t_loss, spread_pips)
                    cnt += 1
                pos = 0

        elif pos == 0:
            if signos_in[i] > 0 and extremo_in[i] >= (sat_sup_in[i] * armado_in) and acum_in[i] <= (extremo_in[i] * (1.0 - chasquido_in)):
                autorizado = True; v_req_tmp = 0.0; z_tmp = 0.0; t_raw = 0.0
                if activar_ml:
                    z_tmp = (W_R[0]*z_base_in[i] + W_R[1]*in_v[i] + W_R[2]*in_a[i] + W_R[3]*math.sin(math.atan2(in_v[i], z_base_in[i])) +
                             W_R[4]*z_base_out[i] + W_R[5]*out_v[i] + W_R[6]*out_a[i] + W_R[7]*math.sin(math.atan2(out_v[i], z_base_out[i])) +
                             W_R[8]*z_macro_1[i] + W_R[9]*z_macro_2[i]) + B_R
                    if z_tmp < umbral_z_ia: autorizado = False
                    else: v_req_tmp = ((z_tmp * mad_v) + med_v) * RATIO_CAPTURA_VELOCIDAD
                    t_raw = _pred10(W_T, B_T, z_base_in[i], in_v[i], in_a[i], math.sin(math.atan2(in_v[i], z_base_in[i])), z_base_out[i], out_v[i], out_a[i], math.sin(math.atan2(out_v[i], z_base_out[i])), z_macro_1[i], z_macro_2[i])
                    if t_raw < T_min: autorizado = False
                if autorizado:
                    pos = -1; p_in = opens_arr[i+1]; max_v = p_in; min_v = p_in; idx_in = i + 1
                    Z_pred = z_tmp; v_req = v_req_tmp * escala_v[i]; T_hat0 = min(max(t_raw, 0.0), 1.0); t_gain = 0.0; t_loss = 0.0; trade_tuvo_iteracion = False
                    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0

    if pos == -1 and trade_tuvo_iteracion and cnt < max_trades:
        idx_final = n_velas - 1
        profit_apertura = ((p_in - opens_arr[idx_final]) * pips_mult) - spread_pips
        mae_previo = (p_in - max_v) * pips_mult; mfe_actual = (p_in - min_v) * pips_mult
        m_mfe = max(mfe_actual, profit_apertura + spread_pips)
        m_mae = min(mae_previo, profit_apertura + spread_pips)
        mfe_A[cnt] = m_mfe; mae_A[cnt] = m_mae; prof_A[cnt] = profit_apertura
        tscore_A[cnt] = calcular_t_score_trade_numba(m_mfe, m_mae, profit_apertura, t_gain, t_loss, spread_pips)
        cnt += 1

    return mfe_A[:cnt], mae_A[:cnt], prof_A[:cnt], tscore_A[:cnt]

# ==========================================================
# 🚀 4. ESCANEO DE K_ABORTAR — VÍA SIMULADOR REAL, IS-ONLY
# ==========================================================
# [LAB-V7 V0.4] Copias de los simuladores con 2 salidas más (vela de entrada y de salida por trade). Solo las usa NEXUS_LAB_METRICA=v7.
@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def simular_motor_long_superv_T_ix(
    signos_in, extremo_in, sat_inf_in, acum_in, signos_out, extremo_out, sat_sup_out, acum_out,
    z_base_in, in_v, in_a, z_base_out, out_v, out_a, z_macro_1, z_macro_2,
    opens_arr, highs_arr, lows_arr, phantom_arr, pips_mult, n_velas,
    armado_in, chasquido_in, armado_out, chasquido_out, spread_pips,
    activar_ml, W_R, B_R, med_v, mad_v, atrac_t, umbral_z_ia,
    activar_superv, W_S, B_S, K_abortar, W_T, B_T, T_min, escala_v, v3p=None):

    pos = 0; p_in = 0.0; max_v = 0.0; min_v = 0.0; idx_in = 0; v_req = 0.0; Z_pred = 0.0
    t_gain = 0.0; t_loss = 0.0; trade_tuvo_iteracion = False; T_hat0 = 0.0
    mae_previo = 0.0; mfe_actual = 0.0; profit_apertura = 0.0
    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0   # [LAB-V8] estado vivo de Vida v3

    max_trades = (n_velas // 2) + 5
    mfe_A = np.empty(max_trades, dtype=np.float32); mae_A = np.empty(max_trades, dtype=np.float32)
    prof_A = np.empty(max_trades, dtype=np.float32); tscore_A = np.empty(max_trades, dtype=np.float32)
    ent_A = np.empty(max_trades, dtype=np.int64); sal_A = np.empty(max_trades, dtype=np.int64)
    cnt = 0
    lim_T_seguro = (atrac_t * TOLERANCIA_VIDA_MEDIA) + 1e-9 if atrac_t > 0 else LIM_T_FALLBACK_VELAS

    for i in range(1, n_velas - 1):
        if pos == 1:
            trade_tuvo_iteracion = True
            if highs_arr[i] > max_v: max_v = highs_arr[i]
            if lows_arr[i] < min_v: min_v = lows_arr[i]

            if phantom_arr[i] == 0.0:
                prof_vela = ((opens_arr[i] - p_in) * pips_mult) - spread_pips
                if prof_vela > 0.0: t_gain += 1.0
                else: t_loss += 1.0

            velas_abiertas = max(float(i - idx_in + 1), 1.0)
            mae_previo = (min_v - p_in) * pips_mult; mfe_actual = (max_v - p_in) * pips_mult
            profit_apertura = ((opens_arr[i+1] - p_in) * pips_mult) - spread_pips
            if v3p is not None:   # [LAB-V8] estado vivo de Vida v3
                if velas_abiertas >= 2.0:
                    cn_v += 1.0
                    if profit_apertura > 0.0: cg_v += 1.0
                if profit_apertura < minp_v: minp_v = profit_apertura; vfondo_v = velas_abiertas
            closed = False; m_mae = mae_previo

            if activar_ml:
                if atrac_t > 0 and velas_abiertas > lim_T_seguro:
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)
                else:
                    target_req = max((v_req * velas_abiertas * (1.0 + (abs(mae_previo) / 10.0))) + (abs(mae_previo) * 0.5), spread_pips + 1.0)
                    if profit_apertura >= target_req: closed = True; m_mae = mae_previo
            if not closed:
                if signos_out[i] > 0 and extremo_out[i] >= (sat_sup_out[i] * armado_out) and acum_out[i] <= (extremo_out[i] * (1.0 - chasquido_out)):
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)

            if not closed and activar_superv and velas_abiertas > INMUNIDAD_VELAS_EFECTIVA:
                v_ef = max(velas_abiertas, 3.0); V_z = (_velocidad_snapshot(mfe_actual, mae_previo, profit_apertura, v_ef, spread_pips) - med_v) / (mad_v + 1e-9)
                if velas_abiertas <= 2.0: Fid = 0.5
                else: Fid = (math.tanh(V_z - Z_pred) + 1.0) / 2.0

                D_ = 1.0 / (1.0 + (abs(mae_previo) / (mad_v * v_ef + 1e-9)))
                Theta = 1.0 - min(velas_abiertas / lim_T_seguro, 1.0)
                C_ = (math.tanh(mfe_actual / (mad_v * v_ef + 1e-9)) + 1.0) / 2.0
                inter_TD = Theta * D_; inter_FD = Fid * D_

                Z_pred_norm = math.tanh(Z_pred)
                v_ef_norm = math.tanh(v_ef / lim_T_seguro)

                bruto_s = profit_apertura + spread_pips
                t_obs = calcular_t_score_trade_numba(max(mfe_actual, bruto_s), min(mae_previo, bruto_s), profit_apertura, t_gain, t_loss, spread_pips)
                dT = min(max(t_obs - T_hat0, -1.0), 1.0)
                if v3p is not None:   # [LAB-V8] ΔT con Vida v3 vivo
                    dT = min(max(v3_vivo_nb(profit_apertura, max(mfe_actual, bruto_s), min(mae_previo, bruto_s), velas_abiertas, cg_v, cn_v, minp_v, vfondo_v, spread_pips, v3p) - T_hat0, -1.0), 1.0)
                T_pred = (W_S[0]*Fid + W_S[1]*D_ + W_S[2]*Theta + W_S[3]*C_ + W_S[4]*Z_pred_norm + W_S[5]*v_ef_norm + W_S[6]*inter_TD + W_S[7]*inter_FD + W_S[8]*dT + W_S[9]*(dT*Theta)) + B_S

                if T_pred < K_abortar:
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)

            if closed:
                if cnt < max_trades:
                    m_mfe = max(mfe_actual, profit_apertura + spread_pips)
                    mfe_A[cnt] = m_mfe; mae_A[cnt] = m_mae; prof_A[cnt] = profit_apertura; ent_A[cnt] = idx_in; sal_A[cnt] = i + 1
                    tscore_A[cnt] = calcular_t_score_trade_numba(m_mfe, m_mae, profit_apertura, t_gain, t_loss, spread_pips)
                    cnt += 1
                pos = 0

        elif pos == 0:
            if signos_in[i] < 0 and extremo_in[i] <= (sat_inf_in[i] * armado_in) and acum_in[i] >= (extremo_in[i] * (1.0 - chasquido_in)):
                autorizado = True; v_req_tmp = 0.0; z_tmp = 0.0; t_raw = 0.0
                if activar_ml:
                    z_tmp = (W_R[0]*z_base_in[i] + W_R[1]*in_v[i] + W_R[2]*in_a[i] + W_R[3]*math.sin(math.atan2(in_v[i], z_base_in[i])) +
                             W_R[4]*z_base_out[i] + W_R[5]*out_v[i] + W_R[6]*out_a[i] + W_R[7]*math.sin(math.atan2(out_v[i], z_base_out[i])) +
                             W_R[8]*z_macro_1[i] + W_R[9]*z_macro_2[i]) + B_R
                    if z_tmp < umbral_z_ia: autorizado = False
                    else: v_req_tmp = ((z_tmp * mad_v) + med_v) * RATIO_CAPTURA_VELOCIDAD
                    t_raw = _pred10(W_T, B_T, z_base_in[i], in_v[i], in_a[i], math.sin(math.atan2(in_v[i], z_base_in[i])), z_base_out[i], out_v[i], out_a[i], math.sin(math.atan2(out_v[i], z_base_out[i])), z_macro_1[i], z_macro_2[i])
                    if t_raw < T_min: autorizado = False
                if autorizado:
                    pos = 1; p_in = opens_arr[i+1]; max_v = p_in; min_v = p_in; idx_in = i + 1
                    v_req = v_req_tmp * escala_v[i]; Z_pred = z_tmp; T_hat0 = min(max(t_raw, 0.0), 1.0); t_gain = 0.0; t_loss = 0.0; trade_tuvo_iteracion = False
                    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0

    if pos == 1 and trade_tuvo_iteracion and cnt < max_trades:
        idx_final = n_velas - 1
        profit_apertura = ((opens_arr[idx_final] - p_in) * pips_mult) - spread_pips
        mae_previo = (min_v - p_in) * pips_mult; mfe_actual = (max_v - p_in) * pips_mult
        m_mfe = max(mfe_actual, profit_apertura + spread_pips)
        m_mae = min(mae_previo, profit_apertura + spread_pips)
        mfe_A[cnt] = m_mfe; mae_A[cnt] = m_mae; prof_A[cnt] = profit_apertura; ent_A[cnt] = idx_in; sal_A[cnt] = idx_final
        tscore_A[cnt] = calcular_t_score_trade_numba(m_mfe, m_mae, profit_apertura, t_gain, t_loss, spread_pips)
        cnt += 1

    return mfe_A[:cnt], mae_A[:cnt], prof_A[:cnt], tscore_A[:cnt], ent_A[:cnt], sal_A[:cnt]


@njit(cache=True, fastmath=False, boundscheck=False, nogil=True)
def simular_motor_short_superv_T_ix(
    signos_in, extremo_in, sat_sup_in, acum_in, signos_out, extremo_out, sat_inf_out, acum_out,
    z_base_in, in_v, in_a, z_base_out, out_v, out_a, z_macro_1, z_macro_2,
    opens_arr, highs_arr, lows_arr, phantom_arr, pips_mult, n_velas,
    armado_in, chasquido_in, armado_out, chasquido_out, spread_pips,
    activar_ml, W_R, B_R, med_v, mad_v, atrac_t, umbral_z_ia,
    activar_superv, W_S, B_S, K_abortar, W_T, B_T, T_min, escala_v, v3p=None):

    pos = 0; p_in = 0.0; max_v = 0.0; min_v = 0.0; idx_in = 0; v_req = 0.0; Z_pred = 0.0
    t_gain = 0.0; t_loss = 0.0; trade_tuvo_iteracion = False; T_hat0 = 0.0
    mae_previo = 0.0; mfe_actual = 0.0; profit_apertura = 0.0
    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0   # [LAB-V8] estado vivo de Vida v3

    max_trades = (n_velas // 2) + 5
    mfe_A = np.empty(max_trades, dtype=np.float32); mae_A = np.empty(max_trades, dtype=np.float32)
    prof_A = np.empty(max_trades, dtype=np.float32); tscore_A = np.empty(max_trades, dtype=np.float32)
    ent_A = np.empty(max_trades, dtype=np.int64); sal_A = np.empty(max_trades, dtype=np.int64)
    cnt = 0
    lim_T_seguro = (atrac_t * TOLERANCIA_VIDA_MEDIA) + 1e-9 if atrac_t > 0 else LIM_T_FALLBACK_VELAS

    for i in range(1, n_velas - 1):
        if pos == -1:
            trade_tuvo_iteracion = True
            if highs_arr[i] > max_v: max_v = highs_arr[i]
            if lows_arr[i] < min_v: min_v = lows_arr[i]

            if phantom_arr[i] == 0.0:
                prof_vela = ((p_in - opens_arr[i]) * pips_mult) - spread_pips
                if prof_vela > 0.0: t_gain += 1.0
                else: t_loss += 1.0

            velas_abiertas = max(float(i - idx_in + 1), 1.0)
            mae_previo = (p_in - max_v) * pips_mult; mfe_actual = (p_in - min_v) * pips_mult
            profit_apertura = ((p_in - opens_arr[i+1]) * pips_mult) - spread_pips
            if v3p is not None:   # [LAB-V8] estado vivo de Vida v3
                if velas_abiertas >= 2.0:
                    cn_v += 1.0
                    if profit_apertura > 0.0: cg_v += 1.0
                if profit_apertura < minp_v: minp_v = profit_apertura; vfondo_v = velas_abiertas
            closed = False; m_mae = mae_previo

            if activar_ml:
                if atrac_t > 0 and velas_abiertas > lim_T_seguro:
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)
                else:
                    target_req = max((v_req * velas_abiertas * (1.0 + (abs(mae_previo) / 10.0))) + (abs(mae_previo) * 0.5), spread_pips + 1.0)
                    if profit_apertura >= target_req: closed = True; m_mae = mae_previo
            if not closed:
                if signos_out[i] < 0 and extremo_out[i] <= (sat_inf_out[i] * armado_out) and acum_out[i] >= (extremo_out[i] * (1.0 - chasquido_out)):
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)

            if not closed and activar_superv and velas_abiertas > INMUNIDAD_VELAS_EFECTIVA:
                v_ef = max(velas_abiertas, 3.0); V_z = (_velocidad_snapshot(mfe_actual, mae_previo, profit_apertura, v_ef, spread_pips) - med_v) / (mad_v + 1e-9)
                if velas_abiertas <= 2.0: Fid = 0.5
                else: Fid = (math.tanh(V_z - Z_pred) + 1.0) / 2.0

                D_ = 1.0 / (1.0 + (abs(mae_previo) / (mad_v * v_ef + 1e-9)))
                Theta = 1.0 - min(velas_abiertas / lim_T_seguro, 1.0)
                C_ = (math.tanh(mfe_actual / (mad_v * v_ef + 1e-9)) + 1.0) / 2.0
                inter_TD = Theta * D_; inter_FD = Fid * D_

                Z_pred_norm = math.tanh(Z_pred)
                v_ef_norm = math.tanh(v_ef / lim_T_seguro)

                bruto_s = profit_apertura + spread_pips
                t_obs = calcular_t_score_trade_numba(max(mfe_actual, bruto_s), min(mae_previo, bruto_s), profit_apertura, t_gain, t_loss, spread_pips)
                dT = min(max(t_obs - T_hat0, -1.0), 1.0)
                if v3p is not None:   # [LAB-V8] ΔT con Vida v3 vivo
                    dT = min(max(v3_vivo_nb(profit_apertura, max(mfe_actual, bruto_s), min(mae_previo, bruto_s), velas_abiertas, cg_v, cn_v, minp_v, vfondo_v, spread_pips, v3p) - T_hat0, -1.0), 1.0)
                T_pred = (W_S[0]*Fid + W_S[1]*D_ + W_S[2]*Theta + W_S[3]*C_ + W_S[4]*Z_pred_norm + W_S[5]*v_ef_norm + W_S[6]*inter_TD + W_S[7]*inter_FD + W_S[8]*dT + W_S[9]*(dT*Theta)) + B_S

                if T_pred < K_abortar:
                    closed = True; m_mae = min(mae_previo, profit_apertura + spread_pips)

            if closed:
                if cnt < max_trades:
                    m_mfe = max(mfe_actual, profit_apertura + spread_pips)
                    mfe_A[cnt] = m_mfe; mae_A[cnt] = m_mae; prof_A[cnt] = profit_apertura; ent_A[cnt] = idx_in; sal_A[cnt] = i + 1
                    tscore_A[cnt] = calcular_t_score_trade_numba(m_mfe, m_mae, profit_apertura, t_gain, t_loss, spread_pips)
                    cnt += 1
                pos = 0

        elif pos == 0:
            if signos_in[i] > 0 and extremo_in[i] >= (sat_sup_in[i] * armado_in) and acum_in[i] <= (extremo_in[i] * (1.0 - chasquido_in)):
                autorizado = True; v_req_tmp = 0.0; z_tmp = 0.0; t_raw = 0.0
                if activar_ml:
                    z_tmp = (W_R[0]*z_base_in[i] + W_R[1]*in_v[i] + W_R[2]*in_a[i] + W_R[3]*math.sin(math.atan2(in_v[i], z_base_in[i])) +
                             W_R[4]*z_base_out[i] + W_R[5]*out_v[i] + W_R[6]*out_a[i] + W_R[7]*math.sin(math.atan2(out_v[i], z_base_out[i])) +
                             W_R[8]*z_macro_1[i] + W_R[9]*z_macro_2[i]) + B_R
                    if z_tmp < umbral_z_ia: autorizado = False
                    else: v_req_tmp = ((z_tmp * mad_v) + med_v) * RATIO_CAPTURA_VELOCIDAD
                    t_raw = _pred10(W_T, B_T, z_base_in[i], in_v[i], in_a[i], math.sin(math.atan2(in_v[i], z_base_in[i])), z_base_out[i], out_v[i], out_a[i], math.sin(math.atan2(out_v[i], z_base_out[i])), z_macro_1[i], z_macro_2[i])
                    if t_raw < T_min: autorizado = False
                if autorizado:
                    pos = -1; p_in = opens_arr[i+1]; max_v = p_in; min_v = p_in; idx_in = i + 1
                    Z_pred = z_tmp; v_req = v_req_tmp * escala_v[i]; T_hat0 = min(max(t_raw, 0.0), 1.0); t_gain = 0.0; t_loss = 0.0; trade_tuvo_iteracion = False
                    cg_v = 0.0; cn_v = 0.0; minp_v = 1e30; vfondo_v = 0.0

    if pos == -1 and trade_tuvo_iteracion and cnt < max_trades:
        idx_final = n_velas - 1
        profit_apertura = ((p_in - opens_arr[idx_final]) * pips_mult) - spread_pips
        mae_previo = (p_in - max_v) * pips_mult; mfe_actual = (p_in - min_v) * pips_mult
        m_mfe = max(mfe_actual, profit_apertura + spread_pips)
        m_mae = min(mae_previo, profit_apertura + spread_pips)
        mfe_A[cnt] = m_mfe; mae_A[cnt] = m_mae; prof_A[cnt] = profit_apertura; ent_A[cnt] = idx_in; sal_A[cnt] = idx_final
        tscore_A[cnt] = calcular_t_score_trade_numba(m_mfe, m_mae, profit_apertura, t_gain, t_loss, spread_pips)
        cnt += 1

    return mfe_A[:cnt], mae_A[:cnt], prof_A[:cnt], tscore_A[:cnt], ent_A[:cnt], sal_A[:cnt]

# ==========================================================
# 🚀 4. ESCANEO DE K_ABORTAR — VÍA SIMULADOR REAL, IS-ONLY
# ==========================================================

def escanear_umbral_k(sim_is, W_S, B_S, candidatos_k, min_trades):
    mejor_score = 0.0; mejor_k = None; mejor_r = None
    for K in candidatos_k:
        mfe, mae, prof, tsc = sim_is(True, W_S, B_S, float(K))
        r = eval_robustez_numba_v6(mfe, mae, prof, tsc, min_trades)
        if r[0] > mejor_score:
            mejor_score = r[0]; mejor_k = float(K); mejor_r = r
    return mejor_k, mejor_r

# ==========================================================
# ⚙️ MLOps SCIKIT — RIDGE ENTRADA + RIDGE SUPERVIVENCIA
# ==========================================================
def _estandarizar(X):
    mu = X.mean(axis=0); sd = X.std(axis=0)
    sd = np.where(sd < 1e-9, 1.0, sd)
    return (X - mu) / sd, mu, sd

def _desestandarizar(coef_s, inter_s, mu, sd):
    w = np.asarray(coef_s, dtype=np.float64) / sd
    b = float(inter_s) - float(np.dot(w, mu))
    return np.round(w, DEC_W), round(b, DEC_W)

def entrenar_modelo_ridge(df_ml):
    if df_ml.empty or len(df_ml) < MIN_OPS_IS_REPORTE:
        return None, None, 0.0, 0.0, 0.0, "Cero/Insuficiente."

    df_is = df_ml.copy()
    friccion_mae = 1.0 + (df_is['MAE_Pips'].abs() / 10.0)
    v_cruda_is = (df_is['MFE_Pips'] - df_is['MAE_Pips'].abs()) / (df_is['Velas_Vida'] * friccion_mae)
    df_is['V_cruda'] = v_cruda_is
    ganadores_is = df_is[df_is['Profit_Pips'] > 0.0]
    if len(ganadores_is) < 5: ganadores_is = df_is

    mediana_v = ganadores_is['V_cruda'].median(); mad_v = (ganadores_is['V_cruda'] - mediana_v).abs().median()
    if mad_v < 1e-8: mad_v = 0.01
    atractor_tiempo = ganadores_is['Velas_Vida'].median()
    y_train = ((df_is['V_cruda'] - mediana_v) / mad_v).values.astype(np.float64)
    X_raw = df_is[COLS_X_ENTRADA].values.astype(np.float64)
    if not (np.isfinite(X_raw).all() and np.isfinite(y_train).all()):
        return None, None, 0.0, 0.0, 0.0, "NaN/Inf en dataset Ridge entrada."

    Xs, mu, sd = _estandarizar(X_raw)
    try:
        modelo = RidgeCV(alphas=ALPHAS_RIDGE, cv=None); modelo.fit(Xs, y_train)
    except Exception:
        _registrar_fallback_ridge('entrada')
        modelo = Ridge(alpha=1.0, solver='auto', random_state=42); modelo.fit(Xs, y_train)

    W, B = _desestandarizar(modelo.coef_, modelo.intercept_, mu, sd)
    return W, B, round(float(mediana_v), DEC_W), round(float(mad_v), DEC_W), round(float(atractor_tiempo), DEC_T), "OK"

def entrenar_cabeza_T(df_ml):
    if df_ml.empty or len(df_ml) < MIN_OPS_IS_REPORTE:
        return None, None, 0.0, 0.0, "Cero/Insuficiente."
    X_raw = df_ml[COLS_X_ENTRADA].values.astype(np.float64); y = df_ml['T_Terminal'].values.astype(np.float64)
    if not (np.isfinite(X_raw).all() and np.isfinite(y).all()):
        return None, None, 0.0, 0.0, "NaN/Inf en dataset cabeza T."
    Xs, mu, sd = _estandarizar(X_raw)
    try:
        modelo = RidgeCV(alphas=ALPHAS_RIDGE, cv=None); modelo.fit(Xs, y); alpha = float(modelo.alpha_)
    except Exception:
        _registrar_fallback_ridge('T')
        modelo = Ridge(alpha=1.0, solver='auto', random_state=42); modelo.fit(Xs, y); alpha = 1.0
    oof = np.empty_like(y)
    for tr, te in KFold(n_splits=N_FOLDS_OOF_T, shuffle=False).split(Xs):
        m = Ridge(alpha=alpha, solver='auto', random_state=42); m.fit(Xs[tr], y[tr]); oof[te] = m.predict(Xs[te])
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float(((y - oof) ** 2).sum()) / ss_tot if ss_tot > 1e-12 else 0.0
    T_min = float(np.percentile(oof, 100.0 * Q_ADMISION_T))
    W, B = _desestandarizar(modelo.coef_, modelo.intercept_, mu, sd)
    return W, B, round(T_min, DEC_W), round(r2, DEC_PCT), "OK"

def entrenar_modelo_supervivencia_ridge(X_traj, Y_target, tid_snap, n_trades):
    if n_trades < MIN_TRADES_SUPERV_IS:
        return np.zeros(10, dtype=np.float64), 0.0, "Cero/Insuficiente (trades)."

    X_raw = np.asarray(X_traj[:, :N_FEAT_SUPERV], dtype=np.float64); y = np.asarray(Y_target, dtype=np.float64)
    if not (np.isfinite(X_raw).all() and np.isfinite(y).all()):
        return np.zeros(10, dtype=np.float64), 0.0, "NaN/Inf en dataset supervivencia."

    tid = np.asarray(tid_snap, dtype=np.int64)

    Xs, mu, sd = _estandarizar(X_raw)
    try:
        n_splits = max(2, min(K_FOLDS_CV_SUPERV, n_trades))
        splits = list(GroupKFold(n_splits=n_splits).split(Xs, y, groups=tid))
        modelo = RidgeCV(alphas=ALPHAS_RIDGE_SUPERV, cv=splits)
        modelo.fit(Xs, y)
    except Exception:
        _registrar_fallback_ridge('superv')
        modelo = Ridge(alpha=1.0, solver='auto', random_state=42)
        modelo.fit(Xs, y)

    W, B = _desestandarizar(modelo.coef_, modelo.intercept_, mu, sd)
    W = np.concatenate([np.asarray(W, dtype=np.float64), np.zeros(10 - len(W), dtype=np.float64)])   
    return W, B, "OK"


# ==========================================================
# 🔥 JIT WARM-UP (se invoca desde main)
# ==========================================================
def _warmup_jit():
    n = 100
    f32 = np.zeros(n, dtype=np.float32); p64 = np.ones(n, dtype=np.float64)
    S = (f32,) * 16 + (p64, p64, p64)
    ph = np.zeros(n, dtype=np.float32)
    w10 = np.zeros(10, dtype=np.float64); w8 = np.zeros(10, dtype=np.float64)
    for ext_r, ext_t, sim in ((extractor_ml_long, extractor_trayectoria_long_v2, simular_motor_long_superv_T),
                              (extractor_ml_short, extractor_trayectoria_short_v2, simular_motor_short_superv_T)):
        ext_r(*S, ph, 100.0, n, 0.5, 0.1, 0.5, 0.1, 1.2)
        ext_t(*S, ph, 100.0, n, 0.5, 0.1, 0.5, 0.1, 1.2, w10, 0.0, 0.5, 0.1, 10.0, 0.0, w10, 0.0, -1.0, p64)
        sim(*S, ph, 100.0, n, 0.5, 0.1, 0.5, 0.1, 1.2, True, w10, 0.0, 0.5, 0.1, 10.0, 0.0, True, w8, 0.0, 0.3, w10, 0.0, -1.0, p64)
    cambios = np.zeros(n, dtype=np.int32); cambios[0] = 0
    signos = np.ones(n, dtype=np.float32)
    acum = calcular_acum_ciclo_numba(f32, cambios)
    calcular_extremos_numba(signos, acum, cambios)
    mx, mn = obtener_extremos_ciclo_numba(cambios, acum, signos, 0)
    rolling_median_causal_numba(mn, direction=-1, memoria_fifo=MEMORIA_FIFO)
    rolling_median_causal_numba(mx, direction=1, memoria_fifo=MEMORIA_FIFO)
    # 🛡️ [H-M2-02 CERRADO] Precalentamiento del evaluador SSOT
    eval_robustez_numba_v6(f32, f32, f32, f32, 5)


# ==========================================================
# 🧾 GENERADORES DE EXPORT (D.R.Y.) — COMPATIBLE EA V12.01+
# ==========================================================
def _bloque_mql5(c, export_idx, dir_nombre, cfg, ml, sv, emoji, umbral):
    row = c['row']
    M_in, R_in, P_in, B_in, A_in, arm_in, chq_in = parse_mql5_gatillo(row['⚖️ BASE IN'], row['📊 ACUM IN'], row['⚙️ Arm_IN'], row['⚡ Chq_IN'])
    M_out, R_out, P_out, B_out, A_out, arm_out, chq_out = parse_mql5_gatillo(row['⚖️ BASE OUT'], row['📊 ACUM OUT'], row['⚙️ Arm_OUT'], row['⚡ Chq_OUT'])
    prefix = "" if export_idx == 0 else f"\n      /* --- [OPCIONAL {dir_nombre} RANK #{export_idx+1}] ---\n"
    suffix = "\n" if export_idx == 0 else "\n      */\n"   # [LAB-V8 H-AUD8-02] el bloque RANK #1 termina en salto de línea (antes ""): su última línea ya no se pega a la cabecera del bloque siguiente
    wR = c['W_R']; bR = c['B_R']; wS = c['W_S']; bS = c['B_S']; kA = c['K_opt']
    
    # 🧠 Cabeza A de Ridge 1 (10 pesos canónicos)
    w_ml = " ".join(f"g_pares[idx].{ml}.w[{k}]={wR[k]:.{DEC_W}f};" for k in range(10))
    
    # 🧠 Cabeza B de Ridge 1 (Activa para E2/E3 en EA V12.01+)
    if _GATE_T_ACTIVO:
        w_T_str = " ".join(f"g_pares[idx].{ml}.w_T[{k}]={c['W_T'][k]:.{DEC_W}f};" for k in range(10))
        cabeza_b_mql = (f"g_pares[idx].{ml}.cabeza_t_activa = true; g_pares[idx].{ml}.bias_T = {c['B_T']:.{DEC_W}f}; "
                        f"g_pares[idx].{ml}.t_min_admision = {c['T_min']:.{DEC_W}f};\n      {w_T_str}")
    else:
        cabeza_b_mql = f"g_pares[idx].{ml}.cabeza_t_activa = false; g_pares[idx].{ml}.t_min_admision = 0.0;"

    # 🧠 Ridge 2 de Supervivencia (8 o 10 pesos según ESCALON)
    w_sv = " ".join(f"g_pares[idx].{sv}.w_superv[{k}]={wS[k]:.{DEC_W}f};" for k in range(N_FEAT_SUPERV))
    superv_cfg = f"g_pares[idx].{sv}.inmunidad_velas = {INMUNIDAD_VELAS_EFECTIVA}; g_pares[idx].{sv}.n_features = {N_FEAT_SUPERV};"

    tam_mql = lab_bloque_tam(ml, c.get('TAM'))
    p = DEC_PCT
    return f"""{prefix}      // {emoji} {dir_nombre} SUPERVIVENCIA CONTINUA {FASE4_VERSION} RANK #{export_idx+1} (Fold: {int(row['Fold'])} | Sel_IS: {c['ClaveRank']:.2f} | Flujo: {c['ScoreFlujo']:.1f} | K_Abortar: {kA:.2f} | Vida_IS_Ganadores(atrac_t): {c['atrac_t']:.1f}) | T-Score OOS: {c['Med_T_OOS']:.2f}
      g_pares[idx].cfg.{cfg}.marco_in = {M_in}; g_pares[idx].cfg.{cfg}.res_in = {R_in}; g_pares[idx].cfg.{cfg}.pz_in = {P_in}; g_pares[idx].cfg.{cfg}.base_in = {B_in}; g_pares[idx].cfg.{cfg}.tension_in = {A_in}; g_pares[idx].cfg.{cfg}.armado_in = {arm_in:.{p}f}; g_pares[idx].cfg.{cfg}.chasquido_in = {chq_in:.{p}f};
      g_pares[idx].cfg.{cfg}.marco_out = {M_out}; g_pares[idx].cfg.{cfg}.res_out = {R_out}; g_pares[idx].cfg.{cfg}.pz_out = {P_out}; g_pares[idx].cfg.{cfg}.base_out = {B_out}; g_pares[idx].cfg.{cfg}.tension_out = {A_out}; g_pares[idx].cfg.{cfg}.armado_out = {arm_out:.{p}f}; g_pares[idx].cfg.{cfg}.chasquido_out = {chq_out:.{p}f};
      g_pares[idx].{ml}.activado = true; g_pares[idx].{ml}.umbral = {umbral}; g_pares[idx].{ml}.bias = {bR:.{DEC_W}f}; g_pares[idx].{ml}.mediana_v = {c['med_v']:.{DEC_W}f}; g_pares[idx].{ml}.mad_v = {c['mad_v']:.{DEC_W}f}; g_pares[idx].{ml}.limite_tiempo = {c['atrac_t']:.{DEC_T}f}; g_pares[idx].{ml}.ratio_captura = {RATIO_CAPTURA_VELOCIDAD}; g_pares[idx].{ml}.tolerancia_vida = {TOLERANCIA_VIDA_MEDIA};
      {w_ml}
      {cabeza_b_mql}{tam_mql}
      // 🧠 MOTOR DE SUPERVIVENCIA CONTINUA (superv_toro/oso — compatible EA V12.01+).
      g_pares[idx].{sv}.b_superv = {bS:.{DEC_W}f}; g_pares[idx].{sv}.k_abortar = {kA:.5f}; {superv_cfg}
      {w_sv}{lab_bloque_vida(sv, c.get('V3P'))}{suffix}"""

def _fila_reporte(simbolo, dir_nombre, idx, c, st):
    r = c['row']
    rech = c['Base_Rechazado']
    return {
        'Simbolo': simbolo, 'Core_Ver': FORMULAS_CORE_VERSION, 'Fase4_Ver': FASE4_VERSION,
        'Fid_Vel_Unif': bool(FID_VELOCIDAD_UNIFICADA), 'Escalon': ESCALON, 'T_Min_Admision': round(c['T_min'], 4), 'R2_OOF_T': (round(c['r2_T'], 4) if c['r2_T'] == c['r2_T'] else 'NA'), 'Trades_IS_Base': c['n_is_base'], 'Trades_IS_Superv_Sim': c['n_is_superv'], 'Trades_IS_Superv_Train': c['n_trades_train'], 'Dir': dir_nombre, 'Rank_IA': idx + 1,
        'Fold': int(r['Fold']),
        'Rank_Opt_Orig': r['Rank'], 'K_Abortar': round(c['K_opt'], 2),
        'SEL_SCORE_IS': round(c['ClaveRank'], 3),
        'Metrica': LAB_METRICA, 'SF_IS': round(c['EX']['sf_is'], 3), 'V7_IS': round(c['EX']['v7_is'], 3),
        'SF_OOS': round(c['EX']['sf_oos'], 3), 'V7_OOS': round(c['EX']['v7_oos'], 3),
        'SCORE_FLUJO_IA': round(c['ScoreFlujo'], 2),
        'T-SCORE_OOS': round(c['Med_T_OOS'], 2), 'T-SCORE_IS': round(c['Med_T_IS'], 2),
        'T-SCORE_IS_Base': round(c['Med_T_IS_Base'], 2),
        'Retencion_%': round(c['Retencion'], 2), 'Retencion_Raw_%': round(c['Retencion_Raw'], 2),
        '⚖️ BASE IN': r['⚖️ BASE IN'], '📊 ACUM IN': r['📊 ACUM IN'], '⚙️ Arm_IN': r['⚙️ Arm_IN'], '⚡ Chq_IN': r['⚡ Chq_IN'], '|': '|',
        '⚖️ BASE OUT': r['⚖️ BASE OUT'], '📊 ACUM OUT': r['📊 ACUM OUT'], '⚙️ Arm_OUT': r['⚙️ Arm_OUT'], '⚡ Chq_OUT': r['⚡ Chq_OUT'], '||': '||',
        'WR_IS_Superv_%': round(c['WR_IS'], 1), 'MaxDD_IS_Superv': round(c['MaxDD_IS'], 1),
        'Trades_OOS_Ridge': c['Ops_Ridge'], 'Trades_OOS_Superv': c['Ops_Superv'],
        'WR_OOS_Ridge_%': "RECHAZADO" if rech else round(c['WR_Ridge'], 1),
        'WR_OOS_Superv_%': round(c['WR_Superv'], 1),
        'MaxDD_OOS_Ridge': "RECHAZADO" if rech else round(c['MaxDD_Ridge'], 1),
        'MaxDD_OOS_Superv': round(c['MaxDD_Superv'], 1),
        'PF_OOS_Ridge': "RECHAZADO" if rech else round(c['PF_Ridge'], 2),
        'PF_OOS_Superv': round(c['PF_Superv'], 2),
        'MedProfitPips_OOS_Ridge': "RECHAZADO" if rech else round(c['MedProfitPips_Ridge'], 1),
        'MedProfitPips_OOS_Superv': round(c['MedProfitPips_Superv'], 1),
        'N_Cand_OOS_Evaluados': st['n_eval'], 'N_Cand_Compuerta_OK': st['n_ok'],
        'Mediana_ScoreOOS_Todos': round(st['med_score_oos'], 2),
        **({} if not LAB_USA_VIDA else {'Vida_ver': LAB_VIDA, 'T_modo': LAB_T, 'V3_rit_vmin': (round(float(c['V3P'][1]), 4) if c.get('V3P') is not None else 'NA')}),   # [LAB-V8]
        **({} if LAB_CIERRE not in ('V3', 'dV3') else {**{f'R2V_{n}': (round(v, 4) if v == v else 'NA') for n, v in zip(VV.DESCRIPTORES + ('V3',), c['VIDA'].get('r2', [float('nan')] * 6))}, 'Corr_max_desc': (round(c['VIDA'].get('corr_max', float('nan')), 3) if c['VIDA'] else 'NA')})
    }

def _escritura_atomica(ruta, contenido_o_df, es_df=False):
    tmp = ruta + ".tmp"
    if es_df: contenido_o_df.to_csv(tmp, index=False, encoding='utf-8-sig')
    else:
        with open(tmp, 'w', encoding='utf-8') as f: f.write(contenido_o_df)
    os.replace(tmp, ruta)

# ==========================================================
# 🔄 PROCESAMIENTO POR SÍMBOLO
# ==========================================================
def _columnas_candidato(row):
    cols = set()
    for b, a in ((row['⚖️ BASE IN'], row['📊 ACUM IN']), (row['⚖️ BASE OUT'], row['📊 ACUM OUT'])):
        cols.update([b, a, obtener_z_base(b, a)])
        v, ac = deducir_features(b, a)
        if v is not None: cols.update([v, ac])
    m1, m2 = obtener_contexto_macro(row['⚖️ BASE IN'], row['📊 ACUM IN'])
    cols.update([m1, m2])
    return cols

def _leer_parquet_columnas(archivo, columnas):
    try:
        import pyarrow.parquet as pq
        disp = set(pq.ParquetFile(archivo).schema.names)
        cols = [c for c in columnas if c in disp]
        return pd.read_parquet(archivo, columns=cols).reset_index(drop=True)
    except Exception as e:
        print(f"   ⚠️ Lectura parcial de parquet no disponible ({type(e).__name__}); se lee completo.")
        return pd.read_parquet(archivo).reset_index(drop=True)

# ==========================================================
# [LAB-V7] FUNCIONES DE LABORATORIO (módulo; probadas en lab_pruebas.py)
# ==========================================================
def lab_escala_v(modo, nulo, rng, N_velas, ini_tr, fin_tr, ini_te, fin_te, df_ml, act_arr, X10, params_out=None):
    """Arreglo float64 de largo N_velas con la escala de v_req por vela de decisión. 'off' => unos (idéntico a main).
    Solo usa datos IS para ajustar (mediana de actividad, Ridge MFE, normalización). Lanza ValueError(causa) si no es válida.
    Los parámetros se redondean a DEC_W antes de calcular la escala (los que exporta el EA). params_out (dict) recibe los parámetros."""
    esc_total = np.ones(N_velas, dtype=np.float64)
    if modo == 'off':
        return esc_total
    act_med0 = float(np.nanmedian(act_arr[ini_tr:fin_tr]))
    act_is = act_arr[ini_tr + df_ml['Idx_Decision'].values.astype(np.int64)]
    # [LAB-V8 H-AUD8-01] Las decisiones sin dato de actividad (NaN: primeras ACT_VENTANA-1 velas del archivo) se EXCLUYEN del ajuste (mediana y Ridge de tamaño);
    # antes una sola descartaba al candidato entero. Si todas tienen dato, `ok` es todo True y el resultado es idéntico bit a bit al anterior. Un infinito sigue siendo inválido.
    ok = ~np.isnan(act_is)
    if not (act_med0 > 0.0) or np.isinf(act_is).any() or not ok.any():
        raise ValueError("Lab_actividad_invalida")
    act_med = round(act_med0, DEC_W)
    if not (act_med > 0.0):
        raise ValueError("Lab_actividad_invalida")
    a_is = act_is / act_med
    a_is_med = round(float(np.median(a_is[ok])), DEC_W)
    if not (a_is_med > 0.0):
        raise ValueError("Lab_actividad_invalida")
    act_w = np.ascontiguousarray(act_arr[ini_tr:fin_te], dtype=np.float64)
    par = {'modo': modo, 'act_med': act_med, 'a_is_med': a_is_med}
    if modo == 'B':
        esc = _lab_esc_B_nb(act_w, act_med, a_is_med, ESCALA_MIN, ESCALA_MAX)
    else:
        Xi = np.c_[df_ml[COLS_X_ENTRADA].values.astype(np.float64), a_is][ok]   # [LAB-V8 H-AUD8-01] solo decisiones con dato de actividad
        Xs_i, mu_i, sd_i = _estandarizar(Xi)
        mod_m = RidgeCV(alphas=ALPHAS_RIDGE, cv=None); mod_m.fit(Xs_i, df_ml['MFE_Pips'].values.astype(np.float64)[ok])
        med_pred = round(float(np.median(mod_m.predict(Xs_i))), DEC_W)
        if not (med_pred > 0.0):
            raise ValueError("Lab_MFE_mediana_no_positiva")
        coef = np.round(np.asarray(mod_m.coef_, dtype=np.float64), DEC_W); inter = round(float(mod_m.intercept_), DEC_W)
        mu_r = np.round(np.asarray(mu_i, dtype=np.float64), DEC_W); sd_r = np.round(np.asarray(sd_i, dtype=np.float64), DEC_W)
        if not (sd_r > 0.0).all():
            raise ValueError("Lab_sd_nula")
        esc = _lab_esc_A_nb(np.ascontiguousarray(X10, dtype=np.float64), act_w, act_med, a_is_med, coef, inter, mu_r, sd_r, med_pred,
                            ESCALA_MIN, ESCALA_MAX)
        par.update({'coef': coef, 'intercept': inter, 'mu': mu_r, 'sd': sd_r, 'med_pred': med_pred})
    if not np.isfinite(esc).all():
        raise ValueError("Lab_escala_no_finita")
    esc_total[ini_tr:fin_te] = esc
    if nulo:
        for _a, _b in ((ini_tr, fin_tr), (ini_te, fin_te)):
            _L = _b - _a; _sh = int(rng.integers(int(0.1 * _L), int(0.9 * _L) + 1))
            esc_total[_a:_b] = np.roll(esc_total[_a:_b], _sh)
    if params_out is not None:
        params_out.clear(); params_out.update(par)
    return esc_total


def lab_bloque_vida(sv, v3p):
    """[LAB-V8] Constantes de Vida v3 del cerebro (solo con NEXUS_LAB_T=V3). Vacío si v3p es None: el bloque exportado queda idéntico al de lab-v7."""
    if v3p is None: return ""
    t = f"\n      g_pares[idx].{sv}.vida_activa = true; g_pares[idx].{sv}.vida_h = {v3p[0]:.{DEC_W}f}; g_pares[idx].{sv}.vida_rit_vmin = {v3p[1]:.{DEC_W}f}; g_pares[idx].{sv}.vida_rec_na = {v3p[2]:.{DEC_W}f};"
    for nombre, a in (('vida_med', 3), ('vida_esc', 8), ('vida_peso', 13)):
        t += "\n      " + " ".join(f"g_pares[idx].{sv}.{nombre}[{k}]={v3p[a + k]:.{DEC_W}f};" for k in range(5))
    return t


def lab_bloque_tam(ml, tam):
    """Texto C++ con los parámetros del Ridge de tamaño para el EA gemelo. Vacío si no hay modo de tamaño (texto idéntico a main)."""
    if not tam or tam.get('modo', 'off') == 'off':
        return ""
    p = f"g_pares[idx].{ml}."
    modo = 1 if tam['modo'] == 'A' else 2
    t = (f"\n      // 📐 [LAB-V7] RIDGE DE TAMAÑO (modo {tam['modo']}): v_req = v_req * escala (clip {ESCALA_MIN}-{ESCALA_MAX}). Solo EA gemelo.\n      "
         f"{p}tam_modo = {modo}; {p}tam_act_med = {tam['act_med']:.{DEC_W}f}; {p}tam_a_is_med = {tam['a_is_med']:.{DEC_W}f}; "
         f"{p}tam_esc_min = {ESCALA_MIN}; {p}tam_esc_max = {ESCALA_MAX};")
    if modo == 1:
        t += f" {p}tam_intercept = {tam['intercept']:.{DEC_W}f}; {p}tam_med_pred = {tam['med_pred']:.{DEC_W}f};"
        for nombre, v in (('tam_w', tam['coef']), ('tam_mu', tam['mu']), ('tam_sd', tam['sd'])):
            t += "\n      " + " ".join(f"{p}{nombre}[{k}]={v[k]:.{DEC_W}f};" for k in range(11))
    return t


def lab_eval_v7(tup, dircode, O, H, L, pm, c, nt, sigma_sr, n_min, min_trades, seed):
    """Evalúa un resultado de simulador `_ix` (mfe, mae, prof, tsc, ent, sal). Devuelve (r, ex): r = vector de eval_robustez_numba_v6 con
    r[0] reemplazado por Score_v7; ex = {'sf': Score_final de los mismos trades, 'v7': Score_v7}."""
    mfe, mae, prof, tsc, ent, sal = tup
    r = np.array(eval_robustez_numba_v6(mfe, mae, prof, tsc, min_trades), dtype=np.float64)
    sf = float(r[0]); n = len(prof); v7 = 0.0; _res_v7 = None
    if n >= 3:
        try:
            res = V7.score_v7(np.full(n, dircode, dtype=np.int64), ent, sal, prof.astype(np.float64), O, H, L, O, pm, c, nt=nt,
                              sigma_sr=sigma_sr, opcion=LAB_V7_OPCION, rng=np.random.default_rng(seed), R=LAB_V7_R, n_min=n_min)
            v7 = float(res['score_v7']); _res_v7 = res
        except ValueError:
            v7 = 0.0        # ventana más corta que la escala h (60 velas): sin puntaje
    r[0] = v7
    ex = {'sf': sf, 'v7': v7}
    if LAB_CENSO: ex.update(INF.extras_v7(prof, _res_v7))   # [LAB-V8 informes] componentes de Score_v7 y pips totales (ya calculados)
    return r, ex


def lab_escanear_k_v7(sim_ix, grid, dircode, O, H, L, pm, c, min_trades, seed):
    """Escaneo de K con Score_v7. Pasada 1: simula cada K y mide el Sharpe del alfa -> sigma_sr; pasada 2: Score_v7 con nt = len(grid)."""
    tups = [sim_ix(True, float(K)) for K in grid]
    srs = []
    for t in tups:
        n = len(t[2])
        if n >= 3:
            sen = V7.fusionar(np.full(n, dircode, dtype=np.int64), t[4], t[5], t[2].astype(np.float64))
            if len(sen['E']) >= 3:
                a = V7.alfa(sen, O, pm, LAB_V7_OPCION); sd = a.std(ddof=1)
                if sd > 0: srs.append(a.mean() / sd)
    sigma = float(np.std(srs, ddof=1)) if len(srs) >= 2 else 0.0
    mejor_score = 0.0; mejor_k = None; mejor_r = None; mejor_ex = {'sf': float('nan'), 'v7': float('nan')}
    for K, t in zip(grid, tups):
        r, ex = lab_eval_v7(t, dircode, O, H, L, pm, c, len(grid), sigma, min_trades, min_trades, seed + int(round(float(K) * 1e5)) % 1000003)
        if r[0] > mejor_score:
            mejor_score = r[0]; mejor_k = float(K); mejor_r = r; mejor_ex = ex
    return mejor_k, mejor_r, mejor_ex


def lab_target_cierre(modo, y_target, tsc_snap, prof_snap, tid_snap, mfe_snap=None, mae_snap=None, vela_snap=None, spread=None, h=None, vida_out=None, v3p=None):
    """Target de Ridge 2 por foto. T_terminal => sin cambio. dT_cont = T_terminal - T_obs(t). G_pips = pips finales del trade - profit_apertura(t).
    V3 = Vida v3 terminal del trade (vida_v3.py); si se pasa `vida_out` (dict) se llena con el resultado completo (descriptores) para el reporte."""
    if len(tid_snap) == 0 or modo == 'T_terminal':
        return y_target
    if modo in ('V3', 'dV3'):
        v = VV.vida_v31(prof_snap, mfe_snap, mae_snap, tid_snap, vela_snap, float(spread), float(h), ver=LAB_VIDA, v3p=v3p)   # [LAB-V8]
        if vida_out is not None: vida_out.update(v)
        if modo == 'dV3': return (v['V3_term'].astype(np.float64) - v['V3']).astype(np.float32)   # H-V3-01: V3 terminal - V3 vivo(t)
        return v['V3_term']
    if modo == 'dT_cont':
        return (y_target - tsc_snap).astype(np.float32)
    tids, rev = np.unique(tid_snap[::-1], return_index=True)       # última foto de cada trade = vela de cierre
    fin = prof_snap[len(tid_snap) - 1 - rev]
    return (fin[np.searchsorted(tids, tid_snap)] - prof_snap).astype(np.float32)


def lab_grid_k(modo, x_traj, W_S, B_S):
    """Grilla de K. T_terminal => la de main. Otro target => percentiles 0..50 de la predicción IS (T_pred = x·W_S + B_S, como en el kernel)."""
    if modo == 'T_terminal':
        return CANDIDATOS_K_ABORTAR
    pred = x_traj[:, :N_FEAT_SUPERV].astype(np.float64) @ W_S[:N_FEAT_SUPERV] + B_S
    return np.unique(np.round(np.percentile(pred, PERCENTILES_K_LAB), 5)).astype(np.float64)   # 5 decimales = precisión de export (k_abortar %.5f)


def procesar_simbolo(SIMBOLO):
    print("\n" + "█" * 90)
    print(f"🪙 INICIANDO ORÁCULO {FASE4_VERSION} (RIDGE ENTRADA + SUPERVIVENCIA CONTINUA) T_SCORE_IS/OOS C-SYNC: {SIMBOLO}")
    print("█" * 90)

    SPREAD_ACTIVO = round(float(MATRIZ_SPREADS.get(SIMBOLO, SPREAD_FALLBACK)), DEC_SPREAD)
    reporte_torneo_local = []
    censo_local = []   # [LAB-V8 informes]

    nombre_csv = PATRON_CSV_FASE3.format(simbolo=SIMBOLO)
    if not os.path.exists(nombre_csv):
        print(f"   ⚠️ [{SIMBOLO}] Sin CSV de Fase 3 ({nombre_csv}). Símbolo saltado.")
        return 'sin_csv'

    df_opt = pd.read_csv(nombre_csv)
    _faltan = [c for c in COLS_REQ_FASE3 if c not in df_opt.columns]
    if _faltan:
        print(f"   ⛔ [{SIMBOLO}] CSV de Fase 3 sin columnas requeridas {_faltan}. Símbolo saltado.")
        _registrar_descarte(SIMBOLO, "ALL", "CSV_Fase3_columnas_faltantes")
        return 'csv_invalido'
    df_long = df_opt[df_opt['Dir'].str.contains('LONG')]; df_short = df_opt[df_opt['Dir'].str.contains('SHORT')]
    if df_long.empty or df_short.empty:
        print(f"   ⚠️ [{SIMBOLO}] CSV de Fase 3 sin candidatos LONG y/o SHORT. Símbolo saltado.")
        return 'sin_campeones'

    archivo_parquet = f'nexus_df_salida_3D_{SIMBOLO}_MultiZ.parquet'
    if not os.path.exists(archivo_parquet):
        print(f"   ⚠️ [{SIMBOLO}] Sin Parquet de Fase 1&2 ({archivo_parquet}). Símbolo saltado.")
        return 'sin_parquet'

    requeridas = {'OpenM1', 'HighM1', 'LowM1', 'Phantom'}
    for _df in (df_long.head(TOP_CANDIDATOS), df_short.head(TOP_CANDIDATOS)):
        for _row in _df.to_dict('records'):
            try: requeridas.update(_columnas_candidato(_row))
            except Exception: pass   
    df_map = _leer_parquet_columnas(archivo_parquet, sorted(requeridas))
    N_total = len(df_map); df_map = TAB.recortar(df_map)   
    try:
        TAB.verificar_sello(df_opt, n_total=N_total, origen=f"CSV de Fase 3 ({nombre_csv})")   
    except TAB.ErrorSello as e:
        print(f"   ⛔ [{SIMBOLO}] {e}"); _registrar_descarte(SIMBOLO, "ALL", "Sello_Fase3_invalido")
        del df_map; gc.collect(); return 'csv_invalido'

    if 'Phantom' in df_map.columns:
        phantom_arr = df_map['Phantom'].to_numpy(dtype=np.float32, copy=True)
    elif PERMITIR_PHANTOM_AUSENTE:
        print(f"   ⚠️ [{SIMBOLO}] Columna 'Phantom' ausente: se asume 0.0 por flag explícito PERMITIR_PHANTOM_AUSENTE.")
        phantom_arr = np.zeros(len(df_map), dtype=np.float32)
    else:
        print(f"   ⛔ FATAL ERROR [{SIMBOLO}]: columna 'Phantom' ausente en el parquet. Símbolo abortado.")
        _registrar_descarte(SIMBOLO, "ALL", "Phantom_ausente_SIMBOLO_ABORTADO")
        del df_map; gc.collect()
        return 'sin_phantom'

    N_velas = len(df_map); PIPS_MULT = 100.0 if 'JPY' in SIMBOLO else 10000.0
    opens_arr = df_map['OpenM1'].to_numpy(dtype=np.float64, copy=True)
    highs_arr = df_map['HighM1'].to_numpy(dtype=np.float64, copy=True)
    lows_arr = df_map['LowM1'].to_numpy(dtype=np.float64, copy=True)
    ACT_ARR = lab_actividad_nb(opens_arr, PIPS_MULT, ACT_VENTANA)   # [LAB-V7] suma directa secuencial (paridad con el EA gemelo); NaN en las primeras 59 velas

    ARR = {c: df_map[c].to_numpy(dtype=np.float32, copy=True) for c in df_map.columns if c not in ('OpenM1', 'HighM1', 'LowM1', 'Phantom')}
    del df_map; gc.collect()
    bytes_cache = sum(a.nbytes for a in ARR.values()) + opens_arr.nbytes + highs_arr.nbytes + lows_arr.nbytes + phantom_arr.nbytes

    GEOM = TAB.geometria(N_total)   
    assert GEOM['n_ef'] == N_velas, f"[TABLERO] N efectivo {GEOM['n_ef']} != filas cargadas {N_velas}"
    TEST_SIZE = GEOM['test']; TRAIN_SIZE = GEOM['train']
    print(f"   🧭 [TABLERO v{TAB.TABLERO_VERSION} | hash {TAB.hash_params()}] N_total={N_total} N_efectivo={N_velas} "
          f"reserva={'[%d, %d)' % GEOM['reserva'] if GEOM['reserva'] else 'ninguna'} | folds={N_FOLDS} | IS/OOS={TRAIN_SIZE}/{TEST_SIZE}")

    n_workers, ram_ef, huella = _calibrar_workers(N_velas, bytes_cache)
    print(f"   🎛️ RAM efectiva {ram_ef / 1e9:.2f} GB | cache {bytes_cache / 1e6:.0f} MB | huella/candidato ≈{huella / 1e6:.0f} MB "
          f"=> Workers {n_workers}/{MAX_VCPUS}")

    def calc_dinamico(col_base, col_acum, mode, hasta):
        signos = np.sign(ARR[col_base][:hasta]).astype(np.float32)
        mask_zero = (signos == 0)
        if mask_zero.any():
            idx_validos = np.where(~mask_zero)[0]
            if len(idx_validos) > 0:
                if mask_zero[0]: signos[0] = 1.0
                idx_arr = np.arange(len(signos))
                idx_arr[mask_zero] = 0
                idx_arr = np.maximum.accumulate(idx_arr)
                signos = signos[idx_arr]
            else:
                signos[:] = 1.0

        cambios = np.concatenate(([0], (signos[1:] != signos[:-1]).astype(np.int32))).astype(np.int32)
        ciclos = cambios.cumsum().astype(np.int32)
        acum = calcular_acum_ciclo_numba(ARR[col_acum][:hasta].copy(), cambios)
        extremo = calcular_extremos_numba(signos, acum, cambios)
        max_v, min_v = obtener_extremos_ciclo_numba(ciclos, acum, signos, int(ciclos[-1]))
        if mode == 'inf': sat_series = rolling_median_causal_numba(min_v, direction=-1, memoria_fifo=MEMORIA_FIFO)
        else: sat_series = rolling_median_causal_numba(max_v, direction=1, memoria_fifo=MEMORIA_FIFO)
        return signos, extremo, sat_series[ciclos], acum

    def ejecutar_torneo(df_candidatos, direccion_nombre, extract_r_func, ext_traj_func, sim_superv_func, umbral_z_ia):
        top_n = df_candidatos.head(TOP_CANDIDATOS)

        def procesar_candidato(row_data):
            cz = {'etapa': '1_preparacion'}   # [LAB-V8 informes] anotaciones del candidato para el censo (solo valores ya calculados)
            if LAB_CENSO: cz['_t0'] = INF.reloj()
            def desc(causa):
                _registrar_descarte(SIMBOLO, direccion_nombre, causa)
                if LAB_CENSO: INF.registrar(censo_local, cz, row_data, SIMBOLO, direccion_nombre, 'descartado', causa)
                return None
            try:
                idx, row = row_data

                fold = int(row['Fold']) - 1
                if not (0 <= fold < N_FOLDS): return desc("Fold_fuera_de_rango")
                start_train, end_train, start_test, end_test = GEOM['folds'][fold + 1]   
                TRAIN_LEN = end_train - start_train; TEST_LEN = end_test - start_test
                if TRAIN_LEN <= 0 or TEST_LEN <= 0 or end_test > N_velas: return desc("Ventana_fuera_de_limites")

                arm_in = parse_pct(row['⚙️ Arm_IN']); chq_in = parse_pct(row['⚡ Chq_IN'])
                arm_out = parse_pct(row['⚙️ Arm_OUT']); chq_out = parse_pct(row['⚡ Chq_OUT'])
                modo_in = 'inf' if 'LONG' in direccion_nombre else 'sup'; modo_out = 'sup' if 'LONG' in direccion_nombre else 'inf'

                try:
                    parse_mql5_gatillo(row['⚖️ BASE IN'], row['📊 ACUM IN'], row['⚙️ Arm_IN'], row['⚡ Chq_IN'])
                    parse_mql5_gatillo(row['⚖️ BASE OUT'], row['📊 ACUM OUT'], row['⚙️ Arm_OUT'], row['⚡ Chq_OUT'])
                except (ValueError, IndexError):
                    return desc("Formato_MQL5_invalido")

                c_in_v, c_in_a = deducir_features(row['⚖️ BASE IN'], row['📊 ACUM IN'])
                c_out_v, c_out_a = deducir_features(row['⚖️ BASE OUT'], row['📊 ACUM OUT'])
                if c_in_v is None or c_out_v is None: return desc("Familia_features_desconocida")

                z_base_in_col = obtener_z_base(row['⚖️ BASE IN'], row['📊 ACUM IN']); z_base_out_col = obtener_z_base(row['⚖️ BASE OUT'], row['📊 ACUM OUT'])
                col_macro_1, col_macro_2 = obtener_contexto_macro(row['⚖️ BASE IN'], row['📊 ACUM IN'])

                sig_in, ext_in, sat_in, ac_in = calc_dinamico(row['⚖️ BASE IN'], row['📊 ACUM IN'], modo_in, end_test)
                sig_out, ext_out, sat_out, ac_out = calc_dinamico(row['⚖️ BASE OUT'], row['📊 ACUM OUT'], modo_out, end_test)

                zbi = ARR[z_base_in_col]; zbo = ARR[z_base_out_col]
                viv = ARR[c_in_v]; via = ARR[c_in_a]; vov = ARR[c_out_v]; voa = ARR[c_out_a]
                zm1 = ARR[col_macro_1]; zm2 = ARR[col_macro_2]
            except KeyError as e:
                return desc(f"KeyError:{str(e)}")
            except Exception as e:
                return desc(f"Excepcion_preparacion:{type(e).__name__}")

            try:
                arrs_check = (sig_in, ext_in, sat_in, ac_in, sig_out, ext_out, sat_out, ac_out,
                              zbi, viv, via, zbo, vov, voa, zm1, zm2, opens_arr, highs_arr, lows_arr, phantom_arr)
                if not all(np.isfinite(a[start_train:end_test]).all() for a in arrs_check): return desc("NaN_Inf_en_ventana")

                def S(a, b):
                    return (sig_in[a:b], ext_in[a:b], sat_in[a:b], ac_in[a:b], sig_out[a:b], ext_out[a:b], sat_out[a:b], ac_out[a:b],
                            zbi[a:b], viv[a:b], via[a:b], zbo[a:b], vov[a:b], voa[a:b], zm1[a:b], zm2[a:b],
                            opens_arr[a:b], highs_arr[a:b], lows_arr[a:b])

                phantom_train = phantom_arr[start_train:end_train]
                phantom_test = phantom_arr[start_test:end_test]

                cz['etapa'] = '2_ridge1'
                mat_train = extract_r_func(*S(start_train, end_train), phantom_train, PIPS_MULT, TRAIN_LEN, arm_in, chq_in, arm_out, chq_out, SPREAD_ACTIVO, *((True,) if LAB_T == 'V3' else ()))   # [LAB-V8] +3 columnas de Vida con NEXUS_LAB_T=V3
                df_ml = pd.DataFrame(mat_train, columns=COLS_X_ENTRADA + ['Profit_Pips', 'MAE_Pips', 'MFE_Pips', 'Velas_Vida', 'T_Terminal', 'Idx_Decision'] + (['V3_FET', 'V3_PFONDO', 'V3_VFONDO'] if LAB_T == 'V3' else []))
                if LAB_CENSO: cz.update(INF.datos_ml(df_ml))
                # [LAB-V8] Vida v3 extendida: constantes de la población IS (operaciones del extractor de entrada); la Cabeza B aprende V3 terminal
                V3P = None; H_VIDA = None
                if LAB_USA_VIDA:
                    try: H_VIDA = V7.escala_h(opens_arr[start_train:end_train], float(PIPS_MULT))   # h solo del IS (Close ≈ Open)
                    except ValueError as e_h: return desc(str(e_h))
                if LAB_T == 'V3':
                    V3P, _raw_pob, _apl_pob = VV.v3p_poblacion(df_ml['Profit_Pips'].values, df_ml['MFE_Pips'].values, df_ml['MAE_Pips'].values, df_ml['Velas_Vida'].values,
                                                                df_ml['V3_FET'].values, df_ml['V3_PFONDO'].values, df_ml['V3_VFONDO'].values, SPREAD_ACTIVO, H_VIDA, LAB_VIDA)
                    V3P = np.array([float(f"{v:.{DEC_W}f}") for v in V3P])   # precisión de export: el laboratorio usa lo mismo que leerán 4.5 y el EA
                    if not np.isfinite(V3P).all(): return desc("Vida_constantes_no_finitas")
                    df_ml['T_Terminal'] = VV.v3_terminal_poblacion(_raw_pob, _apl_pob, V3P)

                W_R, B_R, med_v, mad_v, atrac_t, msg = entrenar_modelo_ridge(df_ml)
                if W_R is None: return desc(f"Ridge_entrada:{msg}")
                if atrac_t <= 0 or mad_v <= 0: return desc("Parametros_Ridge_invalidos")

                if _GATE_T_ACTIVO:
                    W_T, B_T, T_min, r2_T, msg_T = entrenar_cabeza_T(df_ml)
                    if W_T is None: return desc(f"Cabeza_T:{msg_T}")
                    cz['r1_r2_T'] = float(r2_T); cz['r1_T_min'] = float(T_min)
                    if r2_T <= 0.0: return desc("Cabeza_T_sin_habilidad_OOF")
                else:
                    W_T = np.zeros(10, dtype=np.float64); B_T = 0.0; T_min = -1.0; r2_T = float('nan')

                # [LAB-V7] escala de v_req (Ridge de tamaño) y gemelo nulo
                cz.update(r1_med_v=float(med_v), r1_mad_v=float(mad_v), r1_atrac_t=float(atrac_t)); cz['etapa'] = '3_tamano'
                rng_lab = np.random.default_rng(zlib.crc32(f"{SIMBOLO}|{direccion_nombre}|{idx}".encode()))
                X10 = None
                if LAB_TAMANO == 'A':
                    X10 = np.column_stack([zbi, viv, via, lab_fase_nb(viv, zbi),
                                           zbo, vov, voa, lab_fase_nb(vov, zbo),
                                           zm1, zm2])[start_train:end_test].astype(np.float64)   # [LAB-V7 V0.3] sin(atan2) con tipos float32 como el kernel
                PAR_TAM = {}
                try:
                    ESC = lab_escala_v(LAB_TAMANO, LAB_NULO, rng_lab, N_velas, start_train, end_train, start_test, end_test, df_ml, ACT_ARR, X10, PAR_TAM)
                except ValueError as e_lab:
                    return desc(str(e_lab))

                def run_sim(a, b, phantom, activar_superv, W_S, B_S, K, _f=None):   # [LAB-V8] v3p al final solo con NEXUS_LAB_T=V3
                    return (_f or sim_superv_func)(*S(a, b), phantom, PIPS_MULT, b - a, arm_in, chq_in, arm_out, chq_out, SPREAD_ACTIVO,
                                           True, W_R, B_R, med_v, mad_v, atrac_t, umbral_z_ia,
                                           activar_superv, W_S, B_S, K, W_T, B_T, T_min, ESC[a:b], *((V3P,) if V3P is not None else ()))

                # [LAB-V7 V0.4] evaluador según NEXUS_LAB_METRICA (final = exactamente lo de main)
                dir_code_lab = 1 if direccion_nombre == 'LONG' else -1
                sim_ix_func = (simular_motor_long_superv_T_ix if dir_code_lab == 1 else simular_motor_short_superv_T_ix) if LAB_METRICA == 'v7' else None
                seed_lab = zlib.crc32(f"{SIMBOLO}|{direccion_nombre}|{idx}|v7".encode())

                def EVAL(a, b, phantom, activar_superv, W_S, B_S, K, min_tr):
                    if LAB_METRICA == 'v7':
                        tup = run_sim(a, b, phantom, activar_superv, W_S, B_S, K, sim_ix_func)
                        return lab_eval_v7(tup, dir_code_lab, opens_arr[a:b], highs_arr[a:b], lows_arr[a:b], PIPS_MULT, SPREAD_ACTIVO,
                                           1, 0.0, min_tr, min_tr, seed_lab)
                    mfe, mae, prof, tsc = run_sim(a, b, phantom, activar_superv, W_S, B_S, K)
                    r = eval_robustez_numba_v6(mfe, mae, prof, tsc, min_tr)
                    _e = {'sf': float(r[0]), 'v7': float('nan')}
                    if LAB_CENSO: _e['pips'] = float(np.sum(prof))   # [LAB-V8 informes]
                    return r, _e

                w0 = np.zeros(10, dtype=np.float64)

                cz['etapa'] = '4_base_is'
                r_is_base, _ex_b_is = EVAL(start_train, end_train, phantom_train, False, w0, 0.0, 1.0, MIN_OPS_IS_LAB)
                if LAB_CENSO: cz.update(INF.fila_r('is_base', r_is_base, _ex_b_is))
                if r_is_base[0] <= 0 or int(r_is_base[10]) < MIN_OPS_IS_LAB: return desc("IS_base_no_robusto")
                cz['etapa'] = '5_ridge2'

                x_traj, y_target, prof_snap, mae_snap, mfe_snap, tsc_snap, tid_snap, vela_snap = ext_traj_func(
                    *S(start_train, end_train), phantom_train, PIPS_MULT, TRAIN_LEN,
                    arm_in, chq_in, arm_out, chq_out, SPREAD_ACTIVO,
                    W_R, B_R, med_v, mad_v, atrac_t, umbral_z_ia, W_T, B_T, T_min, ESC[start_train:end_train], *((V3P,) if V3P is not None else ())
                )
                _VIDA = {}
                y_target = lab_target_cierre(LAB_CIERRE, y_target, tsc_snap, prof_snap, tid_snap, mfe_snap, mae_snap, vela_snap, SPREAD_ACTIVO, H_VIDA, _VIDA, V3P)   # [LAB-V7/V8] (T_terminal = main)
                _m = vela_snap > INMUNIDAD_VELAS_EFECTIVA
                if LAB_CIERRE in ('V3', 'dV3') and _VIDA and _m.sum() > 50:
                    _Y6 = np.column_stack([_VIDA['S_term'][_m], _VIDA['V3_term'][_m].astype(np.float64)])
                    _r2 = VV.r2_agrupado(x_traj[_m][:, :N_FEAT_SUPERV], _Y6, tid_snap[_m])
                    _ult, _ = VV._ultimas_fotos(tid_snap)
                    _cc = np.corrcoef(_VIDA['S'][_ult].T) if len(_ult) > 5 else np.eye(5)
                    _off = np.abs(_cc[~np.eye(5, dtype=bool)]); PAR_VIDA = {'r2': [float(v) for v in _r2], 'corr_max': float(np.nanmax(_off)) if _off.size else float('nan')}
                else: PAR_VIDA = {}
                if LAB_CENSO and PAR_VIDA: cz.update(INF.datos_vida(PAR_VIDA, VV.DESCRIPTORES))   # [LAB-V8 informes]
                x_traj = x_traj[_m]; y_target = y_target[_m]; tid_snap = tid_snap[_m]
                if len(x_traj) == 0: return desc("Trayectoria_vacia")
                if LAB_NULO: y_target = rng_lab.permutation(y_target)      # [LAB-V7] gemelo nulo de Ridge 2
                n_trades_train = int(np.unique(tid_snap).size)
                cz['r2_n_fotos'] = int(len(x_traj)); cz['r2_n_trades'] = n_trades_train

                W_S, B_S, msg_s = entrenar_modelo_supervivencia_ridge(x_traj, y_target, tid_snap, n_trades_train)
                if msg_s != "OK": return desc(f"Ridge_superv:{msg_s}")
                GRID_K = lab_grid_k(LAB_CIERRE, x_traj, W_S, B_S)   # [LAB-V7]
                del x_traj, y_target, prof_snap, mae_snap, mfe_snap, tsc_snap, tid_snap

                sim_is = lambda act, ws, bs, k: run_sim(start_train, end_train, phantom_train, act, ws, bs, k)
                if LAB_METRICA == 'v7':
                    K_opt, r_k_is, _ex_is = lab_escanear_k_v7(lambda act, k: run_sim(start_train, end_train, phantom_train, act, W_S, B_S, k, sim_ix_func),
                                                              GRID_K, dir_code_lab, opens_arr[start_train:end_train], highs_arr[start_train:end_train],
                                                              lows_arr[start_train:end_train], PIPS_MULT, SPREAD_ACTIVO, MIN_OPS_IS_LAB, seed_lab)
                else:
                    K_opt, r_k_is = escanear_umbral_k(sim_is, W_S, B_S, GRID_K, MIN_OPS_IS_LAB)
                    _ex_is = {'sf': float(r_k_is[0]) if K_opt is not None else float('nan'), 'v7': float('nan')}
                if K_opt is None: return desc("Escaneo_K_sin_score_positivo")
                score_k_is = float(r_k_is[0])
                if LAB_CENSO: cz['K_opt'] = float(K_opt); cz.update(INF.fila_r('is_sup', r_k_is, _ex_is))

                r_s_oos, _ex_s_oos = EVAL(start_test, end_test, phantom_test, True, W_S, B_S, K_opt, MIN_OPS_OOS_EXPORT)

                r_b_oos, _ex_b_oos = EVAL(start_test, end_test, phantom_test, False, w0, 0.0, 1.0, 3)
                cz['etapa'] = '6_compuerta_oos'
                if LAB_CENSO: cz.update(INF.fila_r('oos_sup', r_s_oos, _ex_s_oos)); cz.update(INF.fila_r('oos_base', r_b_oos, _ex_b_oos))

                score_s_is = score_k_is
                score_s_oos = float(r_s_oos[0])
                if score_s_is > 0 and score_s_oos > 0:
                    score_s_armonico = 2 * (score_s_is * score_s_oos) / (score_s_is + score_s_oos)
                else:
                    score_s_armonico = 0.0

                trades_superv = int(r_s_oos[10]); trades_base = int(r_b_oos[10])
                retencion_raw = math.sqrt(trades_superv / max(trades_base, 1))
                retencion = min(1.0, retencion_raw)
                score_flujo = score_s_armonico * retencion
                clave_rank = score_s_is if RANKEAR_SOLO_IS else score_flujo
                if LAB_CENSO:   # [LAB-V8 informes] una fila por candidato que llegó al OOS, pase o no la compuerta
                    _pasa = score_flujo > 0 and trades_superv >= MIN_OPS_OOS_EXPORT
                    cz.update(retencion_raw=float(retencion_raw), retencion=float(retencion), score_armonico=float(score_s_armonico), score_flujo=float(score_flujo), clave_rank=float(clave_rank))
                    INF.registrar(censo_local, cz, row_data, SIMBOLO, direccion_nombre, 'paso' if _pasa else 'descartado',
                                  None if _pasa else ("Compuerta_OOS_trades_insuficientes" if trades_superv < MIN_OPS_OOS_EXPORT else "Compuerta_OOS_score_no_positivo"))

                if score_flujo > 0 and trades_superv >= MIN_OPS_OOS_EXPORT:
                    return {
                        'row': row, 'TAM': PAR_TAM, 'VIDA': PAR_VIDA, 'V3P': V3P, 'W_R': W_R, 'B_R': B_R, 'med_v': med_v, 'mad_v': mad_v, 'atrac_t': atrac_t,
                        'W_S': W_S, 'B_S': B_S, 'K_opt': K_opt, 'ScoreK_IS': score_k_is,
                        'ClaveRank': clave_rank, '_cz': cz,
                        'ScoreFlujo': score_flujo, 'Retencion': retencion * 100, 'Retencion_Raw': retencion_raw * 100,
                        'ScoreIS': score_s_is, 'WR_IS': r_k_is[6], 'MaxDD_IS': r_k_is[8],
                        'Med_T_IS': r_k_is[12], 'Med_T_IS_Base': r_is_base[12], 'Med_T_OOS': r_s_oos[12],
                        'Ops_Ridge': trades_base, 'Ops_Superv': trades_superv, 'Base_Rechazado': bool(_ex_b_oos['sf'] <= 0.0), 'EX': {'sf_is': _ex_is['sf'], 'v7_is': _ex_is['v7'], 'sf_oos': _ex_s_oos['sf'], 'v7_oos': _ex_s_oos['v7']},
                        'WR_Ridge': r_b_oos[6], 'WR_Superv': r_s_oos[6], 'MaxDD_Ridge': r_b_oos[8], 'MaxDD_Superv': r_s_oos[8],
                        'PF_Ridge': r_b_oos[7], 'PF_Superv': r_s_oos[7],
                        'MedProfitPips_Ridge': r_b_oos[3], 'MedProfitPips_Superv': r_s_oos[3],
                        'score_oos': score_s_oos, 'fold': fold + 1,
                        'T_min': T_min, 'r2_T': r2_T, 'W_T': W_T, 'B_T': B_T, 'n_trades_train': n_trades_train, 'n_is_base': int(r_is_base[10]), 'n_is_superv': int(r_k_is[10])
                    }
                _registrar_descarte(SIMBOLO, direccion_nombre, "Compuerta_OOS_no_superada")
                _registrar_descarte(SIMBOLO, direccion_nombre, "Compuerta_OOS_trades_insuficientes" if trades_superv < MIN_OPS_OOS_EXPORT else "Compuerta_OOS_score_no_positivo")
                return {'_gate_fail': True, 'score_oos': score_s_oos, 'fold': fold + 1}
            except Exception as e:
                return desc(f"Excepcion_calculo:{type(e).__name__}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
            lista_diccionarios_planos = top_n.to_dict('records')
            lista_jobs = [(i, fila) for i, fila in enumerate(lista_diccionarios_planos)]
            resultados = list(executor.map(procesar_candidato, lista_jobs))

        candidatos_validos = [r for r in resultados if r is not None and not r.get('_gate_fail')]
        candidatos_validos.sort(key=lambda x: x['ClaveRank'], reverse=True)

        stats = {}
        for f in range(1, N_FOLDS + 1):
            ev = [r for r in resultados if r is not None and r['fold'] == f]
            stats[f] = {'n_eval': len(ev), 'n_ok': sum(1 for r in ev if not r.get('_gate_fail')),
                        'med_score_oos': float(np.median([r['score_oos'] for r in ev])) if ev else 0.0}
        return candidatos_validos, stats

    print(f"   ↳ 🟢 Threading Test {FASE4_VERSION} SUPERVIVENCIA CONTINUA: LONG (Top {TOP_CANDIDATOS})...")
    campeones_L, stats_L = ejecutar_torneo(df_long, 'LONG', extractor_ml_long, extractor_trayectoria_long_v2, simular_motor_long_superv_T, Z_SCORE_MINIMO_LONG)
    print(f"   ↳ 🔴 Threading Test {FASE4_VERSION} SUPERVIVENCIA CONTINUA: SHORT (Top {TOP_CANDIDATOS})...")
    campeones_S, stats_S = ejecutar_torneo(df_short, 'SHORT', extractor_ml_short, extractor_trayectoria_short_v2, simular_motor_short_superv_T, Z_SCORE_MINIMO_SHORT)

    for _d, _st in (('LONG', stats_L), ('SHORT', stats_S)):
        for f, s in _st.items():
            if s['n_eval']:
                print(f"      📉 [H-10] {_d} Fold {f}: compuerta OOS {s['n_ok']}/{s['n_eval']} ({100.0 * s['n_ok'] / s['n_eval']:.1f}%) | mediana score OOS (todos) = {s['med_score_oos']:.2f}")

    if LAB_CENSO:   # [LAB-V8 informes] censo y vista del símbolo (se escriben aunque no haya campeones)
        try:
            _exporta = bool(campeones_L and campeones_S)
            for _camp in (campeones_L, campeones_S):
                for _i, _c in enumerate(_camp): _c['_cz']['_fila'].update(rank_ia=_i + 1, en_cerebro=bool(_exporta and _i < EXPORTAR_MQL5_TOP))
            _sal = INF.escribir_censo(SIMBOLO, TAG_ARCHIVOS, censo_local, TAB.sello(N_total), LAB_VISTA_TOP,
                                      {'LONG': (len(df_long), min(len(df_long), TOP_CANDIDATOS)), 'SHORT': (len(df_short), min(len(df_short), TOP_CANDIDATOS))})
            _cortes = {f'fold{_f}_{_n}': _v for _f, _t in GEOM['folds'].items() for _n, _v in zip(('is_ini', 'is_fin', 'oos_ini', 'oos_fin'), _t)}
            if GEOM['reserva']: _cortes.update(reserva_ini=GEOM['reserva'][0], reserva_fin=GEOM['reserva'][1] - 1)
            _manif_simbolos[SIMBOLO] = {'n_total': int(N_total), 'n_efectivo': int(N_velas), 'cortes_indice': {k: int(v) for k, v in _cortes.items()},
                                        'cortes_fecha': INF.fechas_parquet(archivo_parquet, _cortes), 'spread': float(SPREAD_ACTIVO), 'exporta': _exporta,
                                        'parquet': {'archivo': archivo_parquet, 'bytes': os.path.getsize(archivo_parquet)},
                                        'csv_fase3': {'archivo': nombre_csv, 'sha1': INF.sha1_archivo(nombre_csv), 'filas': int(len(df_opt)),
                                                      'busq_hash': (str(df_opt['Busq_Hash'].iloc[0]) if 'Busq_Hash' in df_opt.columns and len(df_opt) else None)},
                                        'censo_filas': (_sal[2] if _sal else 0), 'campeones': {'LONG': len(campeones_L), 'SHORT': len(campeones_S)}}
            if _sal: print(f"   🧾 [INFORMES] {_sal[0]} ({_sal[2]} filas) y {_sal[1]}")
        except Exception as _e_inf:   # los informes nunca cortan la corrida: el fallo se cuenta y se muestra
            INF.anotar_error('censo_simbolo', _e_inf); print(f"   ⚠️ [INFORMES] fallo en censo_simbolo: {type(_e_inf).__name__}: {_e_inf}")
    if not campeones_L or not campeones_S:
        print(f"   ⚠️ [{SIMBOLO}] Sin campeones en ambas direcciones (L={len(campeones_L)}, S={len(campeones_S)}). "
              f"No se escribe ningún artefacto; los exports previos permanecen intactos.")
        del ARR; gc.collect()
        return 'sin_campeones'

    print(f"\n      🏆 TABLERO {FASE4_VERSION}: SCORE MATRIZ SUPERVIVENCIA CONTINUA MULTIPLEX- {SIMBOLO} (orden: {'IS-ONLY' if RANKEAR_SOLO_IS else 'FLUJO'})")
    print(f"      {'RANK':<5} | {'DIR':<5} | {'FOLD':<5} | {'K_ABORTAR':<10} | {'RETENCION':<10} | {'SEL_IS':<8} | {'🏆 FLUJO':<10} | {'🏅 C.I.E (T-SCORE IS ➔ OOS)':<30} ")
    print("      " + "-" * 118)

    for dir_nombre, campeones, stats in (('LONG', campeones_L, stats_L), ('SHORT', campeones_S, stats_S)):
        for idx, c in enumerate(campeones):
            if idx < IMPRIMIR_CONSOLA_TOP:
                print(f"      {idx+1:<5} | {dir_nombre:<5} | {int(c['row']['Fold']):<5} | {c['K_opt']:<10.2f} | {c['Retencion']:<9.1f}% | {c['ClaveRank']:<8.2f} | {c['ScoreFlujo']:<10.1f} | 🏅 {c['Med_T_IS']:<5.2f}  ➔  {c['Med_T_OOS']:<5.2f}")
            reporte_torneo_local.append(_fila_reporte(SIMBOLO, dir_nombre, idx, c, stats[int(c['row']['Fold'])]))

    archivo_mql5_simbolo = f"Cerebro_MQL5_{TAG_ARCHIVOS}_{SIMBOLO}.txt"
    partes_txt = [
        "// =====================================================================\n",
        f"// CÓDIGO AUTOGENERADO {FASE4_VERSION} — MOTOR DE SUPERVIVENCIA CONTINUA ({SIMBOLO})\n",
        f"// nexus_formulas_core version: {FORMULAS_CORE_VERSION}\n",
        f"// Fase_4 build: {FASE4_VERSION} | Ridge supervivencia: sample_weight=None (1 snapshot = 1 dato unitario)\n",
        f"// {TAB.sello_linea(N_total)}\n",
        f"// ESCALON={ESCALON} | INMUNIDAD_VELAS={INMUNIDAD_VELAS_EFECTIVA} | compuerta T={_GATE_T_ACTIVO} (q={Q_ADMISION_T}) | features superv={N_FEAT_SUPERV} => COMPATIBLE CON EA V12.01+\n",
        f"// FID_VELOCIDAD_UNIFICADA = {FID_VELOCIDAD_UNIFICADA}  (True => EA calcula V_cruda con envolvente MFE/MAE y costo trx)\n",
        "// Pesos/bias/mad/mediana/atrac_t/armado/chasquido/spread redondeados a la precisión de export ANTES de simular.\n",
        "// =====================================================================\n\n",
        f"    else if(sym == \"{SIMBOLO}\") {{\n",
        f"      g_pares[idx].spread_asumido_ia = {SPREAD_ACTIVO:.{DEC_SPREAD}f};\n\n",
    ]
    for export_idx in range(min(EXPORTAR_MQL5_TOP, len(campeones_L))):
        partes_txt.append(_bloque_mql5(campeones_L[export_idx], export_idx, 'LONG', 'toro', 'ml_toro', 'superv_toro', '🟢', Z_SCORE_MINIMO_LONG))
    for export_idx in range(min(EXPORTAR_MQL5_TOP, len(campeones_S))):
        partes_txt.append(_bloque_mql5(campeones_S[export_idx], export_idx, 'SHORT', 'oso', 'ml_oso', 'superv_oso', '🔴', Z_SCORE_MINIMO_SHORT))
    partes_txt.append("\n      g_pares[idx].cfg.configurado = true;\n    }\n")

    df_torneo = pd.DataFrame(reporte_torneo_local)
    df_torneo = df_torneo.sort_values(by=['Simbolo', 'Dir', 'Fold', 'Rank_IA'], ascending=[True, True, True, True])
    for _k, _v in TAB.sello(N_total).items(): df_torneo[_k] = _v   
    archivo_reporte_simbolo = f"Reporte_OOS_Phase4_{TAG_ARCHIVOS}_Superv_{SIMBOLO}.csv"

    _escritura_atomica(archivo_mql5_simbolo, "".join(partes_txt))
    _escritura_atomica(archivo_reporte_simbolo, df_torneo, es_df=True)
    print(f"   💾 Phase 4 {FASE4_VERSION} Guardado (atómico por archivo). Master-Export Bridge Supervivencia Continua a MT5 Finalizado Exitosamente.")

    del ARR; gc.collect()
    return 'ok'

# ==========================================================
# 🚀 MAIN
# ==========================================================
def main():
    set_num_threads(1)
    if _TPL_OK:
        threadpool_limits(limits=1)   

    print(f"🚀 Iniciando PIPELINE MLOPS {FASE4_VERSION} — MOTOR DE SUPERVIVENCIA CONTINUA (SELLO INSTITUCIONAL W.F.O)...")
    print(f"⚡ Enjambre Local Thread-Pool: hasta {MAX_VCPUS} Workers (autocalibrados por RAM en cada símbolo).")
    print(f"🧮 nexus_formulas_core v{FORMULAS_CORE_VERSION} | Fid velocidad unificada: {FID_VELOCIDAD_UNIFICADA}")
    print(f"🧪 ESCALÓN {ESCALON} | inmunidad>{INMUNIDAD_VELAS_EFECTIVA} velas | compuerta T: {_GATE_T_ACTIVO} (q={Q_ADMISION_T}) | features Ridge2: {N_FEAT_SUPERV} | tag salida: {TAG_ARCHIVOS}")
    if LAB_ACTIVO: print(f"🧪 [LAB-V7] tamano={LAB_TAMANO} cierre={LAB_CIERRE} nulo={LAB_NULO} | NO exportable al EA (sin paridad M7)")
    if not _TPL_OK:
        print("⚠️ threadpoolctl no disponible: BLAS puede sobresuscribir CPU.")

    _warmup_jit()

    for SIMBOLO in LISTA_SIMBOLOS:
        estado = procesar_simbolo(SIMBOLO)
        if estado == 'ok': _cobertura['ok'] += 1
        else: _cobertura[estado].append(SIMBOLO)
        gc.collect()

    print("\n" + "=" * 80)
    print(f"📊 [COBERTURA {FASE4_VERSION}] Símbolos procesados con éxito: {_cobertura['ok']}/{len(LISTA_SIMBOLOS)} | "
          f"Sin CSV: {len(_cobertura['sin_csv'])} | Sin Parquet: {len(_cobertura['sin_parquet'])} | "
          f"Sin campeones: {len(_cobertura['sin_campeones'])} | Sin phantom: {len(_cobertura['sin_phantom'])} | CSV inválido: {len(_cobertura['csv_invalido'])}")
    for k, etq in (('sin_csv', 'Sin CSV'), ('sin_parquet', 'Sin Parquet'), ('sin_campeones', 'Sin campeones'), ('sin_phantom', 'Sin phantom'), ('csv_invalido', 'CSV inválido')):
        if _cobertura[k]: print(f"   ↳ {etq}: {_cobertura[k]}")
    if _fallbacks_ridge['entrada'] or _fallbacks_ridge['superv']:
        print(f"   ⚠️ Fallbacks Ridge(alpha=1.0): entrada={_fallbacks_ridge['entrada']} | superv={_fallbacks_ridge['superv']} (RidgeCV falló)")
    print("=" * 80)

    if _descartes:
        print("\n" + "=" * 80)
        print("🔬 [FORENSE] Candidatos descartados por causa (símbolo|dirección|causa):")
        for clave, cnt in sorted(_descartes.items(), key=lambda x: -x[1]):
            print(f"   - {clave}: {cnt}")
        print("=" * 80)

    if LAB_CENSO:   # [LAB-V8 informes] resumen (desde los censos del disco) y manifiesto de la corrida
        try:
            import glob as _glob, datetime as _dt
            _res = INF.resumen(TAG_ARCHIVOS)
            _sals = [{'archivo': a} for pat in (f'Cerebro_MQL5_{TAG_ARCHIVOS}_*.txt', f'Reporte_OOS_Phase4_{TAG_ARCHIVOS}_Superv_*.csv', f'Censo_Fase4_{TAG_ARCHIVOS}_*.csv',
                                                  f'Vista_Fase4_{TAG_ARCHIVOS}_*.csv', f'Resumen_Fase4_{TAG_ARCHIVOS}.md') for a in sorted(_glob.glob(pat))
                     if any(a.endswith(f'_{s}.txt') or a.endswith(f'_{s}.csv') for s in _manif_simbolos) or a.endswith('.md')]
            _man = INF.manifiesto(TAG_ARCHIVOS, {
                'inicio': _T_INICIO.isoformat(timespec='seconds'), 'fin': _dt.datetime.now().isoformat(timespec='seconds'),
                'fase4_version': FASE4_VERSION, 'core_version': FORMULAS_CORE_VERSION, 'tag': TAG_ARCHIVOS,
                'tablero_lab': {k: v for k, v in sorted(os.environ.items()) if k.startswith('NEXUS_LAB_')},
                'tablero_geometria': {'version': TAB.TABLERO_VERSION, 'hash': TAB.hash_params(), 'N_FOLDS': TAB.N_FOLDS, 'RATIO_TRAIN_TEST': TAB.RATIO_TRAIN_TEST,
                                      'RESERVA_FINAL': TAB.RESERVA_FINAL, 'MEMORIA_FIFO': TAB.MEMORIA_FIFO},
                'constantes': {'ESCALON': ESCALON, 'TOP_CANDIDATOS': TOP_CANDIDATOS, 'EXPORTAR_MQL5_TOP': EXPORTAR_MQL5_TOP, 'MIN_OPS_OOS_EXPORT': MIN_OPS_OOS_EXPORT,
                               'MIN_OPS_IS_LAB': MIN_OPS_IS_LAB, 'RANKEAR_SOLO_IS': RANKEAR_SOLO_IS, 'Q_ADMISION_T': Q_ADMISION_T, 'INMUNIDAD_VELAS': INMUNIDAD_VELAS_EFECTIVA,
                               'N_FEAT_SUPERV': N_FEAT_SUPERV, 'Z_MIN_LONG': Z_SCORE_MINIMO_LONG, 'Z_MIN_SHORT': Z_SCORE_MINIMO_SHORT, 'VISTA_TOP': LAB_VISTA_TOP,
                               'LAB_V7_R': LAB_V7_R, 'LAB_V7_OPCION': LAB_V7_OPCION},
                'simbolos_pedidos': list(LISTA_SIMBOLOS), 'simbolos': _manif_simbolos,
                'cobertura': {k: (v if isinstance(v, int) else list(v)) for k, v in _cobertura.items()}, 'descartes': dict(_descartes),
                'fallbacks_ridge': dict(_fallbacks_ridge), 'salidas': _sals})
            print(f"🧾 [INFORMES] {_res} | {_man}")
        except Exception as _e_inf:   # los informes nunca cortan la corrida: el fallo se cuenta y se muestra
            INF.anotar_error('resumen_manifiesto', _e_inf); print(f"   ⚠️ [INFORMES] fallo en resumen_manifiesto: {type(_e_inf).__name__}: {_e_inf}")
    if _cobertura['ok'] == 0:
        raise RuntimeError(
            f"🛑 FATAL [Auditoría F4-08]: CERO símbolos de {len(LISTA_SIMBOLOS)} fueron procesados con éxito en esta corrida. "
            f"Sin CSV: {len(_cobertura['sin_csv'])} | Sin Parquet: {len(_cobertura['sin_parquet'])} | Sin campeones: {len(_cobertura['sin_campeones'])} | "
            f"Sin phantom: {len(_cobertura['sin_phantom'])} | CSV inválido: {len(_cobertura['csv_invalido'])}. "
            f"Verificar PATRON_CSV_FASE3 contra la salida real de Fase_3.py y la presencia de los .parquet de Fase 1&2."
        )

    print("\n" + "=" * 80)
    print(f"🎉 CÓDIGO MATRIX FASE 4 {FASE4_VERSION} (MOTOR DE SUPERVIVENCIA CONTINUA) COMPLETADO.")
    print("✅ COMPATIBILIDAD DE SILICIO: Generador _bloque_mql5 totalmente alineado con EA_Dual_V12_01.mq5 (Superset E0..E3).")
    print(f"✅ Build {FASE4_VERSION}: Ridge de Supervivencia con sample_weight=None (1 snapshot = 1 dato unitario, decisión CRO).")
    print("=" * 80)

if __name__ == "__main__":
    main()