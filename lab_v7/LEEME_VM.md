# LAB V8 (rama lab-v8, sobre lab-v7) — GUÍA DE LA VM (de la carpeta al cerebro exportado)

## 0. Qué hay en esta carpeta
- Raíz: `nexus_formulas_core.py`, `nexus_tablero.py` (geometría WFO), `requirements.txt`, `limpiar_cache.sh`, y las fases de main (`Fase_0`, `Fase_1___2`, y las copias de main que usan las pruebas).
- `lab_v7/`: `Fase_3_lab.py`, `Fase_4_lab.py`, `Fase_4_5_lab_A.py`, `Fase_4_5_lab_B.py`, `vida_v3.py`, `v7_metricas.py`, `lab_escala.py`, **`tablero_lab.env`** (todos los interruptores), `correr_tablero.sh`, `verificar_vm.py`, pruebas y `EA_V12.01_LAB.txt`.

## 1. Qué decides (y dónde)
| Decisión | Dónde | Valor actual |
|---|---|---|
| Métrica de búsqueda/selección | `tablero_lab.env` NEXUS_LAB_METRICA | v7 |
| CSV de Fase 3 que lee Fase 4 | NEXUS_LAB_F3 | v7 |
| Qué aprende el Ridge 2 | NEXUS_LAB_CIERRE | V3 (también dV3) |
| Escala de la Cabeza B y del ΔT vivo (lab-v8) | NEXUS_LAB_T | V3 (T = comportamiento lab-v7) |
| Versión de Vida v3 (lab-v8) | NEXUS_LAB_VIDA | 3.1 (3.0 = lab-v7) |
| Escala de v_req | NEXUS_LAB_TAMANO | A |
| Gemelo nulo (diagnóstico, no exportable) | NEXUS_LAB_NULO | 0 |
| Símbolos | NEXUS_LAB_SIMBOLOS | vacío = 28 (recomendado empezar con 1) |
| Presupuesto Fase 3 | NEXUS_LAB_N_SIM / NEXUS_LAB_STARTUP | vacío = 20000 / 5000 |
| Medir costo de Fase 3 sin escribir CSV | NEXUS_LAB_F3_MEDIR | 0 (poner 200 para medir) |
| Folds, razón IS/OOS, reserva ciega, FIFO | `nexus_tablero.py` (raíz) | 2 / 2.0 / 0.25 / 100 |
| Escalón de ablación | `ESCALON` en Fase_4_lab.py y 4.5 A/B (los tres iguales) | E3 |
Las constantes finas (rangos de Optuna, mínimos de operaciones, alphas, grilla de K) quedan como están en cada fase.

## 2. Orden de ejecución (desde una carpeta de trabajo vacía o con los parquets)
1. `pip install -r requirements.txt` (Python 3.13 o 3.14) y `bash limpiar_cache.sh`.
2. Datos: Fase 0 y Fase 1&2 de main, UNA sola vez, producen `nexus_df_salida_3D_{SIMBOLO}_MultiZ.parquet`. Si ya los tienes, cópialos a la carpeta de trabajo.
3. `python /ruta/lab_v7/verificar_vm.py` (desde la carpeta de trabajo). Solo lectura. No sigas si dice FALLA.
4. Medir: pon `NEXUS_LAB_F3_MEDIR=200` y `NEXUS_LAB_SIMBOLOS=EURUSDm` → `bash /ruta/lab_v7/correr_tablero.sh f3`. Imprime ms por trial y la estimación total. Vuelve `F3_MEDIR=0`.
5. Fase 3: `bash /ruta/lab_v7/correr_tablero.sh f3` → `Reporte_Fase3_WFO_V5.8_{SIMBOLO}_MV7.csv`.
6. Fases 4 y 4.5: `bash /ruta/lab_v7/correr_tablero.sh f4` → `Cerebro_MQL5_*_{SIMBOLO}.txt`, `Reporte_OOS_Phase4_*.csv`, carpeta `F45_V12_E3_LAB_...`.
7. EA: con NEXUS_LAB_T=V3 el bloque exportado trae campos `vida_*`; el EA gemelo de lab-v8 los lee (hay que recompilarlo en MetaEditor). Pega el bloque de `Cerebro_MQL5_*.txt` dentro de `CargarConfiguracionesOptuna` de `EA_V12.01_LAB.txt`, compila y prueba en el probador.

## 3. Reglas
- No mezclar tableros: todas las fases deben correr con el MISMO `tablero_lab.env` y el MISMO `nexus_tablero.py`. El sello lo verifica y se niega a seguir si no coinciden.
- Cambiar la geometría invalida los CSV de Fase 3: se vuelve a correr.
- Con recursos escasos, no repitas Fase 3 porque sí: es la fase pesada.
- Nada de esto corrió con datos reales todavía. La primera corrida real es la prueba.

## 4. Cuántas configuraciones pasa cada fase (verificado en el código)
- **Fase 3** escribe hasta `TOP_REPORTE`=100 filas por (fold, dirección, símbolo). Con 2 folds: hasta 200 por dirección. El nulo (R=20) corre SOLO sobre ese top, al final; durante la búsqueda Optuna usa R=0.
- **Fase 4** lee TODAS esas filas (`TOP_CANDIDATOS`=1000 no limita: hay a lo sumo 200 por dirección). Cada fila es un candidato: entrena Ridge 1 y 2, escanea K y evalúa OOS. No hay una segunda selección previa.
- En Fase 4 el nulo NO se aplica a una selección: cada evaluación de Score_v7 lleva R=20 réplicas dentro del cálculo (≈15 evaluaciones por candidato). Medido con datos sintéticos: ~7 ms con R=0 y ~12 ms con R=20 por evaluación. Con datos reales puede variar.
- Exporta los 10 mejores por dirección (`EXPORTAR_MQL5_TOP`=10). **Fase 4.5** simula esos 10 ranks.
- `NEXUS_LAB_NULO=1` es otra cosa: una corrida completa aparte con el objetivo barajado, solo diagnóstico, nunca exportable.

