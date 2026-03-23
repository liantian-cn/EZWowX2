"""Icon title repository backed by SQLite."""

import base64
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast

import numpy as np

from ..utils.image_utils import COLOR_MAP, app_dir

FULL_ICON_BYTES: int = 8 * 8 * 3


def calculate_footnote_title(full_array: np.ndarray) -> str:
    footnote_array: np.ndarray = full_array[-2:, -2:]
    first_pixel: np.ndarray = footnote_array[0, 0]
    if np.all(footnote_array == first_pixel):
        color_string: str = f'{first_pixel[0]},{first_pixel[1]},{first_pixel[2]}'
        return COLOR_MAP['IconType'].get(color_string, 'Unknown')
    return 'Unknown'


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a_flat: np.ndarray = a.flatten().astype(np.float32)
    b_flat: np.ndarray = b.flatten().astype(np.float32)
    norm_a: np.floating = np.linalg.norm(a_flat)
    norm_b: np.floating = np.linalg.norm(b_flat)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a_flat, b_flat) / (norm_a * norm_b))


def _normalize_match_type(match_type: str) -> str:
    return match_type if match_type in {'manual', 'cosine'} else 'manual'


def _decode_full_blob(value: bytes | str) -> bytes:
    blob: bytes = value.encode('ascii') if isinstance(value, str) else bytes(value)
    if len(blob) == FULL_ICON_BYTES:
        return blob
    decoded: bytes = base64.b64decode(blob, validate=True)
    if len(decoded) != FULL_ICON_BYTES:
        raise ValueError('invalid full icon bytes length')
    return decoded


def _full_array_from_blob(value: bytes | str) -> np.ndarray:
    return np.frombuffer(_decode_full_blob(value), dtype=np.uint8).reshape(8, 8, 3)


def _require_lastrowid(cursor: sqlite3.Cursor, table_name: str) -> int:
    last_row_id: int | None = cursor.lastrowid
    if last_row_id is None:
        raise sqlite3.DatabaseError(f'insert into {table_name} did not produce lastrowid')
    return int(last_row_id)


