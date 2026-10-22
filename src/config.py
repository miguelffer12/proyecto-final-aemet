"""Rutas y constantes del proyecto."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"

RAW_ACCIDENTES = RAW / "accidentes_madrid"   # CSV anuales del Ayuntamiento de Madrid
RAW_AEMET = RAW / "aemet_retiro"             # Climatología diaria AEMET (CSV o JSON)

ACCIDENTES_CLEAN = INTERIM / "accidentes_limpio.csv"
METEO_CLEAN = INTERIM / "meteo_limpio.csv"
FINAL_CSV = PROCESSED / "accidentes_meteo_madrid.csv"

# Código de lesividad -> categoría de gravedad.
# Verificado contra los CSV 2019-2024 (cod_lesividad vs texto de lesividad).
# Nulo en cod_lesividad (~43 % de filas) se trata como 77 = desconocido.
LESIVIDAD_A_GRAVEDAD = {
    14: "ileso",       # sin asistencia sanitaria
    1: "leve",         # urgencias sin ingreso
    5: "leve",         # asistencia ambulatoria con posterioridad
    6: "leve",         # asistencia inmediata en centro de salud o mutua
    7: "leve",         # asistencia sanitaria solo en el lugar del accidente
    2: "moderado",     # ingreso <= 24 h
    3: "grave",        # ingreso > 24 h
    4: "mortal",       # fallecido en las 24 h siguientes
    77: "desconocido",
}
ORDEN_GRAVEDAD = ["desconocido", "ileso", "leve", "moderado", "grave", "mortal"]
GRAVES = {"grave", "mortal"}

FRANJAS = {"madrugada": (0, 6), "mañana": (6, 12), "tarde": (12, 20), "noche": (20, 24)}
