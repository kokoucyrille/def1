"""Focused regression tests for the v6 interface and regional network coverage."""
from __future__ import annotations

import csv
import math
from numbers import Real
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_app_page(page: str):
    import pytest
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(ROOT / "views" / page), default_timeout=120).run()
    errors = [error.value for error in app.exception]
    if any("DLL load failed while importing _bounded_integers" in error for error in errors):
        pytest.skip("Windows application control blocks NumPy's _bounded_integers extension.")
    assert not errors, (page, errors)
    return app


def test_regional_bad_condition_uses_join_coverage():
    with (ROOT / "data" / "processed" / "etat_reseau_region_indicatif.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        rows = {row["region"]: row for row in csv.DictReader(source)}

    assert len(rows) == 6
    assert float(rows["Grand Lomé"]["couverture"]) == 0
    assert rows["Grand Lomé"]["part_mauvais"] == ""
    assert all(float(row["couverture"]) > 0 for region, row in rows.items() if region != "Grand Lomé")


def test_eight_pages_have_reading_and_territory_controls():
    pages = (
        "vue_ensemble.py",
        "immatriculations.py",
        "permis.py",
        "securite.py",
        "etat_reseau.py",
        "routes_auto_ecoles.py",
        "diagnostic.py",
        "donnees.py",
    )
    for page in pages:
        app = run_app_page(page)
        assert "À retenir" in " ".join(element.value for element in app.markdown)
        assert any(widget.key == "show_readings" and widget.value for widget in app.sidebar.checkbox)


def test_recommendations_expose_cited_territories_and_diagnostic_top_five():
    app = run_app_page("diagnostic.py")
    text = " ".join(element.value for element in app.markdown)
    assert "Top 5 des priorités" in text
    assert any(button.label == "Voir Kpendjal-Ouest" for button in app.button)


def test_panel_css_keeps_content_height_flexible(monkeypatch):
    from components import ui

    css = []
    monkeypatch.setattr(ui.st, "markdown", lambda content, **kwargs: css.append(content))
    ui._PANEL_HEIGHTS["test_panel"] = 200
    ui.flush_panel_css()

    assert "min-height:200px" in css[0]
    assert "min-height:224px" in css[0]
    assert ";height:200px" not in css[0]


def test_prepare_figure_adds_hover_and_sanitizes_non_finite_customdata():
    import plotly.graph_objects as go

    from components.charts import prepare_figure

    fig = go.Figure(go.Scatter(x=[1, 2], y=[1, 2], customdata=[float("nan"), float("inf")]))
    prepare_figure(fig)

    assert fig.data[0].hovertemplate
    assert list(fig.data[0].customdata) == ["n.d.", "n.d."]


def test_filtered_csv_download_exists_on_all_pages():
    pages = (
        "vue_ensemble.py",
        "immatriculations.py",
        "permis.py",
        "securite.py",
        "etat_reseau.py",
        "routes_auto_ecoles.py",
        "diagnostic.py",
        "donnees.py",
    )
    for page in pages:
        app = run_app_page(page)
        assert any("CSV" in button.label for button in app.get("download_button")), page


def test_all_page_plotly_traces_have_safe_hover_data(monkeypatch):
    from components import charts

    figures = []

    def collect(fig, key, select=False):
        figures.append(charts.prepare_figure(fig))
        return None

    monkeypatch.setattr(charts, "show", collect)
    pages = (
        "vue_ensemble.py",
        "immatriculations.py",
        "permis.py",
        "securite.py",
        "etat_reseau.py",
        "routes_auto_ecoles.py",
        "diagnostic.py",
        "donnees.py",
    )
    for page in pages:
        run_app_page(page)

    assert figures, "No Plotly figures were captured from the eight pages."
    for fig in figures:
        for trace in fig.data:
            assert trace.hovertemplate, (trace.type, trace.name)

            def check_customdata(value):
                if hasattr(value, "tolist"):
                    value = value.tolist()
                if isinstance(value, (list, tuple)):
                    for item in value:
                        check_customdata(item)
                elif isinstance(value, Real):
                    assert math.isfinite(float(value)), (trace.type, trace.name, value)

            if trace.customdata is not None:
                check_customdata(trace.customdata)
