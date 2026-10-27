# nexus-hybrid — Laboratorio NEXUS (Fases 0 a 4.5B)

Pipeline cuantitativo: Python soberano (kernels Numba) + EA de MetaTrader 5 como pasarela. Normas en `docs/SSoT.md`.

## 1. Entorno
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
Las versiones fijadas están en `requirements.txt` (indica cuáles fueron medidas en Codespace y cuáles solo en el sandbox).
**Tras cambiar `nexus_formulas_core.py`, cualquier kernel o la versión de numba, ejecutar `bash limpiar_cache.sh`.**
Motivo (H-CACHE-01, reproducido en 2 entornos): Numba no invalida el caché de un llamador cuando cambia una función de OTRO archivo.

## 2. Orden de ejecución (todas las fases en la MISMA carpeta de trabajo)
| Fase | Archivo | Entrada | Salida |
|---|---|---|---|
| Extractor (PC local, Windows) | `extraxtor_mt5_rangofecha.py` | MetaTrader 5 | `nexus_matrix_ohlc_m1_24m.csv.gz` |
| 0 | `Fase_0.py` | el CSV.gz | `nexus_matrix_ohlc_m1_24m.parquet` (sello `nexus_fase0`) |
| 1&2 | `Fase_1___2.py` | parquet de Fase 0 (28 pares) | `nexus_df_salida_3D_{sim}_MultiZ.parquet` (sello `nexus_fase12`) |
| 3 | `Fase_3.py` | salidas de 1&2 | `Reporte_Fase3_WFO_V5.8_{sim}.csv` |
| 4 | `Fase_4_V12_0.py` | salidas 1&2 + reporte F3 | `Cerebro_MQL5_PROD_V12_E3_{sim}.txt`, `Reporte_OOS_Phase4_…csv` |
| 4.5A | `Fase_4_5_V_12_0_A.py` | salidas de Fase 4 | `F45_V12_E3/` |
| 4.5B | `Fase_4_5_V_12_0_B.py` | `F45_V12_E3/` | portafolio y gráficos |

`Fase_3.py` no tiene guarda `__main__`: importarlo ejecuta el trabajo. No lo importes desde otros scripts.

## 3. Tablero de producción vigente (`nexus_tablero.py`)
`N_FOLDS=2 · RATIO_TRAIN_TEST=2.0 · RESERVA_FINAL=0.25 · MEMORIA_FIFO=100 · EXIGIR_SELLO=True · ESCALON=E3`.
Verificar contratos entre fases: `python3 auditoria/verificar_tableros.py . --salida auditoria/tablero_produccion.json` (sale con código 1 si hay hallazgo crítico).

## 4. Pruebas de humo (datos sintéticos, no representan mercado)
`python3 auditoria/generar_datos_sinteticos.py nexus_matrix_ohlc_m1_24m.csv.gz 6000` en una carpeta temporal con copia de los `.py`, luego Fase 0 y Fase 1&2.
Informe completo de solo lectura: `bash auditoria/correr_codespace.sh`.

## 5. Estado y decisiones pendientes del CRO
- **NO VERIFICADO:** ejecución extremo a extremo con los 24 meses reales (Fases 3, 4, 4.5A, 4.5B no se han corrido sobre datos).
- **RESERVA_FINAL=0.25 (decisión del CRO):** Fases 3 y 4 usan el 75 % inicial del archivo; el último 25 % queda ciego para 4.5B. Cualquier resultado previo de Fase 3 queda invalidado: hay que volver a correrla. La reserva "se gasta" si se ajusta la configuración mirando el resultado de 4.5B.
- Esta rama solo cambia `nexus_tablero.py` (RESERVA_FINAL 0.0 → 0.25) respecto de los renombres de `prep/nombres`.
