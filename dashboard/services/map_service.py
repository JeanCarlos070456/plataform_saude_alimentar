from __future__ import annotations

import html
import math

import folium
import pandas as pd
from branca.element import Element
from django.conf import settings


def _risk_class(prevalence: float) -> str:
    """Retorna somente classes semânticas; as cores ficam no CSS."""
    if pd.isna(prevalence):
        return "risk-unknown"
    if prevalence < 40:
        return "risk-low"
    if prevalence < 60:
        return "risk-medium"
    return "risk-high"


def _fmt(value: float, suffix: str = "%") -> str:
    if pd.isna(value):
        return "Não disponível"
    return f"{value:.1f}{suffix}".replace(".", ",")


def _safe_text(value: object, fallback: str = "Não informado") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return fallback
    return html.escape(str(value))


def create_school_map(schools: list[dict]) -> tuple[str, list[dict]]:
    locations = pd.read_csv(settings.CAAFE_SCHOOL_LOCATIONS)
    stats = pd.DataFrame(schools)
    data = locations.merge(stats, on=["school_code", "school_name"], how="left")

    valid_coordinates = data.dropna(subset=["latitude", "longitude"])
    if valid_coordinates.empty:
        center = [-15.7939, -47.8828]
        zoom_start = 10
    else:
        center = [valid_coordinates["latitude"].mean(), valid_coordinates["longitude"].mean()]
        zoom_start = 12

    map_object = folium.Map(
        location=center,
        zoom_start=zoom_start,
        tiles="CartoDB positron",
        control_scale=True,
        prefer_canvas=False,
    )
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(map_object)

    # O mesmo CSS do painel é carregado dentro do iframe do Folium.
    css_url = f"{settings.STATIC_URL.rstrip('/')}/dashboard/css/app.css"
    map_object.get_root().header.add_child(
        Element(f'<link rel="stylesheet" href="{html.escape(css_url)}">')
    )

    for _, row in valid_coordinates.iterrows():
        prevalence = row.get("prevalence", float("nan"))
        valid_n = int(row.get("n_valid", 0) or 0)
        marker_size = max(31, min(48, 29 + valid_n / 11))
        marker_class = _risk_class(prevalence)
        marker_label = "—" if pd.isna(prevalence) else f"{prevalence:.0f}%"

        popup = f"""
        <div class="caafe-popup">
            <h4>{_safe_text(row.get('school_name'))}</h4>
            <div class="caafe-popup-subtitle">INEP: {_safe_text(row.get('school_inep'))} · n válido: {valid_n}</div>
            <div class="caafe-popup-grid">
                <span>Alguma insegurança</span><strong>{_fmt(prevalence)}</strong>
                <span>IC95%</span><strong>{_fmt(row.get('ci_low'))} – {_fmt(row.get('ci_high'))}</strong>
                <span>Moderada/grave</span><strong>{_fmt(row.get('moderate_severe'))}</strong>
                <span>Renda até 1 SM</span><strong>{_fmt(row.get('low_income'))}</strong>
                <span>Escolaridade materna 0–8</span><strong>{_fmt(row.get('low_mother_education'))}</strong>
                <span>Pardos/pretos</span><strong>{_fmt(row.get('black_brown'))}</strong>
                <span>Idade média</span><strong>{_fmt(row.get('mean_age'), ' anos')}</strong>
            </div>
            <div class="caafe-popup-note">{_safe_text(row.get('coordinate_status'))}</div>
        </div>
        """
        tooltip = (
            f"{_safe_text(row.get('school_name'))}: "
            f"{_fmt(prevalence)} de alguma insegurança (n={valid_n})"
        )
        icon_html = (
            f'<div class="caafe-map-marker {marker_class}" '
            f'style="--marker-size:{marker_size:.0f}px"><span>{marker_label}</span></div>'
        )

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            tooltip=tooltip,
            popup=folium.Popup(popup, max_width=370),
            icon=folium.DivIcon(
                html=icon_html,
                icon_size=(marker_size, marker_size),
                icon_anchor=(marker_size / 2, marker_size),
                class_name="caafe-div-icon",
            ),
        ).add_to(map_object)

    legend = """
    <div class="caafe-map-legend">
        <strong>Alguma insegurança</strong>
        <span><i class="risk-low"></i> Menor que 40%</span>
        <span><i class="risk-medium"></i> 40% a 59,9%</span>
        <span><i class="risk-high"></i> 60% ou mais</span>
    </div>
    """
    map_object.get_root().html.add_child(Element(legend))
    folium.LayerControl(collapsed=True).add_to(map_object)
    return map_object._repr_html_(), data.to_dict("records")
