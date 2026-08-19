from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    AccessRequestForm,
    CriticalDeactivationForm,
    GalleryItemForm,
    TeamMemberForm,
    UserRoleForm,
)
from .models import AccessRequest, AuditLog, GalleryItem, PublicationStatus, TeamMember, UserProfile
from .services.access import (
    approve_access_request,
    critical_action_secret_is_valid,
    reject_access_request,
    send_initial_password_email,
)
from .services.audit import log_action
from .services.media import upload_public_image
from .services.gallery import apply_featured_state, remove_from_featured
from .services.permissions import content_editor_required, management_required, user_can_manage


User = get_user_model()


class EmailLoginView(auth_views.LoginView):
    template_name = "gestao/login.html"

    def get_success_url(self):
        redirect_url = self.get_redirect_url()
        if redirect_url:
            return redirect_url
        if user_can_manage(self.request.user):
            return reverse("gestao:dashboard")
        return reverse("institutional:home")


def request_access(request):
    if request.user.is_authenticated:
        if user_can_manage(request.user):
            return redirect("gestao:dashboard")
        return redirect("institutional:home")
    form = AccessRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        access_request = form.save()
        log_action(request, "ACCESS_REQUEST_CREATED", access_request)
        return redirect("gestao:request_access_done")
    return render(request, "gestao/request_access.html", {"form": form})


def request_access_done(request):
    return render(request, "gestao/request_access_done.html")


@management_required
def dashboard(request):
    context = {
        "pending_requests": AccessRequest.objects.filter(status=AccessRequest.Status.PENDING).count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "published_gallery": GalleryItem.objects.filter(status=PublicationStatus.PUBLISHED).count(),
        "published_team": TeamMember.objects.filter(status=PublicationStatus.PUBLISHED).count(),
        "recent_requests": AccessRequest.objects.filter(status=AccessRequest.Status.PENDING)[:5],
        "recent_audit": AuditLog.objects.select_related("actor")[:8],
    }
    return render(request, "gestao/dashboard.html", context)


@management_required
def access_requests(request):
    status = request.GET.get("status", "pending")
    queryset = AccessRequest.objects.select_related("reviewed_by")
    if status in AccessRequest.Status.values:
        queryset = queryset.filter(status=status)
    return render(
        request,
        "gestao/access_requests.html",
        {"requests": queryset, "selected_status": status},
    )


@require_POST
@management_required
def approve_request(request, pk: int):
    access_request = get_object_or_404(AccessRequest, pk=pk)
    if access_request.status != AccessRequest.Status.PENDING:
        messages.warning(request, "Esta solicitação já foi analisada.")
        return redirect("gestao:access_requests")
    try:
        user, email_error = approve_access_request(access_request, request.user, request)
    except Exception as exc:
        messages.error(request, f"Não foi possível aprovar esta solicitação: {exc}")
        return redirect("gestao:access_requests")
    log_action(request, "ACCESS_REQUEST_APPROVED", access_request, details={"user_id": user.pk})
    if email_error:
        messages.warning(
            request,
            "O acesso foi aprovado, mas o convite não pôde ser enviado. "
            "Corrija a configuração de e-mail e use 'Reenviar convite'.",
        )
    else:
        messages.success(
            request,
            f"Acesso aprovado para {access_request.email}. O convite foi enviado por e-mail.",
        )
    return redirect("gestao:access_requests")


@require_POST
@management_required
def reject_request(request, pk: int):
    access_request = get_object_or_404(AccessRequest, pk=pk)
    if access_request.status != AccessRequest.Status.PENDING:
        messages.warning(request, "Esta solicitação já foi analisada.")
        return redirect("gestao:access_requests")
    reason = request.POST.get("reason", "")
    reject_access_request(access_request, request.user, reason)
    log_action(request, "ACCESS_REQUEST_REJECTED", access_request, details={"reason": reason[:500]})
    messages.success(request, "Solicitação recusada.")
    return redirect("gestao:access_requests")


