from pathlib import Path
import pandas as pd

ARQUIVO_XLSX = Path("data/data.xlsx")
ARQUIVO_CSV = Path("data/data.csv")

df = pd.read_excel(
    ARQUIVO_XLSX,
    sheet_name=0,
    engine="openpyxl"
)

# Remove espaços extras dos nomes das colunas
df.columns = [str(col).strip() for col in df.columns]

# Exporta em UTF-8 compatível com acentos
df.to_csv(
    ARQUIVO_CSV,
    index=False,
    encoding="utf-8-sig"
)

print(f"CSV criado: {ARQUIVO_CSV}")
print(f"Linhas: {len(df)}")
print(f"Colunas: {len(df.columns)}")