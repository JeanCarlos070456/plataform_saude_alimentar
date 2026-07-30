"""Exporta uma base analítica sem identificadores diretos a partir do Excel original.
Uso: python scripts/export_dashboard_csv.py entrada.xlsx saida.csv
A lógica operacional deve permanecer sincronizada com o dicionário analítico do projeto.
"""
from pathlib import Path
import sys, pandas as pd
if len(sys.argv)!=3: raise SystemExit("Uso: export_dashboard_csv.py entrada.xlsx saida.csv")
df=pd.read_excel(sys.argv[1])
cols=["CdigodaEscola","Codigodaescola","Sexo","idade","TurnoEscolar","escolaridade_mae","renda_class","raca_class","inseguranca","inseguranca_moderada_grave"]
missing=[c for c in cols if c not in df.columns]
if missing: raise SystemExit(f"Colunas ausentes: {missing}")
print("Este script-base deve ser adaptado somente se o dicionário mudar. Use o CSV já incluído no projeto como referência.")
