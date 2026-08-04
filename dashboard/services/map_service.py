from __future__ import annotations

import html

import folium
import pandas as pd
from branca.element import Element

from dashboard.services.school_source import load_schools


def _normalize_school_code(series: pd.Series) -> pd.Series:
    """Padroniza 1, 1.0 e '1' para a mesma chave de junção."""
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def _color(prevalence):
    if pd.isna(prevalence):
        return "#6b7280"
    if prevalence < 40:
        return "#2a9d8f"
    if prevalence < 60:
        return "#f4a261"
    return "#d1495b"


def _fmt_pct(value) -> str:
    try:
        if pd.isna(value):
            return "—"
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "—"


def _fmt_number(value, decimals: int = 1) -> str:
    try:
        if pd.isna(value):
            return "—"
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def _fmt_inep(value) -> str:
    try:
        if pd.isna(value):
            return "—"
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return html.escape(text or "—")


def _safe_n(value) -> int:
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def create_school_map(schools: list[dict]) -> tuple[str, list[dict]]:
    """
    Cria o mapa escolar usando o cache geográfico mantido por school_source.

    Fonte geográfica:
        Supabase/escolas.csv -> data/cache/escolas.parquet -> load_schools()

    Os indicadores continuam chegando pelo argumento ``schools`` e são
    unidos às coordenadas por ``school_code``.
    """
    locations = load_schools().copy()

    locations["school_code"] = _normalize_school_code(
        locations["school_code"]
    )

    stats = pd.DataFrame(schools)

    if stats.empty:
        stats = pd.DataFrame(columns=["school_code"])
    elif "school_code" not in stats.columns:
        raise ValueError(
            "Indicadores por escola sem a coluna obrigatória 'school_code'."
        )
    else:
        stats = stats.copy()
        stats["school_code"] = _normalize_school_code(stats["school_code"])

        # Os metadados oficiais de escola vêm do escolas.csv.
        # Evita school_name_x / school_name_y após o merge.
        for column in (
            "school_name",
            "school_inep",
            "address",
            "latitude",
            "longitude",
            "coordinate_status",
        ):
            if column in stats.columns:
                stats = stats.drop(columns=[column])

        duplicated = stats["school_code"].duplicated(keep=False)
        if duplicated.any():
            codes = sorted(
                stats.loc[duplicated, "school_code"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            raise ValueError(
                f"Indicadores possuem school_code duplicado: {codes}"
            )

    data = locations.merge(
        stats,
        on="school_code",
        how="left",
        validate="one_to_one",
    )

    if data.empty:
        raise ValueError("Nenhuma escola disponível para renderizar o mapa.")

    center = [
        float(data["latitude"].mean()),
        float(data["longitude"].mean()),
    ]

    m = folium.Map(
        location=center,
        zoom_start=12,
        tiles="CartoDB positron",
        control_scale=True,
    )
    folium.TileLayer(
        "OpenStreetMap",
        name="OpenStreetMap",
    ).add_to(m)

    for _, row in data.iterrows():
        prevalence = row.get("prevalence", float("nan"))
        n_valid = _safe_n(row.get("n_valid", 0))

        school_name = html.escape(str(row.get("school_name", "Escola")))
        coordinate_status = html.escape(
            str(row.get("coordinate_status", "") or "")
        )

        ci_low = row.get("ci_low", float("nan"))
        ci_high = row.get("ci_high", float("nan"))

        if pd.isna(ci_low) or pd.isna(ci_high):
            ci_text = "—"
        else:
            ci_text = f"{float(ci_low):.1f}–{float(ci_high):.1f}%"

        popup = f"""
        <div style="font-family:Arial;min-width:280px">
            <h4 style="margin:0 0 8px">{school_name}</h4>
            <div><b>INEP:</b> {_fmt_inep(row.get("school_inep"))}</div>
            <div><b>N válido:</b> {n_valid}</div>

            <hr style="border:0;border-top:1px solid #ddd">

            <div>
                <b>Alguma insegurança:</b>
                {_fmt_pct(prevalence)}
            </div>
            <div><b>IC95%:</b> {ci_text}</div>
            <div>
                <b>Moderada/grave:</b>
                {_fmt_pct(row.get("moderate_severe", float("nan")))}
            </div>
            <div>
                <b>Renda até 1 SM:</b>
                {_fmt_pct(row.get("low_income", float("nan")))}
            </div>
            <div>
                <b>Escolaridade materna 0–8:</b>
                {_fmt_pct(row.get("low_mother_education", float("nan")))}
            </div>
            <div>
                <b>Pardos/pretos:</b>
                {_fmt_pct(row.get("black_brown", float("nan")))}
            </div>
            <div>
                <b>Idade média:</b>
                {_fmt_number(row.get("mean_age", float("nan")))} anos
            </div>

            <div style="
                margin-top:8px;
                font-size:11px;
                color:#6b7280;
            ">
                {coordinate_status}
            </div>
        </div>
        """

        if pd.isna(prevalence):
            tooltip = f"{row['school_name']}: sem estimativa disponível"
        else:
            tooltip = (
                f"{row['school_name']}: "
                f"{float(prevalence):.1f}% de alguma insegurança "
                f"(n={n_valid})"
            )

        folium.CircleMarker(
            location=[
                float(row["latitude"]),
                float(row["longitude"]),
            ],
            radius=max(8, min(18, 6 + n_valid / 12)),
            color="#ffffff",
            weight=2,
            fill=True,
            fill_color=_color(prevalence),
            fill_opacity=0.9,
            tooltip=tooltip,
            popup=folium.Popup(
                popup,
                max_width=360,
            ),
        ).add_to(m)

    legend = """
    <div style="
        position:fixed;
        bottom:35px;
        left:35px;
        z-index:9999;
        background:white;
        padding:10px 12px;
        border:1px solid #ddd;
        border-radius:8px;
        font:12px Arial;
        box-shadow:0 3px 12px rgba(0,0,0,.15)
    ">
        <b>Alguma insegurança</b><br>
        <span style="color:#2a9d8f">●</span> &lt;40%<br>
        <span style="color:#f4a261">●</span> 40–59,9%<br>
        <span style="color:#d1495b">●</span> ≥60%<br>
        <span style="color:#6b7280">●</span> Sem estimativa
    </div>
    """

    m.get_root().html.add_child(Element(legend))
    folium.LayerControl(collapsed=True).add_to(m)

    return m._repr_html_(), data.to_dict("records")