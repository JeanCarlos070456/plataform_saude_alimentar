import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "projeto_saude_alimentar")

LOCAL_FILE = ROOT / "data" / "caafe_dashboard.csv"
REMOTE_PATH = "data.csv"

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL não definido no .env")

if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY não definido no .env")

if not LOCAL_FILE.exists():
    raise FileNotFoundError(f"Arquivo local não encontrado: {LOCAL_FILE}")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
storage = supabase.storage.from_(SUPABASE_BUCKET)

with LOCAL_FILE.open("rb") as f:
    storage.upload(
        path=REMOTE_PATH,
        file=f,
        file_options={
            "content-type": "text/csv; charset=utf-8",
            "cache-control": "3600",
            "upsert": "true",
        },
    )

print(f"Upload concluído: {LOCAL_FILE.name} -> {SUPABASE_BUCKET}/{REMOTE_PATH}")