"""Clé de jointure géographique (identique à celle de build_data.py)."""
import re, unicodedata
import numpy as np

def cle_geo(s):
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return np.nan
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"[^A-Z0-9+]+", " ", s)
    s = re.sub(r"([A-Z])(\d)", r"\1 \2", s)
    return re.sub(r"\s+", " ", s).strip()
