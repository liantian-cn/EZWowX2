from __future__ import annotations
from EZBridgeX2.core.database import FULL_ICON_BYTES, calculate_footnote_title, initialize_database_schema

import argparse
import base64
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

SRC_DIR: Path = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _normalize_match_type(match_type: str) -> str:
    return match_type if match_type in {'manual', 'cosine'} else 'manual'


def _decode_full_data(value: bytes | str | None) -> bytes:
    if value is None:
        raise ValueError('full_data is missing')
    blob: bytes = value.encode('ascii') if isinstance(value, str) else bytes(value)
    if len(blob) == FULL_ICON_BYTES:
        return blob
    decoded: bytes = base64.b64decode(blob, validate=True)
    if len(decoded) != FULL_ICON_BYTES:
        raise ValueError('invalid full_data payload')
    return decoded


def _extract_full_blob(row: sqlite3.Row, columns: set[str]) -> bytes:
    if 'full_blob' in columns and row['full_blob'] is not None:
        blob: bytes = bytes(row['full_blob'])
        if len(blob) != FULL_ICON_BYTES:
            raise ValueError('invalid full_blob payload')
        return blob
    if 'full_data' in columns:
        return _decode_full_data(row['full_data'])
    raise ValueError('missing full image payload columns')


def migrate_node_titles_to_database_sqlite(source_db: Path, target_db: Path, overwrite: bool = False) -> tuple[int, int, int]:
    if not source_db.exists():
        raise FileNotFoundError(f'源数据库不存在: {source_db}')
    if target_db.exists():
        if not overwrite:
            raise FileExistsError(f'目标数据库已存在: {target_db}')
        target_db.unlink()
    initialize_database_schema(str(target_db))
    src_conn: sqlite3.Connection = sqlite3.connect(str(source_db))
    src_conn.row_factory = sqlite3.Row
    src_cursor: sqlite3.Cursor = src_conn.cursor()
    src_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='node_titles'")
    if src_cursor.fetchone() is None:
        raise ValueError(f'源数据库缺少 node_titles 表: {source_db}')
    src_cursor.execute('PRAGMA table_info(node_titles)')
    columns: set[str] = {str(col['name']) for col in src_cursor.fetchall()}
    if 'middle_hash' not in columns or 'title' not in columns:
        raise ValueError('源数据库字段不足，至少需要 middle_hash 和 title')
    select_columns: list[str] = ['middle_hash', 'title']
    for column in ('match_type', 'created_at', 'footnote_title', 'full_data', 'full_blob'):
        if column in columns:
            select_columns.append(column)
    src_cursor.execute(f"SELECT {', '.join(select_columns)} FROM node_titles ORDER BY id ASC")
    dst_conn: sqlite3.Connection = sqlite3.connect(str(target_db))
    dst_cursor: sqlite3.Cursor = dst_conn.cursor()
    imported_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    for row in src_cursor.fetchall():
        try:
            middle_hash: str = str(row['middle_hash']).strip()
            title: str = str(row['title']).strip()
            if not middle_hash or not title:
                skipped_count += 1
                continue
            raw_full: bytes = _extract_full_blob(row, columns)
            full_array: np.ndarray = np.frombuffer(raw_full, dtype=np.uint8).reshape(8, 8, 3)
            footnote_title_value = row['footnote_title'] if 'footnote_title' in columns else None
            footnote_title: str = str(footnote_title_value).strip() if footnote_title_value else calculate_footnote_title(full_array)
            match_type_value = row['match_type'] if 'match_type' in columns else None
            match_type: str = _normalize_match_type(str(match_type_value).strip() if match_type_value else 'manual')
            created_at_value = row['created_at'] if 'created_at' in columns else None
            created_at: str = str(created_at_value).strip() if created_at_value else datetime.now().isoformat()
            dst_cursor.execute(
                '''
                INSERT INTO icons (title, footnote_title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ''',
                (title, footnote_title, created_at, created_at)
            )
            icon_id: int = int(dst_cursor.lastrowid)  # type: ignore
            dst_cursor.execute(
                '''
                INSERT INTO icon_signatures (icon_id, middle_hash, full_data, match_type, created_at)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (icon_id, middle_hash, raw_full, match_type, created_at)
            )
            imported_count += 1
        except sqlite3.IntegrityError:
            skipped_count += 1
        except Exception:
            error_count += 1
    dst_conn.commit()
    src_conn.close()
    dst_conn.close()
    return imported_count, skipped_count, error_count


def main() -> int:
    parser = argparse.ArgumentParser(description='迁移 node_titles.db 到新 schema 的 database.sqlite')
    parser.add_argument('source', type=Path, help='旧 node_titles.db 文件路径')
    parser.add_argument('target', nargs='?', type=Path, default=Path('database.sqlite'), help='输出 database.sqlite 文件路径')
    parser.add_argument('--overwrite', action='store_true', help='若目标文件存在则覆盖')
    args = parser.parse_args()
    source_db: Path = args.source.resolve()
    target_db: Path = args.target.resolve()
    try:
        imported_count, skipped_count, error_count = migrate_node_titles_to_database_sqlite(
            source_db=source_db,
            target_db=target_db,
            overwrite=bool(args.overwrite)
        )
        print(f'迁移完成: 成功 {imported_count} 条, 跳过 {skipped_count} 条, 错误 {error_count} 条')
        print(f'输出文件: {target_db}')
        return 0
    except Exception as exc:
        print(f'迁移失败: {exc}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
