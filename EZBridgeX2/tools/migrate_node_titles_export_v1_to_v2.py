from __future__ import annotations
from EZBridgeX2.core.database import calculate_footnote_title
import base64
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
import numpy as np
SRC_DIR: Path = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _migrate_record_v1_to_v2(item: dict[str, Any]) -> dict[str, Any]:
    full_array: np.ndarray = np.array(item['full'], dtype=np.uint8)
    full_data: str = base64.b64encode(full_array.tobytes()).decode('ascii')
    return {'middle_hash': str(item['middle_hash']), 'title': str(item['title']), 'match_type': str(item.get('match_type', 'manual')), 'created_at': str(item.get('created_at', datetime.now().isoformat())), 'footnote_title': calculate_footnote_title(full_array), 'full_data': full_data}


def migrate_v1_to_v2(input_path: Path, output_path: Path) -> tuple[int, int]:
    with input_path.open('r', encoding='utf-8') as f:
        payload: Any = json.load(f)
    if not isinstance(payload, list):
        raise ValueError('输入文件不是 v1 格式（v1 顶层应为数组）')
    migrated_records: list[dict[str, Any]] = []
    skipped: int = 0
    for item in payload:  # type: ignore
        if not isinstance(item, dict):
            skipped += 1
            continue
        try:
            migrated_records.append(_migrate_record_v1_to_v2(item))  # type: ignore
        except Exception:
            skipped += 1
    output_payload: dict[str, Any] = {'format': 'EZBridgeX2.NodeTitlesExport', 'version': 2, 'exported_at': datetime.now().isoformat(), 'record_count': len(migrated_records), 'records': migrated_records}
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)
    return (len(migrated_records), skipped)


def main() -> int:
    if len(sys.argv) < 2:
        print('用法: uv run python src/tools/migrate_node_titles_export_v1_to_v2.py <输入v1.json> [输出v2.json]')
        return 1
    input_path: Path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        print(f'错误: 输入文件不存在: {input_path}')
        return 1
    if len(sys.argv) >= 3:
        output_path: Path = Path(sys.argv[2]).resolve()
    else:
        output_path = input_path.with_name(f'{input_path.stem}_v2{input_path.suffix}')
    try:
        migrated_count, skipped_count = migrate_v1_to_v2(input_path, output_path)
        print(f'迁移完成: {migrated_count} 条成功，{skipped_count} 条跳过')
        print(f'输出文件: {output_path}')
        return 0
    except Exception as e:
        print(f'迁移失败: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
