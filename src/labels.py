
import pandas as pd
from typing import Dict

def normalize_codebook(df_cb: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df_cb.columns}
    var_col = cols.get("variable") or cols.get("var") or list(df_cb.columns)[0]
    val_col = cols.get("value") or cols.get("valor") or list(df_cb.columns)[1]
    lab_val_col = cols.get("label_value") or cols.get("etiqueta_valor") or cols.get("etiqueta") or list(df_cb.columns)[2]
    lab_var_col = cols.get("label_variable") or cols.get("etiqueta_variable") or (list(df_cb.columns)[3] if len(df_cb.columns) > 3 else lab_val_col)

    for c in [var_col, val_col, lab_val_col, lab_var_col]:
        if c not in df_cb.columns:
            df_cb[c] = None

    out = df_cb[[var_col, val_col, lab_val_col, lab_var_col]].copy()
    out.columns = ["variable", "value", "label_value", "label_variable"]
    return out

def build_label_maps(df_cb: pd.DataFrame) -> (Dict[str, str], Dict[str, Dict]):
    cb = normalize_codebook(df_cb)
    var_labels = (
        cb.dropna(subset=["variable", "label_variable"])
          .drop_duplicates(subset=["variable"])
          .set_index("variable")["label_variable"].to_dict()
    )
    val_labels = {}
    for var, g in cb.dropna(subset=["variable"]).groupby("variable"):
        sub = g.dropna(subset=["value", "label_value"])
        if not sub.empty:
            val_labels[var] = {str(r['value']): str(r['label_value']) for _, r in sub.iterrows()}
    return var_labels, val_labels

def apply_value_labels(df: pd.DataFrame, val_labels: Dict[str, Dict]) -> pd.DataFrame:
    out = df.copy()
    for var, mapping in val_labels.items():
        if var in out.columns:
            out[var] = out[var].astype(str).map(mapping).fillna(out[var].astype(str))
    return out
