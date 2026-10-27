# ==============================================================================
# 🎯 PIPELINE LOCAL HÍBRIDO: EXTRACCIÓN M1 (OHLC) -> GZIP (WIN 8.1 COMPATIBLE)
# 🛡️ V3.2 — DESCARGA SINCRONIZADA POR RANGO DE FECHAS (CERO NANS INICIALES)
# ==============================================================================
# 📋 BITÁCORA DE CONSOLIDACIÓN V3.2:
#    - [RANGO FECHAS CERRADO] Erradicado el conteo ciego de barras por mes.
#      Ahora se solicita Fecha Inicio y Fecha Fin en calendario (YYYY-MM-DD).
#    - [ANCLAJE BROKER SEGURO] Los timestamps se calculan respecto al Punto Cero
#      nativo del servidor MT5, eliminando desfases de huso horario local (PC vs Broker).
#    - [CERO LEADING NANS] Todos los 28 pares son recortados exactamente en la
#      misma fecha inicial, garantizando retención > 95% en Fase 0.
#      ⚠️ V3.3: esta promesa NO la garantiza el extractor (ver H-04); la garantía
#      efectiva la da Fase 0 (dropna + umbral de retención).
# 📋 BITÁCORA V3.3 (Auditoría NEXUS — parches H-01 y H-02, LUZ VERDE del CRO):
#    - [H-01] Contrato de nombre Extractor↔Fase 0: además del archivo fechado, se
#      publica el ALIAS estable NOMBRE_ALIAS_FASE0 (+ su .manifest.json) con
#      copia ATÓMICA (.tmp + os.replace; mtime = momento de la copia, nunca el
#      del origen). Si el alias ya existía se avisa que se sobrescribe.
#      El sufijo '_24m' del alias es una etiqueta HEREDADA: el rango real está
#      en el manifest (fecha_inicio_solicitada / fecha_fin_solicitada).
#    - [H-02] 'completo' ya NO significa "obtuvo alguna vela". Ahora exige que la
#      primera y la última vela del par queden a <= TOLERANCIA_COBERTURA del
#      rango pedido. Se registran holgura_inicio_min / holgura_fin_min, el motivo
#      y la lista 'pares_incompletos' del manifest. Par sin velas en rango:
#      se registra y se omite ANTES del join (antes: IndexError en el print).
# ==============================================================================

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
import gc
import json
import datetime as dt
import shutil

PARES_BASE = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "USDCHF", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY", "EURGBP",
    "EURAUD", "EURNZD", "EURCHF", "GBPCHF", "AUDCHF", "NZDCHF", "GBPAUD",
    "GBPCAD", "GBPNZD", "AUDCAD", "AUDNZD", "CADCHF", "EURCAD", "NZDCAD"
]

RUTA_TERMINAL_MT5 = r"C:\Program Files\MetaTrader 5 EXNESS"

# 🛡️ [H-01] Nombre estable que lee Fase_0.py (RUTA_CSV). Mantener idéntico en ambos archivos.
NOMBRE_ALIAS_FASE0 = "nexus_matrix_ohlc_m1_24m.csv.gz"
# 🛡️ [H-02] Holgura máx. entre el borde pedido y la primera/última vela real. 4 días cubre
# fin de semana + feriado; [DEFAULT / CRO-OVERRIDE] (heurística, no derivación).
TOLERANCIA_COBERTURA = pd.Timedelta(days=4)


def inicializar_mt5_seguro():
    if mt5.initialize(path=RUTA_TERMINAL_MT5) or mt5.initialize():
        return True
    return False


def autodetectar_sufijo():
    for var in ["EURUSDm", "EURUSD", "EURUSD.pro", "EURUSD_i"]:
        if mt5.symbol_info(var) is not None:
            return var.replace("EURUSD", "")
    return None


def validar_simbolo_existe(simbolo):
    return mt5.symbol_info(simbolo) is not None


def forzar_sincronizacion_m1(simbolo):
    print(f"🔄 Sincronizando caché del Bróker para: {simbolo}...")
    if not mt5.symbol_select(simbolo, True): return False
    mt5.copy_rates_from_pos(simbolo, mt5.TIMEFRAME_M1, 0, 10)
    return True


