import base64
import io
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import xxhash
from PIL import Image

from .error import (
    TitleHashMismatchError,
    TitleImportError,
    TitleRecordNotFoundError,
    TitleValidationError,
)

DEBUFF_ON_FRIENDLY = ["MAGIC", "CURSE", "DISEASE", "POISON", "ENRAGE", "BLEED", "DEBUFF_ON_FRIENDLY"]
BUFF_ON_FRIENDLY = ["BUFF_ON_FRIENDLY"]
DEBUFF_ON_ENEMY = ["DEBUFF_ON_ENEMY"]
PLAYER_SPELL = ["PLAYER_SPELL"]
ENEMY_SPELL = ["ENEMY_SPELL_INTERRUPTIBLE", "ENEMY_SPELL_NOT_INTERRUPTIBLE"]
NO_CATEGORY_TITLE_TYPES = ["NONE", "UNKNOWN"]
TITLE_TYPES = tuple(
    DEBUFF_ON_FRIENDLY
    + BUFF_ON_FRIENDLY
    + PLAYER_SPELL
    + ENEMY_SPELL
    + DEBUFF_ON_ENEMY
    + NO_CATEGORY_TITLE_TYPES
)

CACHE_KIND_PERSISTENT = "persistent"
CACHE_KIND_SIMILAR_MATCH = "similar_match"
CACHE_KIND_MISS = "miss"


@dataclass(slots=True)
class TitleRecord:
    hash: str
    title_type: str
    title: str
    valid_array: np.ndarray
    png_bytes: bytes
    from_sqlite: bool
    cache_kind: str


def _resolve_default_db_path() -> Path:
    runtime_dir = Path(sys.argv[0]).resolve().parent
    return runtime_dir / "database.sqlite"


DEFAULT_DB_PATH = _resolve_default_db_path()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a_flat = a.reshape(-1).astype(np.float32)
    b_flat = b.reshape(-1).astype(np.float32)
    norm_a = np.linalg.norm(a_flat)
    norm_b = np.linalg.norm(b_flat)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a_flat, b_flat) / (norm_a * norm_b))


def ndarray_to_hash(valid_array: np.ndarray) -> str:
    checked_array = _normalize_valid_array(valid_array)
    return xxhash.xxh3_64_hexdigest(np.ascontiguousarray(checked_array), seed=0)


def _normalize_valid_array(valid_array: np.ndarray) -> np.ndarray:
    array = np.asarray(valid_array, dtype=np.uint8)
    if array.shape != (6, 6, 3):
        raise TitleValidationError(f"valid_array 必须是 6x6x3，当前是 {array.shape}")
    return np.ascontiguousarray(array.copy())


def _normalize_title_type(title_type: str) -> str:
    normalized = title_type.strip().upper()
    if normalized not in TITLE_TYPES:
        raise TitleValidationError(f"不支持的 title_type: {title_type}")
    return normalized


def _valid_array_to_json(valid_array: np.ndarray) -> str:
    return json.dumps(valid_array.tolist(), ensure_ascii=False, separators=(",", ":"))


def _json_to_valid_array(payload: str) -> np.ndarray:
    return _normalize_valid_array(np.array(json.loads(payload), dtype=np.uint8))


