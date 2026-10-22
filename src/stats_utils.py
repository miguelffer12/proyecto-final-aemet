"""Contrastes y medidas de efecto."""
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportion_confint


def cramers_v(table: pd.DataFrame) -> float:
    chi2 = stats.chi2_contingency(table, correction=False)[0]
    n = table.values.sum()
    k = min(table.shape) - 1
    return float(np.sqrt(chi2 / (n * k)))


def chi2_report(df: pd.DataFrame, a: str, b: str) -> dict:
    t = pd.crosstab(df[a], df[b])
    chi2, p, dof, expected = stats.chi2_contingency(t)
    return {"chi2": chi2, "p": p, "gl": dof, "V_cramer": cramers_v(t),
            "min_esperada": float(expected.min()), "tabla": t}


def kruskal_report(groups: list[np.ndarray]) -> dict:
    h, p = stats.kruskal(*groups)
    n = sum(len(g) for g in groups)
    k = len(groups)
    eps2 = (h - k + 1) / (n - k)        # epsilon² (tamaño de efecto)
    return {"H": h, "p": p, "epsilon2": eps2}


def mannwhitney_report(x, y) -> dict:
    u, p = stats.mannwhitneyu(x, y, alternative="two-sided")
    r = 1 - 2 * u / (len(x) * len(y))   # rank-biserial
    return {"U": u, "p": p, "rank_biserial": r}


def prop_ci(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float, float]:
    lo, hi = proportion_confint(successes, n, alpha=alpha, method="wilson")
    return successes / n, lo, hi
