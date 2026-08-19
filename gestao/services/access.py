from __future__ import annotations

import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from gestao.models import AccessRequest, UserProfile


User = get_user_model()


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def split_name(full_name: str) -> tuple[str, str]:
    parts = [part for part in full_name.strip().split() if part]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def send_initial_password_email(access_request: AccessRequest, user, request) -> None:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    relative = reverse(
        "gestao:initial_password",
        kwargs={"uidb64": uid, "token": token},
    )
    absolute_url = request.build_absolute_uri(relative)
    subject = "Defina sua senha — Projeto Nutri na Escola"
    body = (
        f"Olá, {access_request.full_name}.\n\n"
        "Sua solicitação de acesso ao Projeto Nutri na Escola foi aprovada.\n"
        "Use o link abaixo para cadastrar sua senha de acesso. O link é individual e de uso único:\n\n"
        f"{absolute_url}\n\n"
        "Se você não solicitou este acesso, desconsidere esta mensagem.\n"
    )
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    access_request.invite_sent_at = timezone.now()
    access_request.save(update_fields=["invite_sent_at"])


def approve_access_request(access_request: AccessRequest, reviewer, request):
    email = normalize_email(access_request.email)
    user = User.objects.filter(username__iexact=email).first()
    if user is None:
        first_name, last_name = split_name(access_request.full_name)
        user = User(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )
        # Senha aleatória nunca é enviada ao usuário. O primeiro acesso ocorre via token.
        user.set_password(secrets.token_urlsafe(48))
        user.save()
    elif not user.is_active:
        raise ValueError(
            "Este e-mail pertence a um usuário inativo. A reativação deve ser tratada pela gestão."
        )
    else:
        user.email = email
        user.save(update_fields=["email"])

    profile, _ = UserProfile.objects.get_or_create(user=user)
    if not profile.role:
        profile.role = UserProfile.Role.USER
        profile.save(update_fields=["role", "updated_at"])

    access_request.status = AccessRequest.Status.APPROVED
    access_request.reviewed_at = timezone.now()
    access_request.reviewed_by = reviewer
    access_request.rejection_reason = ""
    access_request.save(
        update_fields=["status", "reviewed_at", "reviewed_by", "rejection_reason"]
    )
    email_error = None
    try:
        send_initial_password_email(access_request, user, request)
    except Exception as exc:  # A aprovação permanece registrada e o convite pode ser reenviado.
        email_error = exc
    return user, email_error


def reject_access_request(access_request: AccessRequest, reviewer, reason: str = "") -> None:
    access_request.status = AccessRequest.Status.REJECTED
    access_request.reviewed_at = timezone.now()
    access_request.reviewed_by = reviewer
    access_request.rejection_reason = reason.strip()
    access_request.save(
        update_fields=["status", "reviewed_at", "reviewed_by", "rejection_reason"]
    )


def critical_action_secret_is_valid(raw_secret: str) -> bool:
    encoded = (settings.GESTOR_CRITICAL_ACTION_SECRET_HASH or "").strip()
    if not encoded or not raw_secret:
        return False
    return check_password(raw_secret, encoded)
