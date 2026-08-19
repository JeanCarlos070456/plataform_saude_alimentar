from django.contrib import admin

from .models import AccessRequest, AuditLog, GalleryItem, TeamMember, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "updated_at")
    list_filter = ("role",)
    search_fields = ("user__email", "user__username", "user__first_name", "user__last_name")


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "status", "requested_at", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("full_name", "email", "role_description")


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "is_featured", "featured_at", "sort_order", "updated_at")
    list_filter = ("status", "is_featured")
    search_fields = ("title", "summary")


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role", "status", "sort_order", "updated_at")
    list_filter = ("status",)
    search_fields = ("full_name", "role", "short_bio")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "object_type", "object_repr")
    list_filter = ("action", "object_type")
    search_fields = ("actor__email", "action", "object_repr")
    readonly_fields = ("actor", "action", "object_type", "object_id", "object_repr", "details", "ip_address", "created_at")
