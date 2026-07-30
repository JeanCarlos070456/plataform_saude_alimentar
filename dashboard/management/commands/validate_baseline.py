import json
from django.conf import settings
from django.core.management.base import BaseCommand
from dashboard.services.analytics import build_payload
class Command(BaseCommand):
    help="Compara os resultados atuais com a linha de base do relatório técnico."
    def handle(self,*args,**opts):
        baseline=json.loads((settings.DATA_DIR/"baseline_metrics.json").read_text(encoding="utf-8"))
        current=build_payload(force=True)["summary"]
        checks=[("N válido",current["valid_n"],baseline["valid_outcome_n"]),("Prevalência",round(current["prevalence"],1),baseline["any_insecurity_pct"]),("Moderada/grave",round(current["moderate_severe_pct"],1),baseline["moderate_severe_pct"])]
        for label,got,expected in checks:
            mark="OK" if got==expected else "DIVERGENTE"
            self.stdout.write(f"{mark}: {label}: atual={got} | referência={expected}")
