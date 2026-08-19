from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm

from .models import AccessRequest, GalleryItem, TeamMember, UserProfile
from .services.access import normalize_email
from .services.media import validate_image_upload


User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def clean(self):
        email = normalize_email(self.cleaned_data.get("username", ""))
        password = self.cleaned_data.get("password")
        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)
        self.cleaned_data["username"] = email
        return self.cleaned_data


class AccessRequestForm(forms.ModelForm):
    class Meta:
        model = AccessRequest
        fields = ("full_name", "email", "role_description")
        labels = {
            "full_name": "Nome completo",
            "email": "E-mail",
            "role_description": "Função ou vínculo com o projeto",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "role_description": forms.TextInput(
                attrs={"placeholder": "Ex.: graduanda, pesquisadora, residente..."}
            ),
        }

    def clean_email(self):
        email = normalize_email(self.cleaned_data["email"])
        existing = User.objects.filter(username__iexact=email).first()
        if existing:
            if existing.is_active:
                raise forms.ValidationError("Este e-mail já possui acesso cadastrado.")
            raise forms.ValidationError(
                "Este e-mail possui um cadastro inativo. Entre em contato com a gestão do projeto."
            )
        if AccessRequest.objects.filter(
            email__iexact=email,
            status=AccessRequest.Status.PENDING,
        ).exists():
            raise forms.ValidationError("Já existe uma solicitação pendente para este e-mail.")
        return email


class GalleryItemForm(forms.ModelForm):
    image_file = forms.FileField(label="Foto", required=False)

    class Meta:
        model = GalleryItem
        fields = (
            "title",
            "eyebrow",
            "summary",
            "external_url",
            "link_label",
            "is_featured",
            "sort_order",
            "status",
        )
        labels = {
            "title": "Título",
            "eyebrow": "Legenda curta",
            "summary": "Texto rápido",
            "external_url": "Link externo",
            "link_label": "Texto do link",
            "is_featured": "Exibir como destaque na Home",
            "sort_order": "Ordem de exibição",
            "status": "Status",
        }
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 5}),
            "external_url": forms.URLInput(attrs={"placeholder": "https://..."}),
        }

    def clean_image_file(self):
        image = self.cleaned_data.get("image_file")
        if image:
            validate_image_upload(image)
        return image

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("is_featured"):
            return cleaned

        if cleaned.get("status") != "published":
            self.add_error(
                "is_featured",
                "Somente uma vivência publicada pode ser marcada como destaque.",
            )

        has_new_image = bool(cleaned.get("image_file"))
        has_existing_image = bool(
            getattr(self.instance, "image_url", "")
            or getattr(self.instance, "static_image", "")
        )
        if not has_new_image and not has_existing_image:
            self.add_error(
                "is_featured",
                "Para usar este card como destaque, cadastre uma imagem.",
            )
        return cleaned


class TeamMemberForm(forms.ModelForm):
    photo_file = forms.FileField(label="Foto", required=False)

    class Meta:
        model = TeamMember
        fields = (
            "full_name",
            "role",
            "short_bio",
            "lattes_url",
            "sort_order",
            "status",
        )
        labels = {
            "full_name": "Nome completo",
            "role": "Função no projeto",
            "short_bio": "Apresentação rápida",
            "lattes_url": "Currículo Lattes",
            "sort_order": "Ordem de exibição",
            "status": "Status",
        }
        widgets = {
            "short_bio": forms.Textarea(attrs={"rows": 5}),
            "lattes_url": forms.URLInput(attrs={"placeholder": "https://lattes.cnpq.br/..."}),
        }

    def clean_photo_file(self):
        image = self.cleaned_data.get("photo_file")
        if image:
            validate_image_upload(image)
        return image


class UserRoleForm(forms.Form):
    role = forms.ChoiceField(label="Perfil", choices=UserProfile.Role.choices)


class CriticalDeactivationForm(forms.Form):
    authorization_password = forms.CharField(
        label="Senha de autorização da coordenação",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "off"}),
    )
