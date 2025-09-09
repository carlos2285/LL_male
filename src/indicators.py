
import re
import pandas as pd
import yaml
from pathlib import Path

def load_rules(path: str):
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("rules", {})

def pct_true(mask: pd.Series) -> float:
    denom = len(mask)
    if denom == 0:
        return float("nan")
    return round(100.0 * (mask.sum() / denom), 2)

def compute_indicators(df: pd.DataFrame, rules: dict) -> dict:
    out = {}
    for k, spec in rules.items():
        var = spec.get("var")
        if var not in df.columns:
            out[k] = None
            continue
        s = df[var].astype(str).str.lower()
        if "label_regex_any" in spec:
            pats = spec["label_regex_any"]
            mask = s.apply(lambda x: any(re.search(p, x) for p in pats))
            out[k] = pct_true(mask)
        elif "threshold" in spec:
            try:
                vals = pd.to_numeric(df[var], errors="coerce").fillna(0)
                mask = vals >= float(spec["threshold"])
                out[k] = pct_true(mask)
            except Exception:
                out[k] = None
        else:
            out[k] = None
    return out
