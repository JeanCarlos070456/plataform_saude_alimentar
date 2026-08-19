from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from gestao.models import GalleryItem, PublicationStatus


MAX_FEATURED_GALLERY_ITEMS = 3


def apply_featured_state(item: GalleryItem, *, requested_featured: bool) -> list[GalleryItem]:
    """Mantém no máximo três vivências destacadas.

    Quando uma quarta vivência é marcada como destaque, a que está há mais
    tempo em destaque perde essa condição automaticamente.
    """
    removed: list[GalleryItem] = []

    with transaction.atomic():
        item = GalleryItem.objects.select_for_update().get(pk=item.pk)

        should_feature = bool(
            requested_featured and item.status == PublicationStatus.PUBLISHED
        )

        if should_feature:
            if not item.is_featured or item.featured_at is None:
                item.is_featured = True
                item.featured_at = timezone.now()
                item.save(update_fields=["is_featured", "featured_at", "updated_at"])

            other_featured = list(
                GalleryItem.objects.select_for_update()
                .filter(
                    is_featured=True,
                    status=PublicationStatus.PUBLISHED,
                )
                .exclude(pk=item.pk)
                .order_by("featured_at", "pk")
            )

            overflow = max(0, len(other_featured) - (MAX_FEATURED_GALLERY_ITEMS - 1))
            for old_item in other_featured[:overflow]:
                old_item.is_featured = False
                old_item.featured_at = None
                old_item.save(
                    update_fields=["is_featured", "featured_at", "updated_at"]
                )
                removed.append(old_item)
        else:
            if item.is_featured or item.featured_at is not None:
                item.is_featured = False
                item.featured_at = None
                item.save(update_fields=["is_featured", "featured_at", "updated_at"])

    return removed


def remove_from_featured(item: GalleryItem) -> None:
    if item.is_featured or item.featured_at is not None:
        item.is_featured = False
        item.featured_at = None
        item.save(update_fields=["is_featured", "featured_at", "updated_at"])
