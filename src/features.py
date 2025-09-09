
import pandas as pd
from typing import Optional, List

CANDIDATE_JEFE_SEXO = [
    "sexo_jefatura", "sexo_jefe", "jefe_sexo", "sexo_jefehogar",
    "sexo_jefatura_hogar", "p010_sexo_jefatura", "p010_sexo_jefe"
]

def derive_sexo_jefatura(df: pd.DataFrame) -> pd.Series:
    # If there's already a column for sexo de la jefatura
    for c in CANDIDATE_JEFE_SEXO:
        if c in df.columns:
            return df[c]
    # Heurísticas mínimas: si existe columna 'jefatura' con valores tipo 'F/M' o etiquetas
    for c in df.columns:
        lc = c.lower()
        if "jef" in lc and "sexo" in lc:
            return df[c]
    # Sin información fiable, devolvemos NaN
    return pd.Series([None]*len(df), index=df.index, dtype="object")

def apply_all(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "sexo_jefatura" not in out.columns:
        out["sexo_jefatura"] = derive_sexo_jefatura(out)
    return out
