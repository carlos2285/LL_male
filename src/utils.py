
import streamlit as st

def cache_data(func):
    return st.cache_data(show_spinner=False)(func)
