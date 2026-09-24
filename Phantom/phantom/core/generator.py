"""
Summary:
    将已加载的 rotation 集合生成到零售 WoW 的 AddOns 目录，并保留单份入口。
Description:
    先验证并准备完整内容，再安全清空本插件目录，最后发布只引用本次文件的 TOC。
    共享源码与每个条件实例均使用本次随机 UUID 文件名；专精目录内条件和宏各自独立加载。
Key Variables:
    RotationGenerationResult.rotations: 本次共同生成的已加载 rotation 对象。
    GenerationResult.directory: 单份兼容入口的插件输出目录。
Change Log:
    2026-09-19: Changed 按专精拆分随机 UUID 文件，并在完整预准备与路径校验后清空旧包。
    2026-09-19: Added 集合校验、共享资源单次生成和统一 TOC 发布。
    2026-09-19: Changed 为全部宏生成安全按钮，使用解析阶段自动分配的快捷键。
    2026-09-14: Changed 生成 bind_key 宏安全按钮，按 Lua 5.1 规则转义文本。
    2026-09-12: Added 第 10 步离线生成链路。
    2026-09-12: Fixed 生成包漏掉面板字体与图标边框资源。
"""

import re
import stat
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from phantom.core.rotation import Rotation, atomic_write, load_rotation, validate_addon_name
from phantom.core.specializations import SPECIALIZATION_BY_PROFILE

LUA_ROOT = Path(__file__).resolve().parents[1] / "lua"


@dataclass(frozen=True)
class GenerationResult:
    directory: Path
    rotation: Rotation
    files: tuple[str, ...]


@dataclass(frozen=True)
class RotationGenerationResult:
    directory: Path
    rotations: tuple[Rotation, ...]
    files: tuple[str, ...]


def render(rotation: Rotation, addon_name: str) -> dict[str, str]:
    return render_rotations((rotation,), addon_name)


def render_rotations(rotations: tuple[Rotation, ...], addon_name: str) -> dict[str, str]:
    validate_addon_name(addon_name)
    if not rotations:
        raise ValueError("生成集合不能为空")
    groups: set[tuple[str, int]] = set()
    uuids: set[UUID] = set()
    for rotation in rotations:
        group = (rotation.profile.unit_class, rotation.profile.unit_spec)
        if group not in SPECIALIZATION_BY_PROFILE:
            raise ValueError(f"生成集合存在非法职业专精：{group[0]}/{group[1]}")
        rotation_id = UUID(rotation.uuid)
        if group in groups:
            raise ValueError(f"生成集合存在重复职业专精：{group[0]}/{group[1]}")
        if rotation_id in uuids:
            raise ValueError(f"生成集合存在重复 UUID：{rotation.uuid}")
        groups.add(group)
        uuids.add(rotation_id)
    files: dict[str, str] = {}
    generated_ids: set[UUID] = set()
    for directory in ("runtime", "general"):
        for path in sorted((LUA_ROOT / directory).glob("*.lua")):
            identifier = _new_identifier(generated_ids)
            source = path.read_text(encoding="utf-8")
            source, count = re.subn(r"(?m)^uuid: [^\r\n]+$", f"uuid: {identifier}", source, count=1)
            if count != 1:
                raise ValueError(f"共享 Lua 缺少 uuid 文件头：{path}")
            files[f"{directory}/{identifier}.lua"] = source
    for rotation in rotations:
        directory = SPECIALIZATION_BY_PROFILE[(rotation.profile.unit_class, rotation.profile.unit_spec)].key.replace(".", "_")
        for entry in rotation.conditions:
            identifier = _new_identifier(generated_ids)
            files[f"{directory}/{identifier}.lua"] = _instance_header(rotation, identifier) + entry.instance.generate_lua(identifier)
        identifier = _new_identifier(generated_ids)
        files[f"{directory}/{identifier}.lua"] = _instance_header(rotation, identifier) + _render_macros(rotation, addon_name)
    template = (LUA_ROOT / "addonTemplateName.toc").read_text(encoding="utf-8")
    metadata = [line.replace("addonTemplateName", addon_name) for line in template.splitlines() if line.startswith("##")]
    toc = "\n".join(metadata) + "\n\n" + "\n".join(name.replace("/", "\\") for name in files) + "\n"
    files[f"{addon_name}.toc"] = toc
    return files


def _new_identifier(used: set[UUID]) -> str:
    identifier = uuid4()
    if identifier in used:
        raise ValueError(f"生成文件 UUID 碰撞：{identifier}")
    used.add(identifier)
    return str(identifier)


def _instance_header(rotation: Rotation, identifier: str) -> str:
    # 配置中的文本不会作为 Lua 代码插入；token 已经过职业白名单校验。
    return (
        f"--[[\nuuid: {identifier}\nrotation: {rotation.uuid}\n]]\n"
        f'if select(2, UnitClass("player")) ~= "{rotation.profile.unit_class}" or C_SpecializationInfo.GetSpecialization() ~= {rotation.profile.unit_spec} then\n    return\nend\n\n'
        "local addonName, addonTable = ...\n\n"
    )


