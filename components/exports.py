"""Helpers for downloads of the data currently represented by a page."""
from __future__ import annotations

import pandas as pd
import streamlit as st


def download_csv(label: str, data: pd.DataFrame, filename: str, key: str) -> None:
    st.download_button(
        label,
        data=data.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=key,
        width="stretch",
    )