## 5. En Jupyter (Ubuntu)
- Sube el zip con el explorador de archivos de Jupyter y descomprime en una celda: `!unzip -q nexus-hybrid-lab-v7.zip`.
- Las corridas largas NO deben ir en una celda normal: si se cierra el navegador o el kernel, se cortan. Abre una terminal de Jupyter (File → New → Terminal) y lanza en segundo plano:
  `cd carpeta_de_trabajo && nohup bash ../nexus-hybrid-lab-v7/lab_v7/correr_tablero.sh f3 > f3.log 2>&1 &`
  y mira el avance con `tail -f f3.log`. Lo mismo con `f4`.
- Si Jupyter corre en un contenedor sin `bash`/`nohup`, avísame el mensaje de error.

## 6. Informes de Fase 4 (lab-v8, 2026-11-10)
Con `NEXUS_LAB_CENSO=1` en el tablero (valor actual), Fase 4 escribe además, sin cambiar la selección ni el cerebro:

| Archivo | Para qué | Tamaño |
|---|---|---|
| `Resumen_Fase4_{tag}.md` | Lectura rápida: embudo por símbolo y dirección, Ridge 1, Ridge 2 con y sin, nulo de entrada (C3), exportados | 1-2 páginas |
| `Vista_Fase4_{tag}_{SIMBOLO}.csv` | Lectura directa del CRO: las primeras `NEXUS_LAB_VISTA_TOP` (50) por dirección y fold, primero las que pasaron; columnas reducidas | chico |
| `Censo_Fase4_{tag}_{SIMBOLO}.csv` | Análisis completo: UNA fila por configuración leída, pase o no, con la etapa donde cayó y todo lo calculado hasta ahí | 1 fila por configuración |
| `Manifiesto_Fase4_{tag}.json` | Trazabilidad: commit y sha1 del código, tablero, geometría, cortes IS/OOS/reserva por símbolo, sha1 de entradas y salidas, descartes, errores de informes | chico |

- Etapas del embudo: `1_preparacion` → `2_ridge1` → `3_tamano` → `4_base_is` → `5_ridge2` → `6_compuerta_oos`. `estado` = `paso` o `descartado`; `causa` dice por qué.
- Columna `ridge2` (solo si la configuración llegó al OOS): `APORTA` = con Ridge 2 mejoran el PF y la mediana de pips en OOS; `MIXTO` = mejora uno; `NO_APORTA` = ninguno; `BASE_RECHAZADA` = sin Ridge 2 el Score_final OOS no era positivo (misma regla que `Reporte_OOS`). Criterio propuesto por el sistema: `[DEFAULT / CRO-OVERRIDE]`.
- El resumen sale SOLO de los censos del disco; se regenera con `python lab_v7/lab_informes.py TAG` desde la carpeta de trabajo.
- Entrega: `python lab_v7/armar_entrega.py` (desde la carpeta de trabajo) arma `entrega_AAAAMMDD_HHMM.zip` con resumen, manifiesto, vistas, censos, reportes, cerebros, registros y tableros.
- Cómo leerlos: las configuraciones de un símbolo se parecen entre sí y los símbolos comparten divisas (tendencias, no pruebas independientes). El OOS de Fase 4 es filtro de exportación; la medición sin filtro es la reserva ciega de Fase 4.5. La tabla "ridge2 solo las que pasaron" favorece a Ridge 2 por construcción: mirar "ridge2 todas".
- Si cambias `TOP_REPORTE` (Fase 3) a mano, pon `TOP_CANDIDATOS` (Fase 4) ≥ `TOP_REPORTE × N_FOLDS`: el CSV de Fase 3 va ordenado por fold y Fase 4 toma las primeras filas por dirección. El resumen lo delata en la columna `recortadas_por_tope`.
- Prueba: L20 (`lab_pruebas.py`) cubre el módulo. La identidad byte a byte de cerebro y `Reporte_OOS` entre el código anterior, `CENSO=0` y `CENSO=1` se comprobó con una cadena sintética de dos símbolos fuera del repo (solo flujo). Nada corrió con datos reales.

## Notas lab-v8
- Con NEXUS_LAB_T=T y NEXUS_LAB_VIDA=3.0 y CIERRE sin dV3, el lab usa las rutas de código de lab-v7. [Corrección 2026-11-10, H-DOC-01: aquí decía "prueba N2"; esa prueba no existe. Lo demostrado es: interruptores apagados == main bit a bit (L1) y la trayectoria sin v3p produce datos (N1). No hay una prueba que compare esta rama con la rama lab-v7 corrida con el mismo tablero; además, desde df69b3a esta rama difiere de lab-v7 a propósito en H-AUD8-01 y H-AUD8-02.]
- Con T=V3, Fase 4 y 4.5 deben correr con el mismo T/VIDA: las etiquetas de archivo llevan `_TV3` / `_VID31` y 4.5 busca el cerebro con la misma etiqueta (si T/VIDA difieren, no lo encuentra).
- Nada de V3 en Cabeza B/ΔT se ha corrido con datos reales: son hipótesis a decidir con corridas pareadas (T vs V3).