@require_POST
@management_required
def resend_invite(request, pk: int):
    access_request = get_object_or_404(AccessRequest, pk=pk, status=AccessRequest.Status.APPROVED)
    user = User.objects.filter(username__iexact=access_request.email).first()
    if not user:
        messages.error(request, "Usuário aprovado não encontrado.")
        return redirect("gestao:access_requests")
    try:
        send_initial_password_email(access_request, user, request)
    except Exception as exc:
        messages.error(request, f"Falha ao reenviar convite: {exc}")
        return redirect("gestao:access_requests")
    log_action(request, "ACCESS_INVITE_RESENT", access_request)
    messages.success(request, "Convite reenviado.")
    return redirect("gestao:access_requests")


@management_required
def users_list(request):
    users = User.objects.all().order_by("-is_active", "first_name", "username")
    rows = []
    for user in users:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        rows.append({"user": user, "profile": profile})
    return render(request, "gestao/users.html", {"rows": rows, "role_choices": UserProfile.Role.choices})


@require_POST
@management_required
def update_user_role(request, pk: int):
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.error(request, "Por segurança, você não pode alterar seu próprio perfil nesta tela.")
        return redirect("gestao:users")
    form = UserRoleForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Perfil inválido.")
        return redirect("gestao:users")
    new_role = form.cleaned_data["role"]
    if new_role == UserProfile.Role.DEVELOPER and not request.user.is_superuser:
        messages.error(request, "Somente um superusuário pode conceder o perfil Desenvolvedor.")
        return redirect("gestao:users")
    if target.is_superuser and not request.user.is_superuser:
        messages.error(request, "Somente um superusuário pode alterar outro superusuário.")
        return redirect("gestao:users")
    profile, _ = UserProfile.objects.get_or_create(user=target)
    before = profile.role
    profile.role = new_role
    profile.save(update_fields=["role", "updated_at"])
    log_action(request, "USER_ROLE_UPDATED", target, details={"before": before, "after": profile.role})
    messages.success(request, f"Perfil de {target.email or target.username} atualizado.")
    return redirect("gestao:users")


@management_required
def deactivate_user(request, pk: int):
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.error(request, "Você não pode desativar seu próprio usuário.")
        return redirect("gestao:users")
    if target.is_superuser and not request.user.is_superuser:
        messages.error(request, "Somente um superusuário pode desligar outro superusuário.")
        return redirect("gestao:users")
    if not target.is_active:
        messages.info(request, "Este usuário já está inativo.")
        return redirect("gestao:users")

    form = CriticalDeactivationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not critical_action_secret_is_valid(form.cleaned_data["authorization_password"]):
            form.add_error("authorization_password", "Senha de autorização inválida.")
        else:
            target.is_active = False
            target.save(update_fields=["is_active"])
            log_action(request, "USER_DEACTIVATED", target)
            messages.success(request, f"Acesso de {target.email or target.username} desativado.")
            return redirect("gestao:users")
    return render(request, "gestao/deactivate_user.html", {"target": target, "form": form})


@content_editor_required
def gallery_list(request):
    items = GalleryItem.objects.exclude(status=PublicationStatus.DELETED)
    return render(request, "gestao/gallery_list.html", {"items": items})


def _save_gallery_form(request, instance=None):
    form = GalleryItemForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        image = form.cleaned_data.get("image_file")
        if image:
            try:
                image_url, storage_path = upload_public_image(image, "gallery")
            except ValidationError as exc:
                form.add_error("image_file", exc)
                return form, None
            item.image_url = image_url
            item.image_storage_path = storage_path
        requested_featured = bool(form.cleaned_data.get("is_featured"))
        if instance is None:
            item.created_by = request.user
        item.updated_by = request.user
        item.save()
        removed = apply_featured_state(item, requested_featured=requested_featured)
        item.refresh_from_db()
        for old_item in removed:
            log_action(
                request,
                "GALLERY_FEATURE_AUTO_REMOVED",
                old_item,
                details={"reason": "featured_limit", "limit": 3},
            )
        return form, item
    return form, None


@content_editor_required
def gallery_create(request):
    form, item = _save_gallery_form(request)
    if item:
        log_action(request, "GALLERY_CREATED", item)
        messages.success(request, "Card da galeria criado.")
        return redirect("gestao:gallery_list")
    return render(request, "gestao/gallery_form.html", {"form": form, "title": "Nova vivência"})


@content_editor_required
def gallery_edit(request, pk: int):
    item = get_object_or_404(GalleryItem, pk=pk)
    form, saved = _save_gallery_form(request, item)
    if saved:
        log_action(request, "GALLERY_UPDATED", saved)
        messages.success(request, "Card atualizado.")
        return redirect("gestao:gallery_list")
    return render(request, "gestao/gallery_form.html", {"form": form, "title": "Editar vivência", "item": item})