def _valid_array_to_png_bytes(valid_array: np.ndarray) -> bytes:
    image = Image.fromarray(valid_array, mode="RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _encode_png_bytes(png_bytes: bytes) -> str:
    return base64.b64encode(png_bytes).decode("ascii")


def _decode_png_bytes(payload: str) -> bytes:
    return base64.b64decode(payload.encode("ascii"))


class TitleManager:
    def __init__(
        self,
        db_path: str | Path | None = None,
        similarity_threshold: float = 0.999,
    ) -> None:
        self.db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.similarity_threshold = similarity_threshold
        self._closed = False
        self.records_by_hash: dict[str, TitleRecord] = {}
        self.persistent_hashes_by_type: dict[str, set[str]] = {title_type: set() for title_type in TITLE_TYPES}
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()
        self.rebuild_memory()

    def _create_table(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS icon_titles (
                hash TEXT PRIMARY KEY,
                title_type TEXT NOT NULL,
                title TEXT NOT NULL,
                valid_array_json TEXT NOT NULL,
                png_bytes BLOB NOT NULL
            )
            """
        )
        self.conn.commit()

    def close(self) -> None:
        if self._closed:
            return
        self.conn.close()
        self._closed = True

    def _row_to_record(self, row: sqlite3.Row) -> TitleRecord:
        return TitleRecord(
            hash=row["hash"],
            title_type=row["title_type"],
            title=row["title"],
            valid_array=_json_to_valid_array(row["valid_array_json"]),
            png_bytes=bytes(row["png_bytes"]),
            from_sqlite=True,
            cache_kind=CACHE_KIND_PERSISTENT,
        )

    def _record_to_public_dict(self, record: TitleRecord) -> dict[str, Any]:
        return {
            "hash": record.hash,
            "title_type": record.title_type,
            "title": record.title,
            "valid_array": record.valid_array.tolist(),
            "png_bytes": record.png_bytes,
            "from_sqlite": record.from_sqlite,
            "cache_kind": record.cache_kind,
        }

    def _clear_memory(self) -> None:
        self.records_by_hash.clear()
        self.persistent_hashes_by_type = {title_type: set() for title_type in TITLE_TYPES}

    def _store_memory_record(self, record: TitleRecord) -> None:
        existing = self.records_by_hash.get(record.hash)
        if existing is not None and existing.from_sqlite:
            self.persistent_hashes_by_type[existing.title_type].discard(existing.hash)
        self.records_by_hash[record.hash] = record
        if record.from_sqlite:
            self.persistent_hashes_by_type[record.title_type].add(record.hash)

    def _delete_memory_record(self, record_hash: str) -> None:
        existing = self.records_by_hash.pop(record_hash, None)
        if existing is not None and existing.from_sqlite:
            self.persistent_hashes_by_type[existing.title_type].discard(existing.hash)

    def rebuild_memory(self) -> None:
        self._clear_memory()
        rows = self.conn.execute(
            "SELECT hash, title_type, title, valid_array_json, png_bytes FROM icon_titles ORDER BY hash"
        ).fetchall()
        for row in rows:
            self._store_memory_record(self._row_to_record(row))

    def list_database_records(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT hash, title_type, title, valid_array_json, png_bytes FROM icon_titles ORDER BY hash"
        ).fetchall()
        return [self._record_to_public_dict(self._row_to_record(row)) for row in rows]

    def list_memory_records(self) -> list[dict[str, Any]]:
        return [self._record_to_public_dict(record) for record in self.records_by_hash.values()]

    def has_persistent_record(self, record_hash: str) -> bool:
        record = self.records_by_hash.get(record_hash)
        return bool(record is not None and record.from_sqlite)

    def add_record(
        self,
        *,
        valid_array: np.ndarray,
        title_type: str,
        title: str,
        hash: str | None = None,
    ) -> dict[str, Any]:
        normalized_array = _normalize_valid_array(valid_array)
        normalized_title_type = _normalize_title_type(title_type)
        computed_hash = ndarray_to_hash(normalized_array)
        if hash is not None and hash != computed_hash:
            raise TitleHashMismatchError("传入的 hash 和 valid_array 计算结果不一致")

        png_bytes = _valid_array_to_png_bytes(normalized_array)
        record = TitleRecord(
            hash=computed_hash,
            title_type=normalized_title_type,
            title=title,
            valid_array=normalized_array,
            png_bytes=png_bytes,
            from_sqlite=True,
            cache_kind=CACHE_KIND_PERSISTENT,
        )
        self.conn.execute(
            """
            INSERT INTO icon_titles(hash, title_type, title, valid_array_json, png_bytes)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(hash) DO UPDATE SET
                title_type=excluded.title_type,
                title=excluded.title,
                valid_array_json=excluded.valid_array_json,
                png_bytes=excluded.png_bytes
            """,
            (
                record.hash,
                record.title_type,
                record.title,
                _valid_array_to_json(record.valid_array),
                sqlite3.Binary(record.png_bytes),
            ),
        )
        self.conn.commit()
        self._store_memory_record(record)
        return self._record_to_public_dict(record)

    def delete_record(self, record_hash: str) -> None:
        self.conn.execute("DELETE FROM icon_titles WHERE hash = ?", (record_hash,))
        self.conn.commit()
        self._delete_memory_record(record_hash)

    def update_record(
        self,
        current_hash: str,
        *,
        valid_array: np.ndarray,
        title_type: str,
        title: str,
        hash: str | None = None,
    ) -> dict[str, Any]:
        if current_hash not in {record["hash"] for record in self.list_database_records()}:
            raise TitleRecordNotFoundError(f"找不到要更新的 hash: {current_hash}")
        updated_record = self.add_record(valid_array=valid_array, title_type=title_type, title=title, hash=hash)
        if updated_record["hash"] != current_hash:
            self.delete_record(current_hash)
        return updated_record

    def get_title(self, valid_array: np.ndarray, title_type: str, hash: str) -> str:
        normalized_array = _normalize_valid_array(valid_array)
        normalized_title_type = _normalize_title_type(title_type)

        cached_record = self.records_by_hash.get(hash)
        if cached_record is not None:
            return cached_record.title

        best_match: TitleRecord | None = None
        best_score = -1.0
        for candidate_hash in self.persistent_hashes_by_type[normalized_title_type]:
            candidate = self.records_by_hash[candidate_hash]
            score = cosine_similarity(normalized_array, candidate.valid_array)
            if score > best_score:
                best_match = candidate
                best_score = score

        if best_match is not None and best_score > self.similarity_threshold:
            matched_record = TitleRecord(
                hash=hash,
                title_type=normalized_title_type,
                title=best_match.title,
                valid_array=normalized_array,
                png_bytes=_valid_array_to_png_bytes(normalized_array),
                from_sqlite=False,
                cache_kind=CACHE_KIND_SIMILAR_MATCH,
            )
            self._store_memory_record(matched_record)
            return matched_record.title

        miss_record = TitleRecord(
            hash=hash,
            title_type=normalized_title_type,
            title=hash,
            valid_array=normalized_array,
            png_bytes=_valid_array_to_png_bytes(normalized_array),
            from_sqlite=False,
            cache_kind=CACHE_KIND_MISS,
        )
        self._store_memory_record(miss_record)
        return miss_record.title

    def export_json(self, output_path: str | Path) -> Path:
        payload = []
        for record in self.list_database_records():
            payload.append(
                {
                    "hash": record["hash"],
                    "title_type": record["title_type"],
                    "title": record["title"],
                    "valid_array": record["valid_array"],
                    "png_base64": _encode_png_bytes(record["png_bytes"]),
                }
            )
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_file

    def import_json(self, input_path: str | Path) -> None:
        try:
            payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
            for item in payload:
                valid_array = _normalize_valid_array(np.array(item["valid_array"], dtype=np.uint8))
                title_type = _normalize_title_type(item["title_type"])
                title = str(item["title"])
                png_bytes = _decode_png_bytes(item["png_base64"]) if item.get("png_base64") else _valid_array_to_png_bytes(valid_array)
                computed_hash = ndarray_to_hash(valid_array)
                if item.get("hash") and item["hash"] != computed_hash:
                    raise TitleImportError("JSON 里的 hash 和 valid_array 不一致")
                self.conn.execute(
                    """
                    INSERT INTO icon_titles(hash, title_type, title, valid_array_json, png_bytes)
                    VALUES(?, ?, ?, ?, ?)
                    ON CONFLICT(hash) DO UPDATE SET
                        title_type=excluded.title_type,
                        title=excluded.title,
                        valid_array_json=excluded.valid_array_json,
                        png_bytes=excluded.png_bytes
                    """,
                    (
                        computed_hash,
                        title_type,
                        title,
                        _valid_array_to_json(valid_array),
                        sqlite3.Binary(png_bytes),
                    ),
                )
        except TitleImportError:
            self.conn.rollback()
            raise
        except Exception as exc:
            self.conn.rollback()
            raise TitleImportError(f"导入标题 JSON 失败: {exc}") from exc

        self.conn.commit()
        self.rebuild_memory()


_DEFAULT_TITLE_MANAGER: TitleManager | None = None


def get_default_title_manager(db_path: str | Path | None = None) -> TitleManager:
    global _DEFAULT_TITLE_MANAGER
    if _DEFAULT_TITLE_MANAGER is None or _DEFAULT_TITLE_MANAGER._closed:
        _DEFAULT_TITLE_MANAGER = TitleManager(db_path=db_path)
    elif db_path is not None and Path(db_path) != _DEFAULT_TITLE_MANAGER.db_path:
        _DEFAULT_TITLE_MANAGER.close()
        _DEFAULT_TITLE_MANAGER = TitleManager(db_path=db_path)
    return _DEFAULT_TITLE_MANAGER


def reset_default_title_manager(db_path: str | Path | None = None) -> TitleManager | None:
    global _DEFAULT_TITLE_MANAGER
    if _DEFAULT_TITLE_MANAGER is not None and not _DEFAULT_TITLE_MANAGER._closed:
        _DEFAULT_TITLE_MANAGER.close()
    _DEFAULT_TITLE_MANAGER = None
    if db_path is None:
        return None
    _DEFAULT_TITLE_MANAGER = TitleManager(db_path=db_path)
    return _DEFAULT_TITLE_MANAGER
