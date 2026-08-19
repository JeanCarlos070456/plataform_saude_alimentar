from __future__ import annotations

import logging

from django.shortcuts import render

from dashboard.services.analytics import build_payload
from gestao.models import GalleryItem, PublicationStatus, TeamMember
from gestao.services.permissions import user_can_manage

from .content import EXPERIENCES, METHOD_STEPS, PROJECT_AREAS, TEAM_GROUPS

logger = logging.getLogger(__name__)


def _fallback_metrics() -> dict:
    return {
        "source": {"rows": 0, "updated_at": "", "type": "indisponível", "hash": "—"},
        "summary": {
            "valid_n": 0,
            "prevalence_fmt": "—",
            "moderate_severe_fmt": "—",
        },
        "schools": [],
    }


def _initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


def _fallback_team_members() -> list[dict]:
    members = []
    order = 0
    for group in TEAM_GROUPS:
        for raw_member in group.get("members", []):
            order += 1
            if " — " in raw_member:
                name, specific_role = raw_member.split(" — ", 1)
                role = specific_role
            else:
                name = raw_member
                role = group.get("subtitle", group.get("title", "Equipe de pesquisa"))
            members.append(
                {
                    "full_name": name,
                    "role": role,
                    "short_bio": "",
                    "lattes_url": "",
                    "photo_url": "",
                    "initials": _initials(name),
                    "sort_order": order,
                }
            )
    return members


def _load_team_members():
    try:
        items = list(
            TeamMember.objects.filter(status=PublicationStatus.PUBLISHED).order_by(
                "sort_order", "full_name"
            )
        )
        if items:
            return items
    except Exception:
        logger.exception("Falha ao carregar equipe dinâmica")
    return _fallback_team_members()


def _load_experiences() -> list[dict]:
    try:
        items = list(
            GalleryItem.objects.filter(status=PublicationStatus.PUBLISHED).order_by(
                "sort_order", "-created_at"
            )
        )
        if items:
            return [
                {
                    "title": item.title,
                    "text": item.summary,
                    "meta": item.eyebrow,
                    "image_url": item.image_url,
                    "static_image": item.static_image,
                    "external_url": item.external_url,
                    "link_label": item.link_label or "Saiba mais",
                }
                for item in items
            ]
    except Exception:
        logger.exception("Falha ao carregar galeria dinâmica")

    return [
        {
            "title": item["title"],
            "text": item["text"],
            "meta": item.get("meta", ""),
            "image_url": "",
            "static_image": item.get("image", ""),
            "external_url": "",
            "link_label": "Saiba mais",
        }
        for item in EXPERIENCES
    ]




def _load_hero_slides(limit: int = 3) -> list[dict]:
    slides: list[dict] = []
    try:
        items = list(
            GalleryItem.objects.filter(
                status=PublicationStatus.PUBLISHED,
                is_featured=True,
            ).order_by("featured_at", "pk")[:limit]
        )
        for item in items:
            if not item.has_image:
                continue
            slides.append(
                {
                    "title": item.title,
                    "image_url": item.image_url,
                    "static_image": item.static_image,
                    "external_url": item.external_url,
                    "is_placeholder": False,
                }
            )
    except Exception:
        logger.exception("Falha ao carregar destaques da galeria")

    while len(slides) < limit:
        slides.append(
            {
                "title": "Projeto Nutri na Escola",
                "image_url": "",
                "static_image": "",
                "external_url": "",
                "is_placeholder": True,
            }
        )
    return slides[:limit]


def home(request):
    try:
        data = build_payload()
        data_available = True
    except Exception:
        logger.exception("Falha ao carregar indicadores para a Home institucional")
        data = _fallback_metrics()
        data_available = False

    context = {
        "data": data,
        "data_available": data_available,
        "school_count": len(
            [row for row in data.get("schools", []) if row.get("n_valid", 0)]
        ),
        "project_areas": PROJECT_AREAS,
        "method_steps": METHOD_STEPS,
        "team_members": _load_team_members(),
        "experiences": _load_experiences(),
        "hero_slides": _load_hero_slides(),
        "can_manage_site": user_can_manage(request.user),
    }
    return render(request, "institutional/home.html", context)