@require_POST
@content_editor_required
def gallery_archive(request, pk: int):
    item = get_object_or_404(GalleryItem, pk=pk)
    item.status = (
        PublicationStatus.PUBLISHED
        if item.status == PublicationStatus.ARCHIVED
        else PublicationStatus.ARCHIVED
    )
    item.updated_by = request.user
    item.save(update_fields=["status", "updated_by", "updated_at"])
    if item.status != PublicationStatus.PUBLISHED:
        remove_from_featured(item)
    log_action(request, "GALLERY_STATUS_UPDATED", item, details={"status": item.status})
    messages.success(request, "Status da vivência atualizado.")
    return redirect("gestao:gallery_list")


@require_POST
@content_editor_required
def gallery_delete(request, pk: int):
    item = get_object_or_404(GalleryItem, pk=pk)
    item.status = PublicationStatus.DELETED
    item.updated_by = request.user
    item.save(update_fields=["status", "updated_by", "updated_at"])
    remove_from_featured(item)
    log_action(request, "GALLERY_SOFT_DELETED", item)
    messages.success(request, "Card removido da gestão ativa e preservado na auditoria.")
    return redirect("gestao:gallery_list")


@content_editor_required
def team_list(request):
    members = TeamMember.objects.exclude(status=PublicationStatus.DELETED)
    return render(request, "gestao/team_list.html", {"members": members})


def _save_team_form(request, instance=None):
    form = TeamMemberForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        member = form.save(commit=False)
        photo = form.cleaned_data.get("photo_file")
        if photo:
            try:
                photo_url, storage_path = upload_public_image(photo, "team")
            except ValidationError as exc:
                form.add_error("photo_file", exc)
                return form, None
            member.photo_url = photo_url
            member.photo_storage_path = storage_path
        if instance is None:
            member.created_by = request.user
        member.updated_by = request.user
        member.save()
        return form, member
    return form, None


@content_editor_required
def team_create(request):
    form, member = _save_team_form(request)
    if member:
        log_action(request, "TEAM_MEMBER_CREATED", member)
        messages.success(request, "Membro cadastrado.")
        return redirect("gestao:team_list")
    return render(request, "gestao/team_form.html", {"form": form, "title": "Novo membro"})


@content_editor_required
def team_edit(request, pk: int):
    member = get_object_or_404(TeamMember, pk=pk)
    form, saved = _save_team_form(request, member)
    if saved:
        log_action(request, "TEAM_MEMBER_UPDATED", saved)
        messages.success(request, "Membro atualizado.")
        return redirect("gestao:team_list")
    return render(request, "gestao/team_form.html", {"form": form, "title": "Editar membro", "member": member})


@require_POST
@content_editor_required
def team_archive(request, pk: int):
    member = get_object_or_404(TeamMember, pk=pk)
    member.status = (
        PublicationStatus.PUBLISHED
        if member.status == PublicationStatus.ARCHIVED
        else PublicationStatus.ARCHIVED
    )
    member.updated_by = request.user
    member.save(update_fields=["status", "updated_by", "updated_at"])
    log_action(request, "TEAM_MEMBER_STATUS_UPDATED", member, details={"status": member.status})
    messages.success(request, "Status do membro atualizado.")
    return redirect("gestao:team_list")


@require_POST
@content_editor_required
def team_delete(request, pk: int):
    member = get_object_or_404(TeamMember, pk=pk)
    member.status = PublicationStatus.DELETED
    member.updated_by = request.user
    member.save(update_fields=["status", "updated_by", "updated_at"])
    log_action(request, "TEAM_MEMBER_SOFT_DELETED", member)
    messages.success(request, "Membro removido da gestão ativa e preservado na auditoria.")
    return redirect("gestao:team_list")


@management_required
def audit_list(request):
    query = (request.GET.get("q") or "").strip()
    logs = AuditLog.objects.select_related("actor")
    if query:
        logs = logs.filter(
            Q(action__icontains=query)
            | Q(object_repr__icontains=query)
            | Q(actor__email__icontains=query)
        )
    return render(request, "gestao/audit_list.html", {"logs": logs[:300], "query": query})
