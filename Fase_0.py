# ==============================================================================
# 🗄️ FASE 0: EXPLORACIÓN, SUTURA QUIRÚRGICA Y CONVERSIÓN A PARQUET
# 🛡️ CAPA BRONCE A CAPA PLATA: Cero Data-Leakage y Downcasting
# ==============================================================================
# 📋 BITÁCORA DE CONSOLIDACIÓN (Auditoría NEXUS V3.0):
#    - RUTA_CSV fijada a valor PRODUCTIVO confirmado por CRO: 24 meses.
#    - [C3] Path absoluto neutralizado. Ruta parametrizada en formato relativo.
#    - Hallazgo "vela fantasma" en AMPLITUD (High/Low, MAE/MFE): RETRACTADO.
#    - [M1] Hallazgo "vela fantasma" en TIEMPO (dilución de Theta/FET/v_ef/atrac_t):
#      RESUELTO. Implementado aplanamiento geométrico (O=H=L=C=Prev_Close),
#      congelación volumétrica y vectorización explícita de máscara _phantom
#      para propagación asíncrona hacia las Fases 1, 2, 3 y 4.
# ==============================================================================
# 📋 BITÁCORA DE CONSOLIDACIÓN V3.1 (Auditoría NEXUS — Ronda Fase 0):
#    - [CERRADO] Invalidación de Parquet por staleness (mtime/hash vs CSV origen).
#    - [CERRADO] Escritura no-transaccional del Parquet final (patrón .tmp).
#    - [CERRADO] dropna() con atribución forense por símbolo/columna.
#      ⚠️ NOTA V3.2: esta declaración de "CERRADO" resultó PARCIALMENTE
#      INEXACTA — ver hallazgo T2-H3 abajo. El código real sólo medía el
#      estado PRE-ffill (diagnóstico preliminar), no lo que efectivamente
#      se amputaba en el corte final. Corregido en V3.2.
#    - [CERRADO] Post-condición de integridad tras dropna (assert explícito).
# ==============================================================================
# 📋 BITÁCORA DE CONSOLIDACIÓN V3.2 (Auditoría NEXUS — Turno 2/8):
#    - [T2-H1 CERRADO] Fatal Error explícito (ya NO skip silencioso) si un
#      cierre no encuentra sus 3 homólogos Open/High/Low. Antes, un símbolo
#      con convención de nombres rota simplemente no generaba su columna
#      '_phantom', y Fase 1&2 asumía silenciosamente "cero fricción de gaps"
#      para ese símbolo. Ley Zero-Hallucination: ahora se aborta con detalle
#      forense de qué homólogo falta por símbolo.
#    - [T2-H2 CERRADO] Umbral mínimo de retención post-dropna
#      (UMBRAL_RETENCION_MINIMA, default 90%) — antes sólo se validaba
#      `len(df_full) > 0`, lo que no detectaba una amputación masiva pero
#      no total (ej. 85% del dataset perdido por un símbolo con histórico
#      corto). Configurable si la causa está documentada y es legítima.
#    - [T2-H3 CERRADO] Atribución forense REAL del dropna final: se mide el
#      estado de NaN inmediatamente ANTES del corte que efectivamente se
#      ejecuta (post-ffill, pre-dropna), no sólo el estado pre-ffill que
#      sólo sirve de diagnóstico preliminar y no refleja qué se amputa.
#    - [T2-Patrón CERRADO] Detección de homólogos OHLC migrada de substring
#      laxo ('close' in c.lower()) a comparación exacta por sufijo
#      (c.endswith('_Close')) + reconstrucción determinística del
#      base_name — elimina la fragilidad de matching cross-módulo también
#      señalada en Fase 1&2 (mismo patrón de riesgo, dos módulos).
#    - [T1↔T2 CERRADO] Si existe manifest forense de extracción
#      (.manifest.json, emitido por extractor_mt5_pc_local.py V3.1), se
#      carga y se listan explícitamente los símbolos que llegaron con
#      extracción parcial — permite al operador distinguir defecto de
#      extracción de gap legítimo de mercado antes de que ambos se
#      disuelvan indiferenciados dentro de la máscara '_phantom'.
# ==============================================================================
# ==============================================================================
# 📋 BITÁCORA DE CONSOLIDACIÓN V3.3 (Auditoría NEXUS — Bloque Fase 0→1→2):
#    - [N6-A1 CERRADO] Se elimina el `except Exception` genérico que dejaba terminar
#      el script "sin error" (y sin Parquet nuevo) ante AssertionError, fallo de
#      lectura/escritura o MemoryError. Los `assert` pasan a RuntimeError explícito.
#      FileNotFoundError conserva su mensaje amigable y se relanza.
#    - [N6-M1 CERRADO] El Parquet lleva un SELLO en sus metadatos ('nexus_fase0':
#      versión, CSV origen nombre/bytes/mtime, zona horaria, rango, filas, retención,
#      % fantasmas por símbolo). La frescura ahora exige sello de versión + mtime.
#      ⚠️ CORRECCIÓN a la bitácora V3.1: la invalidación NUNCA fue por hash (sólo mtime).
#      Regla: subir FASE0_VERSION ante cualquier cambio de lógica.
#    - [N6-M2 CERRADO] Reloj validado (`_preparar_reloj`): la columna temporal existe y
#      NO es numérica, sin NaT, rango plausible, orden cronológico (avisa si reordena),
#      sin duplicados, cadencia M1. Índice siempre llamado 'time'. La zona horaria no se
#      convierte: se registra (decisión: validar, no transformar).
#    - [N6-M3 CERRADO] Fantasma = falta CUALQUIERA de O/H/L/C (antes sólo Open). En
#      datos limpios es idéntico; las barras parciales se aplanan y se reportan.
#    - [N6-M4 CERRADO] % de filas fantasma por símbolo, impreso y sellado.
#    - [NUEVO] Calidad de precios sobre el dataset final: OHLC finito y > 0 (fatal) y
#      coherencia de barras reales (umbral UMBRAL_OHLC_INCOHERENTE).
#    - [N6-B1 CERRADO] Preview sólo en la rama de regeneración (la rama "CSV ausente" era
#      inalcanzable), mask_nan liberado, .tmp huérfano eliminado si falla la escritura.
# ==============================================================================
# 📋 BITÁCORA V3.4 (Auditoría NEXUS — parches H-01 y H-02, LUZ VERDE del CRO):
#    - [H-01] La frescura del Parquet ahora verifica IDENTIDAD del CSV: nombre, bytes y
#      mtime sellados deben coincidir con el CSV actual (antes se guardaban y no se
#      comparaban). Un CSV nuevo renombrado a RUTA_CSV ya no reutiliza un Parquet viejo.
#      ⚠️ Cubre además el núcleo de H-03 (bytes/mtime sellados); H-03 sigue registrado
#      hasta verificación del CRO. Contrato de nombre: el extractor V3.3 publica el alias.
#    - [H-02] Si el manifest del extractor marca símbolos con cobertura parcial y
#      ABORTAR_SI_EXTRACCION_PARCIAL=True, Fase 0 aborta (RuntimeError). Antes sólo
#      imprimía. `except Exception` del lector de manifest acotado a (OSError, ValueError)
#      para que el abort no sea tragado como "manifest ilegible".
# ==============================================================================
import pandas as pd
import numpy as np
import os
import gc
import json
import pyarrow as pa
import pyarrow.parquet as pq

