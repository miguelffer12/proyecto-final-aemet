"""Carga y limpieza de las dos fuentes en bruto."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from .config import LESIVIDAD_A_GRAVEDAD


# ---------- utilidades generales ----------
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """minúsculas, sin tildes, espacios -> '_'."""
    cols = [re.sub(r"\W+", "_", strip_accents(str(c)).strip().lower()).strip("_") for c in df.columns]
    out = df.copy()
    out.columns = cols
    return out


def normalize_text(s: pd.Series) -> pd.Series:
    """strip, minúsculas, sin tildes, espacios colapsados; vacíos -> NaN."""
    out = s.astype("string").str.strip().str.lower()
    out = out.map(lambda x: strip_accents(x) if isinstance(x, str) else x)
    out = out.str.replace(r"\s+", " ", regex=True)
    return out.replace({"": pd.NA, "nan": pd.NA, "null": pd.NA})


def read_csv_robust(path: Path) -> pd.DataFrame:
    """Prueba varias codificaciones y detecta el separador. Todo como texto."""
    last = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, sep=None, engine="python", encoding=enc, dtype=str)
        except UnicodeDecodeError as e:
            last = e
    raise last


def to_float(s: pd.Series) -> pd.Series:
    """Texto con coma decimal -> float."""
    return pd.to_numeric(s.astype("string").str.replace(",", ".", regex=False).str.strip(), errors="coerce")


def parse_dates(s: pd.Series, dayfirst: bool = True) -> pd.Series:
    """Primero formatos habituales; lo que falle, parseo flexible."""
    s = s.astype("string").str.strip()
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        mask = out.isna() & s.notna()
        if not mask.any():
            break
        out[mask] = pd.to_datetime(s[mask], format=fmt, errors="coerce")
    mask = out.isna() & s.notna()
    if mask.any():
        out[mask] = pd.to_datetime(s[mask], format="mixed", dayfirst=dayfirst, errors="coerce")
    return out


# ---------- Fuente A: accidentes Madrid ----------
def load_accidentes(folder: Path) -> pd.DataFrame:
    files = sorted(Path(folder).glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No hay CSV en {folder}")
    frames = []
    for f in files:
        d = standardize_columns(read_csv_robust(f))
        d["archivo_origen"] = f.name
        frames.append(d)
        print(f"{f.name}: {d.shape[0]:,} filas, {d.shape[1]} columnas")
    cols = [set(d.columns) for d in frames]
    if any(c != cols[0] for c in cols):
        print("AVISO: los archivos no comparten el mismo esquema de columnas:")
        for f, d in zip(files, frames):
            print("  ", f.name, sorted(set(d.columns) ^ cols[0]))
    return pd.concat(frames, ignore_index=True, sort=False)


def clean_accidentes(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    log = {"filas_iniciales": len(df)}
    d = df.copy()

    # filas idénticas: NO se eliminan. El CSV no trae identificador de persona y
    # las filas idénticas suelen ser personas distintas del mismo accidente
    # (varios pasajeros del mismo tipo, conductores desconocidos...).
    log["filas_identicas_conservadas"] = int(d.duplicated().sum())

    # fecha y hora
    d["fecha"] = parse_dates(d["fecha"])
    log["fechas_no_parseables"] = int(d["fecha"].isna().sum())
    d = d.dropna(subset=["fecha"])
    if "hora" in d.columns:
        h = pd.to_numeric(d["hora"].astype("string").str.extract(r"(\d{1,2})")[0], errors="coerce")
        d["hora_num"] = h.where(h.between(0, 23))
        log["horas_invalidas"] = int(d["hora_num"].isna().sum())

    # texto categórico
    text_cols = ["distrito", "tipo_accidente", "estado_meteorologico", "tipo_vehiculo",
                 "tipo_persona", "rango_edad", "sexo", "lesividad", "positiva_alcohol",
                 "positiva_droga", "localizacion"]
    for c in text_cols:
        if c in d.columns:
            d[c] = normalize_text(d[c])
    if "num_expediente" in d.columns:
        d["num_expediente"] = d["num_expediente"].astype("string").str.strip()

    # sexo
    if "sexo" in d.columns:
        d["sexo"] = d["sexo"].replace({"varon": "hombre", "masculino": "hombre", "femenino": "mujer"})
        d.loc[~d["sexo"].isin(["hombre", "mujer"]), "sexo"] = "desconocido"

    # alcohol -> 1/0/NaN (S/N; nulo = sin dato)
    if "positiva_alcohol" in d.columns:
        d["positiva_alcohol"] = d["positiva_alcohol"].map({"s": 1, "si": 1, "n": 0, "no": 0}).astype("float")
    # droga: en el CSV solo aparece "1" (positivo) o nulo. Nulo = no positivo o sin prueba.
    if "positiva_droga" in d.columns:
        d["positiva_droga"] = d["positiva_droga"].map({"1": 1, "s": 1, "si": 1}).fillna(0).astype(int)

    # coordenadas UTM (coma decimal, ceros = faltante)
    for c in ("coordenada_x_utm", "coordenada_y_utm"):
        if c in d.columns:
            d[c] = to_float(d[c]).replace(0, np.nan)

    # lesividad -> gravedad
    d["cod_lesividad"] = pd.to_numeric(d.get("cod_lesividad"), errors="coerce")
    d["cod_lesividad"] = d["cod_lesividad"].fillna(77).astype(int)
    d["gravedad"] = d["cod_lesividad"].map(LESIVIDAD_A_GRAVEDAD).fillna("desconocido")
    log["codigos_lesividad_sin_mapear"] = sorted(
        set(d["cod_lesividad"]) - set(LESIVIDAD_A_GRAVEDAD))

    # nulos tras limpieza (para auditar y justificar)
    log["nulos_pct"] = (d.isna().mean() * 100).round(2).sort_values(ascending=False).to_dict()
    log["filas_finales"] = len(d)
    return d.reset_index(drop=True), log


# ---------- Fuente B: AEMET ----------
def load_aemet(folder: Path) -> pd.DataFrame:
    files = sorted(list(Path(folder).glob("*.csv")) + list(Path(folder).glob("*.json")))
    if not files:
        raise FileNotFoundError(f"No hay CSV/JSON en {folder}")
    frames = []
    for f in files:
        d = pd.read_json(f, dtype=str) if f.suffix == ".json" else read_csv_robust(f)
        frames.append(standardize_columns(d))
        print(f"{f.name}: {len(d):,} filas")
    return pd.concat(frames, ignore_index=True, sort=False)


def clean_aemet(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    log = {"filas_iniciales": len(df)}
    d = df.copy()
    d["fecha"] = parse_dates(d["fecha"], dayfirst=False)
    d = d.dropna(subset=["fecha"])
    n0 = len(d)
    d = d.drop_duplicates(subset="fecha", keep="last")
    log["fechas_duplicadas_eliminadas"] = n0 - len(d)

    # precipitación: "Ip" = inapreciable (<0,1 mm); "Acum" = acumulada en otro día
    if "prec" in d.columns:
        p = d["prec"].astype("string").str.strip()
        d["prec_inapreciable"] = (p.str.lower() == "ip").fillna(False).astype(int)
        d["prec"] = to_float(p.replace({"Ip": "0", "ip": "0"}))
        log["prec_nula_o_acum"] = int(d["prec"].isna().sum())

    numeric = ["tmed", "tmin", "tmax", "velmedia", "racha", "sol", "presmax", "presmin", "dir"]
    for c in numeric:
        if c in d.columns:
            d[c] = to_float(d[c])

    # incoherencias físicas
    if {"tmin", "tmax"} <= set(d.columns):
        bad = d["tmin"] > d["tmax"]
        log["tmin_mayor_que_tmax"] = int(bad.sum())
        d.loc[bad, ["tmin", "tmax"]] = np.nan

    keep = ["fecha"] + [c for c in ["tmed", "tmin", "tmax", "prec", "prec_inapreciable",
                                     "velmedia", "racha", "sol", "presmax", "presmin"] if c in d.columns]
    d = d[keep].sort_values("fecha").reset_index(drop=True)
    d = d.rename(columns={c: f"meteo_{c}" for c in d.columns if c != "fecha"})

    # huecos en el calendario
    full = pd.date_range(d["fecha"].min(), d["fecha"].max(), freq="D")
    log["dias_sin_registro"] = int(len(full) - len(d))
    log["nulos_pct"] = (d.isna().mean() * 100).round(2).to_dict()
    log["filas_finales"] = len(d)
    return d, log


# ---------- Unión ----------
def merge_accidentes_meteo(acc: pd.DataFrame, meteo: pd.DataFrame) -> pd.DataFrame:
    """Left join por fecha (muchos accidentes -> un día). Valida que no se pierdan ni dupliquen filas."""
    n = len(acc)
    out = acc.merge(meteo, on="fecha", how="left", validate="m:1")
    assert len(out) == n, f"El merge cambió el nº de filas: {n} -> {len(out)}"
    sin_meteo = out["meteo_tmed"].isna().mean() * 100 if "meteo_tmed" in out else float("nan")
    print(f"Filas: {n:,} -> {len(out):,} | sin dato meteorológico: {sin_meteo:.2f}%")
    return out
