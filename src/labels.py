
import pandas as pd
from typing import Dict, List, Optional

def _canonicalize_var_name(name: str, df_cols: Optional[List[str]] = None) -> str:
    if df_cols:
        target = str(name).strip().lower()
        for c in df_cols:
            if str(c).strip().lower() == target:
                return c
    return str(name)

def normalize_codebook(df_cb: pd.DataFrame, df_columns: Optional[List[str]] = None) -> pd.DataFrame:
    if df_cb is None or df_cb.empty:
        return pd.DataFrame(columns=["variable","value","value_str","label_value","label_variable"])
    cols = {c.lower(): c for c in df_cb.columns}
    var_col = cols.get("variable") or cols.get("var") or list(df_cb.columns)[0]
    val_col = cols.get("value") or cols.get("valor") or list(df_cb.columns)[1]
    lab_val_col = cols.get("label_value") or cols.get("etiqueta_valor") or cols.get("etiqueta") or list(df_cb.columns)[2]
    lab_var_col = cols.get("label_variable") or cols.get("etiqueta_variable") or (list(df_cb.columns)[3] if len(df_cb.columns) > 3 else lab_val_col)

    for c in [var_col, val_col, lab_val_col, lab_var_col]:
        if c not in df_cb.columns:
            df_cb[c] = None

    out = df_cb[[var_col, val_col, lab_val_col, lab_var_col]].copy()
    out.columns = ["variable","value","label_value","label_variable"]
    out["variable"] = out["variable"].astype(str).str.strip()
    out["variable"] = out["variable"].apply(lambda v: _canonicalize_var_name(v, df_columns))
    out["value_str"] = out["value"].astype(str).str.strip()
    return out[["variable","value","value_str","label_value","label_variable"]]

def build_label_maps(df_cb: pd.DataFrame, df_columns: Optional[List[str]] = None) -> (Dict[str, str], Dict[str, Dict]):
    cb = normalize_codebook(df_cb, df_columns=df_columns)
    var_labels = {}
    for var, lab in cb[["variable","label_variable"]].dropna().drop_duplicates("variable").itertuples(index=False):
        s = str(lab).strip()
        if s and s.lower() != "nan":
            var_labels[str(var)] = s

    val_labels: Dict[str, Dict] = {}
    for var, g in cb.groupby("variable"):
        sub = g.dropna(subset=["value","label_value"])
        if sub.empty:
            continue
        mapping = {}
        for _, row in sub.iterrows():
            lv = str(row["label_value"]).strip()
            if not lv or lv.lower() == "nan":
                continue
            mapping[str(row["value_str"])] = lv
            try:
                vi = int(float(row["value"]))
                mapping[vi] = lv
            except Exception:
                pass
            try:
                vf = float(row["value"])
                mapping[vf] = lv
            except Exception:
                pass
        if mapping:
            val_labels[str(var)] = mapping
    return var_labels, val_labels

def apply_value_labels(df: pd.DataFrame, val_labels: Dict[str, Dict]) -> pd.DataFrame:
    if not val_labels:
        return df
    out = df.copy()
    for var, mapping in val_labels.items():
        if var in out.columns:
            orig = out[var]
            mapped = orig.map(mapping)
            mapped2 = orig.astype(str).map(mapping)
            combined = mapped.where(mapped.notna(), mapped2)
            out[var] = combined.where(combined.notna(), orig)
    return out