# 🛡️ [N6-M1] Subir ANTE CUALQUIER cambio de lógica de esta fase: un Parquet con
# otra versión sellada se considera obsoleto y se regenera (ver _parquet_esta_actualizado).
FASE0_VERSION = "V3.4"

# 🔧 CONSOLIDADO: Valor productivo confirmado (24 meses).
# Ruta RELATIVA al CWD. Resuelve C3 (Ruptura Absoluta /).
RUTA_CSV = 'nexus_matrix_ohlc_m1_24m.csv.gz'
RUTA_PARQUET = RUTA_CSV.replace('.csv.gz', '.parquet')

# 🛡️ [FIX T2-H2] Umbral mínimo de retención post-dropna. Por debajo de esto
# se considera degradación estructural del dataset, no fricción de mercado
# determinista (Axioma Cero), y el pipeline aborta en lugar de persistir
# un Parquet silenciosamente mutilado.
UMBRAL_RETENCION_MINIMA = 0.90

# 🛡️ [V3.3] Controles de calidad de datos (configurables, documentar si se relajan).
MAX_TIMESTAMPS_DUPLICADOS = 0      # Un reloj con timestamps repetidos rompe "N filas atrás"
UMBRAL_OHLC_INCOHERENTE = 0.001    # Fracción máx. de barras REALES con High<Low, High<max(O,C) o Low>min(O,C)
# 🛡️ [V3.4 H-02] True: extracción parcial declarada por el manifest => abortar. False sólo explícito y temporal.
ABORTAR_SI_EXTRACCION_PARCIAL = True


