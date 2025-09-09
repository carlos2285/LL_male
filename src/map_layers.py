
import pydeck as pdk
import pandas as pd

def scatter_points(df: pd.DataFrame, lat_col: str, lon_col: str, get_fill_color="[0, 128, 255]"):
    if lat_col not in df.columns or lon_col not in df.columns:
        return None
    pts = df.dropna(subset=[lat_col, lon_col])
    if pts.empty:
        return None
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=pts,
        get_position=[lon_col, lat_col],
        get_radius=50,
        pickable=True,
        radius_min_pixels=3,
        radius_max_pixels=10,
        get_fill_color=get_fill_color,
    )
    return layer

def polygons_layer(geojson_obj: dict):
    if not geojson_obj or not geojson_obj.get("features"):
        return None
    layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson_obj,
        pickable=True,
        stroked=True,
        filled=False,
        get_line_color=[0, 0, 0],
        get_line_width=2,
    )
    return layer
