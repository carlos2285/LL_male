
import pandas as pd
from typing import Dict, Optional

def normalize_codebook(df_cb: pd.DataFrame) -> pd.DataFrame:
    # Intentar encontrar columnas clave en diversos formatos
    cols = {c.lower(): c for c in df_cb.columns}
    var_col = cols.get("variable") or cols.get("var") or "variable"
    val_col = cols.get("value") or cols.get("valor") or "value"
    lab_val_col = cols.get("label_value") or cols.get("etiqueta_valor") or cols.get("etiqueta") or "label_value"
    lab_var_col = cols.get("label_variable") or cols.get("etiqueta_variable") or "label_variable"

    # Si faltan, crear por defecto
    for c in [var_col, val_col, lab_val_col, lab_var_col]:
        if c not in df_cb.columns:
            df_cb[c] = None

    out = df_cb[[var_col, val_col, lab_val_col, lab_var_col]].copy()
    out.columns = ["variable", "value", "label_value", "label_variable"]
    return out

def build_label_maps(df_cb: pd.DataFrame) -> (Dict[str, str], Dict[str, Dict]):
    cb = normalize_codebook(df_cb)
    # Mapa de etiquetas de variables
    var_labels = (
        cb.dropna(subset=["variable", "label_variable"])
          .drop_duplicates(subset=["variable"])
          .set_index("variable")["label_variable"].to_dict()
    )
    # Mapa de etiquetas de valores por variable
    val_labels = {}
    for var, g in cb.dropna(subset=["variable"]).groupby("variable"):
        sub = g.dropna(subset=["value", "label_value"])
        if not sub.empty:
            # cohercion de 'value' a string para evitar problemas
            val_labels[var] = {str(row["value"]): str(row["label_value"]) for _, row in sub.iterrows()}
    return var_labels, val_labels

def apply_value_labels(df: pd.DataFrame, val_labels: Dict[str, Dict]) -> pd.DataFrame:
    out = df.copy()
    for var, mapping in val_labels.items():
        if var in out.columns:
            # map por str para ser robustos ante tipos
            out[var] = out[var].astype(str).map(mapping).fillna(out[var].astype(str))
    return out
