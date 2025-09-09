
import pandas as pd
import json
from pathlib import Path

def read_data(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No se encuentra el archivo de datos: {path}")
    try:
        return pd.read_csv(p, low_memory=False)
    except Exception:
        try:
            return pd.read_csv(p, encoding="utf-8-sig", low_memory=False)
        except Exception:
            return pd.read_csv(p, encoding="latin-1", low_memory=False)

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
        # retornar vacío
        return {"type": "FeatureCollection", "features": []}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
