from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
BUCKET = os.getenv("SUPABASE_BUCKET", "projeto_saude_alimentar").strip()

DATA_OBJECT = os.getenv("SUPABASE_OBJECT_PATH", "data.csv").strip()
SCHOOLS_OBJECT = os.getenv("SUPABASE_SCHOOLS_OBJECT_PATH", "escolas.csv").strip()

DATA_LOCAL = ROOT / "data" / "data.csv"
SCHOOLS_LOCAL = ROOT / "data" / "escolas.csv"


def fail(message: str) -> None:
    print(f"\nERRO: {message}")
    sys.exit(1)


def validate_env() -> None:
    if not SUPABASE_URL:
        fail("SUPABASE_URL não está definido no .env.")
    if not SUPABASE_KEY:
        fail("SUPABASE_SERVICE_ROLE_KEY não está definido no .env.")
    if not BUCKET:
        fail("SUPABASE_BUCKET não está definido no .env.")

    print("Configuração:")
    print(f"  URL configurada: {'SIM' if SUPABASE_URL else 'NÃO'}")
    print(f"  Chave configurada: {'SIM' if SUPABASE_KEY else 'NÃO'}")
    print(f"  Bucket: {BUCKET}")
    print(f"  data.csv remoto: {DATA_OBJECT}")
    print(f"  escolas.csv remoto: {SCHOOLS_OBJECT}")


def validate_local_files() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not DATA_LOCAL.exists():
        fail(f"Arquivo não encontrado: {DATA_LOCAL}")
    if not SCHOOLS_LOCAL.exists():
        fail(
            f"Arquivo não encontrado: {SCHOOLS_LOCAL}\n"
            "Copie o escolas.csv para a pasta data/ antes de executar."
        )

    data_df = pd.read_csv(DATA_LOCAL, low_memory=False)
    schools_df = pd.read_csv(SCHOOLS_LOCAL)

    print("\nArquivos locais:")
    print(f"  data.csv: {len(data_df)} linhas x {len(data_df.columns)} colunas")
    print(f"  escolas.csv: {len(schools_df)} linhas x {len(schools_df.columns)} colunas")

    required_schools = {
        "school_code",
        "school_name",
        "latitude",
        "longitude",
    }
    missing = required_schools - set(schools_df.columns)
    if missing:
        fail(
            "escolas.csv não possui as colunas mínimas: "
            + ", ".join(sorted(missing))
        )

    if schools_df["school_name"].isna().any():
        fail("Há school_name vazio no escolas.csv.")

    lat = pd.to_numeric(schools_df["latitude"], errors="coerce")
    lon = pd.to_numeric(schools_df["longitude"], errors="coerce")

    if lat.isna().any() or lon.isna().any():
        fail("Há latitude/longitude não numérica no escolas.csv.")

    if not lat.between(-90, 90).all():
        fail("Há latitude fora do intervalo -90 a 90.")

    if not lon.between(-180, 180).all():
        fail("Há longitude fora do intervalo -180 a 180.")

    return data_df, schools_df


def upload_csv(storage, local_path: Path, remote_path: str) -> None:
    print(f"\nEnviando {local_path.name} -> {BUCKET}/{remote_path}")

    with local_path.open("rb") as file_obj:
        storage.upload(
            path=remote_path,
            file=file_obj,
            file_options={
                "content-type": "text/csv; charset=utf-8",
                "cache-control": "3600",
                "upsert": "true",
            },
        )

    print("  Upload concluído.")


def validate_remote_csv(storage, remote_path: str, expected_rows: int, label: str) -> None:
    print(f"Validando download de {remote_path}...")
    payload = storage.download(remote_path)

    if not payload:
        fail(f"O download remoto de {remote_path} retornou vazio.")

    df = pd.read_csv(io.BytesIO(payload), low_memory=False)

    print(f"  {label}: {len(df)} linhas x {len(df.columns)} colunas")

    if len(df) != expected_rows:
        fail(
            f"{label}: número de linhas remoto ({len(df)}) "
            f"difere do local ({expected_rows})."
        )


def main() -> None:
    print("=" * 72)
    print("TESTE SUPABASE STORAGE - PROJETO SAÚDE ALIMENTAR")
    print("=" * 72)

    validate_env()
    data_df, schools_df = validate_local_files()

    print("\nConectando ao Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    storage = supabase.storage.from_(BUCKET)

    try:
        before = storage.list()
        print(f"Conexão OK. Objetos encontrados no bucket antes do upload: {len(before)}")
    except Exception as exc:
        fail(
            "Não foi possível acessar o bucket.\n"
            f"Detalhe: {exc}"
        )

    try:
        upload_csv(storage, DATA_LOCAL, DATA_OBJECT)
        upload_csv(storage, SCHOOLS_LOCAL, SCHOOLS_OBJECT)
    except Exception as exc:
        fail(
            "Falha durante o upload.\n"
            f"Detalhe: {exc}"
        )

    try:
        validate_remote_csv(
            storage,
            DATA_OBJECT,
            expected_rows=len(data_df),
            label="data.csv remoto",
        )
        validate_remote_csv(
            storage,
            SCHOOLS_OBJECT,
            expected_rows=len(schools_df),
            label="escolas.csv remoto",
        )
    except Exception as exc:
        fail(
            "Falha na validação por download.\n"
            f"Detalhe: {exc}"
        )

    try:
        after = storage.list()
        names = sorted(
            item.get("name", "")
            for item in after
            if isinstance(item, dict)
        )

        print("\nObjetos no bucket após o upload:")
        for name in names:
            print(f"  - {name}")
    except Exception:
        pass

    print("\n" + "=" * 72)
    print("SUCESSO: conexão, upload e leitura dos dois CSVs validados.")
    print("=" * 72)


if __name__ == "__main__":
    main()