def initialize_database_schema(db_path: str) -> None:
    conn: sqlite3.Connection = sqlite3.connect(db_path)
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS icons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            footnote_title TEXT NOT NULL DEFAULT 'Unknown',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS icon_signatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icon_id INTEGER NOT NULL,
            middle_hash TEXT NOT NULL UNIQUE,
            full_data BLOB NOT NULL,
            match_type TEXT NOT NULL DEFAULT 'manual',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(icon_id) REFERENCES icons(id) ON DELETE CASCADE
        )
        '''
    )
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_icon_signatures_icon_id ON icon_signatures(icon_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_icons_title ON icons(title)')
    conn.commit()
    conn.close()


@dataclass
class IconTitleRecord:
    id: int
    icon_id: int
    full_data: bytes
    middle_hash: str
    title: str
    match_type: str
    created_at: str
    footnote_title: str

    @property
    def full_blob(self) -> bytes:
        return _decode_full_blob(self.full_data)

    @property
    def middle_blob(self) -> bytes:
        full_array: np.ndarray = np.frombuffer(self.full_blob, dtype=np.uint8).reshape(8, 8, 3)
        middle_array: np.ndarray = full_array[1:7, 1:7]
        return middle_array.tobytes()

    @property
    def footnote_color(self) -> tuple[int, int, int] | None:
        full_array: np.ndarray = np.frombuffer(self.full_blob, dtype=np.uint8).reshape(8, 8, 3)
        footnote_array: np.ndarray = full_array[-2:, -2:]
        first_pixel: np.ndarray = footnote_array[0, 0]
        if np.all(footnote_array == first_pixel):
            return (int(first_pixel[0]), int(first_pixel[1]), int(first_pixel[2]))
        return None


class IconTitleRepository:
    """Repository for icon titles, signatures, matching and import/export."""

    def __init__(self, db_path: str | None = None, similarity_threshold: float = 0.995) -> None:
        if db_path is None:
            db_path = str(app_dir / 'database.sqlite')
        self.db_path: str = db_path
        self.similarity_threshold: float = similarity_threshold
        self._hash_map: dict[str, tuple[str, int]] = {}
        self._middle_cache: list[tuple[int, np.ndarray, str]] = []
        self._unmatched_hashes: set[str] = set()
        self._unmatched_nodes: list[dict[str, Any]] = []
        self._cosine_matches: list[dict[str, Any]] = []
        initialize_database_schema(self.db_path)
        self._load_data_to_memory()

    def _connect(self) -> sqlite3.Connection:
        conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def _load_data_to_memory(self) -> None:
        self._hash_map.clear()
        self._middle_cache.clear()
        conn: sqlite3.Connection = self._connect()
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT s.id AS signature_id, s.middle_hash, s.full_data, i.title
            FROM icon_signatures AS s
            INNER JOIN icons AS i ON i.id = s.icon_id
            '''
        )
        for row in cursor.fetchall():
            signature_id: int = int(row['signature_id'])
            middle_hash: str = str(row['middle_hash'])
            title: str = str(row['title'])
            full_array: np.ndarray = _full_array_from_blob(row['full_data'])
            middle_array: np.ndarray = full_array[1:7, 1:7]
            self._hash_map[middle_hash] = (title, signature_id)
            self._middle_cache.append((signature_id, middle_array, title))
        conn.close()
        print(f'[IconTitleRepository] loaded {len(self._hash_map)} records')

    def _cache_signature(self, signature_id: int, middle_hash: str, title: str, middle_array: np.ndarray) -> None:
        self._hash_map[middle_hash] = (title, signature_id)
        existing_idx: int | None = None
        for idx, (cached_id, _, _) in enumerate(self._middle_cache):
            if cached_id == signature_id:
                existing_idx = idx
                break
        if existing_idx is None:
            self._middle_cache.append((signature_id, middle_array, title))
        else:
            self._middle_cache[existing_idx] = (signature_id, middle_array, title)

    def _upsert_signature(
        self,
        full_array: np.ndarray,
        middle_hash: str,
        title: str,
        match_type: str,
        created_at: str | None = None
    ) -> int:
        normalized_match_type: str = _normalize_match_type(match_type)
        timestamp: str = str(created_at) if created_at is not None else datetime.now().isoformat()
        full_data: bytes = full_array.astype(np.uint8).tobytes()
        footnote_title: str = calculate_footnote_title(full_array)
        conn: sqlite3.Connection = self._connect()
        cursor: sqlite3.Cursor = conn.cursor()
        try:
            cursor.execute('SELECT id, icon_id FROM icon_signatures WHERE middle_hash = ?', (middle_hash,))
            existing = cursor.fetchone()
            if existing is None:
                cursor.execute(
                    '''
                    INSERT INTO icons (title, footnote_title, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (title, footnote_title, timestamp, timestamp)
                )
                icon_id: int = _require_lastrowid(cursor, 'icons')
                cursor.execute(
                    '''
                    INSERT INTO icon_signatures (icon_id, middle_hash, full_data, match_type, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (icon_id, middle_hash, full_data, normalized_match_type, timestamp)
                )
                signature_id: int = _require_lastrowid(cursor, 'icon_signatures')
            else:
                signature_id = int(existing['id'])
                icon_id = int(existing['icon_id'])
                cursor.execute(
                    '''
                    UPDATE icons
                    SET title = ?, footnote_title = ?, updated_at = ?
                    WHERE id = ?
                    ''',
                    (title, footnote_title, datetime.now().isoformat(), icon_id)
                )
                cursor.execute(
                    '''
                    UPDATE icon_signatures
                    SET full_data = ?, match_type = ?
                    WHERE id = ?
                    ''',
                    (full_data, normalized_match_type, signature_id)
                )
            conn.commit()
            return signature_id
        except sqlite3.Error:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_title(self, middle_hash: str, middle_array: np.ndarray, full_array: np.ndarray) -> str:
        if middle_hash in self._hash_map:
            return self._hash_map[middle_hash][0]
        if middle_hash in self._unmatched_hashes:
            return middle_hash
        footnote_title: str = calculate_footnote_title(full_array)
        skip_cosine_match: bool = footnote_title in {'NONE', 'Unknown'}
        best_match: tuple[int, str, np.ndarray] | None = None
        best_similarity: float = -1.0
        for signature_id, cached_middle, title in self._middle_cache:
            similarity: float = cosine_similarity(middle_array, cached_middle)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = (signature_id, title, cached_middle)
        if best_match and best_similarity >= self.similarity_threshold and not skip_cosine_match:
            _signature_id, matched_title, _matched_middle = best_match
            self.add_title(
                full_array=full_array,
                middle_hash=middle_hash,
                middle_array=middle_array,
                title=matched_title,
                match_type='cosine'
            )
            self._cosine_matches.append(
                {
                    'hash': middle_hash,
                    'title': matched_title,
                    'similarity': best_similarity,
                    'full_array': full_array,
                    'timestamp': datetime.now().isoformat()
                }
            )
            print(f'[IconTitleRepository] cosine matched: {matched_title} ({best_similarity:.4f})')
            return matched_title
        self._unmatched_hashes.add(middle_hash)
        closest_title: str = best_match[1] if best_match is not None else ''
        closest_similarity: float = best_similarity if best_match is not None else 0.0
        self._unmatched_nodes.append(
            {
                'hash': middle_hash,
                'full_array': full_array,
                'middle_array': middle_array,
                'closest_title': closest_title,
                'closest_similarity': closest_similarity,
                'timestamp': datetime.now().isoformat()
            }
        )
        print(f'[IconTitleRepository] unmatched: {middle_hash} ({closest_title}, {closest_similarity:.4f})')
        return middle_hash

    def add_title(
        self,
        full_array: np.ndarray,
        middle_hash: str,
        middle_array: np.ndarray,
        title: str,
        match_type: str = 'manual'
    ) -> int:
        signature_id: int = self._upsert_signature(
            full_array=full_array,
            middle_hash=middle_hash,
            title=title,
            match_type=match_type
        )
        self._cache_signature(signature_id, middle_hash, title, middle_array)
        if middle_hash in self._unmatched_hashes:
            self._unmatched_hashes.discard(middle_hash)
            self._unmatched_nodes = [node for node in self._unmatched_nodes if node['hash'] != middle_hash]
        print(f'[IconTitleRepository] upserted: {title} ({match_type})')
        return signature_id

    def _add_title_with_data(
        self,
        full_array: np.ndarray,
        middle_hash: str,
        title: str,
        match_type: str = 'manual',
        created_at: str | None = None
    ) -> int:
        middle_array: np.ndarray = full_array[1:7, 1:7]
        signature_id: int = self._upsert_signature(
            full_array=full_array,
            middle_hash=middle_hash,
            title=title,
            match_type=match_type,
            created_at=created_at
        )
        self._cache_signature(signature_id, middle_hash, title, middle_array)
        return signature_id

    def delete_title(self, record_id: int) -> bool:
        conn: sqlite3.Connection = self._connect()
        cursor: sqlite3.Cursor = conn.cursor()
        try:
            cursor.execute('SELECT icon_id, middle_hash FROM icon_signatures WHERE id = ?', (record_id,))
            row = cursor.fetchone()
            if row is None:
                return False
            icon_id: int = int(row['icon_id'])
            middle_hash: str = str(row['middle_hash'])
            cursor.execute('DELETE FROM icon_signatures WHERE id = ?', (record_id,))
            cursor.execute('SELECT COUNT(*) AS c FROM icon_signatures WHERE icon_id = ?', (icon_id,))
            count_row = cursor.fetchone()
            signature_count: int = int(count_row['c']) if count_row is not None else 0
            if signature_count == 0:
                cursor.execute('DELETE FROM icons WHERE id = ?', (icon_id,))
            conn.commit()
            self._hash_map.pop(middle_hash, None)
            self._middle_cache = [
                (signature_id, middle_array, title)
                for signature_id, middle_array, title in self._middle_cache
                if signature_id != record_id
            ]
            print(f'[IconTitleRepository] deleted signature id: {record_id}')
            return True
        except sqlite3.Error as exc:
            conn.rollback()
            print(f'[IconTitleRepository] database error: {exc}')
            return False
        finally:
            conn.close()

    def update_title(self, record_id: int, new_title: str, match_type: str | None = None) -> bool:
        conn: sqlite3.Connection = self._connect()
        cursor: sqlite3.Cursor = conn.cursor()
        try:
            cursor.execute('SELECT icon_id FROM icon_signatures WHERE id = ?', (record_id,))
            row = cursor.fetchone()
            if row is None:
                return False
            icon_id: int = int(row['icon_id'])
            cursor.execute(
                'UPDATE icons SET title = ?, updated_at = ? WHERE id = ?',
                (new_title, datetime.now().isoformat(), icon_id)
            )
            if match_type is not None:
                cursor.execute(
                    'UPDATE icon_signatures SET match_type = ? WHERE id = ?',
                    (_normalize_match_type(match_type), record_id)
                )
            cursor.execute('SELECT id, middle_hash FROM icon_signatures WHERE icon_id = ?', (icon_id,))
            related_rows = cursor.fetchall()
            conn.commit()
            related_ids: set[int] = set()
            for related_row in related_rows:
                signature_id: int = int(related_row['id'])
                middle_hash: str = str(related_row['middle_hash'])
                self._hash_map[middle_hash] = (new_title, signature_id)
                related_ids.add(signature_id)
            self._middle_cache = [
                (signature_id, middle_array, new_title if signature_id in related_ids else title)
                for signature_id, middle_array, title in self._middle_cache
            ]
            print(f'[IconTitleRepository] updated title for signature id: {record_id}')
            return True
        except sqlite3.Error as exc:
            conn.rollback()
            print(f'[IconTitleRepository] database error: {exc}')
            return False
        finally:
            conn.close()

    def get_all_titles(self) -> list[IconTitleRecord]:
        conn: sqlite3.Connection = self._connect()
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT
                s.id AS signature_id,
                s.icon_id,
                s.full_data,
                s.middle_hash,
                i.title,
                s.match_type,
                s.created_at,
                i.footnote_title
            FROM icon_signatures AS s
            INNER JOIN icons AS i ON i.id = s.icon_id
            ORDER BY s.id DESC
            '''
        )
        records: list[IconTitleRecord] = []
        for row in cursor.fetchall():
            records.append(
                IconTitleRecord(
                    id=int(row['signature_id']),
                    icon_id=int(row['icon_id']),
                    full_data=bytes(row['full_data']),
                    middle_hash=str(row['middle_hash']),
                    title=str(row['title']),
                    match_type=str(row['match_type']),
                    created_at=str(row['created_at']),
                    footnote_title=str(row['footnote_title'])
                )
            )
        conn.close()
        return records

    def get_cosine_matched_records(self) -> list[IconTitleRecord]:
        conn: sqlite3.Connection = self._connect()
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT
                s.id AS signature_id,
                s.icon_id,
                s.full_data,
                s.middle_hash,
                i.title,
                s.match_type,
                s.created_at,
                i.footnote_title
            FROM icon_signatures AS s
            INNER JOIN icons AS i ON i.id = s.icon_id
            WHERE s.match_type = 'cosine'
            ORDER BY s.id DESC
            '''
        )
        records: list[IconTitleRecord] = []
        for row in cursor.fetchall():
            records.append(
                IconTitleRecord(
                    id=int(row['signature_id']),
                    icon_id=int(row['icon_id']),
                    full_data=bytes(row['full_data']),
                    middle_hash=str(row['middle_hash']),
                    title=str(row['title']),
                    match_type=str(row['match_type']),
                    created_at=str(row['created_at']),
                    footnote_title=str(row['footnote_title'])
                )
            )
        conn.close()
        return records

    def get_stats(self) -> dict[str, int]:
        conn: sqlite3.Connection = self._connect()
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) AS c FROM icon_signatures')
        total_row = cursor.fetchone()
        total: int = int(total_row['c']) if total_row is not None else 0
        cursor.execute("SELECT COUNT(*) AS c FROM icon_signatures WHERE match_type = 'manual'")
        manual_row = cursor.fetchone()
        manual: int = int(manual_row['c']) if manual_row is not None else 0
        cursor.execute("SELECT COUNT(*) AS c FROM icon_signatures WHERE match_type = 'cosine'")
        cosine_row = cursor.fetchone()
        cosine: int = int(cosine_row['c']) if cosine_row is not None else 0
        conn.close()
        return {
            'total': total,
            'manual': manual,
            'cosine': cosine,
            'hash_cached': len(self._hash_map),
            'unmatched_memory': len(self._unmatched_hashes),
            'cosine_matches_session': len(self._cosine_matches)
        }

    def update_threshold(self, new_threshold: float) -> None:
        self.similarity_threshold = max(0.98, min(0.999, new_threshold))
        print(f'[IconTitleRepository] threshold updated: {self.similarity_threshold}')

    def get_unmatched_nodes(self) -> list[dict[str, Any]]:
        return self._unmatched_nodes.copy()

    def get_cosine_matches(self) -> list[dict[str, Any]]:
        return self._cosine_matches.copy()

    def export_to_json(self, path: str) -> bool:
        try:
            records: list[IconTitleRecord] = self.get_all_titles()
            export_records: list[dict[str, Any]] = []
            for record in records:
                full_data_text: str = base64.b64encode(record.full_blob).decode('ascii')
                export_records.append(
                    {
                        'middle_hash': record.middle_hash,
                        'title': record.title,
                        'match_type': record.match_type,
                        'created_at': record.created_at,
                        'footnote_title': record.footnote_title,
                        'full_data': full_data_text
                    }
                )
            export_payload: dict[str, Any] = {
                'format': 'EZBridgeX2.NodeTitlesExport',
                'version': 2,
                'exported_at': datetime.now().isoformat(),
                'record_count': len(export_records),
                'records': export_records
            }
            with open(path, 'w', encoding='utf-8') as file:
                json.dump(export_payload, file, ensure_ascii=False, indent=2)
            print(f'[IconTitleRepository] exported {len(export_records)} records to {path}')
            return True
        except Exception as exc:
            print(f'[IconTitleRepository] export failed: {exc}')
            return False

    def import_from_json(self, path: str, merge: bool = True) -> bool:
        try:
            with open(path, 'r', encoding='utf-8') as file:
                import_payload: Any = json.load(file)
            if isinstance(import_payload, list):
                raise ValueError(
                    '检测到旧版导出格式（v1）。请先运行一次迁移工具: '
                    'uv run python src/tools/migrate_node_titles_export_v1_to_v2.py <输入> <输出>'
                )
            if not isinstance(import_payload, dict):
                raise ValueError('导入文件格式错误：顶层必须为对象')
            import_payload_dict: dict[str, Any] = cast(dict[str, Any], import_payload)
            if import_payload_dict.get('version') != 2:
                raise ValueError('导入文件版本不支持：仅支持 v2')
            import_data_raw: Any = import_payload_dict.get('records')
            if not isinstance(import_data_raw, list):
                raise ValueError('导入文件格式错误：records 必须为数组')
            import_data: list[Any] = cast(list[Any], import_data_raw)
            if not merge:
                conn: sqlite3.Connection = self._connect()
                cursor: sqlite3.Cursor = conn.cursor()
                cursor.execute('DELETE FROM icon_signatures')
                cursor.execute('DELETE FROM icons')
                conn.commit()
                conn.close()
                self._hash_map.clear()
                self._middle_cache.clear()
                self._unmatched_hashes.clear()
                self._unmatched_nodes.clear()
                self._cosine_matches.clear()
            imported_count: int = 0
            skipped_count: int = 0
            for item_raw in import_data:
                if not isinstance(item_raw, dict):
                    skipped_count += 1
                    continue
                item: dict[str, Any] = cast(dict[str, Any], item_raw)
                middle_hash: str = str(item.get('middle_hash', '')).strip()
                title: str = str(item.get('title', '')).strip()
                full_data_text: str = str(item.get('full_data', '')).strip()
                if not middle_hash or not title or not full_data_text:
                    skipped_count += 1
                    continue
                if middle_hash in self._hash_map:
                    continue
                try:
                    full_blob: bytes = base64.b64decode(full_data_text, validate=True)
                    full_array: np.ndarray = np.frombuffer(full_blob, dtype=np.uint8).reshape(8, 8, 3)
                    created_at_raw: Any = item.get('created_at')
                    created_at: str | None = str(created_at_raw) if created_at_raw is not None else None
                    self._add_title_with_data(
                        full_array=full_array,
                        middle_hash=middle_hash,
                        title=title,
                        match_type=str(item.get('match_type', 'manual')),
                        created_at=created_at
                    )
                    imported_count += 1
                except Exception:
                    skipped_count += 1
                    continue
            print(f'[IconTitleRepository] imported {imported_count} records, skipped {skipped_count}')
            return True
        except Exception as exc:
            print(f'[IconTitleRepository] import failed: {exc}')
            return False

    def clear_unmatched_cache(self) -> None:
        self._unmatched_hashes.clear()
        self._unmatched_nodes.clear()
        print('[IconTitleRepository] unmatched cache cleared')

    def clear_cosine_matches_cache(self) -> None:
        self._cosine_matches.clear()
        print('[IconTitleRepository] cosine session cache cleared')
