from datetime import timedelta

from django.db import migrations, models
from django.utils import timezone


def seed_initial_featured(apps, schema_editor):
    GalleryItem = apps.get_model("gestao", "GalleryItem")
    items = list(
        GalleryItem.objects.filter(status="published")
        .exclude(image_url="", static_image="")
        .order_by("sort_order", "created_at", "pk")[:3]
    )
    base_time = timezone.now()
    for index, item in enumerate(items):
        item.is_featured = True
        item.featured_at = base_time + timedelta(microseconds=index)
        item.save(update_fields=["is_featured", "featured_at"])


def clear_featured(apps, schema_editor):
    GalleryItem = apps.get_model("gestao", "GalleryItem")
    GalleryItem.objects.update(is_featured=False, featured_at=None)


class Migration(migrations.Migration):
    dependencies = [
        ("gestao", "0002_seed_initial_content"),
    ]

    operations = [
        migrations.AddField(
            model_name="galleryitem",
            name="is_featured",
            field=models.BooleanField(
                db_index=True, default=False, verbose_name="Destaque na Home"
            ),
        ),
        migrations.AddField(
            model_name="galleryitem",
            name="featured_at",
            field=models.DateTimeField(
                blank=True, db_index=True, null=True, verbose_name="Destacado em"
            ),
        ),
        migrations.RunPython(seed_initial_featured, clear_featured),
    ]
