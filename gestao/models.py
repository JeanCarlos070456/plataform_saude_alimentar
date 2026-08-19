from __future__ import annotations

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        DEVELOPER = "developer", "Desenvolvedor"
        MANAGER = "manager", "Gestor"
        EDITOR = "editor", "Editor"
        USER = "user", "Usuário"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="site_profile",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil de acesso"
        verbose_name_plural = "perfis de acesso"

    def __str__(self) -> str:
        return f"{self.user.email or self.user.username} — {self.get_role_display()}"


class AccessRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        APPROVED = "approved", "Aprovada"
        REJECTED = "rejected", "Recusada"

    full_name = models.CharField(max_length=180)
    email = models.EmailField(db_index=True)
    role_description = models.CharField(max_length=220, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_access_requests",
    )
    rejection_reason = models.TextField(blank=True)
    invite_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-requested_at"]
        verbose_name = "solicitação de acesso"
        verbose_name_plural = "solicitações de acesso"

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"


class PublicationStatus(models.TextChoices):
    PUBLISHED = "published", "Publicado"
    ARCHIVED = "archived", "Arquivado"
    DELETED = "deleted", "Excluído"


class GalleryItem(models.Model):
    title = models.CharField(max_length=180)
    eyebrow = models.CharField(
        max_length=120,
        blank=True,
        help_text="Ex.: Seminário técnico-científico · 2026",
    )
    summary = models.TextField(max_length=700)
    image_url = models.URLField(max_length=1000, blank=True)
    image_storage_path = models.CharField(max_length=500, blank=True)
    static_image = models.CharField(max_length=500, blank=True)
    external_url = models.URLField(max_length=1000, blank=True)
    link_label = models.CharField(max_length=80, blank=True, default="Saiba mais")
    status = models.CharField(
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PUBLISHED,
        db_index=True,
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Destaque na Home",
    )
    featured_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Destacado em",
    )
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_gallery_items",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_gallery_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]
        verbose_name = "vivência"
        verbose_name_plural = "galeria de vivências"

    def __str__(self) -> str:
        return self.title

    @property
    def has_image(self) -> bool:
        return bool(self.image_url or self.static_image)


class TeamMember(models.Model):
    full_name = models.CharField(max_length=180)
    role = models.CharField(max_length=180)
    short_bio = models.TextField(max_length=700, blank=True)
    lattes_url = models.URLField(max_length=1000, blank=True)
    photo_url = models.URLField(max_length=1000, blank=True)
    photo_storage_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PUBLISHED,
        db_index=True,
    )
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_team_members",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_team_members",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "full_name"]
        verbose_name = "membro da equipe"
        verbose_name_plural = "membros da equipe"

    def __str__(self) -> str:
        return self.full_name

    @property
    def initials(self) -> str:
        words = [part for part in self.full_name.split() if part]
        if not words:
            return "?"
        if len(words) == 1:
            return words[0][:2].upper()
        return f"{words[0][0]}{words[-1][0]}".upper()


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="site_audit_logs",
    )
    action = models.CharField(max_length=80, db_index=True)
    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "registro de auditoria"
        verbose_name_plural = "registros de auditoria"

    def __str__(self) -> str:
        return f"{self.created_at:%d/%m/%Y %H:%M} — {self.action}"