def _leer_meta_fase0(ruta_parquet):
    """Sello forense 'nexus_fase0' guardado en los metadatos del Parquet (None si no existe)."""
    try:
        meta = pq.read_schema(ruta_parquet).metadata or {}
        return json.loads(meta[b'nexus_fase0'].decode('utf-8'))
    except Exception:
        return None


def _parquet_esta_actualizado(ruta_csv, ruta_parquet):
    """
    Parquet válido SÓLO si existe, su sello de versión coincide con FASE0_VERSION
    y su mtime es posterior al del CSV origen (os.stat, O(1)). [V3.3] Antes sólo
    se comparaba mtime (la bitácora V3.1 decía "mtime/hash": el hash nunca existió).
    Con CSV ausente no hay forma de regenerar: se acepta el Parquet y se avisa.
    """
    if not os.path.exists(ruta_parquet):
        return False
    meta = _leer_meta_fase0(ruta_parquet)
    version_ok = (meta is not None and meta.get('version') == FASE0_VERSION)
    if not os.path.exists(ruta_csv):
        if not version_ok:
            print("   [⚠️  V3.3] CSV origen ausente y el Parquet no trae sello de esta versión "
                  f"({FASE0_VERSION}); no se puede regenerar. Se usa tal cual.")
        return True
    if not version_ok:
        print(f"   [ℹ️  V3.3] Parquet sin sello de {FASE0_VERSION} (o de otra versión): se regenera.")
        return False
    # 🛡️ [V3.4 H-01] Identidad del CSV: nombre + bytes + mtime sellados vs. CSV actual.
    csv_sellado = (meta or {}).get('csv', {})
    if (csv_sellado.get('nombre') != os.path.basename(ruta_csv)
            or csv_sellado.get('bytes') != os.path.getsize(ruta_csv)
            or csv_sellado.get('mtime') != os.path.getmtime(ruta_csv)):
        print("   [ℹ️  V3.4] El CSV actual difiere del sellado en el Parquet (nombre/bytes/mtime): se regenera.")
        return False
    return os.path.getmtime(ruta_parquet) >= os.path.getmtime(ruta_csv)


