from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from gestao.models import UserProfile


class Command(BaseCommand):
    help = "Cria ou atualiza o usuário desenvolvedor com acesso total."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=False)

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        password = options.get("password") or getpass("Senha do desenvolvedor: ")
        if not password:
            raise CommandError("A senha não pode ficar vazia.")

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=email,
            defaults={"email": email},
        )
        user.email = email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = UserProfile.Role.DEVELOPER
        profile.save(update_fields=["role", "updated_at"])

        status = "criado" if created else "atualizado"
        self.stdout.write(self.style.SUCCESS(f"Desenvolvedor {status}: {email}"))
