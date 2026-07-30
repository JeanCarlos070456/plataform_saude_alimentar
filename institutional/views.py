from __future__ import annotations

import logging

from django.shortcuts import render

from dashboard.services.analytics import build_payload

from .content import EXPERIENCES, METHOD_STEPS, PROJECT_AREAS, TEAM_GROUPS

logger = logging.getLogger(__name__)


def _fallback_metrics() -> dict:
    """Mantém a Home disponível mesmo se a fonte analítica estiver indisponível."""
    return {
        "source": {"rows": 0, "updated_at": "", "type": "indisponível", "hash": "—"},
        "summary": {
            "valid_n": 0,
            "prevalence_fmt": "—",
            "moderate_severe_fmt": "—",
        },
        "schools": [],
    }


def home(request):
    try:
        data = build_payload()
        data_available = True
    except Exception:  # A página institucional não deve cair junto com o painel.
        logger.exception("Falha ao carregar indicadores para a Home institucional")
        data = _fallback_metrics()
        data_available = False

    context = {
        "data": data,
        "data_available": data_available,
        "school_count": len([row for row in data.get("schools", []) if row.get("n_valid", 0)]),
        "project_areas": PROJECT_AREAS,
        "method_steps": METHOD_STEPS,
        "team_groups": TEAM_GROUPS,
        "experiences": EXPERIENCES,
    }
    return render(request, "institutional/home.html", context)