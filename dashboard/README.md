# Dashboard en Excel

Archivo: `dashboard_accidentes_madrid.xlsx`

## Hojas
| Hoja | Contenido |
|---|---|
| **Resumen** | Indicadores (accidentes, personas, % graves o mortales, fallecidos a 24 h, accidentes por día, variación anual), evolución anual y gravedad. |
| **Temporal** | Mapa de calor día de la semana × hora, media por día de la semana, laborables / fines de semana / festivos, estaciones y accidentes por mes y año. |
| **Distritos** | Accidentes, personas y % de graves o mortales por distrito. |
| **Meteorología** | Día seco frente a lluvia, por intensidad de lluvia y por temperatura media. |
| **Léeme** | Instrucciones, definiciones y limitaciones. |
| **Datos_diarios · Datos_hora · Datos_distrito** | Tablas base (calculadas con Python a partir del dataset final). El resto del libro son fórmulas sobre ellas. |

## Cómo usarlo
- En Resumen, Temporal y Distritos, elige un año (o «Todos») en la **celda amarilla**: las tablas y los gráficos se actualizan.
- No modifiques la celda gris pequeña de «criterio interno».

## Cómo se construyó
1. Con los notebooks se obtiene `data/processed/accidentes_meteo_madrid.csv` (271.250 filas × 47 columnas) y un fichero diario con la meteorología y los festivos.
2. De ese dataset se agregan tres tablas base: por día, por día de la semana × hora × año y por distrito × año.
3. Las hojas del dashboard calculan todo con fórmulas (`SUMIFS`, `COUNTIFS`, `AVERAGEIFS`) sobre esas tablas; el mapa de calor usa formato condicional de escala de color.

## Definiciones
- **Accidente:** `num_expediente` distinto. **Persona implicada:** una fila del fichero.
- **Grave o mortal:** lesividad 3 (ingreso de más de 24 h) o 4 (fallecido a 24 h). El % se calcula solo sobre las personas con lesividad conocida (≈ 55 % del total).
- **Lluvia:** precipitación diaria > 0,1 mm (estación Madrid-Retiro, AEMET).
- **Festivo:** festivo nacional o de la Comunidad de Madrid según la librería `holidays`.

## Limitaciones
- Una sola estación meteorológica; la lluvia es diaria, no horaria.
- 91 días sin dato de precipitación y 20 sin temperatura se excluyen de la hoja de Meteorología.
- 4 accidentes sin distrito quedan fuera de la hoja Distritos.
- Las medias del Excel son descriptivas; el efecto ajustado (por ejemplo, festivos con IRR = 0,62 o lluvia con IRR = 1,046) está en el notebook 03.
