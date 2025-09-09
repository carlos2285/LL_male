
import json
import pandas as pd
import streamlit as st
import pydeck as pdk
from pathlib import Path

from src.io import read_data, read_codebook, read_geojson
from src.labels import build_label_maps, apply_value_labels
from src.tables import freq, crosstab
from src.map_layers import scatter_points, polygons_layer

st.set_page_config(page_title="Encuesta Dashboard", layout="wide")

# -------- Config --------
CFG_PATH = Path("config/settings.yaml")
TAB_PATH = Path("config/tabulados.yaml")

import yaml
with open(CFG_PATH, "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

# -------- Load data --------
@st.cache_data(show_spinner=False)
def load_all():
    df = read_data(CFG["data_path"])
    cb = read_codebook(CFG["codebook_path"])
    var_labels, val_labels = build_label_maps(cb)
    geojson_polys = read_geojson(CFG["polygons_path"])
    return df, var_labels, val_labels, geojson_polys

df, var_labels, val_labels, geojson_polys = load_all()

# -------- Apply value labels (without renaming columns) --------
df_labeled = apply_value_labels(df, val_labels)

# -------- Sidebar filters --------
st.sidebar.header("Filtros")

key_filter_col = CFG.get("key_filter_col")
available_cols = list(df_labeled.columns)

if key_filter_col not in available_cols:
    # pick a categorical-like column as fallback
    nunique = df_labeled.nunique(dropna=True)
    cand = nunique[(nunique >= 3) & (nunique <= 30)].sort_values(ascending=False)
    key_filter_col = cand.index[0] if len(cand) > 0 else available_cols[0]

st.sidebar.markdown("**Filtro global**")
values = sorted([v for v in df_labeled[key_filter_col].dropna().unique().tolist()])
selected_values = st.sidebar.multiselect(f"{var_labels.get(key_filter_col, key_filter_col)}", values, default=values[:5])

mask = df_labeled[key_filter_col].isin(selected_values) if selected_values else pd.Series([True]*len(df_labeled))
df_f = df_labeled[mask].copy()

# Optional extra filters: pick up to 3 low-cardinality columns
nunique = df_f.nunique(dropna=True).sort_values()
cand_filters = [c for c in nunique.index if 2 <= nunique[c] <= 10 and c != key_filter_col][:3]

for c in cand_filters:
    vals = sorted([v for v in df_f[c].dropna().unique().tolist()])
    sel = st.sidebar.multiselect(var_labels.get(c, c), vals, default=[])
    if sel:
        df_f = df_f[df_f[c].isin(sel)]

# -------- Header --------
st.title("Encuesta Dashboard")
st.caption("Datos filtrados por tu selección en la barra lateral.")

# -------- KPIs --------
col1, col2, col3 = st.columns(3)
col1.metric("Registros (n)", f"{len(df_f):,}")
w_col = CFG.get("weight_col")
if w_col and w_col in df_f.columns:
    total_w = df_f[w_col].sum()
    col2.metric("Suma de pesos", f"{total_w:,.2f}")
else:
    col2.metric("Suma de pesos", "—")

unique_key = df_f[key_filter_col].nunique() if key_filter_col in df_f.columns else 0
col3.metric(f"#{var_labels.get(key_filter_col, key_filter_col)}", f"{unique_key:,}")

st.divider()

# -------- Plan de tabulados --------
with open(TAB_PATH, "r", encoding="utf-8") as f:
    TAB = yaml.safe_load(f)

st.header("Plan de tabulados")
for group in TAB.get("tabulados", []):
    st.subheader(group.get("name", "Grupo"))
    for spec in group.get("tables", []):
        if "freq" in spec:
            v = spec["freq"]
            if v in df_f.columns:
                st.markdown(f"**Frecuencia:** {var_labels.get(v, v)}")
                st.dataframe(freq(df_f, v, weight=w_col))
        elif "crosstab" in spec:
            row = spec["crosstab"].get("row")
            col = spec["crosstab"].get("col")
            w  = spec["crosstab"].get("weight") or w_col
            if row in df_f.columns and col in df_f.columns:
                st.markdown(f"**Crosstab:** {var_labels.get(row, row)} × {var_labels.get(col, col)}")
                st.dataframe(crosstab(df_f, row, col, weight=w, normalize="index"))

st.divider()

# -------- Mapa --------
st.header("Mapa (pydeck)")
lat_col = CFG.get("lat_col")
lon_col = CFG.get("lon_col")

initial_view = pdk.ViewState(latitude=13.7, longitude=-89.2, zoom=8)  # ES general
layers = []

poly_layer = polygons_layer(geojson_polys)
if poly_layer:
    layers.append(poly_layer)

pt_layer = scatter_points(df_f, lat_col, lon_col)
if pt_layer:
    layers.append(pt_layer)

if layers:
    tooltip = {"text": f"{key_filter_col}: {{{{ {key_filter_col} }}}}"}
    st.pydeck_chart(pdk.Deck(map_style="mapbox://styles/mapbox/light-v9", initial_view_state=initial_view, layers=layers, tooltip=tooltip))
else:
    st.info("No hay capas cargadas. Asegúrate de configurar lat/lon y subir polygons.geojson.")
