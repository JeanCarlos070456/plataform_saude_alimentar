from __future__ import annotations

import hashlib
import io
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from django.conf import settings
from django.core.cache import cache
from dotenv import load_dotenv
from supabase import create_client


BASE_DIR = Path(settings.BASE_DIR)
load_dotenv(BASE_DIR / ".env")


REQUIRED_COLUMNS = {
    "school_code",
    "school_name",
    "latitude",
    "longitude",
}


@dataclass
class SchoolRefreshStatus:
    rows: int
    source: str
    sha256: str
    updated: bool
    parquet_path: str


def _env(name: str, default: str = "") -> str:
    value = getattr(settings, name, None)
    if value not in (None, ""):
        return str(value)
    return os.getenv(name, default).strip()


def _paths() -> tuple[Path, Path, Path]:
    local_csv = Path(
        getattr(
            settings,
            "CAAFE_SCHOOLS_LOCAL_CSV",
            BASE_DIR / "data" / "escolas.csv",
        )
    )
    parquet = Path(
        getattr(
            settings,
            "CAAFE_SCHOOLS_PARQUET_PATH",
            BASE_DIR / "data" / "cache" / "escolas.parquet",
        )
    )
    metadata = Path(
        getattr(
            settings,
            "CAAFE_SCHOOLS_METADATA_PATH",
            BASE_DIR / "data" / "cache" / "schools_metadata.json",
        )
    )
    return local_csv, parquet, metadata


def _refresh_seconds() -> int:
    raw = getattr(
        settings,
        "CAAFE_SCHOOLS_REFRESH_SECONDS",
        os.getenv("CAAFE_SCHOOLS_REFRESH_SECONDS", "86400"),
    )
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 86400


def _read_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_metadata(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _within_ttl(metadata: dict[str, Any]) -> bool:
    checked_at = metadata.get("checked_at")
    if not checked_at:
        return False

    try:
        previous = datetime.fromisoformat(checked_at)
        if previous.tzinfo is None:
            previous = previous.replace(tzinfo=timezone.utc)
    except Exception:
        return False

    age = (datetime.now(timezone.utc) - previous).total_seconds()
    return age < _refresh_seconds()


def _normalize_school_code(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def _validate(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"escolas.csv sem colunas obrigatórias: {sorted(missing)}"
        )

    out = df.copy()
    out["school_code"] = _normalize_school_code(out["school_code"])
    out["school_name"] = out["school_name"].astype("string").str.strip()
    out["latitude"] = pd.to_numeric(out["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(out["longitude"], errors="coerce")

    if out["school_code"].isna().any() or (out["school_code"] == "").any():
        raise ValueError("Há school_code vazio no escolas.csv.")

    if out["school_name"].isna().any() or (out["school_name"] == "").any():
        raise ValueError("Há school_name vazio no escolas.csv.")

    duplicated = out["school_code"].duplicated(keep=False)
    if duplicated.any():
        values = sorted(out.loc[duplicated, "school_code"].dropna().unique())
        raise ValueError(
            f"Há school_code duplicado no escolas.csv: {values}"
        )

    if out["latitude"].isna().any() or out["longitude"].isna().any():
        raise ValueError("Há latitude/longitude vazia ou não numérica.")

    if not out["latitude"].between(-90, 90).all():
        raise ValueError("Há latitude fora do intervalo válido [-90, 90].")

    if not out["longitude"].between(-180, 180).all():
        raise ValueError("Há longitude fora do intervalo válido [-180, 180].")

    return out


def _download_remote() -> tuple[bytes, str]:
    url = _env("SUPABASE_URL")
    key = _env("SUPABASE_SERVICE_ROLE_KEY")
    bucket = _env("SUPABASE_BUCKET", "projeto_saude_alimentar")
    object_path = _env("SUPABASE_SCHOOLS_OBJECT_PATH", "escolas.csv")

    if not url:
        raise RuntimeError("SUPABASE_URL não configurado.")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY não configurado.")

    client = create_client(url, key)
    raw = client.storage.from_(bucket).download(object_path)

    if not raw:
        raise RuntimeError(
            f"Supabase retornou conteúdo vazio para {bucket}/{object_path}."
        )

    return raw, f"supabase:{bucket}/{object_path}"


def _load_local_bytes(local_csv: Path) -> tuple[bytes, str]:
    if not local_csv.exists():
        raise FileNotFoundError(
            f"Fallback local não encontrado: {local_csv}"
        )
    return local_csv.read_bytes(), f"local:{local_csv.name}"


def _write_parquet_atomic(df: pd.DataFrame, parquet_path: Path) -> None:
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = parquet_path.with_suffix(".tmp.parquet")
    df.to_parquet(
        tmp,
        engine="pyarrow",
        compression="zstd",
        index=False,
    )
    os.replace(tmp, parquet_path)


def refresh_schools(force: bool = False) -> SchoolRefreshStatus:
    local_csv, parquet_path, metadata_path = _paths()
    metadata = _read_metadata(metadata_path)

    if (
        not force
        and parquet_path.exists()
        and metadata
        and _within_ttl(metadata)
    ):
        return SchoolRefreshStatus(
            rows=int(metadata.get("rows", 0)),
            source=str(metadata.get("source", "cache")),
            sha256=str(metadata.get("sha256", "")),
            updated=False,
            parquet_path=str(parquet_path),
        )

    try:
        raw, source = _download_remote()
    except Exception:
        # Em produção, preserve a última versão válida sempre que possível.
        if parquet_path.exists():
            return SchoolRefreshStatus(
                rows=int(metadata.get("rows", 0)),
                source=str(metadata.get("source", "cache-fallback")),
                sha256=str(metadata.get("sha256", "")),
                updated=False,
                parquet_path=str(parquet_path),
            )
        raw, source = _load_local_bytes(local_csv)

    sha256 = hashlib.sha256(raw).hexdigest()
    now = datetime.now(timezone.utc).isoformat()

    if (
        parquet_path.exists()
        and metadata.get("sha256") == sha256
    ):
        metadata["checked_at"] = now
        metadata["source"] = source
        _write_metadata(metadata_path, metadata)

        return SchoolRefreshStatus(
            rows=int(metadata.get("rows", 0)),
            source=source,
            sha256=sha256,
            updated=False,
            parquet_path=str(parquet_path),
        )

    # A fonte só substitui o cache depois de ser lida e validada.
    df = pd.read_csv(io.BytesIO(raw), low_memory=False)
    df = _validate(df)

    _write_parquet_atomic(df, parquet_path)

    payload = {
        "checked_at": now,
        "updated_at": now,
        "rows": int(len(df)),
        "columns": list(df.columns),
        "source": source,
        "sha256": sha256,
    }
    _write_metadata(metadata_path, payload)

    # Indicadores/mapas eventualmente armazenados no Django cache
    # precisam ser recalculados após mudança da fonte geográfica.
    try:
        cache.clear()
    except Exception:
        pass

    return SchoolRefreshStatus(
        rows=len(df),
        source=source,
        sha256=sha256,
        updated=True,
        parquet_path=str(parquet_path),
    )


def load_schools(force_refresh: bool = False) -> pd.DataFrame:
    _, parquet_path, _ = _paths()

    refresh_schools(force=force_refresh)

    if not parquet_path.exists():
        raise FileNotFoundError(
            f"Cache geográfico não foi criado: {parquet_path}"
        )

    df = pd.read_parquet(parquet_path)
    return _validate(df)
