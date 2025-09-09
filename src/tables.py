
import pandas as pd
from typing import Optional

def freq(df: pd.DataFrame, var: str, weight: Optional[str] = None) -> pd.DataFrame:
    x = df.dropna(subset=[var])
    if weight and weight in x.columns:
        s = x.groupby(var)[weight].sum()
        total = s.sum()
        pct = 100 * s / total if total else s * 0
        out = pd.DataFrame({"n": s, "%": pct}).reset_index().sort_values("n", ascending=False)
    else:
        s = x[var].value_counts(dropna=False)
        total = s.sum()
        pct = 100 * s / total if total else s * 0
        out = pd.DataFrame({var: s.index, "n": s.values, "%": pct.values})
    return out

def crosstab(df: pd.DataFrame, row: str, col: str, weight: Optional[str] = None, normalize: Optional[str] = "index") -> pd.DataFrame:
    x = df.dropna(subset=[row, col])
    if weight and weight in x.columns:
        # weighted crosstab
        pivot = x.pivot_table(index=row, columns=col, values=weight, aggfunc="sum", fill_value=0)
    else:
        pivot = pd.crosstab(x[row], x[col], dropna=False)
    if normalize == "index":
        pct = pivot.div(pivot.sum(axis=1).replace(0, 1), axis=0) * 100
        return pct.round(2)
    elif normalize == "columns":
        pct = pivot.div(pivot.sum(axis=0).replace(0, 1), axis=1) * 100
        return pct.round(2)
    else:
        return pivot
