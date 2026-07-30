from django.core.management.base import BaseCommand
from dashboard.services.data_source import refresh_data
class Command(BaseCommand):
    help="Baixa o CSV do Supabase e atualiza o cache Parquet."
    def add_arguments(self,parser): parser.add_argument("--force",action="store_true")
    def handle(self,*args,**opts):
        status=refresh_data(force=opts["force"])
        self.stdout.write(self.style.SUCCESS(f"Dados atualizados: {status.rows} linhas | {status.source} | {status.hash[:12]}"))
