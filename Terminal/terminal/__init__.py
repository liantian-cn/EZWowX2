from __future__ import annotations
from .application import Termnal

import json
import os
import subprocess
import sys
from pathlib import Path


_PYTHON_SIGNATURE_HELP_URL = "https://discord.gg/9z7Ubbabpg"
_PYTHON_SIGNATURE_REQUIRED_CN = "CN=Python Software Foundation"


def _read_authenticode_signature(target_path: Path) -> dict[str, str | bool | None]:
    escaped_target_path = str(target_path).replace("'", "''")
    command = """
$signature = Get-AuthenticodeSignature -LiteralPath '{target_path}'

[ordered]@{{
    path = $signature.Path
    status = [string]$signature.Status
    status_message = $signature.StatusMessage
    has_signature = $null -ne $signature.SignerCertificate
    signer_subject = if ($null -ne $signature.SignerCertificate) {{ $signature.SignerCertificate.Subject }} else {{ $null }}
    signer_issuer = if ($null -ne $signature.SignerCertificate) {{ $signature.SignerCertificate.Issuer }} else {{ $null }}
}} | ConvertTo-Json -Compress
""".strip().format(target_path=escaped_target_path)
    powershell_executable = (
        Path(os.environ.get("SystemRoot", r"C:\Windows"))
        / "System32"
        / "WindowsPowerShell"
        / "v1.0"
        / "powershell.exe"
    )

    completed = subprocess.run(
        [
            str(powershell_executable),
            "-NoProfile",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        error_message = completed.stderr.strip() or completed.stdout.strip() or "Get-AuthenticodeSignature failed"
        raise RuntimeError(error_message)
    return json.loads(completed.stdout)


def _ensure_supported_python_signature() -> None:
    python_executable = Path(sys.executable).resolve()

    try:
        signature = _read_authenticode_signature(python_executable)
    except Exception as exc:
        raise SystemExit(
            "Terminal 导入已终止：无法验证当前 Python 的数字签名。\n"
            f"python: {python_executable}\n"
            f"error: {exc}\n"
            f"如何解决：{_PYTHON_SIGNATURE_HELP_URL}"
        ) from exc

    has_signature = signature.get("has_signature") is True
    status = str(signature.get("status") or "")
    signer_subject = str(signature.get("signer_subject") or "")
    is_valid = status == "Valid"
    has_expected_cn = _PYTHON_SIGNATURE_REQUIRED_CN in signer_subject

    if has_signature and is_valid and has_expected_cn:
        return

    problems: list[str] = []
    if not has_signature:
        problems.append("未检测到数字签名")
    if not is_valid:
        problems.append(f"签名状态不是 Valid（当前：{status or 'Unknown'}）")
    if not has_expected_cn:
        problems.append(
            "签名主题不是 CN=Python Software Foundation"
            f"（当前：{signer_subject or 'None'}）"
        )

    raise SystemExit(
        "Terminal 导入已终止：当前 Python 未通过签名校验。\n"
        f"python: {python_executable}\n"
        f"问题: {'；'.join(problems)}\n"
        f"如何解决：{_PYTHON_SIGNATURE_HELP_URL}"
    )


_ensure_supported_python_signature()


__all__ = ["Termnal"]
