from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib, json, os, tempfile, time
import pandas as pd
from django.conf import settings

@dataclass(frozen=True)
class SourceStatus:
    source: str
    hash: str
    rows: int
    updated_at: float
    parquet_path: str

REQUIRED_COLUMNS = {
    "record_id", "school_code", "school_name", "sex", "age_years", "age_group", "shift",
    "mother_education", "income_group", "race_group", "insecurity_level",
    "any_insecurity", "moderate_severe",
}

def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def _read_metadata() -> dict:
    try:
        return json.loads(settings.CAAFE_METADATA_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        tmp.write(raw)
        temp_name = tmp.name
    os.replace(temp_name, path)

def _download_supabase() -> bytes:
    from supabase import create_client
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return client.storage.from_(settings.SUPABASE_BUCKET).download(settings.SUPABASE_OBJECT_PATH)

def _get_source_bytes() -> tuple[bytes, str]:
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        return _download_supabase(), "supabase"
    if not settings.CAAFE_LOCAL_CSV.exists():
        raise FileNotFoundError(f"CSV analítico não encontrado: {settings.CAAFE_LOCAL_CSV}")
    return settings.CAAFE_LOCAL_CSV.read_bytes(), "local"

def refresh_data(force: bool = False) -> SourceStatus:
    metadata = _read_metadata()
    parquet = settings.CAAFE_PARQUET_PATH
    fresh = parquet.exists() and metadata and (time.time() - metadata.get("updated_at", 0) < settings.CAAFE_REFRESH_SECONDS)
    if fresh and not force:
        return SourceStatus(**{k: metadata[k] for k in SourceStatus.__dataclass_fields__})

    raw, source = _get_source_bytes()
    digest = _sha256(raw)
    if parquet.exists() and metadata.get("hash") == digest and not force:
        metadata["updated_at"] = time.time()
        settings.CAAFE_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return SourceStatus(**{k: metadata[k] for k in SourceStatus.__dataclass_fields__})

    csv_path = settings.CAAFE_LOCAL_CSV
    if source == "supabase":
        _atomic_write(csv_path, raw)
    frame = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"CSV analítico sem colunas obrigatórias: {sorted(missing)}")
    frame["school_code"] = pd.to_numeric(frame["school_code"], errors="coerce").astype("Int64")
    frame["age_years"] = pd.to_numeric(frame["age_years"], errors="coerce")
    frame["any_insecurity"] = pd.to_numeric(frame["any_insecurity"], errors="coerce").astype("Int64")
    frame["moderate_severe"] = pd.to_numeric(frame["moderate_severe"], errors="coerce").astype("Int64")
    parquet.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(parquet, index=False, compression="zstd")
    metadata = {
        "source": source, "hash": digest, "rows": int(len(frame)),
        "updated_at": time.time(), "parquet_path": str(parquet),
    }
    settings.CAAFE_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings.CAAFE_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return SourceStatus(**metadata)

def load_dataframe(force: bool = False) -> tuple[pd.DataFrame, SourceStatus]:
    status = refresh_data(force=force)
    return pd.read_parquet(status.parquet_path), status
