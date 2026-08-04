from django.core.management.base import BaseCommand

from dashboard.services.school_source import refresh_schools


class Command(BaseCommand):
    help = "Atualiza o cache das escolas a partir do Supabase Storage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Ignora o TTL e verifica a fonte imediatamente.",
        )

    def handle(self, *args, **options):
        status = refresh_schools(force=options["force"])

        action = "atualizadas" if status.updated else "sem alteração"

        self.stdout.write(
            self.style.SUCCESS(
                "Escolas "
                f"{action}: {status.rows} linhas | "
                f"{status.source} | "
                f"{status.sha256[:12]}"
            )
        )
