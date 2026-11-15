# NEXUS-HYBRID

**Laboratorio de investigación cuantitativa en forex: cómo construir un sistema de trading, ponerlo a prueba contra el azar y aceptar lo que dicen los datos.**

> **English summary.** NEXUS-HYBRID is a research lab for intraday FX trading. A Numba-compiled Python pipeline handles feature engineering ("kinematic" metrics of a 28-pair, 8-currency system), an Optuna walk-forward search of a zero-cross trigger, and Ridge models for entry and for trade survival. It exports frozen configurations to an MQL5 Expert Advisor that replicates the decision kernels bit for bit. The lab enforces strict causality (decide on bar close, execute on next open), Python/C++ parity, preregistered criteria, structure-preserving null models and multiplicity correction. **Main result: after costs, no strategy tested beat its null at intraday horizons.** Strategy tests were run on **one symbol (EURUSD)**, one broker and one period. This repository shows the engineering, the validation method and the negative results, including our own mistakes. The project was built by one person working with an LLM under a written instruction system (included). Contact: sidereotosca@gmail.com

---

## Estado, sin adornos

| | |
|---|---|
| **Resultado principal** | Después de costos, ninguna estrategia probada superó a su nulo en horizontes intradiarios |
| **Alcance de las pruebas de la estrategia** | **Un solo símbolo (EURUSDm)**, un broker, un período de desarrollo (2023-11 → 2026-02) y dos pliegues walk-forward |
| **Otras mediciones** | Algunas mediciones de estructura usaron varios pares (álgebra de 8 divisas con 28 pares, fixings con 7 pares contra el dólar), siempre en el mismo período |
| **Reserva ciega** | Los últimos 25 % de los datos (2026-02 → 2026-11) no se usan para elegir nada |
| **Lo que sí funciona** | La ingeniería: paridad Python/MQL5, causalidad, reproducibilidad, controles sintéticos. El tamaño del movimiento (volatilidad) es predecible; la dirección, no |

No se publican cifras de rentabilidad porque no hay una que se sostenga contra el nulo.

## Qué es

El laboratorio lee los 28 pares de 8 divisas como un solo sistema y procesa velas de 1 minuto en cinco etapas:

| Fase | Qué hace |
|---|---|
| 0 | Limpieza y alineación de los 28 pares; marca las velas rellenadas ("fantasma") |
| 1&2 | Métricas por par y por marco temporal: el FPP (participación del par en el movimiento del sistema), su primera y segunda integral, y la velocidad y curvatura de cada una (pendiente y curvatura de una parábola ajustada en la vela actual, equivalente a un filtro Savitzky–Golay causal). Z robusto (mediana/MAD) |
| 3 | Gatillo de cruce por cero con "armado" (el acumulado del ciclo supera un saturador: la mediana de los últimos 100 extremos) y "chasquido" (retroceso). Búsqueda walk-forward de configuraciones con Optuna |
| 4 / 4.5 | Dos modelos Ridge: uno decide si se toma el trade (Cabeza B) y otro vigila la vida del trade y lo corta si se degrada. Exportación de los "cerebros" |
| EA | Expert Advisor MQL5 que recalcula las métricas en vivo y aplica los cerebros, con paridad binaria contra Python |

Tecnología: Python 3 · Numba (`fastmath=False` en todo kernel replicado en C++) · NumPy · pandas · PyArrow · scikit-learn · Optuna · MQL5 / MetaTrader 5 · VM en la nube (Oracle OCI, Google Cloud) con JupyterLab · Git.

## Cómo se validó

1. **Preregistro.** Hipótesis, métrica, umbral y regla de decisión se fijan por escrito antes de ver los datos.
2. **Nulos que conservan la estructura.** No se compara contra "otra configuración" sino contra el azar construido igual. Por ejemplo:
   - métrica desfasada respecto del precio;
   - entradas al azar con las duraciones reales permutadas;
   - "nulo de reloj": las mismas ventanas horarias corridas a otra hora del día.
