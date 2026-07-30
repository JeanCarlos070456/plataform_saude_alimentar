from django.urls import path

from . import views

urlpatterns = [
    path("tabelas/", views.tables_view, name="tables"),
    path("dashboards/", views.dashboards_view, name="dashboards"),
    path("mapa/", views.map_view, name="map"),
    path("api/metricas/", views.api_metrics, name="api_metrics"),
    path("api/atualizar/", views.refresh_api, name="refresh_api"),
    path("healthz/", views.health, name="health"),
]
