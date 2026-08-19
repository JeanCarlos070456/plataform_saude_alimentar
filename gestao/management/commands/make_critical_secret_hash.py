from getpass import getpass

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Gera o hash para GESTOR_CRITICAL_ACTION_SECRET_HASH sem salvar a senha em arquivo."

    def handle(self, *args, **options):
        first = getpass("Senha de autorização crítica: ")
        second = getpass("Repita a senha: ")
        if not first:
            raise CommandError("A senha não pode ficar vazia.")
        if first != second:
            raise CommandError("As senhas não coincidem.")
        self.stdout.write(make_password(first))