3. **Primero, datos sintéticos.** Cada script se prueba en una caminata aleatoria (debe dar cero menos el costo) y con un efecto sembrado (debe detectarlo).
4. **Multiplicidad.** Corrección de Holm, o una sola prueba principal.
5. **Unidad de análisis y dependencia.** Intervalos por remuestreo de semanas, lados (compra y venta) y pliegues por separado.
6. **Criterio económico.** Pips o puntos básicos netos de spread, no R² ni precisión.
7. **Paridad y causalidad.** Decisión con la vela cerrada, ejecución en la apertura siguiente. El EA reproduce a Python bit a bit.

## Qué se encontró

| Pregunta | Resultado |
|---|---|
| ¿Las métricas de Fase 1&2 anticipan el precio? | No. Van detrás: correlación con el movimiento pasado de 0,3 a 0,6 y con el futuro ≈ 0. La forma media de sus ciclos es la misma que en el nulo |
| ¿La Cabeza B (Ridge de entrada) aprende? | No. Su R² fuera de pliegue (mediana −0,028 en 18 555 configuraciones) es el mismo que da el procedimiento con variables de puro ruido |
| ¿El Ridge de supervivencia aprende? | Su R² (0,26–0,61) está inflado por construcción: una simulación sin información da 0,54–0,62. El R² útil (sobre "lo que falta" del trade) no estaba medido |
| ¿Cortar los trades de Fase 3 con trailing, SL, TP o tiempo mejora salir en el cruce? | No. En el nulo los cortes "ayudan" más que en lo real (725 configuraciones, OOS) |
| ¿La salida de Fase 3 lleva información? | Un indicio en compras: +1,05 pips por trade contra +0,20 del nulo (OOS). En ventas, lo real es igual al nulo: domina la tendencia del período |
| ¿Fase 4 mejora a Fase 3? | No. Su salida mecánica destruye el valor de Fase 3, y elegir configuraciones por su resultado IS selecciona a las más sobreajustadas |
| ¿El álgebra de 8 divisas da dirección? | No a escalas de minutos a un día. Las divisas se mueven juntas en el mismo instante, pero ninguna anticipa a otra |
| ¿La reversión del dólar alrededor de los fixings (Krohn, Mueller y Whelan, *JF* 2024) existe en este broker? | No es utilizable: −0,24 pb/día bruto y −4,79 neto, dentro del nulo de reloj. Las ventanas van en la dirección del paper, con ≈ 0,5 pb, contra 2,5 pb en 1999–2019 |
| ¿Algo es predecible? | Sí: el **tamaño** del movimiento (volatilidad). Sirve para dimensionar y controlar el drawdown, no para ganar |

## Errores y lecciones

- **Una métrica alta no es evidencia.** El R² del Ridge de supervivencia parecía bueno, pero el azar da lo mismo. Lección: medir siempre la métrica sobre datos sin información antes de interpretarla.
- **El nulo tiene que conservar la construcción.** Medimos que "después del extremo de la velocidad, el precio retrocede" y lo tomamos como señal. Una caminata aleatoria da el mismo patrón (−0,7 a −1,8 pips), porque el extremo solo se conoce después de que pasó. El nulo que usamos (métrica desfasada) no conservaba eso.
- **Elegir entre miles de configuraciones selecciona ruido.** El orden de las configuraciones en el IS no se transfiere al OOS.
- **La tendencia del período explica casi todo.** El lado ganador de cada pliegue era el lado de la tendencia.
- **Los costos dominan en intradiario.** Un efecto de 0,5 pb no sobrevive a un spread de ≈ 1 pb por operación. Además, alrededor del cambio de día del broker (17:00 ET) el spread se abre y sesga los precios.

