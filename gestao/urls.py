from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .forms import EmailAuthenticationForm
from . import views

app_name = "gestao"

urlpatterns = [
    path(
        "login/",
        views.EmailLoginView.as_view(
            authentication_form=EmailAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="institutional:home"),
        name="logout",
    ),
    path("solicitar-acesso/", views.request_access, name="request_access"),
    path("solicitar-acesso/enviado/", views.request_access_done, name="request_access_done"),
    path(
        "senha/esqueci/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.txt",
            subject_template_name="registration/password_reset_subject.txt",
            success_url=reverse_lazy("gestao:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "senha/esqueci/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "senha/redefinir/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("gestao:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "senha/redefinir/concluido/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "primeiro-acesso/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/initial_password_confirm.html",
            success_url=reverse_lazy("gestao:initial_password_done"),
        ),
        name="initial_password",
    ),
    path(
        "primeiro-acesso/concluido/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/initial_password_done.html"
        ),
        name="initial_password_done",
    ),
    path("", views.dashboard, name="dashboard"),
    path("solicitacoes/", views.access_requests, name="access_requests"),
    path("solicitacoes/<int:pk>/aprovar/", views.approve_request, name="approve_request"),
    path("solicitacoes/<int:pk>/recusar/", views.reject_request, name="reject_request"),
    path("solicitacoes/<int:pk>/reenviar-convite/", views.resend_invite, name="resend_invite"),
    path("usuarios/", views.users_list, name="users"),
    path("usuarios/<int:pk>/perfil/", views.update_user_role, name="update_user_role"),
    path("usuarios/<int:pk>/desligar/", views.deactivate_user, name="deactivate_user"),
    path("galeria/", views.gallery_list, name="gallery_list"),
    path("galeria/novo/", views.gallery_create, name="gallery_create"),
    path("galeria/<int:pk>/editar/", views.gallery_edit, name="gallery_edit"),
    path("galeria/<int:pk>/arquivar/", views.gallery_archive, name="gallery_archive"),
    path("galeria/<int:pk>/excluir/", views.gallery_delete, name="gallery_delete"),
    path("equipe/", views.team_list, name="team_list"),
    path("equipe/novo/", views.team_create, name="team_create"),
    path("equipe/<int:pk>/editar/", views.team_edit, name="team_edit"),
    path("equipe/<int:pk>/arquivar/", views.team_archive, name="team_archive"),
    path("equipe/<int:pk>/excluir/", views.team_delete, name="team_delete"),
    path("auditoria/", views.audit_list, name="audit_list"),
]
