from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=180)),
                ("email", models.EmailField(db_index=True, max_length=254)),
                ("role_description", models.CharField(blank=True, max_length=220)),
                ("status", models.CharField(choices=[("pending", "Pendente"), ("approved", "Aprovada"), ("rejected", "Recusada")], default="pending", max_length=20)),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("rejection_reason", models.TextField(blank=True)),
                ("invite_sent_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_access_requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "solicitação de acesso",
                "verbose_name_plural": "solicitações de acesso",
                "ordering": ["-requested_at"],
            },
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(db_index=True, max_length=80)),
                ("object_type", models.CharField(blank=True, max_length=80)),
                ("object_id", models.CharField(blank=True, max_length=80)),
                ("object_repr", models.CharField(blank=True, max_length=255)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="site_audit_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "registro de auditoria",
                "verbose_name_plural": "registros de auditoria",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="GalleryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("eyebrow", models.CharField(blank=True, help_text="Ex.: Seminário técnico-científico · 2026", max_length=120)),
                ("summary", models.TextField(max_length=700)),
                ("image_url", models.URLField(blank=True, max_length=1000)),
                ("image_storage_path", models.CharField(blank=True, max_length=500)),
                ("static_image", models.CharField(blank=True, max_length=500)),
                ("external_url", models.URLField(blank=True, max_length=1000)),
                ("link_label", models.CharField(blank=True, default="Saiba mais", max_length=80)),
                ("status", models.CharField(choices=[("published", "Publicado"), ("archived", "Arquivado"), ("deleted", "Excluído")], db_index=True, default="published", max_length=20)),
                ("sort_order", models.PositiveIntegerField(db_index=True, default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_gallery_items", to=settings.AUTH_USER_MODEL)),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_gallery_items", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "vivência",
                "verbose_name_plural": "galeria de vivências",
                "ordering": ["sort_order", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TeamMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=180)),
                ("role", models.CharField(max_length=180)),
                ("short_bio", models.TextField(blank=True, max_length=700)),
                ("lattes_url", models.URLField(blank=True, max_length=1000)),
                ("photo_url", models.URLField(blank=True, max_length=1000)),
                ("photo_storage_path", models.CharField(blank=True, max_length=500)),
                ("status", models.CharField(choices=[("published", "Publicado"), ("archived", "Arquivado"), ("deleted", "Excluído")], db_index=True, default="published", max_length=20)),
                ("sort_order", models.PositiveIntegerField(db_index=True, default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_team_members", to=settings.AUTH_USER_MODEL)),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_team_members", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "membro da equipe",
                "verbose_name_plural": "membros da equipe",
                "ordering": ["sort_order", "full_name"],
            },
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("developer", "Desenvolvedor"), ("manager", "Gestor"), ("editor", "Editor"), ("user", "Usuário")], default="user", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="site_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "perfil de acesso",
                "verbose_name_plural": "perfis de acesso",
            },
        ),
    ]
