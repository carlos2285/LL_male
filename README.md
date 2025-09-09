
# Encuesta Dashboard (Streamlit Cloud-ready)

- Requiere `pyyaml` declarado en `requirements.txt` (no instalamos en caliente dentro de funciones cacheadas).
- Filtro global: `SECTOR` si existe en tus datos.
- Plan de tabulados oficial ya configurado en `config/tabulados.yaml` (bloques B–I).
- Explora todas las variables y arma cruces ad-hoc.

## Despliegue
1) Sube este repo a GitHub (mantén `app.py` y `requirements.txt` en la raíz).
2) En Streamlit Cloud, apunta a `app.py` y usa `requirements.txt`.
3) Si cambias dependencias: Manage app → Restart. Si persiste cache viejo: Clear cache.