def _render_macros(rotation: Rotation, addon_name: str) -> str:
    # 按钮局部变量属于函数调用，148 个宏也不会累积到 Lua 5.1 的 chunk 局部变量上限。
    source = (
        "local function BindMacro(buttonName, macroText, key)\n"
        '    local frame = CreateFrame("Button", buttonName, UIParent, "SecureActionButtonTemplate")\n'
        '    frame:SetAttribute("type", "macro")\n'
        '    frame:SetAttribute("macrotext", macroText)\n'
        '    frame:RegisterForClicks("AnyDown", "AnyUp")\n'
        "    SetOverrideBindingClick(frame, true, key, buttonName)\n"
        "end\n\n"
    )
    for index, macro in enumerate(rotation.macros):
        # 名称不包含用户文本；宏文本只作为字符串传给安全按钮。
        button = addon_name + "Button" + UUID(rotation.uuid).hex + str(index)
        source += f"BindMacro({lua_string(button)}, {lua_string(macro.macro_text)}, {lua_string(macro.key)})\n"
    return source


def lua_string(value: str) -> str:
    """Lua 5.1 字符串转义；三位十进制转义避免与后继数字粘连。"""
    escaped = "".join("\\\\" if character == "\\" else '\\"' if character == '"' else f"\\{ord(character):03d}" if ord(character) < 32 or ord(character) == 127 else character for character in value)
    return '"' + escaped + '"'


def generate(rotation_path: Path, executable: Path, addon_name: str = "Phantom") -> GenerationResult:
    validate_addon_name(addon_name)
    executable = _validate_executable(executable)
    rotation = load_rotation(rotation_path)
    result = generate_rotations((rotation,), executable, addon_name)
    return GenerationResult(result.directory, rotation, result.files)


def _validate_executable(executable: Path) -> Path:
    executable = executable.resolve()
    if executable.name.casefold() != "wow.exe" or executable.parent.name.casefold() != "_retail_" or not executable.is_file():
        raise ValueError("wow.executable 必须指向实际存在的 _retail_/Wow.exe")
    return executable


def generate_rotations(rotations: tuple[Rotation, ...], executable: Path, addon_name: str = "Phantom") -> RotationGenerationResult:
    validate_addon_name(addon_name)
    executable = _validate_executable(executable)
    sources = render_rotations(rotations, addon_name)
    toc_name = f"{addon_name}.toc"
    toc = sources.pop(toc_name)
    files = {name: source.encode("utf-8") for name, source in sources.items()}
    # 共享运行时通过路径读取字体/纹理；这些二进制资源不能作为 Lua 加入 TOC。
    for asset in sorted((LUA_ROOT / "media").rglob("*")):
        if asset.is_file():
            files[asset.relative_to(LUA_ROOT).as_posix()] = asset.read_bytes()
    for required in ("media/UiFont.ttf", "media/aura/aura_border_32_4px.tga"):
        if required not in files:
            raise ValueError(f"共享运行时资源缺失：{required}")
    files[toc_name] = toc.encode("utf-8")
    directory = executable.parent / "Interface" / "AddOns" / addon_name
    # 先完成资源读取、目标与整个旧树检查；任何失败都保留旧包。
    for name in files:
        relative = Path(name)
        if relative.is_absolute() or relative.drive or ".." in relative.parts:
            raise ValueError(f"生成目标超出插件目录：{name}")
    old_entries = _validate_output_tree(directory)
    # 子项先于父目录删除；包含隐藏和手工文件，只保留本插件根目录，不重试或回滚。
    for path, is_directory in old_entries:
        if is_directory:
            path.rmdir()
        else:
            path.unlink()
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(target, content)
    return RotationGenerationResult(directory, rotations, tuple(files))


def _validate_output_tree(directory: Path) -> tuple[tuple[Path, bool], ...]:
    """不跟随链接检查中间目录、插件根及整个旧树，返回清理的后序列表。"""

    def inspect(path: Path) -> bool | None:
        try:
            info = path.lstat()
        except FileNotFoundError:
            return None
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f"生成目录含危险链接或 reparse point：{path}")
        if not stat.S_ISDIR(info.st_mode) and not stat.S_ISREG(info.st_mode):
            raise ValueError(f"生成目录含非普通文件：{path}")
        return stat.S_ISDIR(info.st_mode)

    for path in (directory.parent.parent, directory.parent, directory):
        if inspect(path) is False:
            raise ValueError(f"生成路径不是目录：{path}")

    entries: list[tuple[Path, bool]] = []

    def visit(parent: Path) -> None:
        for child in sorted(parent.iterdir()):
            is_directory = inspect(child)
            if is_directory is None:
                raise ValueError(f"生成目录在校验期间发生变化：{child}")
            if is_directory:
                visit(child)
            entries.append((child, is_directory))

    if directory.exists():
        visit(directory)
    return tuple(entries)
