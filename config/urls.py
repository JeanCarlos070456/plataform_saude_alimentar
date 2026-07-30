from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Página institucional
    path("", include("institutional.urls")),

    # Painel analítico
    path("", include("dashboard.urls")),
]