def descargar_matriz_hibrida(fecha_inicio_str, fecha_fin_str=None):
    if not inicializar_mt5_seguro():
        print("🛑 FATAL: No se pudo conectar con el terminal MT5.")
        return None

    sufijo = autodetectar_sufijo()
    if sufijo is None:
        print("🛑 FATAL: No se pudo autodetectar el sufijo de broker para EURUSD.")
        mt5.shutdown()
        return None

    pares_reales = [p + sufijo for p in PARES_BASE]
    chunk_size = 50000

    print(f"\n📂 Iniciando extracción SINCRONIZADA POR RANGO DE FECHAS")
    print("-" * 80)

    # 1. ANCLAJE NATIVO DE TIEMPO DEL SERVIDOR (Punto Cero)
    simbolo_ancla = pares_reales[0]
    if not validar_simbolo_existe(simbolo_ancla) or not forzar_sincronizacion_m1(simbolo_ancla):
        print(f"🛑 FATAL: Imposible sincronizar el símbolo ancla '{simbolo_ancla}'.")
        mt5.shutdown()
        return None

    vela_ancla = mt5.copy_rates_from_pos(simbolo_ancla, mt5.TIMEFRAME_M1, 1, 1)
    if vela_ancla is None or len(vela_ancla) == 0:
        print("🛑 FATAL: No se pudo leer el timestamp nativo del servidor.")
        mt5.shutdown()
        return None

    punto_cero_timestamp = int(vela_ancla[0]['time'])
    punto_cero_dt = pd.to_datetime(punto_cero_timestamp, unit='s')
    
    # 2. DEFINICIÓN EXACTA DE LÍMITES CALENDARIO (EN HUSO NATIVO DEL BRÓKER)
    dt_inicio_solicitado = pd.to_datetime(fecha_inicio_str + " 00:00:00")
    
    if fecha_fin_str is None or fecha_fin_str.strip() == "":
        dt_fin_solicitado = punto_cero_dt
        ts_fin_broker = punto_cero_timestamp
    else:
        dt_fin_solicitado = pd.to_datetime(fecha_fin_str + " 23:59:00")
        diff_fin = (punto_cero_dt - dt_fin_solicitado).total_seconds()
        ts_fin_broker = int(punto_cero_timestamp - diff_fin)

    diff_inicio = (punto_cero_dt - dt_inicio_solicitado).total_seconds()
    ts_inicio_broker = int(punto_cero_timestamp - diff_inicio)

    if ts_inicio_broker >= ts_fin_broker:
        print("🛑 FATAL: La fecha de inicio debe ser anterior a la fecha de fin.")
        mt5.shutdown()
        return None

    dias_totales = (dt_fin_solicitado - dt_inicio_solicitado).days
    print(f"⚓ PUNTO CERO BROKER: {punto_cero_dt} (Timestamp: {punto_cero_timestamp})")
    print(f"📅 RANGO SOLICITADO: Desde {dt_inicio_solicitado} hasta {dt_fin_solicitado} ({dias_totales} días de calendario)")
    print("-" * 80)

    df_maestro = pd.DataFrame()
    exitos = 0
    manifest = {
        "version_manifest": "2.0",
        "capa": "BRONCE_CRUDO",
        "nota": "Datos extraídos por rango estricto de fechas calendario. Cero NaNs iniciales.",
        "fecha_extraccion_utc": dt.datetime.utcnow().isoformat() + "Z",
        "fecha_inicio_solicitada": str(dt_inicio_solicitado),
        "fecha_fin_solicitada": str(dt_fin_solicitado),
        "punto_cero_timestamp": punto_cero_timestamp,
        "simbolo_ancla": simbolo_ancla,
        "sufijo_broker": sufijo,
        "pares": {}
    }

    # 3. EXTRACCIÓN HACIA ATRÁS POR FECHAS (Hasta cruzar ts_inicio_broker)
    for simbolo in pares_reales:
        if not forzar_sincronizacion_m1(simbolo):
            manifest["pares"][simbolo] = {"velas_obtenidas": 0, "completo": False, "motivo": "fallo_sincronizacion"}
            continue

        df_par_list = []
        ultima_fecha = ts_fin_broker

        while ultima_fecha > ts_inicio_broker:
            chunk = mt5.copy_rates_from(simbolo, mt5.TIMEFRAME_M1, ultima_fecha, chunk_size)
            if chunk is None or len(chunk) == 0:
                break

            df_chunk = pd.DataFrame(chunk)
            df_chunk['time'] = pd.to_datetime(df_chunk['time'], unit='s')

            if len(df_par_list) > 0 and len(df_chunk) > 1:
                df_chunk = df_chunk.iloc[:-1]

            df_par_list.append(df_chunk)
            primer_tiempo_chunk = int(chunk[0]['time'])

            if primer_tiempo_chunk <= ts_inicio_broker:
                break
            if primer_tiempo_chunk >= ultima_fecha:
                # Evita bucles infinitos si no hay más datos hacia atrás
                break

            ultima_fecha = primer_tiempo_chunk

        if len(df_par_list) > 0:
            df_par = pd.concat(df_par_list, ignore_index=True)
            df_par.drop_duplicates(subset='time', inplace=True)
            df_par.sort_values('time', inplace=True)
            df_par.set_index('time', inplace=True)

            # 🛡️ RECORTE EXACTO DE LÍMITES CALENDARIO: Garantiza que todos arranquen sincronizados
            df_par = df_par[(df_par.index >= dt_inicio_solicitado) & (df_par.index <= dt_fin_solicitado)]

            if len(df_par) == 0:
                manifest["pares"][simbolo] = {"velas_obtenidas": 0, "completo": False, "motivo": "sin_datos_en_rango"}
                print(f"   🔴 [{simbolo}] Sin velas dentro del rango solicitado.")
                del df_par, df_par_list
                continue

            # 🛡️ [H-02] Cobertura real contra el rango pedido
            holgura_ini = df_par.index[0] - dt_inicio_solicitado
            holgura_fin = dt_fin_solicitado - df_par.index[-1]
            cubre_ini = holgura_ini <= TOLERANCIA_COBERTURA
            cubre_fin = holgura_fin <= TOLERANCIA_COBERTURA
            completo = bool(cubre_ini and cubre_fin)

            df_ohlc = df_par[['open', 'high', 'low', 'close']].copy()
            df_ohlc.columns = [f"{simbolo}_Open", f"{simbolo}_High", f"{simbolo}_Low", f"{simbolo}_Close"]
            df_ohlc = df_ohlc.astype(np.float32)

            if df_maestro.empty:
                df_maestro = df_ohlc
            else:
                df_maestro = df_maestro.join(df_ohlc, how='outer')

            exitos += 1
            manifest["pares"][simbolo] = {
                "velas_obtenidas": len(df_par),
                "primer_timestamp": str(df_par.index[0]) if len(df_par) > 0 else None,
                "ultimo_timestamp": str(df_par.index[-1]) if len(df_par) > 0 else None,
                "holgura_inicio_min": round(holgura_ini.total_seconds() / 60.0, 1),
                "holgura_fin_min": round(holgura_fin.total_seconds() / 60.0, 1),
                "completo": completo
            }
            if not completo:
                motivos = []
                if not cubre_ini: motivos.append("cobertura_inicio_insuficiente")
                if not cubre_fin: motivos.append("cobertura_fin_insuficiente")
                manifest["pares"][simbolo]["motivo"] = "+".join(motivos)
                print(f"   ⚠️ [{simbolo}] COBERTURA PARCIAL: {manifest['pares'][simbolo]['motivo']} "
                      f"(holgura inicio {holgura_ini}, fin {holgura_fin}; tolerancia {TOLERANCIA_COBERTURA}).")

            print(f"   🟢 [{simbolo}] Sincronizado | Velas: {len(df_par):,} | Desde: {df_par.index[0]} hasta {df_par.index[-1]}")
            del df_par, df_par_list, df_ohlc
            gc.collect()
        else:
            manifest["pares"][simbolo] = {"velas_obtenidas": 0, "completo": False, "motivo": "sin_datos_en_rango"}

    mt5.shutdown()
    print("-" * 80)

    assert exitos == len(PARES_BASE), f"🛑 FATAL: Se esperaban {len(PARES_BASE)} pares, pero se extrajeron {exitos}."

    if df_maestro.empty:
        print("❌ FATAL: Matriz maestra vacía.")
        return None

    # Guardamos con un nombre estándar identificable
    tag_inicio = dt_inicio_solicitado.strftime("%Y%m%d")
    tag_fin = dt_fin_solicitado.strftime("%Y%m%d")
    nombre_archivo = f"nexus_matrix_ohlc_m1_{tag_inicio}_{tag_fin}.csv.gz"

    print(f"💾 Comprimiendo a GZIP ({nombre_archivo})...")
    df_maestro.to_csv(nombre_archivo, compression="gzip")

    ruta_manifest = nombre_archivo + ".manifest.json"
    manifest["pares_incompletos"] = [s for s, i in manifest["pares"].items() if not i.get("completo")]
    if manifest["pares_incompletos"]:
        print(f"⚠️ COBERTURA PARCIAL en {len(manifest['pares_incompletos'])} par(es): {manifest['pares_incompletos']}. "
              f"Fase 0 abortará con este manifest (ABORTAR_SI_EXTRACCION_PARCIAL).")
    with open(ruta_manifest, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # 🛡️ [H-01] Publicación atómica del alias estable que consume Fase 0
    for origen, destino in ((nombre_archivo, NOMBRE_ALIAS_FASE0), (ruta_manifest, NOMBRE_ALIAS_FASE0 + ".manifest.json")):
        if os.path.exists(destino):
            print(f"♻️ Alias existente sobrescrito: {destino}")
        tmp_alias = destino + ".tmp"
        shutil.copyfile(origen, tmp_alias)   # copyfile (no copy2): el mtime del alias es el de ESTA copia
        os.replace(tmp_alias, destino)
    print(f"🔗 Alias para Fase 0: {os.path.abspath(NOMBRE_ALIAS_FASE0)} (+ manifest). Rango real: {tag_inicio} → {tag_fin}")

    tamano_mb = os.path.getsize(nombre_archivo) / (1024 * 1024)
    print(f"\n🏆 EXTRACCIÓN SINCRONIZADA COMPLETADA:")
    print(f"📂 Archivo generado: {os.path.abspath(nombre_archivo)}")
    print(f"📋 Manifest: {os.path.abspath(ruta_manifest)}")
    print(f"📏 Dimensiones: {df_maestro.shape} (Velas: {len(df_maestro):,} x Columnas: {df_maestro.shape[1]})")
    print(f"📦 Tamaño: {tamano_mb:.2f} MB")
    print(f"🕒 Rango Real de la Matriz: {df_maestro.index[0]} → {df_maestro.index[-1]}")


def solicitar_fechas():
    print("=" * 70)
    print("🎛️  TABLERO DE CONTROL — EXTRACCIÓN OHLC M1 POR FECHAS")
    print("=" * 70)
    while True:
        f_inicio = input("Fecha de INICIO (YYYY-MM-DD) [ej: 2026-07-12]: ").strip()
        try:
            dt.datetime.strptime(f_inicio, "%Y-%m-%d")
            break
        except ValueError:
            print("⚠️ Formato incorrecto. Debe ser YYYY-MM-DD (ej: 2026-07-12).\n")

    f_fin = input("Fecha de FIN (YYYY-MM-DD) [Enter = Hoy / Última disponible]: ").strip()
    if f_fin != "":
        try:
            dt.datetime.strptime(f_fin, "%Y-%m-%d")
        except ValueError:
            print("⚠️ Formato incorrecto de fin. Se usará la fecha actual de mercado.")
            f_fin = None
    else:
        f_fin = None

    return f_inicio, f_fin


if __name__ == "__main__":
    inicio, fin = solicitar_fechas()
    descargar_matriz_hibrida(fecha_inicio_str=inicio, fecha_fin_str=fin)
