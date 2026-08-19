from __future__ import annotations

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from gestao.models import UserProfile


MANAGEMENT_ROLES = {UserProfile.Role.DEVELOPER, UserProfile.Role.MANAGER}
EDITOR_ROLES = MANAGEMENT_ROLES | {UserProfile.Role.EDITOR}


def _role(user) -> str:
    if not getattr(user, "is_authenticated", False):
        return ""
    if user.is_superuser:
        return UserProfile.Role.DEVELOPER
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.role


def user_can_manage(user) -> bool:
    return bool(getattr(user, "is_authenticated", False) and _role(user) in MANAGEMENT_ROLES)


def user_can_edit_content(user) -> bool:
    return bool(getattr(user, "is_authenticated", False) and _role(user) in EDITOR_ROLES)


def role_required(*allowed_roles):
    allowed = set(allowed_roles)

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.is_superuser or _role(request.user) in allowed:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("Você não possui permissão para acessar esta área.")

        return wrapped

    return decorator


management_required = role_required(*MANAGEMENT_ROLES)
content_editor_required = role_required(*EDITOR_ROLES)
