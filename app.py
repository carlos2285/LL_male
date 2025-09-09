
import json
import pandas as pd
import streamlit as st
import pydeck as pdk
from pathlib import Path

from src.io import read_data, read_codebook, read_geojson
from src.labels import build_label_maps, apply_value_labels
from src.tables import freq, crosstab, summarize_numeric, crosstab_binned
from src.map_layers import scatter_points, polygons_layer
from src.features import apply_all
from src.indicators import compute_indicators

# ---- YAML import (no dynamic pip inside cached funcs). If missing, show friendly error and stop.
try:
    import yaml
except Exception as e:
    yaml = None

def _require_yaml():
    if yaml is None:
        st.error("Falta la dependencia **PyYAML**. Agrega `pyyaml` a `requirements.txt` en la raíz del repo y reinicia la app (Manage → Restart).")
        st.stop()

def _safe_label(var_labels, key):
    val = var_labels.get(key, key)
    try:
        s = str(val)
    except Exception:
        s = key if isinstance(key, str) else repr(key)
    if s.lower() == "nan":
        s = key if isinstance(key, str) else repr(key)
    return s

# ---- UI helpers seguros ----
def _safe_text(x):
    try:
        s = str(x)
    except Exception:
        s = repr(x)
    if s.lower() == "nan":
        return ""
    return s

def ui_multiselect(label, options, default=None, key=None):
    label_s = _safe_text(label)
    opts = list(options) if options is not None else []
    default = list(default) if default else []
    return st.sidebar.multiselect(label_s, opts, default=default, key=key)

def ui_selectbox(label, options, index=0, key=None):
    label_s = _safe_text(label)
    opts = list(options) if options is not None else []
    if not opts:
        opts = ["—"]
        index = 0
    return st.selectbox(label_s, opts, index=min(index, len(opts)-1), key=key)

st.set_page_config(page_title="Encuesta Dashboard", layout="wide")

# --- Load settings and tabs ---
_require_yaml()
CFG_PATH = Path("config/settings.yaml")
TAB_PATH = Path("config/tabulados.yaml")

