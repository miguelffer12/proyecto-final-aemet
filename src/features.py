"""Variables derivadas."""
import numpy as np
import pandas as pd
import holidays

from .config import GRAVES, ORDEN_GRAVEDAD

ESTACION = {12: "invierno", 1: "invierno", 2: "invierno", 3: "primavera", 4: "primavera",
            5: "primavera", 6: "verano", 7: "verano", 8: "verano", 9: "otoño", 10: "otoño", 11: "otoño"}
DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["anio"] = d["fecha"].dt.year
    d["mes"] = d["fecha"].dt.month
    d["dia_semana"] = d["fecha"].dt.dayofweek.map(dict(enumerate(DIAS)))
    d["es_fin_semana"] = (d["fecha"].dt.dayofweek >= 5).astype(int)
    d["estacion"] = d["mes"].map(ESTACION)
    years = range(int(d["anio"].min()), int(d["anio"].max()) + 1)
    fest = holidays.Spain(subdiv="MD", years=years)
    d["es_festivo"] = d["fecha"].dt.date.map(lambda x: x in fest).astype(int)
    d["franja_horaria"] = pd.cut(d["hora_num"], bins=[-1, 5, 11, 19, 23],
                                 labels=["madrugada", "mañana", "tarde", "noche"]).astype("string")
    return d


def add_weather_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["lluvia"] = (d["meteo_prec"] > 0.1).astype("Int64").where(d["meteo_prec"].notna())
    d["intensidad_lluvia"] = pd.cut(d["meteo_prec"], bins=[-0.01, 0.1, 2, 10, np.inf],
                                    labels=["seco", "debil", "moderada", "fuerte"]).astype("string")
    d["rango_termico"] = d["meteo_tmax"] - d["meteo_tmin"]
    d["categoria_temp"] = pd.cut(d["meteo_tmed"], bins=[-np.inf, 5, 15, 25, np.inf],
                                 labels=["frio", "fresco", "templado", "calido"]).astype("string")
    return d


def add_accident_level_features(df: pd.DataFrame) -> pd.DataFrame:
    """El fichero tiene 1 fila por persona implicada; añadimos agregados por accidente."""
    d = df.copy()
    d["n_implicados"] = d.groupby("num_expediente")["num_expediente"].transform("size")
    rank = {g: i for i, g in enumerate(ORDEN_GRAVEDAD)}
    d["gravedad_orden"] = d["gravedad"].map(rank)
    d["gravedad_max_accidente"] = d.groupby("num_expediente")["gravedad_orden"].transform("max") \
        .map(dict(enumerate(ORDEN_GRAVEDAD)))
    d["es_grave"] = d["gravedad"].isin(GRAVES).astype(int)
    d["accidente_con_grave"] = d["gravedad_max_accidente"].isin(GRAVES).astype(int)
    return d


def collapse_top(s: pd.Series, n: int = 6, other: str = "otros") -> pd.Series:
    top = s.value_counts().nlargest(n).index
    return s.where(s.isin(top), other)
