
import pandas as pd
import json
from pathlib import Path

def read_data(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No se encuentra el archivo de datos: {path}")
    for enc in [None, "utf-8-sig", "latin-1"]:
        try:
            return pd.read_csv(p, encoding=enc, low_memory=False)
        except Exception:
            continue
    raise RuntimeError(f"No pude leer {path}")

def read_codebook(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No se encuentra el codebook: {path}")
    if p.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(p, sheet_name=0)
    else:
        return pd.read_csv(p)

def read_geojson(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
