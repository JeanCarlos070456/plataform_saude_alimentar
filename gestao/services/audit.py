from __future__ import annotations

from typing import Any

from gestao.models import AuditLog


def _ip_from_request(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def log_action(
    request,
    action: str,
    obj: Any | None = None,
    *,
    details: dict | None = None,
) -> AuditLog:
    return AuditLog.objects.create(
        actor=request.user if getattr(request.user, "is_authenticated", False) else None,
        action=action,
        object_type=obj.__class__.__name__ if obj is not None else "",
        object_id=str(getattr(obj, "pk", "") or "") if obj is not None else "",
        object_repr=str(obj)[:255] if obj is not None else "",
        details=details or {},
        ip_address=_ip_from_request(request),
    )