with open(CFG_PATH, "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

@st.cache_data(show_spinner=False)
def load_all(CFG):
    df = read_data(CFG["data_path"])
    cb = read_codebook(CFG["codebook_path"])
    var_labels, val_labels = build_label_maps(cb, df_columns=list(df.columns))
    geojson_polys = read_geojson(CFG["polygons_path"])
    return df, var_labels, val_labels, geojson_polys

df, var_labels, val_labels, geojson_polys = load_all(CFG)

# Apply labels and derived features
df_labeled = apply_value_labels(df, val_labels)
df_labeled = apply_all(df_labeled)
var_labels.setdefault('sexo_jefatura', 'Sexo de la jefatura')

# Sidebar filters
st.sidebar.header("Filtros")
key_filter_col = CFG.get("key_filter_col")
available_cols = list(df_labeled.columns)
if key_filter_col not in available_cols and available_cols:
    nunique = df_labeled.nunique(dropna=True)
    cand = nunique[(nunique >= 3) & (nunique <= 30)].sort_values(ascending=False)
    key_filter_col = cand.index[0] if len(cand) > 0 else available_cols[0]

if key_filter_col in df_labeled.columns:
    values = sorted([v for v in df_labeled[key_filter_col].dropna().unique().tolist()])
    selected_values = ui_multiselect(_safe_label(var_labels, key_filter_col), values, default=values[:5] if values else [], key="ms_sector")
    mask = df_labeled[key_filter_col].isin(selected_values) if selected_values else pd.Series(True, index=df_labeled.index)
else:
    st.sidebar.info("No se encontró columna de filtro global; usando todo el conjunto.")
    mask = pd.Series(True, index=df_labeled.index)

df_f = df_labeled[mask].copy()

# KPIs
st.title("Encuesta Dashboard")
st.caption("Filtros aplicados en la barra lateral.")
col1, col2, col3 = st.columns(3)
col1.metric("Registros (n)", f"{len(df_f):,}")
w_col = CFG.get("weight_col")
if w_col and w_col in df_f.columns:
    total_w = df_f[w_col].sum()
    col2.metric("Suma de pesos", f"{total_w:,.2f}")
else:
    col2.metric("Suma de pesos", "—")
if key_filter_col and key_filter_col in df_f.columns:
    col3.metric(f"#{_safe_label(var_labels, key_filter_col)}", f"{df_f[key_filter_col].nunique():,}")
else:
    col3.metric("#Grupos", "—")

# Indicators
from pathlib import Path as _P
IND_PATH = _P("config/indicators.yaml")
try:
    with open(IND_PATH, "r", encoding="utf-8") as _f:
        IND_RULES = yaml.safe_load(_f).get("rules", {})
except Exception:
    IND_RULES = {}
with st.expander("📌 Indicadores clave (editables en config/indicators.yaml)"):
    vals = compute_indicators(df_f, IND_RULES) if IND_RULES else {}
    if vals:
        cols = st.columns(min(4, len(vals)))
        i = 0
        for name, v in vals.items():
            col = cols[i % len(cols)]
            col.metric(name.replace("_", " ").title(), f"{v}%" if v is not None else "—")
            i += 1
    else:
        st.caption("Configura reglas en indicators.yaml para ver métricas.")

st.divider()
st.header("Plan de tabulados (oficial)")
with open(TAB_PATH, "r", encoding="utf-8") as f:
    PLAN = yaml.safe_load(f)

def apply_block_filter(df_in, spec: dict):
    if not spec:
        return df_in
    df_out = df_in.copy()
    # Exact equality lists
    if "in" in spec:
        for var, values in spec["in"].items():
            if var in df_out.columns:
                df_out = df_out[df_out[var].isin(values)]
    # Case-insensitive substring contains (for labeled/unlabeled values)
    if "in_text" in spec:
        for var, values in spec["in_text"].items():
            if var in df_out.columns:
                s = df_out[var].astype(str).str.lower()
                vals = [str(v).lower() for v in values]
                keep = s.apply(lambda x: any(v in x for v in vals))
                df_out = df_out[keep]
    if "eq" in spec:
        for var, value in spec["eq"].items():
            if var in df_out.columns:
                df_out = df_out[df_out[var] == value]
    return df_out

for block in PLAN.get("blocks", []):
    bname = block.get("name", "Bloque")
    st.subheader(bname)
    bfilter = block.get("filter", {})
    dblock = apply_block_filter(df_f, bfilter)
    if dblock.empty:
        st.info("Sin datos para este bloque con los filtros actuales.")
        continue
    for spec in block.get("tables", []):
        if "freq" in spec:
            v = spec["freq"]
            if v in dblock.columns:
                st.markdown(f"**Frecuencia:** {_safe_label(var_labels, v)}")
                st.dataframe(freq(dblock, v, weight=w_col))
        elif "crosstab" in spec:
            row = spec["crosstab"].get("row")
            col = spec["crosstab"].get("col")
            w  = spec["crosstab"].get("weight") or w_col
            if row in dblock.columns and col in dblock.columns:
                st.markdown(f"**Crosstab:** {_safe_label(var_labels, row)} × {_safe_label(var_labels, col)}")
                st.dataframe(crosstab_binned(dblock, row, col, weight=w, normalize="index"))
        elif "summary" in spec:
            v = spec["summary"].get("var")
            if v in dblock.columns:
                st.markdown(f"**Resumen:** {_safe_label(var_labels, v)}")
                st.dataframe(summarize_numeric(dblock, v, weight=w_col))

st.divider()
with st.expander("🔧 Diagnóstico de etiquetas"):
    df_cols = list(df.columns)
    labeled_vars = set(var_labels.keys())
    sin_etiqueta = [c for c in df_cols if c not in labeled_vars]
    st.write("Variables en la base:", len(df_cols))
    st.write("Con etiqueta:", len(labeled_vars), " | Sin etiqueta:", len(sin_etiqueta))
    if sin_etiqueta:
        st.write("Ejemplos sin etiqueta:", sin_etiqueta[:20])

st.divider()
st.header("Explorador de variables")
vars_sorted = sorted(df_f.columns)
labels_map = {v: _safe_label(var_labels, v) for v in vars_sorted}
reverse_map = {labels_map[v]: v for v in vars_sorted}
lab_options = sorted(reverse_map.keys())
sel_lab = ui_selectbox("Selecciona una variable", lab_options, index=0, key="explorador_var")
sel_var = reverse_map.get(sel_lab, vars_sorted[0] if vars_sorted else None)
if sel_var and sel_var in df_f.columns:
    st.markdown(f"**Frecuencia (Explorador):** {_safe_label(var_labels, sel_var)}")
    st.dataframe(freq(df_f, sel_var, weight=w_col))

st.divider()
st.header("Tabulado ad-hoc")
nunq_all = df_f.nunique(dropna=True) if not df_f.empty else df_labeled.nunique(dropna=True)
cat_vars = [c for c in nunq_all.index if 2 <= nunq_all[c] <= 20]
lab_cat = sorted([labels_map.get(c, c) for c in cat_vars])
row_lab = ui_selectbox("Fila (row)", lab_cat, key="adhoc_row")
col_lab = ui_selectbox("Columna (col)", lab_cat, key="adhoc_col")
row_var = reverse_map.get(row_lab)
col_var = reverse_map.get(col_lab)
peso_opts = ["(sin peso)"] + ([w_col] if w_col and w_col in df_f.columns else [])
peso_lab = ui_selectbox("Ponderación", peso_opts, key="adhoc_w")
peso_sel = None if peso_lab == "(sin peso)" else w_col
if row_var and col_var and row_var in df_f.columns and col_var in df_f.columns:
    st.markdown(f"**Crosstab ad-hoc:** {_safe_label(var_labels, row_var)} × {_safe_label(var_labels, col_var)}")
    st.dataframe(crosstab_binned(df_f, row_var, col_var, weight=peso_sel, normalize="index"))

st.divider()
st.header("Mapa (pydeck)")
lat_col = CFG.get("lat_col")
lon_col = CFG.get("lon_col")
initial_view = pdk.ViewState(latitude=13.7, longitude=-89.2, zoom=8)
layers = []
poly_layer = polygons_layer(geojson_polys)
if poly_layer:
    layers.append(poly_layer)
pt_layer = scatter_points(df_f, lat_col, lon_col)
if pt_layer:
    layers.append(pt_layer)
if layers:
    tooltip = {"text": f"{key_filter_col}: {{{ {key_filter_col} }}}"}
    st.pydeck_chart(pdk.Deck(map_style="mapbox://styles/mapbox/light-v9", initial_view_state=initial_view, layers=layers, tooltip=tooltip))
else:
    st.info("No hay capas cargadas. Sube polygons.geojson y verifica lat/lon en settings.yaml.")