def _cargar_manifest_extraccion(ruta_csv):
    """
    🛡️ [FIX T1↔T2] Best-effort: si el extractor (Turno 1, V3.1+) dejó un
    manifest forense junto al CSV, se carga para cruzar símbolos con
    extracción parcial. Si no existe (CSV generado por una versión anterior
    del extractor, o cargado manualmente), se declara explícitamente la
    ausencia — no se asume nada sobre la integridad de origen por omisión.
    """
    ruta_manifest = ruta_csv + ".manifest.json"
    if not os.path.exists(ruta_manifest):
        print("   [ℹ️  T1↔T2] Sin manifest de extracción disponible junto al CSV. "
              "No es posible distinguir aquí defecto-de-extracción de gap-de-mercado "
              "legítimo (reserva registrada en auditoría Turno 1 — el CSV probablemente "
              "proviene de una versión previa del extractor).")
        return None
    try:
        with open(ruta_manifest, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        simbolos_parciales = [
            s for s, info in manifest.get("pares", {}).items()
            if not info.get("completo", True)
        ]
        if simbolos_parciales:
            print(f"   [⚠️  T1↔T2] Manifest de extracción indica {len(simbolos_parciales)} "
                  f"símbolo(s) con extracción PARCIAL (corte prematuro de descarga, NO gap "
                  f"de mercado legítimo): {simbolos_parciales}")
            if ABORTAR_SI_EXTRACCION_PARCIAL:
                raise RuntimeError(
                    f"🛑 FATAL [H-02]: el manifest declara extracción parcial en {simbolos_parciales}. "
                    f"Re-extraer con un rango que el broker cubra, o poner ABORTAR_SI_EXTRACCION_PARCIAL=False "
                    f"(explícito y temporal) si la causa está documentada.")
        else:
            print("   [✅ T1↔T2] Manifest de extracción confirma: todos los símbolos "
                  "completaron su descarga en su totalidad.")
        return manifest
    except (OSError, ValueError) as e:
        print(f"   [⚠️  T1↔T2] Manifest presente pero ilegible ({e}). Se ignora sin bloquear el pipeline.")
        return None


def _preparar_reloj(df):
    """
    🛡️ [V3.3 N6-M2] Construye el índice temporal 'time' VALIDANDO que la columna exista y
    sea realmente una fecha (un precio convertido con to_datetime daría 1970 sin error).
    Comprueba: columna temporal no numérica, sin NaT, rango plausible, orden cronológico
    (avisa si hubo que reordenar), sin duplicados y cadencia M1 (paso mediano = 1 min).
    La zona horaria NO se convierte: se registra en el sello (naive o la declarada por el CSV).
    """
    col = 'time' if 'time' in df.columns else df.columns[0]
    if pd.api.types.is_numeric_dtype(df[col]):
        raise RuntimeError(f"🛑 FATAL [Reloj]: la columna de tiempo '{col}' es numérica; no se "
                           f"interpreta un precio como fecha. Revisar que el CSV traiga la fecha primero.")
    t = pd.to_datetime(df[col], errors='coerce')
    if not pd.api.types.is_datetime64_any_dtype(t):
        raise RuntimeError(f"🛑 FATAL [Reloj]: '{col}' no se pudo convertir a un tipo fecha uniforme "
                           f"(¿zonas horarias mezcladas en el CSV?).")
    n_nat = int(t.isna().sum())
    if n_nat > 0:
        raise RuntimeError(f"🛑 FATAL [Reloj]: {n_nat} valor(es) de '{col}' no son una fecha válida.")
    tz = t.dt.tz
    t_cmp = t.dt.tz_localize(None) if tz is not None else t
    if t_cmp.min() < pd.Timestamp('2000-01-01') or t_cmp.max() > pd.Timestamp.now() + pd.Timedelta(days=2):
        raise RuntimeError(f"🛑 FATAL [Reloj]: rango de fechas implausible ({t.min()} → {t.max()}).")

    df = df.drop(columns=[col])
    df.index = pd.DatetimeIndex(t)
    df.index.name = 'time'

    if not df.index.is_monotonic_increasing:
        print("   [⚠️  V3.3] El CSV venía desordenado cronológicamente: se reordena (posible defecto de extracción).")
        df = df.sort_index()
    n_dup = int(df.index.duplicated().sum())
    if n_dup > MAX_TIMESTAMPS_DUPLICADOS:
        raise RuntimeError(f"🛑 FATAL [Reloj]: {n_dup} timestamps duplicados (máx. permitido: "
                           f"{MAX_TIMESTAMPS_DUPLICADOS}). Depurar el CSV origen.")
    paso = df.index.to_series().diff().dropna()
    if paso.median() != pd.Timedelta(minutes=1):
        raise RuntimeError(f"🛑 FATAL [Reloj]: el paso mediano es {paso.median()}, no 1 minuto: "
                           f"el CSV no parece ser M1.")

    zona = str(tz) if tz is not None else "naive (sin zona declarada en el CSV)"
    print(f"   [🕒 RELOJ] Columna '{col}' → índice 'time' | {len(df)} filas | {df.index[0]} → {df.index[-1]} | zona: {zona}")
    print("   [🕒 RELOJ] Mayores huecos (fines de semana/feriados esperados; otros = posible hueco de extracción): "
          + " | ".join(f"hasta {ts} (+{g})" for ts, g in paso.nlargest(3).items()))
    return df, {'tz': zona, 't_inicio': str(df.index[0]), 't_fin': str(df.index[-1])}


def _validar_ohlc(df, bases):
    """
    🛡️ [V3.3] Calidad de precios sobre el dataset FINAL (pre-downcast): todo OHLC finito y > 0
    (error fatal si no) y coherencia de barras REALES (los fantasmas son planas por construcción).
    Aborta si la fracción incoherente supera UMBRAL_OHLC_INCOHERENTE; si no, la reporta.
    """
    total_reales, malas_por_simbolo = 0, {}
    for b in bases:
        o, h, l, c = (df[f'{b}_{x}'].values for x in ('Open', 'High', 'Low', 'Close'))
        for nombre, arr in (('Open', o), ('High', h), ('Low', l), ('Close', c)):
            if not np.isfinite(arr).all() or (arr <= 0).any():
                raise RuntimeError(f"🛑 FATAL [Datos]: {b}_{nombre} contiene precios no finitos o <= 0.")
        reales = df[f'{b}_phantom'].values == 0
        malas = reales & ((h < l) | (h < np.maximum(o, c)) | (l > np.minimum(o, c)))
        total_reales += int(reales.sum())
        if malas.any():
            malas_por_simbolo[b] = int(malas.sum())
    total_malas = sum(malas_por_simbolo.values())
    frac = total_malas / max(total_reales, 1)
    if total_malas:
        print(f"   [⚠️  V3.3] Barras reales con OHLC incoherente: {total_malas} ({frac*100:.4f}%). Por símbolo: {malas_por_simbolo}")
    else:
        print("   [✅ V3.3] Coherencia OHLC verificada en todas las barras reales.")
    if frac > UMBRAL_OHLC_INCOHERENTE:
        raise RuntimeError(f"🛑 FATAL [Datos]: {frac*100:.4f}% de barras reales con OHLC incoherente supera el "
                           f"umbral {UMBRAL_OHLC_INCOHERENTE*100:.2f}%. Revisar el CSV/extractor.")
    return malas_por_simbolo


print(f"⏳ Fase 0 {FASE0_VERSION}: verificando estado del Parquet...")

try:
    # 1. CONVERSIÓN A PARQUET BLINDADA (CAPA PLATA)
    if not _parquet_esta_actualizado(RUTA_CSV, RUTA_PARQUET):

        # Lectura superficial para auditoría (5 filas) — sólo cuando hay que regenerar
        df_preview = pd.read_csv(RUTA_CSV, nrows=5)
        print("\n" + "="*70)
        print("✅ ¡ARCHIVO LEÍDO CON ÉXITO!")
        print("="*70)
        print("📋 ESTOS SON LOS NOMBRES EXACTOS DE TUS COLUMNAS:")
        for i, col in enumerate(df_preview.columns[:15]):
            print(f"   {i}. '{col}'")
        if len(df_preview.columns) > 15:
            print(f"   ... (y {len(df_preview.columns) - 15} columnas más)")
        print("="*70)

        print(f"\n🚀 Iniciando procesamiento masivo en servidor dedicado...")
        print(f"   [!] Cargando matriz completa en RAM. Por favor espera...")

        # 🛡️ [FIX T1↔T2] Cruce best-effort con manifest forense de extracción
        _cargar_manifest_extraccion(RUTA_CSV)

        df_full = pd.read_csv(RUTA_CSV)

        # A+B. Indexación temporal absoluta + orden cronológico, CON validación del reloj
        df_full, info_reloj = _preparar_reloj(df_full)

        # ======================================================================
        # 🛡️ C. LA SUTURA MATEMÁTICA (El puente de tiempo de mercado)
        # ======================================================================
        print("   [+] Aplicando Sutura Quirúrgica (Forward Fill + Aplanamiento Códex M1)...")
        filas_iniciales = len(df_full)

        # 🔬 LOG FORENSE PRE-FFILL (diagnóstico preliminar — NO es lo que se amputa)
        nan_counts_pre = df_full.isna().sum()
        columnas_con_nan = nan_counts_pre[nan_counts_pre > 0].sort_values(ascending=False)
        if len(columnas_con_nan) > 0:
            print(f"   [🔬 FORENSE PRE-FFILL] Columnas con NaN (Top 10 de {len(columnas_con_nan)}):")
            for col, cnt in columnas_con_nan.head(10).items():
                print(f"        - {col}: {cnt} NaN ({(cnt/filas_iniciales)*100:.2f}%)")

        # 1. Micro-suturas de liquidez y Aplanamiento Geométrico (Códex M1)
        print("   [+] Calculando máscaras de inactividad (Velas Fantasma)...")
        mask_nan = df_full.isna()

        # Ffill base: arrastra Close y Spreads al nuevo índice t
        df_full = df_full.ffill()

        print("   [+] Aplanando espectro (O=H=L=C=Prev_Close) e inyectando tensores de tiempo nulo...")

        # 🛡️ [FIX T2-Patrón] Detección robusta por sufijo EXACTO ('_Close'),
        # no por substring laxo ('close' in c.lower()).
        cols_close = [c for c in df_full.columns if c.endswith('_Close')]
        if not cols_close:
            raise RuntimeError("🛑 FATAL [Datos]: el CSV no tiene ninguna columna '*_Close'. "
                               "No hay símbolos que procesar.")

        faltantes_homologos = []  # 🛡️ [FIX T2-H1]
        bases_ok = []
        parciales_ohlc = {}       # 🛡️ [V3.3 N6-M3] filas con NaN en H/L/C pero Open presente

        for c_close in cols_close:
            # Reconstrucción determinística del base_name — sin ambigüedad de matching.
            base_name = c_close[:-len('_Close')]

            c_open = f"{base_name}_Open"
            c_high = f"{base_name}_High"
            c_low = f"{base_name}_Low"
            c_vol_candidatos = [f"{base_name}_Volume", f"{base_name}_Vol", f"{base_name}_Tick_Volume"]
            c_vol = next((c for c in c_vol_candidatos if c in df_full.columns), None)

            homologos_ok = (
                c_open in df_full.columns and
                c_high in df_full.columns and
                c_low in df_full.columns
            )

            if not homologos_ok:
                faltantes_homologos.append({
                    "cierre": c_close,
                    "base_name": base_name,
                    "open_encontrado": c_open in df_full.columns,
                    "high_encontrado": c_high in df_full.columns,
                    "low_encontrado": c_low in df_full.columns,
                })
                continue

            # Condición de fallo: la barra no existía en el mercado real. [V3.3 N6-M3] Se considera
            # fantasma si falta CUALQUIERA de O/H/L/C (antes sólo Open): una barra parcial dejaba un
            # High/Low arrastrado de la vela anterior (extremo falso). En datos limpios es idéntico.
            is_phantom = mask_nan[[c_open, c_high, c_low, c_close]].any(axis=1)
            n_parcial = int((is_phantom & ~mask_nan[c_open]).sum())
            if n_parcial:
                parciales_ohlc[base_name] = n_parcial

            # Aplanamiento de amplitud: Neutraliza MFE/MAE falsos sobre ticks inexistentes
            df_full.loc[is_phantom, c_open] = df_full.loc[is_phantom, c_close]
            df_full.loc[is_phantom, c_high] = df_full.loc[is_phantom, c_close]
            df_full.loc[is_phantom, c_low]  = df_full.loc[is_phantom, c_close]

            # Congelación volumétrica
            if c_vol:
                df_full.loc[is_phantom, c_vol] = 0.0

            # Marcador booleano (1.0 = Fantasma). Obligatorio para dilución en Fase 1&2
            col_mask_name = f"{base_name}_phantom"
            df_full[col_mask_name] = is_phantom.astype(np.float32)
            bases_ok.append(base_name)

        del mask_nan
        gc.collect()

        # 🛡️ [FIX T2-H1] FATAL EXPLÍCITO — Ley Zero-Hallucination.
        # Un símbolo sin marcador '_phantom' se traduce corriente abajo
        # (Fase 1&2) en "cero fricción de gaps" ASUMIDA SILENCIOSAMENTE.
        if faltantes_homologos:
            print("\n   🛑 [FORENSE T2-H1] Símbolos sin homólogos OHLC completos:")
            for item in faltantes_homologos:
                print(f"        - {item['cierre']} (base='{item['base_name']}') → "
                      f"Open={item['open_encontrado']} High={item['high_encontrado']} Low={item['low_encontrado']}")
            raise RuntimeError(
                f"🛑 FATAL [Auditoría T2-H1]: {len(faltantes_homologos)} símbolo(s) no tienen "
                f"sus 3 homólogos OHLC completos — imposible generar el marcador '_phantom' "
                f"para ellos con integridad forense. Bajo la Ley Zero-Hallucination, el "
                f"pipeline NO asume 'cero fricción' por defecto para un símbolo huérfano. "
                f"Corregir la convención de nombres en el CSV origen o excluir estos "
                f"símbolos explícitamente antes de reintentar."
            )

        if parciales_ohlc:
            print(f"   [⚠️  V3.3] Barras con Open presente pero H/L/C ausente (extracción parcial) tratadas como "
                  f"fantasma: {sum(parciales_ohlc.values())} filas. Por símbolo: {parciales_ohlc}")

        # 2. Amputación del asimetrismo inicial (minutos cero sin cotización 100%)

        # 🛡️ [FIX T2-H3] Atribución forense REAL — estado inmediatamente ANTES
        # del corte que efectivamente se ejecuta (post-ffill, pre-dropna).
        nan_counts_final_pre_drop = df_full.isna().sum()
        columnas_con_nan_final = nan_counts_final_pre_drop[nan_counts_final_pre_drop > 0].sort_values(ascending=False)
        if len(columnas_con_nan_final) > 0:
            print(f"\n   [🔬 FORENSE PRE-DROP FINAL] Columnas que causan la amputación real de filas "
                  f"(Top 10 de {len(columnas_con_nan_final)}):")
            for col, cnt in columnas_con_nan_final.head(10).items():
                print(f"        - {col}: {cnt} filas con NaN remanente post-ffill (candidatas a amputación)")
        else:
            print("\n   [🔬 FORENSE PRE-DROP FINAL] Sin columnas con NaN remanente tras ffill — "
                  "dropna() no debería amputar ninguna fila.")

        df_full.dropna(inplace=True)

        filas_borradas = filas_iniciales - len(df_full)
        retencion = (len(df_full) / filas_iniciales) if filas_iniciales > 0 else 0.0
        print(f"   [+] Limpieza completada. Filas iniciales asimétricas borradas: {filas_borradas} "
              f"({(1-retencion)*100:.2f}% del total) — Retención efectiva: {retencion*100:.2f}%")

        # 🛡️ POST-CONDICIONES DE INTEGRIDAD. [V3.3 N6-A1] RuntimeError explícito (un `assert` se
        # perdía en el except genérico y con `python -O`): cubren aniquilación total y degradación masiva.
        if len(df_full) == 0:
            raise RuntimeError(
                "🛑 FATAL: dropna() post-ffill eliminó el 100% de las filas (¿una columna 100% NaN?). "
                "Matriz resultante vacía — abortando antes de persistir un Parquet corrupto."
            )
        if retencion < UMBRAL_RETENCION_MINIMA:
            raise RuntimeError(
                f"🛑 FATAL [Auditoría T2-H2]: retención post-dropna de {retencion*100:.2f}% "
                f"está por debajo del umbral mínimo configurado ({UMBRAL_RETENCION_MINIMA*100:.0f}%). "
                f"Esto no es fricción determinista de mercado (Axioma Cero) — es degradación "
                f"estructural del dataset (probablemente un símbolo con histórico incompleto o "
                f"mal alineado temporalmente). Revisar el reporte forense pre-drop-final arriba "
                f"antes de reintentar, o ajustar UMBRAL_RETENCION_MINIMA únicamente si la causa "
                f"está identificada, documentada y es legítima."
            )

        # 🛡️ [V3.3 N6-M4] Tasa de fantasmas por símbolo — mide cuánto difiere "N filas atrás" (Python)
        # de "N barras atrás" (MT5, que no tiene barra donde Python tiene fantasma).
        tasas_phantom = {b: round(float(df_full[f'{b}_phantom'].mean()) * 100.0, 3) for b in bases_ok}
        top = sorted(tasas_phantom.items(), key=lambda kv: kv[1], reverse=True)[:10]
        print("   [👻 FANTASMAS] % de filas fantasma por símbolo (Top 10 de "
              f"{len(tasas_phantom)}): " + " | ".join(f"{b} {v:.2f}%" for b, v in top))

        # 🛡️ [V3.3] Calidad de precios (finitos > 0, coherencia OHLC) sobre el dataset final.
        incoherentes = _validar_ohlc(df_full, bases_ok)

        # D. Downcasting Extremo de RAM
        print("   [+] Optimizando RAM (Downcasting a float32)...")
        cols_float = df_full.select_dtypes(include=['float64']).columns
        df_full[cols_float] = df_full[cols_float].astype(np.float32)

        # E. Guardado en Parquet Transaccional, con sello forense en los metadatos [V3.3 N6-M1]
        print("   [+] Escribiendo base de datos binaria Parquet (modo transaccional + sello forense)...")
        sello = {
            'version': FASE0_VERSION,
            'csv': {'nombre': os.path.basename(RUTA_CSV), 'bytes': os.path.getsize(RUTA_CSV),
                    'mtime': os.path.getmtime(RUTA_CSV)},
            'tz': info_reloj['tz'], 't_inicio': info_reloj['t_inicio'], 't_fin': info_reloj['t_fin'],
            'filas': len(df_full), 'retencion_pct': round(retencion * 100.0, 3),
            'phantom_pct': tasas_phantom, 'ohlc_parciales': parciales_ohlc, 'ohlc_incoherentes': incoherentes,
        }
        ruta_parquet_temp = RUTA_PARQUET + ".tmp"
        try:
            tabla = pa.Table.from_pandas(df_full)          # preserva el índice 'time' y metadatos pandas
            meta = dict(tabla.schema.metadata or {})
            meta[b'nexus_fase0'] = json.dumps(sello).encode('utf-8')
            pq.write_table(tabla.replace_schema_metadata(meta), ruta_parquet_temp, compression='snappy')
            os.replace(ruta_parquet_temp, RUTA_PARQUET)
        finally:
            if os.path.exists(ruta_parquet_temp):          # [N6-B1] no dejar .tmp huérfano si falló la escritura
                os.remove(ruta_parquet_temp)

        # Limpieza de memoria
        del df_full, tabla
        gc.collect()

        print(f"\n🎉 ¡ÉXITO! Archivo optimizado (Indexado, Suturado, Validado y Downcasted) — {FASE0_VERSION}.")
        print(f"Guardado localmente como:\n{RUTA_PARQUET}")
    else:
        print(f"\n⚡ El archivo Parquet de Fase 0 está actualizado: {RUTA_PARQUET}")
        print("(sello de versión OK y mtime Parquet >= mtime CSV origen. "
              "Si forzaste una re-descarga del CSV y ves este mensaje, verificá el "
              "mtime del sistema de archivos antes de asumir datos frescos.)")

except FileNotFoundError:
    print(f"\n🛑 ERROR: No pude encontrar el archivo:\n{RUTA_CSV}")
    print("Asegúrate de haber arrastrado el archivo CSV.gz al panel izquierdo de Jupyter.")
    raise
# [V3.3 N6-A1] Sin `except Exception` genérico: cualquier otro error (RuntimeError de auditoría,
# fallo de lectura/escritura, MemoryError) se propaga VISIBLE al operador y detiene el pipeline.