De esto salió un protocolo de 10 reglas para analizar datos complejos (M-PROT):
1. Decir si la pregunta es simultánea o predictiva.
2. Revisar si el resultado sale de cómo está construida la métrica.
3. Leer la definición en el código antes de interpretar.
4. Probar primero en datos sintéticos sin información.
5. Usar un nulo que conserve la estructura.
6. Verificar que el script reproduce al sistema.
7. Usar un criterio primario económico.
8. Separar lados, períodos y la deriva de fondo.
9. Declarar la unidad de análisis y la dependencia.
10. Preregistrar y corregir por multiplicidad.

## Trabajar con un LLM: el sistema de instrucciones

Todo el laboratorio se construyó en colaboración con un modelo de lenguaje bajo un sistema de instrucciones escrito y versionado (NEXUS-STE, hoy V4). Sus piezas:

- **Etiquetas de evidencia** en cada afirmación técnica: `[HECHO EJECUTADO]`, `[HECHO LEÍDO]`, `[INFERENCIA LÓGICA]`, `[HIPÓTESIS]`, `[NO CORRIDO]`. Nada se da por cerrado sin la evidencia de su clase.
- **Autoridad explícita.** El modelo no cambia código ejecutable sin una "luz verde" con el alcance escrito. Las decisiones de diseño, los criterios y el uso de la VM son del responsable humano.
- **Ciclo de laboratorio.** Propuesta, especificación, construcción, verificación, corrida real, dictamen y traspaso. Una rama, una hipótesis; todo interruptor apagado reproduce la rama base.
- **Registros.** Uno de conocimiento (diccionario, arquitectura, malentendidos) y uno de trabajo (solo se le agregan entradas: hipótesis, hallazgos y decisiones).
- **Evolución con evidencia.** Cada versión del sistema de instrucciones registra qué falló y en qué turno.

Lo más útil fue obligar al modelo a decir lo que no se ejecutó en la primera respuesta, y a corregir en voz alta sus afirmaciones equivocadas.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `Fase_0.py`, `Fase_1___2.py`, `Fase_3.py`, `Fase_4_V12_0.py`, `Fase_4_5_V_12_0_A/B.py` | Pipeline de producción (rama `main`) |
| `nexus_tablero.py`, `nexus_formulas_core.py` | Fuente única de pliegues, spreads y fórmulas compartidas |
| `EA_V12.01.txt` | Expert Advisor MQL5 |
| `lab_v7/` (ramas `lab-v7` y `lab-v8`) | Laboratorio paralelo con interruptores, métricas rediseñadas y controles sintéticos |
| `auditoria/`, `docs/` | Herramientas de verificación y documentación |
| `extraxtor_mt5_rangofecha.py` | Extracción de velas M1 desde MetaTrader 5 |

Ramas: `main` (producción), `lab-v7` y `lab-v8` (laboratorios aditivos sobre una rama base declarada), más ramas de parche y refactorización. No se incluyen datos del broker.

## Competencias que muestra este proyecto

- Diseño de experimentos y validación estadística para finanzas: preregistro, nulos que conservan la estructura, walk-forward, remuestreo por bloques, Holm.
- Ingeniería numérica en Python: Numba, kernels causales y reproducibilidad bit a bit.
- MQL5 / MetaTrader 5 y paridad Python ↔ C++.
- MLOps de laboratorio: VM en la nube montada con un script (JupyterLab, systemd, fail2ban), corridas largas en tmux, sellos y controles de integridad.
- Auditoría de modelos: R² inflado, fugas IS→OOS, sobreajuste por selección.
- Trabajo con LLM bajo reglas escritas de evidencia y autoridad.

## Cómo correrlo

Instrucciones de entorno y orden de ejecución de las fases: [`docs/COMO_CORRER.md`](docs/COMO_CORRER.md). Normas del pipeline: [`docs/SSoT.md`](docs/SSoT.md).

## Contacto

sidereotosca@gmail.com — abierto a trabajo remunerado en investigación cuantitativa, validación de modelos, MLOps e ingeniería de sistemas de trading.

## Licencia

MIT. Ver [`LICENSE`](LICENSE).
