from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def read_authenticode_signature(target_path: Path) -> dict[str, str | bool | None]:
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


def main() -> int:
    python_executable = Path(sys.executable).resolve()
    signature = read_authenticode_signature(python_executable)

    print(f"python_executable: {python_executable}")
    print(f"has_digital_signature: {signature['has_signature']}")
    print(f"signature_status: {signature['status']}")

    status_message = signature.get("status_message")
    if status_message:
        print(f"status_message: {status_message}")

    signer_subject = signature.get("signer_subject")
    if signer_subject:
        print(f"signer_subject: {signer_subject}")

    signer_issuer = signature.get("signer_issuer")
    if signer_issuer:
        print(f"signer_issuer: {signer_issuer}")

    return 0 if signature["status"] == "Valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
