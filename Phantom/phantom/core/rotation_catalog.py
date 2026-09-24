"""
Summary:
    启动时按职业专精选择循环，发现替代候选并持久化成功的自动选择。
Description:
    显式路径优先，扫描只读元数据，完整加载只尝试当前需要的候选。
    按职业 ID 与专精索引处理已选文件的 UUID 冲突；应用选择回写失败只产生警告。
Key Variables:
    LoadedRotations.rotations: 本次启动可供生成与运行的稳定排序循环集合。
    LoadedRotations.warnings: 配置、发现、候选加载与选择回写的警告。
Change Log:
    2026-09-19: Added 多份循环按需加载、回退、UUID 去重和选择回写。
"""

from dataclasses import dataclass
from pathlib import Path

import tomlkit
from tomlkit.container import OutOfOrderTableProxy
from tomlkit.items import InlineTable, Table

from phantom.core.configuration import AppConfig
from phantom.core.rotation import Rotation, RotationError, load_rotation, read_rotation_metadata, write_toml
from phantom.core.specializations import SPECIALIZATION_BY_KEY, SPECIALIZATION_BY_PROFILE, SPECIALIZATIONS


@dataclass(frozen=True)
class LoadedRotations:
    rotations: tuple[Rotation, ...]
    warnings: tuple[str, ...]


def _discover(directory: Path, warnings: list[str]) -> dict[str, list[Path]]:
    candidates: dict[str, list[Path]] = {}
    try:
        paths = sorted((path for path in directory.iterdir() if path.suffix.lower() == ".toml" and path.is_file()), key=lambda path: path.name)
    except OSError as error:
        warnings.append(f"无法扫描 rotation 目录 {directory}：{error}")
        return candidates
    if not paths:
        warnings.append(f"rotation 目录 {directory} 中没有顶层 TOML 候选")
    for path in paths:
        try:
            metadata = read_rotation_metadata(path)
            key = SPECIALIZATION_BY_PROFILE[metadata.profile.unit_class, metadata.profile.unit_spec].key
            candidates.setdefault(key, []).append(path.resolve())
        except (OSError, RotationError) as error:
            warnings.append(f"跳过候选 {path}：{error}")
    return candidates


def _save_selections(config: AppConfig, source: str, selections: dict[str, Path]) -> None:
    document = tomlkit.parse(source)
    table = document.get("rotations")
    if not isinstance(table, (Table, InlineTable, OutOfOrderTableProxy)):
        table = tomlkit.table()
        document["rotations"] = table
    for key, path in selections.items():
        try:
            value = path.relative_to(config.path.parent.resolve()).as_posix()
        except ValueError:
            value = str(path)
        table[key] = value
    write_toml(config.path, source, document)


def load_rotations(config: AppConfig) -> LoadedRotations:
    warnings = list(config.warnings)
    source = config._source
    if source is None:
        try:
            source = config.path.read_bytes().decode("utf-8")
        except (OSError, ValueError) as error:
            warnings.append(f"无法读取选择回写源 {config.path}：{error}")
    candidates = _discover(config.path.parent / "rotations", warnings)
    rotations: list[Rotation] = []
    used_uuids: set[str] = set()
    selected_paths: set[Path] = set()
    selections: dict[str, Path] = {}
    for key in config.rotation_paths:
        if key not in SPECIALIZATION_BY_KEY:
            warnings.append(f"忽略非法 rotation 组合键：{key}")
    for specialization in SPECIALIZATIONS:
        key = specialization.key
        explicit = config.rotation_paths.get(key)
        paths = ([explicit] if explicit is not None else []) + candidates.get(key, [])
        attempted: set[Path] = set()
        for candidate in paths:
            try:
                path = (config.path.parent / candidate).resolve()
                if path in attempted:
                    continue
                attempted.add(path)
                if path in selected_paths:
                    raise RotationError("该文件已由其他职业专精选用")
                metadata = read_rotation_metadata(path)
                if (metadata.profile.unit_class, metadata.profile.unit_spec) != (specialization.unit_class, specialization.unit_spec):
                    raise RotationError(f"职业专精与配置组合 {key} 不符")
                rotation = load_rotation(path, expected_specialization=specialization, reserved_uuids=used_uuids)
            except (OSError, ValueError) as error:
                warnings.append(f"{key} 跳过 {candidate}：{error}")
                continue
            if rotation.uuid != metadata.uuid:
                warnings.append(f"{key} 的 UUID 冲突已保存修复：{path} → {rotation.uuid}")
            rotations.append(rotation)
            used_uuids.add(rotation.uuid)
            selected_paths.add(path)
            if explicit is None or path != (config.path.parent / explicit).resolve():
                selections[key] = path
            break
    if selections:
        if source is None:
            warnings.append("自动选择未能回写 phantom.toml，本次内存选择仍有效")
        else:
            try:
                _save_selections(config, source, selections)
            except (OSError, ValueError, TypeError) as error:
                warnings.append(f"自动选择回写 {config.path} 失败，本次内存选择仍有效：{error}")
    return LoadedRotations(tuple(rotations), tuple(warnings))
